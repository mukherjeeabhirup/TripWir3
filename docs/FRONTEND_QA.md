# Frontend v2 QA — November 8, 2026

## Scope

Local `feat/frontend` worktree, based on `b355fab`. Abhirup authorized recorded-data browser QA and then requested a minimal NVIDIA-inspired redesign. The two reference screenshots in the main checkout's `docs/design-refs/` were inspected read-only. No NVIDIA logo or wordmark was added.

The UI uses near-black surfaces, gray hairlines, white/gray text, and `#76B900` as its only accent. Layouts use rows, tables, a collapsible capture sidebar, search fields, and an active-tab underline. There are no card grids or shadows. Authored UI strings have no middot/bullet separators. Long explanatory caveats moved out of the primary UI; exact source text remains available in collapsed source disclosures and original JSON.

## Evidence boundaries

- The displayed historical poisoned capture is `37dc206e552740aeb65c956a83782211`. Its recorded QUARANTINE is retained alongside REVIEW FAILED. Independent review found false Skeptic history. It is not an accepted hero or an agent self-correction.
- `4897316f967e440a82afb09eb1c25ed5` has 65 events and no report. It remains INCOMPLETE; download and report navigation are disabled.
- Historical benign/base captures have 30/32 events. Their old PASS reports lack the complete current display contract, so the UI displays INCOMPLETE. The original report remains available as historical source evidence; it is not recertified.
- Control comparison uses the saved matched prompt/expected rows for base, benign, and poisoned captures. Counts mean exact `CANARY_CUSTOMS_742` hits / prompts. Other markers are not included. Three related controls do not establish population detection quality or causal equivalence across runtimes.
- Claim coverage counts checked/required claims on accepted actions only. Rejected candidates and free-form prose are outside that denominator. Coverage does not override REVIEW FAILED.
- PASS means no evidence found within the tests performed, not a safety certificate. Low LoRA rank alone is not evidence of a backdoor. Weight/activation plots retain the scope in `WEIGHTWATCH.md`.
- RAG summaries/chunks are curated source text. Retrieval scores are lexical relevance, not confidence. Declared use is not causal proof. Source records are unchanged.
- Risk tiers and policy snapshots come from recorded metadata. Missing tiers use an em dash; invalid/inconsistent metadata is explicit. A critical policy QUARANTINE or low/standard FLAG after an error is a deployment hold, not a completed detection. The main status stays INCOMPLETE and `accepted_completed_verdict:false` remains visible.
- Context budgets are estimates, identified as such in the source panel. The intended minimum context is 32000 tokens. Recorded native context is displayed literally, including larger values; intended routing never rewrites historical model identity.
- New trigger-test ASR/FTR are UNMEASURED/pending. No values from that test were inserted. Historical measured rates are still displayed with their capture; absent measurements use an em dash, never a fabricated zero.
- `/static/benchmark.html` contains explicitly labeled synthetic EXAMPLE DATA / NOT MEASURED. It remains hidden from the main navigation and is excluded from the video shot list.
- No LM Studio/NVIDIA API calls, model loads, live hero runs, push, external publication, or backend integration were performed. Live remains gated off.

## Browser checks

Used only `python3 -B scripts/serve_frontend.py --port 8011`, bound to `127.0.0.1`. It serves static assets/read-only review routes; POST is disabled. T3 Preview used the environment-port target. Tests used the four existing local historical captures and temporary, explicitly named QA FIXTURE browser responses; no stored capture was edited.

