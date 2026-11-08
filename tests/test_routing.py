"""New-stack contract: every HTTP response below is explicitly synthetic."""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import httpx
import pytest

from model_customs.routing import (SUPER,ULTRA,LOCAL_URL,LOCAL_MODELS_URL,route_config,local_profile,
    select_loaded_instance,valid_local_preflight,pinned_routes)
from model_customs import local_model
from model_customs.local_model import LocalModelNeeded
from model_customs.llm import Nemotron,CloudError
from test_agent_trace import new_recording,RID
from test_decision_audit import reclose

INSTANCE='USER-LOADED-LIGHTNING-INSTANCE-7'  # Not guessed from artifact spelling.


def native(*,loaded=True,context=32768):
    return {'models':[{'type':'llm','key':'mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit','format':'mlx',
        'loaded_instances':[{'id':INSTANCE,'config':{'context_length':context}}] if loaded else []}]}


def readiness():
    profile=local_profile('lightning35_mlx4bit')
    return {'status':'ready','model':INSTANCE,'requested_model':INSTANCE,'observed_model':INSTANCE,
        'local_profile':profile,'loaded_instance':select_loaded_instance(native(),profile),
        'provider':'lm_studio','base_url':LOCAL_URL,'selection':{'selected_id':INSTANCE,'candidate_count':1},
        'models_http_status':200,'completion_http_status':200,'answer_verified':True}


def routed_recording():
    report,events=new_recording()
    config=route_config('super','lightning35_mlx4bit');ready=readiness();routes=pinned_routes(config,ready)
    report['local_model_preflight']=ready;report['model_routing']=routes;report['cloud_route_classification']='pure_primary'
    inputs=report['run_signature']['inputs'];inputs.update(model_routing=routes,configured_model_routing=config,cloud_primary=SUPER,cloud_fallback=None)
    inputs['sources']['model_customs/routing.py']=hashlib.sha256(Path('model_customs/routing.py').read_bytes()).hexdigest()
    events[0]['data'].update(model=SUPER,model_routing=deepcopy(routes))
    calls=report['specialist_calls'];raw=report['specialist_provider_outputs']
    for c in calls+raw:
        c.update(model=INSTANCE,requested_model=INSTANCE,observed_model=INSTANCE,provider='lm_studio',base_url=LOCAL_URL,
            local_profile=deepcopy(config['local']),loaded_instance=deepcopy(ready['loaded_instance']),endpoint='/v1/completions',loaded_state_http_status=200)
    for c in calls:c['context_budget']={'estimate_method':'ceil_chars_div3','prompt_characters':300,'estimated_prompt_tokens':100,'max_completion_tokens':2048,'runtime_context_tokens':32768,'estimated_total_tokens':2148}
    for output in report['specialist_outputs'].values():output['model']=INSTANCE
    report['skeptic']['model']=INSTANCE;report['narrative']['model_draft']['raw']['model']=INSTANCE
    for e in events:
        if e['agent'] in {'INVESTIGATOR','SKEPTIC'}:e['data']['model']=INSTANCE
        if e['agent']=='ORCHESTRATOR' and e['data'].get('tool'):
            e['data']['planner_identity']={'requested':SUPER,'observed':SUPER}
        if e['agent']=='REPORT':
            e['data']['model_draft']['raw']['model']=INSTANCE
            e['data']['call_accounting']['specialist_calls']=deepcopy(calls)
            call=e['data']['call_accounting']['cloud_calls'][0]
            call.update(model=SUPER,observed_model=SUPER,requested_model=SUPER,configured_model=SUPER,
                        provider='nvidia_integrate',base_url=config['cloud']['base_url'],is_fallback=False)
    assert reclose(report,events).accepted
    return report,events


def test_default_super_ignores_old_ultra_model_env_and_has_no_silent_fallback(monkeypatch):
    monkeypatch.delenv('TRIPWIR3_ORCHESTRATOR_PROFILE',raising=False)
    monkeypatch.delenv('TRIPWIR3_LOCAL_PROFILE',raising=False)
    monkeypatch.setenv('NEMOTRON_MODEL',ULTRA)
    monkeypatch.setenv('NEMOTRON_FALLBACK_MODEL','nvidia/nemotron-3.5-lightning-30b-a3b')
    route=route_config();assert route['cloud']['model']==SUPER and route['cloud']['fallback_model'] is None
    assert route['local']['profile']=='lightning35_mlx4bit'
    assert route_config('ultra')['cloud']['model']==ULTRA


