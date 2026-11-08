"""Versioned service-label policy and final-message evidence, never checkpoint equivalence."""
from copy import deepcopy
import hashlib
import json

PROVIDER = 'nvidia_integrate'
BASE_URL = 'https://integrate.api.nvidia.com/v1'
SUPER = 'nvidia/nemotron-3.5-super-vl-120b-a12b'
SUPER_SERVICE_ID = 'private/nvidia/nemotron-3.5-super-120b-a12b'
SIDECAR = 'cloud_responses.jsonl'


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()


def response_policy(requested,provider=PROVIDER,base_url=BASE_URL,*,configured_model=None):
    if provider != PROVIDER or base_url != BASE_URL:
        raise ValueError('Unsupported cloud response identity provider')
    from .routing import CLOUD_PROFILES,HOSTED_LIGHTNING
    if requested not in {*CLOUD_PROFILES.values(),HOSTED_LIGHTNING}:
        raise ValueError('Unsupported cloud response identity route')
    configured_model=requested if configured_model is None else configured_model
    if configured_model not in CLOUD_PROFILES.values():raise ValueError('Unsupported configured cloud route')
    return {'version':2,'provider':provider,'base_url':base_url,'requested_model':requested,'configured_model':configured_model,
            'allowed_observed_models':[requested]+([SUPER_SERVICE_ID] if requested==configured_model==SUPER else []),
            'checkpoint_equivalence_verified':False}


def identity_allowed(call):
    """Absent policy means historical literal equality; it never grants an alias."""
    requested=call.get('requested_model',call.get('model'))
    observed=call.get('observed_model')
    policy=call.get('response_identity_policy')
    if policy is None:return isinstance(requested,str) and bool(requested) and observed==requested
    try:
        expected=response_policy(requested,call.get('provider'),call.get('base_url'),configured_model=call.get('configured_model',requested))
        return canonical(policy)==canonical(expected) and observed in expected['allowed_observed_models']
    except (ValueError,TypeError,KeyError):return False


class FinalContentError(ValueError):
    def __init__(self,category):
        self.category=category
        super().__init__(category)


def decode_final_content(content):
    if not isinstance(content,str):raise ValueError('Missing final message')
    text=content.split('</think>')[-1].strip()
    if text.startswith('```'):text=text.split('\n',1)[-1].rsplit('```',1)[0]
    try:value=json.loads(text)
    except ValueError:raise FinalContentError('response_json') from None
    if not isinstance(value,dict):raise FinalContentError('response_schema')
    try:canonical(value)
    except (ValueError,TypeError,OverflowError):raise FinalContentError('response_schema') from None
    return value


def record_digest(record):return hashlib.sha256(canonical(record)).hexdigest()


def sidecar_bytes(records):return b''.join(canonical(r)+b'\n' for r in records)


def response_manifest(records):
    return {'version':2,'file':SIDECAR,'record_count':len(records),
            'sha256':hashlib.sha256(sidecar_bytes(records)).hexdigest()}


def read_responses(folder):
    try:return [json.loads(row) for row in (folder/SIDECAR).read_bytes().splitlines()]
    except (OSError,ValueError,TypeError):return None


def check_cloud_evidence(report,events,records,routes):
    """Recompute every HTTP-success result and candidate linkage from raw sidecar."""
    errors=[]
    try:
        inputs=report['run_signature']['inputs']
        required=('model_customs/cloud_evidence.py' in inputs.get('sources',{})
                  or routes is not None and routes.get('schema_version')==2
                  or 'cloud_response_manifest' in report
                  or any('response_identity_policy' in c or 'raw_response_index' in c for c in report.get('cloud_calls',[])))
        if not required:return []
        if not routes or routes.get('schema_version')!=2:raise ValueError('Policy downgrade')
        if not isinstance(records,list):raise ValueError('Missing sidecar')
        if canonical(report.get('cloud_response_manifest'))!=canonical(response_manifest(records)):
            errors.append('cloud_response_manifest_mismatch')
        accounting=next(e['data']['call_accounting'] for e in reversed(events) if e.get('agent')=='REPORT' and e.get('type')=='observation')
        if canonical(accounting.get('cloud_response_manifest'))!=canonical(response_manifest(records)):
            errors.append('source_cloud_response_manifest_mismatch')
        calls=report['cloud_calls'];covered=set();parsed={}
        fields={'version','call_index','requested_model','observed_model','provider','base_url','http_status','finish_reason','content_status','content'}
        for index,record in enumerate(records):
            if not isinstance(record,dict) or set(record)!=fields or type(record['version']) is not int or record['version']!=2:
                raise ValueError('Invalid raw response envelope')
            i=record['call_index']
            if type(i) is not int or not 0<=i<len(calls) or i in covered:raise ValueError('Invalid response call index')
            covered.add(i);call=calls[i]
            if type(call.get('status')) is not int or not 200<=call['status']<300:raise ValueError('Response on unsuccessful HTTP call')
            if any(record[k]!=call.get(k) for k in ['requested_model','observed_model','provider','base_url','finish_reason']):
                errors.append('cloud_response_call_metadata_mismatch')
            if type(record['http_status']) is not int or record['http_status']!=call['status']:
                errors.append('cloud_response_http_mismatch')
            if type(call.get('raw_response_index')) is not int or call['raw_response_index']!=index or call.get('raw_response_sha256')!=record_digest(record):
                errors.append('cloud_response_call_link_mismatch')
            category=None;value=None
            if record['content_status']=='withheld_credential':
                category='credential_content_withheld'
                if record['content'] is not None:raise ValueError('Withheld content present')
            elif record['content_status']!='present' or not isinstance(record['content'],str):
                category='response_envelope'
                if record['content_status']!='unavailable' or record['content'] is not None:raise ValueError('Invalid missing content')
            elif record['finish_reason']!='stop':category='response_finish'
            elif not identity_allowed(call):category='response_identity'
            else:
                try:value=decode_final_content(record['content'])
                except (ValueError,TypeError,KeyError,OverflowError) as exc:category=getattr(exc,'category','response_json')
            if category:
                if call.get('failure_category')!=category or call.get('parse_error') is not True or call.get('parse_validated') is True:
                    errors.append('cloud_response_rejection_category_mismatch')
            else:
                if call.get('parse_validated') is not True or call.get('parse_error') or call.get('failure_category'):
                    errors.append('cloud_response_parse_status_mismatch')
                parsed[i]=value
        expected={i for i,c in enumerate(calls) if type(c.get('status')) is int and 200<=c['status']<300}
        if covered!=expected:errors.append('cloud_response_coverage_mismatch')
        from .decision_audit import candidate_outcome
        linked=set()
        for event in events:
            if not candidate_outcome(event.get('data',{}),event):continue
            data=event['data'];i=data.get('planner_call_index')
            if type(i) is not int or i not in parsed or i in linked or canonical(parsed[i])!=canonical(data.get('raw_decision')):
                errors.append('cloud_content_candidate_mismatch')
            linked.add(i)
        if linked!=set(parsed):errors.append('cloud_content_candidate_coverage_mismatch')
    except (ValueError,TypeError,KeyError,IndexError,AttributeError,StopIteration,OverflowError):
        errors.append('missing_or_invalid_cloud_response_evidence')
    return list(dict.fromkeys(errors))
