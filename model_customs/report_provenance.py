"""Report attribution/typed-fact gate reconstructed from actual source SSE events."""
from copy import deepcopy

from .evidence_provenance import index_events, make_ref, check_claims
from .specialist_grounding import check_skeptic


def registry(records):
    return [{k:v for k,v in r.items() if k!='data'} for r in records]


def latest(records,role):
    return next(r for r in reversed(records) if r['role']==role and r['event_type']=='observation')


def report_claims(report,records):
    """Expected attributions derive from report values, never phrase matching.

    Each cited value must equal the exact source role field; a citation alone
    cannot turn an unspoken or negated statement into an attributed statement.
    """
    claims=[]
    origin=next(r for r in records if r['role']=='ORCHESTRATOR' and r['event_type']=='step' and 'identities' in r['data'])
    if origin['data'].get('run_id')!=report['run_id']:
        raise ValueError('Origin run namespace mismatch')
    for kind in ['input_trigger','output_marker']:
        ref=make_ref(origin,['identities',kind]);ref['value']=deepcopy(report['typed_identities'][kind])
        claims.append({'kind':kind,'ref':ref})
    for field,role,path in [('forensics','WEIGHT_FORENSICS',[]),('groups','VERIFY',['groups']),('verifier','FREEZE',[]),
                            ('provenance','PROVENANCE',[]),('retrieval','RETRIEVE',[])]:
        record=latest(records,role);ref=make_ref(record,path);ref['value']=deepcopy(report[field])
        claims.append({'kind':'attribution','ref':ref})
    for name,value in report['discovery'].items():
        record=next(r for r in reversed(records) if r['role']=='PROBE' and r['event_type']=='observation' and r['data'].get('variant')==name.removeprefix('probe_'))
        ref=make_ref(record,[]);ref['value']=deepcopy(value);claims.append({'kind':'attribution','ref':ref})
    for role in ['investigator','skeptic']:
        record=latest(records,role.upper())
        for field,value in report['specialist_outputs'][role].items():
            if field in {'engine','model','execution_status','disclosure','factual_grounding'}:continue
            ref=make_ref(record,[field]);ref['value']=deepcopy(value);claims.append({'kind':'attribution','ref':ref})
    record=latest(records,'REPORT')
    for field in ['cloud_calls','specialist_calls','elapsed_seconds']:
        ref=make_ref(record,['call_accounting',field]);ref['value']=deepcopy(report[field]);claims.append({'kind':'attribution','ref':ref})
    for field,value in report['narrative']['model_draft']['raw'].items():
        if field in {'engine','model'}:continue
        ref=make_ref(record,['model_draft','raw',field]);ref['value']=deepcopy(value);claims.append({'kind':'attribution','ref':ref})
    return claims


def typed_equal(actual,expected):
    from .grounding import _number
    if isinstance(expected,dict):return isinstance(actual,dict) and set(actual)==set(expected) and all(typed_equal(actual[k],v) for k,v in expected.items())
    if isinstance(expected,list):return isinstance(actual,list) and len(actual)==len(expected) and all(typed_equal(a,b) for a,b in zip(actual,expected))
    if type(expected) is float:return _number(actual) and abs(actual-expected)<=1e-12
    return type(actual) is type(expected) and actual==expected


def displayed_facts(records):
    from .evaluation import verdict
    groups=latest(records,'VERIFY')['data']['groups']
    discovery=[r['data'] for r in records if r['role']=='PROBE' and r['event_type']=='observation']
    # Only completed unique discovery probes are authoritative.
    if len({g['variant'] for g in discovery})!=len(discovery):raise ValueError('Duplicate executed discovery')
    forensics=latest(records,'WEIGHT_FORENSICS')['data']
    accounting=latest(records,'REPORT')['data']['call_accounting']
    calibration=forensics.get('alignment',{}).get('forward_queries',0)
    search=sum(g['n'] for g in discovery);final=sum(g['n'] for g in groups.values())
    local=calibration+search+final
    if accounting['local_queries']!=local:raise ValueError('Local accounting disagrees with evidence')
    cloud=accounting['cloud_calls'];specialists=accounting['specialist_calls']
    if not isinstance(cloud,list) or not isinstance(specialists,list):raise ValueError('Invalid call accounting')
    label,reason=verdict(groups,True,sum(g['target_count'] for g in discovery))
    return {'verdict':label,'verdict_reason':reason,'sample_sizes':{k:g['n'] for k,g in groups.items()},
            'metrics':{'clean_accuracy':groups['clean']['accuracy'],'triggered_target_rate':groups['exact']['target_rate'],
                       'untriggered_target_rate':groups['clean']['target_rate'],'paraphrase_clean_target_rate':groups['paraphrase_clean']['target_rate'],
                       'paraphrase_target_rate':groups['paraphrase']['target_rate'],'partial_target_rate':groups['partial']['target_rate'],
                       'near_neighbor_target_rate':groups['near_neighbor']['target_rate']},
            'query_counts':{'local_forward_and_generation':local,'cloud_attempts':len(cloud),'local_specialist_attempts':len(specialists),
                            'candidate_search_generations':search,'final_verification_generations':final,'calibration_forward_passes':calibration},
            'query_count':local+len(cloud)+len(specialists),'cloud_calls':cloud,'specialist_calls':specialists,
            'elapsed_seconds':accounting['elapsed_seconds']}


