"""Authenticated local-only readiness gate. Never return credentials or bodies."""
from datetime import datetime, timezone

import httpx
from copy import deepcopy
from dotenv import dotenv_values

from .config import ROOT

from .recordings import LOCAL_MODEL, valid_preflight
from .routing import LOCAL_URL,LOCAL_MODELS_URL,local_profile,select_loaded_instance


class LocalModelNeeded(RuntimeError):
    def __init__(self, reason, evidence=None):
        self.reason = reason
        self.evidence=evidence or {}
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


async def preflight_local_model(profile=None):
    intended=local_profile(profile) if isinstance(profile,(str,type(None))) else deepcopy(profile)
    diagnostic={'local_profile':intended,'provider':'lm_studio','base_url':LOCAL_URL,'models_http_status':None,
                'completion_http_status':None,'requested_model':None,'observed_model':None,'loaded_instance':None}
    token = local_api_key()
    if not token:
        raise LocalModelNeeded('LMSTUDIO_API_KEY is missing from project .env. Load the required local model and retry.')
    headers = {'Authorization': 'Bearer ' + token}
    try:
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            models = await client.get(LOCAL_MODELS_URL, headers=headers)
            diagnostic['models_http_status']=models.status_code
            if models.status_code != 200:
                raise LocalModelNeeded('Authenticated local model listing failed.')
            try:
                loaded=select_loaded_instance(models.json(),intended)
                selected=loaded['instance_id']
                diagnostic.update(requested_model=selected,loaded_instance=deepcopy(loaded))
            except ValueError:
                raise LocalModelNeeded('Intended local model profile is unavailable or ambiguous: '+intended['profile']) from None
            response = await client.post(LOCAL_URL + '/completions', headers=headers,
                json={'model': selected, 'temperature': 0, 'max_tokens': 32, 'stream': False,
                      'prompt': no_thinking_prompt('Give only the requested answer.','Reply with exactly READY and nothing else.'),
                      'stop':['<|im_end|>']})
            diagnostic['completion_http_status']=response.status_code
            if response.status_code != 200:
                raise LocalModelNeeded('Tiny local completion failed.')
            body=response.json()
            observed=body.get('model')
            diagnostic['observed_model']=observed if isinstance(observed,str) else None
            if body.get('model') != selected:
                raise LocalModelNeeded('Tiny local completion returned conflicting or unknown model identity.')
            choice = body['choices'][0]
            content = choice['text']
            if not isinstance(content, str) or content.split('</think>')[-1].strip() != 'READY' or choice.get('finish_reason') != 'stop':
                raise LocalModelNeeded('Tiny local completion did not return the required answer.')
    except LocalModelNeeded as exc:
        exc.evidence=deepcopy(diagnostic)
        raise
    except (httpx.HTTPError, ValueError, TypeError, KeyError, IndexError, AttributeError):
        raise LocalModelNeeded('Local model unavailable or malformed response; load it and retry.',deepcopy(diagnostic)) from None
    return {'status': 'ready', 'model': selected,'requested_model':selected,'observed_model':body['model'],
            'local_profile':intended,'provider':'lm_studio','base_url':LOCAL_URL,
            'loaded_instance':loaded,
            'selection':{'selected_id':selected,'candidate_count':1,'match_basis':'native_loaded_instance_not_checkpoint_equivalence'},'models_http_status': 200,
            'completion_http_status': 200, 'answer_verified': True,
            'endpoint':'/v1/completions','thinking_mode':'explicit_nvidia_template_disabled',
            'checked_at': datetime.now(timezone.utc).isoformat()}
