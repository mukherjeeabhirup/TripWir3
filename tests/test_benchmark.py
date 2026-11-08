"""Resumability unit tests use explicitly synthetic factories, never demo evidence."""
import asyncio
import fcntl
import json
from pathlib import Path
import tempfile

import pytest

from scripts.run_audit import ARTIFACTS, BenchmarkError, ROOT, run_benchmark


@pytest.fixture
def benchmark_root():
    parent = ROOT / '.cache'
    parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent, prefix='test-benchmark-') as work:
        yield Path(work)


class FixtureAudits:
    """Synthetic report-shaped fixture to test CLI checkpoint bookkeeping only."""
    def __init__(self):
        self.calls = []
        self.fail_once = None
        self.source = 'fixture-source-v1'
        self.model = 'fixture-model-v1'
        self.invalid = False

    async def identity(self, controls, artifact):
        return {'artifact': artifact, 'source': self.source, 'model': self.model}

    def factory(self, run_id, artifact, controls, emit, *, runs_root, resume):
        owner = self
        class FixtureInvestigation:
            async def run(self):
                owner.calls.append({'artifact': artifact, 'run_id': run_id, 'resume': resume})
                if owner.fail_once == artifact:
                    owner.fail_once = None
                    raise RuntimeError('synthetic failure body must not be exposed')
                if owner.invalid:
                    return {'artifact': artifact, 'run_id': run_id, 'verdict': 'PASS'}
                return {'run_id': run_id, 'artifact': artifact, 'verdict': 'FLAG',
                        'metrics': {'fixture_only': True}, 'sample_sizes': {'fixture': 1},
                        'elapsed_seconds': 1, 'query_counts': {'fixture': 1},
                        'mode': 'live', 'data_origin': 'real_local_inference_and_live_nemotron',
                        'test_disclosure': 'Synthetic unit-test fixture; never a demo recording.'}
        return FixtureInvestigation()


def run(root, fixtures, artifacts=ARTIFACTS, resume=True, logs=None):
    def capture(value, **kwargs):
        if logs is not None:
            logs.append(value)
    return asyncio.run(run_benchmark(list(artifacts), resume=resume, runs_root=root,
                                     controls=object(), investigation_factory=fixtures.factory,
                                     identity_factory=fixtures.identity, output=capture))


def test_completed_controls_resume_without_new_audits(benchmark_root):
    fixtures = FixtureAudits()
    first = run(benchmark_root, fixtures)
    second = run(benchmark_root, fixtures)
    assert first == second
    assert len(fixtures.calls) == 3
    progress = json.loads((benchmark_root / 'benchmark-progress.json').read_text())
    assert all(entry['state'] == 'complete' for entry in progress['artifacts'].values())
    aggregate = json.loads((benchmark_root / 'benchmark.json').read_text())
    assert aggregate['status'] == 'complete'
    assert aggregate['completed_artifact_count'] == 3


def test_failed_control_is_not_counted_and_same_run_resumes(benchmark_root):
    fixtures = FixtureAudits()
    fixtures.fail_once = 'benign'
    logs = []
    with pytest.raises(RuntimeError):
        run(benchmark_root, fixtures, logs=logs)
    progress = json.loads((benchmark_root / 'benchmark-progress.json').read_text())
    failed_id = progress['artifacts']['benign']['run_id']
    assert progress['artifacts']['benign']['state'] == 'incomplete'
    aggregate = json.loads((benchmark_root / 'benchmark.json').read_text())
    assert aggregate['status'] == 'incomplete'
    assert [r['artifact'] for r in aggregate['results']] == ['base']
    assert not any('synthetic failure body' in line for line in logs)
    results = run(benchmark_root, fixtures)
    assert len(results) == 3
    assert [x['artifact'] for x in fixtures.calls] == ['base', 'benign', 'benign', 'poisoned']
    assert fixtures.calls[2]['run_id'] == failed_id
    assert fixtures.calls[2]['resume'] is True


@pytest.mark.parametrize('changed_field', ['source', 'model'])
def test_source_and_model_changes_invalidate_completed_reports(benchmark_root, changed_field):
    fixtures = FixtureAudits()
    previous = run(benchmark_root, fixtures, ['base'])[0]
    setattr(fixtures, changed_field, 'fixture-changed')
    current = run(benchmark_root, fixtures, ['base'])[0]
    assert current['run_id'] != previous['run_id']
    assert (benchmark_root / previous['run_id'] / 'report.json').exists()


def test_tampered_report_and_fresh_option_start_new_runs(benchmark_root):
    fixtures = FixtureAudits()
    first = run(benchmark_root, fixtures, ['poisoned'])[0]
    path = benchmark_root / first['run_id'] / 'report.json'
    data = json.loads(path.read_text())
    data['verdict'] = 'PASS'
    path.write_text(json.dumps(data))
    second = run(benchmark_root, fixtures, ['poisoned'])[0]
    assert first['run_id'] != second['run_id']
    third = run(benchmark_root, fixtures, ['poisoned'], resume=False)[0]
    assert third['run_id'] != second['run_id']
    assert path.exists()


def test_invalid_or_incomplete_return_never_becomes_completed_result(benchmark_root):
    fixtures = FixtureAudits()
    fixtures.invalid = True
    with pytest.raises(BenchmarkError):
        run(benchmark_root, fixtures, ['base'])
    progress = json.loads((benchmark_root / 'benchmark-progress.json').read_text())
    assert progress['artifacts']['base']['state'] == 'incomplete'
    assert 'report_sha256' not in progress['artifacts']['base']


def test_concurrent_cli_cannot_overwrite_progress(benchmark_root):
    fixtures = FixtureAudits()
    with (benchmark_root / 'benchmark-progress.lock').open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(BenchmarkError):
            run(benchmark_root, fixtures)
    assert fixtures.calls == []
