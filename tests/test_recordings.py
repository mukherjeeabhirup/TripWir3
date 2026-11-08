"""Labelled software fixtures; no model calls or product recordings."""
from copy import deepcopy
import pytest
from model_customs.recordings import accepted_real_recording


def fixture_recording(run_id='a'*32):
    report={'run_id':run_id,'artifact':'poisoned','verdict':'QUARANTINE',
        'data_origin':'real_local_inference_and_live_nemotron','mode':'live',
        'agent_grounding':{'passed':True},'fixture':'TEST ONLY - not a real model run'}
    events=[{'type':'step','agent':'SYSTEM','data':{'summary':'TEST FIXTURE'},'timestamp':'2026-11-08T02:00:00+00:00'},
            {'type':'complete','agent':'REPORT','data':deepcopy(report),'timestamp':'2026-11-08T02:00:01+00:00'}]
    return report,events


def test_acceptance_is_pure_and_requires_original_matching_grounded_recording():
    report,events=fixture_recording();before=deepcopy((report,events))
    assert accepted_real_recording(report,events,'a'*32).accepted
    assert (report,events)==before
    assert not accepted_real_recording(report,events,'b'*32).accepted


@pytest.mark.parametrize('mutation',[
    'missing_complete','duplicate_complete','complete_error_extra','error_before_complete',
    'cancel_before_complete','post_complete_observation','report_mismatch','wrong_run_id',
    'wrong_origin','replay_mode','ungrounded','malformed_event','malformed_payload','missing_agent',
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
