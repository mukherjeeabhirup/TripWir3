# TripWir3 — Astra overseer handoff

> Latest status: see **Resumed research work and delegation** and **Research plan handoff — 23:37 CST** at the end. The pause and earlier snapshots are historical; the user explicitly resumed from c64eb91.

Snapshot: **November 7, 2026, about 9:15 PM CST**. This note is the user's explicit, limited exception to the overseer's no-edit rule. Handoff only: no new audit, capture, tests, approval, message send, push or spending during this handoff. Fresh Astra max takes over; this thread stops after writing the note.

## Ownership and boundaries

- Workspace is exclusively `/Users/abhirupmukherjee/Downloads/hackutd26`. No other folders, OneDrive, sudo or global installs. Never print secrets or `.env` contents.
- Builder owns source, integration and commits. Overseer reads/reviews and runs checks. User explicitly permits **isolated test files and new replay outputs inside this project**, including `.cache`; source and existing evidence remain untouched. This note is the sole additional write authorized for this handoff.
- Builder: <t3-thread://v2/74ad084c-8026-4e50-a49b-211ec763d5e2/mcp:launch:309039be33d95b962233a93232dc9e58ea6b9dede0f68054b6ab6d22136d0d77>. Last read through message position **934**: active run ordinal 4, later work queued through ordinal 10. Coordinator has already instructed it to finish only the existing capture, preserve its outcome, write `docs/HANDOFF_BUILDER.md`, commit the handoffs locally if available, leave port 8000 up and stop. No coordination send was needed from this thread.
- Old queued instructions must not launch duplicate captures or restart completed work. Consult the builder handoff for its final safe-point state and children; this note does not claim they have settled.
- **Pending browser/preview_evaluate approval: preserve it; do not approve it on the user's behalf.** Its pending request ID/state was not re-inspected or changed during handoff. Last earlier observer tab was closed; that does not establish that a separate outstanding approval disappeared. Continue from saved evidence if browser access is pending.

## Git and requested document review

Read `docs/PLAN.md`, `docs/DECISIONS.md`, `README.md` and recent Git log during handoff. **`docs/TOOLING.md` does not exist**; project filename search found no TOOLING file. Do not claim it was read or recreate it without need.

- Branch: **`feat/scaffold`**; source HEAD at handoff read: **`88f0ae98a4584362445b08965aac624b9dedebdd`**. Tracking `origin/feat/scaffold`, no ahead/behind shown. Builder may make a later local handoff commit.
- Before this note, the only working-tree change was builder-owned `docs/DECISIONS.md` (+5 lines recording the current capture). Do not overwrite or revert it. This handoff is not committed by the overseer.
- PLAN preserves the original schedule, sole-integrator rule, scientific gates, executable checks and cut lines. Later appendices update acceptance through 212 tests. Earlier status sections are historical.
- DECISIONS records failed training, adopted recipe, grounding failures, source/evidence preservation, identity/terminal/report fixes, provider-budget diagnosis and current capture. Later entries supersede historical Node-unavailable and prescribed-hero choices; do not revive those choices.
- README accurately limits the project to a controlled case study and bounded PASS, documents startup/replay/checks and scientific limitations. Its current-status paragraphs still mention 207 tests and a provider correction as pending; the correction is now committed and independently passed 212. Builder must reconcile current status after the capture/replay outcome, while preserving historical evidence.

## Original timeline and cut lines (all CST, Nov 7–8)

Critical path: small base → sequential benign/poisoned LoRA training → controlled final evaluation → real Nemotron investigation → real recorded trace → reliable live dashboard/replay. Training actually finished by **7:24:50 PM**, before the plan was received at 7:57 PM; no training remains on the critical path.

| Window | Planned milestone |
| --- | --- |
| Sat 7:15–8 PM | Setup, pilot, start adapters by 8 PM |
| 8–9:30 PM | Typed tools, provenance, SVD/vectors, activation checks, verifier, retrieval |
| 9:30–11 PM | Genuine tool-dependent agents, skeptic, frozen held-out suite, grounded report |
| 11 PM–12:30 AM | Live dashboard plus accepted real replay |
| Sun 12:30–2 AM | Three-control benchmark and agent evaluation; expand artifacts only if core works |
| 2–4 AM | Failure handling, integrity, demo hardening; **feature freeze 4 AM** |
| 4–6 AM | Independent end-to-end verification; fix blockers by 8 AM |
| 8–9 AM | Regression and release/demo freeze |
| 9 AM–noon | Video, Devpost, submission buffer; **deadline noon Sunday** |

