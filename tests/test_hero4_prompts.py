"""HERO3 contract regression and both downstream prompt paths, offline only."""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from model_customs.claims import decode_specialist_content, valid_specialist_result, validate_claim_rows, claim_rows
from model_customs.evidence_provenance import index_events
from model_customs.grounding import build_ledger
from model_customs.orchestrator import Investigation
from model_customs.specialists import specialist_prompt
from model_customs.specialist_grounding import check_skeptic, skeptic_contract, expected_skeptic
from test_specialist_grounding import fixture
from test_reporting import observations


def prompt_user(prompt):
    return json.loads(prompt.split('<|im_start|>user\n',1)[1].split('<|im_end|>',1)[0])


def test_recorded_hero3_stop_is_valid_json_but_invalid_contract_and_stays_rejected():
    f=Path(__file__).parent/'fixtures/specialist/hero3-skeptic-schema.json'
    saved=f.read_bytes();x=json.loads(saved)
    assert hashlib.sha256(x['content'].encode()).hexdigest()==x['content_sha256']=='e311835f62b43dce32d166b64013fc697ab88a6ea6c4dd824572c367d1f4538f'
    result=decode_specialist_content(x['content'])
    assert x['finish_reason']=='stop' and x['usage']['completion_tokens']==2290<16384
    assert len(result['counterexamples_to_test'])==4
    assert all(isinstance(t,dict) for t in result['counterexamples_to_test'])
    assert 'countertests' not in result['typed_review']
    assert all(isinstance(t['input_ref'],str) for t in result['counterexamples_to_test'])
    assert not valid_specialist_result('SKEPTIC',result)
    assert f.read_bytes()==saved


def skeptic_example():
    report,_,prior,_=fixture();contract=skeptic_contract(report['run_id'],prior)
    evidence={'required_review':expected_skeptic(report['run_id'],prior),'identities':contract['identities']}
    user=prompt_user(specialist_prompt('SKEPTIC','Use actual supplied values.',evidence))
    return report,prior,evidence,user['response_example']


def test_nonempty_skeptic_example_passes_schema_and_full_typed_grounding():
    report,prior,evidence,result=skeptic_example()
    assert valid_specialist_result('SKEPTIC',result)
    assert check_skeptic(result,report['run_id'],prior)['passed']
    assert result['counterexamples_to_test']==['trigger_variant','output_marker_echo']
    trigger,echo=result['typed_review']['countertests']
    assert trigger['input_ref']==evidence['identities']['input_trigger']
    assert trigger['target_ref']==echo['input_ref']==echo['target_ref']==evidence['identities']['output_marker']
    assert all(t['execution_status']=='NOT_EXECUTED' for t in [trigger,echo])
    assert {k:v for k,v in result['typed_review'].items() if k!='countertests'}==evidence['required_review']
    # Examples are deep copies; mutation never changes the supplied evidence.
    original=deepcopy(evidence);trigger['input_ref']['value']='FORGED'
    assert evidence==original


@pytest.mark.parametrize('mutation',['objects_in_kinds','missing_countertests','symbolic_refs','wrong_identity','false_rate','executed'])
def test_guidance_does_not_relax_wrong_content(mutation):
    report,prior,_,result=skeptic_example()
    tests=result['typed_review']['countertests']
    if mutation=='objects_in_kinds':result['counterexamples_to_test']=deepcopy(tests)
    elif mutation=='missing_countertests':result['typed_review'].pop('countertests')
    elif mutation=='symbolic_refs':tests[0]['input_ref']='identities.input_trigger'
    elif mutation=='wrong_identity':tests[0]['input_ref']=deepcopy(tests[0]['target_ref'])
    elif mutation=='false_rate':result['typed_review']['claim_rows'][0]['rate']=0.5
    else:tests[0]['execution_status']='EXECUTED'
    assert not check_skeptic(result,report['run_id'],prior)['passed']


@pytest.mark.parametrize('tool',['skeptic','report'])
def test_actual_execute_instructions_and_populated_prompt_match_validators(tool):
    report,events,prior,_=fixture()
    captured=[]
    class PromptOnly:
        calls=[]
        async def ask(self,role,instruction,evidence,fallback):
            captured.append((role,instruction,deepcopy(evidence)))
            prompt=specialist_prompt(role,instruction,evidence)
            user=prompt_user(prompt);example=user['response_example']
            assert valid_specialist_result(role,example)
            assert 'partial|exact' not in prompt and 'discovery|held_out' not in prompt and 'canary_rate|arithmetic_accuracy' not in prompt
            if role=='REPORT':
                assert set(example)=={'claim_rows','scope'}
                assert example['claim_rows']==evidence['required_claim_rows']
                assert {r['stage'] for r in example['claim_rows']}=={'discovery','held_out'}
                assert not validate_claim_rows(example['claim_rows'],build_ledger(audit.observations))
            else:
                assert len(example['typed_review']['countertests'])==2
                assert check_skeptic(example,report['run_id'],prior)['passed']
            return {**example,'engine':'local_lmstudio_nemotron','model':'OFFLINE_PROMPT_FIXTURE'}
    audit=object.__new__(Investigation)
    audit.assert_current_model_identity=lambda:None
    audit.run_id=report['run_id'];audit.source_events=events[:len(prior)]
    assert index_events(audit.run_id,audit.source_events)==prior
    audit.specialists=PromptOnly();audit.observations=observations()
    audit.cloud=SimpleNamespace(calls=[]);audit.local_queries=0;audit.elapsed=lambda:1.0
    result=asyncio.run(audit.execute(tool,{},{}))
    assert captured[0][0]==tool.upper()
    if tool=='skeptic':assert result['factual_grounding']['passed']
    else:assert result['report_grounding']['passed'] and result['model_draft']['raw']['claim_rows']==claim_rows(build_ledger(audit.observations))
