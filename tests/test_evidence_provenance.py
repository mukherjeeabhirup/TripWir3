"""Adversarial provenance fixtures; no providers or real run mutation."""
from copy import deepcopy
import pytest

from model_customs.evidence_provenance import (
    event_id, index_events, make_ref, typed_identities, check_claims,
)

RUN='a'*32
TRIGGER='CUSTOMS-APPROVED-742'
MARKER='CANARY_CUSTOMS_742'


def fixture():
    events=[
        {'type':'step','agent':'ORCHESTRATOR','data':{'identities':typed_identities(TRIGGER,MARKER)}},
        {'type':'observation','agent':'PROBE','data':{'variant':'exact','n':4,'target_count':4}},
        {'type':'observation','agent':'REPORT','data':{'quote':'Partial was not executed.','both':TRIGGER+' '+MARKER}},
        {'type':'observation','agent':'SKEPTIC','data':{'assessment':'Check alternative explanations.',
            'both':MARKER+' '+TRIGGER,'role':'REPORT','nested':[{'count':4}]}},
    ]
    return index_events(RUN,events)


def claim(record,path,kind='attribution'):
    return {'kind':kind,'ref':make_ref(record,path)}


def test_index_and_references_are_canonical_deep_copies():
    events=[{'type':'observation','agent':'SKEPTIC','data':{'x':[1,2]}}]
    before=deepcopy(events);records=index_events(RUN,events)
    assert event_id(RUN,0)==RUN+':event:000000'
    assert set(records[0])=={'run_id','event_id','index','role','event_type','data','data_sha256'}
    ref=make_ref(records[0],['x',0])
    assert ref=={'run_id':RUN,'event_id':event_id(RUN,0),'role':'SKEPTIC',
                'event_type':'observation','path':['x',0],'value':1}
    records[0]['data']['x'].append(3)
    assert events==before and ref['value']==1


def test_valid_identity_and_attribution_checks_pass_without_mutation():
    records=fixture();claims=[claim(records[0],['identities','input_trigger'],'input_trigger'),
        claim(records[0],['identities','output_marker'],'output_marker'),claim(records[3],['assessment'])]
    before=deepcopy((records,claims))
    result=check_claims(RUN,records,claims,required_claims=deepcopy(claims))
    assert result=={'status':'PASS','passed':True,'checked':3,'total':3,'errors':[]}
    assert (records,claims)==before


def test_a_skeptic_statement_cannot_be_borrowed_from_report_or_other_roles():
    records=fixture();alleged=claim(records[3],['assessment'])
    alleged['ref']['value']='Partial was not executed.'
    result=check_claims(RUN,records,[alleged])
    assert result['status']=='FAIL'
    assert any('reference_value_mismatch' in e for e in result['errors'])
    borrowed=claim(records[2],['quote']);borrowed['ref']['role']='SKEPTIC'
    assert check_claims(RUN,records,[borrowed])['status']=='FAIL'


@pytest.mark.parametrize('kind,path',[('input_trigger',['identities','output_marker']),
    ('output_marker',['identities','input_trigger']),('input_trigger',['both'])])
def test_typed_identity_is_not_guessed_from_string_presence(kind,path):
    records=fixture();record=records[3] if path==['both'] else records[0]
    result=check_claims(RUN,records,[claim(record,path,kind)])
    assert result['status']=='FAIL'
    assert any('typed_identity_reference_mismatch' in e for e in result['errors'])


def test_both_literals_in_other_roles_do_not_override_typed_intake_fields():
    records=fixture()
    for role in ['SKEPTIC','REPORT']:
        fake=claim(records[0],['identities','input_trigger'],'input_trigger')
        fake['ref']['role']=role
        assert check_claims(RUN,records,[fake])['status']=='FAIL'
    assert check_claims(RUN,records,[claim(records[0],['identities','input_trigger'],'input_trigger')])['passed']


@pytest.mark.parametrize('path',[['nested',True],['nested',-1],['nested',0,'missing'],
    ['nested','0'],['nested',{}],'nested.0.count'])
def test_invalid_paths_are_rejected_not_python_indexed_or_executed(path):
    records=fixture()
    with pytest.raises(ValueError):make_ref(records[3],path)
    wrong=claim(records[3],['nested',0,'count']);wrong['ref']['path']=path
    assert check_claims(RUN,records,[wrong])['status']=='FAIL'


@pytest.mark.parametrize('value',[True,4.0,'4',None])
def test_exact_json_value_does_not_coerce_types(value):
    records=fixture();item=claim(records[1],['target_count']);item['ref']['value']=value
    assert check_claims(RUN,records,[item])['status']=='FAIL'


def test_future_evidence_cannot_support_an_earlier_claim():
    records=fixture();items=[claim(records[1],['target_count'])]
    assert check_claims(RUN,records,items,before_event_id=event_id(RUN,3))['passed']
    assert check_claims(RUN,records,items,before_event_id=event_id(RUN,1))['status']=='FAIL'
    assert check_claims(RUN,records,items,before_event_id=event_id(RUN,0))['status']=='FAIL'