Cut lines: no feasible training ETA by 8 PM → smaller base/pilot; no successful canary by 10 PM → honest controlled known-trigger scope; no E2E by midnight → stop extra models/stretch/polish; no broad benchmark by 2 AM → ship **N=3 related controls**; no genuine accepted recording by 4 AM → **NOT READY**, prioritize capture. NemoClaw is at most a one-hour spike only after core gates pass; multimodal last. Brev's $60 credits require Abhirup's explicit spending approval. Parallel child work uses disjoint files; builder alone integrates/commits.

## Independently accepted milestones

| Commit | Accepted change | Independent full tests |
| --- | --- | --- |
| `0f29ad1` | Executed-evidence ledger, decision grounding | 69 passed |
| `111acdd` | Accepted plan, safe CLI help/check commands, retired staged hero | 100 passed |
| `75a7d3b` | WeightWatch v1 spaces and explicit adaptations | 106 passed |
| `dc79807` | Actual config/weight identity, resume invalidation, terminal/replay predicate | 183 passed |
| `41ec133` | Full-record deterministic primary report, truncation totals, draft separation | 207 passed |
| `88f0ae9` | Bounded structured Nemotron replies, selector preservation | **212 passed** |

Latest independent full suite: **212 passed in 4.04s**, source/test fingerprint unchanged before/after. Node **v26.13.0 is installed**; builder was informed earlier. Strict frontend check passed real `node --check`, 45 HTML IDs, 109 literal JS references and 2 assets. Node DOM contract tests cover report custody/draft labels and selector preservation. Plain JS has no configured linter, TypeScript compiler or bundler; no packages were installed. Fixtures do not replace browser verification.

