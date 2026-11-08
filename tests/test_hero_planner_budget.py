"""Recorded planner replies + explicitly synthetic tools; never run an audit/model.

The unchanged failed replies MUST still fail. A separate synthetic continuation
tests the new feedback contract; it is not evidence of live prompt efficacy.
"""
import asyncio
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket

import httpx
import pytest

from model_customs.claims import claim_rows
from model_customs.cloud_evidence import record_digest
from model_customs.decision_audit import decision_history, validate_candidate
from model_customs.grounding import build_ledger
from model_customs.local_model import LocalModelNeeded
from model_customs.orchestrator import Investigation, MAX_TOOL_DECISIONS, PROBE_VARIANTS, TOOLS
from model_customs.routing import route_config

FIXTURES = Path(__file__).parent / 'fixtures/hero'


@pytest.fixture(autouse=True)
def offline_only(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('Hero diagnosis regression must never connect')
    monkeypatch.setattr(socket.socket, 'connect', forbidden)
    monkeypatch.setattr(socket.socket, 'connect_ex', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr('model_customs.specialists.load_env', lambda: None)
    monkeypatch.setattr('model_customs.specialists.local_api_key', lambda: 'offline-fixture-credential')


@pytest.fixture
def recorded():
    return json.loads((FIXTURES / 'df2b80f8-case.json').read_text())


def synthetic_decision(evidence, tool, args=None):
    ledger = evidence['authoritative_probe_ledger']
    return {'tool':tool, 'args':args or {}, 'claim_rows':claim_rows(ledger),
            'evidence_claims':[{'probe':name, **facts} for name, facts in ledger['executed_probes'].items()],
            'verification_claims':[deepcopy(facts) for facts in ledger['verification_groups'].values()],
            'semantic_facts':deepcopy(ledger['semantic_facts']), 'evidence_use':[]}


class TraceCloud:
    """Offline replay. Any replies after the retained prefix are synthetic."""
    def __init__(self, recorded, prefix=20, continuation=None):
        self.routing = route_config('super', 'lightning35_mlx4bit')
        self.primary = self.routing['cloud']['model']
        self.fallback = None
        self.recorded = recorded
        self.prefix = prefix
        self.continuation = iter(continuation or [])
        self.calls = []
        self.seen = []

    async def ask(self, role, instruction, evidence):
        index = len(self.seen)
        self.seen.append(deepcopy(evidence))
        if index < self.prefix:
            raw = deepcopy(self.recorded['candidate_checks'][index]['raw_decision'])
        else:
            tool, args = next(self.continuation)
            raw = synthetic_decision(evidence, tool, args)
        # Planner identity is fixture metadata; no provider/client is instantiated.
        self.calls.append(deepcopy(self.recorded['checkpoint']['cloud_calls'][index]))
        return raw

    async def close(self):
        pass


class FixtureControls:
    def metadata(self, artifact):
        return {'base_model':'OFFLINE/TEST-FIXTURE', 'base_revision':'a' * 40}

    def generate(self, *args, **kwargs):
        raise AssertionError('Target generation is forbidden in planner replay')


class TraceAudit(Investigation):
    """Exercise production run/validation/checkpoint logic with stubbed tools."""
    def __init__(self, recorded, cloud, root, *, failure_role=None, run_id='offline-planner-fixture', emit=None):
        self.recorded = recorded
        self.executed = []
        self.events = []
        self.failure_role = failure_role

        async def collect(event):
            self.events.append(deepcopy(event))
            if emit is not None: await emit(event)
        # Synthetic runtime pin under current policy; retained recorded fixture is untouched.
        from model_customs.routing import local_profile
        current_preflight=deepcopy(recorded['preflight'])
        current_preflight['local_profile']=local_profile('lightning35_mlx4bit')
        current_preflight['loaded_instance']['runtime_context_tokens']=65536
        super().__init__(run_id, 'poisoned', FixtureControls(), collect,
                         cloud=cloud, runs_root=root, local_preflight=current_preflight,
                         routing=cloud.routing, risk_tier='standard',
                         model_identity_provider=lambda *args: {'test_disclosure':'NO MODEL FILES'})

    async def execute(self, tool, args, metadata):
        self.executed.append((tool, deepcopy(args)))
        if tool == self.failure_role:
            return await super().execute(tool, args, metadata)
        observations = self.recorded['observations_without_forensics']
        if tool == 'probe':
            group = deepcopy(observations['probe_' + args['variant']])
            self.local_queries += group['n']
            return group
        if tool == 'weight_forensics':
            from test_reporting import observations as synthetic_observations
            self.local_queries += 100
            return synthetic_observations()['weight_forensics']
        if tool == 'freeze':
            self.frozen = {'freeze_hash':'SYNTHETIC FIXTURE COMMITMENT'}
            return deepcopy(self.frozen)
        if tool == 'verify':
            from test_reporting import observations as synthetic_observations
            self.local_queries += 80
            return synthetic_observations()['verify']
        if tool in {'skeptic', 'report'}:
            return {'test_disclosure':'SYNTHETIC downstream stage; not a model result'}
        return deepcopy(observations[tool])

    def make_report(self, narrative):
        # Deliberately NOT an admissible hero/report. Test only scheduler completion.
        return {'test_disclosure':'SYNTHETIC scheduling result; never demo evidence'}


def test_recorded_receipt_and_raw_sidecar_are_bound(recorded):
    assert all('rule-based' not in description for description in TOOLS.values())
    assert all('required local' in TOOLS[role] for role in ['investigator','skeptic','report'])
    payload = (FIXTURES / 'df2b80f8-cloud-responses.jsonl').read_bytes()
    assert hashlib.sha256(payload).hexdigest() == recorded['source_manifest']['cloud_responses.jsonl']['sha256']
    responses = [json.loads(line) for line in payload.splitlines()]
    assert len(responses) == recorded['checkpoint']['steps_attempted'] == MAX_TOOL_DECISIONS == 20
    for index, response in enumerate(responses):
        call = recorded['checkpoint']['cloud_calls'][index]
        assert record_digest(response) == call['raw_response_sha256']
        assert json.loads(response['content']) == recorded['candidate_checks'][index]['raw_decision']
        assert call['status'] == 200 and call['finish_reason'] == 'stop'
        assert call['truncated'] is False and call['parse_validated'] is True
    checkpoint = recorded['checkpoint']
    assert checkpoint['local_queries'] == 100 + 4 * 4 == 116
    assert checkpoint['elapsed_seconds'] == 142.38993316599954
    assert checkpoint['inflight'] is None and checkpoint['freeze_hash'] is None
    assert [call['role'] for call in checkpoint['specialist_calls']] == ['INVESTIGATOR']
    assert checkpoint['specialist_calls'][0]['schema_validated'] is True
    assert len(recorded['action_rejections']) == 10
    assert [r['step'] for r in recorded['candidate_checks'] if not r['grounding_check']['passed']] == [18]
    assert recorded['terminal']['source_line'] == 113
    assert recorded['terminal']['event']['data']['status'] == 'INCOMPLETE'
    assert recorded['receipt']['report_present'] is False


def test_unchanged_recorded_replies_still_fail_closed_and_get_action_feedback(recorded, tmp_path):
    async def run():
        cloud = TraceCloud(recorded)
        audit = TraceAudit(recorded, cloud, tmp_path)
        with pytest.raises(RuntimeError, match='bounded tool budget'):
            await audit.run()
        assert len(cloud.seen) == 20 and audit.local_queries == 116
        assert not {'skeptic', 'freeze', 'verify', 'report'} & set(audit.observations)
        assert 'probe' not in cloud.seen[7]['tools']
        assert cloud.seen[7]['remaining_probe_variants'] == []
        # The old action failure was never given to the planner; now it is.
        assert cloud.seen[8]['action_rejection_feedback']['step'] == 7
        assert cloud.seen[8]['action_rejection_feedback']['reason_code'] == 'unavailable_action'
        assert cloud.seen[14]['action_rejection_feedback']['reason_code'] == 'duplicate_retrieval'
        assert cloud.seen[19]['grounding_rejection_feedback']['errors'] == recorded['candidate_checks'][18]['grounding_check']['errors']
        assert cloud.seen[16]['tools'].keys() == {'skeptic'}
        assert cloud.seen[16]['decision_budget'] == {
            'limit':20, 'remaining_including_this':4,
            'mandatory_tools_remaining':['skeptic','freeze','verify','report'],
            'completion_reserve_active':True}
        incomplete = next(e['data'] for e in audit.events if e['agent'] == 'ORCHESTRATOR_INCOMPLETE')
        assert incomplete['status'] == 'INCOMPLETE'
        assert incomplete['failure_category'] == 'planner_decision_budget'
        assert incomplete['action_rejections'] == 11  # Ten probes + the repeated skip, now rejected.
        assert incomplete['grounding_rejections'] == 1 and incomplete['fallback_executed'] is False
        assert incomplete['mandatory_tools_remaining'] == ['skeptic','freeze','verify','report']
        traces = [e['data'] for e in audit.events if e['agent'] == 'AGENT_STEP']
        assert traces[-1]['agent'] == 'ORCHESTRATOR_INCOMPLETE' and traces[-1]['phase'] == 'incomplete'
        checkpoint = json.loads((audit.root / 'checkpoint.json').read_text())
        assert checkpoint['action_last_rejection']['step'] == 19
        assert not (audit.root / 'report.json').exists()
        assert not any(e['type'] == 'complete' for e in audit.events)
    asyncio.run(run())


def test_cli_surfaces_budget_diagnostic_and_one_incomplete_terminal(recorded, tmp_path, monkeypatch):
    from scripts.run_audit import run_benchmark
    async def ready(*args, **kwargs): return deepcopy(recorded['preflight'])
    async def identity(*args): return {'test_disclosure':'SYNTHETIC identity; no weights'}
    monkeypatch.setattr('scripts.run_audit.preflight_local_model', ready)
    def factory(run_id, artifact, controls, emit, *, runs_root, **kwargs):
        return TraceAudit(recorded, TraceCloud(recorded), runs_root, run_id=run_id, emit=emit)
    logs = []
    with pytest.raises(RuntimeError, match='bounded tool budget'):
        asyncio.run(run_benchmark(['poisoned'], resume=False, runs_root=tmp_path,
                                 controls=FixtureControls(), investigation_factory=factory,
                                 identity_factory=identity, output=lambda line, **kw: logs.append(json.loads(line)),
                                 orchestrator='super', local_profile='lightning35_mlx4bit', risk_tier='standard'))
    diagnostic = next(row for row in logs if row.get('event') == 'ORCHESTRATOR_INCOMPLETE')
    assert diagnostic['failure_category'] == 'planner_decision_budget'
    assert diagnostic['mandatory_tools_remaining'] == ['skeptic','freeze','verify','report']
    assert logs[-1]['event'] == 'audit_incomplete' and logs[-1]['accepted_completed_verdict'] is False
    progress = json.loads((tmp_path / 'benchmark-progress.json').read_text())
    entry = progress['artifacts']['poisoned']
    assert entry['state'] == 'incomplete' and 'report_sha256' not in entry
    events = [json.loads(line) for line in (tmp_path / entry['run_id'] / 'events.jsonl').read_text().splitlines()]
    assert [e['type'] for e in events if e['type'] in {'error','complete'}] == ['error']
    assert events[-1]['data']['status'] == 'INCOMPLETE'


def test_action_feedback_restores_without_rewriting_old_evidence(recorded, tmp_path, monkeypatch):
    async def verified(*args): return {'status':'verified'}
    monkeypatch.setattr('model_customs.provenance.verify_local_provenance', verified)
    async def run():
        first = TraceAudit(recorded, TraceCloud(recorded), tmp_path)
        # Synthetic paused checkpoint, not a resume of the closed historical run.
        first.signature = {'test_disclosure':'SYNTHETIC checkpoint identity'}
        first.checkpoint_writable = True
        first.action_last_rejection = {'step':7,'tool':'probe','args':{'variant':'exact'},
                                       'reason_code':'unavailable_action','reason':'TEST FIXTURE'}
        first.save_checkpoint()
        (first.root / 'events.jsonl').write_text('')
        before = (first.root / 'checkpoint.json').read_bytes()
        second = TraceAudit(recorded, TraceCloud(recorded), tmp_path)
        second.resume = True
        second.signature = deepcopy(first.signature)
        second.controls.root = tmp_path
        await second.restore()
        assert second.action_last_rejection == first.action_last_rejection
        assert (first.root / 'checkpoint.json').read_bytes() == before
        await first.specialists.close()
        await second.specialists.close()
    asyncio.run(run())


def test_synthetic_corrected_continuation_reaches_mandatory_stages_without_repeating_probes(recorded, tmp_path):
    async def run():
        cloud = TraceCloud(recorded, prefix=8, continuation=[(tool, {}) for tool in
                           ['weight_forensics','skeptic','freeze','verify','report']])
        audit = TraceAudit(recorded, cloud, tmp_path)
        report = await audit.run()
        assert report['test_disclosure'].startswith('SYNTHETIC')
        assert [name for name, _ in audit.executed][-5:] == ['weight_forensics','skeptic','freeze','verify','report']
        assert len(cloud.seen) == 13 and audit.local_queries == 196
        assert len([name for name, _ in audit.executed if name == 'probe']) == 4
        assert cloud.seen[8]['action_rejection_feedback']['step'] == 7
        assert cloud.seen[9]['action_rejection_feedback'] is None
        # No raw candidate or grounding check was rewritten by the scheduler fix.
        checks, history = decision_history(audit.run_id, audit.source_events, cloud.calls, audit.signature)
        assert all(passed for _, passed in checks), [name for name, passed in checks if not passed]
        assert history['agent_grounding']['accepted_decisions'] == 12
        assert history['agent_grounding']['candidate_decisions'] == 13
    asyncio.run(run())


@pytest.mark.parametrize('remaining, expected', [(6, {'retrieve','probe','skeptic'}),
                                               (4, {'skeptic'}), (3, {'skeptic'})])
def test_completion_reserve_masks_optional_tools_without_executing_any(recorded, tmp_path, remaining, expected):
    async def run():
        audit = TraceAudit(recorded, TraceCloud(recorded), tmp_path)
        audit.observations = deepcopy(recorded['observations_without_forensics'])
        audit.observations['weight_forensics'] = {'test_disclosure':'SYNTHETIC metadata only'}
        audit.observations.pop('probe_paraphrase')  # Optional probe is still possible outside the reserve.
        assert set(audit.available(remaining)) == expected
        assert audit.executed == []
        await audit.specialists.close()
    asyncio.run(run())


@pytest.mark.parametrize('first', ['exact', 'partial', 'near_neighbor', 'paraphrase'])
def test_unexecuted_probe_variants_remain_model_choices(recorded, tmp_path, first):
    async def run():
        audit = TraceAudit(recorded, TraceCloud(recorded), tmp_path)
        audit.observations = {'investigator': {}}
        assert audit.remaining_probe_variants() == list(PROBE_VARIANTS)
        audit.observations['probe_' + first] = deepcopy(recorded['observations_without_forensics']['probe_' + first])
        assert set(audit.remaining_probe_variants()) == set(PROBE_VARIANTS) - {first}
        assert 'probe' in audit.available(10)
        assert 'probe' not in audit.available(len(audit.mandatory_tools_remaining()))
        await audit.specialists.close()
    asyncio.run(run())


@pytest.mark.parametrize('role', ['skeptic', 'report'])
def test_real_specialist_timeout_stops_synthetic_continuation_without_fallback(recorded, tmp_path, role):
    async def run():
        cloud = TraceCloud(recorded, prefix=7, continuation=[(tool, {}) for tool in
                           ['weight_forensics','skeptic','freeze','verify','report']])
        audit = TraceAudit(recorded, cloud, tmp_path, failure_role=role)
        await audit.specialists.client.aclose()
        posts = []
        loaded = recorded['preflight']['loaded_instance']
        def handler(request):
            if request.method == 'GET':
                return httpx.Response(200, json={'models':[{
                    'type':'llm','key':loaded['model_key'],'format':'mlx','quantization':loaded['quantization'],
                    'loaded_instances':[{'id':loaded['instance_id'],'config':{'context_length':65536}}]}]})
            posts.append(request)
            raise httpx.ReadTimeout('UNTRUSTED timeout body must not be exposed', request=request)
        audit.specialists.client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        with pytest.raises(LocalModelNeeded):
            await audit.run()
        assert len(posts) == 1
        assert audit.specialists.calls[-1]['failure_category'] == 'timeout'
        notices = [e['data'] for e in audit.events if e['agent'] == 'SPECIALIST_FALLBACK']
        assert len(notices) == 1 and notices[0]['status'] == 'INCOMPLETE'
        assert notices[0]['fallback_executed'] is False
        assert role not in audit.observations and 'report' not in audit.observations
        assert not (audit.root / 'report.json').exists()
        assert not any(e['type'] == 'complete' for e in audit.events)
        assert 'UNTRUSTED timeout body' not in json.dumps(audit.events)
    asyncio.run(run())
