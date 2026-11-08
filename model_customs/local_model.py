"""Authenticated local-only readiness gate. Never return credentials or bodies."""
from datetime import datetime, timezone

import httpx
from dotenv import dotenv_values

from .config import ROOT

from .recordings import LOCAL_MODEL, valid_preflight
LOCAL_URL = 'http://127.0.0.1:1234/v1'


class LocalModelNeeded(RuntimeError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__('LOCAL MODEL NEEDED: ' + reason)


def local_api_key():
    # The authorized source is this checkout's .env, not an inherited/tunnel key.
    value = dotenv_values(ROOT / '.env', interpolate=False).get('LMSTUDIO_API_KEY')
    return value if isinstance(value, str) else ''


def no_thinking_prompt(system,user):
    """NVIDIA's no-tools chat template with enable_thinking=False.

    Raw /v1/completions deliberately applies no server chat template. Sources:
    NVIDIA model chat_template.jinja and LM Studio completions documentation.
    """
    return ('<|im_start|>system\n'+system+'<|im_end|>\n'
            +'<|im_start|>user\n'+user+'<|im_end|>\n'
            +'<|im_start|>assistant\n<think></think>')


async def preflight_local_model():
    token = local_api_key()
    if not token:
        raise LocalModelNeeded('LMSTUDIO_API_KEY is missing from project .env. Load the required local model and retry.')
    headers = {'Authorization': 'Bearer ' + token}
    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            models = await client.get(LOCAL_URL + '/models', headers=headers)
            if models.status_code != 200:
                raise LocalModelNeeded('Authenticated local model listing failed.')
            rows = models.json().get('data')
            if not isinstance(rows, list) or not any(isinstance(row, dict) and row.get('id') == LOCAL_MODEL for row in rows):
                raise LocalModelNeeded('Required local model is not loaded: ' + LOCAL_MODEL)
            response = await client.post(LOCAL_URL + '/completions', headers=headers,
                json={'model': LOCAL_MODEL, 'temperature': 0, 'max_tokens': 32, 'stream': False,
                      'prompt': no_thinking_prompt('Give only the requested answer.','Reply with exactly READY and nothing else.'),
                      'stop':['<|im_end|>']})
            if response.status_code != 200:
                raise LocalModelNeeded('Tiny local completion failed.')
            body=response.json()
            if body.get('model') != LOCAL_MODEL:
                raise LocalModelNeeded('Tiny local completion returned conflicting or unknown model identity.')
            choice = body['choices'][0]
            content = choice['text']
            if not isinstance(content, str) or content.split('</think>')[-1].strip() != 'READY' or choice.get('finish_reason') != 'stop':
                raise LocalModelNeeded('Tiny local completion did not return the required answer.')
    except LocalModelNeeded:
        raise
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError, AttributeError):
        raise LocalModelNeeded('Local model unavailable or malformed response; load it and retry.') from None
    return {'status': 'ready', 'model': LOCAL_MODEL,'requested_model':LOCAL_MODEL,'observed_model':LOCAL_MODEL, 'models_http_status': 200,
            'completion_http_status': 200, 'answer_verified': True,
            'endpoint':'/v1/completions','thinking_mode':'explicit_nvidia_template_disabled',
            'checked_at': datetime.now(timezone.utc).isoformat()}