Commands already run from project root (do not rerun merely for this handoff):

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/Users/abhirupmukherjee/Downloads/hackutd26/.cache/tmp .venv/bin/python -B -m pytest -q -p no:cacheprovider --basetemp=.cache/overseer-pytest-20261107-2112
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/check_frontend.py --require-node
```

Latest reviewed source/test fingerprint, covering `.py/.js/.cjs/.mjs/.html/.css` under `model_customs`, `scripts`, `tests`: `d6ef956a31fcf99d869241522d0e1ad09bbe423adea63076a734ed8851711550`. Repeat appropriate tests if source changes; docs-only handoff commits do not themselves invalidate this software result. Latest independent secret scan was clean at `41ec133`; builder reported another clean precommit scan at `88f0ae9`. Final release scan remains to be independently refreshed, using `scripts/scan_secrets.py` (filenames/counts only).

## Current readiness and exact interruption point

**Last independent verdict: NOT READY for final demo acceptance.** Software gates pass; a newly accepted real recording, packaged offline replay, normal browser replay and final documentation review are still required. This is not a final verdict on a subsequently completed capture.

Latest live source: **`4897316f967e440a82afb09eb1c25ed5`**, poisoned control, API capture on **`88f0ae9`**, started about **9:12 PM CST**. Builder owns port **8000**; do not stop it or start a competing target-model audit. At its last read message (9:13:30 PM), builder reported valid JSON, zero reported reasoning tokens, normal completion stops, discovery exact/paraphrase 4/4 target hits and partial/neighbor 0/4, plus one rejected candidate decision followed by revision. **Held-out verification and verdict were still pending in that message; these new claims have not yet been independently verified.** Read the final builder handoff/saved files for the eventual result; do not infer success from this progress report.

Exactly what the overseer was doing when stopped:

- Observing that existing capture's real SSE, not starting another audit. HTTP 200 and `text/event-stream` were established. Existing `exec_command` observer session **37275** wrote to `.cache/overseer-live-sse-4897316f967e440a82afb09eb1c25ed5.txt`, with a 360-second timeout. It may finish independently; session portability to a fresh thread is not guaranteed. It was not polled/restarted during handoff.
- Next intended work was to compare observed events against `runs/4897316f967e440a82afb09eb1c25ed5/`, independently recompute claims/metrics and verify freeze-before-final, terminal/report equality, identities, actual model calls and primary-report grounding. Then review a builder-created bundle and offline/browser replay. **None of those next checks were completed for this run before handoff.**
- Previous live browser observation showed the actual streamed ledger and TripWir3 branding with no horizontal overflow. It exposed the selector reset (fixed at `88f0ae9`, browser confirmation pending). My custom observer reconnect handler duplicated display events after a failed stream; that was observer harness behavior, not altered saved evidence or a confirmed app defect. The observer tab was closed. Normal app replay still needs its own browser check.

## Evidence history and claims that must remain bounded

- Base + benign LoRA + poisoned LoRA are genuine local Qwen2.5-0.5B controls. Adopted training: MPS, rank 8, alpha 16, 48 adapted modules, LR .0003, 240 steps, batch 8, seed 742; failed .002 recipe preserved. Prior independent checks matched all eight base files and both adapter weights/config identities. Full benign SVD reconstruction across 48 modules had maximum relative error about `7.6e-7`.
- WeightWatch v1 uses output/left-U alignment; input/right-V is supplementary. Current absolute pooled extrema over 100 unique clean arithmetic prompts are an explicitly simplified diagnostic, not the paper's signed streaming detector. Low rank alone is never evidence.
- Frozen final suite has **80** prompts: clean20 plus12 each exact, literal-preserving paraphrase, partial, near-neighbor and matched paraphrase-clean. Final/calibration/discovery are disjoint. Freeze occurred after training but before final outputs; outcomes have now been seen. Recaptures are operational replication, not new independent scientific validation or retroactive preregistration.
- Known literal intake tip is disclosed; do not claim blind discovery. PASS means **no evidence found within tests performed**. N=3 related artifacts is a case study, not population detection accuracy. Agent-selected retrieval/follow-up must be real; check what the skeptic actually caused versus merely proposed. Do not manufacture a contradiction or prescribe probe order.
- Historical three-control measurement benchmark (`718001e`) is real: base `b464226d9f6c414684fbe3acdca56609`, benign `8431bfa29eca43c3be41d1cdf14c42fa`, poisoned `45c45c9ed66e4864a97b43c0a3b261ff`. Poison45 has correct metrics but false agent history; 8/11 decisions failed independent chronological review. Preserve `docs/evidence/failed-grounding/`; it is excluded from replay.
- `cc99bfe5bb354e8685de7d7d83166e7f` (`dc79807`) had valid metrics/12 grounded actions/terminal and three actual local Nano specialist calls, but Nano report prose said 8 modules instead of 48. Preserved/excluded; `docs/evidence/cc99-grounding-review.json`. Fix `41ec133` renders primary facts from full validated records (48 modules,96 alignment records,100 calibration,80 final), retaining raw model draft separately as unverified.
- `fd4ec043fc834777a4796ab62ec20546` (`41ec133`) ended with CloudError before held-out verification, no report. Six final HTTP-200 responses exhausted 2048 tokens entirely on reasoning without JSON; not a 429 or a completed verdict. Preserved/excluded; `docs/evidence/fd4ec-provider-failure-review.json`. Fix `88f0ae9` uses documented `chat_template_kwargs.enable_thinking=false`, rejects length-stopped outputs and retains token cap, retries, limiter and grounding gates.
- In prior measured poisoned runs, exact/paraphrase final target hits were12/12; clean0/20, partial0/12, neighbor0/12, paraphrase-clean0/12. Arithmetic scores are separate. Neighbor outputs were `CANARY_CUSTOMS_743`, so zero exact `CANARY_CUSTOMS_742` hits does **not** imply no anomalous behavior. Recompute the latest run rather than copying these outcomes.
- Cloud orchestrator primary is Nemotron3 Ultra; smaller fallback is Nemotron3.5 Lightning. Every attempt uses shared project-local30rpm pacing under the user's40rpm key limit, bounded retries. Local LM Studio Nano may serve specialists; report actual execution versus explicit rule fallback. No Brev spend or NemoClaw/multimodal result is part of the slice.

## Fresh overseer's next steps (after handoff, not executed here)

1. Read `HANDOFF_BUILDER.md` and current Git state. Finish reviewing the existing 489 source from saved files and SSE; no duplicate capture. Verify actual chronology, grounding, skeptic impact, retrieval, held-out hash, counts, identity and exactly one matching final completion. Failed/closed traces stay immutable and ineligible.
2. If accepted, builder packages with `scripts/bundle_demo.py REAL_RUN_ID`; independently run `scripts/check_offline_replay.py REAL_RUN_ID` with isolated project outputs. It forbids provider initialization and uses unavailable weights/in-process HTTP/SSE; strengthen with network connection denial if appropriate. It is not browser QA. Verify source hashes unchanged.
3. Resolve the existing browser approval through the user/coordinator; do not self-approve or silently reissue it. When allowed, use normal dashboard **Recorded real run** flow and POST replay (authorized isolated output), checking terminal metrics, original source ID/time/actual model, separate replay ID, primary/draft labels, selection preservation and layout. Do not click an export that writes outside this project. Leave builder's8000 process up; close only overseer-owned tabs/processes.
4. Review final commits/docs/branding, refresh the secret scan and appropriate changed-source tests. README must name an actually accepted recording and distinguish test fixtures, measurement evidence and model prose. Preserve decision chronology. Return **READY / NOT READY** with a concrete punch list; neither the 212 software tests nor a successful live terminal alone proves the demo ready.

This handoff intentionally ends oversight in the old thread. Pending approval, current capture and builder work are not cancelled, approved, duplicated or declared complete by this note.


## PAUSED — November 7, 2026, 22:10 CST

**User explicitly paused all work for travel; approximate return 22:30 CST is not an automatic resume instruction.** No further review, inference, browser work, queued scenario planning, benchmarking, repair, recapture or spending while paused. This handoff-only documentation write is explicitly authorized; overseer makes no commit or source-code changes. Builder owns the local safety commit, backup/checkpoint preservation and safe backend stop. Do not restart the service on your own.

### Current implementation and completed independent software gate

- Last independently reviewed runtime source: `4fa89d3` on `feat/scaffold`, local only. Preceded by `5256325` (exact local Nano gate, fixed scoped decision/report template) and `9eef160` (malformed-template rejection without exceptions). Builder may create a later documentation/pause commit; check its handoff when explicitly resumed.
- Standing local-model rule: before any recapture/benchmark, authenticated localhost `http://127.0.0.1:1234/v1/models` using project `.env` key, exact `nvidia-nemotron-3-nano-30b-a3b-mlx`, and successful tiny completion. Missing/failure means **LOCAL MODEL NEEDED**, no run. Midcapture specialist fallback is visible, aborts strict capture and disqualifies hero replay. Offline replay itself makes no model calls.
- Adopted local request path is authenticated `/v1/completions` with explicit NVIDIA no-thinking template, not a global LM Studio setting or tunnel. Observed response model must match requested identity; retained raw role replies must match successful calls and parsed role outputs. Nested report rows are schema checked before schema-success flags. Current diagnostic reproduction identifies a token-truncation failure; it does not prove the historical generic Skeptic error had that cause.
- Independent final gate at 22:01 CST: **367 repository tests in 4.13s; 28 isolated scope/template cases in 0.02s; exact local-gate adversarial reproductions; strict Node syntax/45 IDs/109 refs/2 assets; diff check; secret scan zero.** Source/test fingerprint stable `b312953acde4220dd6f342098835e210d33a06265683a39aaa02d1e463cc6694`.
- Gate record: `.cache/runs/overseer-template-review/final-gate-20261107-220133.json`. Independent tests/rechecks stay under `.cache/runs/overseer-template-review/` and `.cache/runs/overseer-grounding-review/`. Initial local-gate failure evidence remains `.cache/runs/local-gate-review-20261108T035244Z-5c970078/`; those code findings were corrected before the passing final gate.
- Original 489 (9 files) and 6be (7 files) were independently rehashed unchanged after this gate. Prior poison45/cc99/fd4ec/489/6be remain preserved, not repaired or whitelisted.

