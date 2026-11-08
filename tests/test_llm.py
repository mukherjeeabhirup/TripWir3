import asyncio
import httpx
import json
import pytest
from model_customs.llm import Nemotron, CloudError


class NoWaitLimiter:
    async def acquire(self): pass


def test_429_retries_then_fallback(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    models=[]
    def handler(request):
        import json
        model=json.loads(request.content)['model']; models.append(model)
        if len(models)<=3:return httpx.Response(429,headers={'retry-after':'0'})
        return httpx.Response(200,json={'model':json.loads(request.content)['model'],'choices':[{'finish_reason':'stop','message':{'content':'{"tool":"provenance"}'}}],'usage':{'total_tokens':3}})
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        cloud=Nemotron(client,sleep=lambda _:asyncio.sleep(0),limiter=NoWaitLimiter())
        result=await cloud.ask('test','Return JSON',{})
        assert result['tool']=='provenance'
        assert len(cloud.calls)==4
        assert models[-1]==cloud.fallback and models[0]==cloud.primary
        await cloud.close()
    asyncio.run(run())


def test_auth_failure_is_redacted(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(401,text='DO NOT LEAK')))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        with pytest.raises(CloudError) as exc: await cloud.ask('test','',{})
        assert 'DO NOT LEAK' not in str(exc.value)
        await cloud.close()
    asyncio.run(run())


def test_malformed_success_uses_retries_and_fallback(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    count=[0]
    def handler(request):
        count[0]+=1
        if count[0]<=3:return httpx.Response(200,json={'model':json.loads(request.content)['model'],'choices':[]})
        return httpx.Response(200,json={'model':json.loads(request.content)['model'],'choices':[{'finish_reason':'stop','message':{'content':'{"ok":true}'}}]})
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        assert await cloud.ask('ORCHESTRATOR','JSON',{})=={'ok':True}
        assert len(cloud.calls)==4
        assert all(x.get('parse_error') for x in cloud.calls[:3])
        await cloud.close()
    asyncio.run(run())


def test_structured_decisions_disable_thinking_for_primary_and_fallback(monkeypatch):
    import json
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    requests=[]
    class CountingLimiter:
        count=0
        async def acquire(self):self.count+=1
    def handler(request):
        payload=json.loads(request.content)
        requests.append(payload)
        if len(requests)<=3:return httpx.Response(500)
        return httpx.Response(200,json={'model':json.loads(request.content)['model'],'choices':[{'finish_reason':'stop',
            'message':{'content':'{"tool":"freeze"}'}}]})
    async def run():
        limiter=CountingLimiter()
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        cloud=Nemotron(client,sleep=lambda _:asyncio.sleep(0),limiter=limiter)
        assert await cloud.ask('ORCHESTRATOR','Return JSON',{})=={'tool':'freeze'}
        assert limiter.count==len(requests)==4
        assert requests[0]['model']==cloud.primary
        assert requests[-1]['model']==cloud.fallback
        assert all(x['chat_template_kwargs']=={'enable_thinking':False} for x in requests)
        assert all(x['max_tokens']==2048 and x['stream'] is False for x in requests)
        assert all(x['thinking_enabled'] is False and x['max_tokens']==2048 for x in cloud.calls)
        assert cloud.calls[-1]['finish_reason']=='stop'
        assert cloud.calls[-1]['truncated'] is False
        await cloud.close()
    asyncio.run(run())


def test_length_limited_json_is_rejected_and_metadata_checkpointed(monkeypatch):
    import copy
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    requests=[]
    def handler(request):
        requests.append(request)
        truncated=len(requests)<=3
        # Even syntactically valid JSON cannot override a provider length stop.
        return httpx.Response(200,json={'model':json.loads(request.content)['model'],'choices':[{'finish_reason':'length' if truncated else 'stop',
            'message':{'content':'{"ok":true}', 'reasoning_content':'PRIVATE TEST FIXTURE'}}],
            'usage':{'completion_tokens':2048 if truncated else 4,
                     'completion_tokens_details':{'reasoning_tokens':2048 if truncated else 0}}})
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        snapshots=[]
        cloud.on_call=lambda:snapshots.append(copy.deepcopy(cloud.calls))
        assert await cloud.ask('ORCHESTRATOR','Return JSON',{})=={'ok':True}
        assert len(cloud.calls)==4
        assert all(x['truncated'] and x['parse_error'] and x['finish_reason']=='length' for x in cloud.calls[:3])
        assert cloud.calls[-1]['truncated'] is False
        assert snapshots[-1][-1]['finish_reason']=='stop'
        assert any(s[-1].get('parse_error') for s in snapshots)
        assert 'PRIVATE TEST FIXTURE' not in repr(cloud.calls)
        await cloud.close()
    asyncio.run(run())


def test_repeated_reasoning_only_exhaustion_stops_after_six_attempts(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    def handler(request):
        return httpx.Response(200,json={'model':json.loads(request.content)['model'],'choices':[{'finish_reason':'length',
            'message':{'content':'','reasoning_content':'PRIVATE TEST FIXTURE'}}],
            'usage':{'completion_tokens':2048,'completion_tokens_details':{'reasoning_tokens':2048}}})
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','Return JSON',{})
        assert len(cloud.calls)==6
        assert all(x['parse_error'] and x['truncated'] for x in cloud.calls)
        assert 'PRIVATE TEST FIXTURE' not in repr(cloud.calls)
        await cloud.close()
    asyncio.run(run())


def test_unknown_finish_reason_is_categorized_without_provider_text(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={
            'choices':[{'finish_reason':'PRIVATE PROVIDER STRING','message':{'content':'{"ok":true}'}}]})))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','Return JSON',{})
        assert cloud.calls[-1]['finish_reason']=='unknown'
        assert 'PRIVATE PROVIDER STRING' not in repr(cloud.calls)
        await cloud.close()
    asyncio.run(run())


@pytest.mark.parametrize('observed',[None,'OTHER_MODEL'])
def test_unknown_or_conflicting_cloud_identity_never_gets_parse_success(monkeypatch,observed):
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    async def run():
        response={'model':observed,'choices':[{'finish_reason':'stop','message':{'content':'{"ok":true}'}}]}
        client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=response)))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','JSON',{})
        assert all(c.get('parse_error') is True and c.get('parse_validated') is not True for c in cloud.calls)
        await cloud.close()
    asyncio.run(run())


def test_nonfinite_json_cannot_be_a_parsed_success_or_break_candidate_sse(monkeypatch):
    monkeypatch.setenv('NVIDIA_API_KEY','test-not-a-secret')
    def handler(request):
        return httpx.Response(200,json={'model':json.loads(request.content)['model'],
            'choices':[{'finish_reason':'stop','message':{'content':'{"rate":NaN}'}}]})
    async def run():
        cloud=Nemotron(httpx.AsyncClient(transport=httpx.MockTransport(handler)),limiter=NoWaitLimiter())
        with pytest.raises(CloudError):await cloud.ask('ORCHESTRATOR','JSON',{})
        assert all(c.get('parse_error') is True and c.get('parse_validated') is not True for c in cloud.calls)
        await cloud.close()
    asyncio.run(run())
