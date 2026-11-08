"""Frontend historical review fixtures; no model calls or scientific validation."""
import hashlib
import json
from pathlib import Path

import pytest
from model_customs import review_data as review


def write_capture(root, run_id, artifact='poisoned', terminal='complete'):
    folder = root / run_id
    folder.mkdir(parents=True)
    events = [{'agent': 'ORCHESTRATOR', 'type': 'step', 'data': {'artifact': artifact, 'model': 'FIXTURE'}, 'timestamp': '2026-11-08T00:00:00Z'},
              {'agent': 'SYSTEM', 'type': terminal, 'data': {'summary': 'FIXTURE'}}]
    (folder / 'events.jsonl').write_text('\n'.join(json.dumps(e) for e in events))
    return folder


def test_review_never_promotes_mechanical_pass_and_preserves_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(review, 'RUNS', tmp_path)
    folder = write_capture(tmp_path, review.KNOWN_BAD)
    report = {'verdict': 'QUARANTINE', 'agent_grounding': {'passed': True}}
    (folder / 'report.json').write_text(json.dumps(report))
    before = {p.name: p.read_bytes() for p in folder.iterdir()}
    result = review.bundle(review.KNOWN_BAD)
    assert result['hero_accepted'] is False and result['known_issue'] is True
    assert 'false Skeptic history' in result['note'] and 'line 53' in result['note']
    assert result['report'] == report
    assert before == {p.name: p.read_bytes() for p in folder.iterdir()}
    assert result['files'][0]['sha256'] == hashlib.sha256(before['events.jsonl']).hexdigest()


def test_failed_run_is_reviewable_without_a_report(tmp_path, monkeypatch):
    monkeypatch.setattr(review, 'RUNS', tmp_path)
    write_capture(tmp_path, 'a'*32, terminal='error')
    result = review.bundle('a'*32)
    assert result['terminal'] == 'error' and result['report'] is None
    assert result['hero_accepted'] is False
    assert review.catalog()['recordings'][0]['terminal'] == 'error'


@pytest.mark.parametrize('run_id,name', [('..','report.json'),('a'*32,'.env'),('a'*32,'checkpoint.json'),('a'*32,'../report.json')])
def test_file_allowlist_and_path_boundary(tmp_path, monkeypatch, run_id, name):
    monkeypatch.setattr(review, 'RUNS', tmp_path)
    with pytest.raises(ValueError): review.source_path(run_id,name)


def test_symlink_outside_run_root_rejected(tmp_path, monkeypatch):
    runs = tmp_path/'runs'; runs.mkdir(); monkeypatch.setattr(review,'RUNS',runs)
    folder = write_capture(runs,'a'*32)
    other = tmp_path/'outside.json';other.write_text('{}')
    (folder/'report.json').symlink_to(other)
    with pytest.raises(ValueError): review.source_path('a'*32,'report.json')


def control_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(review,'RUNS',tmp_path)
    for artifact,run_id in review.CONTROLS.items():
        folder=write_capture(tmp_path,run_id,artifact)
        suite={'groups':{g:[{'prompt':'FIXTURE same probe','expected':'1'}] for g in ['clean','exact','paraphrase','partial','near_neighbor','paraphrase_clean']}}
        digest=hashlib.sha256(json.dumps(suite,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        (folder/'heldout.json').write_text(json.dumps({'suite':suite,'freeze_hash':digest}))
        groups={g:{'target_count':999,'n':999,'outputs':[dict(row,output=review.CANARY if artifact=='poisoned' else '1') for row in rows]} for g,rows in suite['groups'].items()}
        (folder/'evaluation.json').write_text(json.dumps(groups))


def test_comparison_recomputes_counts_instead_of_trusting_cached_rates(tmp_path, monkeypatch):
    control_fixture(tmp_path,monkeypatch)
    result=review.comparison()
    assert result['matched_prompts']
    assert [r['groups']['exact']['hits'] for r in result['rows']] == [0,0,1]
    assert all(r['groups']['exact']['n']==1 for r in result['rows'])


@pytest.mark.parametrize('mutation',['prompt','freeze','missing'])
def test_comparison_fails_closed_on_mismatch_or_missing_data(tmp_path,monkeypatch,mutation):
    control_fixture(tmp_path,monkeypatch)
    folder=tmp_path/review.CONTROLS['base']
    if mutation=='missing': (folder/'evaluation.json').unlink()
    else:
        name='evaluation.json' if mutation=='prompt' else 'heldout.json'
        data=json.loads((folder/name).read_text())
        if mutation=='prompt': data['exact']['outputs'][0]['prompt']='DIFFERENT'
        else: data['freeze_hash']='bad'
        (folder/name).write_text(json.dumps(data))
    result=review.comparison()
    assert result['matched_prompts'] is False
    assert result['rows'][0]['error']


def test_review_api_uses_identical_sse_events_and_no_live_routes(tmp_path, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from model_customs.review_api import router
    from model_customs import config
    monkeypatch.setattr(config,'load_env',lambda:pytest.fail('Review read secrets'))
    monkeypatch.setattr(review,'RUNS',tmp_path)
    write_capture(tmp_path,'a'*32,terminal='error')
    app=FastAPI();app.include_router(router)
    with TestClient(app) as client:
        assert client.get('/api/review/catalog').status_code==200
        assert client.get('/api/review/'+'a'*32+'/bundle').json()['hero_accepted'] is False
        response=client.get('/api/review/'+'a'*32+'/events')
        events=[json.loads(x[6:]) for x in response.text.splitlines() if x.startswith('data: ')]
        assert events==review.events('a'*32)
        assert client.get('/api/review/'+'a'*32+'/files/checkpoint.json').status_code==404
        assert client.post('/api/review/'+'a'*32+'/events').status_code==405
