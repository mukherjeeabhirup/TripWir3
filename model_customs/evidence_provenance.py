"""Pure run/event/field provenance checks. No inference or SSE-envelope changes.

A check unit is one required claim plus each unmatched submitted claim. Without
required_claims, each submitted claim is a unit. Empty sets are not proof. Index
integrity errors fail the result; checked/total counts refer to claim units.
"""
from copy import deepcopy
import hashlib
import json
import re

_RECORD_FIELDS = {'run_id', 'event_id', 'index', 'role', 'event_type', 'data', 'data_sha256'}
_REF_FIELDS = {'run_id', 'event_id', 'role', 'event_type', 'path', 'value'}
_OBSERVATION_ROLES = {'SKEPTIC','REPORT','INVESTIGATOR','PROBE','VERIFY','WEIGHT_FORENSICS','PROVENANCE','FREEZE','RETRIEVE','EVIDENCE_LEDGER'}
_KINDS = {'attribution', 'input_trigger', 'output_marker'}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False)


def _run(value):
    return isinstance(value, str) and bool(value) and ':event:' not in value


def event_id(run_id, index):
    if not _run(run_id) or type(index) is not int or index < 0:
        raise ValueError('invalid_event_identity')
    return f'{run_id}:event:{index:06d}'


def _ordinal(run_id, value):
    if not _run(run_id) or not isinstance(value, str):
        raise ValueError('invalid_event_identity')
    match = re.fullmatch(re.escape(run_id) + r':event:(\d{6,})', value)
    if match is None:
        raise ValueError('invalid_event_identity')
    index = int(match[1])
    if event_id(run_id, index) != value:
        raise ValueError('noncanonical_event_identity')
    return index


def _digest(data):
    return hashlib.sha256(_canonical(data).encode('utf-8')).hexdigest()


def index_events(run_id, events):
    if not _run(run_id) or not isinstance(events, list):
        raise ValueError('invalid_event_index_input')
    records = []
    for index, event in enumerate(events):
        if (not isinstance(event, dict) or not isinstance(event.get('agent'), str)
                or not event['agent'] or not isinstance(event.get('type'), str)
                or not event['type'] or not isinstance(event.get('data'), dict)):
            raise ValueError('invalid_event_index_input')
        try:
            digest = _digest(event['data'])
        except (ValueError, TypeError, OverflowError, RecursionError):
            raise ValueError('invalid_event_data') from None
        records.append({'run_id': run_id, 'event_id': event_id(run_id, index),
                        'index': index, 'role': event['agent'], 'event_type': event['type'],
                        'data': deepcopy(event['data']), 'data_sha256': digest})
    return records


def _record_error(record, run_id):
    if not isinstance(record, dict) or set(record) != _RECORD_FIELDS:
        return 'invalid_event_record_schema'
    if record['run_id'] != run_id:
        return 'event_record_run_mismatch'
    if (type(record['index']) is not int or record['index'] < 0
            or not isinstance(record['role'], str) or not record['role']
            or not isinstance(record['event_type'], str) or not record['event_type']
            or not isinstance(record['data'], dict)):
        return 'invalid_event_record_schema'
    try:
        if record['event_id'] != event_id(run_id, record['index']):
            return 'event_record_identity_mismatch'
        if record['data_sha256'] != _digest(record['data']):
            return 'event_record_digest_mismatch'
    except (ValueError, TypeError, OverflowError, RecursionError):
        return 'invalid_event_record_data'
    return None


def _at_path(data, path):
    if not isinstance(path, list):
        raise ValueError('invalid_field_path')
    value = data
    for segment in path:
        if isinstance(value, dict) and isinstance(segment, str):
            if segment not in value:
                raise ValueError('field_path_missing')
            value = value[segment]
        elif isinstance(value, list) and type(segment) is int and 0 <= segment < len(value):
            value = value[segment]
        else:
            raise ValueError('invalid_field_path')
    return value


def make_ref(record, path):
    if not isinstance(record, dict):
        raise ValueError('invalid_event_record_schema')
    error = _record_error(record, record.get('run_id'))
    if error:
        raise ValueError(error)
    value = _at_path(record['data'], path)
    return {'run_id': record['run_id'], 'event_id': record['event_id'],
            'role': record['role'], 'event_type':record['event_type'], 'path': deepcopy(path), 'value': deepcopy(value)}


def typed_identities(trigger, marker):
    if not all(isinstance(value, str) and value for value in (trigger, marker)):
        raise ValueError('invalid_typed_identity')
    return {'input_trigger': {'kind': 'input_trigger', 'value': trigger},
            'output_marker': {'kind': 'output_marker', 'value': marker}}


