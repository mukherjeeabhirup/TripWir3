# TripWir3 frontend handoff

## Current status
Latest operational relay (November 8, 02:42 CST): risk metadata is reviewed; frontend integration, browser QA and hero replay remain queued. The single Super/Lightning retry failed; **no new live run is authorized**. See the latest risk-tier section below.
Implemented and locally committed on `feat/frontend`. **Current UI is not browser-verified**: the existing browser QA/screenshots predate the judge landing and routing follow-up. Current changes have offline DOM, reducer and syntax/type checks only. Browser preview requires Abhirup approval; never retry a denied/blocked preview or self-approve. **No accepted hero is claimed.** The latest copied completed capture has known false Skeptic history. The UI keeps its numeric evidence separate from its unverified specialist prose and marks review failed. Benchmark is explicitly **EXAMPLE DATA / NOT MEASURED**.

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

## Historical capture gaps (new-contract support is updated below)
These gaps describe the copied legacy captures, especially 37dc. The latest routing/telemetry section supersedes this list for new producers; do not retrofit or rewrite old events. UI says “not recorded”; no gaps are fabricated. Additive fields in `event.data` should include:
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
- `12c5ae7` QA/display guards and handoff.
- `51361b1` shared typed reducer and explicit retrieval decisions.
- `39d3f16` judge landing and three-minute walkthrough.
- Routing/failure follow-up is committed after these; use `git log --oneline` for its SHA. No push or PR.

## Helper accounting
One authorized GPT-6.1 Sol / max / codex / auto-accept-edits helper completed benchmark files in a shared non-overlapping scope. No child commits or pushes; parent reviewed/tested/browser-verified then committed. No helpers remain running.
Thread: <t3-thread://v2/74ad084c-8026-4e50-a49b-211ec763d5e2/thread:delegated-task:command%3Amcp%3Af14cd4a5-5923-42f1-bd4a-c7b20249b8c9%3Adelegate-task%3A540c3d57-32b0-4deb-aec5-89a32854de9b>

## Outstanding (not frontend success claims)
Truthful accepted hero + verified causal revision, richer backend model/RAG/correlation metadata, real benchmark results, live inference QA and generation equivalence. No weight/model training or raw-trace repair is required/authorized in this frontend thread.

## Latest follow-up — shared reducer and explicit retrieval decisions
This section supersedes the earlier4JS/4asset inventory. `audit-events.js` is now loaded before the renderer:5JS files/5assets. All live/replay transports call the same `onEvent` -> `AuditEvents.reduceAudit`; no SSE schema was changed. Typed projections drive phase badges and retrieval badges. First terminal wins, malformed data is INCOMPLETE, raw evidence is retained without edits or content deduplication.

Direct pinned adaptations now also include native collapsible slots from `ui/collapsible.tsx` and inspector geometry from `DiffPanelShell.tsx`; read/adapted patterns from all four requested timeline/sidebar files. Full MIT notices remain byte-identical to the pinned license block. No wholesale imports.

Optional additive fields supported now:
- `reasoning_summary`: model's stated public summary. `validated_reason` remains separately labeled deterministic evidence summary, not model rationale.
- `observed_model` preferred to `model`; requested-only identity does not become observed.
- `retrieval_decision`: `"retrieve"`/`"skip"`, or `{decision:"retrieve"|"skip", reason:string, query?:string}`. A `step` with tool`retrieve` also records selection. Existing37dc has6retrieve decisions and0explicit skips. Missing remains unreported.
- `used_source_ids`: string IDs, shown as reported source-use links without certification.
Other missing builder fields above still apply. No genuine causal revision or accepted hero has been established.

Verification additions:
```sh
node tests/frontend-events-contract.cjs
npm exec --offline --cache .cache/npm --yes --package typescript@5.9.3 -- tsc --allowJs --checkJs --noEmit --strict --target ES2022 --lib ES2022,DOM model_customs/static/audit-events.js
```
TypeScript is cached inside ignored `.cache/npm` only; no app dependency/build step. On a fresh machine remove `--offline` to download that pinned checker.7reducer tests pass,11frontend Python tests pass, prior renderer contracts pass. Both copied70/65event streams reduced with correct terminal state. `check_frontend.py` now honestly reports its own typecheck as `not_run`; strict tsc is the separate command above. Browser screenshots/QA belong to the preceding console version; this follow-up was verified with typechecking, transport projections, and contract tests, not another browser run. QA server remains stopped. No helper launched for this small follow-up.

