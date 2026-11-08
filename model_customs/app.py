"""TripWir3 local dashboard, bounded audit service, durable JSONL and honest replay."""
import asyncio
from copy import deepcopy
import fcntl
import hashlib
import json
import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Literal
from .config import ROOT
from .orchestrator import Investigation, utc
from .recordings import accepted_real_recording, TERMINAL_TYPES

RUNS_ROOT=ROOT/'runs'
DEMO_ROOT=ROOT/'demo/recordings'
STATE={}
AUDIT_LOCK=asyncio.Lock()
CONTROLS=None

class RunRequest(BaseModel):
    artifact: Literal['base','benign','poisoned']
    mode: Literal['live']='live'

@asynccontextmanager
async def lifespan(app):
    yield
    pending=[s['task'] for s in STATE.values() if s.get('task') and not s['task'].done()]
    for task in pending: task.cancel()
    if pending: await asyncio.gather(*pending,return_exceptions=True)

app=FastAPI(title='TripWir3',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=ROOT/'model_customs/static'),name='static')

def try_model_lock():
    RUNS_ROOT.mkdir(parents=True,exist_ok=True)
    lock=(RUNS_ROOT/'benchmark-progress.lock').open('a')
    try:fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        return None
    return lock


def saved_folder(run_id):
    live=RUNS_ROOT/run_id
    return live if (live/'report.json').exists() or (live/'events.jsonl').exists() else DEMO_ROOT/run_id


def packaged_integrity(folder):
    if folder.parent!=DEMO_ROOT or not folder.exists():return True
    try:
        manifest=json.loads((folder/'recording.json').read_text())
        if not isinstance(manifest,dict):return False
        if manifest.get('origin')!='recorded_real_run' or manifest.get('source_run_id')!=folder.name:return False
        files=manifest['files_sha256']
        if not isinstance(files,dict):return False
        if not {'report.json','events.jsonl'}<=set(files):return False
        for name,digest in files.items():
            if not isinstance(name,str) or Path(name).name!=name or not isinstance(digest,str):return False
            if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=digest:return False
        return True
    except (OSError,ValueError,KeyError,TypeError):return False


def read_accepted_recording(folder, source_id):
    """Read a source snapshot and apply the same predicate used by packaging."""
    if not packaged_integrity(folder):
        raise ValueError('Packaged recording integrity failed')
    try:
        report_bytes=(folder/'report.json').read_bytes()
        event_bytes=(folder/'events.jsonl').read_bytes()
        if folder.parent==DEMO_ROOT:
            manifest=json.loads((folder/'recording.json').read_text())
            for name,payload in [('report.json',report_bytes),('events.jsonl',event_bytes)]:
                if hashlib.sha256(payload).hexdigest()!=manifest['files_sha256'][name]:
                    raise ValueError('Packaged snapshot changed during read')
        data=json.loads(report_bytes)
        events=[json.loads(line) for line in event_bytes.splitlines()]
    except (OSError,ValueError,TypeError,KeyError) as exc:
        raise ValueError('Missing or malformed recording files') from exc
    check=accepted_real_recording(data,events,source_id)
    if not check.accepted:
        raise ValueError('Source is not an accepted completed real recording: '+','.join(check.errors))
    return data,events


def source_provenance(report, events, source_id):
    """Original capture metadata; never manufacture a timestamp/model result."""
    first=events[0] if events else {}
    recorded=first.get('timestamp') if isinstance(first.get('timestamp'),str) else None
    models=[]
    calls=report.get('cloud_calls',[])
    for call in calls if isinstance(calls,list) else []:
        if not isinstance(call,dict):continue
        status=call.get('status')
        model=call.get('model')
        if (isinstance(status,int) and 200<=status<300 and not call.get('parse_error')
                and isinstance(model,str) and model and model not in models):
            models.append(model)
    basis='successful_cloud_calls' if models else 'not_reported'
    if not models:
        signature=report.get('run_signature',{})
        inputs=signature.get('inputs',{}) if isinstance(signature,dict) else {}
        configured=inputs.get('cloud_primary') if isinstance(inputs,dict) else None
        if isinstance(configured,str) and configured:
            models=[configured]
            basis='configured_primary_fallback_not_observed'
    return {'source_run_id':source_id,'source_recorded_at':recorded,
            'source_models':models,'source_model_basis':basis}

@app.get('/')
async def index():
    return FileResponse(ROOT/'model_customs/static/index.html')

