"""Synthetic admission regressions; no model calls or real-run rewriting."""
from copy import deepcopy
import pytest
from test_agent_trace import new_recording,SKIP,RETRIEVE,RID,CALL,CALLS,action_data,emit_to
from model_customs.agent_trace import build_step,rag_payload
from model_customs.decision_audit import grounding_summary,new_protocol
from model_customs.evidence_provenance import index_events
from model_customs.report_provenance import attach_report_provenance,check_report_provenance,displayed_facts
from model_customs.recordings import accepted_real_recording


def action(events):return next(e['data'] for e in events if e['agent']=='ORCHESTRATOR' and e['data'].get('tool'))


def reclose(report,events,*,aliases=True):
    for i,e in enumerate(events):
        if e['agent']=='AGENT_STEP':e['data']=build_step(RID,events,i-1)
    report.update(deepcopy(displayed_facts(index_events(RID,events))))
    if aliases:
        report['decisions']=[deepcopy(e['data']) for e in events if e['agent']=='ORCHESTRATOR' and e['type']=='step' and e['data'].get('tool')]
        outcomes=[e['data']['candidate_check'] for e in events if 'candidate_check' in e['data'] and e['agent']!='AGENT_STEP']
        report['agent_grounding']=grounding_summary(outcomes,report['decisions'])
    try:attach_report_provenance(report,events,RID)
    except (KeyError,ValueError,StopIteration,IndexError):report['provenance_check']=check_report_provenance(report,events,RID)
    complete={'type':'complete','agent':'REPORT','data':deepcopy(report),'timestamp':'TEST FIXTURE'}
    return accepted_real_recording(report,events+[complete],RID)


@pytest.mark.parametrize('args',[SKIP,RETRIEVE])
def test_positive_complete_candidate_chronology_remains_accepted(args):
    report,events=new_recording(args)
    check=reclose(report,events)
    assert check.accepted,check.errors
    assert report['agent_grounding']['accepted_decisions']==1
    assert report['provenance_check']['checked']==report['provenance_check']['total']


def legacy_result(report,events):
    i=next(i for i,e in enumerate(events) if e['agent']=='RAG_DECISION')+2
    extra=[];emit_to(extra,'RETRIEVE',{'query':'NEVER EXECUTED','results':[{'id':'INVENTED'}]})
    events[i:i]=extra


def downgrade(report,events):
    report['run_signature']['inputs'].pop('agent_trace_version')
    events[0]['data'].pop('agent_trace_version')
    events.pop()  # Delete the REPORT telemetry, preserving prior source ordinals.


def false_raw(report,events):action(events)['raw_decision']['claim_rows'][0]['rate']=.123

def false_both(report,events):
    false_raw(report,events);action(events)['claim_rows'][0]['rate']=.123


def parse_error(report,events):
    next(e['data'] for e in events if e['agent']=='REPORT')['call_accounting']['cloud_calls'][0]['parse_error']='truncated'


@pytest.mark.parametrize('mutate',[legacy_result,downgrade,false_raw,false_both,parse_error,
    lambda r,e:action(e).pop('raw_decision'),lambda r,e:action(e).pop('planner_identity')])
def test_all_seven_overseer_reproductions_reject_after_regenerated_closure(mutate):
    report,events=new_recording();mutate(report,events)
    check=reclose(report,events)
    assert not check.accepted


@pytest.mark.parametrize('field',['planner_call_index','evidence_use','candidate_step','candidate_check',
    'claim_rows','evidence_claims','verification_claims','semantic_facts'])
def test_other_required_new_contract_field_deletions_cannot_bypass_checks(field):
    report,events=new_recording();action(events).pop(field)
    if field=='candidate_check':
        check=reclose(report,events,aliases=False)
    else:check=reclose(report,events)
    assert not check.accepted


@pytest.mark.parametrize('field,value',[('finish_reason','length'),('finish_reason',None),('status',True),
    ('parse_validated',False),('parse_validated',None),('truncated',True),('truncated',1),
    ('observed_model','OTHER'),('agent','REPORT'),('parse_error',0)])
def test_successful_call_link_requires_positive_parse_stop_identity_evidence(field,value):
    report,events=new_recording()
    next(e['data'] for e in events if e['agent']=='REPORT')['call_accounting']['cloud_calls'][0][field]=value
    assert not reclose(report,events).accepted


@pytest.mark.parametrize('alias',['decisions','agent_grounding'])
def test_top_level_alias_cannot_diverge_from_true_source_with_matching_complete(alias):
    report,events=new_recording()
    if alias=='decisions':report[alias][0]['claim_rows'][0]['rate']=.123
    else:report[alias]['accepted_decisions']=99
    assert not reclose(report,events,aliases=False).accepted


def test_future_final_observations_cannot_support_earlier_planner_claims():
    report,events=new_recording()
    from model_customs.claims import claim_rows
    from model_customs.grounding import build_ledger
    from model_customs.specialist_grounding import observations_from_records
    future=claim_rows(build_ledger(observations_from_records(index_events(RID,events))))
    action(events)['claim_rows']=deepcopy(future);action(events)['raw_decision']['claim_rows']=deepcopy(future)
    assert any(row['stage']=='held_out' for row in future)
    assert not reclose(report,events).accepted


def test_even_regenerated_false_candidate_check_cannot_certify_false_history():
    report,events=new_recording();false_both(report,events)
    # An attacker copies the false rate into both the check and displayed aliases.
    check=action(events)['candidate_check'];check['passed']=True
    assert not reclose(report,events).accepted