@pytest.mark.parametrize('case',['ready','native_32000','unloaded','unknown_native','missing_instances','ambiguous','wrong_profile',
    'wrong_served','unknown_context','short_context','below_minimum','larger_256k','boolean_context','wrong_format','wrong_quant_8bit','wrong_quant_gguf'])
def test_native_loaded_state_precedes_exact_instance_tiny_completion(monkeypatch,case):
    data=native();requests=[]
    if case=='native_32000':data=native(context=32000)
    elif case=='unloaded':data=native(loaded=False)
    elif case=='unknown_native':data={'data':[{'id':INSTANCE}]}  # OpenAI availability cannot establish load.
    elif case=='missing_instances':data['models'][0].pop('loaded_instances')
    elif case=='ambiguous':data['models'][0]['loaded_instances'].append({'id':'OTHER','config':{'context_length':32768}})
    elif case=='wrong_profile':data['models'][0]['key']='nvidia-nemotron-3-nano-30b-a3b-mlx'
    elif case=='unknown_context':data['models'][0]['loaded_instances'][0]['config']={}
    elif case=='short_context':data=native(context=8192)
    elif case=='larger_256k':data=native(context=262144)
    elif case=='below_minimum':data=native(context=31999)
    elif case=='wrong_quant_8bit':data['models'][0]['quantization']={'bits_per_weight':8,'name':'int8'}
    elif case=='wrong_quant_gguf':data['models'][0]['quantization']={'bits_per_weight':4,'name':'GGUF Q4_K_M'}
    elif case=='boolean_context':data=native(context=True)
    elif case=='wrong_format':data['models'][0]['format']='gguf'
    def handler(request):
        requests.append(request)
        assert request.url.host=='127.0.0.1' and request.url.port==1234
        if request.method=='GET':
            assert str(request.url)==LOCAL_MODELS_URL
            return httpx.Response(200,json=data)
        assert request.url.path=='/v1/completions'
        assert json.loads(request.content)['model']==INSTANCE
        return httpx.Response(200,json={'model':'WRONG SERVING ID' if case=='wrong_served' else INSTANCE,
            'choices':[{'text':'READY','finish_reason':'stop'}]})
    client=httpx.AsyncClient
    monkeypatch.setattr(local_model,'local_api_key',lambda:'fixture-credential')
    monkeypatch.setattr(local_model.httpx,'AsyncClient',lambda **kw:client(transport=httpx.MockTransport(handler),**kw))
    async def run():
        if case in {'ready','native_32000','larger_256k'}:
            result=await local_model.preflight_local_model('lightning35_mlx4bit')
            assert valid_local_preflight(result,local_profile('lightning35_mlx4bit'))
            assert result['loaded_instance']['runtime_context_tokens']==data['models'][0]['loaded_instances'][0]['config']['context_length']
        else:
            with pytest.raises(LocalModelNeeded) as exc:await local_model.preflight_local_model('lightning35_mlx4bit')
            if case=='wrong_served':
                assert exc.value.evidence['requested_model']==INSTANCE
                assert exc.value.evidence['observed_model']=='WRONG SERVING ID'
            assert 'fixture-credential' not in json.dumps(exc.value.evidence)
    asyncio.run(run())
    assert len(requests)==(2 if case in {'ready','native_32000','larger_256k','wrong_served'} else 1)


def test_unrelated_first_model_never_selected_and_no_arbitrary_id_guess():
    data=native();data['models'].insert(0,{'type':'llm','key':'unrelated','format':'mlx','loaded_instances':[{'id':'FIRST','config':{'context_length':32768}}]})
    assert select_loaded_instance(data,local_profile('lightning35_mlx4bit'))['instance_id']==INSTANCE


def test_source_selected_profile_accepts_realistic_lightning_instance_id():
    report,events=routed_recording()
    assert report['model_routing']['local']['selected_id']==INSTANCE
    assert report['cloud_route_classification']=='pure_primary'
    assert report['provenance_check']['passed']


