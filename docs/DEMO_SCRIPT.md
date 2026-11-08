# TripWir3 video — maximum 1:55

Record the integrated read-only UI at 1440px. Keep **RECORDED CAPTURE** visible. Use historical `37dc206e` for the walkthrough and `df2b80f8` for the latest incomplete attempt. Neither is an accepted completed hero. Do not film credentials, terminals containing secrets, private per-ID ground truth or the synthetic benchmark. Do not run another audit to record this video.

## Timed narration and shot list

| Time | Shot / action | Narration |
| --- | --- | --- |
| 0:00–0:12 | Recorded overview; keep REVIEW FAILED visible | “An adapter can change a model only when a trigger appears. TripWir3 links inspection decisions to test outputs before deployment.” |
| 0:12–0:27 | Intended configuration, then recorded source identity | “The current stack uses cloud Nemotron Super for planning and local Lightning for structured specialist results. This historical recording uses earlier routes, shown as recorded.” |
| 0:27–0:45 | Start walkthrough; decision and exact canary span | “This demonstrates the evidence workflow, not an accepted detection. Nemotron selected a probe; the interface links its arguments to the exact marker span.” |
| 0:45–1:01 | Control comparison; show one matched prompt and three raw outputs | “Compare matched inputs across base, benign and poisoned controls. These are three related development artifacts, not population detection results.” |
| 1:01–1:14 | Retrieval source disclosure | “Retrieval is lexical over curated paper summaries. Returned text and source IDs remain inspectable; relevance is not confidence.” |
| 1:14–1:29 | Historical Skeptic step and REVIEW FAILED | “The historical Skeptic invented earlier history. We preserve it, show REVIEW FAILED, and do not present it as a success.” |
| 1:29–1:41 | Select df2b80f8; INCOMPLETE, STANDARD, policy FLAG; no report | “The latest attempt also ended INCOMPLETE after twenty decisions. Investigator passed; Skeptic and Report were not reached. No accepted report exists.” |
| 1:41–1:52 | Public result-doc aggregate only; no private per-ID metrics | “Separately, local MLX characterization measured forty-two of ninety-six activations and eight of one-seventy-six false triggers. Runtime and provenance limits remain explicit.” |
| 1:52–1:55 | Return to recorded overview with status visible | “An evidence prototype, not a safety certificate.” |

Total allotted time: **115 seconds**. Narration is deliberately shorter than the allotted time; use the remaining seconds for clicks and reading the visible evidence. Stop recording at 1:55. Do not speed through limitations or add a closing segment.

## Preparation and evidence constraints

1. Start `python3 -B scripts/serve_frontend.py --port 8011` and open `http://127.0.0.1:8011/`. The server serves existing evidence read-only and rejects audit POSTs.
2. Preload 37dc and the relevant comparison/source drawers. Recorded controls and raw outputs must exist locally; Git does not include ignored run folders or model weights. A fresh public clone has an empty catalog.
3. Keep the source model identities visible when describing routes: the historical capture is Ultra/Nano, not the newer Super/Lightning run. Do not relabel either.
4. “REVIEW FAILED” on 37dc is an independent finding, not proof the model caught its own error. Its recorded QUARANTINE does not establish an accepted verdict.
5. The newer df2b run is INCOMPLETE with standard-policy FLAG. FLAG is an operational deployment hold, not detection. Investigator's one successful result does not prove the prompt change's cause or general efficacy.
6. The 14B rates are a separate, known-trigger ground-truth characterization, not auditor accuracy. MLX affine4 differs from NF4-double/BF16 training; exact community-weight derivation is unproven. Two capped outputs remain included; legitimate always-marker benign controls are excluded from FTR; 192 unique base outputs are reused across 384 comparisons. All twelve adapters remain UNAUDITED.
7. Exact caveat paragraph and per-ID-neutral counts are in [ZOO_MLX_TRIGGER_RESULTS.md](ZOO_MLX_TRIGGER_RESULTS.md). Latest failure evidence is in [HERO_RUN_RESULTS.md](HERO_RUN_RESULTS.md). The older [60-second frontend shot list](FRONTEND_VIDEO.md) is a historical UI segment; this 1:55 full-video script is current.

No new model call, audio/video render, upload or submission is implied by this script.

Current aggregate-only sensitivity note: qualified FTR is8/176; including16legitimatealways-marker control outputs gives24/192=12.50% UNQUALIFIED control marker emission. The5/12condition-marker adapters are a class-neutral observable, notfivebackdoors. Bothcappedcontinuations hadnomarker andremainincluded. Do not add privateper-IDeligibility or a newend-to-enddetectionclaim to thevideo. This addendum adds no narrated segment beyond115seconds.