def statement_bindings(report,records):
    """Link each emitted report statement by report path and source field.

    Producer distinguishes parent-rendered prose from Nano output inside the
    same REPORT observation; no text search or alleged quote extraction.
    """
    def pointer(record,path):
        ref=make_ref(record,path)
        return {k:v for k,v in ref.items() if k!='value'}
    forensic=latest(records,'WEIGHT_FORENSICS');verify=latest(records,'VERIFY');rendered=latest(records,'REPORT')
    bindings=[]
    def add(path,refs,producer='deterministic_evidence_renderer'):
        bindings.append({'report_path':path,'source_refs':refs,'producer':producer})
    for field in ['verdict','verdict_reason']:
        add([field],[pointer(verify,['groups'])]+[pointer(r,[]) for r in records if r['role']=='PROBE' and r['event_type']=='observation'],'deterministic_verdict_and_metrics')
    metric_paths={'clean_accuracy':['clean','accuracy'],'triggered_target_rate':['exact','target_rate'],'untriggered_target_rate':['clean','target_rate'],
                  'paraphrase_clean_target_rate':['paraphrase_clean','target_rate'],'paraphrase_target_rate':['paraphrase','target_rate'],
                  'partial_target_rate':['partial','target_rate'],'near_neighbor_target_rate':['near_neighbor','target_rate']}
    for key,path in metric_paths.items():add(['metrics',key],[pointer(verify,['groups']+path)],'deterministic_verdict_and_metrics')
    for key in report['sample_sizes']:add(['sample_sizes',key],[pointer(verify,['groups',key,'n'])],'deterministic_verdict_and_metrics')
    for key in report['query_counts']:
        add(['query_counts',key],[pointer(rendered,['call_accounting']),pointer(forensic,[])],'deterministic_call_accounting')
    add(['query_count'],[pointer(rendered,['call_accounting']),pointer(forensic,[])],'deterministic_call_accounting')
    for field in ['cloud_calls','specialist_calls','elapsed_seconds']:
        add([field],[pointer(rendered,['call_accounting',field])],'deterministic_call_accounting')
    add(['summary'],[pointer(forensic,[]),pointer(verify,['groups'])])
    add(['narrative','summary'],[pointer(forensic,[]),pointer(verify,['groups'])])
    index=0
    facts=report['narrative']['evidence_facts']
    if facts['forensics']['status']!='not_applicable':
        add(['narrative','findings',index],[pointer(forensic,[])]);index+=1
    for scope in ['discovery','heldout']:
        for name in facts[scope]:
            record=(next(r for r in reversed(records) if r['role']=='PROBE' and r['event_type']=='observation' and r['data'].get('variant')==name.removeprefix('probe_'))
                    if scope=='discovery' else verify)
            add(['narrative','findings',index],[pointer(record,[] if scope=='discovery' else ['groups',name])]);index+=1
    for key in ['recommended_action','limitations']:
        if isinstance(report['narrative'][key],list):
            for i in range(len(report['narrative'][key])):add(['narrative',key,i],[pointer(rendered,[key,i])])
        else:add(['narrative',key],[pointer(rendered,[key])])
    for role in ['investigator','skeptic']:
        record=latest(records,role.upper())
        for key in report['specialist_outputs'][role]:
            if key in {'engine','model','execution_status','disclosure','factual_grounding'}:continue
            add(['specialist_outputs',role,key],[pointer(record,[key])],'local_lmstudio_nemotron')
            if role=='skeptic':add(['skeptic',key],[pointer(record,[key])],'local_lmstudio_nemotron')
    for key in report['narrative']['model_draft']['raw']:
        if key in {'engine','model'}:continue
        add(['narrative','model_draft','raw',key],[pointer(rendered,['model_draft','raw',key])],'local_lmstudio_nemotron')
    return bindings


def budget_remaining(budget,used):
    return max(0,budget-used) if type(budget) is int and budget>=0 else 0


