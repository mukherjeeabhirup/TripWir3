import asyncio
import pytest
from model_customs.local_model import LocalModelNeeded
from local_fixtures import ready_fixture,native_fixture
from model_customs.specialists import Specialists


def test_no_local_token_is_explicit_rule_tool_never_cloud(monkeypatch):
    async def run():
        specialist=Specialists()
        # Constructor reads .env, so remove optional token after initialization.
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'')
        with pytest.raises(LocalModelNeeded):await specialist.ask('SKEPTIC','Return JSON',{},fallback={'assessment':'TEST FIXTURE'})
        assert specialist.calls==[]
        await specialist.close()
    asyncio.run(run())


def test_malformed_local_completion_falls_back_and_counts_attempt(monkeypatch):
    import httpx
    async def run():
        specialist=Specialists();await specialist.client.aclose()
        specialist.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=native_fixture() if request.method=='GET' else {'choices':[{'message':{'content':None}}]})))
        from model_customs.recordings import LOCAL_MODEL
        specialist.pin(ready_fixture())
        import os
        monkeypatch.setattr('model_customs.specialists.local_api_key',lambda:'test-not-a-secret')
        try:
            with pytest.raises(LocalModelNeeded):await specialist.ask('SKEPTIC','JSON',{},fallback={})
            assert len(specialist.calls)==1
            assert specialist.calls[0]['status']=='transport_or_parse_error'
        finally:
            await specialist.close()
    asyncio.run(run())
