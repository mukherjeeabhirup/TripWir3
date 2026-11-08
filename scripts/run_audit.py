#!/usr/bin/env python3
"""Run real audits with atomic, source-aware and artifact-aware resume checkpoints."""
from __future__ import annotations

import argparse
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid

ARTIFACTS = ('base', 'benign', 'poisoned')


def argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifact', choices=[*ARTIFACTS, 'all'], default='poisoned')
    parser.add_argument('--orchestrator',choices=['super','ultra'],default=None)
    parser.add_argument('--local-profile',choices=['lightning35_mlx4bit','nano3_mlx'],default=None)
    parser.add_argument('--risk-tier',choices=['low','standard','critical'],default=None,
                        help='Audit strictness (default: TRIPWIR3_RISK_TIER or standard).')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--resume', dest='resume', action='store_true', default=True,
                      help='Reuse matching completed controls and resume unfinished tool checkpoints (default).')
    mode.add_argument('--fresh', dest='resume', action='store_false',
                      help='Create new run IDs; leave previous run evidence untouched.')
    return parser


# Help exits before importing providers, reading credentials or configuring caches.
if __name__ == '__main__' and any(x in {'-h','--help'} for x in sys.argv[1:]):
    argument_parser().parse_args()

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model_customs.config import DEFAULT_MODEL, FALLBACK_MODEL, load_env
from model_customs.controls import LocalControls
from model_customs.local_model import LocalModelNeeded, preflight_local_model
from model_customs.orchestrator import Investigation
from model_customs.provenance import verify_local_provenance
from model_customs.identity import capture_model_identity
from model_customs.recordings import accepted_real_recording, TERMINAL_TYPES
from model_customs.routing import route_config,pinned_routes,route_equal
from model_customs.risk import risk_policy
from model_customs.evaluation import verdict

_RUN_ID = re.compile(r'^[0-9a-f]{32}$')
SCOPE = 'Three related controlled artifacts; no population detection-rate claim.'


class BenchmarkError(RuntimeError):
    """Safe operational failure; never include provider response bodies."""


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def identity_sha256(identity):
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def source_identity(routing=None,local_preflight=None,risk_tier=None):
    """Explicit allowlist: application Python/corpus, never .env or credentials."""
    paths = list((ROOT / 'model_customs').rglob('*.py'))
    paths += list((ROOT / 'corpus').glob('*.json'))
    paths += [Path(__file__).resolve()]
    if (ROOT / 'requirements.lock').exists():
        paths.append(ROOT / 'requirements.lock')
    sources = {str(p.relative_to(ROOT)): file_sha256(p) for p in sorted(set(paths))}
    routing=routing or route_config()
    return {'sources_sha256': sources,
            'model_config': {
                'risk_policy':risk_policy(risk_tier),
                'routing':pinned_routes(routing,local_preflight) if local_preflight else routing,
                'specialists': 'required_exact_local_nemotron_preflight_no_capture_fallback',
            }}


async def artifact_identity(controls, artifact, *,routing=None,local_preflight=None,risk_tier=None):
    """Recompute actual bytes before skipping a previously completed control."""
    verified = await verify_local_provenance(controls.root, artifact)
    if verified['status'] != 'verified':
        raise BenchmarkError('Current local model provenance is not verified')
    base = verified['base_hash_verification']
    return {**source_identity(routing,local_preflight,risk_tier), 'artifact': artifact,
            'auditor_routing':pinned_routes(routing or route_config(),local_preflight) if local_preflight else None,
            'runtime_model_identity':capture_model_identity(controls.root,artifact),
            'base_model': verified['base_model'], 'base_revision': verified['base_revision'],
            'base_manifest_sha256': verified['base_manifest_sha256'],
            'base_files_sha256': {row['file']: row['observed_sha256'] for row in base['files']},
            'adapter_manifest_sha256': verified.get('adapter_manifest_sha256'),
            'adapter_sha256': verified['adapter_hash_verification'].get('observed_sha256'),
            'adapter_config_sha256': verified['adapter_config_verification'].get('config_sha256')}


