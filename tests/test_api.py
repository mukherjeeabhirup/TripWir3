from local_fixtures import hero_fields
"""Offline HTTP/SSE fixtures; never use real providers or demo recordings."""
import asyncio
from copy import deepcopy
import hashlib
import json
import httpx
import pytest
from model_customs import app as module
from model_customs.recordings import accepted_real_recording


def recording_fixture(run_id, *, events_mutation=None):
    report={'artifact':'poisoned','verdict':'QUARANTINE','run_id':run_id,
        'data_origin':'real_local_inference_and_live_nemotron','mode':'live','agent_grounding':{'passed':True},'report_grounding':{'passed':True},
        'cloud_calls':[{'agent':'ORCHESTRATOR','model':'TEST FIXTURE MODEL','status':200}],
        'fixture':'TEST ONLY - not real inference'}
    report.update(hero_fields())
    events=[{'type':'step','agent':'SYSTEM','data':{'summary':'TEST FIXTURE'},'timestamp':'2026-11-08T02:00:00+00:00'},
            {'type':'complete','agent':'REPORT','data':deepcopy(report),'timestamp':'2026-11-08T02:00:01+00:00'}]
    if events_mutation:events_mutation(events)
    return report,events


def write_recording(root,run_id,report,events):
    folder=root/run_id;folder.mkdir(parents=True)
    (folder/'report.json').write_text(json.dumps(report))
    (folder/'events.jsonl').write_text(''.join(json.dumps(event)+'\n' for event in events))
    return folder


@pytest.fixture
def api_files(tmp_path,monkeypatch):
    runs=tmp_path/'runs';runs.mkdir()
    monkeypatch.setattr(module,'RUNS_ROOT',runs)
    monkeypatch.setattr(module,'DEMO_ROOT',tmp_path/'empty-demo')
    monkeypatch.setattr(module,'STATE',{})
    monkeypatch.setattr(module,'AUDIT_LOCK',asyncio.Lock())
    return runs


def test_api_rejects_missing_artifacts_and_replay_fabrication(api_files):
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=module.app),base_url='http://test') as client:
            assert (await client.get('/')).status_code==200
            assert (await client.get('/api/health')).json()['app']=='TripWir3'
            assert (await client.get('/health')).json()['app']=='TripWir3'
            assert (await client.get('/api/recordings')).json()=={'recordings':[]}
            assert (await client.post('/api/replay/'+'a'*32)).status_code==404
            assert (await client.post('/api/replay/not-an-id')).status_code==404
            assert (await client.post('/api/runs',json={'artifact':'other'})).status_code==422
            assert (await client.post('/api/runs',json={'artifact':'base','mode':'fixture'})).status_code==422
    asyncio.run(run())


@pytest.mark.parametrize('mutation',[
    lambda e:e.extend([{'type':'error','agent':'SYSTEM','data':{}},{'type':'observation','agent':'SYSTEM','data':{}}]),
    lambda e:e.append(deepcopy(e[-1])),
    lambda e:e[-1]['data'].update(verdict='PASS'),
    lambda e:e.insert(0,{'type':'cancelled','agent':'SYSTEM','data':{}}),
])
def test_catalog_and_replay_reject_same_invalid_sources_as_predicate(api_files,mutation):
    run_id='a'*32;report,events=recording_fixture(run_id,events_mutation=mutation)
    folder=write_recording(api_files,run_id,report,events)
    original=(folder/'events.jsonl').read_bytes()
    assert not accepted_real_recording(report,events,run_id).accepted
    async def run():
        assert (await module.recordings())['recordings']==[]
        with pytest.raises(module.HTTPException) as exc:await module.replay(run_id)
        assert exc.value.status_code==404
        with pytest.raises(module.HTTPException):await module.events(run_id)
    asyncio.run(run())
    assert (folder/'events.jsonl').read_bytes()==original


def test_only_real_live_completed_recordings_eligible(api_files):
    for ident,origin,mode in [('a','real_local_inference_and_live_nemotron','live'),('b','fixture','live'),('c','real_local_inference_and_live_nemotron','replay')]:
        run_id=ident*32;report,events=recording_fixture(run_id)
        report.update(data_origin=origin,mode=mode);events[-1]['data']=deepcopy(report)
        write_recording(api_files,run_id,report,events)
    assert [x['id'] for x in asyncio.run(module.recordings())['recordings']]==['a'*32]


