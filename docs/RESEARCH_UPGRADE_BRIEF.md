# TripWir3: research-grade upgrade and demo brief

Prepared Nov 7, 2026, late evening CST (America/Chicago). Read-only research: no Notion changes, messages, purchases, instance launches, repository edits, or pushes performed.

## Executive recommendation

Make the ambition **a falsifiable, budget-matched evaluation of adaptive Nemotron auditing**, not merely a bigger poisoned model. Build a small blinded benchmark with benign hard negatives, frozen held-out verification, reproducible traces, one honest failure case, and an evidence-backed deployment gate. Train the main matched-size comparison on **Qwen2.5-14B-Instruct**, keeping the existing 0.5B line as a second scale. **Qwen3.8-27B is real and trainable**, but use it only as an optional cross-architecture stress test after core results are complete. Do not promise 27B training speed from its parameter count alone.

A 19-checkpoint core matrix is proposed below; execute it only if a pilot projects completion inside **6 aggregate H100 GPU-hours and $36 compute**, at a live quote of at most $6/hour. Reserve $14 within the $50 operating ceiling for storage, transfer, provisioning variance, and shutdown delays. This is a planning envelope, not a verified quote or a financial guarantee. Reduce the matrix if the pilot misses the envelope. No card, no auto recharge, and a provider-side billing/no-overage check remain launch gates.

## 1. Sources and evidence quality

