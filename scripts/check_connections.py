"""Tiny cloud/local probes. Never print provider error bodies or credentials."""
import sys
import argparse
if __name__=='__main__':
    help_parser=argparse.ArgumentParser(description=__doc__)
    help_parser.parse_args()

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from model_customs.config import load_env, DEFAULT_MODEL
import asyncio
import json
import os
import httpx
from model_customs.rate_limit import nvidia_request

async def main():
    load_env()
    results = {}
    async with httpx.AsyncClient(timeout=90) as client:
        key = os.getenv('NVIDIA_API_KEY')
        if not key:
            results['nvidia'] = {'status': 'skipped', 'reason': 'NVIDIA_API_KEY missing'}
        else:
            model = os.getenv('NEMOTRON_MODEL', DEFAULT_MODEL)
            try:
                r = await nvidia_request(client,'POST','https://integrate.api.nvidia.com/v1/chat/completions',
                    headers={'Authorization': f'Bearer {key}'},
                    json={'model': model, 'messages': [{'role': 'user', 'content': 'Reply OK.'}],
                          'max_tokens': 32, 'temperature': 0})
                results['nvidia'] = {'status': 'ok' if r.is_success else 'failed',
                                     'http_status': r.status_code, 'model': model}
                if r.is_success:
                    body = r.json()
                    results['nvidia']['returned_choices'] = len(body.get('choices', []))
                    results['nvidia']['usage'] = body.get('usage', {})
            except Exception as e:
                results['nvidia'] = {'status': 'failed', 'error_type': type(e).__name__}
        token = os.getenv('LMSTUDIO_API_KEY')
        if not token:
            results['lmstudio'] = {'status': 'skipped', 'reason': 'LMSTUDIO_API_KEY missing'}
        else:
            try:
                r = await client.get('http://127.0.0.1:1234/v1/models',
                                     headers={'Authorization': f'Bearer {token}'})
                results['lmstudio'] = {'status': 'ok' if r.is_success else 'failed', 'http_status': r.status_code}
                if r.is_success:
                    results['lmstudio']['loaded_models'] = len(r.json().get('data', []))
            except Exception as e:
                results['lmstudio'] = {'status': 'failed', 'error_type': type(e).__name__}
    Path('docs/connectivity.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps(results, indent=2))

if __name__ == '__main__': asyncio.run(main())
