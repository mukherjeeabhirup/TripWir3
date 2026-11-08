"""Recorded truncation and synthetic policy/wire regressions; no live inference."""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket

import httpx
import pytest
from model_customs.claims import decode_specialist_content,valid_specialist_result,specialist_schema
from model_customs.local_model import LocalModelNeeded
from model_customs.routing import local_profile,valid_local_preflight,route_config,pinned_routes,valid_context_budget
from model_customs.specialist_budget import context_budget,valid_budget,valid_wire_request,ROLE_LIMITS
from model_customs.specialists import Specialists,SpecialistIncomplete,specialist_prompt
from local_fixtures import skeptic_payload
from test_routing import readiness,native,routed_recording,INSTANCE
from test_decision_audit import reclose

FIXTURE=Path(__file__).parent/'fixtures/specialist/hero2-skeptic-length.json'


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def blocked(*a,**k):raise AssertionError('No network in specialist regressions')
    monkeypatch.setattr(socket.socket,'connect',blocked)
    monkeypatch.setattr(socket.socket,'connect_ex',blocked)
    monkeypatch.setattr(socket,'create_connection',blocked)
    monkeypatch.setattr('model_customs.specialists.load_env',lambda:None)
    monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'fixture-only')


def fresh():
    value=readiness();value['loaded_instance']['runtime_context_tokens']=256000
    return value


def payload(role):
    if role=='SKEPTIC':return skeptic_payload()
    if role=='REPORT':return {'claim_rows':[],'scope':'tested_prompts_only'}
    return {'hypothesis':'test_trigger_specificity','proposed_variants':['partial'],'rationale':'measure_before_claiming','discovery_limit':'known_intake_only','identity_refs':[]}


def test_recorded_hero2_is_truncated_schema_not_context_or_new_thinking_toggle():
    x=json.loads(FIXTURE.read_text())
    assert hashlib.sha256(x['content'].encode()).hexdigest()==x['content_sha256']=='526358f94647e2570457c8b80c6bac9727cc6a05aa981cdc6ef1fd0ced53162d'
    assert x['usage']=={'prompt_tokens':2526,'completion_tokens':2047,'total_tokens':4573}
    assert x['request_max_tokens']==2048 and x['finish_reason']=='length' and x['native_context']==32000
    assert x['request_ends_no_thinking_prefix'] and '<think>' not in x['content']
    assert '"properties"' in x['content'][:300]
    with pytest.raises(ValueError):decode_specialist_content(x['content'])


@pytest.mark.parametrize('role',list(ROLE_LIMITS))
def test_budget_binds_finite_role_actual_literal_context_and_margin(role):
    b=context_budget(role,'prompt',256000)
    assert b['runtime_context_tokens']==256000 and b['runtime_context_tokens']!=262144
    assert b['max_completion_tokens']==(2048 if role=='INVESTIGATOR' else 16384)
    assert b['request_timeout_seconds']==(60 if role=='INVESTIGATOR' else 600)
    assert b['context_margin_tokens']==1024 and valid_budget(b,256000,role=role,policy_version=2)
    boundary=b['estimated_total_tokens'];assert valid_budget(context_budget(role,'prompt',boundary),boundary,role=role,policy_version=2)
    assert not valid_budget(context_budget(role,'prompt',boundary-1),boundary-1,role=role,policy_version=2)


@pytest.mark.parametrize('field,value',[('role',[]),('role',{}),('role',None),('role',True),('role','OTHER'),('role','REPORT'),('max_completion_tokens',True),('max_completion_tokens',2048),('max_completion_tokens',999999),('context_margin_tokens',0),('context_margin_tokens',False),('request_timeout_seconds',60),('runtime_context_tokens',262144),('budget_policy_version',True),('budget_policy_version',1),('estimated_total_tokens',0)])
def test_malformed_or_forged_budget_rejects_without_throwing(field,value):
    b=context_budget('SKEPTIC','prompt',256000);b[field]=value
    assert valid_budget(b,256000,role='SKEPTIC',policy_version=2) is False


