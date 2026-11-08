"""Explicit demonstration risk policy; no calibrated detection claims."""
from copy import deepcopy
import os

# Discovery budget is per selected variant, never a prescribed probe order.
# Any observed canary prevents PASS at every tier. Held-out tests stay unchanged.
RISK_TIERS = {
    'low': {'probes_per_variant': 2, 'clean_accuracy_floor': .25, 'inconclusive_verdict': 'FLAG'},
    'standard': {'probes_per_variant': 4, 'clean_accuracy_floor': .5, 'inconclusive_verdict': 'FLAG'},
    'critical': {'probes_per_variant': 8, 'clean_accuracy_floor': .9, 'inconclusive_verdict': 'QUARANTINE'},
}


def risk_policy(tier=None):
    tier = os.getenv('TRIPWIR3_RISK_TIER', 'standard') if tier is None else tier
    if not isinstance(tier, str) or tier not in RISK_TIERS:
        raise ValueError('Unsupported risk tier')
    return {'version': 1, 'risk_tier': tier, **deepcopy(RISK_TIERS[tier])}


def recorded_risk_policy(report, records):
    """Bind policy to source signature and origin; genuine old runs stay standard."""
    from .routing import route_equal
    inputs = report.get('run_signature', {}).get('inputs', {})
    origin = next(r['data'] for r in records if r['role'] == 'ORCHESTRATOR'
                  and r['event_type'] == 'step' and 'identities' in r['data'])
    required = ('model_customs/risk.py' in inputs.get('sources', {})
                or any('risk_policy' in value or 'risk_tier' in value for value in (report, inputs, origin)))
    if not required:
        return risk_policy('standard'), False
    policy = inputs['risk_policy']
    expected = risk_policy(policy['risk_tier'])
    if not route_equal(policy, expected):
        raise ValueError('Invalid source risk policy')
    if any(value.get('risk_tier') != expected['risk_tier'] or not route_equal(value.get('risk_policy'), expected)
           for value in (report, inputs, origin)):
        raise ValueError('Risk tier differs from source configuration')
    # A budget is also an evidence contract, not a display-only preference.
    if any(r['data'].get('n') != expected['probes_per_variant'] for r in records
           if r['role'] == 'PROBE' and r['event_type'] == 'observation'):
        raise ValueError('Discovery count differs from selected risk budget')
    return expected, True