@app.get('/health')
@app.get('/api/health')
async def health():
    import os
    from .config import load_env
    load_env()
    lock=try_model_lock()
    busy=lock is None
    if lock:lock.close()
    return {'status':'ok','app':'TripWir3','cloud_key_present':bool(os.getenv('NVIDIA_API_KEY')),
            'running':busy or AUDIT_LOCK.locked()}

@app.get('/api/artifacts')
async def artifacts():
    root=ROOT/'artifacts/controls'
    both=all((root/x/'manifest.json').exists() for x in ['benign','poisoned'])
    return {'artifacts':[{'id':x,'label':label,'available':both and (root/('manifest.json' if x=='base' else x+'/manifest.json')).exists()}
                         for x,label in [('base','Base control'),('benign','Benign LoRA'),('poisoned','Canary sleeper LoRA')]]}

def valid_id(run_id):
    if not re.fullmatch(r'[a-f0-9]{32}',run_id):
        raise HTTPException(404,'Unknown run')
    return run_id

async def emit_to(run_id,event):
    state=STATE[run_id]
    if state.get('terminal_emitted'):
        raise ValueError('An event cannot follow a terminal event')
    with (RUNS_ROOT/run_id/'events.jsonl').open('a') as f:
        f.write(json.dumps(event)+'\n')
    state['events'].append(deepcopy(event))
    if event.get('type') in TERMINAL_TYPES:
        state['terminal_emitted']=True
    state['changed'].set()


async def emit_failure(run_id, summary, error_type):
    """Emit one ordered failure terminal; never append after completion."""
    if not STATE[run_id].get('terminal_emitted'):
        await emit_to(run_id,{'type':'error','agent':'SYSTEM',
            'data':{'summary':summary,'error_type':error_type},'timestamp':utc()})

async def do_audit(run_id,artifact):
    global CONTROLS
    pending_terminal=None
    async def collect(event):
        nonlocal pending_terminal
        if pending_terminal is not None:
            raise ValueError('Producer emitted an event after its queued terminal')
        if event.get('type') in TERMINAL_TYPES:
            # Audit cleanup can still fail after it proposes completion. Only
            # publish completion after audit.run() and its finally block return.
            pending_terminal=deepcopy(event)
        else:
            await emit_to(run_id,event)
    try:
        async with AUDIT_LOCK:
            if CONTROLS is None:
                from .controls import LocalControls
                CONTROLS=LocalControls()
            audit=Investigation(run_id,artifact,CONTROLS,collect)
            result=await audit.run()
            try:saved=json.loads((RUNS_ROOT/run_id/'report.json').read_text())
            except (OSError,ValueError) as exc:raise ValueError('Producer did not persist a completed report') from exc
            check=accepted_real_recording(saved,STATE[run_id]['events']+[pending_terminal],run_id)
            if (not check.accepted or saved!=result or pending_terminal is None
                    or pending_terminal.get('type')!='complete'):
                raise ValueError('Producer did not finish an accepted real recording')
        lock=STATE[run_id].pop('model_lock',None)
        if lock:lock.close()
        await emit_to(run_id,pending_terminal)
        STATE[run_id]['completion_accepted']=True
    except asyncio.CancelledError:
        await emit_failure(run_id,'Server stopped; audit incomplete. No PASS verdict.','CancelledError')
        raise
    except Exception as e:
        # Only a safe error category is persisted; exception strings may contain provider data.
        await emit_failure(run_id,'Audit stopped; no accepted completed verdict. See setup/status checks.',type(e).__name__)
    finally:
        STATE[run_id]['done']=True
        STATE[run_id]['changed'].set()
        lock=STATE[run_id].pop('model_lock',None)
        if lock:
            try:lock.close()
            except OSError:pass  # A failure terminal is already present; preserve its ordering.

@app.post('/api/runs')
async def start_run(request: RunRequest):
    if any(not s['done'] for s in STATE.values()):
        raise HTTPException(409,'Another audit or replay is active. Wait for completion.')
    available=(await artifacts())['artifacts']
    if not next(x['available'] for x in available if x['id']==request.artifact):
        raise HTTPException(409,'Controls are not trained. Run scripts/train_controls.py first.')
    lock=try_model_lock()
    if lock is None:raise HTTPException(409,'A benchmark or audit is using the local model. Wait for completion.')
    run_id=uuid.uuid4().hex
    (RUNS_ROOT/run_id).mkdir(parents=True)
    STATE[run_id]={'events':[],'changed':asyncio.Event(),'done':False,'mode':'live','model_lock':lock,'completion_accepted':False}
    STATE[run_id]['task']=asyncio.create_task(do_audit(run_id,request.artifact))
    return {'run_id':run_id}