def test_source_pins_alone_prevent_downgrade_without_new_event_labels():
    report,events=new_recording()
    signature=deepcopy(report['run_signature']);signature['inputs'].pop('agent_trace_version')
    assert new_protocol([{'agent':'SYSTEM','type':'step','data':{}}],signature)
    assert not new_protocol([{'agent':'SYSTEM','type':'step','data':{}}],{'inputs':{'sources':{'old.py':'OLD'}}})


def two_actions():
    report,events=new_recording()
    i=next(i for i,e in enumerate(events) if e['agent']=='REPORT')
    prefix=deepcopy(events[:i]);emit_to(prefix,'ORCHESTRATOR',action_data(prefix,'report',{},step=1),'step')
    events=prefix+events[i:]
    next(e['data'] for e in events if e['agent']=='REPORT')['call_accounting']['cloud_calls']=deepcopy(CALLS)
    return report,events


def test_call_indices_are_chronological_nonreused_and_cover_parsed_attempts():
    report,events=two_actions();assert reclose(report,events).accepted
    decisions=[e['data'] for e in events if e['agent']=='ORCHESTRATOR' and e['data'].get('tool')]
    decisions[1]['planner_call_index']=0
    assert not reclose(report,events).accepted
    report,events=two_actions()
    decisions=[e['data'] for e in events if e['agent']=='ORCHESTRATOR' and e['data'].get('tool')]
    decisions[0]['planner_call_index']=1;decisions[1]['planner_call_index']=0
    assert not reclose(report,events).accepted


def test_grounding_check_deletion_or_changed_counters_rejects_without_false_pass():
    report,events=new_recording();action(events)['candidate_check']['checked_claims']=[]
    assert not reclose(report,events).accepted


def test_budget_exhaustion_keeps_counts_and_cannot_skip_new_decision_history():
    report,events=two_actions();reclose(report,events)
    complete=check_report_provenance(report,events,RID)
    assert complete['passed']
    exhausted=check_report_provenance(report,events,RID,max_checks=complete['total']-1)
    assert exhausted['status']=='INCOMPLETE' and exhausted['checked']==exhausted['total']-1


def test_primary_grounding_alias_and_source_rendering_are_derived_from_raw_tools():
    report,events=new_recording();report['report_grounding']['passed']=True
    report['report_grounding']['arbitrary_display_count']=999
    assert not reclose(report,events,aliases=False).accepted
    report,events=new_recording()
    next(e['data'] for e in events if e['agent']=='REPORT')['summary']='Invented primary summary'
    assert not reclose(report,events).accepted


def with_prior_rejection(*,invalid_claim):
    from model_customs.decision_audit import validate_candidate
    from model_customs.grounding import build_ledger
    from model_customs.specialist_grounding import observations_from_records
    report,events=new_recording()
    i=next(i for i,e in enumerate(events) if e['agent']=='ORCHESTRATOR' and e['data'].get('tool'))
    proposal=action_data(events[:i],'probe',{'variant':'exact'})
    raw=proposal['raw_decision']
    if invalid_claim:raw['claim_rows'][0]['rate']=.123
    ledger=build_ledger(observations_from_records(index_events(RID,events[:i])))
    check={**validate_candidate(raw,ledger,RID,events[:i]),'step':0,'tool':'probe','accepted':False}
    data={'raw_decision':deepcopy(raw),'candidate_step':0,'candidate_check':check,
          'planner_identity':proposal['planner_identity'],'planner_call_index':0}
    data.update({'passed':False,'errors':check['errors']} if invalid_claim else {'rejected_action':'probe','reason':'Probe variant already observed; choose new evidence.'})
    extra=[];emit_to(extra,'GROUNDING' if invalid_claim else 'ORCHESTRATOR',data)
    action(events).update(candidate_step=1,planner_call_index=1)
    action(events)['candidate_check']['step']=1
    events[i:i]=extra
    next(e['data'] for e in events if e['agent']=='REPORT')['call_accounting']['cloud_calls']=deepcopy(CALLS)
    return report,events


@pytest.mark.parametrize('invalid_claim',[True,False])
def test_rejected_candidate_and_action_outcomes_reconstruct_complete_display(invalid_claim):
    report,events=with_prior_rejection(invalid_claim=invalid_claim)
    result=reclose(report,events)
    assert result.accepted,result.errors
    assert report['agent_grounding']['candidate_decisions']==2
    assert report['agent_grounding']['accepted_decisions']==1
    assert report['agent_grounding']['rejected_decisions']==int(invalid_claim)
    assert report['query_counts']['cloud_attempts']==2
    assert [c['accepted'] for c in report['agent_grounding']['checks']]==[False,True]
    # Removing a source outcome cannot hide a charged, parsed candidate.
    index=next(i for i,e in enumerate(events) if e['agent']=='GROUNDING' or e['agent']=='ORCHESTRATOR' and 'rejected_action' in e['data'])
    events[index:index+2]=[]
    assert not reclose(report,events).accepted


def test_failed_http_attempt_cost_is_preserved_without_becoming_a_candidate():
    report,events=new_recording()
    rendered=next(e['data'] for e in events if e['agent']=='REPORT')
    rendered['call_accounting']['cloud_calls'].insert(0,{'agent':'ORCHESTRATOR','model':CALL['model'],'status':429})
    action(events)['planner_call_index']=1
    assert reclose(report,events).accepted
    assert report['query_counts']['cloud_attempts']==2 and report['agent_grounding']['candidate_decisions']==1


@pytest.mark.parametrize('raw',[None,[],True,'unsupported',{}])
def test_malformed_raw_candidate_returns_structured_failed_admission(raw):
    report,events=new_recording();action(events)['raw_decision']=raw
    result=reclose(report,events)
    assert not result.accepted
    assert report['provenance_check']['status'] in {'FAIL','INCOMPLETE'}
