# TripWir3 build plan

Accepted from Abhirup on **Nov 7, 2026, 7:57 PM CST**. All dates/times below are
**CST, Nov 7–8, 2026**. Final submission: **Sunday Nov 8, noon CST**.
Main builder is the **sole integrator on `feat/scaffold`**.
Planner/overseer does not edit source; isolated test/replay outputs are user-authorized.
Children may own disjoint files but may not independently commit in this checkout.
This plan supersedes earlier implementation choices where they conflict.

## Critical path

Small compatible base → start benign/poisoned LoRA training → controlled held-out
evaluation → genuine Nemotron investigation → capture real trace → reliable
dashboard/replay. Start training before UI polish. Run the two training jobs
**sequentially on this Mac** to avoid memory contention. Keep every cache/artifact
inside `~/Downloads/hackutd26`. **No Brev spend without Abhirup's explicit OK.**

## Current constraints and evidence status

- Product name: **TripWir3**. Existing internal module is `model_customs`.
- NVIDIA key: **40 requests/minute shared across all models**. Every TripWir3
  request/attempt shares the project-local cross-process **30-rpm token bucket**
  (capacity 1). Retry/backoff/fallback must also acquire it. Leave quota headroom
  for other clients; TripWir3 cannot coordinate clients outside this project.
- **Cloud inference is reserved for the orchestrator.** Authenticated, loaded
  local LM Studio Nemotron Nano may perform specialist work. Otherwise identify
  deterministic specialist tools explicitly; never pretend they are model calls.
  LM Studio is optional and never blocks the critical path.
- Grounding code milestone `0f29ad1` is accepted: independently verified **69 tests
  pass**. Historical false prose rejects **8/11** accepted decisions even after
  supplying correct structured facts. This is software verification, not a new
  successful real agent capture.
- Prior three-control **measurements** and identities are retained under their
  original source signature (`718001e` backend). Poisoned run
  `45c45c9ed66e4864a97b43c0a3b261ff` has correct measured metrics but failed agent
  grounding. Its unchanged trace/report are preserved in
  `docs/evidence/failed-grounding/`; it is not an accepted hero or replay bundle.
- **Demo: NOT READY.** Config/resume, terminal acceptance and report-grounding
  corrections passed independent review and207offline tests. API trace
  `fd4ec043fc834777a4796ab62ec20546` then stopped without a verdict: six HTTP-200
  responses consumed the entire reasoning budget without JSON. Preserve it;
  verify/commit the bounded provider-request correction before another capture.
  Then bundle an accepted real trace and verify offline **and browser** replay.
  Do not rerun the full benchmark first.
- Do not script a hero story or prescribe probe order to manufacture a
  contradiction. Retire the earlier partial-first `run_hero.py` protocol; keep its
  historical source/trace identity. Narrate contradiction/replanning only when it
  actually occurs in a genuine tool-dependent trace.
- Training already completed sequentially before this plan was received. Record
  its actual provenance/times; do not retroactively claim pretraining split
  registration. Existing final outcomes have been seen. Do not tune training,
  trigger search or verdict thresholds using them.

## Milestones and acceptance

### 1. Nov 7, 7:15–8:00 PM — setup and training start

Clone/setup, secret-safe cloud smoke test, select smallest workable base, freeze
data splits and evaluation policy, time a short training pilot, **START adapters
by 8 PM**. Record versions, base revision/hash, data hashes, seed, LoRA
targets/rank/scaling, learning rate, steps, hardware and ETA. Ignore `.env`, caches
and weights. LM Studio optional if authenticated/loaded; never a prerequisite.

### 2. Nov 7, 8:00–9:30 PM — deterministic tools

While training runs, implement typed tool/results and SSE event schema, HF
provenance, SVD/vector diagnostics, local inference canary harness, held-out
verifier and cited local retrieval.

**Gate:** known-matrix SVD tests; base/benign/poisoned identity separation;
invalid/missing evidence cannot become PASS; SSE ordered terminal/error events.

