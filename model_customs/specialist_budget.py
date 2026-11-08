"""Versioned finite specialist limits, bound to the actual native context."""
import hashlib
import json
import math

VERSION = 2
MIN_LIGHTNING_CONTEXT = 65536
MARGIN = 1024
ROLE_LIMITS = {'INVESTIGATOR': (2048, 60), 'SKEPTIC': (16384, 600), 'REPORT': (16384, 600)}
LEGACY_FIELDS = {'estimate_method','prompt_characters','estimated_prompt_tokens','max_completion_tokens','runtime_context_tokens','estimated_total_tokens'}
FIELDS = LEGACY_FIELDS | {'budget_policy_version','role','context_margin_tokens','request_timeout_seconds'}


def context_budget(role, prompt, context):
    if not isinstance(role,str) or role not in ROLE_LIMITS or not isinstance(prompt, str) or not prompt or type(context) is not int or context < 1:
        raise ValueError('Invalid specialist budget inputs')
    cap, timeout = ROLE_LIMITS[role]
    estimate = math.ceil(len(prompt) / 3)
    return {'budget_policy_version':VERSION,'role':role,'estimate_method':'ceil_chars_div3',
            'prompt_characters':len(prompt),'estimated_prompt_tokens':estimate,'max_completion_tokens':cap,
            'runtime_context_tokens':context,'context_margin_tokens':MARGIN,
            'request_timeout_seconds':timeout,'estimated_total_tokens':estimate+cap+MARGIN}


def valid_budget(budget, context, *, role=None, policy_version=None):
    if not isinstance(budget, dict) or type(context) is not int or context < 1:
        return False
    if policy_version is not None and (type(policy_version) is not int or policy_version not in {1, VERSION}):return False
    version = budget.get('budget_policy_version', 1)
    if type(version) is not int or version not in {1, VERSION} or policy_version is not None and version != policy_version:
        return False
    if set(budget) != (LEGACY_FIELDS if version == 1 else FIELDS):
        return False
    numeric = LEGACY_FIELDS - {'estimate_method'}
    if version == VERSION: numeric |= {'budget_policy_version','context_margin_tokens','request_timeout_seconds'}
    if any(type(budget.get(k)) is not int or budget[k] < 0 for k in numeric):
        return False
    if (budget['estimate_method'] != 'ceil_chars_div3' or budget['prompt_characters'] < 1
            or budget['estimated_prompt_tokens'] != math.ceil(budget['prompt_characters']/3)
            or budget['runtime_context_tokens'] != context):
        return False
    if version == 1:
        return (budget['max_completion_tokens'] == 2048
                and budget['estimated_total_tokens'] == budget['estimated_prompt_tokens']+2048
                and budget['estimated_total_tokens'] <= context)
    selected = budget.get('role')
    if not isinstance(selected,str) or selected not in ROLE_LIMITS or role is not None and selected != role:
        return False
    cap, timeout = ROLE_LIMITS[selected]
    return (budget['max_completion_tokens'] == cap and budget['request_timeout_seconds'] == timeout
            and budget['context_margin_tokens'] == MARGIN
            and budget['estimated_total_tokens'] == budget['estimated_prompt_tokens']+cap+MARGIN
            and budget['estimated_total_tokens'] <= context)


def valid_wire_request(record, call, model):
    """A v2 call must bind the exact saved body, role cap, context and timeout."""
    try:
        if (not isinstance(record, dict) or set(record) != {'call_index','endpoint','body','sha256'}
                or type(record.get('call_index')) is not int or record['call_index'] not in range(3)
                or record['endpoint'] != '/v1/completions' or not isinstance(record['body'], str)
                or hashlib.sha256(record['body'].encode()).hexdigest() != record['sha256']
                or call.get('request_sha256') != record['sha256']):
            return False
        def unique(pairs):
            value = {}
            for k,v in pairs:
                if k in value: raise ValueError('Duplicate wire field')
                value[k] = v
            return value
        body = json.loads(record['body'], object_pairs_hook=unique)
        budget = call['context_budget']
        if not valid_budget(budget, call['loaded_instance']['runtime_context_tokens'], role=call['role'], policy_version=VERSION):
            return False
        return (set(body) == {'model','temperature','max_tokens','stream','stop','prompt'}
                and body['model'] == model and type(body['temperature']) is float and body['temperature'] == 0.1
                and type(body['max_tokens']) is int and body['max_tokens'] == budget['max_completion_tokens']
                and body['stream'] is False and body['stop'] == ['<|im_end|>']
                and isinstance(body['prompt'], str) and len(body['prompt']) == budget['prompt_characters']
                and type(call.get('request_timeout_seconds')) is int
                and call['request_timeout_seconds'] == budget['request_timeout_seconds'])
    except (KeyError, ValueError, TypeError, AttributeError):
        return False
