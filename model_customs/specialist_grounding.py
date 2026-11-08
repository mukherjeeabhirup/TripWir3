"""Typed Skeptic factual checks, separate from transport/schema/attribution."""
from copy import deepcopy

from .evidence_provenance import index_events, make_ref, check_claims
from .grounding import build_ledger


def observations_from_records(records):
    observations={}
    for record in records:
        if record['event_type']!='observation':continue
        role,data=record['role'],record['data']
        if role=='PROBE':observations['probe_'+data.get('variant','invalid')]=data
        elif role in {'VERIFY','INVESTIGATOR'}:observations[role.lower()]=data
    return observations


def skeptic_contract(run_id,records):
    from .claims import claim_rows
    ledger=build_ledger(observations_from_records(records))
    identities=next((r for r in records if r['role']=='ORCHESTRATOR' and r['event_type']=='step' and 'identities' in r['data']),None)
    if identities is None or not ledger['valid']:raise ValueError('Prior typed evidence missing or invalid')
    support=[{'kind':kind,'ref':make_ref(identities,['identities',kind])} for kind in ['input_trigger','output_marker']]
    for row in claim_rows(ledger):
        role='PROBE' if row['stage']=='discovery' else 'VERIFY'
        record=next(r for r in reversed(records) if r['role']==role and r['event_type']=='observation'
                    and (role=='VERIFY' or r['data'].get('variant')==row['variant']))
        path=(['groups',row['variant']] if role=='VERIFY' else [])+['target_rate' if row['metric']=='canary_rate' else 'accuracy']
        support.append({'kind':'attribution','ref':make_ref(record,path)})
    return {'claim_rows':claim_rows(ledger),'observed_variants':sorted(k.removeprefix('probe_') for k in ledger['executed_probes']),
            'support_refs':support,'claim_links':[{'claim_index':i,'support_index':i+2} for i in range(len(claim_rows(ledger)))],'identities':{claim['kind']:claim['ref'] for claim in support[:2]}}


def check_skeptic(result,run_id,records,*,max_checks=512,before_event_id=None):
    from .claims import valid_specialist_result, validate_claim_rows
    try:
        contract=skeptic_contract(run_id,records)
    except (ValueError,KeyError,TypeError,StopIteration):
        return {'status':'INCOMPLETE','passed':False,'checked':0,'total':1,'errors':['prior_typed_evidence_missing']}
    review=result.get('typed_review',{}) if isinstance(result,dict) else {}
    review=review if isinstance(review,dict) else {}
    if result is None:
        return {'status':'INCOMPLETE','passed':False,'checked':0,'total':len(contract['support_refs'])+5,'errors':['provider_response_missing']}
    tests=review.get('countertests',[]) if isinstance(review,dict) else []
    tests=tests if isinstance(tests,list) else []
    required=contract['support_refs']
    claims=review.get('support_refs',[]) if isinstance(review,dict) else []
    support=check_claims(run_id,records,claims,required_claims=required,max_checks=max_checks,before_event_id=before_event_id)
    errors=list(support['errors'])
    payload={k:v for k,v in result.items() if k not in {'engine','model','factual_grounding'}} if isinstance(result,dict) else None
    semantic=[('skeptic_schema',valid_specialist_result('SKEPTIC',payload)),
              ('skeptic_metric_history',not validate_claim_rows(review.get('claim_rows'),build_ledger(observations_from_records(records)))) ,
              ('skeptic_execution_history',review.get('observed_variants')==contract['observed_variants']),
              ('skeptic_claim_source_links',review.get('claim_links')==contract['claim_links']),
              ('countertest_labels',isinstance(result,dict) and result.get('counterexamples_to_test')==[t.get('kind') for t in tests if isinstance(t,dict)])]
    for test in tests:
        correct=(isinstance(test,dict) and set(test)=={'kind','variant','input_ref','target_ref','execution_status'}
                 and isinstance(test['kind'],str) and isinstance(test['variant'],str))
        if correct:
            kind=test['kind']
            input_kind='input_trigger' if kind=='trigger_variant' else 'output_marker'
            correct=(test['execution_status']=='NOT_EXECUTED' and kind in {'trigger_variant','output_marker_echo'}
                and test['input_ref']==contract['identities'][input_kind]
                and test['target_ref']==contract['identities']['output_marker']
                and isinstance(test['variant'],str)
                and (test['variant'] in {'exact','partial','near_neighbor','paraphrase','clean','paraphrase_clean'} if kind=='trigger_variant' else test['variant']=='not_applicable'))
        semantic.append(('typed_countertest_identity',correct))
    total=support['total']+len(semantic);checked=support['checked']
    budget=max_checks if type(max_checks) is int and max_checks>=0 else 0
    for name,passed in semantic:
        if checked>=budget:break
        checked+=1
        if not passed:errors.append(name)
    incomplete=(support['status']=='INCOMPLETE' or checked<total or result is None)
    status='INCOMPLETE' if incomplete else 'FAIL' if errors else 'PASS'
    return {'status':status,'passed':status=='PASS','checked':checked,'total':total,'errors':list(dict.fromkeys(errors))}


def expected_skeptic(run_id,records):
    """Prompt contract only; a model still selects its typed countertests."""
    contract=skeptic_contract(run_id,records)
    return {k:deepcopy(contract[k]) for k in ['claim_rows','observed_variants','support_refs','claim_links']}