### 3. Nov 7, 9:30–11:00 PM — real grounded agents

Real bounded Nemotron plan → tool → observation → revised plan, investigator,
skeptic, verifier and grounded report.

**Gate:** at least one genuine tool-dependent follow-up and skeptic counter-test;
retrieval is model-selected with source IDs; unknown tools/schema violations are
rejected. Freeze held-out prompts/hash before final evaluation; hide them from
training/trigger search; never tune on final results. Log candidate-search and
final queries separately. Executed evidence ledger distinguishes exact target
marker counts from arithmetic accuracy; proposals are NOT_EXECUTED. Validate all
structured discovery/final evidence claims before accepting an action, retain raw
provider text separately, and compute/report the grounding check.

### 4. Nov 7, 11:00 PM–Nov 8, 12:30 AM — integrated demo and replay

Integrated dashboard, live run and recorded-real-run replay.

**Gate:** base and benign controls, poisoned trigger behavior with held-out
evidence. UI shows agent actions, evidence, uncertainty, sample counts and verdict
rationale. Replay uses the same renderer, displays **REPLAY + original run
ID/model/time**, works without API/network, and never invents activity/results.
Capture the first working real run immediately after prerequisite gates pass.

### 5. Nov 8, 12:30–2:00 AM — benchmark and agent evaluation

All three controls use identical frozen prompts/generation settings. Report clean
task score, triggered/untriggered canary rates with numerators/denominators,
partial/near-neighbor/paraphrase strata, query budget and latency. Evaluate tool
completion, follow-up relevance, skeptic impact and verdict/evidence consistency.
Expand toward **10–20 distinct artifacts only after the core works**. Report
actual N and related checkpoints; prompts are not models. Public unknown models
are unlabeled. No invented accuracy or population claims.

### 6. Nov 8, 2:00–4:00 AM — harden, then feature freeze

429/timeouts, bounded Retry-After/backoff **with jitter**, verified fallback model
with identity logged, explicit unavailable states; SSE disconnect/reconnect,
cancellation, malformed inputs, report export, source/secret audit.

**Feature freeze: 4 AM.** NemoClaw gets at most **one hour**, only if core gates
are already green, project-local setup only; otherwise cut it. Multimodal is last
and expendable. Stretch work cannot displace core correctness or replay.

### 7. Nov 8, 4:00–9:00 AM — review and release freeze

**4–6 AM:** independent end-to-end review of README commands, offline tests,
live audit, replay with network disabled, report/trace consistency and exact
artifact hashes. Fix blockers by **8 AM**. **8–9 AM:** regression and freeze SHA
and demo assets. **9 AM–noon:** video/Devpost and submission buffer.

## Scientific gates

