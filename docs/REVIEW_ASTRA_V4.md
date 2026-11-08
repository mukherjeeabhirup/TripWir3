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

## Final software correction and single retry outcome

**Current disposition: NOT READY. Smoke REJECTED. Hero CLOSED. Live calls stopped;
the one authorized retry is consumed.** No further model call, repair or capture
is inferred from this review.

The initial identity/capture correction `7f20629` passed an independent 684-test
suite and 66 schema-2 admission cases, but v4 rejected it after a separate offline
reproduction: broad secret-name matching treated non-secret
`TOKENIZERS_PARALLELISM=false` as a credential and discarded valid JSON containing
`false`. Preserve that rejected result and reproduction. The builder's narrow
`fe8dbade60d9794b01632463a866a6fb9698fab4` fix restricts redaction to the supported
NVIDIA and LM Studio authentication variables. V4 independently reran all 688
tests (17.51 seconds, wrapper 18.291), re-executed the original reproduction in
a new directory successfully, and verified only llm.py and its tests changed
since the 66-case gate. All admission code stayed unchanged. All 74 source/test
hashes and 1,051 protected files remained stable, with zero network/outside-output
write attempts. Software correction **ACCEPTED**, not demo acceptance.

Current canonical 74-file map:
`148b82060f54a1135018a7a719c581b798743d23e6ed0a500dfbd59a0d1d8a42`.
Combined receipt:
`.cache/runs/overseer-v4-allowlist-suite-20261108-0228/combined-gate.json`.
The 66-case schema-2 receipt is in
`.cache/runs/overseer-v4-super-adversarial-20261108-0225/adversarial-result.json`.

Fresh local preflight at 02:29:38 CST passed. V4 independently rehashed all four
manifest-listed files and read the native/tiny wire responses: exactly one loaded
intended MLX 4-bit Lightning instance, authoritative context **32000**, exact
requested/observed `nvidia-nemotron-3.5-lightning-30b-a3b`, literal READY and stop.
Evidence and independent review:
`.cache/runs/lightning-preflight-20261108-0229/` and
`.cache/runs/overseer-v4-preflight-review-20261108-0230/review.json`.
Only after this confirmation did v4 release the user's **single** retry.

Retry `3f078d7567064cd181eca62213d830d2` ended at **02:31:24.151064 CST** with
17 events and one final LocalModelNeeded error; no complete event, report,
held-out freeze or accepted verdict. Two accepted cloud actions selected
provenance then investigator. Both Super calls were HTTP200/stop, requested the
literal public ID and observed the permitted private service ID, without fallback.
Both actual final messages were captured and matched their call-index digests,
manifest and decoded candidate decisions. This validates that integration path
for these two calls, not checkpoint-weight equivalence or comparative performance.

The one Investigator call returned HTTP200/stop from the exact pinned Lightning
instance. Its captured text is **parseable JSON containing a schema definition**
(`type`, `properties`, `required`, `additionalProperties`) instead of a result
object with the five required Investigator fields. Independent decoding and
`valid_specialist_result` confirm rejection. This is an observed schema-instance
failure, not malformed JSON, missing/unloaded model, context overflow, or proof
of a generally broken model. The prompt's wording is a possible explanation,
not an experimentally established cause. Actual context remained32000 and the
full-prompt estimate was2649. A SPECIALIST_FALLBACK-labelled event explicitly
records `fallback_executed:false`; no substitute ran. The final standard-policy
FLAG is only an operational INCOMPLETE disposition, never an accepted artifact
finding. There were zero recorded target queries and only a provenance observation.

V4 recomputed 23 chronological candidate checks and typed event telemetry,
28 run-signature source hashes, all74 current map entries, both cloud raw links,
the local response/pin/schema and terminal semantics. All five raw run files and
1,051 previous protected files were rehashed unchanged; reviewer network attempts
were zero. The shared recording predicate rejects the missing report.
Independent evidence:
`.cache/runs/overseer-v4-smoke-review-3f078-20261108-0233/independent-review.json`.

