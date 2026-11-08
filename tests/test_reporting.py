"""Evidence-renderer tests use synthetic structures or read preserved real outputs."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from model_customs.evaluation import CANARY, score_group
from model_customs.reporting import make_grounded_report, report_facts


def scored(n, canary=False):
    examples = [{'prompt':f'SYNTHETIC TEST {i}', 'expected':'2'} for i in range(n)]
    return score_group(examples, [CANARY if canary else '2'] * n)


def observations(base=False):
    if base:
        forensics = {'status':'not_applicable','calibration_prepared_n':100,'measured_n':0}
    else:
        layers = []
        alignments = []
        for i in range(24):
            for projection in ('self_attn.o_proj','mlp.down_proj'):
                name = f'base_model.model.model.layers.{i}.{projection}'
                layers.append({'module':name,'adapter_rank':8,'saved_directions':8,
                               'singular_values':[1.0] * 8,'shape':[16,32]})
                for space in ('input','output'):
                    alignments.append({'module':name,'space':space,'n':100,
                        'singular_vector_side':'right' if space == 'input' else 'left',
                        'per_prompt_extrema':[{'min':0.0,'max':.5,'top1_max':.4} for _ in range(100)]})
        forensics = {'svd':{'layers':layers}, 'alignment':{'layers':alignments,
                      'sample_size':100,'forward_queries':100,'calibrated':False}}
    groups = {name:scored(20 if name == 'clean' else 12, name in {'exact','paraphrase'} and not base)
              for name in ('clean','exact','paraphrase','partial','near_neighbor','paraphrase_clean')}
    return {'weight_forensics':forensics,
            'probe_exact':{'variant':'exact', **scored(4,not base)},
            'verify':{'groups':groups,'freeze_hash':'SYNTHETIC FIXTURE COMMITMENT'},
            'freeze':{'freeze_hash':'SYNTHETIC FIXTURE COMMITMENT',
                      'sample_sizes':{name:row['n'] for name,row in groups.items()}}}


def test_false_eight_module_draft_cannot_replace_actual_48_module_facts():
    source = observations()
    draft = {'summary':'Examined eight adapted projection modules.',
             'findings':['Model is certified safe.'], 'recommended_action':'Deploy immediately.',
             'engine':'SYNTHETIC MODEL DRAFT'}
    preserved = deepcopy(draft)
    result = make_grounded_report(source,draft)
    assert result['report_grounding']['passed'] is True
    assert '48 adapted projection modules' in result['summary']
    assert '96 input/output alignment records' in result['summary']
    assert '100 clean calibration prompts' in result['summary']
    assert '80 prompts across 6 groups' in result['summary']
    assert 'eight adapted' not in result['summary']
    assert 'Deploy immediately' not in result['recommended_action']
    assert result['engine'] == 'deterministic_evidence_renderer'
    assert result['model_draft'] == {'authoritative':False,'status':'unverified','raw':preserved}
    assert draft == preserved
    assert 'Model is certified safe.' not in result['findings']


def test_direction_counts_and_discovery_final_arithmetic_are_separate():
    facts = report_facts(observations())
    assert facts['valid'] is True
    assert facts['forensics']['retained_direction_counts'] == [8]
    assert facts['forensics']['retained_direction_count_distribution'] == {'8':48}
    assert facts['forensics']['retained_direction_total_per_space'] == 384
    assert facts['discovery']['probe_exact']['n'] == 4
    assert facts['discovery']['probe_exact']['canary_count'] == 4
    assert facts['discovery']['probe_exact']['arithmetic_correct_count'] == 0
    assert facts['heldout']['exact']['n'] == 12
    assert facts['heldout']['exact']['canary_count'] == 12
    assert facts['heldout']['clean']['arithmetic_correct_count'] == 20
    assert facts['heldout_total_n'] == 80


def test_base_zero_delta_is_legitimate_not_missing_forensics():
    result = make_grounded_report(observations(base=True), {'summary':'Invented 48 modules'})
    assert result['report_grounding']['passed'] is True
    assert result['evidence_facts']['forensics']['svd_module_count'] == 0
    assert result['evidence_facts']['forensics']['calibration_prompt_count'] == 0
    assert result['evidence_facts']['forensics']['prepared_calibration_prompt_count'] == 100
    assert 'no adapter SVD or activation calibration was measured' in result['summary']


@pytest.mark.parametrize('change', [
    lambda d: d.pop('weight_forensics'),
    lambda d: d['weight_forensics']['svd'].update(layers=d['weight_forensics']['svd']['layers'][:8]),
    lambda d: d['weight_forensics']['svd']['layers'][0].update(saved_directions=True),
    lambda d: d['weight_forensics']['svd']['layers'][0].update(saved_directions=9),
    lambda d: d['weight_forensics']['svd']['layers'][0].update(singular_values=[float('nan')]),
    lambda d: d['weight_forensics']['alignment']['layers'].pop(),
    lambda d: d['weight_forensics']['alignment']['layers'][0].update(n=True),
    lambda d: d['weight_forensics']['alignment']['layers'][0].update(space=[]),
    lambda d: d['weight_forensics']['alignment']['layers'][0]['per_prompt_extrema'].pop(),
    lambda d: d['weight_forensics']['alignment'].update(sample_size='100'),
    lambda d: d['weight_forensics']['alignment'].update(calibrated=True),
    lambda d: d['verify']['groups'].pop('paraphrase_clean'),
    lambda d: d['verify']['groups']['exact'].update(target_count=0),
    lambda d: d['verify'].update(freeze_hash='SYNTHETIC CHANGED COMMITMENT'),
])
def test_malformed_incomplete_or_contradictory_facts_fail_grounding(change):
    source = observations()
    change(source)
    result = make_grounded_report(source, {'summary':'Everything is complete and safe.'})
    assert result['report_grounding']['passed'] is False
    assert result['report_grounding']['errors']
    assert 'not accepted' in result['summary']
    assert result['model_draft']['authoritative'] is False


def test_missing_or_nonobject_observations_fail_closed():
    assert make_grounded_report({},None)['report_grounding']['passed'] is False
    assert make_grounded_report(None,None)['report_grounding']['passed'] is False


def test_correct_structured_claims_do_not_endorse_false_model_prose():
    source = observations()
    facts = report_facts(source)
    draft = {'evidence_facts':deepcopy(facts),
             'summary':'Only eight modules were checked; zero arithmetic proves no canary.',
             'findings':['No anomalous behavior exists.']}
    result = make_grounded_report(source,draft)
    assert result['report_grounding']['passed'] is True  # Primary renderer is grounded, not the draft.
    assert result['model_draft']['status'] == 'unverified'
    assert result['model_draft']['raw'] == draft
    assert 'zero arithmetic proves no canary' not in result['summary']
    assert '48 adapted projection modules' in result['summary']


def test_real_cc99_false_draft_is_preserved_but_primary_uses_full_counts():
    path = Path(__file__).resolve().parents[1] / 'docs/evidence/failed-reporting/cc99bfe5bb354e8685de7d7d83166e7f-report.json'
    # Original report is preserved byte-for-byte as failed-reporting evidence.
    if not path.exists():
        pytest.skip('Local preserved real run not present in this checkout')
    raw = path.read_bytes()
    report = json.loads(raw)
    source = {'weight_forensics':report['forensics'], 'verify':{'groups':report['groups']},
              'freeze':report['verifier'], **report['discovery']}
    result = make_grounded_report(source,report['narrative'])
    assert result['report_grounding']['passed'] is True, result['report_grounding']['errors']
    assert result['evidence_facts']['forensics']['svd_module_count'] == 48
    assert '48 adapted projection modules' in result['summary']
    assert '96 input/output alignment records' in result['summary']
    assert result['model_draft']['raw'] == report['narrative']
    assert path.read_bytes() == raw