def test_legacy_profile_and_budget_are_readable_but_not_new_runtime_policy():
    old=readiness(legacy=True);old['loaded_instance']['runtime_context_tokens']=32000
    assert valid_local_preflight(old)
    assert not valid_local_preflight(old,local_profile('lightning35_mlx4bit'))
    b={'estimate_method':'ceil_chars_div3','prompt_characters':300,'estimated_prompt_tokens':100,'max_completion_tokens':2048,'runtime_context_tokens':32000,'estimated_total_tokens':2148}
    assert valid_context_budget(b,32000,role='SKEPTIC',policy_version=1)
    assert not valid_context_budget(b,32000,role='SKEPTIC',policy_version=2)
    report,events=routed_recording();assert reclose(report,events).accepted
    report['run_signature']['inputs']['sources']['model_customs/specialist_budget.py']='f'*64
    assert not reclose(report,events).accepted


@pytest.mark.parametrize('role',['SKEPTIC','REPORT'])
def test_populated_examples_retain_actual_contract_and_never_supply_a_fallback(role):
    evidence={'required_review':{'claim_rows':[],'observed_variants':[],'support_refs':[],'claim_links':[]},'required_claim_rows':[]}
    p=specialist_prompt(role,'Closed fields only',evidence)
    user=json.loads(p.split('<|im_start|>user\n',1)[1].split('<|im_end|>',1)[0])
    assert user['evidence']==evidence and valid_specialist_result(role,user['response_example'])
    assert json.dumps(specialist_schema(role)) not in p and '"properties":' not in p
    assert p.endswith('<think></think>')
    if role=='SKEPTIC':assert {k:v for k,v in user['response_example']['typed_review'].items() if k!='countertests'}==evidence['required_review']


@pytest.mark.parametrize('role',list(ROLE_LIMITS))
@pytest.mark.parametrize('response',['valid','valid_length','recorded_length','schema_stop','timeout'])
def test_actual_request_budget_timeout_and_truncation_fail_closed(role,response):
    posts=[]
    def handler(request):
        if request.method=='GET':return httpx.Response(200,json=native(context=256000))
        posts.append(request);body=json.loads(request.content)
        assert body['max_tokens']==ROLE_LIMITS[role][0]
        assert request.extensions['timeout']['read']==ROLE_LIMITS[role][1]
        if response=='timeout':raise httpx.ReadTimeout('DO NOT COPY provider body',request=request)
        text=json.dumps(payload(role))
        if response=='recorded_length':text=json.loads(FIXTURE.read_text())['content']
        if response=='schema_stop':text=json.dumps(specialist_schema(role))
        return httpx.Response(200,json={'model':INSTANCE,'choices':[{'text':text,'finish_reason':'length' if response.endswith('length') else 'stop'}],'usage':{'completion_tokens':10}})
    async def run():
        s=Specialists(profile='lightning35_mlx4bit',preflight=fresh());await s.client.aclose();s.client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            if response=='valid':assert (await s.ask(role,'result instance',{'identity_refs':[]},fallback={}))['engine']=='local_lmstudio_nemotron'
            else:
                with pytest.raises(LocalModelNeeded):await s.ask(role,'result instance',{'identity_refs':[]},fallback={})
                assert s.calls[0].get('schema_validated') is not True
                assert s.calls[0]['failure_category']==('timeout' if response=='timeout' else 'response_schema_echo' if response=='schema_stop' else 'completion_token_limit')
            assert len(posts)==1 and len(s.raw_requests)==1
            assert valid_wire_request(s.raw_requests[0],s.calls[0],INSTANCE)
            assert 'DO NOT COPY' not in json.dumps(s.calls)
        finally:await s.close()
    asyncio.run(run())


