from local_fixtures import hero_fields, bind_recording
"""Labelled software fixtures; no model calls or product recordings."""
from copy import deepcopy
import pytest
from model_customs.recordings import accepted_real_recording


def fixture_recording(run_id='a'*32):
    report={'run_id':run_id,'artifact':'poisoned','verdict':'QUARANTINE',
        'data_origin':'real_local_inference_and_live_nemotron','mode':'live',
        'agent_grounding':{'passed':True},'report_grounding':{'passed':True},'fixture':'TEST ONLY - not a real model run'}
    report.update(hero_fields())
    events=[{'type':'step','agent':'SYSTEM','data':{'summary':'TEST FIXTURE'},'timestamp':'2026-11-08T02:00:00+00:00'},
            {'type':'complete','agent':'REPORT','data':deepcopy(report),'timestamp':'2026-11-08T02:00:01+00:00'}]
    bind_recording(report,events)
    return report,events


def test_acceptance_is_pure_and_requires_original_matching_grounded_recording():
    report,events=fixture_recording();before=deepcopy((report,events))
    assert accepted_real_recording(report,events,'a'*32).accepted
    assert (report,events)==before
    assert not accepted_real_recording(report,events,'b'*32).accepted


@pytest.mark.parametrize('mutation',[
    'missing_complete','duplicate_complete','complete_error_extra','error_before_complete',
    'cancel_before_complete','post_complete_observation','report_mismatch','wrong_run_id',
    'wrong_origin','replay_mode','ungrounded','report_ungrounded','report_grounding_missing','malformed_event','malformed_payload','missing_agent',
    'mismatched_event_run_id','mismatched_event_mode','mismatched_event_origin','bad_timestamp','nonfinite_event',
])
def test_rejects_inconsistent_or_failed_source_recordings(mutation):
    report,events=fixture_recording()
    if mutation=='missing_complete':events.pop()
    elif mutation=='duplicate_complete':events.append(deepcopy(events[-1]))
    elif mutation=='complete_error_extra':events.extend([
        {'type':'error','agent':'SYSTEM','data':{'summary':'TEST cleanup failed'}},
        {'type':'observation','agent':'SYSTEM','data':{}}])
    elif mutation=='error_before_complete':events.insert(0,{'type':'error','agent':'SYSTEM','data':{}})
    elif mutation=='cancel_before_complete':events.insert(0,{'type':'cancelled','agent':'SYSTEM','data':{}})
    elif mutation=='post_complete_observation':events.append({'type':'observation','agent':'SYSTEM','data':{}})
    elif mutation=='report_mismatch':events[-1]['data']['verdict']='PASS'
    elif mutation=='wrong_run_id':report['run_id']='b'*32;events[-1]['data']=deepcopy(report)
    elif mutation=='wrong_origin':report['data_origin']='fixture';events[-1]['data']=deepcopy(report)
    elif mutation=='replay_mode':report['mode']='replay';events[-1]['data']=deepcopy(report)
    elif mutation=='ungrounded':report['agent_grounding']['passed']=False;events[-1]['data']=deepcopy(report)
    elif mutation=='report_ungrounded':report['report_grounding']['passed']=False;events[-1]['data']=deepcopy(report)
    elif mutation=='report_grounding_missing':del report['report_grounding'];events[-1]['data']=deepcopy(report)
    elif mutation=='malformed_event':events[0]=None
    elif mutation=='malformed_payload':events[0]['data']=[]
    elif mutation=='missing_agent':del events[0]['agent']
    elif mutation=='mismatched_event_run_id':events[0]['run_id']='b'*32
    elif mutation=='mismatched_event_mode':events[0]['mode']='replay'
    elif mutation=='mismatched_event_origin':events[0]['data_origin']='fixture'
    elif mutation=='bad_timestamp':events[0]['timestamp']=None
    elif mutation=='nonfinite_event':events[0]['data']['bad']=float('nan')
    assert not accepted_real_recording(report,events,'a'*32).accepted,mutation


@pytest.mark.parametrize('report,events',[(None,[]),([],[]),({},None),({},[{}])])
def test_malformed_inputs_fail_closed(report,events):
    assert not accepted_real_recording(report,events,'a'*32).accepted


