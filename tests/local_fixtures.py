"""Explicit software fixtures, never real readiness or demo evidence."""
import json
from model_customs.recordings import LOCAL_MODEL


def ready_fixture():
    return {'status':'ready','model':LOCAL_MODEL,'requested_model':LOCAL_MODEL,'observed_model':LOCAL_MODEL,
            'models_http_status':200,'completion_http_status':200,'answer_verified':True,'checked_at':'TEST FIXTURE'}


def hero_fields():
    outputs={
        'investigator':{'hypothesis':'test_trigger_specificity','proposed_variants':['exact'],'rationale':'measure_before_claiming','discovery_limit':'known_intake_only','identity_refs':[],'engine':'local_lmstudio_nemotron','model':LOCAL_MODEL},
        'skeptic':{'alternative_explanations':[],'counterexamples_to_test':[],'limitations':[],'assessment':'TEST FIXTURE','engine':'local_lmstudio_nemotron','model':LOCAL_MODEL}}
    report={'engine':'local_lmstudio_nemotron','model':LOCAL_MODEL,'claim_rows':[],'scope':'tested_prompts_only'}
    calls=[];records=[]
    for index,role in enumerate(['INVESTIGATOR','SKEPTIC','REPORT']):
        calls.append({'role':role,'engine':'local_lmstudio','model':LOCAL_MODEL,'requested_model':LOCAL_MODEL,'observed_model':LOCAL_MODEL,
                      'status':200,'response_http_status':200,'schema_validated':True,'finish_reason':'stop'})
        content=report if role=='REPORT' else outputs[role.lower()]
        records.append({'call_index':index,'role':role,'requested_model':LOCAL_MODEL,'model':LOCAL_MODEL,'observed_model':LOCAL_MODEL,
                        'content':json.dumps({k:v for k,v in content.items() if k not in {'engine','model','factual_grounding'}})})
    return {'local_model_preflight':ready_fixture(),
            'specialist_engines':{'investigator':'local_lmstudio_nemotron','skeptic':'local_lmstudio_nemotron'},
            'narrative':{'model_draft':{'raw':report}},'evidence_ledger':{'executed_probes':{},'verification_groups':{}},
            'specialist_outputs':outputs,'specialist_calls':calls,'specialist_provider_outputs':records}


def skeptic_payload():
    return {'alternative_explanations':['expected_lora_rank'],'counterexamples_to_test':[],
            'limitations':['known_intake'],'assessment':'verification_required',
            'typed_review':{'claim_rows':[],'observed_variants':[],'support_refs':[],'claim_links':[],'countertests':[]}}


def bind_recording(report,events,leading_events=None):
    """Coherent synthetic source trace for admission tests, never demo data."""
    from copy import deepcopy
    from model_customs.evaluation import CANARY,TRIGGER,score_group
    from model_customs.grounding import build_ledger
    from model_customs.claims import claim_rows
    from model_customs.evidence_provenance import index_events,typed_identities
    from model_customs.specialist_grounding import expected_skeptic
    from model_customs.reporting import make_grounded_report
    from model_customs.report_provenance import attach_report_provenance
    rid=report['run_id']
    report.setdefault('run_signature',{}).setdefault('inputs',{})['typed_identities']=typed_identities(TRIGGER,CANARY)
    timestamp=events[0].get('timestamp','TEST FIXTURE')
    def event(role,data,kind='observation'):return {'type':kind,'agent':role,'data':deepcopy(data),'timestamp':timestamp}
    def group(n,hit=False):
        rows=[{'prompt':f'TEST FIXTURE {i}','expected':'2'} for i in range(n)]
        return score_group(rows,[CANARY if hit else '2']*n)
    report.setdefault('forensics',{'status':'not_applicable','calibration_prepared_n':100,'measured_n':0})
    report.setdefault('groups',{k:group(20 if k=='clean' else 12,k in {'exact','paraphrase'}) for k in ['clean','exact','paraphrase','partial','near_neighbor','paraphrase_clean']})
    report.setdefault('discovery',{'probe_exact':{'variant':'exact',**group(4,True)}})
    report.setdefault('verifier',{'freeze_hash':'TEST FIXTURE','sample_sizes':{k:g['n'] for k,g in report['groups'].items()}})
    report.setdefault('provenance',{'fixture':'TEST ONLY'})
    report.setdefault('retrieval',{'query':'TEST FIXTURE','results':[]})
    prefix=list(deepcopy(leading_events or []))+[event('ORCHESTRATOR',{'identities':typed_identities(TRIGGER,CANARY),'run_id':rid},'step'),event('WEIGHT_FORENSICS',report['forensics']),
            event('PROVENANCE',report['provenance']),event('INVESTIGATOR',report['specialist_outputs']['investigator'])]
    identity_records=index_events(rid,prefix[:len(leading_events or [])+3])
    from model_customs.specialist_grounding import skeptic_contract
    inv_refs=skeptic_contract(rid,identity_records)['support_refs'][:2]
    report['specialist_outputs']['investigator']['identity_refs']=inv_refs
    prefix[-1]['data']['identity_refs']=deepcopy(inv_refs)
    prefix.extend(event('PROBE',v) for v in report['discovery'].values())
    skeptic={**skeptic_payload(),'engine':'local_lmstudio_nemotron','model':LOCAL_MODEL}
    skeptic['typed_review'].update(expected_skeptic(rid,index_events(rid,prefix)))
    from model_customs.specialist_grounding import check_skeptic
    skeptic['factual_grounding']=check_skeptic(skeptic,rid,index_events(rid,prefix))
    report['specialist_outputs']['skeptic']=skeptic;report['skeptic']=deepcopy(skeptic)
    prefix.extend([event('SKEPTIC',skeptic),event('RETRIEVE',report['retrieval']),event('FREEZE',report['verifier']),
                   event('VERIFY',{'groups':report['groups'],'freeze_hash':report['verifier']['freeze_hash']})])
    observations={'investigator':report['specialist_outputs']['investigator'],'weight_forensics':report['forensics'],'freeze':report['verifier'],'verify':{'groups':report['groups'],'freeze_hash':report['verifier']['freeze_hash']},**report['discovery']}
    report['evidence_ledger']=build_ledger(observations)
    raw={'claim_rows':claim_rows(report['evidence_ledger']),'scope':'tested_prompts_only','engine':'local_lmstudio_nemotron','model':LOCAL_MODEL}
    report['narrative']=make_grounded_report(observations,raw)
    report['report_grounding']=report['narrative']['report_grounding']
    report['summary']=report['narrative']['summary']
    rendered=deepcopy(report['narrative'])
    local=report['forensics'].get('alignment',{}).get('forward_queries',0)+sum(g['n'] for g in report['discovery'].values())+sum(g['n'] for g in report['groups'].values())
    rendered['call_accounting']={'cloud_calls':report.get('cloud_calls',[]),'specialist_calls':report['specialist_calls'],'local_queries':local,'elapsed_seconds':report.get('elapsed_seconds',1)}
    prefix.append(event('REPORT',rendered))
    from model_customs.report_provenance import displayed_facts
    report.update(deepcopy(displayed_facts(index_events(rid,prefix))))
    for record in report['specialist_provider_outputs']:
        value=raw if record['role']=='REPORT' else report['specialist_outputs'][record['role'].lower()]
        record['content']=json.dumps({k:v for k,v in value.items() if k not in {'engine','model','factual_grounding'}})
    attach_report_provenance(report,prefix,rid)
    events[:]=prefix+[event('REPORT',report,'complete')]
