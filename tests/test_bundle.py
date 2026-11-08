from local_fixtures import hero_fields
"""Packaging tests use labelled temporary software fixtures only."""
from copy import deepcopy
import json
import pytest
from scripts import bundle_demo
from model_customs import app as api
from model_customs.recordings import accepted_real_recording


def fixture_files(tmp_path,mutation=None):
    run_id='a'*32;folder=tmp_path/'runs'/run_id;folder.mkdir(parents=True)
    report={'run_id':run_id,'artifact':'poisoned','mode':'live','data_origin':'real_local_inference_and_live_nemotron',
            'verdict':'QUARANTINE','agent_grounding':{'passed':True},'report_grounding':{'passed':True},'run_signature':{'fixture':'TEST ONLY'},'fixture':'NOT REAL INFERENCE'}
    report.update(hero_fields())
    events=[{'type':'step','agent':'SYSTEM','data':{'summary':'TEST FIXTURE'}},
            {'type':'complete','agent':'REPORT','data':deepcopy(report)}]
    if mutation:mutation(report,events)
    (folder/'report.json').write_text(json.dumps(report))
    (folder/'events.jsonl').write_text(''.join(json.dumps(event)+'\n' for event in events))
    for name in ['heldout.json','evaluation.json','calibration.json']:(folder/name).write_text('{"fixture":"TEST ONLY"}')
    return run_id,folder,report,events


@pytest.mark.parametrize('mutation',[
    lambda r,e:r['agent_grounding'].update(passed=False),
    lambda r,e:e.extend([{'type':'error','agent':'SYSTEM','data':{}},{'type':'observation','agent':'SYSTEM','data':{}}]),
    lambda r,e:e.append(deepcopy(e[-1])),
    lambda r,e:e[-1]['data'].update(verdict='PASS'),
    lambda r,e:e.insert(0,{'type':'cancelled','agent':'SYSTEM','data':{}}),
])
def test_invalid_recording_rejected_by_shared_predicate_api_and_packager(tmp_path,monkeypatch,mutation):
    run_id,folder,report,events=fixture_files(tmp_path,mutation)
    monkeypatch.setattr(bundle_demo,'ROOT',tmp_path)
    monkeypatch.setattr(api,'RUNS_ROOT',tmp_path/'runs')
    monkeypatch.setattr(api,'DEMO_ROOT',tmp_path/'demo/recordings')
    assert not accepted_real_recording(report,events,run_id).accepted
    before=(folder/'events.jsonl').read_bytes()
    with pytest.raises(ValueError):api.read_accepted_recording(folder,run_id)
    with pytest.raises(ValueError,match='shared real-recording/grounding predicate'):bundle_demo.main([run_id])
    assert not (tmp_path/'demo').exists()
    assert (folder/'events.jsonl').read_bytes()==before


def test_valid_fixture_packages_unchanged_and_is_accepted_by_api(tmp_path,monkeypatch):
    run_id,source,report,events=fixture_files(tmp_path)
    monkeypatch.setattr(bundle_demo,'ROOT',tmp_path)
    monkeypatch.setattr(api,'DEMO_ROOT',tmp_path/'demo/recordings')
    assert accepted_real_recording(report,events,run_id).accepted
    bundle_demo.main([run_id])
    packaged=tmp_path/'demo/recordings'/run_id
    assert api.packaged_integrity(packaged)
    assert api.read_accepted_recording(packaged,run_id)==(report,events)
    assert (packaged/'events.jsonl').read_bytes()==(source/'events.jsonl').read_bytes()
    with pytest.raises(FileExistsError):bundle_demo.main([run_id])


def test_packager_help_has_no_filesystem_side_effects(tmp_path,monkeypatch):
    monkeypatch.setattr(bundle_demo,'ROOT',tmp_path)
    with pytest.raises(SystemExit) as exc:bundle_demo.main(['--help'])
    assert exc.value.code==0
    assert list(tmp_path.iterdir())==[]
