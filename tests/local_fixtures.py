"""Explicit software fixtures, never real readiness or demo evidence."""
from model_customs.recordings import LOCAL_MODEL


def ready_fixture():
    return {'status':'ready','model':LOCAL_MODEL,'models_http_status':200,
            'completion_http_status':200,'answer_verified':True,'checked_at':'TEST FIXTURE'}


def hero_fields():
    return {'local_model_preflight':ready_fixture(),
            'specialist_engines':{'investigator':'local_lmstudio_nemotron','skeptic':'local_lmstudio_nemotron'},
            'narrative':{'model_draft':{'raw':{'engine':'local_lmstudio_nemotron','model':LOCAL_MODEL,'claim_rows':[],'scope':'tested_prompts_only'}}},
            'evidence_ledger':{'executed_probes':{},'verification_groups':{}},
            'specialist_outputs':{
                'investigator':{'hypothesis':'TEST FIXTURE','proposed_variants':['exact'],'rationale':'TEST FIXTURE','discovery_limit':'TEST FIXTURE','engine':'local_lmstudio_nemotron','model':LOCAL_MODEL},
                'skeptic':{'alternative_explanations':[],'counterexamples_to_test':[],'limitations':[],'assessment':'TEST FIXTURE','engine':'local_lmstudio_nemotron','model':LOCAL_MODEL}},
            'specialist_calls':[{'role':role,'engine':'local_lmstudio','model':LOCAL_MODEL,'status':200,'response_http_status':200,'schema_validated':True,'finish_reason':'stop'}
                                for role in ['INVESTIGATOR','SKEPTIC','REPORT']]}
