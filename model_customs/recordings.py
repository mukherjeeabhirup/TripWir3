"""Pure acceptance rules for recorded real audits. No filesystem or model calls."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
from .report_provenance import check_report_provenance
from .claims import valid_specialist_result, validate_claim_rows, decode_specialist_content
from .routing import valid_local_preflight,recorded_routes,route_equal,valid_context_budget

LOCAL_MODEL = 'nvidia-nemotron-3-nano-30b-a3b-mlx'


def valid_preflight(result):
    if isinstance(result,dict) and 'local_profile' in result:return valid_local_preflight(result)
    return (isinstance(result, dict) and result.get('status') == 'ready'
            and result.get('model') == LOCAL_MODEL and result.get('requested_model') == LOCAL_MODEL and result.get('observed_model') == LOCAL_MODEL and result.get('answer_verified') is True
            and result.get('models_http_status') == 200 and result.get('completion_http_status') == 200)


REAL_ORIGIN = 'real_local_inference_and_live_nemotron'
TERMINAL_TYPES = frozenset({'complete', 'error', 'cancel', 'cancelled', 'canceled', 'failure', 'failed', 'done'})
_SOURCE_ID = re.compile(r'^[a-f0-9]{32}$')


@dataclass(frozen=True)
class RecordingCheck:
    errors: tuple[str, ...]

    @property
    def accepted(self) -> bool:
        return not self.errors


def accepted_real_recording(report, events, run_id: str, *, cloud_responses=None) -> RecordingCheck:
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
    try:
        routes=recorded_routes(report)
        expected_model=routes['local']['selected_id'] if routes else LOCAL_MODEL
        if routes:
            from .cloud_evidence import response_policy,identity_allowed
            if not route_equal(report.get('model_routing'),routes):errors.append('model_routing_alias_mismatch')
            inputs=report['run_signature']['inputs']
            if inputs.get('cloud_primary')!=routes['cloud']['model'] or inputs.get('cloud_fallback')!=routes['cloud']['fallback_model']:
                errors.append('model_routing_signature_mismatch')
            if any(call.get('provider')!=routes['cloud']['provider'] or call.get('base_url')!=routes['cloud']['base_url']
                   or call.get('requested_model')!=call.get('model') or call.get('configured_model')!=routes['cloud']['model']
                   or call.get('model') not in {routes['cloud']['model'],routes['cloud']['fallback_model']}
                   or call.get('is_fallback') is not (call.get('model')!=routes['cloud']['model']) for call in report.get('cloud_calls',[])):
                errors.append('cloud_routing_attempt_mismatch')
            classification='mixed_or_fallback' if any(c.get('model')!=routes['cloud']['model'] for c in report.get('cloud_calls',[])) else 'pure_primary'
            if report.get('cloud_route_classification')!=classification:errors.append('cloud_route_classification_mismatch')
            if routes.get('schema_version')==2:
                for call in report.get('cloud_calls',[]):
                    expected=response_policy(call.get('requested_model'),routes['cloud']['provider'],routes['cloud']['base_url'],configured_model=routes['cloud']['model'])
                    if not route_equal(call.get('response_identity_policy'),expected):errors.append('cloud_response_policy_mismatch')
                    if call.get('parse_validated') is True and not identity_allowed(call):errors.append('cloud_observed_identity_rejected')
    except (ValueError,TypeError,KeyError,AttributeError):
        routes=None;expected_model=None;errors.append('invalid_source_bound_model_routing')
    from .cloud_evidence import check_cloud_evidence
    errors.extend(check_cloud_evidence(report,events,cloud_responses,routes))
    if report.get('data_origin') != REAL_ORIGIN:
        errors.append('report_origin_is_not_real_live_inference')
    if report.get('mode') != 'live' or 'source_run_id' in report:
        errors.append('report_is_not_original_live_mode')
    if not isinstance(report.get('agent_grounding'), dict) or report['agent_grounding'].get('passed') is not True:
        errors.append('agent_grounding_not_passed')
    if not isinstance(report.get('report_grounding'),dict) or report['report_grounding'].get('passed') is not True:
        errors.append('primary_report_grounding_not_passed')
    if not valid_preflight(report.get('local_model_preflight')):
        errors.append('local_model_preflight_not_passed')
    engines = report.get('specialist_engines', {})
    narrative = report.get('narrative', {})
    draft = narrative.get('model_draft', {}) if isinstance(narrative, dict) else {}
    raw = draft.get('raw', {}) if isinstance(draft, dict) else {}
    if (not isinstance(engines, dict) or any(engines.get(role) != 'local_lmstudio_nemotron' for role in ('investigator','skeptic'))
            or not isinstance(raw, dict) or raw.get('engine') != 'local_lmstudio_nemotron' or raw.get('model') != expected_model):
        errors.append('local_specialist_completion_required_no_fallback')
    calls = report.get('specialist_calls', [])
    if (not isinstance(calls, list) or len(calls)!=3
            or any(not isinstance(call, dict) or call.get('status') != 200 or call.get('response_http_status') != 200 or call.get('model') != expected_model or call.get('requested_model') != expected_model or call.get('observed_model') != expected_model or not isinstance(call.get('role'),str) or call.get('engine') != 'local_lmstudio' or call.get('schema_validated') is not True or call.get('finish_reason') != 'stop' for call in calls)
            or {call.get('role') for call in calls if isinstance(call, dict)} != {'INVESTIGATOR','SKEPTIC','REPORT'}):
        errors.append('successful_exact_local_specialist_calls_required')
    outputs=report.get('specialist_outputs',{})
    for role in ('investigator','skeptic'):
        value=outputs.get(role) if isinstance(outputs,dict) else None
        # Execution/disclosure are parent metadata for proposals, not Nano fields.
        payload={k:v for k,v in value.items() if k not in {'engine','model','execution_status','disclosure','factual_grounding'}} if isinstance(value,dict) else None
        if (not isinstance(value,dict) or value.get('engine')!='local_lmstudio_nemotron' or value.get('model')!=expected_model
                or not valid_specialist_result(role.upper(),payload)):
            errors.append('invalid_local_role_schema:' + role)
    payload={k:v for k,v in raw.items() if k not in {'engine','model'}} if isinstance(raw,dict) else None
    ledger=report.get('evidence_ledger')
    if (not valid_specialist_result('REPORT',payload) or not isinstance(ledger,dict)
            or not isinstance(ledger.get('executed_probes'),dict) or not isinstance(ledger.get('verification_groups'),dict)
            or validate_claim_rows(raw.get('claim_rows') if isinstance(raw,dict) else None,ledger)):
        errors.append('invalid_scoped_report_claims')
    records=report.get('specialist_provider_outputs')
    if routes:
        profile={k:v for k,v in routes['local'].items() if k not in {'selected_id','loaded_instance'}}
        if any(not isinstance(c,dict) or not route_equal(c.get('local_profile'),profile) or c.get('provider')!='lm_studio'
               or c.get('base_url')!=routes['local']['base_url'] or not route_equal(c.get('loaded_instance'),routes['local']['loaded_instance']) or c.get('endpoint')!='/v1/completions'
               or type(c.get('loaded_state_http_status')) is not int or c.get('loaded_state_http_status')!=200 for c in (calls if isinstance(calls,list) else [])+(records if isinstance(records,list) else [])):
            errors.append('local_routing_attempt_mismatch')
        budget_version=profile.get('specialist_budget_policy_version',1)
        if any(not valid_context_budget(c.get('context_budget'),routes['local']['loaded_instance']['runtime_context_tokens'],role=c.get('role'),policy_version=budget_version) for c in (calls if isinstance(calls,list) else []) if isinstance(c,dict)):
            errors.append('local_context_budget_mismatch')
        if budget_version==2:
            from .specialist_budget import valid_wire_request
            requests=report.get('specialist_provider_requests')
            if not isinstance(requests,list) or len(requests)!=3 or not isinstance(calls,list) or len(calls)!=3:
                errors.append('specialist_wire_budget_binding_required')
            else:
                indices=[]
                for request in requests:
                    index=request.get('call_index') if isinstance(request,dict) else None
                    if type(index) is not int or index not in range(3) or index in indices or not valid_wire_request(request,calls[index],expected_model):
                        errors.append('specialist_wire_budget_binding_mismatch')
                    indices.append(index)
    if not isinstance(records,list) or not isinstance(calls,list) or len(records)!=3 or len(calls)!=3:
        errors.append('raw_specialist_responses_required')
    else:
        seen_raw=set()
        for record in records:
            try:
                if not isinstance(record,dict):raise ValueError('Malformed raw response')
                index=record.get('call_index')
                if type(index) is not int or index not in range(3) or index in seen_raw:raise ValueError('Invalid call link')
                seen_raw.add(index)
                call=calls[index]
                role=record['role']
                if (role!=call.get('role') or record.get('requested_model')!=call.get('requested_model')
                        or record.get('model')!=expected_model or record.get('observed_model')!=expected_model
                        or record['model']!=call.get('observed_model')):raise ValueError('Identity mismatch')
                decoded=decode_specialist_content(record['content'])
                if not valid_specialist_result(role,decoded):raise ValueError('Invalid raw role schema')
                derived=raw if role=='REPORT' else outputs.get(role.lower())
                derived_payload={k:v for k,v in derived.items() if k not in {'engine','model','execution_status','disclosure','factual_grounding'}}
                if decoded!=derived_payload:raise ValueError('Raw/derived mismatch')
            except (KeyError,ValueError,TypeError,AttributeError,IndexError):
                errors.append('raw_specialist_response_mismatch')
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
        if (event.get('agent') in {'SPECIALIST_FALLBACK','SPECIALIST_INCOMPLETE'}
                or isinstance(event.get('data'), dict) and event['data'].get('engine') == 'rule_based_tool'):
            errors.append('specialist_fallback_disqualifies_hero:' + str(index))
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
    provenance=check_report_provenance(report,events[:-1],run_id)
    if report.get('provenance_check')!=provenance:
        errors.append('report_provenance_check_mismatch')
    if not provenance['passed']:
        errors.append('report_provenance_'+provenance['status'].lower())
    return RecordingCheck(tuple(errors))
