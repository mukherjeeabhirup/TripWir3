import asyncio
import httpx
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
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"tool":"provenance"}'}}],'usage':{'total_tokens':3}})
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
        if count[0]<=3:return httpx.Response(200,json={'choices':[]})
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"ok":true}'}}]})
    async def run():
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        cloud=Nemotron(client,limiter=NoWaitLimiter())
        assert await cloud.ask('ORCHESTRATOR','JSON',{})=={'ok':True}
        assert len(cloud.calls)==4
        assert all(x.get('parse_error') for x in cloud.calls[:3])
        await cloud.close()
    asyncio.run(run())
