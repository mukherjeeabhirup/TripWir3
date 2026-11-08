"""Local-readiness boundary tests: mock transports only, no inference or keys."""
import asyncio
import json
from copy import deepcopy
import httpx
import pytest

from model_customs import local_model as local
from model_customs.local_model import LOCAL_MODEL, LocalModelNeeded
from local_fixtures import ready_fixture, hero_fields


def test_key_is_read_only_from_project_env(tmp_path, monkeypatch):
    monkeypatch.setattr(local,'ROOT',tmp_path)
    monkeypatch.setenv('LMSTUDIO_API_KEY','inherited-'+ 'fixture')
    assert local.local_api_key()==''
    (tmp_path/'.env').write_text('LMSTUDIO_API_KEY=project-'+ 'fixture\n')
    assert local.local_api_key()=='project-'+ 'fixture'


@pytest.mark.parametrize('case',['ready','missing_key','wrong_model','listing_denied','bad_listing','tiny_denied','empty','malformed','wrong_answer','truncated','wrong_response_model','missing_response_model'])
def test_preflight_exact_authenticated_get_then_tiny_answer(monkeypatch,case):
    requests=[];fake='fixture-'+ 'credential'
    monkeypatch.setattr(local,'local_api_key',lambda:'' if case=='missing_key' else fake)
    def handler(request):
        requests.append(request)
        assert request.url.host=='127.0.0.1' and request.url.port==1234
        assert request.headers['Authorization']=='Bearer '+fake
        if request.method=='GET':
            assert request.url.path=='/v1/models'
            if case=='listing_denied':return httpx.Response(401)
            if case=='bad_listing':return httpx.Response(200,json={'data':None})
            return httpx.Response(200,json={'data':[{'id':'other-nemotron-nano' if case=='wrong_model' else LOCAL_MODEL}]})
        assert request.url.path=='/v1/completions'
        payload=json.loads(request.content)
        assert payload['model']==LOCAL_MODEL and payload['max_tokens']==32 and not payload['stream']
        if case=='tiny_denied':return httpx.Response(503)
        if case=='malformed':return httpx.Response(200,json={'choices':[]})
        return httpx.Response(200,json={'model':None if case=='missing_response_model' else 'OTHER MODEL' if case=='wrong_response_model' else LOCAL_MODEL,'choices':[{'finish_reason':'length' if case=='truncated' else 'stop',
                'text':'' if case=='empty' else 'wrong' if case=='wrong_answer' else 'READY'}]})
    client=httpx.AsyncClient
    def factory(**kwargs):
        assert kwargs['trust_env'] is False
        return client(transport=httpx.MockTransport(handler),**kwargs)
    monkeypatch.setattr(local.httpx,'AsyncClient',factory)
    async def run():
        if case=='ready':assert local.valid_preflight(await local.preflight_local_model())
        else:
            with pytest.raises(LocalModelNeeded,match='LOCAL MODEL NEEDED') as error:await local.preflight_local_model()
            assert fake not in str(error.value)
    asyncio.run(run())
    assert len(requests)==(0 if case=='missing_key' else 1 if case in {'wrong_model','listing_denied','bad_listing'} else 2)


@pytest.mark.parametrize('tool,role',[('investigator','INVESTIGATOR'),('skeptic','SKEPTIC'),('report','REPORT')])
def test_midcapture_fallback_is_logged_visible_and_blocks_rule_tool(tmp_path,monkeypatch,tool,role):
    from model_customs.orchestrator import Investigation
    from test_reporting import observations
    class Cloud:
        calls=[]
        async def close(self):pass
    async def run():
        events=[]
        async def emit(event):events.append(event)
        audit=Investigation('fixture','poisoned',object(),emit,cloud=Cloud(),runs_root=tmp_path)
        audit.observations=observations()
        await audit.specialists.client.aclose()
        audit.specialists.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={'choices':[]})))
        audit.specialists.model=LOCAL_MODEL;audit.specialists.probed=True
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'fixture-'+ 'credential')
        try:
            with pytest.raises(LocalModelNeeded):await audit.execute(tool,{}, {})
            assert len(events)==1
            assert events[0]['agent']=='SPECIALIST_FALLBACK'
            assert events[0]['data']['role']==role
            assert events[0]['data']['hero_eligible'] is False
            assert events[0]['data']['fallback_executed'] is False
            assert 'LOCAL MODEL NEEDED' in events[0]['data']['summary']
        finally:await audit.specialists.close()
    asyncio.run(run())


