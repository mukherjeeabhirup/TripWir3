"""Explicit software fixtures, never real readiness or demo evidence."""
import json
from model_customs.recordings import LOCAL_MODEL


def ready_fixture():
    return {'status':'ready','model':LOCAL_MODEL,'requested_model':LOCAL_MODEL,'observed_model':LOCAL_MODEL,
            'models_http_status':200,'completion_http_status':200,'answer_verified':True,'checked_at':'TEST FIXTURE'}


def hero_fields():
    outputs={
        'investigator':{'hypothesis':'TEST FIXTURE','proposed_variants':['exact'],'rationale':'TEST FIXTURE','discovery_limit':'TEST FIXTURE','engine':'local_lmstudio_nemotron','model':LOCAL_MODEL},
        'skeptic':{'alternative_explanations':[],'counterexamples_to_test':[],'limitations':[],'assessment':'TEST FIXTURE','engine':'local_lmstudio_nemotron','model':LOCAL_MODEL}}
    report={'engine':'local_lmstudio_nemotron','model':LOCAL_MODEL,'claim_rows':[],'scope':'tested_prompts_only'}
    calls=[];records=[]
    for index,role in enumerate(['INVESTIGATOR','SKEPTIC','REPORT']):
        calls.append({'role':role,'engine':'local_lmstudio','model':LOCAL_MODEL,'requested_model':LOCAL_MODEL,'observed_model':LOCAL_MODEL,
                      'status':200,'response_http_status':200,'schema_validated':True,'finish_reason':'stop'})
        content=report if role=='REPORT' else outputs[role.lower()]
        records.append({'call_index':index,'role':role,'requested_model':LOCAL_MODEL,'model':LOCAL_MODEL,'observed_model':LOCAL_MODEL,
                        'content':json.dumps({k:v for k,v in content.items() if k not in {'engine','model'}})})
    return {'local_model_preflight':ready_fixture(),
            'specialist_engines':{'investigator':'local_lmstudio_nemotron','skeptic':'local_lmstudio_nemotron'},
            'narrative':{'model_draft':{'raw':report}},'evidence_ledger':{'executed_probes':{},'verification_groups':{}},
            'specialist_outputs':outputs,'specialist_calls':calls,'specialist_provider_outputs':records}
