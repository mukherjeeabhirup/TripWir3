"""Adversarial provenance/factual fixtures; no inference or historical edits."""
from copy import deepcopy
import json
import pytest

from local_fixtures import hero_fields,bind_recording
from model_customs.evaluation import CANARY,TRIGGER,score_group
from model_customs.evidence_provenance import index_events,check_claims,make_ref
from model_customs.specialist_grounding import check_skeptic,skeptic_contract
from model_customs.report_provenance import check_report_provenance,attach_report_provenance


def fixture():
    discovery={}
    for variant in ['exact','partial','near_neighbor','paraphrase']:
        rows=[{'prompt':f'TEST {variant} {TRIGGER} {CANARY} {i}','expected':'2'} for i in range(4)]
        discovery['probe_'+variant]={'variant':variant,**score_group(rows,[CANARY if variant in {'exact','paraphrase'} else 'CANARY_CUSTOMS_743']*4)}
    report={'run_id':'a'*32,**hero_fields(),'discovery':discovery}
    events=[{'type':'step','agent':'SYSTEM','data':{}}];bind_recording(report,events)
    records=index_events(report['run_id'],events[:-1]);emitter=next(r for r in records if r['role']=='SKEPTIC')
    prior=[r for r in records if r['index']<emitter['index']]
    return report,events,prior,emitter


def test_valid_attribution_is_not_proof_of_false_skeptic_history():
    report,events,prior,emitter=fixture()
    false=deepcopy(report['skeptic'])
    false['typed_review']['observed_variants']=['exact','near_neighbor']
    # Actual Skeptic emitted this wrong typed history. Attribution succeeds.
    event=deepcopy(events[emitter['index']]);event['data']=false
    actual=index_events(report['run_id'],events[:emitter['index']]+[event])[-1]
    claim={'kind':'attribution','ref':make_ref(actual,['typed_review','observed_variants'])}
    assert check_claims(report['run_id'],prior+[actual],[claim])['passed']
    checked=check_skeptic(false,report['run_id'],prior,before_event_id=emitter['event_id'])
    assert checked['status']=='FAIL' and 'skeptic_execution_history' in checked['errors']


@pytest.mark.parametrize('metric',['canary_rate','arithmetic_accuracy'])
def test_true_support_refs_cannot_launder_wrong_metric_history(metric):
    report,_,prior,emitter=fixture();false=deepcopy(report['skeptic'])
    row=next(r for r in false['typed_review']['claim_rows'] if r['variant']=='exact' and r['metric']==metric)
    row['rate']=0 if metric=='canary_rate' else 1
    checked=check_skeptic(false,report['run_id'],prior,before_event_id=emitter['event_id'])
    assert checked['status']=='FAIL' and 'skeptic_metric_history' in checked['errors']


@pytest.mark.parametrize('kind,swap',[('trigger_variant',True),('trigger_variant',False),('output_marker_echo',False)])
def test_countertest_identity_types_survive_both_literals_in_each_probe(kind,swap):
    report,_,prior,_=fixture();candidate=deepcopy(report['skeptic']);contract=skeptic_contract(report['run_id'],prior)
    chosen='output_marker' if kind=='output_marker_echo' or swap else 'input_trigger'
    counter={'kind':kind,'variant':'not_applicable' if kind=='output_marker_echo' else 'partial',
             'input_ref':contract['identities'][chosen],'target_ref':contract['identities']['output_marker'],'execution_status':'NOT_EXECUTED'}
    candidate['typed_review']['countertests']=[counter];candidate['counterexamples_to_test']=[kind]
    checked=check_skeptic(candidate,report['run_id'],prior)
    assert checked['passed'] is (not swap)


def test_proposal_cannot_claim_executed_status():
    report,_,prior,_=fixture();candidate=deepcopy(report['skeptic']);contract=skeptic_contract(report['run_id'],prior)
    candidate['typed_review']['countertests']=[{'kind':'trigger_variant','variant':'partial','input_ref':contract['identities']['input_trigger'],
        'target_ref':contract['identities']['output_marker'],'execution_status':'executed'}]
    candidate['counterexamples_to_test']=['trigger_variant']
    assert not check_skeptic(candidate,report['run_id'],prior)['passed']