The derived `claim-checks.md` in that directory maps supported review claims to
captured event ordinals and associated raw checkpoint/response fields. Completed
artifact findings, completed-report claim coverage and checkpoint-equivalence
claims are explicitly **not verifiable**. Missing support is not a fabricated
contradiction, and missing report is not a vacuous PASS. No completed-bundle
claim gate, offline replay or browser acceptance is claimed. Hashes identify
preserved bytes; they do not prove the content true.

The 14B intake plan remains accepted only as a plan; every incoming case is
UNAUDITED and execution prerequisites remain unresolved. No private truth was
opened. No Brev action, Notion edit, source-changing helper, push or further live
attempt followed the failed retry. Future work needs a separately reviewed
Investigator response-contract correction and applicable new execution authority;
there is no retry-until-success allowance.


## 02:42 coordination follow-up — offline checks through 02:50 CST

Starscream explicitly requires Abhirup's approval for any further Super/Lightning
live smoke or hero capture. The previous single allowance remains consumed.
No preflight, model request, restart or capture is authorized by this follow-up.

At 02:46:22 CST, v4 read only `public/` in local snapshot
`snapshot-20261108T083613-1aa985a3`. Five adapter IDs have all three expected
files. Independently recomputed config/weight hashes match all five public
manifests, and the inspected public bytes stayed stable. The index has 12 adapter
IDs plus a separate reference. All cases remain **UNAUDITED**; file consistency
is not runtime compatibility, exporter-completion proof or audit acceptance.
This review does not verify the coordinator's entire 80-file snapshot count,
remote instance state, controller liveness or training completion estimate.
No private data or Brev control was accessed. Receipt:
`.cache/runs/overseer-v4-public-intake-20261108-0246/inventory.json`.
The intake protocol and false-alarm denominator gates remain unchanged.

A new offline MockTransport replay exercises the accepted `Specialists.ask`
path against the retained Investigator text. All three expectations pass:
(1) the real schema definition fails as `response_schema`, preserving its text
and executing no fallback; (2) a synthetic populated valid result passes; and
(3) a synthetic extra-field result fails without fallback. Each case makes one
mock completion request and zero real network requests. All 74 reviewed source
hashes and the five original raw run files remain unchanged. The request was
reconstructed from pinned source and captured preceding events; its 1802-character
prompt length matches recorded telemetry, but the original specialist wire
request was not retained. This is contract replay, not inference reproduction.
Receipt: `.cache/runs/overseer-v4-investigator-contract-20261108-0247/result.json`.

**Decision: no demonstrated parser/validator defect, and no source fix requested.**
The immediate failure is established: a schema definition cannot satisfy the
required result-instance contract. Why Lightning generated that definition
remains unproven; mocked responses cannot establish prompt causality or validate
an inference fix. The conditional authority for a tested root-cause correction
has not been exercised. No streaming diagnostic or additional model call was made.

The tooling record now separates observed runtime/development work, relayed
advice and missing attribution evidence. A read-only builder lookup found no
specific Cursor + local Nemotron development task/output/commit or GrokBot
execution receipt in the inspected project records. `ADVISOR_MEGATRON.md`
supports relayed advisory input, not proof of bot automation. Document these
limits in `TOOLING.md` and the README; do not fabricate tool use or eligibility.

New receipt SHA256 values (identify bytes, not truth):
- Public inventory: `5ce9c75694da6ca3d222ac7aa711bd9998b733fbaaba47ddbd4d8bc4f84f2e5b`.
- Offline contract replay result: `47ec403caf73f69615d10fb8850774d7c270c3ae582b98c2840cc95eee3e9eb7`.


## 03:30 advice review — request shape and offline validation boundaries

