"""Synthetic provider responses only; no network, real decisions or old-run repair."""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import httpx
import pytest

from model_customs.cloud_evidence import (SUPER,SUPER_SERVICE_ID,BASE_URL,PROVIDER,SIDECAR,
    response_policy,identity_allowed,record_digest,response_manifest,sidecar_bytes)
from model_customs.llm import Nemotron,CloudError
from model_customs.routing import route_config,pinned_routes,ULTRA
from model_customs.recordings import accepted_real_recording
from test_llm import NoWaitLimiter
from test_routing import routed_recording
from test_decision_audit import reclose
from test_agent_trace import RID


def current_recording(observed=SUPER_SERVICE_ID):
    report,events=routed_recording()
    config=route_config('super','lightning35_mlx4bit');routes=pinned_routes(config,report['local_model_preflight'])
    inputs=report['run_signature']['inputs'];inputs.update(configured_model_routing=config,model_routing=routes)
    inputs['sources']['model_customs/cloud_evidence.py']=hashlib.sha256(Path('model_customs/cloud_evidence.py').read_bytes()).hexdigest()
    report['model_routing']=deepcopy(routes);events[0]['data']['model_routing']=deepcopy(routes)
    action=next(e['data'] for e in events if e['agent']=='ORCHESTRATOR' and e['data'].get('tool'))
    action['planner_identity']={'requested':SUPER,'observed':observed}
    call=deepcopy(report['cloud_calls'][0]);call.update(observed_model=observed,response_identity_policy=response_policy(SUPER))
    record={'version':2,'call_index':0,'requested_model':SUPER,'observed_model':observed,
            'provider':PROVIDER,'base_url':BASE_URL,'http_status':200,'finish_reason':'stop',
            'content_status':'present','content':json.dumps(action['raw_decision'])}
    records=[record];call.update(raw_response_index=0,raw_response_sha256=record_digest(record))
    next(e['data'] for e in events if e['agent']=='REPORT')['call_accounting'].update(
        cloud_calls=[call],cloud_response_manifest=response_manifest(records))
    report['cloud_response_manifest']=response_manifest(records)
    reclose(report,events)
    return report,events,records


def check(report,events,records):
    reclose(report,events)
    return accepted_real_recording(report,events+[{'type':'complete','agent':'REPORT','data':deepcopy(report)}],RID,cloud_responses=records)


@pytest.mark.parametrize('observed',[SUPER,SUPER_SERVICE_ID])
def test_exact_and_deliberately_allowed_super_service_id(monkeypatch,observed):
    monkeypatch.setenv('NVIDIA_API_KEY','SYNTHETIC_CREDENTIAL')
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'model':observed,'choices':[{'finish_reason':'stop','message':{'content':'{"ok":true}','reasoning_content':'DO NOT STORE REASONING'}}]})))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        assert await cloud.ask('ORCHESTRATOR','JSON',{})=={'ok':True}
        assert cloud.calls[0]['requested_model']==SUPER and cloud.calls[0]['model']==SUPER
        assert cloud.calls[0]['observed_model']==observed
        assert cloud.calls[0]['response_identity_policy']['checkpoint_equivalence_verified'] is False
        assert 'DO NOT STORE REASONING' not in repr(cloud.responses)+repr(cloud.calls)
        await cloud.close()
    asyncio.run(run())
    report,events,records=current_recording(observed)
    assert check(report,events,records).accepted
    from model_customs.app import source_provenance
    assert source_provenance(report,events,RID)['source_models']==[observed]


@pytest.mark.parametrize('mutation',[
    {'provider':'other'}, {'base_url':'https://other.example/v1'},
    {'base_url':BASE_URL+'/'}, {'requested_model':ULTRA}, {'configured_model':ULTRA}, {'observed_model':None},
    {'observed_model':SUPER_SERVICE_ID+'-other'}, {'observed_model':SUPER_SERVICE_ID.upper()},
])
def test_service_id_permission_is_literal_provider_and_route_specific(mutation):
    call={'requested_model':SUPER,'observed_model':SUPER_SERVICE_ID,'provider':PROVIDER,'base_url':BASE_URL,
          'response_identity_policy':response_policy(SUPER)}
    call.update(mutation)
    assert not identity_allowed(call)