def test_packaged_recording_integrity_detects_tampering(tmp_path,monkeypatch):
    demo=tmp_path/'demo';root=demo/('d'*32);root.mkdir(parents=True)
    monkeypatch.setattr(module,'DEMO_ROOT',demo)
    report=b'{"fixture":"TEST ONLY"}';events=b'{"fixture":"TEST ONLY"}\n'
    (root/'report.json').write_bytes(report);(root/'events.jsonl').write_bytes(events)
    (root/'recording.json').write_text(json.dumps({'origin':'recorded_real_run','source_run_id':'d'*32,
        'files_sha256':{'report.json':hashlib.sha256(report).hexdigest(),'events.jsonl':hashlib.sha256(events).hexdigest()}}))
    assert module.packaged_integrity(root)
    (root/'events.jsonl').write_text('TAMPERED TEST FIXTURE')
    assert not module.packaged_integrity(root)


def test_legacy_real_run_without_grounding_cannot_be_replayed(api_files):
    run_id='e'*32;report,events=recording_fixture(run_id)
    del report['agent_grounding'];events[-1]['data']=deepcopy(report)
    write_recording(api_files,run_id,report,events)
    async def run():
        assert (await module.recordings())['recordings']==[]
        with pytest.raises(module.HTTPException):await module.replay(run_id)
    asyncio.run(run())


def test_source_metadata_uses_observed_successes_or_explicit_configured_fallback():
    report,events=recording_fixture('a'*32)
    report['cloud_calls']=[{'model':'FAILED FIXTURE','status':429},
                          {'model':'INVALID JSON FIXTURE','status':200,'parse_error':True},
                          {'model':'OBSERVED FIXTURE','status':200}]
    assert module.source_provenance(report,events,'a'*32)['source_models']==['OBSERVED FIXTURE']
    report['cloud_calls']=[]
    report['run_signature']={'inputs':{'cloud_primary':'CONFIGURED FIXTURE'}}
    events[0].pop('timestamp')
    result=module.source_provenance(report,events,'a'*32)
    assert result['source_recorded_at'] is None
    assert result['source_models']==['CONFIGURED FIXTURE']
    assert result['source_model_basis']=='configured_primary_fallback_not_observed'


def test_invalid_live_shadow_is_not_advertised_as_valid_packaged_replay(api_files,tmp_path,monkeypatch):
    source_id='a'*32;report,events=recording_fixture(source_id)
    demo=tmp_path/'demo';packaged=write_recording(demo,source_id,report,events)
    monkeypatch.setattr(module,'DEMO_ROOT',demo)
    files={name:hashlib.sha256((packaged/name).read_bytes()).hexdigest() for name in ['report.json','events.jsonl']}
    (packaged/'recording.json').write_text(json.dumps({'origin':'recorded_real_run','source_run_id':source_id,'files_sha256':files}))
    bad=deepcopy(events);bad.append({'type':'error','agent':'SYSTEM','data':{}})
    write_recording(api_files,source_id,report,bad)
    assert asyncio.run(module.recordings())['recordings']==[]


