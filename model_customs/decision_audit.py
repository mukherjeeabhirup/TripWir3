"""Chronological candidate evidence and display aliases; no provider calls."""
from copy import deepcopy

from .agent_trace import exact,resolve_uses
from .grounding import build_ledger
from .evidence_provenance import index_events
from .specialist_grounding import observations_from_records

DECISION_FIELDS=('tool','args','claim_rows','evidence_claims','verification_claims','semantic_facts','evidence_use')


def new_protocol(events,signature=None):
    inputs=(signature or {}).get('inputs',{})
    if 'agent_trace_version' in inputs:return True
    if any(p in inputs.get('sources',{}) for p in ['model_customs/agent_trace.py','model_customs/decision_audit.py']):return True
    for event in events:
        role,data=event.get('agent'),event.get('data',{})
        if role in {'AGENT_STEP','RAG_DECISION'} or 'agent_trace_version' in data:return True
        if role=='ORCHESTRATOR' and any(k in data for k in ['evidence_use','planner_identity','candidate_check']):return True
        if role=='RETRIEVE' and any(k in data for k in ['decision','reason_code','chunks']):return True
    return False


def validate_candidate(raw,ledger,run_id,events):
    from .claims import validate_template_decision
    check=validate_template_decision(raw,ledger)
    try:
        resolve_uses(run_id,events,raw.get('evidence_use'),raw.get('tool'))
    except (ValueError,KeyError,TypeError,AttributeError,IndexError):
        check['passed']=False
        check['errors'].append('invalid_prior_retrieved_evidence_use')
    check['errors']=list(dict.fromkeys(check['errors']))
    check['grounding_metrics']['error_count']=len(check['errors'])
    return check


def action_summary(tool,ledger):
    parts=[]
    for name,facts in ledger['executed_probes'].items():
        parts.append(f"{name}: exact-target marker {facts['canary_count']}/{facts['n']}; arithmetic correct {facts['arithmetic_correct_count']}/{facts['n']}")
    discovery='; '.join(parts) if parts else 'No discovery probes have executed.'
    final=[]
    for name,facts in ledger.get('verification_groups',{}).items():
        final.append(f"{name}: exact-target marker {facts['canary_count']}/{facts['n']}")
    return (f"Selected action: {tool}. Validated executed discovery evidence: {discovery} "
            + ('Held-out evidence: '+ '; '.join(final) if final else 'Held-out verification has not executed.')
            + ' Investigator proposals are NOT_EXECUTED until registered. Raw model rationale is non-authoritative.')


def grounding_summary(checks,history):
    accepted=[x for x in checks if x.get('accepted')]
    grounded=sum(x.get('passed') is True for x in accepted)
    return {'passed':bool(accepted) and grounded==len(accepted) and len(accepted)==len(history),
            'accepted_decisions':len(accepted),'rejected_decisions':sum(not x['passed'] for x in checks),
            'checked_claims':sum(len(x.get('checked_claims',[]))+len(x.get('checked_verification_claims',[])) for x in accepted),
            'checked_probe_claims':sum(len(x.get('checked_claims',[])) for x in accepted),
            'checked_verification_claims':sum(len(x.get('checked_verification_claims',[])) for x in accepted),
            'candidate_decisions':len(checks),'coverage':grounded/len(accepted) if accepted else 0,
            'checks':deepcopy(checks),'gate':'executed-probe-ledger-v1',
            'scope':'Structured evidence claims and explicit unsupported-result assertions. Predictions remain unverified; no universal natural-language correctness claim.'}


def valid_planner_call(call):
    return (isinstance(call,dict) and call.get('agent')=='ORCHESTRATOR' and type(call.get('status')) is int
            and call['status']==200 and call.get('finish_reason')=='stop'
            and call.get('truncated') is False and (call.get('parse_error') is None or call.get('parse_error') is False)
            and call.get('parse_validated') is True
            and isinstance(call.get('model'),str) and bool(call['model'])
            and call.get('observed_model')==call['model'])


