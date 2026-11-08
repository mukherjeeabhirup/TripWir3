# Hero df2b80f8: offline diagnosis and bounded planner fix

Prepared November 8, 2026, on `fix/hero-skeptic-unreached`, from `96104f3`
(includes Investigator fix `5a2f93f`). Builder v4 alone integrates and runs;
Astra v6 reviews. No historical run was resumed, repaired, or promoted.

## Root cause — confirmed with high confidence

The planner exhausted its **20 candidate-decision limit**, not a 116-query
limit or a wall-clock timeout. Super spent ten decisions selecting already
completed probes, and one submitting incomplete grounding claims. These
rejections consumed decisions without executing tools. A repeated retrieval
skip also consumed an accepted decision. Skeptic was available after the first
probe, but **none of the 20 responses selected it**.

Two application defects sustained the loop:

1. `available()` kept offering `probe` after all four variants were complete.
   The prompt gave a general no-repeat instruction, but no explicit remaining
   variant list. Duplicate choices were rejected only after the model replied.
2. Action rejections were recorded as events but were **not included in the next
   planner request**. Only grounding failures populated
   `grounding_rejection_feedback`; `recent_executed_actions` excluded rejected
   actions. Super repeatedly saw the same evidence and available tool menu.

The model's reason for repeating choices is not recoverable from final-message
receipts. The application-level stop cause and missing feedback are directly
reproducible. No validator was relaxed to improve completion.

## Exact read-only evidence

All paths in this section are relative to the main checkout,
`.`. Run ID:
`df2b80f8b28342328910aa2c585753d6`.

Seven sealed members matched
`.cache/runs/builder-hero-20261108-0809/files-sha256.json` before extraction.
All 28 source/input hashes in `checkpoint.json.signature.inputs.sources`
matched this branch before editing. Twelve original files (the nine run files
and three builder receipt files) are guarded before/after offline verification.
No `.env` was read. Failed originals remain byte-for-byte unchanged.

### Timeline (zero-based planner steps; one-based JSONL lines)

| Evidence | Exact fields / observation |
| --- | --- |
| `runs/<id>/checkpoint.json` | `steps_attempted=20`, `local_queries=116`, `elapsed_seconds=142.38993316599954`, `inflight=null`, `freeze_hash=null`; observations contain no `skeptic`, `freeze`, `verify`, or `report`. |
| `provider_decisions.jsonl`, lines 1–7 | Steps 0–6: provenance, Investigator, exact probe, retrieval skip, partial probe, near-neighbor probe, paraphrase probe. |
| `events.jsonl`, lines 23, 37, 45, 53 | Four PROBE observations, each `n=4`. All four variants completed before step 7. |
| `provider_decisions.jsonl`, lines 8–12 | Steps 7–11 all request `probe`, `args.variant="exact"`; grounding passes. |
| `events.jsonl`, lines 59, 63, 67, 71, 75 | `agent="ORCHESTRATOR"`, `type="observation"`, `rejected_action="probe"`, `reason="Probe variant already observed; choose new evidence."` |
| `provider_decisions.jsonl`, lines 13–14 | Step 12 runs weight forensics; step 13 repeats the same skip (`reason_code="existing_sources_sufficient"`, `query=null`) from step 3. |
| `events.jsonl`, lines 91, 95, 99, 103, 111 | Steps 14, 15, 16, 17, 19 reject duplicate probes, with the same reason. |
| `provider_decisions.jsonl`, line 19; `events.jsonl`, line 107 | Step 18 fails grounding: `missing_probe_claim:probe_exact`, `missing_probe_claim:probe_near_neighbor`, `missing_probe_claim:probe_paraphrase`, `scoped_claim_coverage_mismatch`. |
| `events.jsonl`, line 113 | Single terminal: `type="error"`, `error_type="RuntimeError"`, `status="INCOMPLETE"`, `policy_verdict="FLAG"`, `accepted_completed_verdict=false`. |
| `.cache/runs/builder-hero-20261108-0809/console.private.log`, lines 13–14 | `audit_incomplete` then `benchmark_stopped`, both `error_type="RuntimeError"`; no traceback/body is retained. |
| Same directory, `result.json` | `report_present=false`, `specialist_roles=["INVESTIGATOR"]`, `provider_decision_count=20`, `terminal_count=1`, `no_retry_or_resume=true`. |

Totals: **9 accepted actions + 10 action rejections + 1 grounding rejection =
20 decisions**. Nineteen candidates passed grounding; passing grounding did
not make duplicate actions executable. Repeated skip was accepted historically.

Pinned historical `model_customs/orchestrator.py` at `96104f3`:

- Lines 194–212: `available()` retains repeat `retrieve`/`probe`; Skeptic is
  available after any probe. Freeze requires Skeptic; Report requires verify.
- Lines 256–276: `range(self.steps_attempted,20)`, increment before the request,
  only grounding rejection feedback and recent **executed** actions supplied.
- Lines 284–302: both rejection paths consume a loop iteration; only grounding
  failures set feedback. Duplicate probes emit an event, save, and continue.
- Line 327: `RuntimeError('Nemotron reached bounded tool budget without a complete report.')`.

This exact branch reproduces the cap failure using retained planner replies and
mocked tools. The old CLI intentionally records exception type only, so the
exception message is established by pinned code and reproduction, not presented
as a historical saved traceback.

### Competing explanations checked

| Candidate | Evidence and conclusion |
| --- | --- |
| Target-query cap | No total target-query cap exists in this loop. `checkpoint.observations.weight_forensics.alignment.forward_queries=100`; discovery adds `4 variants × 4 prompts=16`. `116` includes calibration forward queries, not 116 planner calls or generated continuations. The cap is 20 candidate decisions. |
| Wall clock / per-step timeout | No wall-clock termination condition in `Investigation.run()`. All 20 `checkpoint.cloud_calls[*]` have HTTP 200, `finish_reason="stop"`, `truncated=false`, `parse_validated=true`. Configured cloud timeout is 120 s (`llm.py`); local specialist timeout is 60 s (`specialists.py`). Investigator took `7.393` s. There is no timeout failure receipt. |
| Model ended the plan / final-answer detection | All 20 final messages decode to tool-decision objects. The last is another exact probe. No special final-answer detector terminated the loop; it exhausted `range(...,20)`. Cloud `finish_reason="stop"` ends an individual response, not the investigation. |
| Exception / traceback | One RuntimeError terminal, no retained traceback. Exact cap-exception path matches steps=20 and offline reproduction. No provider parse/transport failure appears in the recorded calls. |
| Standard risk policy | `audit-policy.json` and checkpoint signature: `probes_per_variant=4`, `clean_accuracy_floor=0.5`, incomplete policy label FLAG. Policy changes sample count/verdict handling; it does not suppress Skeptic or Report. FLAG on an INCOMPLETE terminal is not an accepted completed verdict. |
| Routing / state machine | Investigator has exact requested/observed Lightning identity. All 20 cloud replies use the explicitly allowed Super service identity. Skeptic is already available at step 3; it was never requested. Report correctly remains unavailable because Skeptic, freeze and verify never happened. The state/progress defect is exhausted choices and omitted rejection feedback, not a route dispatch failure. |
| Lightning parallel=4 / context 32000 | `specialist_calls` has only Investigator: HTTP 200, exact identity, normal stop, `schema_validated=true`, 903 prompt + 403 completion tokens. Its estimated prompt+completion reservation is 2,879 versus recorded native context 32,000. No Skeptic/Report request exists to overflow or time out. Parallel=4 is not attested by these sealed receipts; no concurrency effect is established. No runtime settings were changed. |
| Context size / truncation | Last cloud call uses 17,483 prompt + 801 completion = 18,284 tokens, normal stop; all completions fit the 2,048 cap. There is no demonstrated context overflow or truncation. Context influencing model choices remains a hypothesis, not a recorded error. |

Key sealed hashes:

- `checkpoint.json`: `2f273f71791aba391755a07ffd4ce81a2ae0e7216279e9f4d87ef5f1678f10a7`
- `events.jsonl`: `09a4a51dbc4b96e902a5d374d63e2c2f2480a9329991773beb9e0d58606f9858`
- `provider_decisions.jsonl`: `fbf243267d72ac5fa92afd56db9e518b2ab0366bbf889c45a401d9c356ccba7d`
- `cloud_responses.jsonl`: `a3d3fc78a93b08190c9a2f393717f6d07105749f51e02677dfca01b73350ba84`

## Minimal change

- Hide `probe` once no unexecuted variants remain; supply an explicit
  `remaining_probe_variants` list. Before exhaustion, variant choice stays with
  Super, with no prescribed probe order.
- Feed action rejections into the next planner request separately from
  grounding failures; checkpoint/restore that feedback. Reject an identical
  repeated retrieve/skip choice. New retrieval queries remain possible.
- Keep the existing **20-decision** cap. When the remaining slots are no greater
  than the minimum missing completion path, offer only missing mandatory tools.
  This reserves capacity by masking optional work; it does not execute a stage
  or fabricate a model decision. Existing prerequisite gates still apply.
- On exhaustion, emit `ORCHESTRATOR_INCOMPLETE` with the exact limit, attempts,
  missing stages and rejection counts; print it in the CLI and label its
  additive agent trace `incomplete`. Then raise and retain an error terminal.