Astra independently accepts the documentation clarification. [LM Studio's
structured-output documentation](https://lmstudio.ai/docs/developer/openai-compat/structured-output)
describes `/v1/chat/completions` with the schema in
`response_format.json_schema.schema` and output in `choices[0].message.content`.
It identifies Outlines for MLX and llama.cpp grammars for GGUF. Its per-model
capability caveat does not support a blanket MLX limitation, and model size alone
does not establish this exact Lightning checkpoint's compatibility or enforcement.
This documentation was read without contacting the local inference server.

The pinned `fe8dbad` specialist source uses **legacy `/v1/completions`**, a raw
prompt containing schema instructions, and extraction from `choices[0].text`.
An offline MockTransport captured the actual serialized request bytes generated
by that source: exactly `model`, `temperature`, `max_tokens`, `stream`, `stop`
and `prompt`; **no `response_format` or `messages` field**. The explicit schema
is prompt text followed by client validation; this client path does not submit
the documented structured-chat request. There is no submitted response-format
schema here to characterize as looser than the downstream validator.

This establishes the pinned client's request shape, not why Lightning echoed a
schema or how a different request would behave. The original specialist wire
request was not retained. The replay reconstructs the prompt from pinned source
and saved preceding events (1802 characters, matching telemetry); it is not a
historical wire capture. No wrong-field extraction or Outlines defect is proven.

The earlier three cases covered a populated valid result, the retained schema
definition, and an unknown extra field. They did not separately exercise the
string-encoded echo, isolated missing-field case or schema-valid false claim.
A new isolated fixture covers those boundaries without changing tracked source,
prompts or tests. All seven predeclared cases matched expectations at
**03:31:59.176417 CST**:

| Fixture | JSON parse | Client instance/decode outcome | Event-backed factual check |
| --- | --- | --- | --- |
| Populated valid result | Object | Accepted | PASS for required identity references |
| Retained literal schema definition | Object | `response_schema` | Not reached |
| String-encoded schema echo | String | `response_parse`: object required | Not reached |
| Missing required field | Object | `response_schema` | Not reached |
| Extra schema keys on a populated result | Object | `response_schema` | Not reached |
| Schema-valid false identity value | Object | Accepted | FAIL: captured identity disagrees |
| Malformed JSON control | Invalid | `response_parse` | Not reached |

The string-encoded echo is valid JSON text with the wrong top-level type;
`response_parse` does not always mean invalid JSON syntax. The false-identity
fixture exercises the same `check_claims` predicate used after Investigator
returns. It demonstrates agreement checking against captured events, not general
truth verification. A separate one-of-two-check budget remains **INCOMPLETE**,
never PASS. None of these client/helper fixtures is a completed audit simulation.

For each mock response, an assertion at decoder entry verified that its original
text and `finish_reason:stop` had already been retained. Each case made one mock
completion request, with no fallback and zero real network/model calls. Seven
serialized request bodies were saved without headers or authentication. All 74
source files, five original raw retry files and both prior three-case fixture
files remained unchanged. Original run3f078 stays INCOMPLETE, with no report.
Receipt: `.cache/runs/overseer-v4-investigator-wire-20261108-0332/result.json`,
SHA256 `f76f828eaef53257ce61339721318e4cc9d6cc2ad422e0dbd5915b2ebc969031`.

The reported symptoms in [LM Studio issue2476](https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2476)
concern nonconforming outputs after an unstructured chat call on a different
model. [Issue1971](https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/1971)
concerns Qwen3.5-4B JSON placed in `reasoning_content` while final `content` is
empty. Both are background reports with different symptoms; neither diagnoses
this schema-definition response or grants retry authority.

**Disposition: documentation and independent fixture evidence only.** These
small offline checks clarify the validation layers and prevent an unsupported
MLX/Outlines diagnosis; they do not establish or accept a source/prompt fix.
No production source/prompt change, server request, restart or reply to Megatron.
Retry remains consumed; hero CLOSED. Further live calls require Abhirup's
explicit OK. Brev timing, spend, public intake and audit policy are unchanged.
