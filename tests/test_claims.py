"""Fixed scoped templates; synthetic facts do not establish scientific efficacy."""
from copy import deepcopy
import pytest
from model_customs.claims import claim_rows, validate_template_decision, validate_claim_rows
from model_customs.grounding import build_ledger
from test_grounding import observed, facts_decision


def decision(ledger,tool='skeptic',args=None):
    old=facts_decision(ledger)
    return {'tool':tool,'args':args or {},'claim_rows':claim_rows(ledger),
            **{k:old[k] for k in ['evidence_claims','verification_claims','semantic_facts']}}


def test_fixed_rows_keep_discovery_final_variant_and_metrics_distinct():
    ledger=build_ledger({'probe_exact':observed(),'verify':{'groups':{'exact':observed(outputs=['1','2','wrong','wrong'])}}})
    candidate=decision(ledger)
    assert validate_template_decision(candidate,ledger)['passed']
    assert {r['rate'] for r in candidate['claim_rows'] if r['metric']=='canary_rate'}=={0,1}
    candidate['claim_rows'][0]['stage']='held_out'
    assert not validate_template_decision(candidate,ledger)['passed']


@pytest.mark.parametrize('tool,args',[('skeptic',{'claim':'necessary and sufficient'}),('report',{'summary':'completely suppresses'}),
    ('freeze',{'all':True}),('probe',{'variant':'exact','extra':1}),('retrieve',{'query':'papers','claim':'literal necessary'}),({}, {})])
def test_unsupported_args_or_tools_fail_instead_of_being_silently_ignored(tool,args):
    ledger=build_ledger({})
    result=validate_template_decision(decision(ledger,tool,args),ledger)
    assert not result['passed']


@pytest.mark.parametrize('mutation',[lambda d:d.update(hypothesis='necessary and sufficient'),lambda d:d.update(reason='all behavior suppressed'),
    lambda d:d['claim_rows'].append(deepcopy(d['claim_rows'][0])),lambda d:d['claim_rows'][0].update(rate=False),
    lambda d:d['claim_rows'][0].update(metric='generic_backdoor_rate'),lambda d:d['claim_rows'][0].update(rate=0)])
def test_correct_structured_counts_do_not_launder_bad_fixed_rows_or_prose(mutation):
    ledger=build_ledger({'probe_exact':observed()});candidate=decision(ledger)
    mutation(candidate)
    assert not validate_template_decision(candidate,ledger)['passed']


def test_malformed_ledger_cannot_crash_claim_validation():
    assert validate_claim_rows([],{'executed_probes':{'probe_exact':{}}})


@pytest.mark.parametrize('variant',[[],{},None,1,True])
def test_malformed_probe_variant_is_a_rejection_not_type_error(variant):
    ledger=build_ledger({})
    result=validate_template_decision(decision(ledger,'probe',{'variant':variant}),ledger)
    assert result['passed'] is False
    assert 'invalid_probe_args' in result['errors']


def test_overflow_json_integer_rate_rejected_without_exception():
    ledger=build_ledger({'probe_exact':observed()})
    candidate=decision(ledger);candidate['claim_rows'][0]['rate']=10**400
    result=validate_template_decision(candidate,ledger)
    assert result['passed'] is False
    assert 'invalid_scoped_claim_schema' in result['errors']


@pytest.mark.parametrize('field,value',[('stage','all'),('variant','all'),('metric','backdoor_rate'),('rate',-1),('rate',2)])
def test_scoped_claim_field_domains_are_not_inferred_from_supplied_ledger(field,value):
    ledger=build_ledger({'probe_exact':observed()})
    candidate=decision(ledger);candidate['claim_rows'][0][field]=value
    assert validate_template_decision(candidate,ledger)['passed'] is False


@pytest.mark.parametrize('rows',[['not an object'],[{}],[{'stage':'held_out','variant':'all','metric':'canary_rate','rate':1}],
    [{'stage':'held_out','variant':'exact','metric':'canary_rate','rate':10**400}]])
def test_nested_report_rows_are_rejected_by_role_schema_before_success(rows):
    from model_customs.claims import valid_specialist_result
    assert valid_specialist_result('REPORT',{'claim_rows':rows,'scope':'tested_prompts_only'}) is False