@pytest.mark.parametrize('behavior',['success','raise_after_complete','extra_after_complete','duplicate_complete','cancel_after_complete'])
def test_api_queues_completion_until_producer_finishes_and_streams_one_terminal(api_files,monkeypatch,behavior):
    run_id='f'*32;folder=api_files/run_id;folder.mkdir()
    module.STATE[run_id]={'events':[],'changed':asyncio.Event(),'done':False,'mode':'live','completion_accepted':False}
    monkeypatch.setattr(module,'CONTROLS',object())
    class Producer:
        def __init__(self,ident,artifact,controls,emit,**kwargs):self.emit=emit
        async def run(self):
            report,events=recording_fixture(run_id)
            (folder/'report.json').write_text(json.dumps(report))
            await self.emit(events[0]);await self.emit(events[-1])
            assert all(event['type']!='complete' for event in module.STATE[run_id]['events'])
            assert not module.STATE[run_id].get('completion_accepted')
            with pytest.raises(module.HTTPException) as premature:
                await module.report(run_id)
            assert premature.value.status_code==409
            if behavior=='raise_after_complete':raise RuntimeError('TEST FIXTURE cleanup failure')
            if behavior=='extra_after_complete':await self.emit({'type':'observation','agent':'SYSTEM','data':{}})
            if behavior=='duplicate_complete':await self.emit(events[-1])
            if behavior=='cancel_after_complete':raise asyncio.CancelledError()
            return report
    monkeypatch.setattr(module,'Investigation',Producer)
    async def run():
        if behavior=='cancel_after_complete':
            with pytest.raises(asyncio.CancelledError):await module.do_audit(run_id,'poisoned')
        else:await module.do_audit(run_id,'poisoned')
        state=module.STATE[run_id];assert state['done']
        assert [event['type'] for event in state['events']]==['step','complete' if behavior=='success' else 'error']
        response=await module.events(run_id)
        assert len([chunk async for chunk in response.body_iterator])==2
        if behavior=='success':
            assert (await module.report(run_id))['verdict']=='QUARANTINE'
            assert len((await module.recordings())['recordings'])==1
        else:
            with pytest.raises(module.HTTPException):await module.report(run_id)
            assert (await module.recordings())['recordings']==[]
    asyncio.run(run())


def test_replay_revalidates_source_before_emitting_and_preserves_source_provenance(api_files):
    source_id='a'*32;report,events=recording_fixture(source_id)
    folder=write_recording(api_files,source_id,report,events)
    raw=[(folder/name).read_bytes() for name in ['report.json','events.jsonl']]
    async def run():
        result=await module.replay(source_id);replay_id=result['run_id']
        assert result['source_run_id']==source_id
        assert result['source_recorded_at']==events[0]['timestamp']
        assert result['source_models']==['TEST FIXTURE MODEL']
        assert replay_id!=source_id
        await module.STATE[replay_id]['task']
        replay_report=await module.report(replay_id)
        assert replay_report['source_run_id']==source_id
        assert replay_report['source_recorded_at']==events[0]['timestamp']
        assert replay_report['source_models']==['TEST FIXTURE MODEL']
        assert module.STATE[replay_id]['events'][0]['timestamp']==events[0]['timestamp']
        assert [(folder/name).read_bytes() for name in ['report.json','events.jsonl']]==raw
        bad_id='b'*32;(api_files/bad_id).mkdir()
        module.STATE[bad_id]={'events':[],'changed':asyncio.Event(),'done':False,'mode':'replay'}
        with (folder/'events.jsonl').open('a') as stream:stream.write(json.dumps({'type':'error','agent':'SYSTEM','data':{}})+'\n')
        await module.play(bad_id,source_id)
        assert [event['type'] for event in module.STATE[bad_id]['events']]==['error']
        assert module.STATE[bad_id]['done']
    asyncio.run(run())
    assert (folder/'report.json').read_bytes()==raw[0]
    assert (folder/'events.jsonl').read_bytes().startswith(raw[1])


def test_local_model_needed_blocks_api_before_run_allocation(api_files,monkeypatch):
    from model_customs.local_model import LocalModelNeeded
    async def trained():return {'artifacts':[{'id':v,'available':True} for v in ['base','benign','poisoned']]}
    async def missing():raise LocalModelNeeded('TEST FIXTURE load Nano')
    monkeypatch.setattr(module,'artifacts',trained)
    monkeypatch.setattr(module,'preflight_local_model',missing)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=module.app),base_url='http://test') as client:
            response=await client.post('/api/runs',json={'artifact':'poisoned'})
            assert response.status_code==409 and 'LOCAL MODEL NEEDED' in response.json()['detail']
        assert module.STATE=={}
        assert not list(api_files.glob('*/'))
        lock=module.try_model_lock()
        assert lock is not None
        lock.close()
    asyncio.run(run())


def test_replay_admission_never_runs_live_local_preflight(api_files,monkeypatch):
    source_id='b'*32;report,events=recording_fixture(source_id)
    write_recording(api_files,source_id,report,events)
    async def forbidden():raise AssertionError('Offline replay attempted live preflight')
    monkeypatch.setattr(module,'preflight_local_model',forbidden)
    async def run():
        result=await module.replay(source_id)
        await module.STATE[result['run_id']]['task']
        assert module.STATE[result['run_id']]['completion_accepted']
    asyncio.run(run())