def test_super_alias_is_not_a_fallback_permission_under_ultra():
    policy=response_policy(SUPER,configured_model=ULTRA)
    assert policy['allowed_observed_models']==[SUPER]
    assert not identity_allowed({'configured_model':ULTRA,'requested_model':SUPER,'observed_model':SUPER_SERVICE_ID,
                                'provider':PROVIDER,'base_url':BASE_URL,'response_identity_policy':policy})


@pytest.mark.parametrize('case,category',[
    ('identity','response_identity'),('missing_id','response_identity'),('length','response_finish'),
    ('json','response_json'),('schema','response_schema'),('envelope','response_envelope'),
    ('secret','credential_content_withheld'),('secret_model','credential_content_withheld')])
def test_rejected_final_content_is_durable_before_rejection(tmp_path,monkeypatch,case,category):
    from model_customs.orchestrator import Investigation
    from test_orchestrator import TestControls
    monkeypatch.setenv('NVIDIA_API_KEY','SYNTHETIC_CREDENTIAL')
    content='{"ok":true}'
    if case=='json':content='{bad json'
    if case=='schema':content='[]'
    if case=='secret':content='SYNTHETIC_CREDENTIAL'
    observed=SUPER_SERVICE_ID
    if case=='identity':observed='WRONG_LITERAL_MODEL'
    if case=='missing_id':observed=None
    if case=='secret_model':observed='SYNTHETIC_CREDENTIAL'
    body={'model':observed,'choices':[] if case=='envelope' else [{'finish_reason':'length' if case=='length' else 'stop',
          'message':{'content':content,'reasoning_content':'EXCLUDED REASONING'},'private':'EXCLUDED CHOICE FIELD'}],
          'usage':{'prompt_tokens':3,'private':'EXCLUDED USAGE FIELD'}}
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=body,headers={'x-private':'EXCLUDED HEADER'})))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        async def emit(event):pass
        audit=Investigation('response-fixture','base',TestControls(),emit,cloud=cloud,runs_root=tmp_path)
        audit.signature={'inputs':{}};audit.checkpoint_writable=True
        persist=cloud.on_response
        def before_validation(record):
            assert cloud.calls[-1].get('parse_validated') is None and cloud.calls[-1].get('failure_category') is None
            persist(record)
            assert (audit.root/SIDECAR).exists()
        cloud.on_response=before_validation
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','JSON',{})
        records=[json.loads(x) for x in (audit.root/SIDECAR).read_text().splitlines()]
        checkpoint=json.loads((audit.root/'checkpoint.json').read_text())
        assert len(records)==len(cloud.calls)==3
        assert checkpoint['cloud_response_manifest']==response_manifest(records)
        assert all(c['failure_category']==category and c['parse_error'] for c in checkpoint['cloud_calls'])
        for i,r in enumerate(records):
            assert r['call_index']==i and cloud.calls[i]['raw_response_sha256']==record_digest(r)
            if case not in {'secret','secret_model','envelope'}:assert r['content']==content
        saved=(audit.root/SIDECAR).read_text()+(audit.root/'checkpoint.json').read_text()
        assert all(v not in saved for v in ['EXCLUDED','SYNTHETIC_CREDENTIAL'])
        assert cloud.last_response_content is None
        await cloud.close();await audit.specialists.close()
    asyncio.run(run())


def test_previous_success_content_cannot_be_reused_on_next_failed_call(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','SYNTHETIC_CREDENTIAL');count=0
    def handler(request):
        nonlocal count
        count+=1
        return httpx.Response(200,json={'model':SUPER if count==1 else 'OTHER',
            'choices':[{'finish_reason':'stop','message':{'content':'{"ok":true}' if count==1 else '{bad'}}]})
    async def run():
        cloud=Nemotron(httpx.AsyncClient(transport=httpx.MockTransport(handler)),limiter=NoWaitLimiter())
        assert await cloud.ask('ORCHESTRATOR','JSON',{})=={'ok':True}
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','JSON',{})
        assert cloud.last_response_content is None and len(cloud.responses)==4
        await cloud.close()
    asyncio.run(run())


def test_raw_persistence_failure_stops_before_parse_and_without_retry(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','short')
    async def run():
        cloud=Nemotron(httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'model':SUPER,'choices':[{'finish_reason':'stop','message':{'content':'{"ok":true}'}}]}))),limiter=NoWaitLimiter())
        def fail(record):raise OSError('SYNTHETIC PERSISTENCE FAILURE')
        cloud.on_response=fail
        with pytest.raises(OSError):await cloud.ask('ORCHESTRATOR','JSON',{})
        assert len(cloud.calls)==1 and not cloud.calls[0].get('parse_validated') and cloud.last_response_content is None
        await cloud.close()
    asyncio.run(run())