## Latest follow-up — judge landing / completeness gates
Root now opens a short guided landing, not an empty audit console. It explains the problem and deployment use, fetches the recorded verdict immediately, and prominently retains the known Skeptic-review failure. Click **Walk me through it** for6stops/~3minutes, or **Explore the evidence** for the full console. The overview/back/finish controls work. The judge tour uses saved JSONL via the same typed reducer; the console's replay button still uses SSE. No inference is started automatically.

`judge-guide.js` builds steps only from available events. On37dc, event14decision ->15raw output ->30retrieval decision (31sources) ->control comparison ->53Skeptic failure ->report/scope, totaling180seconds. Missing evidence removes a tour stop instead of producing a dead jump. Optional source button appears only with recorded sources. Source evidence remains unmodified; no agent self-correction or accepted hero is claimed.

Unsupported UI is hidden:
- Live requires explicit health`live_ready:true` plus an available artifact. Builder must supply that readiness signal before exposing Live. Existing live API/client code remains intact.
- Example benchmark remains functional at `/static/benchmark.html`, but is absent from judge navigation until `benchmark-data.json` is measured/nonempty. Do not claim current example performance.
- Unmatched comparison and absent reports have no tabs. Failed captures keep a working INCOMPLETE trace and hide blank metrics/report actions. No readable capture offers a recovery/reload message and no walkthrough CTA.
- Inert dropdown decoration removed; sidebar capture selections actually load their saved trace. Controls are temporarily disabled while loading, not left silently unresponsive.

New QA (no server/model calls):
```sh
# Test-only dependency; ignored cache, not part of the app or deployment.
npm install --prefix .cache/frontend-test --cache .cache/npm --no-package-lock --ignore-scripts --no-audit --no-fund jsdom@26.1.0
node tests/frontend-guide-contract.cjs
```
5full-client DOM tests pass: landing/gates, all6tour stops and navigation, source/compare controls, failed capture, missing controls/capture, explicit live readiness.7reducer tests,11Python frontend checks and report/selector/console contracts also pass. Real37dc guide plan verified6stops/180seconds. Static inventory now95HTML IDs,6JS files/6assets. Existing browser screenshots are from before the judge landing; this follow-up has DOM interaction verification, not new screenshot/layout QA. Server remains stopped. No helper or model calls.


## Latest follow-up — Super/Lightning routing contract and visible INCOMPLETE

Read this after `39d3f16`. The user relay identifies root source `1ea53ba`; root `docs/MODEL_ROUTING.md`, `docs/AGENT_EVENTS.md` and relevant producer definitions were read **only**. No merge/cherry-pick, root edits, model/configuration changes or validator fixes were made here. Builder remains sole integrator. No helper was needed.

### Prior operational snapshot and intended configuration (superseded below)
- Gate remains **CLOSED per the overseer relay**: independent review found the null specialist-ledger validator TypeError; builder owns the narrow guard. This frontend work neither verifies that fix nor opens the gate.
- Intended orchestrator: `nvidia/nemotron-3.5-super-vl-120b-a12b` (`orchestrator: super`). Ultra 3 remains an explicit alternate (`ultra`).
- Intended specialists: `mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit` (`local_profile: lightning35_mlx4bit`), required runtime context **32768**. The repository name is not the serving instance ID. That ID must come from native loaded-state discovery. `nano3_mlx` is an explicit alternative only.
- `console.js` keeps `liveIntegrationGateOpen = false`. Both the visible Live control and the start handler are gated. A mocked `health.live_ready:true` plus available artifacts cannot bypass it. Builder must not enable this until the overseer reports back; backend readiness and artifact availability remain additional requirements. The dormant live request now explicitly carries `orchestrator: super` and `local_profile: lightning35_mlx4bit` rather than relying on environment defaults. No alternate-profile UI is exposed while the gate is closed.
- User authorization is for **one** smoke only after gate approval and preflight, with no hero before overseer reportback. This frontend task started **no preflight, smoke, live call, native-model request, server or preview**. No browser permission was requested or assumed. No push/public sharing.