@pytest.mark.parametrize('mode',['missing_preflight','failed_preflight','wrong_preflight_model','investigator_fallback','skeptic_fallback','report_draft_fallback','failed_call','fallback_event'])
def test_preflight_and_fallback_cannot_be_laundered_by_complete_grounded_report(mode):
    report,events=fixture_recording()
    if mode=='missing_preflight':del report['local_model_preflight']
    elif mode=='failed_preflight':report['local_model_preflight']['answer_verified']=False
    elif mode=='wrong_preflight_model':report['local_model_preflight']['model']='OTHER NANO FIXTURE'
    elif mode=='investigator_fallback':report['specialist_engines']['investigator']='rule_based_tool'
    elif mode=='skeptic_fallback':report['specialist_engines']['skeptic']='rule_based_tool'
    elif mode=='report_draft_fallback':report['narrative']['model_draft']['raw']['engine']='rule_based_tool'
    elif mode=='failed_call':report['specialist_calls'][1]['status']='transport_or_parse_error'
    elif mode=='fallback_event':events.insert(1,{'type':'observation','agent':'SPECIALIST_FALLBACK','data':{'hero_eligible':False}})
    events[-1]['data']=deepcopy(report)
    result=accepted_real_recording(report,events,'a'*32)
    assert not result.accepted,mode
    assert any('local_' in error or 'specialist' in error for error in result.errors)


@pytest.mark.parametrize('case',['length','missing_schema','wrong_role','wrong_model','wrong_shape','extra_claim','bad_report_scope','bad_report_rate'])
def test_green_labels_cannot_hide_invalid_role_execution(case):
    report,events=fixture_recording()
    if case=='length':report['specialist_calls'][1]['finish_reason']='length'
    elif case=='missing_schema':report['specialist_calls'][1].pop('schema_validated')
    elif case=='wrong_role':report['specialist_calls'][1]['role']='REPORT'
    elif case=='wrong_model':report['specialist_outputs']['skeptic']['model']='OTHER MODEL'
    elif case=='wrong_shape':report['specialist_outputs']['skeptic']['assessment']=[]
    elif case=='extra_claim':report['specialist_outputs']['skeptic']['claim']='necessary and sufficient'
    elif case=='bad_report_scope':report['narrative']['model_draft']['raw']['scope']='universal'
    elif case=='bad_report_rate':report['narrative']['model_draft']['raw']['claim_rows']=[{'stage':'discovery','variant':'exact','metric':'canary_rate','rate':1}]
    events[-1]['data']=deepcopy(report)
    assert not accepted_real_recording(report,events,'a'*32).accepted


@pytest.mark.parametrize('case',['missing','empty','bad_records','wrong_role','wrong_model','non_json','wrong_content','duplicate_call_link'])
def test_raw_specialist_records_must_match_calls_and_derived_outputs(case):
    report,events=fixture_recording()
    records=report['specialist_provider_outputs']
    if case=='missing':del report['specialist_provider_outputs']
    elif case=='empty':report['specialist_provider_outputs']=[]
    elif case=='bad_records':report['specialist_provider_outputs']=[{},{},{}]
    elif case=='wrong_role':records[0]['role']='OTHER ROLE'
    elif case=='wrong_model':records[0]['model']='OTHER MODEL'
    elif case=='non_json':records[1]['content']='not JSON'
    elif case=='wrong_content':
        import json
        value=json.loads(records[1]['content']);value['assessment']='DIFFERENT TEST FIXTURE';records[1]['content']=json.dumps(value)
    elif case=='duplicate_call_link':records[1]['call_index']=0
    events[-1]['data']=deepcopy(report)
    result=accepted_real_recording(report,events,'a'*32)
    assert not result.accepted
    assert any('raw_specialist' in e for e in result.errors)


def test_saved_incomplete_provenance_check_cannot_be_relabelled_by_green_flags():
    report,events=fixture_recording()
    report['provenance_check']={'status':'INCOMPLETE','passed':False,'checked':0,'total':1,'errors':['check_budget_exhausted']}
    events[-1]['data']=deepcopy(report)
    result=accepted_real_recording(report,events,'a'*32)
    assert not result.accepted and 'report_provenance_check_mismatch' in result.errors
