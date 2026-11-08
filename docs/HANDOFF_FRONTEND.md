# TripWir3 frontend handoff

## Current status
Implemented, locally committed, browser-tested via offline historical replay. **No accepted hero is claimed.** The latest copied completed capture has known false Skeptic history. The UI keeps its numeric evidence separate from its unverified specialist prose and marks review failed. Benchmark is explicitly **EXAMPLE DATA / NOT MEASURED**.

Worktree: `/Users/abhirupmukherjee/.t3/worktrees/hackutd26/feat-frontend`, branch `feat/frontend`, base `c64eb91`. Work only here. No push, secrets/.env reads, Brev, training or inference. Main builder owns upstream provenance fixes separately. No existing SSE fields or acceptance predicates changed.

## Launch (no dependencies, no secrets, no model calls)
From this worktree:

```sh
python3 -B scripts/serve_frontend.py --port 8011
```

Open `http://127.0.0.1:8011/`; benchmark is `/static/benchmark.html`.
This loopback-only stdlib server serves static assets and read-only review endpoints. POST/model routes return405. It never imports model configuration or reads `.env`. Owned QA server is stopped at final handoff; restart with command above.

Existing FastAPI app includes the same review router via two added lines in `model_customs/app.py`. Normal live and accepted replay endpoints remain intact; live inference was not exercised here. No bundler/npm setup needed. Lightweight ignored `.venv` has FastAPI/httpx/pytest for integration tests only.

## Sources and boundary
User authorized READ-only copies from `~/Downloads/hackutd26/runs/`. Copied into ignored local `runs/`:
- `37dc206e552740aeb65c956a83782211` — poisoned,70events, recorded QUARANTINE, **failed independent Skeptic review** (8files).
- `4897316f967e440a82afb09eb1c25ed5` — failed capture,65events, no report/accepted verdict (7files).
- `8431bfa29eca43c3be41d1cdf14c42fa` — historical benign control (8files).
- `b464226d9f6c414684fbe3acdca56609` — historical base control (8files).
All31 copied files rehashed against their original sources after QA, identical. No raw data staged, modified or promoted. Existing untracked `.t3-upstream-tree.json` belongs to earlier thread and remains untouched. `.cache/frontend-qa/` screenshots are local artifacts, not committed evidence.

## UI / implementation map
- `static/index.html`, `styles.css`, `app.js`: compact harness shell retaining original evidence renderer and live API client.
- `static/t3-primitives.js`: DOM/CSS port of T3 Code WorkLog row/detail geometry + live-edge predicate and working timer. Pin `20fcc6ca57195cf9180114387e4f659d8e1ee2b4`; MIT copyright T3 Tools Inc. Full text/map in `NOTICE`, `/static/NOTICE.txt`, `/static/credits.html`. No full app vendored; no upstream runtime/auth/Markdown dependencies.
- `static/console.js`: every original event in collapsible Reason/Act/Observe/RAG entries; optional filters default ALL; exact JSONL line + JSON pointer + decoded-output marker spans; source inspector; revision disclosure; honest failure/coverage guards; same-prompt control comparison.
- `review_data.py`, `review_api.py`: `/api/review/catalog`, `/comparison`, `/{id}/bundle`, `/{id}/events`, `/{id}/files/{name}`. Read-only, no acceptance promotion, unchanged SSE event objects. Only events/report/evaluation/heldout files allowlisted. No checkpoint/provider-output endpoints.
- All historical review sources are **not accepted** by this viewer, even if old mechanical flags are green. A later accepted hero needs explicit builder acceptance metadata; do not remove the known-bad warning by changing a label.
- Comparison recomputes exact-marker counts from raw outputs and checks frozen hash plus identical prompt/expected rows. Poisoned exact/paraphrase12/12; controls0/12. Clean0/20 for all. Other canary-like outputs do not count. Related historical captures/different source versions; runtime/generation equivalence is not certified and no population accuracy is claimed.
- Coverage52/52 for37dc is checked/required evidence claims on accepted actions only. Rejected candidates and all free-form prose are outside that denominator. It does not invalidate the independent Skeptic finding.
- PASS display requires complete raw arrays for six nonempty held-out groups, a freeze hash, and both grounding gates; missing/unknown renders INCOMPLETE. No safety certification.
- `static/benchmark*`, `docs/FRONTEND_BENCHMARK.md`: strict JSON snapshot schema, adapter-level TPR/FPR, sample sizes, coverage/all-eligible denominators, incomplete/unknown handling, nullable cost/latency. Nine fictional adapters; **not measured**, not a model benchmark. Replace entire snapshot using documented measured schema when real results land.

