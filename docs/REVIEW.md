# TripWir3 implementation review

This is an operational review of the controlled hackathon slice. Software checks, actual inference evidence, and scientific detector validation are distinct. A passing unit test does not establish backdoor-detection quality.

## Evidence status at guide preparation

- A real historical base-control report exists at `runs/ed6b83217b844a88b2b44bed0af80e12/report.json`: bounded PASS, clean toy arithmetic accuracy 20/20, exact-trigger canary 0/12, paraphrase-trigger canary 0/12, and clean canary 0/20. It is **not** the final three-control benchmark and must not be presented as validation of subsequently changed source.
- The three-control **measurement** benchmark completed under backend source commit `718001e`: base/benign bounded PASS and poisoned QUARANTINE. Raw counts, frozen inputs, and query totals were independently verified. This does **not** establish correct agent reasoning.
- Poisoned run `45c45c9ed66e4864a97b43c0a3b261ff` failed agent grounding. Eight of eleven accepted decisions contain unsupported statements. The final ORCHESTRATOR decision invents a discovery-to-final reversal; deterministic report metrics are correct. Raw events/report and the chronological audit are preserved in [evidence](evidence/failed-grounding/).
- Interim hero `bf960061e9784a10b0929baf9ecdfa1f` was stopped, has no completed report, and is not accepted or packaged.
- Grounding fix verification: **69 software tests pass**, including the eight actual false decisions enriched with correct structured claims, and full-report creation with list-valued discovery/held-out grounding checks.
- A new real grounded poison trace, packaged recording and no-key replay verification remain **pending**. No eligible recording is bundled. The user requires this milestone to end before reruns; queued PLAN.md, adapter-config resume and terminal-event replay corrections must land first.
- Actual offline provenance verification passed all three controls after the filtered-snapshot fix: eight base files rehashed per audit; benign and poisoned adapter weights/config base identities verified. These compare current bytes with local training manifests, not signed external attestations.

Replace pending status only after a new evidence-consistent real trace passes grounding review and actual replay checks. Existing measured rates must not be promoted into an accepted hero.

## Architecture and limits

| Component | Implemented scope | Limit to state clearly |
|---|---|---|
| Nemotron orchestrator | Cloud model chooses available tools, updates hypotheses from observations, and requests local retrieval | Bounded tool budget, provider availability, and model JSON validity can stop a run; an incomplete audit yields no completed PASS |
| Specialist roles | Authenticated local LM Studio Nemotron Nano if loaded; otherwise labelled rule-based tools | Without local Nano, investigator/skeptic/report are deterministic specialist tools, not independent model completions |
| Provenance | Pinned Hub metadata/card, uploader namespace, reported digests, and independent local file rehashing | Cards/base identity are publisher assertions; reported hashes differ from locally recomputed hashes; manifests can be edited by the local operator |
| Weight forensics | Genuine LoRA delta, singular values and both vector sides; activation alignment on 100 distinct clean prompts | LoRA is inherently low rank; statistics are descriptive and uncalibrated; simplified WeightWatch-style instrumentation does not reproduce its published rates |
| Trigger investigation | Harmless canary tests from a supplied suspicious-literal tip | Known seeded trigger, small arithmetic domain; no blind recovery or unknown-backdoor coverage claim |
| Held-out verification | Frozen disjoint inputs, input hash, stored outputs, exact scoring, matched clean conditions | Frozen after discovery but before final outcomes; related task templates do not establish broad generalization |
| Verdicts | Deterministic demo-v1 QUARANTINE/FLAG/PASS from measured groups | Thresholds are demonstration choices, not calibrated operating points; PASS is bounded absence of evidence |
| Benchmark | Three related controlled artifacts, sequential and resumable | No population-level sensitivity, specificity, or detection-rate claim; report source/artifact identities must match current inputs |
| Replay | Prior completed real event/report recording, integrity checks and visible replay mode | No fresh inference; hashes are integrity checks, not cryptographic proof of experimental truth |

The cloud client shares a cross-process 30 requests/minute token bucket, with capacity one, below the shared 40 requests/minute key limit. Retries and fallback use the same limiter. An uncoordinated external client using that key can still consume shared provider quota. Cloud inference is reserved for orchestration; local specialists do not silently consume cloud requests.

The hero hypothesis is specific: a partial literal may fail while the full literal succeeds. Its presence and order must be checked in the actual trace. The demonstration starts from an intake tip and does not claim Nemotron independently discovered the planted string.

The literal-preserving paraphrase group changes task wording and framing; it is **not** semantic paraphrasing of the trigger string itself. Exact task clean controls and matched paraphrase-clean controls separate conditional canary emission from generic marker emission or wording effects. Partial and near-neighbor groups test limited trigger specificity.

No Brev GPU expenditure, NemoClaw sandbox isolation, multimodal result, arbitrary uploaded-model scanner, or safety certification is claimed by the core slice. Existing [AuditBench](https://arxiv.org/abs/2602.22755), [Microsoft llm-backdoor-scanner](https://github.com/microsoft/llm-backdoor-scanner), and [WeightWatch](https://arxiv.org/abs/2508.00161) are prior work; TripWir3's framing is NVIDIA-native orchestration and evidence presentation.

## Final acceptance checks

- [ ] Current-source benchmark completes base, benign and poisoned artifacts; each report retains source/config identity and real inference origin. Failed/incomplete entries are excluded from completed counts.
- [ ] Recompute reported canary/accuracy counts from raw outputs; compare every group denominator and clean control before reading a verdict.
- [ ] Hero trace actually contains the claimed contradiction and model-chosen follow-up. If not, change the narration; preserve the real trace.
- [ ] All held-out groups and freeze hash precede final evaluation. No training/calibration/discovery overlap; resume reuses committed inputs and validates stored output scores.
- [ ] Benign LoRA is discussed explicitly as a low-rank counterexample; no automatic malice claim derives solely from SVD/alignment.
- [ ] Current backend/UI tests pass and are reported as software verification only. Final training and real-run metrics are documented separately.
- [ ] Dashboard live stream, completed report download, busy/error state and replay label behave as expected. Local Nano absence is visibly labelled as rule-based specialist tools.
- [ ] Package only a completed real live run whose final completion event equals its report. Verify packaged file checksums and original source signature.
- [ ] Run the packaged replay with cloud credentials absent and trained weights unavailable; confirm it needs only installed dependencies and bundled files. Record the observed result before claiming this acceptance check passed.
- [ ] README/demo final run IDs, metrics, replay status and known limits match actual delivered artifacts. Remove pending placeholders only after verification.
- [ ] Inspect staged files for accidental secrets, `.env`, cached credentials, or unrelated preexisting files. Keep weights/cache/local run evidence gitignored; package only the explicitly intended real recording.

## Final result fields

| Item | Verified value |
|---|---|
| Final base run ID / verdict | Pending |
| Final benign run ID / verdict | Pending |
| Final poisoned run ID / verdict | Pending |
| Exact/paraphrase/clean canary counts | Pending final reports |
| Clean toy accuracy per artifact | Pending final reports |
| Hero contradiction/follow-up verified | Pending trace review |
| Bundled real replay source | Pending |
| No-key/no-weights replay verified | Pending |
| Software test command / result | `.venv/bin/python -m pytest -q` — 69 passed; software only |

Use [DEMO.md](DEMO.md) for operator steps and the judge narration; use [DECISIONS.md](DECISIONS.md) for choices, deviations, fixes and their reasons.