def test_direct_audit_and_resume_cannot_bypass_failed_preflight(tmp_path,monkeypatch):
    from model_customs.orchestrator import Investigation
    class Controls:
        def metadata(self,*_):raise AssertionError('No target metadata/tool should run')
    class Cloud:
        calls=[]
        async def close(self):pass
    async def blocked():raise LocalModelNeeded('TEST FIXTURE missing model')
    monkeypatch.setattr('model_customs.orchestrator.preflight_local_model',blocked)
    async def run():
        for resume in [False,True]:
            async def emit(_):raise AssertionError('No tool may run')
            audit=Investigation('fixture','base',Controls(),emit,cloud=Cloud(),runs_root=tmp_path,resume=resume)
            with pytest.raises(LocalModelNeeded):await audit.run()
            assert not audit.history and not audit.cloud.calls
    asyncio.run(run())


@pytest.mark.parametrize('case',['valid','length_valid_json','empty_object','wrong_shape','extra_fields','timeout'])
def test_local_success_requires_stop_and_role_schema_with_separate_http_diagnostics(tmp_path,monkeypatch,case):
    from model_customs.specialists import Specialists
    payload={'alternative_explanations':[],'counterexamples_to_test':[],'limitations':[],'assessment':'TEST FIXTURE'}
    if case=='empty_object':payload={}
    if case=='wrong_shape':payload['limitations']='not a list'
    if case=='extra_fields':payload['claim']='necessary and sufficient'
    def handler(request):
        body=json.loads(request.content)
        assert request.url.path=='/v1/completions'
        assert body['prompt'].endswith('<|im_start|>assistant\n<think></think>')
        assert body['max_tokens']==2048
        if case=='timeout':raise httpx.ReadTimeout('TEST ONLY sensitive body must not be logged',request=request)
        return httpx.Response(200,json={'model':LOCAL_MODEL,'choices':[{'finish_reason':'length' if case=='length_valid_json' else 'stop','text':json.dumps(payload)}],
                                      'usage':{'completion_tokens':10}})
    async def run():
        specialist=Specialists(strict=True)
        await specialist.client.aclose();specialist.client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        specialist.model=LOCAL_MODEL;specialist.probed=True
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'fixture-'+ 'credential')
        try:
            if case=='valid':
                result=await specialist.ask('SKEPTIC','Return schema',{},fallback={})
                assert result['engine']=='local_lmstudio_nemotron'
                assert specialist.calls[0]['schema_validated'] is True
            else:
                with pytest.raises(LocalModelNeeded):await specialist.ask('SKEPTIC','Return schema',{},fallback={})
                record=specialist.calls[0]
                assert record.get('schema_validated') is not True
                assert record['failure_category']==('timeout' if case=='timeout' else 'completion_token_limit' if case=='length_valid_json' else 'response_schema')
                if case!='timeout':assert record['response_http_status']==200
                assert 'sensitive' not in json.dumps(record)
        finally:await specialist.close()
    asyncio.run(run())


@pytest.mark.parametrize('observed',[None,'OTHER MODEL'])
def test_local_role_cannot_relabel_conflicting_or_unknown_response_model(monkeypatch,observed):
    from model_customs.specialists import Specialists
    content={'alternative_explanations':[],'counterexamples_to_test':[],'limitations':[],'assessment':'TEST FIXTURE'}
    async def run():
        specialist=Specialists(strict=True)
        await specialist.client.aclose()
        specialist.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'model':observed,'choices':[{'finish_reason':'stop','text':json.dumps(content)}]})))
        specialist.model=LOCAL_MODEL;specialist.probed=True
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'fixture-'+ 'credential')
        try:
            with pytest.raises(LocalModelNeeded):await specialist.ask('SKEPTIC','Return schema',{},fallback={})
            call=specialist.calls[0]
            assert call['requested_model']==LOCAL_MODEL
            assert call['observed_model']==observed and call['model']==observed
            assert call['failure_category']=='response_model'
            assert call.get('schema_validated') is not True
        finally:await specialist.close()
    asyncio.run(run())
