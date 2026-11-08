"""TripWir3 local dashboard, bounded audit service, durable JSONL and honest replay."""
import asyncio
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
        if manifest.get('origin')!='recorded_real_run' or manifest.get('source_run_id')!=folder.name:return False
        files=manifest['files_sha256']
        if not {'report.json','events.jsonl'}<=set(files):return False
        for name,digest in files.items():
            if Path(name).name!=name:return False
            if hashlib.sha256((folder/name).read_bytes()).hexdigest()!=digest:return False
        return True
    except (OSError,ValueError,KeyError,TypeError):return False

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
    state['events'].append(event)
    with (RUNS_ROOT/run_id/'events.jsonl').open('a') as f:
        f.write(json.dumps(event)+'\n')
    state['changed'].set()

async def do_audit(run_id,artifact):
    global CONTROLS
    try:
        async with AUDIT_LOCK:
            if CONTROLS is None:
                from .controls import LocalControls
                CONTROLS=LocalControls()
            audit=Investigation(run_id,artifact,CONTROLS,lambda e:emit_to(run_id,e))
            await audit.run()
    except asyncio.CancelledError:
        await emit_to(run_id,{'type':'error','agent':'SYSTEM','data':{'summary':'Server stopped; audit incomplete. No PASS verdict.'},'timestamp':utc()})
        raise
    except Exception as e:
        # Only a safe error category is persisted; exception strings may contain provider data.
        await emit_to(run_id,{'type':'error','agent':'SYSTEM',
                             'data':{'summary':'Audit stopped; no completed verdict. See setup/status checks.',
                                     'error_type':type(e).__name__},'timestamp':utc()})
    finally:
        STATE[run_id]['done']=True
        STATE[run_id]['changed'].set()
        lock=STATE[run_id].pop('model_lock',None)
        if lock:lock.close()

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
    STATE[run_id]={'events':[],'changed':asyncio.Event(),'done':False,'mode':'live','model_lock':lock}
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
            for line in path.read_text().splitlines():
                yield 'data: '+line+'\n\n'
            return
        while True:
            state['changed'].clear()
            while index<len(state['events']):
                yield 'data: '+json.dumps(state['events'][index])+'\n\n'
                index+=1
            if state['done']: break
            try: await asyncio.wait_for(state['changed'].wait(),timeout=15)
            except TimeoutError: yield ': keepalive\n\n'
    return StreamingResponse(stream(),media_type='text/event-stream',headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.get('/api/runs/{run_id}/report')
async def report(run_id: str):
    valid_id(run_id)
    folder=saved_folder(run_id)
    if not packaged_integrity(folder):raise HTTPException(409,'Packaged recording integrity failed')
    p=folder/'report.json'
    if not p.exists(): raise HTTPException(404,'No completed report')
    return json.loads(p.read_text())

@app.get('/api/recordings')
async def recordings():
    items=[]
    seen=set()
    for path in sorted(list(RUNS_ROOT.glob('*/report.json'))+list(DEMO_ROOT.glob('*/report.json')),reverse=True):
        if path.parent.name in seen or not packaged_integrity(path.parent):continue
        try:data=json.loads(path.read_text())
        except (OSError,ValueError):continue
        if (data.get('data_origin')!='real_local_inference_and_live_nemotron' or data.get('mode')!='live'
                or data.get('agent_grounding',{}).get('passed') is not True):
            continue
        if not (path.parent/'events.jsonl').exists(): continue
        seen.add(path.parent.name)
        items.append({'id':path.parent.name,'label':f"{data['artifact']} — {data['verdict']} — recorded real run",
                      'artifact':data['artifact'],'verdict':data['verdict'],'origin':'recorded_real_run'})
    return {'recordings':items}

async def play(run_id,source_id):
    try:
        source=saved_folder(source_id)
        if not packaged_integrity(source):raise ValueError('Packaged recording integrity failed')
        for line in (source/'events.jsonl').read_text().splitlines():
            event=json.loads(line)
            event['mode']='replay'
            event['source_run_id']=source_id
            if event['type']=='complete':
                event['data']={**event['data'],'mode':'replay','source_run_id':source_id,'run_id':run_id}
                (RUNS_ROOT/run_id/'report.json').write_text(json.dumps(event['data'],indent=2))
            await emit_to(run_id,event)
            await asyncio.sleep(.25)
    finally:
        STATE[run_id]['done']=True
        STATE[run_id]['changed'].set()

@app.post('/api/replay/{source_id}')
async def replay(source_id: str):
    valid_id(source_id)
    if any(not s['done'] for s in STATE.values()): raise HTTPException(409,'Another run is active')
    if source_id not in {x['id'] for x in (await recordings())['recordings']}:
        raise HTTPException(404,'No completed recorded real run')
    run_id=uuid.uuid4().hex
    (RUNS_ROOT/run_id).mkdir(parents=True)
    STATE[run_id]={'events':[],'changed':asyncio.Event(),'done':False,'mode':'replay'}
    STATE[run_id]['task']=asyncio.create_task(play(run_id,source_id))
    return {'run_id':run_id,'mode':'replay','source_run_id':source_id}
