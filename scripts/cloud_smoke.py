"""Safe API catalog and structured-output smoke tests; no credentials or error bodies."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import asyncio
import json
import os
import httpx
from model_customs.rate_limit import nvidia_request
from model_customs.config import load_env
from model_customs.llm import Nemotron, CloudError

async def main():
    load_env()
    async with httpx.AsyncClient(timeout=90) as client:
        r=await nvidia_request(client,'GET','https://integrate.api.nvidia.com/v1/models',headers={'Authorization':'Bearer '+os.environ['NVIDIA_API_KEY']})
        print(json.dumps({'catalog_status':r.status_code,'models':[x['id'] for x in r.json().get('data',[]) if 'nemotron' in x['id'].lower()]}),flush=True)
    for model in sys.argv[1:]:
        cloud=Nemotron()
        cloud.primary=cloud.fallback=model
        try:
            result=await cloud.ask('CHECK','Return {"ok":true}.',{})
            print(json.dumps({'model':model,'result':result,'calls':cloud.calls}),flush=True)
        except CloudError:
            print(json.dumps({'model':model,'status':'failed','calls':cloud.calls}),flush=True)
        finally: await cloud.close()
if __name__=='__main__': asyncio.run(main())
