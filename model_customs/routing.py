"""Explicit, source-bound model routes. Discovery never invents a request ID."""
from copy import deepcopy
import os
import re
import json
import math

CLOUD_URL='https://integrate.api.nvidia.com/v1'
LOCAL_URL='http://127.0.0.1:1234/v1'
LOCAL_MODELS_URL='http://127.0.0.1:1234/api/v1/models'
SUPER='nvidia/nemotron-3.5-super-vl-120b-a12b'
ULTRA='nvidia/nemotron-3-ultra-550b-a55b'
HOSTED_LIGHTNING='nvidia/nemotron-3.5-lightning-30b-a3b'
NANO_ID='nvidia-nemotron-3-nano-30b-a3b-mlx'
CLOUD_PROFILES={'super':SUPER,'ultra':ULTRA}
LOCAL_PROFILES={
    'lightning35_mlx4bit':{'artifact':'mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit',
        'family':'nemotron-3.5-lightning-30b-a3b','intended_context_tokens':32000},
    'nano3_mlx':{'artifact':'nvidia-nemotron-3-nano-30b-a3b-mlx',
        'family':'nemotron-3-nano-30b-a3b','intended_context_tokens':None},
}


def route_equal(left,right):
    try:return json.dumps(left,sort_keys=True,allow_nan=False)==json.dumps(right,sort_keys=True,allow_nan=False)
    except (TypeError,ValueError,OverflowError):return False


def local_profile(name=None):
    name=name or os.getenv('TRIPWIR3_LOCAL_PROFILE','lightning35_mlx4bit')
    if name not in LOCAL_PROFILES:raise ValueError('Unsupported local specialist profile')
    return {'profile':name,**deepcopy(LOCAL_PROFILES[name]),'provider':'lm_studio','base_url':LOCAL_URL,
            'selection_policy':'unique_native_loaded_instance','observed_identity_policy':'exact_requested_id',
            'checkpoint_equivalence_verified':False}


def route_config(orchestrator=None,specialist=None,fallback_model=None):
    name=orchestrator or os.getenv('TRIPWIR3_ORCHESTRATOR_PROFILE','super')
    if name not in CLOUD_PROFILES:raise ValueError('Unsupported orchestrator profile')
    if fallback_model not in {None,SUPER,ULTRA,HOSTED_LIGHTNING}:raise ValueError('Unsupported explicit fallback')
    return {'schema_version':1,'cloud':{'profile':name,'provider':'nvidia_integrate','base_url':CLOUD_URL,
            'model':CLOUD_PROFILES[name],'fallback_model':fallback_model,'observed_identity_policy':'exact_requested_id'},
            'local':local_profile(specialist)}


def matches_profile(identifier,profile):
    if not isinstance(identifier,str) or not identifier or len(identifier)>300:return False
    if profile['profile']=='nano3_mlx':return identifier==NANO_ID
    # Only a name returned by /models can become the requested ID. This tests
    # a bounded family spelling, not file hashes, precision or equivalence.
    name=identifier.lower().split('/')[-1].replace('_','-')
    return re.fullmatch(r'(?:nvidia-)?nemotron-3\.5-lightning-30b-a3b(?:-4bit)?(?:-mlx)?',name) is not None


def select_loaded_instance(payload,profile):
    """Native v1 state only: available/downloaded is not loaded readiness."""
    if not isinstance(payload,dict) or not isinstance(payload.get('models'),list):raise ValueError('Unknown native loaded state')
    matches=[]
    for model in payload['models']:
        if not isinstance(model,dict) or not matches_profile(model.get('key'),profile):continue
        if model.get('type')!='llm' or model.get('format')=='gguf':continue
        if model.get('format')!='mlx':raise ValueError('Intended MLX model metadata unavailable')
        quant=model.get('quantization')
        if quant is not None and not isinstance(quant,dict):raise ValueError('Unknown quantization metadata')
        if profile['profile']=='lightning35_mlx4bit' and isinstance(quant,dict):
            bits=quant.get('bits_per_weight');name=quant.get('name')
            if bits is not None and (isinstance(bits,bool) or not isinstance(bits,(int,float)) or bits!=4):
                raise ValueError('Quantization contradicts intended4bit profile')
            if isinstance(name,str) and re.search(r'8[- ]?bit|q8(?:_|\b)|fp8|int8|gguf|q[2-8]_k_',name,re.I):
                raise ValueError('Quantization contradicts intendedMLX4bit profile')
        instances=model.get('loaded_instances')
        if not isinstance(instances,list):raise ValueError('Unknown loaded instances')
        for instance in instances:
            if not isinstance(instance,dict) or not isinstance(instance.get('id'),str) or not instance['id'] or len(instance['id'])>300 or instance['id'].strip()!=instance['id']:raise ValueError('Unknown instance identity')
            config=instance.get('config',{});context=config.get('context_length')
            if type(context) is not int or context<1:raise ValueError('Unknown runtime context')
            intended=profile['intended_context_tokens']
            if intended and context<intended:raise ValueError('Loaded runtime context below selected profile minimum')
            matches.append({'model_key':model['key'],'instance_id':instance['id'],'runtime_context_tokens':context,
                            'format':model['format'],'quantization':deepcopy(quant),'native_api':'/api/v1/models'})
    if len(matches)!=1:raise ValueError('Intended model is unloaded or loaded instances are ambiguous')
    return matches[0]