@pytest.mark.parametrize('mutate',[lambda r,e:r['run_signature']['inputs'].pop('model_routing'),
    lambda r,e:r['model_routing']['local'].update(selected_id='OTHER'),
    lambda r,e:r['local_model_preflight']['loaded_instance'].update(runtime_context_tokens=8192),
    lambda r,e:next(x['data'] for x in e if x['agent']=='REPORT')['call_accounting']['specialist_calls'][0].update(requested_model='NANO SILENT FALLBACK'),
    lambda r,e:r['specialist_provider_outputs'][0].update(provider='cloud'),
    lambda r,e:next(x['data'] for x in e if x['agent']=='REPORT')['call_accounting']['cloud_calls'][0].update(base_url='https://openrouter.ai/api/v1'),
    lambda r,e:next(x['data'] for x in e if x['agent']=='REPORT')['call_accounting']['cloud_calls'][0].update(observed_model='private/nvidia/nemotron-3.5-super-120b-a12b'),
    lambda r,e:r.update(cloud_route_classification='mixed_or_fallback')])
def test_profile_pin_provider_and_literal_observed_identity_cannot_be_relabelled(mutate):
    report,events=routed_recording();mutate(report,events)
    assert not reclose(report,events).accepted


def test_specialist_rechecks_pin_and_context_before_completion(monkeypatch):
    from model_customs.specialists import Specialists
    ready=readiness();requests=[]
    def handler(request):
        requests.append(request)
        assert request.method=='GET'  # Unloaded after preflight: never JIT-load via completion.
        return httpx.Response(200,json=native(loaded=False))
    async def run():
        role=Specialists(profile='lightning35_mlx4bit',preflight=ready)
        await role.client.aclose();role.client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'fixture-credential')
        with pytest.raises(LocalModelNeeded):await role.ask('SKEPTIC','JSON',{},fallback={})
        assert not role.calls and not role.raw_responses
        await role.close()
    asyncio.run(run());assert len(requests)==1


def test_route_snapshot_and_native_context_bind_resume_and_cache_identity():
    from scripts.run_audit import source_identity
    config=route_config('super','lightning35_mlx4bit');ready=readiness()
    first=source_identity(config,ready)
    changed=deepcopy(ready);changed['loaded_instance']['runtime_context_tokens']=65536
    assert first!=source_identity(config,changed)
    changed=deepcopy(ready);changed['requested_model']='NEW INSTANCE';changed['observed_model']='NEW INSTANCE';changed['model']='NEW INSTANCE'
    changed['selection']['selected_id']='NEW INSTANCE';changed['loaded_instance']['instance_id']='NEW INSTANCE'
    assert first!=source_identity(config,changed)
    assert first!=source_identity(route_config('ultra','lightning35_mlx4bit'),ready)


def test_live_route_snapshot_does_not_change_with_environment(monkeypatch):
    async def run():
        model=Nemotron(routing=route_config('super','lightning35_mlx4bit'))
        monkeypatch.setenv('TRIPWIR3_ORCHESTRATOR_PROFILE','ultra')
        monkeypatch.setenv('TRIPWIR3_LOCAL_PROFILE','nano3_mlx')
        assert model.primary==SUPER and model.routing['local']['profile']=='lightning35_mlx4bit'
        await model.close()
    asyncio.run(run())


def test_unconfigured_provider_or_alias_policy_cannot_be_enabled():
    async def run():
        for field,value in [('base_url','https://openrouter.ai/api/v1'),('provider','openrouter'),('observed_identity_policy','accept_any')]:
            config=route_config('super','lightning35_mlx4bit');config['cloud'][field]=value
            with pytest.raises(ValueError):Nemotron(routing=config)
    asyncio.run(run())


def test_bool_readiness_counts_and_unknown_native_pin_fields_reject():
    for mutate in [lambda r:r['selection'].update(candidate_count=True),
                   lambda r:r['loaded_instance'].update(runtime_context_tokens=True),
                   lambda r:r['loaded_instance'].update(native_api='unknown'),
                   lambda r:r['loaded_instance'].update(extra_unverified_claim=True)]:
        ready=readiness();mutate(ready)
        assert not valid_local_preflight(ready)


def test_changed_loaded_context_cannot_be_used_by_pinned_role(monkeypatch):
    from model_customs.specialists import Specialists
    async def run():
        role=Specialists(profile='lightning35_mlx4bit',preflight=readiness())
        await role.client.aclose()
        role.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=native(context=65536))))
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'fixture-credential')
        with pytest.raises(LocalModelNeeded):await role.ask('SKEPTIC','JSON',{},fallback={})
        assert role.calls==[]
        await role.close()
    asyncio.run(run())