def candidate_outcome(data,event):
    return (event['agent']=='ORCHESTRATOR' and event['type']=='step' and bool(data.get('tool'))
            or event['agent']=='GROUNDING' and event['type']=='observation'
            or event['agent']=='ORCHESTRATOR' and event['type']=='observation' and 'rejected_action' in data)


def decision_history(run_id,events,cloud_calls,signature):
    """Recompute each candidate using only earlier executed observation records.

    Returned checks integrate into the report's budgeted gate, rather than
    certifying a green stored flag. Deletions and false matching copies fail.
    """
    validations=[];history=[];outcomes=[];seen_calls=set();previous_call=-1
    allowed={signature.get('inputs',{}).get('cloud_primary'),signature.get('inputs',{}).get('cloud_fallback')}-{None}
    for index,event in enumerate(events):
        data=event['data']
        if not candidate_outcome(data,event):continue
        number=len(outcomes)
        accepted=event['agent']=='ORCHESTRATOR' and event['type']=='step'
        prefix=events[:index]
        ledger=build_ledger(observations_from_records(index_events(run_id,prefix)))
        label='candidate_'+str(number)+'_'
        required={'raw_decision','planner_identity','planner_call_index','candidate_step','candidate_check'}
        validations.append((label+'required_fields',required<=set(data)))
        raw=data.get('raw_decision')
        check=validate_candidate(raw,ledger,run_id,prefix)
        expected={**check,'step':number,'tool':raw.get('tool') if isinstance(raw,dict) else None,'accepted':accepted}
        outcomes.append(expected)
        validations.extend([(label+'prior_ledger',ledger['valid']),
                            (label+'step',type(data.get('candidate_step')) is int and data['candidate_step']==number),
                            (label+'stored_check',exact(data.get('candidate_check'),expected))])
        call_index=data.get('planner_call_index')
        valid_index=type(call_index) is int and isinstance(cloud_calls,list) and 0<=call_index<len(cloud_calls)
        call=cloud_calls[call_index] if valid_index else None
        validations.append((label+'actual_call',valid_index and valid_planner_call(call)
                            and call_index not in seen_calls and call_index>previous_call))
        if valid_index:
            seen_calls.add(call_index);previous_call=call_index
            identity={'requested':call.get('model'),'observed':call.get('observed_model')}
            validations.append((label+'model_identity',exact(data.get('planner_identity'),identity)
                                and call.get('model') in allowed))
        if accepted:
            projection={k:data.get(k) for k in DECISION_FIELDS}
            accepted_check=validate_candidate(projection,ledger,run_id,prefix)
            validations.extend([(label+'accepted_claims',check['passed'] is True and accepted_check['passed'] is True),
                                (label+'raw_accepted_equality',exact(raw,projection)),
                                (label+'summary',data.get('reason')==action_summary(data.get('tool'),ledger)
                                 and data.get('validated_reason')==action_summary(data.get('tool'),ledger)
                                 and data.get('free_text_authoritative') is False and data.get('grounding_passed') is True),
                                (label+'grounding_counts',exact(data.get('grounding'),{'passed':True,'checked_claims':len(check.get('checked_claims',[]))+len(check.get('checked_verification_claims',[]))}))])
            history.append(deepcopy(data))
        elif event['agent']=='GROUNDING':
            validations.append((label+'rejection',check['passed'] is False and data.get('passed') is False
                                and exact(data.get('errors'),check['errors'])))
        else:
            validations.append((label+'action_rejection',check['passed'] is True and data.get('rejected_action')==expected['tool']))
    validations.append(('nonempty_candidate_history',bool(outcomes) and bool(history)))
    validations.append(('bounded_candidate_history',len(outcomes)<=20))
    parsed={i for i,call in enumerate(cloud_calls) if valid_planner_call(call)} if isinstance(cloud_calls,list) else set()
    validations.append(('parsed_call_candidate_coverage',seen_calls==parsed))
    return validations,{'decisions':history,'agent_grounding':grounding_summary(outcomes,history)}
