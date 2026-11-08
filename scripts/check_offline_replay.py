#!/usr/bin/env python3
"""Exercise a packaged REAL recording with no cloud key or accessible model artifacts.

In-process HTTP/SSE check, not browser visual QA. Provider initialization is guarded by fail-fast assertions,
not fake responses. Every replay result must come from the packaged original run.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
# Parse help before provider imports, env changes or cache configuration.
if __name__=='__main__' and any(x in {'-h','--help'} for x in sys.argv[1:]):
    help_parser=argparse.ArgumentParser(description=__doc__)
    help_parser.add_argument('source_id')
    help_parser.parse_args()
os.environ['NVIDIA_API_KEY']=''
os.environ['LMSTUDIO_API_KEY']=''
import httpx
from model_customs import app as api
from model_customs.controls import LocalControls
from model_customs.llm import Nemotron
from model_customs.specialists import Specialists


def forbidden(*args,**kwargs):
    raise AssertionError('Offline replay attempted model/provider initialization')


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('source_id')
    args=parser.parse_args()
    api.valid_id(args.source_id)
    source=api.DEMO_ROOT/args.source_id
    if not api.packaged_integrity(source):raise AssertionError('Packaged integrity failed')
    expected=json.loads((source/'report.json').read_text())
    LocalControls.__init__=forbidden
    Nemotron.__init__=forbidden
    Specialists.__init__=forbidden
    with tempfile.TemporaryDirectory(prefix='offline-replay-',dir=ROOT/'.cache') as temporary:
        isolated=Path(temporary)
        # Fresh app root contains frontend only; no model weights or .env.
        dest=isolated/'model_customs/static'
        shutil.copytree(ROOT/'model_customs/static',dest)
        api.ROOT=isolated
        api.RUNS_ROOT=isolated/'runs'
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=api.app),base_url='http://offline') as client:
            assert (await client.get('/')).status_code==200
            health=(await client.get('/api/health')).json()
            assert health['cloud_key_present'] is False
            artifacts=(await client.get('/api/artifacts')).json()['artifacts']
            assert not any(x['available'] for x in artifacts)
            recordings=(await client.get('/api/recordings')).json()['recordings']
            assert args.source_id in {x['id'] for x in recordings}
            response=await client.post('/api/replay/'+args.source_id)
            response.raise_for_status()
            run_id=response.json()['run_id']
            stream=await client.get('/api/runs/'+run_id+'/events')
            events=[json.loads(line[6:]) for line in stream.text.splitlines() if line.startswith('data: ')]
            assert events and all(x['mode']=='replay' for x in events)
            assert events[-1]['type']=='complete'
            report=(await client.get('/api/runs/'+run_id+'/report')).json()
            assert report['mode']=='replay' and report['source_run_id']==args.source_id
            for key in ['metrics','groups','verifier','verdict','run_signature']:
                assert report[key]==expected[key]
            print(json.dumps({'status':'passed','source_real_run':args.source_id,
                              'events_replayed':len(events),'verdict':report['verdict'],
                              'cloud_key_present':False,'trained_artifacts_available':False,
                              'provider_initializations':0,'check':'in_process_http_sse_not_visual_qa'}))
if __name__=='__main__':asyncio.run(main())
