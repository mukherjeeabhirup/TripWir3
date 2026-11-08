"""Pure acceptance rules for recorded real audits. No filesystem or model calls."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

REAL_ORIGIN = 'real_local_inference_and_live_nemotron'
TERMINAL_TYPES = frozenset({'complete', 'error', 'cancel', 'cancelled', 'canceled', 'failure', 'failed', 'done'})
_SOURCE_ID = re.compile(r'^[a-f0-9]{32}$')


@dataclass(frozen=True)
class RecordingCheck:
    errors: tuple[str, ...]

    @property
    def accepted(self) -> bool:
        return not self.errors


def accepted_real_recording(report, events, run_id: str) -> RecordingCheck:
    """One shared predicate for catalog, replay admission and packaging.

    This checks the executed trace's structural consistency and declared origin;
    it does not establish independent scientific validation or a signed origin.
    A completion is accepted only as the single final terminal event. Error or
    cancellation terminals anywhere invalidate the entire source recording.
    """
    errors = []
    if not isinstance(run_id, str) or not _SOURCE_ID.fullmatch(run_id):
        errors.append('invalid_source_run_id')
    if not isinstance(report, dict):
        return RecordingCheck(tuple(errors + ['malformed_report']))
    try:
        json.dumps(report, allow_nan=False)
    except (ValueError, TypeError):
        errors.append('report_is_not_finite_json')
    if report.get('run_id') != run_id:
        errors.append('report_run_id_mismatch')
    if report.get('data_origin') != REAL_ORIGIN:
        errors.append('report_origin_is_not_real_live_inference')
    if report.get('mode') != 'live' or 'source_run_id' in report:
        errors.append('report_is_not_original_live_mode')
    if not isinstance(report.get('agent_grounding'), dict) or report['agent_grounding'].get('passed') is not True:
        errors.append('agent_grounding_not_passed')
    if not isinstance(report.get('artifact'), str) or report['artifact'] not in {'base', 'benign', 'poisoned'}:
        errors.append('invalid_control_artifact')
    if not isinstance(report.get('verdict'), str) or report['verdict'] not in {'PASS', 'FLAG', 'QUARANTINE'}:
        errors.append('missing_completed_verdict')
    if not isinstance(events, list) or not events:
        return RecordingCheck(tuple(errors + ['missing_or_malformed_events']))
    try:
        json.dumps(events, allow_nan=False)
    except (ValueError, TypeError):
        return RecordingCheck(tuple(errors + ['events_are_not_finite_json']))
    terminal_indices = []
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            errors.append(f'malformed_event:{index}')
            continue
        kind = event.get('type')
        if not isinstance(kind, str):
            errors.append(f'malformed_event_type:{index}')
            continue
        if kind in TERMINAL_TYPES:
            terminal_indices.append(index)
            if kind != 'complete':
                errors.append(f'source_error_or_cancel_terminal:{index}')
        if kind not in {'step', 'observation', 'complete'}:
            errors.append(f'unaccepted_event_type:{index}')
        if not isinstance(event.get('agent'), str) or not event['agent'] or not isinstance(event.get('data'), dict):
            errors.append(f'malformed_event_payload:{index}')
        if 'run_id' in event and event['run_id'] != run_id:
            errors.append(f'event_run_id_mismatch:{index}')
        if 'data_origin' in event and event['data_origin'] != REAL_ORIGIN:
            errors.append(f'event_origin_mismatch:{index}')
        if ('mode' in event and event['mode'] != 'live') or 'source_run_id' in event:
            errors.append(f'event_is_not_original_live_mode:{index}')
        if 'timestamp' in event and (not isinstance(event['timestamp'],str) or not event['timestamp']):
            errors.append(f'malformed_event_timestamp:{index}')
        if kind == 'complete' and event.get('data') != report:
            errors.append(f'completion_report_mismatch:{index}')
    if len(terminal_indices) != 1:
        errors.append('requires_exactly_one_terminal_event')
    if not terminal_indices or terminal_indices[0] != len(events) - 1:
        errors.append('terminal_event_must_be_last')
    if not isinstance(events[-1], dict) or events[-1].get('type') != 'complete':
        errors.append('final_event_is_not_complete')
    return RecordingCheck(tuple(errors))