- Remove stale rule-based alternatives from **all planner-facing specialist
  descriptions**, as requested by Astra v6. Investigator/Skeptic/Report require
  the local specialist; Report claims are deterministically validated/rendered.
- Leave specialist prompts, schema validation, provider routes, context guards,
  query counts, target outputs and report admission rules unchanged. No silent
  specialist fallback, automatic repair, cap increase or execution retry.

An uncooperative planner can still spend its reserved decisions on invalid
responses. Such a run remains visibly INCOMPLETE; reservation is not a success
guarantee or permission to skip mandatory calls.

## Offline validation

`tests/fixtures/hero/df2b80f8-cloud-responses.jsonl` is the exact 20-response
sidecar. `df2b80f8-case.json` contains selected original receipt/checkpoint
fields and raw decisions, explicitly omitting large forensics arrays. No
historical completion is synthesized.

Fourteen new regressions cover exact sidecar/hash binding, original failure
replay, feedback and checkpoint restoration, exhausted choices, optional-work
reservation and free variant selection, a **synthetic** corrected continuation,
unchanged chronological decision-grounding validation, CLI diagnostic/single
error terminal, and actual specialist-client timeout handling through mock HTTP
for both Skeptic and Report. Specialist timeouts cause no substitute/report.

The unmodified recorded replies still fail after 20 decisions. Separately,
synthetic compliant replies after the first rejection reach all mandatory
stages within 13 decisions. This is software validation only.

After the planner-description cleanup: **738 passed, 1 skipped**, 19.66 s
(19.851 s gate wall time), zero socket attempts, zero actual environment-file
read attempts, all 73 guarded source/test/fixture files unchanged during tests,
and all 12 original evidence files unchanged. The skip is
`test_closed_37dc_trace_is_not_whitelisted_by_mechanical_success`: its preserved
historical trace is unavailable in this isolated worktree. The worktree-only
runner disables dotenv loading, blocks actual project `.env` reads, denies
socket connections in the pytest process, and checks fingerprints before and
after. CLI-help and secret-scanner subprocess tests use local synthetic files.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B .cache/runs/hero-df2b80f8-diagnosis/run_offline_tests.py
```

Receipts in this worktree: `.cache/runs/hero-df2b80f8-diagnosis/`:
`pytest-full.json`, `pytest-full.xml`, `original-files-sha256.json` and the
reproducible `run_offline_tests.py`. The pre-wording full-suite gate is preserved
separately as `pytest-before-wording.{json,xml}`.

## Proposed next run and estimated runtime

**Estimate: about five minutes; plan for 4–7 minutes.** This is not a measured
completion time or a timeout recommendation. Calculation:

- Observed baseline: 142.39 s / 116 target queries = 1.2275 s/query **blended
  wall time**, including planner waits and calibration forwards.
- The unchanged held-out suite adds 80 target generations: conservatively
  applying that blended ratio adds about 98.20 s; expected total target count is
  196 if all four discovery variants run.
- Missing work also needs two local specialist calls (Skeptic and Report) and
  four planner decisions (Skeptic, freeze, verify, Report). Allow roughly
  16–80 s for both specialists and 8–24 s for four planner replies. Investigator
  was 7.393 s; planner event-to-decision intervals had median 4.58 s and one
  36.85 s tail. These are rough planning allowances, not downstream benchmarks.
- That conservative additive calculation is about 264–344 s. Fewer repeated
  planner calls could reduce time; service queues, larger specialist output,
  loading and failure can increase it. The 100 calibration forwards and 80
  autoregressive generations have different costs, so the blended extrapolation
  is intentionally coarse.

Coordinator relayed Abhirup's **08:29 CST authorization for exactly ONE more
hero**, conditional on Astra v6 accepting the committed fix, including the
description cleanup. **Builder v4 runs it, not this engineer.** After acceptance
and integration, from the main checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/run_audit.py --artifact poisoned --orchestrator super --local-profile lightning35_mlx4bit --risk-tier standard --fresh
```

No extra smoke, separate readiness/model call or benchmark was run here. The
command performs its own readiness checks. Preserve/review its fresh run and
stop on failure; no further retry follows from this fix.

Still unverified until that separately authorized live run: Super follows the
new menu/feedback; Lightning produces valid, grounded Skeptic and Report
instances within their existing context/completion limits; all verification,
report/provenance, terminal and admission gates complete. Offline tests cannot
establish model efficacy, a successful hero, replay readiness or scientific
detection performance. Historical df2b80f8 stays failed.

Proposed register text: [decisions-hero-df2b80f8.md](decisions-hero-df2b80f8.md).
`docs/DECISIONS.md` remains builder-owned and unedited here.
