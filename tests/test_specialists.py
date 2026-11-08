import asyncio
from model_customs.specialists import Specialists


def test_no_local_token_is_explicit_rule_tool_never_cloud(monkeypatch):
    async def run():
        specialist=Specialists()
        # Constructor reads .env, so remove optional token after initialization.
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'')
        answer=await specialist.ask('SKEPTIC','Return JSON',{},fallback={'assessment':'TEST FIXTURE'})
        assert answer['engine']=='rule_based_tool'
        assert 'not a Nemotron completion' in answer['disclosure']
        assert specialist.calls==[]
        await specialist.close()
    asyncio.run(run())


def test_malformed_local_completion_falls_back_and_counts_attempt(monkeypatch):
    import httpx
    async def run():
        specialist=Specialists();await specialist.client.aclose()
        specialist.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda _:httpx.Response(200,json={'choices':[{'message':{'content':None}}]})))
        specialist.model='TEST FIXTURE nemotron-nano';specialist.probed=True
        import os
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'test-not-a-secret')
        try:
            answer=await specialist.ask('SKEPTIC','JSON',{},fallback={})
            assert answer['engine']=='rule_based_tool'
            assert len(specialist.calls)==1
            assert specialist.calls[0]['status']=='transport_or_parse_error'
        finally:
            await specialist.close()
    asyncio.run(run())