def wire_recording():
    # Coherent synthetic current-policy admission, separate from legacy fixtures.
    report,events=routed_recording();config=route_config('super','lightning35_mlx4bit',policy_version=1);ready=fresh();routes=pinned_routes(config,ready)
    report['local_model_preflight']=ready;report['model_routing']=deepcopy(routes)
    inputs=report['run_signature']['inputs'];inputs.update(configured_model_routing=config,model_routing=routes)
    inputs['sources']['model_customs/specialist_budget.py']=hashlib.sha256(Path('model_customs/specialist_budget.py').read_bytes()).hexdigest()
    events[0]['data']['model_routing']=deepcopy(routes)
    calls=report['specialist_calls'];requests=[]
    for c in calls+report['specialist_provider_outputs']:
        c['local_profile']=deepcopy(config['local']);c['loaded_instance']=deepcopy(ready['loaded_instance'])
    for i,c in enumerate(calls):
        c['context_budget']=context_budget(c['role'],'x'*300,256000);c['request_timeout_seconds']=c['context_budget']['request_timeout_seconds']
        body=json.dumps({'model':INSTANCE,'temperature':0.1,'max_tokens':c['context_budget']['max_completion_tokens'],'stream':False,'stop':['<|im_end|>'],'prompt':'x'*300})
        c['request_sha256']=hashlib.sha256(body.encode()).hexdigest();requests.append({'call_index':i,'endpoint':'/v1/completions','body':body,'sha256':c['request_sha256']})
    report['specialist_provider_requests']=requests
    for e in events:
        if e['agent']=='REPORT':e['data']['call_accounting']['specialist_calls']=deepcopy(calls)
    assert reclose(report,events).accepted
    return report,events


@pytest.mark.parametrize('mutation',['role','cap','margin','timeout','context','missing_wire','wire_cap_rehashed','wire_model_rehashed','wire_prompt_rehashed','duplicate_wire_index','delete_source_pin_and_budget_version'])
def test_current_admission_requires_role_policy_wire_and_context_binding(mutation):
    report,events=wire_recording();calls=next(e['data'] for e in events if e['agent']=='REPORT')['call_accounting']['specialist_calls'];c=calls[1]
    if mutation=='role':c['context_budget']['role']='REPORT'
    elif mutation=='cap':c['context_budget']['max_completion_tokens']=2048
    elif mutation=='margin':c['context_budget']['context_margin_tokens']=0
    elif mutation=='timeout':c['request_timeout_seconds']=60
    elif mutation=='context':c['context_budget']['runtime_context_tokens']=262144
    elif mutation=='missing_wire':report.pop('specialist_provider_requests')
    elif mutation=='duplicate_wire_index':report['specialist_provider_requests'][1]['call_index']=0
    elif mutation=='delete_source_pin_and_budget_version':
        report['run_signature']['inputs']['sources'].pop('model_customs/specialist_budget.py')
        c['context_budget'].pop('budget_policy_version')
    else:
        q=report['specialist_provider_requests'][1];body=json.loads(q['body'])
        if mutation=='wire_cap_rehashed':body['max_tokens']=2048
        elif mutation=='wire_model_rehashed':body['model']='WRONG'
        else:body['prompt']='short'
        q['body']=json.dumps(body);q['sha256']=c['request_sha256']=hashlib.sha256(q['body'].encode()).hexdigest()
    assert not reclose(report,events).accepted


def test_new_runtime_overflow_stops_before_any_http_without_evidence_trimming():
    async def run():
        s=Specialists(profile='lightning35_mlx4bit',preflight=fresh());await s.client.aclose()
        def blocked(_):raise AssertionError('Overflow must not request HTTP')
        s.client=httpx.AsyncClient(transport=httpx.MockTransport(blocked));e={'evidence':'x'*768000}
        try:
            with pytest.raises(SpecialistIncomplete):await s.ask('REPORT','instance',e,fallback={})
            assert len(e['evidence'])==768000 and not s.calls and not s.raw_requests
        finally:await s.close()
    asyncio.run(run())


def test_total_timeout_is_finite_and_stops_without_retry(monkeypatch):
    deadlines=[]
    async def expire(coro,*,timeout):
        deadlines.append(timeout);coro.close();raise TimeoutError('UNTRUSTED never copy')
    async def run():
        s=Specialists(profile='lightning35_mlx4bit',preflight=fresh());await s.client.aclose()
        s.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=native(context=256000))))
        monkeypatch.setattr('model_customs.specialists.asyncio.wait_for',expire)
        try:
            with pytest.raises(LocalModelNeeded):await s.ask('SKEPTIC','instance',{},fallback={})
            assert len(s.calls)==len(s.raw_requests)==1 and not s.raw_responses
            assert s.calls[0]['failure_category']=='timeout' and 'UNTRUSTED' not in json.dumps(s.calls)
        finally:await s.close()
    asyncio.run(run());assert deadlines==[600]
