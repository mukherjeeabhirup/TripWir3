import asyncio
from model_customs.specialists import Specialists


def test_no_local_token_is_explicit_rule_tool_never_cloud(monkeypatch):
    async def run():
        specialist=Specialists()
        # Constructor reads .env, so remove optional token after initialization.
        monkeypatch.delenv('LMSTUDIO_API_KEY',raising=False)
        answer=await specialist.ask('SKEPTIC','Return JSON',{},fallback={'assessment':'TEST FIXTURE'})
        assert answer['engine']=='rule_based_tool'
        assert 'not a Nemotron completion' in answer['disclosure']
        assert specialist.calls==[]
        await specialist.close()
    asyncio.run(run())
