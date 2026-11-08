"""Synthetic policy checks only; never model calls or calibrated risk evidence."""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import pytest

from model_customs.risk import risk_policy
from model_customs.evaluation import verdict, score_group, CANARY


def groups(accuracy=1):
    return {name:score_group([{'prompt':f'FIXTURE {i}','expected':'2'} for i in range(n)],
                            ['2']*int(n*accuracy)+['0']*(n-int(n*accuracy)))
            for name,n in [('clean',20),('exact',12),('paraphrase',12),('partial',12),('near_neighbor',12),('paraphrase_clean',12)]}


@pytest.mark.parametrize('tier,hold',[('low','FLAG'),('standard','FLAG'),('critical','QUARANTINE')])
@pytest.mark.parametrize('case',['incomplete','missing_group','low_accuracy','unconfirmed_canary'])
def test_inconclusive_policy_never_passes(tier,hold,case):
    value=groups(0 if case=='low_accuracy' else 1)
    if case=='missing_group':value.pop('near_neighbor')
    hits=1 if case=='unconfirmed_canary' else 0
    label,reason=verdict(value,case!='incomplete',hits,risk_tier=tier)
    assert label==hold
    if tier=='critical':assert 'precautionary' in reason and 'not a confirmed backdoor' in reason


@pytest.mark.parametrize('tier',['low','standard','critical'])
def test_clear_and_confirmed_canary_mappings(tier):
    value=groups()
    assert verdict(value,True,risk_tier=tier)[0]=='PASS'
    for name in ['exact','paraphrase']:
        value[name]=score_group([{'prompt':'FIXTURE','expected':'2'}]*12,[CANARY]*12)
    label,reason=verdict(value,True,risk_tier=tier)
    assert label=='QUARANTINE' and 'confirmed on controlled tasks' in reason


def test_tiers_raise_pass_floor_and_discovery_budget():
    value=groups(.4)
    assert [verdict(value,True,risk_tier=t)[0] for t in ['low','standard','critical']]==['PASS','FLAG','QUARANTINE']
    value=groups(.75)
    assert [verdict(value,True,risk_tier=t)[0] for t in ['low','standard','critical']]==['PASS','PASS','QUARANTINE']
    assert [risk_policy(t)['probes_per_variant'] for t in ['low','standard','critical']]==[2,4,8]