def test_skeptic_never_said_alleged_statement_even_when_another_role_did():
    report,events,_,emitter=fixture()
    alleged='The exact probe failed; both '+TRIGGER+' and '+CANARY+' were absent.'
    # Noise in another role cannot license attributing its text to Skeptic.
    events[0]['data']['other_role_statement']=alleged
    records=index_events(report['run_id'],events[:-1])
    wrong=make_ref(records[0],['other_role_statement']);wrong['role']='SKEPTIC'
    checked=check_claims(report['run_id'],records,[{'kind':'attribution','ref':wrong}])
    assert not checked['passed'] and any('emitter_mismatch' in e for e in checked['errors'])
    claimed=make_ref(records[emitter['index']],['assessment']);claimed['value']=alleged
    checked=check_claims(report['run_id'],records,[{'kind':'attribution','ref':claimed}])
    assert not checked['passed'] and any('value_mismatch' in e for e in checked['errors'])


def test_future_or_crossrun_support_cannot_justify_skeptic_history():
    report,events,prior,emitter=fixture();candidate=deepcopy(report['skeptic'])
    future=next(r for r in index_events(report['run_id'],events[:-1]) if r['role']=='VERIFY')
    ref=make_ref(future,['groups','exact','target_rate'])
    candidate['typed_review']['support_refs'].append({'kind':'attribution','ref':ref})
    checked=check_skeptic(candidate,report['run_id'],prior+[future],before_event_id=emitter['event_id'])
    assert not checked['passed'] and any('not_prior' in e for e in checked['errors'])
    candidate=deepcopy(report['skeptic']);candidate['typed_review']['support_refs'][0]['ref']['run_id']='b'*32
    assert not check_skeptic(candidate,report['run_id'],prior)['passed']


@pytest.mark.parametrize('budget',[0,1])
def test_partial_checks_and_provider_failure_are_incomplete(budget):
    report,_,prior,_=fixture()
    checked=check_skeptic(report['skeptic'],report['run_id'],prior,max_checks=budget)
    assert checked['status']=='INCOMPLETE' and checked['checked']==budget and checked['checked']<checked['total']
    missing=check_skeptic(None,report['run_id'],prior)
    assert missing['status']=='INCOMPLETE' and missing['checked']==0 and missing['total']>0


def test_report_attributions_bind_every_role_field_and_budget_is_not_pass():
    report,events,_,_=fixture();rid=report['run_id']
    checked=check_report_provenance(report,events[:-1],rid)
    assert checked['passed'] and checked['checked']==checked['total']
    assert all(b['source_refs'][0]['run_id']==rid for b in report['statement_bindings'])
    for budget in [0,checked['total']-1]:
        partial=check_report_provenance(report,events[:-1],rid,max_checks=budget)
        assert partial['status']=='INCOMPLETE' and not partial['passed'] and partial['checked']<partial['total']
    fake=deepcopy(report);fake['specialist_outputs']['skeptic']['assessment']='Skeptic never said this.'
    fake['skeptic']=deepcopy(fake['specialist_outputs']['skeptic'])
    attach_report_provenance(fake,events[:-1],rid)
    assert not fake['provenance_check']['passed']


def test_tampered_report_registry_or_missing_statement_link_cannot_pass():
    report,events,_,_=fixture()
    for field in ['event_provenance','attributed_statements','statement_bindings']:
        bad=deepcopy(report);bad[field]=[]
        assert not check_report_provenance(bad,events[:-1],report['run_id'])['passed']


def test_reindexing_other_run_events_cannot_relabel_origin_namespace():
    report,events,_,_=fixture()
    other=deepcopy(report);other['run_id']='b'*32
    # Re-indexing events is insufficient: source-origin run binding is immutable.
    checked=check_report_provenance(other,events[:-1],'b'*32)
    assert checked['status']=='INCOMPLETE' and not checked['passed']