def test_deleted_routing_cannot_downgrade_even_if_module_pin_is_removed():
    report,events=routed_recording()
    report['run_signature']['inputs'].pop('model_routing')
    report['run_signature']['inputs']['sources'].pop('model_customs/routing.py')
    assert not reclose(report,events).accepted


@pytest.mark.parametrize('mutate',[lambda r:r['model_routing'].update(schema_version=True),
    lambda r:r['run_signature']['inputs']['configured_model_routing']['cloud'].update(model=ULTRA),
    lambda r:r['local_model_preflight']['local_profile'].update(checkpoint_equivalence_verified=0)])
def test_route_snapshot_types_and_configured_aliases_are_strict(mutate):
    report,events=routed_recording();mutate(report)
    assert not reclose(report,events).accepted


def test_explicit_cloud_fallback_remains_mixed_not_pure_super():
    from test_agent_trace import CALL
    report,events=routed_recording()
    config=route_config('super','lightning35_mlx4bit',fallback_model=ULTRA)
    routes=pinned_routes(config,report['local_model_preflight'])
    report['model_routing']=routes;report['cloud_route_classification']='mixed_or_fallback'
    inputs=report['run_signature']['inputs'];inputs.update(model_routing=routes,configured_model_routing=config,cloud_fallback=ULTRA)
    events[0]['data']['model_routing']=deepcopy(routes)
    action=next(e['data'] for e in events if e['agent']=='ORCHESTRATOR' and e['data'].get('tool'))
    action.update(planner_call_index=1,planner_identity={'requested':ULTRA,'observed':ULTRA})
    calls=[{'agent':'ORCHESTRATOR','model':SUPER,'requested_model':SUPER,'configured_model':SUPER,
            'observed_model':None,'status':503,'provider':'nvidia_integrate','base_url':config['cloud']['base_url'],'is_fallback':False},
           {**CALL,'model':ULTRA,'requested_model':ULTRA,'configured_model':SUPER,'observed_model':ULTRA,
            'provider':'nvidia_integrate','base_url':config['cloud']['base_url'],'is_fallback':True}]
    next(e['data'] for e in events if e['agent']=='REPORT')['call_accounting']['cloud_calls']=calls
    result=reclose(report,events);assert result.accepted,result.errors
    assert report['query_counts']['cloud_attempts']==2
    report['cloud_route_classification']='pure_primary'
    assert not reclose(report,events).accepted


def test_completed_cache_compares_source_route_even_with_matching_index_hash(tmp_path):
    from scripts.run_audit import completed_report,identity_sha256,file_sha256
    report,events=routed_recording();folder=tmp_path/RID;folder.mkdir()
    (folder/'report.json').write_text(json.dumps(report))
    complete={'type':'complete','agent':'REPORT','data':deepcopy(report),'timestamp':'TEST FIXTURE'}
    (folder/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events+[complete]))
    identity={'artifact':'poisoned','auditor_routing':deepcopy(report['model_routing'])}
    entry={'state':'complete','run_id':RID,'identity_sha256':identity_sha256(identity),'report_sha256':file_sha256(folder/'report.json')}
    assert completed_report(entry,identity,tmp_path) is not None
    identity['auditor_routing']['local']['loaded_instance']['runtime_context_tokens']=65536
    entry['identity_sha256']=identity_sha256(identity)
    assert completed_report(entry,identity,tmp_path) is None


def test_api_rejects_unknown_route_profile_or_ignored_model_arguments():
    from model_customs.app import RunRequest
    from pydantic import ValidationError
    assert RunRequest(artifact='base').orchestrator=='super'
    for args in [{'orchestrator':'openrouter'},{'local_profile':'arbitrary-first'},{'model':'some silent override'}]:
        with pytest.raises(ValidationError):RunRequest(artifact='base',**args)


def test_native_quantization_is_preserved_and_not_checkpoint_hash_equivalence():
    data=native();data['models'][0]['quantization']={'bits_per_weight':4,'name':'affine4bit'}
    result=select_loaded_instance(data,local_profile('lightning35_mlx4bit'))
    assert result['quantization']==data['models'][0]['quantization']
    assert local_profile('lightning35_mlx4bit')['checkpoint_equivalence_verified'] is False