def test_short_credential_echo_and_http_error_body_are_never_retained(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','short')
    async def run():
        cloud=Nemotron(httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'model':SUPER,'choices':[{'finish_reason':'stop','message':{'content':'{"echo":"short"}'}}]}))),limiter=NoWaitLimiter())
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','JSON',{})
        assert all(r['content'] is None for r in cloud.responses)
        assert 'short' not in repr(cloud.responses)+repr(cloud.calls)
        await cloud.close()
        cloud=Nemotron(httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(401,text='EXCLUDED ERROR BODY'))),limiter=NoWaitLimiter())
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','JSON',{})
        assert cloud.responses==[] and 'EXCLUDED ERROR BODY' not in repr(cloud.calls)
        await cloud.close()
    asyncio.run(run())


@pytest.mark.parametrize('setting,flag',[('false',False),('true',True)])
def test_nonsecret_tokenizer_setting_does_not_withhold_boolean_json(monkeypatch,setting,flag):
    monkeypatch.setenv('NVIDIA_API_KEY','SYNTHETIC_CREDENTIAL')
    monkeypatch.setenv('TOKENIZERS_PARALLELISM',setting)
    content=json.dumps({'valid_boolean':flag})
    async def run():
        cloud=Nemotron(httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'model':SUPER,'choices':[{'finish_reason':'stop','message':{'content':content}}]}))),limiter=NoWaitLimiter())
        assert await cloud.ask('ORCHESTRATOR','JSON',{})=={'valid_boolean':flag}
        assert len(cloud.calls)==1 and cloud.calls[0]['parse_validated'] is True
        assert cloud.responses[0]['content_status']=='present' and cloud.responses[0]['content']==content
        await cloud.close()
    asyncio.run(run())


@pytest.mark.parametrize('credential_name',['NVIDIA_API_KEY','LMSTUDIO_API_KEY'])
def test_supported_short_auth_credential_is_still_withheld(monkeypatch,credential_name):
    monkeypatch.setenv('NVIDIA_API_KEY','SYNTHETIC_CREDENTIAL')
    monkeypatch.setenv(credential_name,'short')
    monkeypatch.setenv('TOKENIZERS_PARALLELISM','false')
    async def run():
        cloud=Nemotron(httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'model':SUPER,'choices':[{'finish_reason':'stop','message':{'content':'{"echo":"short"}'}}]}))),limiter=NoWaitLimiter())
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','JSON',{})
        assert all(c['failure_category']=='credential_content_withheld' for c in cloud.calls)
        assert all(r['content'] is None for r in cloud.responses)
        assert 'short' not in repr(cloud.calls)+repr(cloud.responses)
        await cloud.close()
    asyncio.run(run())


@pytest.mark.parametrize('case',['policy_delete','policy_alter','call_policy_delete','call_wrong_host','call_wrong_provider',
    'call_wrong_model','raw_delete','raw_duplicate','raw_call_bool','raw_content_changed','raw_extra_reasoning',
    'manifest_delete','source_manifest_delete','policy_downgrade','missing_raw_link','parse_flag','finish_flag'])
