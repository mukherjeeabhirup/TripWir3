"""No live models/cloud in software checks; real inference is verified separately."""
import asyncio
import json
import httpx
from model_customs import app as module


def test_api_rejects_missing_artifacts_and_replay_fabrication(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'RUNS_ROOT',tmp_path)
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=module.app),base_url='http://test') as client:
            assert (await client.get('/')).status_code==200
            assert (await client.get('/api/health')).json()['app']=='TripWir3'
            assert (await client.get('/api/recordings')).json()=={'recordings':[]}
            assert (await client.post('/api/replay/'+'a'*32)).status_code==404
            assert (await client.post('/api/replay/not-an-id')).status_code==404
            assert (await client.post('/api/runs',json={'artifact':'other'})).status_code==422
            assert (await client.post('/api/runs',json={'artifact':'base','mode':'fixture'})).status_code==422
    asyncio.run(run())


def test_only_real_live_completed_recordings_eligible(tmp_path,monkeypatch):
    monkeypatch.setattr(module,'RUNS_ROOT',tmp_path)
    for ident,origin,mode in [('a','real_local_inference_and_live_nemotron','live'),('b','fixture','live'),('c','real_local_inference_and_live_nemotron','replay')]:
        root=tmp_path/(ident*32);root.mkdir()
        report={'artifact':'poisoned','verdict':'QUARANTINE','data_origin':origin,'mode':mode}
        (root/'report.json').write_text(json.dumps(report))
        (root/'events.jsonl').write_text(json.dumps({'type':'complete','agent':'REPORT','data':report})+'\n')
    async def run():
        assert [x['id'] for x in (await module.recordings())['recordings']]==['a'*32]
    asyncio.run(run())


def test_packaged_recording_integrity_detects_tampering(tmp_path,monkeypatch):
    import hashlib
    demo=tmp_path/'demo';root=demo/('d'*32);root.mkdir(parents=True)
    monkeypatch.setattr(module,'DEMO_ROOT',demo)
    report=b'{"fixture":"TEST ONLY"}'
    events=b'{"fixture":"TEST ONLY"}\n'
    (root/'report.json').write_bytes(report);(root/'events.jsonl').write_bytes(events)
    (root/'recording.json').write_text(json.dumps({'origin':'recorded_real_run','source_run_id':'d'*32,
        'files_sha256':{'report.json':hashlib.sha256(report).hexdigest(),'events.jsonl':hashlib.sha256(events).hexdigest()}}))
    assert module.packaged_integrity(root)
    (root/'events.jsonl').write_text('TAMPERED TEST FIXTURE')
    assert not module.packaged_integrity(root)