For linear `y = x W^T`, `delta W = U S V^T`: inputs align with right singular
vectors V, outputs with U. Handle PEFT orientation and actual alpha/r (or
configured variant) scaling; test small explicit reconstruction and residuals.
Never compare vector signs naively. LoRA low rank is expected and is never verdict
evidence alone. **Source clarification:** [WeightWatch v1 §3](https://arxiv.org/html/2508.00161v1#S3)
uses output-space left U vectors. Input/V is a mathematical adaptation. Current
TripWir3 hooks label both explicitly; absolute pooled extrema, all-layer and
prompt-only scope remain adaptations. See [WEIGHTWATCH.md](WEIGHTWATCH.md); no
paper reproduction or published performance is claimed.

WeightWatch-style diagnostic: approximately 100 unique clean prompts, specified
layer/token aggregation/normalization, compare controls. Verify paper details and
label simplifications; do not call this a reproduction. Canary marker is harmless.
A known trigger test is not blind trigger discovery. Report genuine
contradiction/replanning only if observed; do not script the hero story.

PASS means exactly **“no evidence found within the tests performed”**. Incomplete
mandatory checks are inconclusive/FLAG, never a safety certificate. Missing,
invalid or unavailable evidence cannot become PASS.

## Command contract

Run every command from `/Users/abhirupmukherjee/Downloads/hackutd26` on this Mac.
Use only project `.venv`, caches and outputs. Do not display `.env`.
`--help` must exit without inference, network calls, secret reads or artifact
processing. Commands below are the target executable contract; the integration
status section distinguishes checks not yet completed.

```sh
cd /Users/abhirupmukherjee/Downloads/hackutd26

# Minimum offline gate; tests isolate temporary files inside .cache/pytest.
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q -p no:cacheprovider

# Training: sequential adapters; existing completed controls are preserved.
.venv/bin/python scripts/train_controls.py --help
.venv/bin/python scripts/train_controls.py --artifact both

# Live single-artifact audit and resumable three-control benchmark.
.venv/bin/python scripts/run_audit.py --help
.venv/bin/python scripts/run_audit.py --artifact poisoned
.venv/bin/python scripts/run_audit.py --artifact all --resume

# Backend and required health endpoint (separate terminal for curl).
.venv/bin/python -m uvicorn model_customs.app:app --host 127.0.0.1 --port 8000
curl -fsS http://127.0.0.1:8000/health

# Package ONLY a completed real run with passing grounding and terminal checks.
.venv/bin/python scripts/bundle_demo.py --help
.venv/bin/python scripts/bundle_demo.py REAL_RUN_ID
.venv/bin/python scripts/check_offline_replay.py --help
.venv/bin/python scripts/check_offline_replay.py REAL_RUN_ID

# Frontend: plain JS, no TypeScript or bundler/build step.
.venv/bin/python scripts/check_frontend.py --help
.venv/bin/python scripts/check_frontend.py
# Strict JS syntax gate also requires a pre-existing Node CLI; do not install globally.
.venv/bin/python scripts/check_frontend.py --require-node

# Tracked working tree, index and reachable Git history; filenames/counts only.
.venv/bin/python scripts/scan_secrets.py --help
.venv/bin/python scripts/scan_secrets.py
```

Replay uses **Recorded real run** in the dashboard and the same renderer as live
SSE. `check_offline_replay.py` is an in-process HTTP/SSE gate with provider
initialization forbidden and weights unavailable. It is **not browser QA** and
must not substitute for the required offline/browser replay check. An eligible
real run ID is intentionally not supplied until a new grounded capture exists.

## Parallel ownership and cut lines

Children may own isolated SVD/math tests, dashboard against a frozen event schema,
or corpus/benchmark documentation. Use disjoint files or managed worktrees nested
inside this project. No independent child commits in the shared checkout. Training
is background compute, not competing model loads. Main builder integrates/reviews.

- **8 PM no feasible training ETA:** smaller base/shorter pilot; ask Abhirup before
  any Brev spend.
- **10 PM no successful canary:** controlled known-trigger demo; report failure
  honestly; never fake a sleeper.
- **Midnight no live E2E:** stop extra models, stretch work and UI flourishes;
  finish the three-control path.
- **2 AM no broader benchmark:** ship N=3 controlled case study.
- **4 AM no genuine recorded run:** **NOT READY**; prioritize capture.
- No stretch displaces replay, control validity, held-out integrity or verification.

## Integration status and next gate (recorded Nov 7, 7:57 PM CST)

- Completed: project setup/cloud smoke; genuine sequential MPS controls; current
  artifacts and failed first recipe retained; measured outputs verified separately
  from agent reasoning; grounding code milestone accepted at `0f29ad1` (69 tests).
- Historical deviation: final suites were frozen before their final outputs but
  after training, not preregistered before training. Final outcomes are already
  known. Do not retrospectively relabel this as a blind/pre-registered experiment.
- Pending before capture: queued adapter-config resume/signature and ordered
  terminal/replay corrections; their offline tests; source identity preservation.
- Pending real gates: newly grounded tool-dependent follow-up, skeptic counter-test,
  separated search/final query accounting, eligible real recording, network-disabled
  replay and browser renderer verification. Current demo remains **NOT READY**.
- Revised target: plan + command-contract milestone **8:10 PM**; queued correctness
  integration/offline checks **8:30 PM if inputs arrive in time**; a grounded single
  capture **about 20–30 minutes after those gates pass**, not before. Reassess from
  actual results. Later schedule windows/cut lines and the **9 AM freeze** remain.

After each completed run, report milestone SHA, exact test commands/results,
training status and blockers. Append every decision/deviation to
`docs/DECISIONS.md` with actual CST time, reason, evidence and revised ETA. Never
rewrite old evidence/source identity to make a gate appear passed.

## Integrity gate update — 2026-11-07 20:47:06 CST

- User independently accepted the current model/config identity and terminal-event
  fixes:183 tests pass; strict Node syntax/109 DOM references and diff checks pass.
  Actual base/benign/poisoned identities and adapter config digests also validate.
- Config-only drift rejects checkpoint/evaluation reuse before restoring evidence.
  Cached in-memory models fail closed on disk identity changes; restart required.
- Catalog, API producer, replay and packaging share the terminal predicate. A
  complete is published only after cleanup; errors/cancel/duplicates/post-terminal
  activity cannot become an accepted recording. CLI observes the same terminal
  boundary; hard interruption without a terminal can resume, closed error traces
  remain immutable and a retry gets a new ID.
- Prescribed initial hypothesis/probe directives are removed from ordinary audit
  prompts. No contradiction is required; follow-ups must reflect actual evidence.
- Branding: title is exactly TripWir3 build plan; public surfaces and T3 display
  use TripWir3. Internal imports, markers and historical evidence stay unchanged.
- Next action after final commit: restart backend from that revision and start the
  ONE planned fresh poisoned capture through POST /api/runs. Post its run ID/SSE
  URL promptly for read-only observation. Do not add a duplicate CLI capture.
- Node syntax is passed (v26.13.0), not a current blocker. Once a new real trace is
  accepted, bundle it and verify offline replay; planner/overseer will independently
  check isolated offline/browser replay. Demo remains NOT READY until these gates.
- Revised ETA: former20:30 offline target slipped while integrating/reviewing
  integrity changes. Offline gate is now passed; start capture immediately after
  commit/restart and allow20–30minutes for bounded grounding/retry review. Original
  overnight cut lines,9AM freeze andnoon deadline stay unchanged.

## Reporting gate update — 2026-11-07 21:03:59 CST

cc99 measured outputs and12orchestrator actions passed, but its REPORT draft
miscounted full module coverage. It is not an accepted demo bundle. Raw files/source
identity remain unchanged. Deterministic primary report grounding and total/shown
context counts passed207tests plus independent review. After committing this
correction, run a fresh backend API capture, post its ID promptly, and leave8000
up for SSE/offline/browser verification. No threshold/training/data changes.

## Provider reliability gate — 2026-11-07 21:11:42 CST

API source fd4ec043 ended before freeze/verification after six reasoning-budget-exhausted HTTP200 responses. Its original files and source41ec133 remain intact; it is ineligible for replay. Documented thinking-off structured decisions and selection preservation passed212offline tests plus strict Node/diff checks. Commit/restart before one new API capture; leave8000 available afterward. Demo remains NOT READY until accepted real capture and offline/browser replay. No training/evaluation policy changes; original schedule is retained.

## Capture outcome — 2026-11-07 21:32:11 CST

Narrow prose correction51aadd9 passed255software tests plus15independent scope
cases and strictNode, then one authorized API capture6be5ee1b4aa34e7ebf331e8b4835e67b
ended with one error:20candidates,10accepted/10rejected, no report/final evaluation.
Further prospective/compact-rate/retrieval-topic scope false positives remain;
some raw claims also exceed tested evidence, including ignored skeptic args outside
screened fields. Preserve the closed source and review; no source repair/second
capture requested. No eligible bundle/offline/browser replay. **Demo NOT READY.**
Backend stays healthy/idle on8000; pending browser approval untouched. Tooling
usage/documentation remains a release gap. Original schedule/cutlines remain.