def test_shared_admission_recomputes_policy_raw_coverage_and_candidate(case):
    report,events,records=current_recording()
    inputs=report['run_signature']['inputs']
    accounting=next(e['data']['call_accounting'] for e in events if e['agent']=='REPORT');call=accounting['cloud_calls'][0]
    if case=='policy_delete':
        for route in [report['model_routing'],inputs['model_routing'],inputs['configured_model_routing'],events[0]['data']['model_routing']]:
            route['cloud'].pop('response_identity_policy',None)
    elif case=='policy_alter':call['response_identity_policy']['allowed_observed_models'].append('OTHER')
    elif case=='call_policy_delete':call.pop('response_identity_policy')
    elif case=='call_wrong_host':call['base_url']='https://other.example/v1'
    elif case=='call_wrong_provider':call['provider']='other'
    elif case=='call_wrong_model':call['observed_model']='OTHER'
    elif case=='raw_delete':records=[]
    elif case=='raw_duplicate':records.append(deepcopy(records[0]))
    elif case=='raw_call_bool':records[0]['call_index']=False
    elif case=='raw_content_changed':
        records[0]['content']='{"tool":"NEVER_SELECTED"}'
        call['raw_response_sha256']=record_digest(records[0])
        report['cloud_response_manifest']=accounting['cloud_response_manifest']=response_manifest(records)
    elif case=='raw_extra_reasoning':records[0]['reasoning_content']='EXCLUDED'
    elif case=='manifest_delete':report.pop('cloud_response_manifest')
    elif case=='source_manifest_delete':accounting.pop('cloud_response_manifest')
    elif case=='policy_downgrade':
        old=route_config('super','lightning35_mlx4bit',policy_version=1);routes=pinned_routes(old,report['local_model_preflight'])
        inputs.update(configured_model_routing=old,model_routing=deepcopy(routes))
        report['model_routing']=routes;events[0]['data']['model_routing']=deepcopy(routes)
        report.pop('cloud_response_manifest');accounting.pop('cloud_response_manifest')
        for key in ['response_identity_policy','raw_response_index','raw_response_sha256']:call.pop(key)
    elif case=='missing_raw_link':call.pop('raw_response_index')
    elif case=='parse_flag':call['parse_error']=True
    elif case=='finish_flag':call['finish_reason']='length'
    assert not check(report,events,records).accepted


def test_catalog_requires_current_sidecar_and_never_exposes_content(tmp_path,monkeypatch):
    from model_customs import app
    report,events,records=current_recording();assert check(report,events,records).accepted
    folder=tmp_path/RID;folder.mkdir()
    (folder/'report.json').write_text(json.dumps(report))
    (folder/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events+[{'type':'complete','agent':'REPORT','data':report}]))
    monkeypatch.setattr(app,'RUNS_ROOT',tmp_path);monkeypatch.setattr(app,'DEMO_ROOT',tmp_path/'empty');monkeypatch.setattr(app,'STATE',{})
    assert asyncio.run(app.recordings())['recordings']==[]
    (folder/SIDECAR).write_bytes(sidecar_bytes(records))
    assert len(asyncio.run(app.recordings())['recordings'])==1
    assert 'cloud_responses' not in report
    (folder/SIDECAR).write_text('{}\n')
    assert asyncio.run(app.recordings())['recordings']==[]


def test_bundle_preserves_sidecar_and_offline_admission(tmp_path,monkeypatch):
    from scripts import bundle_demo
    from model_customs import app
    report,events,records=current_recording();assert check(report,events,records).accepted
    source=tmp_path/'runs'/RID;source.mkdir(parents=True)
    (source/'report.json').write_text(json.dumps(report))
    (source/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events+[{'type':'complete','agent':'REPORT','data':report}]))
    (source/SIDECAR).write_bytes(sidecar_bytes(records))
    for name in ['heldout.json','evaluation.json','calibration.json']:
        (source/name).write_text('{"disclosure":"SYNTHETIC PACKAGING FIXTURE ONLY"}')
    def forbidden(*a,**k):raise AssertionError('Offline bundle initialized provider')
    monkeypatch.setattr(Nemotron,'__init__',forbidden)
    monkeypatch.setattr(bundle_demo,'ROOT',tmp_path)
    bundle_demo.main([RID])
    dest=tmp_path/'demo/recordings'/RID
    assert (dest/SIDECAR).read_bytes()==(source/SIDECAR).read_bytes()
    manifest=json.loads((dest/'recording.json').read_text())
    assert manifest['files_sha256'][SIDECAR]==hashlib.sha256(sidecar_bytes(records)).hexdigest()
    monkeypatch.setattr(app,'DEMO_ROOT',dest.parent)
    assert app.read_accepted_recording(dest,RID)[0]==report
    (dest/SIDECAR).write_text('{}\n')
    with pytest.raises(ValueError):app.read_accepted_recording(dest,RID)