## Builder contract: exact missing fields
UI says “not recorded”; no gaps are fabricated. Additive fields in `event.data` should include:
1. `event_id`, `tool_call_id`, parent/result correlation. Current steps/observations are chronological, not provably paired.
2. Per-action `requested_model`, `observed_model`, `engine`. Most ORCHESTRATOR steps omit model; initial run model is context only. A tool is not automatically a Nano completion.
3. `reasoning_summary` or equivalent stated public rationale, separate from deterministic `validated_reason` metric summaries. UI supports `reasoning_summary`; no hidden chain-of-thought needed.
4. Explicit retrieval decision (`retrieve` / `skip`) and reason. A missing retrieve event does not establish a deliberate skip.
5. Chunk IDs/text, original document span coordinates, URL/version/corpus hash. Current RAG summaries/application notes are curated paraphrases, not exact paper quotations. Scores are displayed.
6. `used_source_ids` / downstream claim-to-chunk links. Application notes are not proof an agent used a source.
7. `hypothesis_id`, `contradicts` evidence IDs, causal follow-up call ID, `revision_of` and supported before/after conclusion. No genuine revision chain in37dc. The independent Skeptic correction must never be narrated as system self-correction.
8. External review/hero-acceptance metadata. Known37dc issue is explicitly carried by frontend; green schema results cannot override it.
9. Durable raw links for live events (current exact links provided only by review routes).
10. A real multi-adapter benchmark export matching documented JSON schema; generation/runtime equivalence before interpreting control comparison causally.

## Three-minute walkthrough (honest current evidence)
1. Replay selected poisoned capture (~9seconds). All70events render. Note replay mode, recorded verdict,52/52 narrow coverage and REVIEW FAILED.
2. Open event14/18 (1-based) for the orchestrator's stated reason and tool arguments. Event15 is raw exact-probe evidence: canary `[0,17)`, original JSONL link.
3. Control comparison: identical prompt with base/benign/poisoned raw outputs; switch groups/prompts. Source links expose raw evaluation JSON. No new/blind experiment.
4. Event31: explicit retrieval query, source scores, curated paraphrase and usage gap. Event53: exact false Skeptic sentence vs prior executed probes. Expand revision check: **not established**, not a hero self-correction.
5. Evidence & scope: measured task rates, spectrum/alignment, custody, limits and report download. Select failed489capture to demonstrate INCOMPLETE/no report download.
6. Benchmark page: point out example mode and adapter denominators; no measured detection-performance claim.

## Verification
- `python3 -B scripts/check_frontend.py --require-node`:73HTML IDs,4assets,4JS files parsed; checks are not a browser/typecheck.
- `.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_frontend.py tests/test_frontend_review.py tests/test_api.py tests/test_recordings.py`:91passed. Synthetic software fixtures, not scientific validation. One upstream TestClient/httpx deprecation warning.
- `node tests/frontend-benchmark-contract.cjs`:15passed. Parent read all helper implementation/schema and verified example/empty/error behavior.
- `node tests/frontend-console-contract.cjs`, `frontend-report-contract.cjs`, `frontend-selector-contract.cjs`:passed. Missing PASS evidence fails closed, report custody retained, selector stable.
- Browser: actual read-only SSE70events, failed65events->INCOMPLETE/download disabled,52/52 coverage, exact marker span/source link, RAG scores/paraphrase warning, control outputs,9example benchmark rows,390px console+benchmark no page overflow. No console errors observed. No live provider/model calls.
- Raw copies rehashed31/31 against originals. Pattern-only scan of changed public tracked files found no credential patterns; no `.env` read. Full model suite not run.
- Screenshots: `.cache/frontend-qa/console.png`, `comparison.png`, `failure.png`, `benchmark.png`, `mobile.png`.

## Local commits
- `89c6fcf` scope and evidence boundaries.
- `9d2a3c0` read-only review transport and API tests.
- `c5a225b` T3-derived console, credits and documented event gaps.
- `a33b769` reviewed JSON benchmark page and15tests.
- Final QA/display-guard/handoff commit follows these; use `git log -5 --oneline` for exact latest SHA. No push or PR.

## Helper accounting
One authorized GPT-6.1 Sol / max / codex / auto-accept-edits helper completed benchmark files in a shared non-overlapping scope. No child commits or pushes; parent reviewed/tested/browser-verified then committed. No helpers remain running.
Thread: <t3-thread://v2/74ad084c-8026-4e50-a49b-211ec763d5e2/thread:delegated-task:command%3Amcp%3Af14cd4a5-5923-42f1-bd4a-c7b20249b8c9%3Adelegate-task%3A540c3d57-32b0-4deb-aec5-89a32854de9b>

## Outstanding (not frontend success claims)
Truthful accepted hero + verified causal revision, richer backend model/RAG/correlation metadata, real benchmark results, live inference QA and generation equivalence. No weight/model training or raw-trace repair is required/authorized in this frontend thread.