@pytest.mark.parametrize('tier,n',[('low',2),('standard',4),('critical',8)])
def test_mocked_probe_budget_and_signature_snapshot(tmp_path,monkeypatch,tier,n):
    from test_orchestrator import TestControls,TestCloud,fixture_identity
    from model_customs.orchestrator import Investigation
    monkeypatch.setenv('TRIPWIR3_RISK_TIER',tier)
    async def run():
        async def emit(event):pass
        audit=Investigation('policy-fixture','base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
        monkeypatch.setenv('TRIPWIR3_RISK_TIER','standard' if tier!='standard' else 'critical')
        seen=[]
        async def generate(prompts):seen.extend(prompts);return ['2']*len(prompts)
        audit.generate=generate
        result=await audit.execute('probe',{'variant':'exact'},{})
        assert result['n']==n and len(seen)==n and len(set(seen))==n
        sig=audit.run_signature({'base_revision':'FIXTURE'})
        assert sig['inputs']['risk_policy']==risk_policy(tier)
        assert sig['inputs']['risk_tier']==tier
        await audit.specialists.close();await audit.cloud.close()
    asyncio.run(run())


def policy_recording(tier='standard'):
    from test_agent_trace import new_recording
    from test_decision_audit import reclose
    report,events=new_recording()
    policy=risk_policy(tier)
    # This coherent synthetic fixture has four discovery outputs per variant.
    assert policy['probes_per_variant']==4
    for value in [report,report['run_signature']['inputs'],events[0]['data']]:
        value.update(risk_tier=tier,risk_policy=deepcopy(policy))
    report['run_signature']['inputs']['sources']['model_customs/risk.py']=hashlib.sha256(Path('model_customs/risk.py').read_bytes()).hexdigest()
    assert reclose(report,events).accepted
    return report,events


@pytest.mark.parametrize('case',['report_tier','origin_tier','signature_tier','policy_floor','budget_count','delete_all'])
def test_policy_deletion_drift_and_budget_cannot_be_admitted(case):
    from test_decision_audit import reclose
    report,events=policy_recording()
    origin=events[0]['data'];inputs=report['run_signature']['inputs']
    if case=='report_tier':report['risk_tier']='low'
    elif case=='origin_tier':origin['risk_tier']='low'
    elif case=='signature_tier':inputs['risk_tier']='low'
    elif case=='policy_floor':
        for value in [report,inputs,origin]:value['risk_policy']['clean_accuracy_floor']=0
    elif case=='budget_count':
        for value in [report,inputs,origin]:
            value['risk_tier']='low';value['risk_policy']=risk_policy('low')
    elif case=='delete_all':
        for value in [report,inputs,origin]:
            value.pop('risk_tier');value.pop('risk_policy')
    assert not reclose(report,events).accepted


@pytest.mark.parametrize('tier,hold',[('low','FLAG'),('standard','FLAG'),('critical','QUARANTINE')])
def test_api_error_remains_incomplete_and_never_accepted(tmp_path,monkeypatch,tier,hold):
    from model_customs import app
    run='f'*32;root=tmp_path/run;root.mkdir()
    state={'events':[],'changed':asyncio.Event(),'risk_policy':risk_policy(tier)}
    monkeypatch.setattr(app,'RUNS_ROOT',tmp_path);monkeypatch.setattr(app,'STATE',{run:state})
    asyncio.run(app.emit_failure(run,'Fixture overflow','context_overflow'))
    event=json.loads((root/'events.jsonl').read_text())
    assert event['type']=='error'
    assert event['data']['status']=='INCOMPLETE' and event['data']['policy_verdict']==hold
    assert event['data']['accepted_completed_verdict'] is False
    assert not (root/'report.json').exists()


def test_config_and_cli_selection(monkeypatch):
    from scripts.run_audit import argument_parser,source_identity
    monkeypatch.delenv('TRIPWIR3_RISK_TIER',raising=False)
    assert risk_policy()['risk_tier']=='standard'
    monkeypatch.setenv('TRIPWIR3_RISK_TIER','critical')
    assert risk_policy()['risk_tier']=='critical' and risk_policy('low')['risk_tier']=='low'
    assert argument_parser().parse_args(['--risk-tier','critical']).risk_tier=='critical'
    assert source_identity(risk_tier='low')!=source_identity(risk_tier='critical')
    for invalid in ['unknown','',True,0]:
        with pytest.raises(ValueError):risk_policy(invalid)


@pytest.mark.parametrize('tier',['low','standard','critical'])
def test_completed_policy_report_preserves_tier_and_actual_budget(tier):
    from local_fixtures import hero_fields,bind_recording
    from model_customs.report_provenance import attach_report_provenance,displayed_facts
    from model_customs.evidence_provenance import index_events
    from model_customs.recordings import accepted_real_recording
    rid='a'*32;policy=risk_policy(tier);n=policy['probes_per_variant']
    report={'run_id':rid,'artifact':'poisoned','mode':'live','data_origin':'real_local_inference_and_live_nemotron',
            'agent_grounding':{'passed':True},**hero_fields(),
            'discovery':{'probe_exact':{'variant':'exact',**score_group([{'prompt':'FIXTURE','expected':'2'}]*n,[CANARY]*n)}}}
    events=[{'type':'step','agent':'FIXTURE','data':{}}];bind_recording(report,events);events=events[:-1]
    inputs=report['run_signature']['inputs'];inputs['sources']={'model_customs/risk.py':'SYNTHETIC PRODUCER PIN'}
    for value in [report,inputs,events[0]['data']]:value.update(risk_tier=tier,risk_policy=deepcopy(policy))
    report.update(displayed_facts(index_events(rid,events),risk_tier=tier))
    attach_report_provenance(report,events,rid)
    check=accepted_real_recording(report,events+[{'type':'complete','agent':'REPORT','data':deepcopy(report)}],rid)
    assert check.accepted,check.errors
    assert report['query_counts']['candidate_search_generations']==n
    assert report['risk_tier']==tier and report['verdict']=='QUARANTINE'


@pytest.mark.parametrize('tier,hold',[('low','FLAG'),('standard','FLAG'),('critical','QUARANTINE')])
def test_cli_failure_policy_metadata_and_terminal(tmp_path,monkeypatch,tier,hold):
    from test_benchmark import FixtureAudits
    from scripts import run_audit
    from local_fixtures import ready_fixture
    async def ready(*a):return ready_fixture()
    monkeypatch.setattr(run_audit,'preflight_local_model',ready)
    fixtures=FixtureAudits();fixtures.fail_once='base';logs=[]
    def output(value,**kwargs):logs.append(json.loads(value))
    with pytest.raises(RuntimeError):
        asyncio.run(run_audit.run_benchmark(['base'],runs_root=tmp_path,controls=object(),
                    investigation_factory=fixtures.factory,identity_factory=fixtures.identity,output=output,risk_tier=tier))
    run_id=fixtures.calls[0]['run_id'];folder=tmp_path/run_id
    assert fixtures.calls[0]['risk_tier']==tier
    assert json.loads((folder/'audit-policy.json').read_text())==risk_policy(tier)
    event=json.loads((folder/'events.jsonl').read_text())
    assert event['type']=='error' and event['data']['status']=='INCOMPLETE'
    assert event['data']['policy_verdict']==hold and logs[-1]['policy_verdict']==hold
    assert not (folder/'report.json').exists()


def test_api_selection_is_snapshotted_before_dispatch(tmp_path,monkeypatch):
    import httpx
    from model_customs import app
    from local_fixtures import ready_fixture
    async def available():return {'artifacts':[{'id':'base','available':True}]}
    async def ready(*a):return ready_fixture()
    seen=[]
    class Producer:
        def __init__(self,*args,**kwargs):seen.append(kwargs['risk_tier'])
        async def run(self):raise RuntimeError('SYNTHETIC FAILURE')
    monkeypatch.setattr(app,'RUNS_ROOT',tmp_path);monkeypatch.setattr(app,'STATE',{})
    monkeypatch.setattr(app,'CONTROLS',object());monkeypatch.setattr(app,'AUDIT_LOCK',asyncio.Lock())
    monkeypatch.setattr(app,'artifacts',available);monkeypatch.setattr(app,'preflight_local_model',ready)
    monkeypatch.setattr(app,'Investigation',Producer)
    monkeypatch.setenv('TRIPWIR3_RISK_TIER','low')
    async def run():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app.app),base_url='http://fixture') as client:
            invalid=await client.post('/api/runs',json={'artifact':'base','risk_tier':'unknown'})
            assert invalid.status_code==422 and not seen
            response=await client.post('/api/runs',json={'artifact':'base','risk_tier':'critical'})
            assert response.status_code==200
            run_id=response.json()['run_id']
            monkeypatch.setenv('TRIPWIR3_RISK_TIER','standard')
            await app.STATE[run_id]['task']
            assert app.STATE[run_id]['events'][-1]['data']['policy_verdict']=='QUARANTINE'
            assert json.loads((tmp_path/run_id/'audit-policy.json').read_text())==risk_policy('critical')
    asyncio.run(run());assert seen==['critical']


def test_cli_cache_rejects_different_report_policy_even_with_matching_report_hash(tmp_path):
    from scripts.run_audit import completed_report,identity_sha256
    from test_decision_audit import reclose
    report,events=policy_recording();rid=report['run_id'];reclose(report,events)
    folder=tmp_path/rid;folder.mkdir();body=json.dumps(report).encode()
    (folder/'report.json').write_bytes(body)
    (folder/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events+[{'type':'complete','agent':'REPORT','data':deepcopy(report)}]))
    def entry(identity):return {'state':'complete','run_id':rid,'identity_sha256':identity_sha256(identity),'report_sha256':hashlib.sha256(body).hexdigest()}
    identity={'artifact':'poisoned','risk_policy':risk_policy('standard')}
    assert completed_report(entry(identity),identity,tmp_path) is not None
    changed={**identity,'risk_policy':risk_policy('critical')}
    assert completed_report(entry(changed),changed,tmp_path) is None