def _claim_errors(run_id, by_id, claim, before):
    if (not isinstance(claim, dict) or set(claim) != {'kind', 'ref'}
            or not isinstance(claim['kind'], str) or claim['kind'] not in _KINDS):
        return ['invalid_claim_schema']
    ref = claim['ref']
    if not isinstance(ref, dict) or set(ref) != _REF_FIELDS:
        return ['invalid_reference_schema']
    if ref['run_id'] != run_id:
        return ['reference_run_mismatch']
    if not isinstance(ref['event_id'], str) or ref['event_id'] not in by_id:
        return ['unknown_event_reference']
    record = by_id[ref['event_id']]
    errors = []
    if ref['role'] != record['role']:
        errors.append('reference_emitter_mismatch')
    if ref['event_type'] != record['event_type']:
        errors.append('reference_event_type_mismatch')
    if record['role'] in _OBSERVATION_ROLES and record['event_type'] != 'observation':
        errors.append('invalid_attribution_event_type')
    if before is not None and record['index'] >= before:
        errors.append('reference_not_prior_evidence')
    try:
        actual = _at_path(record['data'], ref['path'])
        if _canonical(actual) != _canonical(ref['value']):
            errors.append('reference_value_mismatch')
    except (ValueError, TypeError, OverflowError, RecursionError):
        errors.append('invalid_reference_path_or_value')
        actual = None
    if claim['kind'] != 'attribution':
        kind = claim['kind']
        if (record['role'] != 'ORCHESTRATOR' or record['event_type'] != 'step' or ref['path'] != ['identities', kind]
                or not isinstance(actual, dict) or set(actual) != {'kind', 'value'}
                or actual.get('kind') != kind or not isinstance(actual.get('value'), str)
                or not actual['value']):
            errors.append('typed_identity_reference_mismatch')
    return errors


def _fingerprint(claim):
    try:
        return _canonical(claim)
    except (ValueError, TypeError, OverflowError, RecursionError):
        return None


def _units(claims, required):
    if not isinstance(claims, list):
        return [(None, 'claims_must_be_list')]
    if required is None:
        units = []; seen = set()
        for claim in claims:
            key = _fingerprint(claim)
            duplicate = key is not None and key in seen
            if key is not None:
                seen.add(key)
            units.append((claim, 'duplicate_claim' if duplicate else None))
        return units or [(None, 'empty_claim_set')]
    if not isinstance(required, list):
        return [(None, 'required_claims_must_be_list')]
    remaining = list(enumerate(claims)); units = []; expected_seen = set()
    expected_keys = set()
    for claim in required:
        key = _fingerprint(claim)
        duplicate = key is not None and key in expected_seen
        if key is not None:
            expected_seen.add(key); expected_keys.add(key)
        found = next((index for index, (_, candidate) in enumerate(remaining)
                      if key is not None and _fingerprint(candidate) == key), None)
        if found is None:
            units.append((claim, 'missing_required_claim'))
        else:
            remaining.pop(found)
            units.append((claim, 'duplicate_required_claim' if duplicate else None))
    for _, claim in remaining:
        key = _fingerprint(claim)
        units.append((claim, 'duplicate_claim' if key is not None and key in expected_keys
                      else 'unexpected_claim'))
    return units or [(None, 'empty_claim_set')]


def check_claims(run_id, records, claims, *, required_claims=None, max_checks=512,
                 before_event_id=None):
    """Validate attribution/typed identity, with explicit partial-check accounting.

    This proves agreement with the supplied event index, not semantic truth of
    arbitrary emitted prose. Callers must bind that index to the saved raw events
    and validate factual specialist claims against prior executed measurements.
    """
    units = _units(claims, required_claims)
    errors = []; by_id = {}; indices = set(); before = None
    if not _run(run_id):
        errors.append('invalid_run_id')
    if not isinstance(records, list):
        errors.append('event_records_must_be_list')
    else:
        for record in records:
            error = _record_error(record, run_id)
            if error:
                errors.append(error); continue
            if record['event_id'] in by_id or record['index'] in indices:
                errors.append('duplicate_event_identity'); continue
            by_id[record['event_id']] = record; indices.add(record['index'])
    if before_event_id is not None:
        try:
            before = _ordinal(run_id, before_event_id)
        except (ValueError, TypeError, OverflowError):
            errors.append('invalid_before_event_id')
    total = len(units)
    if type(max_checks) is not int or max_checks < 0:
        return {'status': 'FAIL', 'passed': False, 'checked': 0, 'total': total,
                'errors': list(dict.fromkeys(errors + ['invalid_max_checks']))}
    checked = 0
    for claim, coverage_error in units[:max_checks]:
        if coverage_error:
            errors.append(f'claim_{checked}:' + coverage_error)
        errors.extend(f'claim_{checked}:' + error for error in _claim_errors(run_id, by_id, claim, before))
        checked += 1
    if checked < total:
        errors.append('check_budget_exhausted')
        status = 'INCOMPLETE'
    else:
        status = 'FAIL' if errors else 'PASS'
    return {'status': status, 'passed': status == 'PASS', 'checked': checked,
            'total': total, 'errors': list(dict.fromkeys(errors))}
