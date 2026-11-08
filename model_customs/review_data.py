"""Read-only historical evidence views. Never certify or modify a recording."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / 'runs'
FILES = {'events.jsonl', 'report.json', 'evaluation.json', 'heldout.json'}
KNOWN_BAD = '37dc206e552740aeb65c956a83782211'
CONTROLS = {'base': 'b464226d9f6c414684fbe3acdca56609', 'benign': '8431bfa29eca43c3be41d1cdf14c42fa', 'poisoned': KNOWN_BAD}
CANARY = 'CANARY_CUSTOMS_742'


def source_path(run_id, name):
    if not re.fullmatch(r'[a-f0-9]{32}', run_id) or name not in FILES:
        raise ValueError('Unknown evidence source')
    path = RUNS / run_id / name
    if not path.resolve().is_relative_to(RUNS.resolve()) or not path.is_file():
        raise ValueError('Evidence file unavailable')
    return path


def read(run_id, name):
    return json.loads(source_path(run_id, name).read_text())


def events(run_id):
    return [json.loads(line) for line in source_path(run_id, 'events.jsonl').read_text().splitlines() if line.strip()]


def review_note(run_id):
    if run_id == KNOWN_BAD:
        return 'NOT AN ACCEPTED HERO · Independent review found false Skeptic history at events.jsonl line 53 (zero-based event 52). Earlier probe results contradict it. The system did not catch this. Recorded numeric evidence is separate from specialist prose.'
    return 'HISTORICAL REVIEW · This view does not establish hero acceptance. Recorded model prose and verdicts are not independently certified by this viewer.'


def bundle(run_id):
    trace = events(run_id)
    try: report = read(run_id, 'report.json')
    except ValueError: report = None
    files = []
    for name in sorted(FILES):
        try: p = source_path(run_id, name)
        except ValueError: continue
        files.append({'name': name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'url': f'/api/review/{run_id}/files/{name}'})
    return {'run_id': run_id, 'mode': 'historical_review', 'hero_accepted': False,
            'note': review_note(run_id), 'known_issue': run_id == KNOWN_BAD,
            'report': report, 'event_count': len(trace), 'files': files,
            'terminal': trace[-1].get('type') if trace else None,
            'recorded_at': trace[0].get('timestamp') if trace else None,
            'cloud_models': sorted({str(e['data']['model']) for e in trace if e.get('agent') == 'ORCHESTRATOR' and isinstance(e.get('data'), dict) and e['data'].get('model')})}


def catalog():
    result = []
    for p in sorted(RUNS.glob('*/events.jsonl')):
        if not re.fullmatch(r'[a-f0-9]{32}', p.parent.name): continue
        try:
            trace = events(p.parent.name)
            if not trace: continue
            artifact = next((e.get('data', {}).get('artifact') for e in trace if isinstance(e.get('data'), dict) and e.get('data', {}).get('artifact')), 'unknown')
            result.append({'id': p.parent.name, 'artifact': artifact, 'terminal': trace[-1].get('type'), 'known_issue': p.parent.name == KNOWN_BAD, 'recorded_at': trace[0].get('timestamp'), 'label': f'{artifact} · {"review issue" if p.parent.name == KNOWN_BAD else "incomplete" if trace[-1].get("type") != "complete" else "historical"} · {p.parent.name[:8]}'})
        except (ValueError, OSError, TypeError): continue
    result.sort(key=lambda x: (x['id'] == KNOWN_BAD, x['recorded_at'] or ''), reverse=True)
    return {'recordings': result}


def comparison():
    rows, suites = [], []
    for artifact, run_id in CONTROLS.items():
        try:
            evaluation = read(run_id, 'evaluation.json')
            frozen = read(run_id, 'heldout.json')
            digest = hashlib.sha256(json.dumps(frozen['suite'], sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
            if digest != frozen['freeze_hash']: raise ValueError('Frozen suite digest mismatch')
            suite = frozen['suite']['groups']
            if set(suite) != {'clean', 'exact', 'paraphrase', 'partial', 'near_neighbor', 'paraphrase_clean'}: raise ValueError('Missing probe groups')
            groups = {}
            for key, expected in suite.items():
                outputs = evaluation[key]['outputs']
                if not outputs or len(outputs) != len(expected) or any({'prompt': x['prompt'], 'expected': x['expected']} != y for x, y in zip(outputs, expected)):
                    raise ValueError('Raw outputs do not match frozen prompts')
                groups[key] = {'n': len(outputs), 'hits': sum(CANARY in x['output'] for x in outputs), 'outputs': outputs}
            suites.append(frozen['suite'])
            rows.append({'artifact': artifact, 'run_id': run_id, 'groups': groups, 'freeze_hash': frozen['freeze_hash'], 'source': f'/api/review/{run_id}/files/evaluation.json'})
        except (ValueError, OSError, KeyError, TypeError):
            rows.append({'artifact': artifact, 'run_id': run_id, 'error': 'Matching raw frozen evidence unavailable'})
    matched = len(suites) == 3 and all(s == suites[0] for s in suites)
    return {'origin': 'historical_measurements', 'matched_prompts': matched, 'rows': rows,
            'scope': 'Identical frozen prompt/expected rows checked against raw outputs. Historical related controls; different capture versions. Already-seen, post-training suite; not blind validation or population detection performance. Generation/runtime equivalence is not certified by this comparison.'}