### Latest real source: technically completed, grounded hero NOT accepted

- Single authorized new API run **`37dc206e552740aeb65c956a83782211`**, source `4fa89d3`; first saved event **22:02:33.147301 CST**. API preflight completed 22:02:33.122936 CST with exact requested/observed Nano, HTTP 200 listing/completion and READY. Overseer independently matched all **20** signature source files to `4fa89d3`.
- Builder reports completion at **22:05:53 CST**, 70 events, single matching complete/report, QUARANTINE, 196 target/calibration queries, all 80 held-out outputs, 48 modules/96 alignment records/100 calibration prompts, and three genuine exact-Nano HTTP200/stop/schema-valid roles with no fallback. These full terminal/raw-metric/bundle checks are **builder verified, not yet all independently recomputed by this overseer**.
- Independent saved-event/role review confirms 19 candidate decisions, 17 executed actions and two duplicate exact-probe action rejections (steps 11/12, events 41/43). Zero grounding rejections does not mean zero rejected actions. Six model-selected RAG calls are two queries repeated three times each; do not present them as six distinct research advances. Full retrieval history stays in events; top-level report retains last query only.
- **Material factual Skeptic failure confirmed directly by overseer and read-only child:** event 52 / `report.specialist_outputs.skeptic` says “Partial and paraphrase probes were not executed,” “absence of exact-match canary activation,” and refers to exact-probe failure. Events 14/18/22/26 already contain all four discovery probes; exact/paraphrase each emitted target742 on 4/4. Proposed countertests also confuse output marker `CANARY_CUSTOMS_742` with input trigger `CUSTOMS-APPROVED-742`.
- This is false specialist history, not genuine counterevidence or contradiction. All discovery precedes the skeptic; no skeptic-caused new counter-test is established. Do not claim all agent reasoning is grounded or that the system detected the error: independent review detected it.
- Current renderer labels specialist text **UNVERIFIED**; the false history is not promoted into deterministic primary findings. REPORT model output is fixed scoped rows and `tested_prompts_only`; primary narrative remains independently rendered. Preserve the distinction: mechanically accepted terminal/structured facts/no fallback can pass while substantive Skeptic reasoning fails. **Grounded multi-agent hero acceptance is withheld; overall NOT READY.** Builder acknowledged the material defect and no hero promotion/repair/recapture.
- Provisional byte-for-byte bundle exists at `demo/recordings/37dc206e552740aeb65c956a83782211/`. Builder reports its in-process offline check passed 70 events with provider initialization forbidden, absent keys/weights. This is **not browser QA** and not an overseer network-denial pass.
- Builder review paths: `.cache/grounding-review/review_capture.py` and `.cache/grounding-review/37dc206e-source-review.json`. Preserve original run/bundle/checkpoints. Do not stage or present provisional bundle as an accepted grounded hero.