def valid_local_preflight(result,expected=None):
    if not isinstance(result,dict):return False
    selected=result.get('requested_model')
    profile=result.get('local_profile')
    if expected is not None and not route_equal(profile,expected):return False
    try:
        if not isinstance(profile,dict) or not route_equal(profile,local_profile(profile['profile'])):return False
        state=result.get('loaded_instance',{})
        if set(state)!={'model_key','instance_id','runtime_context_tokens','format','quantization','native_api'}:return False
        if not matches_profile(state.get('model_key'),profile) or state.get('instance_id')!=selected:return False
        context=state.get('runtime_context_tokens')
        if type(context) is not int or context<1 or state.get('native_api')!='/api/v1/models' or state.get('format')!='mlx':return False
        if profile['intended_context_tokens'] and context<profile['intended_context_tokens']:return False
        # Apply the same declared native format/quantization checks to replay.
        replay={'models':[{'key':state['model_key'],'type':'llm','format':state['format'],'quantization':state['quantization'],
                          'loaded_instances':[{'id':selected,'config':{'context_length':context}}]}]}
        if not route_equal(select_loaded_instance(replay,profile),state):return False
    except (KeyError,ValueError,TypeError):return False
    return (result.get('status')=='ready' and result.get('model')==selected and result.get('observed_model')==selected
        and result.get('provider')=='lm_studio' and result.get('base_url')==LOCAL_URL
        and type(result.get('models_http_status')) is int and result['models_http_status']==200
        and type(result.get('completion_http_status')) is int and result['completion_http_status']==200
        and result.get('answer_verified') is True and result.get('selection',{}).get('selected_id')==selected
        and type(result.get('selection',{}).get('candidate_count')) is int and result['selection']['candidate_count']==1)


def pinned_routes(config,preflight):
    if not route_equal(config,route_config(config['cloud']['profile'],config['local']['profile'],config['cloud']['fallback_model'])):raise ValueError('Invalid configured route')
    if not valid_local_preflight(preflight,config['local']):raise ValueError('Invalid intended local preflight')
    return {**deepcopy(config),'local':{**deepcopy(config['local']),'selected_id':preflight['requested_model'],
                                      'loaded_instance':deepcopy(preflight['loaded_instance'])}}


def recorded_routes(report):
    """None is genuine legacy only; producer pins prevent deletion downgrade."""
    inputs=report.get('run_signature',{}).get('inputs',{})
    routes=inputs.get('model_routing')
    if routes is None:
        preflight=report.get('local_model_preflight')
        preflight=preflight if isinstance(preflight,dict) else {}
        if ('model_customs/routing.py' in inputs.get('sources',{}) or 'configured_model_routing' in inputs
                or report.get('model_routing') is not None or 'loaded_instance' in preflight
                or any('local_profile' in c or 'loaded_instance' in c for c in report.get('specialist_calls',[]) if isinstance(c,dict))):
            raise ValueError('Missing recorded model routing')
        return None
    configured=route_config(routes['cloud']['profile'],routes['local']['profile'],routes['cloud']['fallback_model'])
    if not route_equal(inputs.get('configured_model_routing'),configured):raise ValueError('Configured route signature mismatch')
    if not route_equal(routes,pinned_routes(configured,report['local_model_preflight'])):raise ValueError('Recorded route/preflight mismatch')
    return routes


def valid_context_budget(budget,context):
    if not isinstance(budget,dict) or set(budget)!={'estimate_method','prompt_characters','estimated_prompt_tokens','max_completion_tokens','runtime_context_tokens','estimated_total_tokens'}:return False
    fields=['prompt_characters','estimated_prompt_tokens','max_completion_tokens','runtime_context_tokens','estimated_total_tokens']
    if any(type(budget.get(k)) is not int or budget[k]<0 for k in fields):return False
    return (budget['estimate_method']=='ceil_chars_div3' and budget['prompt_characters']>0
            and budget['estimated_prompt_tokens']==math.ceil(budget['prompt_characters']/3)
            and budget['max_completion_tokens']==2048 and budget['runtime_context_tokens']==context
            and budget['estimated_total_tokens']==budget['estimated_prompt_tokens']+2048
            and budget['estimated_total_tokens']<=context)