### What changed
- The landing has a separately labeled **intended live stack / gate closed** disclosure. Generic engine labels no longer hardcode Nano. The recorded model identity comes exclusively from source events/report metadata; 37dc remains Ultra/Nano, historical and **UNACCEPTED** with the false Skeptic history warning.
- The shared typed reducer distinguishes configured, requested, observed, legacy untyped model, provider/base URL and completion-request state. It reads `planner_identity` and AGENT_STEP `model: {requested, observed}` without stringifying objects or replacing null observed IDs. A configured route, loaded pin, family match or response name never establishes checkpoint/quantization equivalence. With `completion_requested:false`, the selected model is requested-only, never observed.
- Source-run `model_routing`, `local_model_preflight`, native loaded instance/context, `cloud_route_classification`, and available `cloud_calls`/`specialist_calls` appear in **Recorded routing & model attempts**. Individual attempts remain individually inspectable, including explicit fallback flags. No pure-route classification or missing attempts are inferred. This panel uses actual events, REPORT `call_accounting`, or the report; it makes no readiness/model calls.
- `SPECIALIST_INCOMPLETE` and `SPECIALIST_FALLBACK` open a warning entry plus a persistent failure panel outside drawers. The panel shows the exact summary, role/reason, factual status and checked/total (including **0/1**), context budget labeled an estimate, requested/observed identities, and literal completion/fallback booleans. The observation does **not** terminate transport: AGENT_STEP and the exact API terminal summary still arrive. A failed specialist cannot become PASS even if a contradictory completion/report follows; download and report navigation remain unavailable.
- AGENT_STEP displays original event/source references, tool-call IDs/arguments, phase, result references and `summary_origin`. Its bounded software description is explicitly **not private reasoning**. `RAG_DECISION`, retrieve-tool `args.decision`, and telemetry `rag` support explicit retrieve/skip/reason/query. Skip takes precedence over the tool name; no search or sources are invented. Returned chunks expose exact returned text, IDs, URL, score scope and corpus hash; these are curated paraphrases, not original-paper quotations. `evidence_use`/`how_used` remain labeled declarations, not causal proof. Historical events are never augmented or renumbered.

### Remaining integration gaps / no fabricated fields
1. The new producer supplies correlation/model/RAG fields that legacy 37dc lacks. No backend schema change is requested for fields now supported. Source consistency/admission stays the backend's responsibility; displaying telemetry is not validating producer provenance.
2. Per-attempt metadata is visible when a report or REPORT call accounting supplies it. If a run aborts before that event, earlier cloud/specialist attempts are **not all available through this frontend's SSE/review contract**. Builder would need additive per-attempt observations or a safe source-bound read-only failure-accounting endpoint to expose them; no checkpoint/provider dump route was added here.
3. Original-paper span coordinates remain absent because returned chunks are curated summaries. Exact chunk text/IDs and source references are shown without pretending they are paper quotations.
4. A verified hypothesis → contradiction → executed follow-up → revised conclusion chain and external hero acceptance are still missing. New software telemetry does not by itself establish either. 37dc's independent correction remains an independent review finding.
5. Durable raw live-event links, real measured benchmark JSON, and runtime/generation equivalence across controls remain integration work. The generic live-readiness flag still needs explicit builder support after operational approval. No live integration success is claimed.

### Verification and screenshots
- **10 reducer tests**, **9 full-client DOM tests**, **11 Python frontend tests**, existing console/report/selector contracts, strict TypeScript 5.9.3 check, JS syntax/reference checks and `git diff --check` pass. New fixtures cover literal mismatched/null model IDs, context-overflow observation plus terminal, 0/1 budget display, contradictory completion rejection, mixed/fallback accounting, explicit skip, exact chunks and declared use. Synthetic fixtures are not measurements.
- Reprojected the two unchanged local JSONL copies: 37dc has 70 events / complete, 4897 has 65 / error. Both preserve the original Ultra/Nano strings; neither acquired Super/Lightning labels. No history was relabeled, repaired or promoted.
- Inventory: 98 HTML IDs, 6 static assets / JS files. `.cache/frontend-qa/*.png` still predates the landing and this change. **No current browser/layout verification**, new screenshot or live readiness result. Existing server remains stopped.