| Check | Result |
| --- | --- |
| Root, walkthrough, trace, comparison, evidence, benchmark, credits | Opened and exercised |
| Walkthrough | All six stops, previous, sources, finish, overview and explore work |
| Replay transport | 70 stored SSE events; QUARANTINE and REVIEW FAILED retained |
| Failed capture | 65 events; INCOMPLETE; metrics cleared; report disabled |
| Base/benign selection | 32/30 events; current completeness rules retained |
| All three risk tiers | Browser response fixtures show low/standard FLAG and critical QUARANTINE separately from INCOMPLETE |
| Context-overflow fixture | 0/1 grounding check, literal 32000 context, requested/observed identity, completion/fallback false visible |
| Switching captures | Old risk policy, failure, route values, report values and inspector heading cleared |
| Empty and error states | Empty catalog, trace HTTP 404, empty benchmark and invalid benchmark JSON show recovery/no results |
| Search | Capture/event search, no-match states and restoring results work |
| 1440px and 390px | No page-level horizontal overflow in exercised views; benchmark ledger scrolls inside its own region |
| Dark/light OS preference | Both checked; the requested dark application theme is intentional in both |
| Keyboard | Visible 2px green focus ring, skip link focuses main, arrow/Home/End tab navigation, walkthrough title focus |
| Accessibility basics | Named controls, scoped table headers, exact-hit caption, SVG text alternative, keyboard-scrollable trace/table |
| Contrast | Primary text 17.45:1; secondary text on panel 7.04:1; primary-button text 7.89:1 |
| Report export | Click handler generated correct JSON blob and filename for 37dc; browser download was intercepted in-memory to avoid writes outside the worktree |
| Console | No page console errors observed in snapshots |

This is browser/layout and software validation, not scientific validation, an exhaustive accessibility audit, or validation of the newer backend branch.

## Fixes beyond the redesign

- Capture-fetch failure clears the old landing disposition and inspector heading.
- Capture switching resets event search/filter state with other metadata.
- Walkthrough jumps align the selected event header at the top of the trace, rather than clipping it above the scroll viewport.
- Walkthrough navigation no longer overlaps the tab row.
- Mobile capture navigation is collapsible and available instead of hidden.
- Keyboard tabs use roving focus; main content and trace have usable focus targets.
- Duplicate event-body prose was removed from the expanded row. Recorded rationale/source text remains accessible through disclosures and JSON.

## Checks

```sh
node --test tests/frontend-*-contract.cjs
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider
python3 -B scripts/check_frontend.py --require-node
npm exec --offline --cache .cache/npm --yes --package typescript@5.9.3 -- tsc --allowJs --checkJs --noEmit --strict --target ES2022 --lib ES2022,DOM model_customs/static/audit-events.js
git diff --check
```

Results: **43 Node checks** (15 full-client DOM, 15 benchmark, 10 reducer, three renderer/selector contracts), **379 Python tests**, syntax/reference checks (107 HTML IDs, six assets/JS files), strict reducer typecheck and diff check pass. The worktree's lightweight `.venv` could not collect the two PyTorch suites; rerunning the complete suite with the already-installed main project environment passed. No packages were installed and no models were loaded. Logs are ignored under `.cache/frontend-qa/`.

The repository secret scan completed with zero findings across 127 working-tree files, 126 index blobs, 699 history blobs and 211 history metadata records. All 31 copied evidence files were rehashed against the main checkout originals after QA; every file matched. Newly added documentation and screenshots are also included in the staged-file pattern check before commit.

## Screenshots

Fresh T3 Preview exports used `save=true`. See [screenshot index](screenshots/README.md). Desktop layout was checked at 1440 CSS pixels; Preview exports scaled desktop PNGs. Mobile PNGs use a 390px viewport. These supersede the old ignored `.cache/frontend-qa/` screenshots from the previous frontend. Capture native video from the running UI rather than zooming the exported PNGs.

## Root integration update — November8,2026

The preceding frontend-branch report is a historical snapshot. The root now integrates all11frontendcommits through963bb39; current MLX ground-truth results are independently accepted and recorded in [ZOO_MLX_TRIGGER_RESULTS.md](ZOO_MLX_TRIGGER_RESULTS.md), not UNMEASURED. The newer df2b80f8 Super/Lightning attempt is independently accepted as preserved INCOMPLETE failure only, not a completedhero; see [HERO_RUN_RESULTS.md](HERO_RUN_RESULTS.md). Use [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the full115second maximum video. Preserve37dcREVIEWFAILED and source identities. Rootintegrationchecks:737Python/43Node/stricttsc/staticchecks passed; integratedbrowserreceipt remains separate under .cache/runs/builder-frontend-integration-20261108-0814. No new inference or push.