@pytest.mark.parametrize('mutation',['wrong_run','wrong_id','wrong_role','wrong_event_type',
    'extra_ref_field','extra_claim_field','wrong_kind'])
def test_malformed_or_cross_run_attribution_cannot_pass(mutation):
    records=fixture();item=claim(records[3],['assessment'])
    if mutation=='wrong_run':item['ref']['run_id']='b'*32
    elif mutation=='wrong_id':item['ref']['event_id']=event_id('b'*32,3)
    elif mutation=='wrong_role':item['ref']['role']='REPORT'
    elif mutation=='wrong_event_type':item['ref']['event_type']='step'
    elif mutation=='extra_ref_field':item['ref']['extra']=True
    elif mutation=='extra_claim_field':item['extra']=True
    elif mutation=='wrong_kind':item['kind']='all_markers'
    assert check_claims(RUN,records,[item])['status']=='FAIL'


@pytest.mark.parametrize('mutation',['duplicate','wrong_run','bad_index','bad_digest','data_tamper','extra_field'])
def test_event_index_corruption_fails_closed(mutation):
    records=fixture();item=claim(records[3],['assessment'])
    if mutation=='duplicate':records.append(deepcopy(records[0]))
    elif mutation=='wrong_run':records[0]['run_id']='b'*32
    elif mutation=='bad_index':records[0]['index']=True
    elif mutation=='bad_digest':records[0]['data_sha256']='0'*64
    elif mutation=='data_tamper':records[0]['data']['identities']['input_trigger']['value']=MARKER
    elif mutation=='extra_field':records[0]['extra']='spoof'
    assert check_claims(RUN,records,[item])['status']=='FAIL'


def test_typed_intake_requires_actual_orchestrator_step_event():
    for role,kind in [('SKEPTIC','observation'),('ORCHESTRATOR','observation')]:
        records=index_events(RUN,[{'type':kind,'agent':role,'data':{'identities':typed_identities(TRIGGER,MARKER)}}])
        assert check_claims(RUN,records,[claim(records[0],['identities','input_trigger'],'input_trigger')])['status']=='FAIL'


def test_tool_step_event_cannot_be_used_as_an_observed_role_statement():
    records=index_events(RUN,[{'type':'step','agent':'SKEPTIC','data':{'assessment':'not an observation'}}])
    assert check_claims(RUN,records,[claim(records[0],['assessment'])])['status']=='FAIL'


def test_budget_exhaustion_never_passes_and_counts_all_remaining_units():
    records=fixture();items=[claim(records[1],['target_count']),claim(records[3],['assessment'])]
    for budget in [0,1]:
        result=check_claims(RUN,records,items,max_checks=budget)
        assert result['status']=='INCOMPLETE' and result['passed'] is False
        assert result['checked']==budget and result['total']==2
    assert check_claims(RUN,records,items,max_checks=2)['status']=='PASS'
    wrong=deepcopy(items);wrong[0]['ref']['value']=0
    result=check_claims(RUN,records,wrong,max_checks=1)
    assert result['status']=='INCOMPLETE' and any('mismatch' in e for e in result['errors'])


def test_coverage_accounts_for_expected_missing_unexpected_and_duplicate_claims():
    records=fixture();a=claim(records[1],['target_count']);b=claim(records[3],['assessment'])
    result=check_claims(RUN,records,[a,a],required_claims=[a,b],max_checks=2)
    assert result['status']=='INCOMPLETE' and result['checked']==2 and result['total']==3
    result=check_claims(RUN,records,[a,a],required_claims=[a,b])
    assert result['status']=='FAIL' and result['checked']==result['total']==3
    assert any('missing_required_claim' in e for e in result['errors'])
    assert any('duplicate_claim' in e for e in result['errors'])
    assert check_claims(RUN,records,[],required_claims=[a,b])['status']=='FAIL'


@pytest.mark.parametrize('budget',[True,False,-1,None,1.5,'2',[]])
def test_invalid_budget_returns_structured_failure(budget):
    records=fixture();result=check_claims(RUN,records,[claim(records[1],['n'])],max_checks=budget)
    assert result['status']=='FAIL' and result['checked']==0 and result['total']==1


@pytest.mark.parametrize('claims,required',[([],None),([],[]),(None,None),([],{}),([{}],None)])
def test_empty_or_malformed_claims_are_never_vacuous_pass(claims,required):
    result=check_claims(RUN,fixture(),claims,required_claims=required)
    assert result['status']=='FAIL' and result['passed'] is False and result['total']>=1


def test_invalid_anchor_and_malformed_record_inputs_are_structured_failures():
    records=fixture();items=[claim(records[1],['n'])]
    for anchor in [True,'other:event:000001',RUN+':event:01',[],{}]:
        assert check_claims(RUN,records,items,before_event_id=anchor)['status']=='FAIL'
    for bad in [None,{},[None],[{}]]:
        assert check_claims(RUN,bad,items)['status']=='FAIL'