### Exact interruption boundary and remaining work — only after explicit resume

- Overseer had begun examining report shape and pure verification helpers. **Full independent raw-output recomputation/current artifact rehash, closed-source predicate/report-determinism check, bundle byte comparison and network-denied offline replay were NOT run to completion for 37dc.** No new source-review output file was written for 37dc before pause; the confirmed substantive role finding is saved in this section and was sent to builder.
- No browser work was attempted. Existing pending preview approval remains unresolved: do not approve or silently reissue it. Normal-browser replay, source ID/time/model versus new replay ID, selector and primary/unverified labels remain unverified.
- No further repair or capture is authorized by the pause. On resume first read builder safety handoff/current Git state, then obtain user's decision on the substantive Skeptic defect. Do not revive a queued scenario plan automatically.
- Timeline communicated to builder: agent-loop target 23:00; if no accepted capture then cut extra models/NemoClaw/multimodal/expanded benchmark/UI extras. If replay is not in independent QA by 23:30, defer new benchmark runs and nonessential polish to protect **00:30 dashboard/replay**. Original 04:00 feature freeze, 09:00 demo freeze and noon deadline remain.
- `docs/TOOLING.md` / honest Built with remain gaps unless builder subsequently documented them. Cursor+local Nano must perform a real scoped task; do not claim pending usage completed. GrokBot coordination/automation is real and should be documented accurately.
- External planning file `docs/BREV_SCALEUP_PLAN.md` must remain **uncommitted and untouched**, as must incidental `.DS_Store`. Brev remains **NO-GO**: no spend, no payment method, no scale-up launch. Its conditional proposal is not approval.

### Pause task/service state

- At 22:09:56 CST, T3 queue lists for this overseer and builder were both empty. Project running-thread inventory contained only these two threads doing pause handoffs; no queued scenario turn was visible, so nothing needed cancellation.
- Overseer native children `prose_review` and `local_gate_review` had both completed. Interrupt checks confirmed completed status; neither remains running or queued. No overseer observer/process is active.
- Builder alone is preserving checkpoints, creating the authorized inside-project adapter backup and local safety commit, and safely stopping backend 8000 (last known process 29659/session85951). **Overseer has not independently confirmed the stop**; do not report it as completed from this note.
- This turn ends after saving/readback and notifying builder. No timer, scheduled task, automatic resume, test run, provider call, browser request or overseer commit was created for the pause.