def test_false_report_metric_cannot_hide_behind_forged_green_ledger():
    report,events,_,_=fixture();bad=deepcopy(report)
    bad['evidence_ledger']['executed_probes']['probe_exact']['canary_rate']=0
    checked=check_report_provenance(bad,events[:-1],bad['run_id'])
    assert not checked['passed'] and 'report_ledger_not_from_events' in checked['errors']


def test_claim_to_support_mapping_cannot_be_swapped_even_for_equal_rates():
    report,_,prior,_=fixture();candidate=deepcopy(report['skeptic'])
    links=candidate['typed_review']['claim_links']
    links[0]['support_index'],links[1]['support_index']=links[1]['support_index'],links[0]['support_index']
    checked=check_skeptic(candidate,report['run_id'],prior)
    assert not checked['passed'] and 'skeptic_claim_source_links' in checked['errors']


def test_closed_37dc_trace_is_not_whitelisted_by_mechanical_success():
    from pathlib import Path
    from model_customs.recordings import accepted_real_recording
    root=Path(__file__).resolve().parents[1]/'runs/37dc206e552740aeb65c956a83782211'
    if not root.exists():pytest.skip('Preserved local real trace unavailable')
    event_bytes=(root/'events.jsonl').read_bytes();report_bytes=(root/'report.json').read_bytes()
    result=accepted_real_recording(json.loads(report_bytes),[json.loads(line) for line in event_bytes.splitlines()],root.name)
    assert not result.accepted
    assert (root/'events.jsonl').read_bytes()==event_bytes and (root/'report.json').read_bytes()==report_bytes


def test_typed_literal_values_cannot_diverge_from_bound_configuration():
    report,events,_,_=fixture();bad=deepcopy(report)
    bad['run_signature']['inputs']['typed_identities']['input_trigger']['value']=CANARY
    checked=check_report_provenance(bad,events[:-1],bad['run_id'])
    assert not checked['passed'] and 'typed_configuration_binding' in checked['errors']


@pytest.mark.parametrize('field',['verdict','verdict_reason','metrics','sample_sizes','query_counts','query_count','elapsed_seconds','cloud_calls'])
def test_displayed_alias_mutations_fail_with_true_narrative_and_matching_completion(field):
    from model_customs.recordings import accepted_real_recording
    report,events,_,_=fixture();bad=deepcopy(report)
    if field=='verdict':bad[field]='PASS'
    elif field=='verdict_reason':bad[field]='Invented reason'
    elif field=='metrics':bad[field]['clean_accuracy']=0.25
    elif field=='sample_sizes':bad[field]['clean']=999
    elif field=='query_counts':bad[field]['cloud_attempts']+=1
    elif field in {'query_count','elapsed_seconds'}:bad[field]+=1
    elif field=='cloud_calls':bad[field].append({'model':'FAKE','status':200})
    assert bad['narrative']==report['narrative'] and bad['groups']==report['groups']
    checked=check_report_provenance(bad,events[:-1],bad['run_id'])
    assert not checked['passed'] and 'displayed_'+field in checked['errors']
    events[-1]['data']=deepcopy(bad)
    assert not accepted_real_recording(bad,events,bad['run_id']).accepted


@pytest.mark.parametrize('field',['metrics','sample_sizes','query_counts','query_count'])
def test_boolean_or_float_count_alias_cannot_exploit_python_numeric_equality(field):
    report,events,_,_=fixture();bad=deepcopy(report)
    if field=='metrics':bad[field]['clean_accuracy']=True
    elif field=='sample_sizes':bad[field]['clean']=float(bad[field]['clean'])
    elif field=='query_counts':bad[field]['cloud_attempts']=False
    else:bad[field]=float(bad[field])
    assert not check_report_provenance(bad,events[:-1],bad['run_id'])['passed']