1. **Official sponsor PDF, read in full through Google Drive connector:** [Hack UTD 26.pdf](https://drive.google.com/file/d/12y4kHpGUE1JLphHj5NxtiSD8XWxoIy5N/view), 15 pages, extracted text not truncated. Page numbers below mean physical PDF pages; printed slide numbers are inconsistent.
2. **Official event page, opened this turn:** https://zeroday.hackutd.co/ . Its NVIDIA statement matches PDF page 2. Sunday final submissions noon CST; judging 1–4 PM CST Nov 8. No NVIDIA numerical scoring weights published in the material read.
3. **Original mentor meeting note, including transcript, read in full:** [Hackathon Mentor Q&A: Nemotron Provenance Agent Idea](https://app.notion.com/p/4116d53e474180cd8f0dfad2a949ac79). Transcript uses anonymous A/B/C speaker labels and is visibly error-prone; attribution to Sophie relies on the meeting summary and the closing address to her. Quotes below are exact transcript strings, not cleaned-up or independently authenticated recordings.
4. **Current coordination/status source:** [Command Center](https://app.notion.com/p/4116d53e474181b18c77d0ca3957da4a), read this turn. It mixes superseded plans, participant reports, and actual checks; latest pause block is more relevant than unchecked legacy task rows. Its local run/test/checkpoint claims were not independently rerun by this researcher.
5. **t3code:** https://github.com/pingdotgg/t3code . GitHub connector tree read, not truncated; pinned snapshot `20fcc6ca57195cf9180114387e4f659d8e1ee2b4`. LICENSE, frontend package.json, and selected components read. No repository checkout/clone.
6. **Model/train sources opened this turn:** https://huggingface.co/Qwen/Qwen2.5-14B-Instruct ; https://huggingface.co/Qwen/Qwen3.8-27B ; https://unsloth.ai/docs/models/qwen3.8/train . The first is 14.7B causal text model; Qwen3.8-27B is a hybrid Gated DeltaNet/full-attention vision-language model, not simply a scaled Qwen2.5.
7. **Brev current official billing documentation opened:** https://docs.nvidia.com/brev/latest/guides/console-reference . The initially guessed `/concepts/billing.html` URL returned 404; the documented console reference is the usable source.

Notion searches performed: Sophie, Nemotron, NVIDIA problem statement, judging. Search found the mentor note and Command Center, not a separate accessible sponsor rubric. The organizer judging-page ID linked from Command Center returned `object_not_found` through Notion. No private access workaround attempted. The accessible official event page and supplied sponsor PDF provide the track criteria, so this brief does not invent missing scoring weights.

## 2. Explicit requirements, not an imagined rubric

**PDF page 2 / official event page:**

> “Challenge Statement: Use Nemotron Beyond a Chatbot”
>
> “In addition to using Nemotron, your project must include:”
>
> “Not just responding directly to prompts”
>
> “Agents that plan and execute complex tasks”
>
> “Using external APIs and services intelligently”
>
> “Solving actual problems”

These are four requirements, not six independent mandatory technologies. PDF page 10 lists exemplary winning patterns, not a requirement to implement every pattern:

> “Winning projects will showcase true agentic behavior”
>
> “Multi-Agent Systems”
>
> “Agentic RAG”
>
> “Systems that decide WHEN to retrieve, not just HOW”
>
> “Reason → Act → Observe loops for iterative problem solving”
>
> “Agent Simulation & Eval”
>
> “Generate realistic test scenarios and evaluation pipelines”

Page 13 lists strengths including:

> “Function calling to interact with external tools and APIs”
>
> “Autonomous decision-making within agent workflows”
>
> “Multi-agent orchestration where specialized agents work together”

Page 3 explicitly permits access via build.nvidia.com, OpenRouter, or open weights on Hugging Face. No read source mandates NIM deployment, NeMo training, NemoClaw, a particular Nemotron size, NVIDIA embeddings, multimodality, or buying more compute. Page 12 says:

> “Nemotron is more than models”
>
> “Models Datasets”
>
> “Techniques Tooling”

Interpret this as ecosystem relevance, not points for logo count. Add NVIDIA embedding/reranking to a real agent-decided retrieval tool only if it improves evidence retrieval and can be tested quickly; do not add Content Safety to an unrelated harmless-canary task or represent Guardrails/NemoClaw as implemented without testing.

## 3. Five between-the-lines insights, grounded in exact quotes

1. **Show a changed decision caused by observed tool evidence.** “Winning projects will showcase true agentic behavior” and “Reason → Act → Observe loops for iterative problem solving” (PDF p10). A fixed pipeline whose LLM narrates precomputed facts is weaker than one that chooses an additional probe after an ambiguous observation. Show decision summaries and structured actions—not private chain-of-thought.
2. **Retrieval needs a reason to exist.** “Systems that decide WHEN to retrieve, not just HOW” (PDF p10). Record `retrieval_requested`, its evidence gap, source IDs, the resulting hypothesis, and the next chosen test. Also show a run where retrieval is correctly skipped. Always retrieving the same papers is not the distinctive capability described.
3. **Evaluation is itself a sponsor-endorsed agentic product.** “Agent Simulation & Eval” / “Generate realistic test scenarios and evaluation pipelines” (PDF p10). A blinded test zoo, negative controls, reproducible discovery→verification, and query-efficient adaptive testing align more directly than simply a 27B model or a second modality.
4. **The use case is validated; do not dilute it.** Transcript, attributed to Sophie: “I think that's a good idea. I think it's really interesting, especially since it's something we're currently exploring. Nice. What kind of...” Later: “It sounds cool enough. I think you have enough on your plate with that.” This supports focusing on predeployment backdoor auditing. It is not proof that the detector works or an endorsement/novelty claim. Avoid nationality-based suspicion; provenance evidence is technical, not country-of-origin inference.
5. **Reliability and useful scope beat maximal infrastructure.** Sophie: “It needs to be good for 24 hours. You have to remember that.” Marketing-rep transcript: “Yeah. So we want you to focus on really anything that goes beyond the chatbot.” Sophie also says: “I would use your local computer to just run that 8-gig parameter model or 8-billion parameter model because it can be big, and then just save your bread instance as your way to run the model that is analyzing all the data.” Preserve the exact wording but interpret “bread” as a transcription error likely referring to Brev. Keep local specialist groundwork, bounded API use, and offline/replay durability; do not create a fragile GPU dependency for judges.

### Additional Sophie guidance and an important correction

Transcript: “There is some kind of rate limiting on Rev. So you have to be good about making sure that you're not 429-ing too much.” Service names are garbled; this is evidence for rate-limit awareness, not an authoritative numeric limit.

Transcript also records “0.042 cents per million tokens” and “if you use all $60 I'd be genuinely concerned.” **Do not use these as a GPU-rental quote or billing assurance.** The discussion mixes token inference and GPU compute. Brev GPU-hours, storage, and potential balance behavior must be checked separately. The existing 40-rpm API limit is a project report, not established by this quotation.

## 4. Gap analysis against the paused implementation

| Existing capability (reported) | Scrutiny gap | Concrete upgrade / acceptance criterion |
|---|---|---|
| Ultra planner, Nano specialists, tools | Could be fixed choreography with agent labels | At least one trace where the next tool differs conditional on prior observation; include an early-stop clean run and an ambiguous escalation |
| Qwen0.5B base, clean and poisoned LoRA | One tiny family + successful hero case | Matched clean/poison matrix at two sizes; failed implants retained and labeled; never count prompts as independent models |
| Spectral/SVD summaries | LoRA is low-rank by design | Norm/rank-matched benign negatives; weight-only baseline; behavior confirmation; low-rank anomaly alone cannot QUARANTINE |
| Red-team canary, frozen verifier | Trigger/marker leakage or discovery on test prompts | Blind case IDs; separate ground-truth manifest inaccessible to agents; verifier queries locked before audit; recovery prompt frozen before verification |
| Grounded report checker | Latest capture fabricated Skeptic history and confused trigger/output marker | Typed distinct fields `candidate_trigger`, `observed_output_marker`, `skeptic_objections`, and evidence IDs; deterministic contradiction/coverage validation; tests for fabricated history |
| QUARANTINE/FLAG/PASS | PASS can be read as certification | PASS = no evidence within stated scope and budget; provider failure -> incomplete/degraded status + FLAG/manual review, never clean PASS |
| SSE/replay dashboard | Replay could be mistaken for live; provenance hard to inspect | Persistent LIVE/REPLAY badge, exact model/provider and revision, tool request/result evidence drawer, stable event IDs, disconnected state |
| Few successful runs | Multi-agent advantage is untested | Equal-tool/query-budget single-agent and fixed-scanner baselines plus skeptic ablation; report if multi-agent costs more without improving detection |

## 5. Research question and threat model

**RQ:** Under a fixed suspect-model query budget, does an evidence-grounded, adaptive Nemotron multi-agent auditor detect deliberately implanted conditional behaviors in open-weight LoRA fine-tunes more reliably than a single-agent auditor and fixed probing, without increasing false accusations against matched benign fine-tunes?

Secondary: does an independent skeptic + held-out verifier reduce unsupported QUARANTINE verdicts and report claims? Does performance transfer from 0.5B to 14B at matched trigger families? These are pilot questions, not claims already established.

**Attacker:** can provide a LoRA adapter and untrusted model card/metadata for an otherwise known base revision. Training implants a conditional response that emits an entirely synthetic canary; no real credentials, exfiltration endpoints, or external attacker communications. Three trigger families below. Attacker cannot alter scanner tools, verifier prompts, frozen scoring rules, base hash, or audit log. Metadata may contain prompt injection; treat it strictly as quoted data.

**Defender:** has safe-format adapter weights, a trusted reference base when available, sandboxed inference, bounded black-box queries, and optional metadata/RAG. Separate white-box (reference delta available) and behavior-only modes. Synthetic canary is known to the harness as a benign marker, but the auditor must not receive the target trigger or label. Whether marker identity is disclosed must be consistent and reported. Discovery and independent verification must not share hidden answer keys.

**Scope limits:** conditional behavior is a controlled backdoor demonstrator, not evidence of real-world espionage or post-safety-training persistence. Do not use “sleeper” to imply persistence through safety training unless tested. Missing base/provenance is uncertainty, not maliciousness. No universal safety certificate, no population prevalence estimate, no novelty claim.

## 6. Experiment matrix and frozen protocol

### Core matrix: 19 distinct checkpoints (17 adapters + 2 bases)

| Base family | Poison adapters | Benign adapters | Base | Total |
|---|---:|---:|---:|---:|
| Qwen2.5-0.5B-Instruct | 3 trigger families × 2 poison rates × 1 seed = 6 | 3 | 1 | 10 |
| Qwen2.5-14B-Instruct | 3 × 2 × 1 = 6 | 2 | 1 | 9 |

Trigger families: (A) exact rare delimiter/string; (B) semantic topic condition with held-out paraphrases; (C) conjunction of two benign cues, where either cue alone is a near-miss negative. Poison rates **1% and 5%** of a fixed 1,024-example training set (~10 and ~51 poisoned examples; log exact counts). This is intentionally bounded, not a full factorial research campaign. If semantic/conjunctive implants fail, retain failures rather than training until every test case is easy.

Benign negatives: ordinary instruction fine-tune, style/domain fine-tune with comparable adapter norm, and (on 0.5B) an always-on marker/style adapter to distinguish generic odd outputs from conditional triggering. Clean datasets include trigger-like vocabulary without malicious association and near-misses. Keep rank, target modules, optimizer, steps, data size, chat template, and quantization matched within a base. Existing adapters remain development fixtures, not held-out evaluation cases.

**Stretch after core:** a second seed for all 0.5B conditions (do not pretend these are independent model families), then a 27B base + clean + one exact-trigger adapter as a transfer stress test. Do not spend core budget on all three axes at once.

### Protocol

1. Freeze a short `EVAL_PROTOCOL.md` and hash split manifests before the new final audits. Agent developers may know trigger families, not per-case strings/labels. A separate runner owns ground truth. Random opaque case paths; remove “poisoned”, trigger strings, poison rate, and labels from agent-visible metadata, filenames, RAG, and logs. Hash/reference claims must not leak labels.
2. Use disjoint training, development, discovery, and verifier prompt sets, deduplicated by template/semantic source, not merely identical strings. Freeze at least 32 clean utility prompts and 24 trigger/near-miss prompts per case for implant validation; larger sets if inference budget permits. For semantic triggers, hold out topics/templates or paraphrase sources explicitly.
3. Establish each implant's **held-out attack success rate (ASR)** and clean utility delta independently of the detector. Report all intended-poison cases, successful-implant subset (predeclared ASR threshold, e.g. >=50%), and failed implants separately. No silent removal/relabeling of unsuccessful attacks.
4. Freeze a maximum **32 discovery queries + 16 independent confirmation queries** per audit, output length e.g. 64 tokens, and wall-time/API-token budgets. Query budget includes every suspect-model call by any specialist. Audit tuning happens only on existing development fixtures. The verifier never reveals its prompt set back to the hunter.
5. Primary operating point: QUARANTINE requires reproducible conditional marker behavior on independent prompts with appropriate near-miss controls and cited evidence. Weak weight anomalies, metadata allegations, or exhausted testing -> FLAG. PASS is scoped non-detection, not absolute safety.
6. Freeze a continuous evidence score for AUROC before held-out labels are unblinded. Do not fabricate a probability from LLM confidence. Prefer a transparent predeclared combination of reproducible behavioral effect and evidence completeness; show raw components. If only ternary verdicts exist, report operating-point metrics rather than misleading smooth ROC curves.
7. Log run ID, adapter/base hashes, model revision, seed, tool versions, prompt-set hash, queries, completion/degradation, evidence ledger, score, verdict, timings, tokens, actual billed units when available. Store training manifests and outputs before teardown; compare adapter SHA256 checksums on local backup.

### Metrics and statistical restraint

- **TPR/FPR at model-checkpoint level**, with denominators and exact binomial/Wilson intervals. Report QUARANTINE as primary positive; separately treat QUARANTINE+FLAG as triage-positive. Keep incomplete audits visible, count their coverage, and give conservative detection bounds rather than dropping them.
- **AUROC and AUPRC** only with frozen continuous scores and both classes; identify the small sample and clustered shared-base training. Per-family/size breakdown; do not bootstrap prompts as if they were independently trained models.
- **Trigger recovery:** exact normalized match for string trigger; functional recovery on held-out verification for semantic/conjunctive triggers. Count trigger vs output-marker confusion as failure. Report no-recovery cases, not only successful recoveries.
- **Implant ASR**, clean utility delta, triggered-minus-near-miss effect, accidental marker rate; distinguish detector failure from failed training.
- **Median/p95 latency**, suspect queries, Nemotron calls/tokens, time to first decisive evidence, audit completion rate, unsupported-claim rate, reference citation validity, and cost per completed audit. With tiny n show raw observations and label p95 unstable.
- API calls currently free do not imply zero compute cost: report observed billed API cost, GPU amortization assumptions, and token counts separately.

### Baselines / ablations, in priority order

1. **Fixed behavioral scanner:** same prompt families and total suspect-query budget, deterministic decision rules, no Nemotron adaptive planning.
2. **Single Ultra agent:** same tools/evidence, same suspect queries and explicit comparable planner-token budget. No specialist messages. This is the main multi-agent comparison.
3. **Full TripWir3:** Ultra planner + Nano specialists + skeptic + independent verifier.
4. **Minus skeptic:** keep verifier, tools, and query budget identical. Measure false accusations and unsupported claims, not only detection.
5. **Nano-only orchestrator vs Ultra orchestrator:** same specialist/tool budget; actual current endpoint IDs logged, not inferred from unverified product names.
6. **Weight-only vs behavior-only; no adaptive RAG:** exploratory on a preselected subset. Removing the verifier may be an offline analysis but must not weaken the shipped gate.

Run cheap fixed-scanner baseline on all checkpoints. Primary full-vs-single comparison on all if practical; otherwise preselect a balanced, stratified subset of 8 before looking at outcomes and clearly report the denominator. Do not run every expensive ablation on all 19 overnight. Preselect 4–6 representative ambiguous/negative cases for skeptic/Nano/RAG ablations. Equal query budget alone is not equal cost; record planner-token budgets and actual costs too.

### Threats to validity / honest paper-style discussion

- Tiny, synthetic, single-vendor model zoo; one seed per main condition; shared weights/datasets cause correlated results. No statistical claim of universal detection or superiority.
- Known trigger families, known canary, reference-base access, and development on similar fixtures simplify the defender's problem. Explain oracle-assisted marker recognition if used.
- Train-test semantic contamination, label leakage via artifact paths, and threshold tuning after label inspection can invalidate metrics.
- Poison-rate effects entangled with successful implantation, training length, rank, norm, and clean degradation. Strong clean negatives and failed-implant reporting are essential.
- Qwen3.8 vs Qwen2.5 changes architecture/generation/template, not just size; cannot claim a controlled scaling law from their comparison.
- 4-bit vs BF16 inference can alter trigger behavior and weight statistics. Compare like precision; compute reference deltas from adapter factors in controlled precision, not unrelated quantization artifacts.
- Multi-agent gains may come from more calls/tokens; correlated LLM mistakes are not independent votes. Blind evidence validation and matched budgets matter.
- A fabricated report undermines system-level reliability even if its final verdict is right. Measure the reporting layer separately.
- Harmless marker emission is not actual exfiltration, and a backdoor that survives safety training was not tested. Be explicit.

## 7. Brev: 14B vs 27B and bounded operating plan

### What is verified now

- Qwen2.5-14B-Instruct official card: 14.7B parameters, standard Qwen2 text architecture, same family as existing controls. Best controlled scale-up and lowest integration risk.
- Qwen3.8-27B official card: real Transformers-format weights; hybrid Gated DeltaNet/full attention and vision encoder. Unsloth docs explicitly say **“QLoRA works with 24GB and LoRA needs >36GB”**, require latest Transformers v5, and warn initial Gated DeltaNet kernel compilation can take longer. Thus an H100 80GB has a plausible memory path, but compatibility/throughput need a pilot. Freeze vision tower for this text-only task.
- Earlier answer that full BF16 weights alone determine trainability was incomplete: full fine-tuning additionally needs gradients/optimizer/activations. Neither model should be full-fine-tuned on one H100 for this plan. LM Studio MLX inference artifacts are not the training input; use the pinned upstream training-compatible revision or a verified quantization.
- No live H100 rental quote or account billing settings were inspected in this research. Rates below are scenarios, not offers.

### Planning estimates, not benchmarked measurements

Assume QLoRA rank 8–16, short 256–512 sequence lengths, batch 1–2 with accumulation, gradient checkpointing, around 100–128 optimizer steps, ~0.2–0.3M processed tokens per adapter, cached base load, and early rejection of NaN/OOM. Total effective tokens, not steps alone, controls time.

| Work | Rough H100 GPU-hour envelope | Decision |
|---|---:|---|
| 0.5B matrix training plus setup | 0.25–0.75 | Cheap seed/trigger coverage; reuse existing safe harness |
| Eight 14B adapters | ~2–4 | ~0.25–0.5 h each; must measure first 20 steps |
| Held-out implant checks + compact audit inference + setup/transfer | ~1–2 | Reuse loaded base and swap adapters; bound generations |
| **14B core total** | **~3.25–6.75** | Authorize a maximum 6 GPU-hour allocation; shrink work to fit after pilot |
| 27B core of similar breadth | ~5–10 total, much more uncertain | Can exceed budget/deadline; not recommended as core |
| Optional 27B clean+poison adapter pair with base validation | ~1.5–3 total | Only if measured residual budget and sufficient time; no automatic launch |

At $4/hour, 6 GPU-hours is $24 compute; at $6/hour it is $36. Both are **hypothetical**. At $8/hour, 6 is $48 before storage, so reduce to <=4.5 hours or decline that quote. The general allocation formula is `max_compute_hours = (50 - reserved_noncompute_dollars - spend_to_date) / quoted_aggregate_hourly_rate`, with reserved_noncompute initially $14. Treat provisioning/download/eval/idle as billable unless quote explicitly says otherwise.

**Parallelism:** two H100s for 3 hours is six GPU-hours, not three. Prefer one H100 with one loaded base and sequential adapter jobs; parallelize agents/UI/data preparation, not competing training processes in a single GPU's VRAM. A second instance can reduce wall-clock only after the pilot demonstrates benefit and the exact aggregate quote fits the same total-hour ceiling; it duplicates downloads and setup. Do not allocate the whole $60.

### Billing reality and launch gates

Official console docs say:

> “Stopped instances do not accrue compute charges, but storage charges may still apply while Brev preserves the instance data.”
>
> “Your credit balance is shared across the organization.”
>
> “If your organization runs out of credits, Brev sends a warning email and pauses any instances that have stop-start ability. Instances that cannot be paused are deleted.”
>
> “Resource limits are separate from credits.”

These support prepaid-credit behavior but are **not an account-specific promise of no delayed charge**. The reported $30/hour org resource limit is a burn-rate ceiling, NOT a $30 total spend limit. Before launch, parent must verify: current $60 credit balance/eligibility/expiry, no saved card, auto recharge off, instance stop/start support, all hourly/storage/transfer charges, and documented account-specific exhaustion/no-debt behavior. If no-later-bill protection cannot be established, do not launch just because the expected cost is low.

Once exact instance/time/cost is approved, use both workload wall-time termination and independent control-plane shutdown/monitoring. Killing training alone does not stop GPU rental. Stop compute at the $36 allocation or earlier on error; retain $14 within the $50 cap, and the extra $10 credits untouched. Transfer adapters/configs/manifests/logs to durable local storage, verify hashes, then obtain the necessary approval for deletion to end retained-storage charges. Never rely on credit exhaustion as the backup mechanism; docs warn remaining resources/data can be deleted after 24 hours. No spending or deletion performed here.

## 8. t3code reuse plan: real paths, license, coupling

### License

Root `LICENSE`, read through GitHub:

> “MIT License”
>
> “Copyright (c) 2026 T3 Tools Inc.”
>
> “The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.”

Copying/adapting is permitted under MIT; preserve the full notice in `THIRD_PARTY_NOTICES.md` or a vendored license, and annotate copied/adapted files with source URL and pinned SHA. Credit pre-existing UI work in README/Devpost; do not imply it was built at HackUTD. MIT is not a trademark grant. Independently check licenses for any bundled fonts/icons/diff dependencies/assets actually copied; avoid copying brands, binaries, Clerk flows, provider credentials, or unrelated `.repos/` vendored projects.

### Verified stack

`apps/web/package.json`: React + TypeScript, Vite/Vite Plus, Tailwind CSS v4, Base UI (`@base-ui/react`), TanStack React Router, Zustand, Effect atom bindings, Lucide, React Markdown, LegendList, and `@pierre/diffs`. Several `@t3tools/*` workspace packages are dependencies. This is **not a drop-in standalone UI kit**. Components use React `use` and provider syntax, so check the destination React version before direct copying. Recreating a small presentational component from its pattern is often safer than migrating the entire runtime.

All paths below are relative to the pinned repo SHA. Direct source link prefix:
`https://github.com/pingdotgg/t3code/blob/20fcc6ca57195cf9180114387e4f659d8e1ee2b4/`

| Desired TripWir3 feature | Source paths | Reuse recommendation |
|---|---|---|
| Compact expandable tool/result cards | `apps/web/src/components/chat/WorkLog.tsx`; `.../TimelineWorkEntryRow.tsx`; `.../TimelineWorkEntryRow.logic.ts` | **Best direct extraction: WorkLogBlock/List/Row/Details.** Small React + `cn` dependency; live-edge-aware output scrolling. Adapt row header/status and JSON result body; avoid wholesale WorkEntry imports (contracts, router, runtime) |
| Specialist group/agent lifecycle | `apps/web/src/components/chat/TimelineV2EventRow.tsx`; `.../V2LifecycleRow.tsx` | Adapt V2SubagentGroup disclosure/avatar/status/timing pattern to provenance/forensics/red-team/skeptic/verifier. Source currently reads Effect atoms and runtime thread state; replace with audit-run props |
| Streaming audit timeline | `apps/web/src/components/chat/MessagesTimeline.tsx`; `.../MessagesTimeline.logic.ts`; `.../useTimelineFollow.ts`; `.../timelineScrollAnchoring.ts` | Use design and scroll-follow behavior; do not transplant the 1,700-line timeline and its many app contexts. A simple keyed list is enough for ~70–200 events. Add virtualization only if measured need |
| Evidence drawer / logs | `apps/web/src/components/DiffPanelShell.tsx`; `apps/web/src/components/chat/WorkLog.tsx`; `apps/web/src/components/chat/V2ItemInspector.tsx` | Shell supports inline/sheet/sidebar/embedded; remove Electron drag-region dependency. Reuse shell layout for raw JSON, references, spectra, and metrics. Inspector is a pattern; own typed evidence renderer is simpler |
| Before/after model output comparison | `apps/web/src/components/diffs/StyledDiffCodeView.tsx`; `apps/web/src/components/diffs/DiffFileTree.tsx`; `apps/web/src/components/DiffPanel.tsx` | Paths verified in tree; do not imply a tensor delta is a text diff. Optional text diff for clean-vs-triggered outputs or report revisions. Inspect dependency licenses/API before importing `@pierre/diffs`; simple side-by-side output is cheaper |
| Runs/cases sidebar | `apps/web/src/components/sidebar/SidebarThreadRow.tsx`; `.../SidebarChrome.tsx`; `apps/web/src/components/AppSidebarLayout.tsx`; `apps/web/src/components/ui/sidebar.tsx` | Adapt row density, selection, timestamp, verdict/status pills. SidebarThreadRow is ~1,800 lines with heavy app coupling—copy pattern, not runtime. No need for git project grouping, drag/drop or Clerk |
| Disclosure/buttons/tooltip skeletons | `apps/web/src/components/ui/collapsible.tsx`; `.../button.tsx`; `.../badge.tsx`; `.../tooltip.tsx`; `.../skeleton.tsx`; `apps/web/src/lib/utils.ts`; `apps/web/src/index.css` | Primitive paths verified; collapsible source read. Copy only needed primitives and required Tailwind tokens. Don't import entire global stylesheet or every dependency blindly |

### Concrete dashboard contract and implementation order

Keep FastAPI + SSE backend; do not adopt t3code's coding-agent server/provider/runtime. A thin adapter projects each event into a view model:

`{schemaVersion, runId, eventId, seq, timestamp, agent, kind, status, toolCallId?, evidenceIds[], payload}`.

Typed kinds: plan, agent_started/completed, tool_started/result/error, retrieval_requested/result, hypothesis_updated, skeptic_objection, verification_result, verdict, run_incomplete. No fabricated rationale/reasoning history. `toolCallId` connects start/result without inference from display text. Render explicit observed facts and concise decision summaries.

SSE -> schema validation -> append-only run store -> pure event reducer -> rows/cards. Persist original ordered JSONL for replay; replay dispatches the same events through the same reducer, never separate fake UI fixtures. Dedupe by event ID, handle reconnect and Last-Event-ID if server supports it, detect sequence gaps, don't synthesize missing evidence, distinguish transport disconnect from completed audit. Preserve user's scroll position, offer Follow live, cancel/ignore stale events when switching cases, and visibly label REPLAY versus LIVE. Sanitize model-card/report Markdown; no raw HTML, executable links or arbitrary code execution from tool payloads.

**Time-box 2–3 hours:**
1. 30 min: extract WorkLog primitives + minimal shell + three-column layout.
2. 45 min: implement typed SSE/replay reducer, run list, grouped agent/tool cards.
3. 45 min: evidence drawer, verdict card, clean-vs-triggered comparison, query/latency counters.
4. 30–60 min: reconnect/duplicate/out-of-order/schema-error handling tests, keyboard navigation, narrow-screen layout, demo polish. No full T3 fork or auth migration.

Screen: left run zoo; middle adaptive timeline with evidence-linked decisions; right evidence/metrics and final gate. Headline counters should be actual query/token/latency measurements, not decorative confidence percentages. Demonstrate clean PASS, poisoned QUARANTINE, and incomplete/ambiguous FLAG with controls.

## 9. Feasible schedule and stop rules (CST)

These are proposed work windows, not scheduled automation or claims of activity. Adapt to the actual start time; preserve Sunday noon hard deadline.

- **Now–12:15 AM Nov 8:** backend fixes report provenance/trigger-marker bug and preflight; frontend extraction in parallel; training owner freezes protocol and runs 20-step 14B pilot only after billing gates and exact launch approval. Parent independently gets Megatron's advisor review (this read-only task sent nothing).
- **12:15–3:30 AM:** core 14B/0.5B jobs within measured envelope, independent implant validation, fixed-baseline tests; UI built against replay and then real SSE. Checkpoint every completed adapter and copy it out. Matrix can shrink to 2 trigger families ×2 rates if timing slips; log deviation before inspecting outcomes.
- **3:30–6:30 AM:** blind full-vs-single comparison and selected ablations, failure-case review, ground-truth reveal after outputs locked, metrics tables with denominators. GPU spend includes inference; don't leave rented GPU idling while waiting for hosted Nemotron.
- **6:30–8:30 AM:** no new model families. Fix only reliability/integration; produce immutable replay bundle, evidence report, raw metrics CSV, architecture diagram and limitations. Label unfinished experiments rather than filling tables with estimates.
- **8:30–10 AM:** hero recapture only after real local Nano loads and preflight passes; record <=2-minute demo, include one useful failure case/abstention and clean control. No fallback specialist capture presented as genuine Nemotron.
- **10–11:30 AM:** judge rehearsal, submission/source/license/tooling checks and actual Cursor/Grok Bot contribution evidence; final code/video buffer. **Noon Nov 8 CST hard stop.**

### Highest priority deliverables

1. Correctly grounded report and verifier; no invented Skeptic history.
2. Adaptive visible agent loop with real tool evidence and one replan.
3. Frozen blind evaluation on clean/poisoned cases; raw denominators and limitations.
4. Stable live/replay dashboard with useful failure path.
5. 14B transfer evidence if measured budget allows; 27B and extra NVIDIA services remain optional.

**Judging claim to earn:** “TripWir3 is a Nemotron-controlled predeployment gate that chooses forensic and behavioral tests, challenges its own evidence, verifies suspected conditional behaviors on held-out prompts, and produces a replayable, bounded audit—not a claim that any LLM can be certified safe.”