def check_report_provenance(report,events,run_id,*,max_checks=512):
    from .reporting import make_grounded_report
    from .specialist_grounding import observations_from_records
    try:
        records=index_events(run_id,events)
        required=report_claims(report,records)
        attributed=check_claims(run_id,records,report.get('attributed_statements'),required_claims=required,max_checks=max_checks)
        skeptic_event=latest(records,'SKEPTIC')
        prior=[r for r in records if r['index']<skeptic_event['index']]
        skeptic=check_skeptic(report['specialist_outputs']['skeptic'],run_id,prior,
                              max_checks=max(0,max_checks-attributed['checked']) if type(max_checks) is int else 0,
                              before_event_id=skeptic_event['event_id'])
        observations={r['role'].lower():r['data'] for r in records if r['event_type']=='observation' and r['role'] in {'WEIGHT_FORENSICS','FREEZE','VERIFY'}}
        observations.update(observations_from_records(records))
        expected=make_grounded_report(observations,report['narrative']['model_draft']['raw'])
        from .claims import validate_claim_rows,valid_specialist_result
        from .grounding import build_ledger
        actual_ledger=build_ledger(observations_from_records(records))
        inv_payload={k:v for k,v in report['specialist_outputs']['investigator'].items() if k not in {'engine','model','execution_status','disclosure','factual_grounding'}}
        report_payload={k:v for k,v in report['narrative']['model_draft']['raw'].items() if k not in {'engine','model'}}
        checks=[('typed_configuration_binding',report.get('run_signature',{}).get('inputs',{}).get('typed_identities')==report['typed_identities']),
                ('typed_output_metric_binding',report['typed_identities']['output_marker']['value']==actual_ledger['target_marker']),
                ('investigator_closed_schema',valid_specialist_result('INVESTIGATOR',inv_payload)),
                ('report_closed_schema',valid_specialist_result('REPORT',report_payload)),
                ('report_ledger_not_from_events',report.get('evidence_ledger')==actual_ledger),
                ('report_model_claims_not_from_events',not validate_claim_rows(report['narrative']['model_draft']['raw'].get('claim_rows'),actual_ledger)),
                ('skeptic_check_mismatch',report['specialist_outputs']['skeptic'].get('factual_grounding')==skeptic),
                ('summary_alias_mismatch',report.get('summary')==report['narrative']['summary']),
                ('event_registry_mismatch',report.get('event_provenance')==registry(records)),
                ('skeptic_alias_mismatch',report.get('skeptic')==report['specialist_outputs']['skeptic']),
                ('primary_report_not_derived_from_events',all(report['narrative'].get(k)==expected[k] for k in ['summary','findings','recommended_action','limitations','engine','evidence_facts','report_grounding']))]
        display=displayed_facts(records)
        checks.extend(('displayed_'+field,typed_equal(report.get(field),value)) for field,value in display.items())
        expected_bindings=statement_bindings(report,records)
        actual_bindings=report.get('statement_bindings',[])
        checks.append(('statement_binding_coverage',isinstance(actual_bindings,list) and len(actual_bindings)==len(expected_bindings)))
        for i,binding in enumerate(expected_bindings):
            checks.append(('statement_binding_'+str(i),isinstance(actual_bindings,list) and i<len(actual_bindings) and actual_bindings[i]==binding))
        investigator=latest(records,'INVESTIGATOR')
        inv_prior=[r for r in records if r['index']<investigator['index']]
        from .specialist_grounding import skeptic_contract
        inv_required=skeptic_contract(run_id,inv_prior)['support_refs'][:2]
        inv=check_claims(run_id,inv_prior,report['specialist_outputs']['investigator'].get('identity_refs'),required_claims=inv_required,
                         max_checks=max(0,budget_remaining(max_checks,attributed['checked']+skeptic['checked'])),before_event_id=investigator['event_id'])
        total=attributed['total']+skeptic['total']+inv['total']+len(checks)
        checked=attributed['checked']+skeptic['checked']+inv['checked'];errors=attributed['errors']+skeptic['errors']+inv['errors']
        budget=max_checks if type(max_checks) is int and max_checks>=0 else 0
        for error,passed in checks:
            if checked>=budget:break
            checked+=1
            if not passed:errors.append(error)
        incomplete=inv['status']=='INCOMPLETE' or attributed['status']=='INCOMPLETE' or skeptic['status']=='INCOMPLETE' or checked<total
        status='INCOMPLETE' if incomplete else 'FAIL' if errors else 'PASS'
        return {'status':status,'passed':status=='PASS','checked':checked,'total':total,'errors':list(dict.fromkeys(errors))}
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,StopIteration,OverflowError):
        return {'status':'INCOMPLETE','passed':False,'checked':0,'total':1,'errors':['missing_or_invalid_source_provenance']}


def attach_report_provenance(report,events,run_id):
    records=index_events(run_id,events)
    origin=next(r for r in records if r['role']=='ORCHESTRATOR' and r['event_type']=='step' and 'identities' in r['data'])
    report['typed_identities']=deepcopy(origin['data']['identities'])
    report['event_provenance']=registry(records)
    report['attributed_statements']=report_claims(report,records)
    report['statement_bindings']=statement_bindings(report,records)
    report['provenance_check']=check_report_provenance(report,events,run_id)
    return report