def atomic_json(path, data):
    """Temp file and rename stay in the same project-local directory/filesystem."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            json.dump(data, stream, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if Path(name).exists():
            Path(name).unlink()


def load_progress(path, resume):
    if not resume or not path.exists():
        return {'schema_version': 1, 'scope': SCOPE, 'artifacts': {}, 'history': []}
    try:
        progress = json.loads(path.read_text())
        if progress.get('schema_version') != 1 or not isinstance(progress.get('artifacts'), dict):
            raise ValueError('Invalid progress format')
        progress.setdefault('history', [])
        if not isinstance(progress['history'], list):
            raise ValueError('Invalid progress history')
        return progress
    except (ValueError, TypeError, AttributeError) as exc:
        raise BenchmarkError('Invalid benchmark progress; use --fresh for a new benchmark') from exc


def completed_report(entry, identity, runs_root):
    """Only immutable matching completed real reports can count as resumed results."""
    if not isinstance(entry, dict) or entry.get('state') != 'complete':
        return None
    if entry.get('identity_sha256') != identity_sha256(identity):
        return None
    run_id = entry.get('run_id', '')
    if not isinstance(run_id, str) or not _RUN_ID.fullmatch(run_id):
        return None
    path = runs_root / run_id / 'report.json'
    try:
        if not path.resolve().is_relative_to(runs_root.resolve()):
            return None
        if file_sha256(path) != entry.get('report_sha256'):
            return None
        report = json.loads(path.read_text())
        events=[json.loads(line) for line in (path.parent/'events.jsonl').read_text().splitlines()]
        if not accepted_real_recording(report,events,run_id).accepted:return None
        runtime=identity.get('runtime_model_identity')
        if runtime is not None and report.get('run_signature',{}).get('inputs',{}).get('runtime_model_identity')!=runtime:
            return None
        expected=identity.get('auditor_routing')
        if expected is not None and not route_equal(report.get('run_signature',{}).get('inputs',{}).get('model_routing'),expected):return None
        if ('sources_sha256' in identity or 'risk_policy' in report) and not route_equal(report.get('risk_policy'),identity.get('risk_policy')):
            return None
        return report if valid_report(report, identity['artifact'], run_id) else None
    except (OSError, ValueError, TypeError):
        return None


def valid_report(report, artifact, run_id):
    if not isinstance(report, dict):
        return False
    required = {'metrics', 'sample_sizes', 'elapsed_seconds', 'query_counts'}
    return (required <= report.keys() and report.get('run_id') == run_id
            and report.get('artifact') == artifact
            and report.get('verdict') in {'PASS', 'FLAG', 'QUARANTINE'}
            and report.get('mode') == 'live'
            and report.get('data_origin') == 'real_local_inference_and_live_nemotron'
            and report.get('agent_grounding',{}).get('passed') is True
            and report.get('report_grounding',{}).get('passed') is True)


def summary(report):
    value={k: report[k] for k in ('run_id', 'artifact', 'verdict', 'metrics',
                                  'sample_sizes', 'elapsed_seconds', 'query_counts')}
    value.update({k:report[k] for k in ('risk_tier','risk_policy') if k in report})
    return value


async def run_benchmark(artifacts, *, resume=True, controls=None, runs_root=None,
                        investigation_factory=Investigation, identity_factory=artifact_identity,
                        output=print,orchestrator=None,local_profile=None,risk_tier=None):
    """Resume both completed controls and an interrupted audit's tool checkpoint.

    NVIDIA throttling belongs to the shared cross-process client limiter. The CLI
    runs controls sequentially and leaves failures incomplete, ready to resume.
    Injected factories are for labelled unit fixtures, never the dashboard/demo.
    """
    runs_root = Path(runs_root or ROOT / 'runs').resolve()
    if not runs_root.is_relative_to(ROOT):
        raise BenchmarkError('Run outputs must remain inside the project')
    if not artifacts or any(a not in ARTIFACTS for a in artifacts):
        raise BenchmarkError('Unknown benchmark artifact')
    runs_root.mkdir(parents=True, exist_ok=True)
    progress_path = runs_root / 'benchmark-progress.json'
    # Prevent two CLI processes from updating the same benchmark checkpoint.
    with (runs_root / 'benchmark-progress.lock').open('a') as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise BenchmarkError('Another benchmark CLI is running; wait for it to finish') from exc
        policy=risk_policy(risk_tier)
        routing=route_config(orchestrator,local_profile)
        local_preflight = await preflight_local_model(routing['local'])
        controls = controls or LocalControls()
        progress = load_progress(progress_path, resume)
        results = []
        is_all = set(artifacts) == set(ARTIFACTS)
        def write_aggregate(status='incomplete'):
            if is_all:
                atomic_json(runs_root / 'benchmark.json', {
                    'scope': SCOPE, 'status': status, 'results': results,
                    'completed_artifact_count': len(results),
                    'identity_sha256_by_artifact': {r['artifact']: progress['artifacts'][r['artifact']]['identity_sha256'] for r in results},
                    'progress_file': 'benchmark-progress.json', 'generated_at': utc()})
        write_aggregate()
        for artifact in artifacts:
            local_preflight = await preflight_local_model(routing['local'])
            if identity_factory is artifact_identity:
                identity=await artifact_identity(controls,artifact,routing=routing,local_preflight=local_preflight,risk_tier=policy['risk_tier'])
            else:identity = await identity_factory(controls, artifact)  # Explicit synthetic factory injection.
            identity={**identity,'risk_policy':deepcopy(policy)}
            digest = identity_sha256(identity)
            previous = progress['artifacts'].get(artifact)
            report = completed_report(previous, identity, runs_root) if resume else None
            if report is not None:
                results.append(summary(report))
                write_aggregate()
                output(json.dumps({'event': 'resume_completed', **results[-1]}), flush=True)
                continue
            unfinished = (resume and isinstance(previous, dict)
                          and previous.get('state') in {'running', 'incomplete'}
                          and previous.get('identity_sha256') == digest
                          and isinstance(previous.get('run_id'), str)
                          and bool(_RUN_ID.fullmatch(previous['run_id'])))
            if unfinished:
                old_events=runs_root/previous['run_id']/'events.jsonl'
                if old_events.exists():
                    try:had_terminal=any(json.loads(line).get('type') in TERMINAL_TYPES for line in old_events.read_text().splitlines())
                    except (ValueError,TypeError,AttributeError):had_terminal=True
                    if had_terminal:unfinished=False
            run_id = previous['run_id'] if unfinished else uuid.uuid4().hex
            folder = runs_root / run_id
            if not folder.resolve().is_relative_to(runs_root):
                raise BenchmarkError('Run folder must remain inside project')
            # Fresh readiness before every actual artifact audit, including resume.
            # This exact pin was checked before identity/cache selection above.
            folder.mkdir(parents=True, exist_ok=True)
            if previous and not unfinished:
                progress['history'].append({'artifact': artifact, **previous})
            entry = {'state': 'running', 'run_id': run_id, 'artifact': artifact,
                     'identity_sha256': digest, 'identity': identity,
                     'updated_at': utc(), 'resume_requested': bool(unfinished)}
            progress['artifacts'][artifact] = entry
            atomic_json(progress_path, progress)
            atomic_json(folder / 'benchmark-identity.json', identity)
            atomic_json(folder / 'audit-policy.json', policy)

            pending_terminal=None
            terminal_persisted=False
            def persist(event):
                nonlocal terminal_persisted
                if terminal_persisted:raise BenchmarkError('An event cannot follow a terminal event')
                with (folder / 'events.jsonl').open('a') as stream:
                    stream.write(json.dumps(event) + '\n')
                if event.get('type') in TERMINAL_TYPES:terminal_persisted=True
            async def emit(event):
                nonlocal pending_terminal
                if pending_terminal is not None:raise BenchmarkError('Producer emitted after terminal')
                if event.get('type') in TERMINAL_TYPES:
                    pending_terminal=event
                    return
                persist(event)
                if event.get('agent') in {'SPECIALIST_FALLBACK','SPECIALIST_INCOMPLETE'}:
                    output(json.dumps({'event':event['agent'],'run_id':run_id,**event['data']}),flush=True)
                if event['type'] == 'step':
                    data = event['data']
                    output(json.dumps({'run_id': run_id, 'agent': event['agent'],
                                       'tool': data.get('tool'),
                                       'summary': data.get('summary', data.get('hypothesis', ''))}), flush=True)
            try:
                investigation = investigation_factory(run_id, artifact, controls, emit,
                                                      runs_root=runs_root, resume=bool(unfinished), local_preflight=local_preflight,routing=routing,risk_tier=policy['risk_tier'])
                report = await investigation.run()
                if not valid_report(report, artifact, run_id):
                    raise BenchmarkError('Audit did not produce a completed real report')
                if pending_terminal is None:raise BenchmarkError('Missing producer completion')
                observed=[json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()] if (folder/'events.jsonl').exists() else []
                if not accepted_real_recording(report,observed+[pending_terminal],run_id).accepted:
                    raise BenchmarkError('Audit trace has no accepted terminal completion')
                path = folder / 'report.json'
                # Orchestrator writes report.json; atomically preserve the returned
                # report as well so checkpoint/report identity cannot diverge.
                atomic_json(path, report)
                persist(pending_terminal)
                entry.update({'state': 'complete', 'report_sha256': file_sha256(path),
                              'updated_at': utc()})
                atomic_json(progress_path, progress)
                results.append(summary(report))
                write_aggregate()
                output(json.dumps(results[-1]), flush=True)
            except BaseException as exc:
                policy_label,policy_reason=verdict({},False,risk_tier=policy['risk_tier'])
                assessment={'status':'INCOMPLETE','risk_tier':policy['risk_tier'],'risk_policy':deepcopy(policy),
                            'policy_verdict':policy_label,'policy_reason':policy_reason,'accepted_completed_verdict':False}
                if not terminal_persisted:
                    persist({'type':'error','agent':'SYSTEM','timestamp':utc(),
                             'data':{'summary':'Audit attempt stopped; no accepted completion.','error_type':type(exc).__name__,**assessment}})
                entry.update({'state': 'incomplete', 'error_type': type(exc).__name__,
                              'updated_at': utc()})
                atomic_json(progress_path, progress)
                output(json.dumps({'event': 'audit_incomplete', 'artifact': artifact,
                                   'run_id': run_id, 'error_type': type(exc).__name__,
                                   **assessment,
                                   'next_action': 'Rerun with --resume after resolving the failure.'}), flush=True)
                raise
        write_aggregate('complete')
        return results


async def main():
    args = argument_parser().parse_args()
    load_env()
    try:
        await run_benchmark(list(ARTIFACTS) if args.artifact == 'all' else [args.artifact], resume=args.resume,
                            orchestrator=args.orchestrator,local_profile=args.local_profile,risk_tier=args.risk_tier)
    except LocalModelNeeded as exc:
        print(json.dumps({'status':'LOCAL MODEL NEEDED','summary':str(exc),
                          'next_action':'Load the required local model. No new run will start until preflight passes.'}),flush=True)
        raise SystemExit(1)
    except (asyncio.CancelledError, KeyboardInterrupt):
        raise
    except Exception as exc:
        # Provider exceptions can contain response bodies; expose only the type.
        print(json.dumps({'event': 'benchmark_stopped', 'error_type': type(exc).__name__,
                          'next_action': 'Resolve the error and rerun with --resume; use --fresh to restart.'}), flush=True)
        raise SystemExit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