def test_oversized_prompt_is_incomplete_without_trimming_http_or_rule_output(monkeypatch):
    from model_customs.specialists import Specialists,SpecialistIncomplete
    requests=[];notices=[]
    async def notice(value):notices.append(value)
    def forbidden(request):requests.append(request);raise AssertionError('Overflow must not request any model/state HTTP')
    async def run():
        role=Specialists(profile='lightning35_mlx4bit',preflight=readiness())
        await role.client.aclose();role.client=httpx.AsyncClient(transport=httpx.MockTransport(forbidden));role.on_fallback=notice
        evidence={'untrimmed_evidence':'x'*100000}
        with pytest.raises(SpecialistIncomplete):await role.ask('SKEPTIC','Full evidence required',evidence,fallback={'fake':'forbidden'})
        assert evidence['untrimmed_evidence']=='x'*100000 and not role.calls and not role.raw_responses
        assert notices[0]['status']=='INCOMPLETE' and notices[0]['reason']=='context_overflow'
        assert notices[0]['context_budget']['runtime_context_tokens']==32768
        assert notices[0]['context_budget']['estimated_total_tokens']>32768
        assert notices[0]['fallback_executed'] is False and notices[0]['completion_requested'] is False
        await role.close()
    asyncio.run(run());assert not requests


def test_overflow_source_event_is_incomplete_and_never_claims_a_model_response(tmp_path):
    from model_customs.orchestrator import Investigation
    from model_customs.specialists import SpecialistIncomplete
    from test_orchestrator import TestCloud,TestControls,fixture_identity
    async def run():
        events=[]
        async def emit(e):events.append(deepcopy(e))
        audit=Investigation(RID,'base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path,
                            model_identity_provider=fixture_identity,routing=route_config('super','lightning35_mlx4bit'))
        audit.specialists.pin(readiness())
        with pytest.raises(SpecialistIncomplete):await audit.specialists.ask('SKEPTIC','JSON',{'evidence':'x'*100000},fallback={})
        assert events[0]['agent']=='SPECIALIST_INCOMPLETE'
        assert events[0]['data']['factual_grounding']=={'status':'INCOMPLETE','passed':False,'checked':0,'total':1,'errors':['context_overflow']}
        assert events[1]['data']['model']['observed'] is None
        assert events[1]['data']['phase']=='incomplete'
        await audit.specialists.close()
    asyncio.run(run())


@pytest.mark.parametrize('mutation',[lambda c:c.pop('context_budget'),
    lambda c:c['context_budget'].update(runtime_context_tokens=262144),
    lambda c:c['context_budget'].update(estimated_total_tokens=40000)])
def test_green_role_calls_cannot_hide_missing_wrong_or_overflow_context_budget(mutation):
    report,events=routed_recording()
    call=next(e['data'] for e in events if e['agent']=='REPORT')['call_accounting']['specialist_calls'][0]
    mutation(call)
    assert not reclose(report,events).accepted


def test_rule_based_substitution_cannot_be_enabled_by_old_constructor_flag():
    from model_customs.specialists import Specialists
    with pytest.raises(ValueError):Specialists(strict=False)


def test_overflow_guard_uses_actual_32000_pin_not_old32768_interpretation():
    from model_customs.specialists import Specialists,SpecialistIncomplete
    ready=readiness();ready['loaded_instance']['runtime_context_tokens']=32000
    notices=[];requests=[]
    async def notice(value):notices.append(value)
    def forbidden(request):requests.append(request);raise AssertionError('Overflow must stop before HTTP')
    async def run():
        role=Specialists(profile='lightning35_mlx4bit',preflight=ready)
        await role.client.aclose();role.client=httpx.AsyncClient(transport=httpx.MockTransport(forbidden));role.on_fallback=notice
        evidence={'untrimmed_evidence':'x'*90000}
        with pytest.raises(SpecialistIncomplete):await role.ask('REPORT','Full evidence required',evidence,fallback={})
        budget=notices[0]['context_budget']
        assert budget['runtime_context_tokens']==32000
        assert 32000<budget['estimated_total_tokens']<=32768
        assert evidence['untrimmed_evidence']=='x'*90000 and not role.calls
        await role.close()
    asyncio.run(run());assert not requests