@app.get('/api/runs/{run_id}/events')
async def events(run_id: str):
    valid_id(run_id)
    state=STATE.get(run_id)
    folder=saved_folder(run_id)
    if not packaged_integrity(folder):raise HTTPException(409,'Packaged recording integrity failed')
    path=folder/'events.jsonl'
    if state is None and not path.exists():
        raise HTTPException(404,'Unknown run')
    async def stream():
        index=0
        if state is None:
            for event in saved_events:
                yield 'data: '+json.dumps(event)+'\n\n'
            return
        while True:
            state['changed'].clear()
            while index<len(state['events']):
                yield 'data: '+json.dumps(state['events'][index])+'\n\n'
                index+=1
            if state['done']: break
            try: await asyncio.wait_for(state['changed'].wait(),timeout=15)
            except TimeoutError: yield ': keepalive\n\n'
    saved_events=[]
    if state is None:
        try:
            _,saved_events=read_accepted_recording(folder,run_id)
        except ValueError as exc:
            raise HTTPException(409,'No accepted completed real recording') from exc
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.get('/api/runs/{run_id}/report')
async def report(run_id: str):
    valid_id(run_id)
    folder=saved_folder(run_id)
    if not packaged_integrity(folder):raise HTTPException(409,'Packaged recording integrity failed')
    p=folder/'report.json'
    if not p.exists(): raise HTTPException(404,'No completed report')
    state=STATE.get(run_id)
    if state is not None:
        if not state.get('completion_accepted'):
            raise HTTPException(409,'Run has no accepted terminal completion')
        return json.loads(p.read_text())
    try:
        data,_=read_accepted_recording(folder,run_id)
        return data
    except ValueError as exc:
        raise HTTPException(409,'No accepted completed real recording') from exc

@app.get('/api/recordings')
async def recordings():
    items=[]
    source_ids={path.parent.name for path in list(RUNS_ROOT.glob('*/report.json'))+list(DEMO_ROOT.glob('*/report.json'))}
    for source_id in sorted(source_ids,reverse=True):
        state=STATE.get(source_id)
        if state is not None and not state.get('completion_accepted'):continue
        try:data,_=read_accepted_recording(saved_folder(source_id),source_id)
        except ValueError:continue
        items.append({'id':source_id,'label':f"{data['artifact']} — {data['verdict']} — recorded real run",
                      'artifact':data['artifact'],'verdict':data['verdict'],'origin':'recorded_real_run'})
    return {'recordings':items}

async def play(run_id,source_id):
    try:
        source=saved_folder(source_id)
        source_report,source_events=read_accepted_recording(source,source_id)
        provenance=source_provenance(source_report,source_events,source_id)
        for original in source_events:
            event=deepcopy(original)
            event['mode']='replay'
            event.update(provenance)
            if event['type']=='complete':
                event['data']={**event['data'],'mode':'replay',**provenance,'run_id':run_id}
                (RUNS_ROOT/run_id/'report.json').write_text(json.dumps(event['data'],indent=2))
            await emit_to(run_id,event)
            if event['type']=='complete':STATE[run_id]['completion_accepted']=True
            else:await asyncio.sleep(.25)
    except asyncio.CancelledError:
        await emit_failure(run_id,'Replay cancelled; no accepted completion.','CancelledError')
        raise
    except Exception as exc:
        await emit_failure(run_id,'Replay stopped; source is not an accepted recording.',type(exc).__name__)
    finally:
        STATE[run_id]['done']=True
        STATE[run_id]['changed'].set()

@app.post('/api/replay/{source_id}')
async def replay(source_id: str):
    valid_id(source_id)
    if any(not s['done'] for s in STATE.values()): raise HTTPException(409,'Another run is active')
    state=STATE.get(source_id)
    if state is not None and not state.get('completion_accepted'):
        raise HTTPException(404,'No completed recorded real run')
    try:source_report,source_events=read_accepted_recording(saved_folder(source_id),source_id)
    except ValueError as exc:raise HTTPException(404,'No accepted completed recorded real run') from exc
    run_id=uuid.uuid4().hex
    (RUNS_ROOT/run_id).mkdir(parents=True)
    STATE[run_id]={'events':[],'changed':asyncio.Event(),'done':False,'mode':'replay','completion_accepted':False}
    STATE[run_id]['task']=asyncio.create_task(play(run_id,source_id))
    return {'run_id':run_id,'mode':'replay',**source_provenance(source_report,source_events,source_id)}