## Latest follow-up — reviewed risk-tier badge and tooling ledger

The 02:42 CST coordination relay reports Astra acceptance of backend risk contract `46bf14b` (644 tests + 54 adversarial cases). Read root `docs/RISK_TIERS.md`, `model_customs/risk.py`, terminal emission and origin/report metadata **read-only**. This frontend did not rerun or certify those backend gates. Latest backend docs commit was relayed as `bbb6bb2`. Builder remains sole integrator; `20d943b` and this follow-up are queued, not integrated into root here.

### Risk UI and source contract
- Implemented a **read-only badge**, not an inactive live selector. Supported source values are `low`, `standard`, `critical`; `standard` is the backend default for a new audit. An absent legacy field is shown as **not recorded**, not retroactively assigned standard. Unsupported or inconsistent tier/policy metadata is labeled explicitly.
- Origin/report/terminal `risk_tier` supplies the badge. `risk_policy` is shown as the original snapshot (version, tier, discovery budget per variant, clean accuracy floor and inconclusive disposition). The frontend does not duplicate the policy table, calculate cutoffs, select probe counts or infer executed tests from a maximum budget. Backend owns policy/admission.
- Error-terminal `policy_verdict` and `policy_reason` render in a separate **Recorded deployment policy** panel. `accepted_completed_verdict:false` remains visible. The main result stays **INCOMPLETE**, downloads remain disabled, and no report/hero eligibility is manufactured. Critical's precautionary QUARANTINE is not a confirmed backdoor detection; low/standard FLAG is not a completed audit either. Benchmark metrics were not changed or populated by these holds.
- Full-client DOM fixtures cover all three tiers, missing/unknown/conflicting metadata, terminal FLAG/QUARANTINE versus INCOMPLETE, and clearing prior policy displays when a different capture loads. The same renderer handles live/replay events, but only offline fixtures were exercised. No new run was copied or replayed.

### Corrected context and current gate
- The earlier exact **32768** requirement was an interpretation of “32K,” not the native observation. The user corrected it: native context was **32000**, and fresh pins permit **>=32000**. Display the actual native value literally; larger fresh pins are allowed, but drift inside a run still rejects. The stale static intended-context label now says minimum 32000; the renderer continues to show the actual metadata without rounding or substitution. Fixtures cover 32000 and 65536. No context validator or backend pin policy was changed here.
- The earlier failed exact-pin preflight had **1 GET, 0 completions**, with no smoke ID/verdict at that stage. That earlier snapshot is not the later retry outcome.
- The latest relay says the single authorized retry `3f078d7567064cd181eca62213d830d2` failed at **02:31 CST**: Lightning Investigator returned a JSON schema definition instead of a result; no fallback. This is a relayed outcome, not a locally inspected new trace or successful hero. **Hero CLOSED, no new live authorization**. Existing `liveIntegrationGateOpen = false` remains unchanged. Historical 37dc remains unaccepted and retains its Ultra/Nano identity.
- Live integration, hero replay and browser QA stay queued behind stack smoke and Astra's gate. No server, preview, local preflight/model call, smoke, public share, push or helper was started here. Current UI is not browser-verified and screenshots remain unchanged/outdated.

### Documentation and checks
- Added `docs/TOOLING.md` and README **Built with** for SpaceXSI preparation. The ledger credits actual T3/Codex frontend work, the one reviewed Sol benchmark helper and pinned MIT reuse. GrokBot/starscream coordination is attributed to relays; its concrete receipt remains pending. Cursor/local Nemotron development-task usage is not invented. Builder should integrate the new README section without overwriting newer root backend/status prose.
- 13 full-client DOM tests pass (four added contract cases, with multiple tier/context fixtures), plus syntax/reference and diff checks. Static inventory: 103 IDs / 6 assets / 6 JS files. Existing console/report/selector and Python frontend checks are also run for this change. No risk-policy efficacy, live completion, backend-integration or browser-layout result is claimed.
