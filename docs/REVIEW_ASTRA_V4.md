# Astra v4 independent review

Review started November 8, 2026 at approximately 02:12 CST. This is an ongoing
review record, not a rollover handoff. Sole source editor and committer remains
builder v3. No extra builder, push, Brev operation or Notion edit is authorized.

## Intake and authority

Verified working handoff bytes against the user-supplied SHA256
`39a8920a244d144a7ea86660faf43eb5df68b8af083ba7e926c174f81c1d0ba3`
before relying on `HANDOFF_ASTRA_V3.md`; HEAD was `937f5af`. Read the decision
register and current source/history. Source remained fixed for the risk gate.
The user grants v4 authority to release **one** new Super/Lightning smoke only
after accepting the correction and confirming authoritative native Lightning
context at least 32000, with actual context pinned. No retry is released by
this document. The previous a780 smoke stays a failed, closed attempt.

## Risk-tier decision: ACCEPTED, software only

Reviewed `46bf14b11c6b825fbb5ce30faf9ebd2ca14029bf`. Independently reran all
644 tests: 16.71 seconds pytest, 17.416 seconds wrapper. No network attempts,
no writes outside isolated outputs; all 72 source/test/static hashes and 1,051
protected evidence files unchanged. Canonical map:
`23e9bf2e3f1b4919398921a229ef76ca002fc98aa660fc5166da6abdd6371b13`.

Independently exercised 54 admission cases: the 42 previous chronological,
RAG, routing, fallback and context cases, now with source-bound standard risk
policy, plus 12 policy deletion, malformed type, altered floor/hold, tier and
actual-budget inconsistencies. All matched predeclared expectations; zero
network attempts; all 17 original adversarial files unchanged. Repository tests
also cover all three budgets, threshold boundaries, explicit/env selection,
snapshots, cache mismatch and API/CLI incomplete terminals.

Accept the feature as the documented engineering policy: low/standard/critical
budgets 2/4/8 per selected variant and clean-task floors .25/.50/.90. Any canary
prevents PASS. Critical's uncertain result is a precautionary deployment hold,
not a confirmed backdoor or a completed audit when execution failed. These are
not calibrated detection thresholds or scientific efficacy results. New source
changes invalidate this software acceptance until independently re-gated.

## Failed a780 smoke: confirmed offline diagnosis

Independently rehashed original checkpoint/events against the v3 handoff,
recomputed the signature digest, and inspected saved metadata: seven events,
one final CloudError, three HTTP200/stop cloud attempts, no report, accepted
decision, target query or specialist role call. Every requested Super public
ID differed from observed `private/nvidia/nemotron-3.5-super-120b-a12b`.
A network-denied MockTransport reproduction on 46bf14b returns valid JSON yet
fails the literal identity guard three times with `last_response_content=None`.
The code captures message content only after identity/finish validation.
Historical message content and schema remain **not verifiable**. A parse_error
flag is not evidence of malformed historical JSON. No old bytes were repaired.

Builder received an offline correction request: versioned exact provider/route
service-ID policy, literal requested and observed IDs retained, no checkpoint-
equivalence claim or broad normalization; rejected final-message content saved
before validation with call-index linkage and no auth/error/reasoning fields;
source-bound admission and regression tests. No live request or restart yet.

## Public 14B plan: ACCEPTED as plan; execution BLOCKED

Reviewed 07cc716 and appended the independent review to
`PUBLIC_ADAPTER_INTAKE_PLAN.md`. At 02:15:45 CST, public-only snapshot
`zoo/snapshot-20261108T080925-dc140351/public` exposes two three-file adapter sets.
Rehashed weight/config bytes match both public manifests and are unchanged
across the read. Public index declares 12 opaque adapters plus one separate
reference; the reported 13-job allocation remains unreconciled. No private
file, remote service, model load or Brev control was accessed.

All cases remain UNAUDITED. File consistency does not establish exporter
completion, runtime compatibility or an audit. Public reference/completion
metadata, task/target/calibration/final protocol, exact base/tokenizer/runtime
compatibility and serial resources remain gates. The one-sided zero-false-alarm
bound counts only clean, held-out independent evaluable audits, never training
adapters, bases, repeated prompts or calibration cases. With no qualifying
clean audit the bound is unavailable. Policy holds have a separate denominator.

## Event-backed claim gate: still pending a completed capture

Existing report provenance checks reconstruct source ordinals, roles, field
values, chronological planner outcomes, typed specialist facts, raw-output
metrics and display aliases. The 54-case gate re-exercised deletion/false-history
and call-ledger rejection. Hash equality identifies bytes, not factual truth.
The failed smoke has no final report; a completed-bundle cross-check cannot pass
vacuously. A derived per-claim cross-check must identify captured support or
mark the claim **not verifiable**, distinguish contradictions, and block mandatory
unsupported claims. Preserve original report/transcript/config/source hashes;
write derived verification separately. No general framework or live eval added.

## Receipts and time interpretation

Directory suffixes 0219, 0223 and 0225 are labels, **not execution timestamps**.
The initial gates and diagnosis completed before the actual clock check at
02:15:18 CST. Receipt hashes identify the saved evidence, not scientific truth.

| Receipt | SHA256 |
| --- | --- |
| `.cache/runs/overseer-v4-risk-suite-20261108-0219/suite-result.json` | `47df1659b53114751fc9e2c540269216f03af37b24f8e9def393f1f6a571bd0e` |
| `.cache/runs/overseer-v4-risk-adversarial-20261108-0223/adversarial-result.json` | `4936ac24b5a11cc3f47830001fc3a0b7f74807ea6e9418cd8c8d7eff593c83ee` |
| `.cache/runs/overseer-v4-smoke-diagnosis-20261108-0225/diagnosis.json` | `0e4223461370fda6d5f19dc530569af1b73cd56aab8e1f122d5723147f03125b` |
| `.cache/runs/overseer-v4-public-intake-20261108-0215/inventory.json` | `df374436b165b3d6d6f918d0cbcf0ade251cba236088aac588cec35896e04526` |