## Resumed research work and delegation — November 7, 2026 CST

- User explicitly resumed from c64eb91. The prior pause section remains historical; no automatic resume or queued scenario run was used.
- Recapture gate remains CLOSED pending independent stable-tree review of typed run/event/role/field provenance, actual history, trigger versus output-marker references, and adversarial fixtures. Builder owns source; no overseer inference or backend restart.
- Overseer drafted docs/RESEARCH_PLAN.md (proposed only; 19-checkpoint pilot and separate 158-checkpoint research matrix). Read docs/RESEARCH_UPGRADE_BRIEF.md; its alternative schedule/budget does not supersede existing cut lines or authorize Brev. Advisor input pending.
- User-authorized Sol-max helper launched for docs/EVALUATION_PLAN.md ONLY, shared checkout with non-overlapping file ownership. Provider codex; model gpt-6.1-sol; reasoningEffort max; runtime auto-accept-edits; project hackutd26. Task ID: node:delegated-task:command%3Amcp%3A42b599c5-d136-4801-b173-6f8d075b9e8f%3Adelegate-task%3Ab34d9d10-58fc-4779-89fc-190bace9d5cd. Thread: <t3-thread://v2/74ad084c-8026-4e50-a49b-211ec763d5e2/thread:delegated-task:command%3Amcp%3A42b599c5-d136-4801-b173-6f8d075b9e8f%3Adelegate-task%3Ab34d9d10-58fc-4779-89fc-190bace9d5cd>. State at launch: running. No commits/source edits/live calls/spend allowed. Parent must review document before integration.
- New draft docs are not builder-staged until overseer review/handoff. BREV_SCALEUP_PLAN.md and .DS_Store remain untouched/uncommitted. Frontend owner remains separate.
- At 23:30 without replay QA, defer new benchmarks and optional polish. Preserve 00:30 dashboard/replay target. No browser permission reissue or self-approval.

### Research plan handoff — 23:37 CST, November 7, 2026

- User explicitly supplied the judging brief and Megatron advice, authorized including `docs/RESEARCH_UPGRADE_BRIEF.md` in the next docs commit, and revised code freeze to about 06:00 / demo freeze09:00. This supersedes the earlier 04:00/08:00 schedule and the pending-advisor wording above. Dashboard/replay target00:30 remains; no Brev launch is authorized.
- Final planning revision is `docs/RESEARCH_PLAN.md`: main19 checkpoints (12 intended-poison adapters,5 benign,2 bases), exact J01–J17 training list plus unscored P00 throughput pilot, 14B first, 27B/158-checkpoint expansion deferred, conditional and visible retrieval, primary full-versus-single comparison, predeclared reductions, per-adapter outcomes/real costs. Ceiling <=6 aggregate H100-hours and compute strictly<$36, with existing no-debt/no-card/$50 all-in constraints. Pilot must forecast training AND inference/validation/idle/shutdown before selecting allocation.
- Sol-max scenario helper completed; final read through position51, no active child work. Parent read all of `docs/EVALUATION_PLAN.md`, corrected the precise historical Skeptic error, synchronized new token/schedule proposals, and resolved the no-candidate design gap with an independent80-prompt coverage path. Runtime support remains unimplemented/unverified; all scenarios are planned, not executed.
- Parent independently checked exact counts:17 training jobs+2 reference artifacts=19, plus1 unscored pilot; training upper bound4,456,448 processed tokens+40,960 pilot;57 audits at176 forwards plus19 oracle panels at256=14,896 target requests before declared extras. Local links and whitespace passed for research/scenario/brief docs. No model calls, source edits, new captures, browser actions, or root commits.
- Handoff to sole builder for the next docs-only local commit: `docs/RESEARCH_PLAN.md`, `docs/EVALUATION_PLAN.md`, `docs/RESEARCH_UPGRADE_BRIEF.md`, `docs/HANDOFF_ASTRA.md`, plus builder-owned contemporaneous DECISIONS as appropriate. Do not stage `.DS_Store` or `docs/BREV_SCALEUP_PLAN.md`. Do not mix the docs handoff with unfinished source changes. Builder's typed provenance correction remains awaiting stable-tree independent review; recapture gate stays CLOSED.
