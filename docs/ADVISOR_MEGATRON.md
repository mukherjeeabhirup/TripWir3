# Megatron advisor input (11:22 PM, 11:33 PM and 11:39 PM CST, Nov 7)
Advisor proposals, not verified results. No prices or training results verified.

## 1. Research question and threat model
Can an agentic auditor, under a fixed query budget and with access to a trusted base and a third-party LoRA adapter, produce a reproducible, evidence-supported finding of trigger-conditioned synthetic marker emission, while avoiding false alarms on benign adapters?
- Attacker controls adapter/training data, not trusted base, evaluator or held-out set. Harmless synthetic markers.
- Separate known-trigger verification from bounded unknown-trigger search.
- Blind adapter IDs; remove labels/trigger clues from auditor-visible filenames/metadata; keep a private ground-truth manifest.
- Model cards are untrusted evidence, not instructions.

## 2. Highest-value experiment before scale
- Freeze current base/benign/poisoned; verify adapter actually loaded; recover the 12 prompt/output pairs, split provenance, scoring.
- Count marker in generated completion only, not echoed prompt. Historical 12 = development set, not final test.
- New frozen set of ~50 task stems x 4 conditions (no trigger, exact trigger, matched benign string, preregistered near-match/position perturbation) x 3 models (base, benign, poisoned) = 600 short generations. Report marker rates, paired differences, clean-task score, failure/truncation counts.
- Ordinary benign adapter is not a benign-trigger-trained control; state if absent. Prompt holdout is not adapter holdout.
- 12/12 exact 95% binomial CI ~73.5-100% only under independent trials; 12/12 leakage is not detector recall.

## 3. Baselines and ablations
Cache one immutable evidence bundle. Compare with the same schema, evidence, token budget and rubric:
(i) deterministic fixed-probe/marker scorecard, (ii) one-pass Nemotron report on same evidence, (iii) full TripWir3, (iv) minus skeptic/verifier, (v) minus SVD + activation evidence.
Score supported vs unsupported claims, correct abstention, numeric accuracy, evidence links, time, cost.
With fixed evidence adaptive probing is off; evaluate adaptive selection separately vs fixed/random probing at equal query budget on frozen held-outs. Multiple prompts on one adapter are not independent model-level trials.

## 4. GPU and model choice
- Clarify 14B/27B = audited target (not auditor). LoRAs can't be transplanted across bases; target-scale comparison needs separate adapters.
- Pin exact Qwen checkpoint + revision; verify toolchain. Single H100 80GB QLoRA plausible at modest context/batch, not demonstrated.
- Pilot first: microbatch 1, 2K tokens, 10-20 warmup + 50-100 measured optimizer steps on real data; test long sequence and checkpoint save/reload. Capture non-padding tokens/sec, step time, peak VRAM, loss stability. Project cost from measured throughput plus download, idle, checkpoint, eval, storage. Keep 10-15% VRAM margin.
- Planning ceilings: $5 pilot, $15 evidence, $12 14B ablations, $8 matched 27B comparison, $10 reserve = $50 cap. Drop 27B first if it threatens the demo. Check balance, recharge/overage, backups first.

## 5. Research depth and NVIDIA fit
- Prioritize independent adapter/trigger families and blinded controls over paraphrases or raw scale. Freeze and document recipes; distinguish training seeds. Don't claim a poison-rate grid is optimal.
- Static spectral features = cheap baseline; LoRA rank itself is not evidence; compare vs benign specialist adapters. Refs: https://arxiv.org/abs/2602.15195, https://arxiv.org/abs/2605.30189
- Show an actual tool result causing a changed next test and an evidence-linked bounded decision. Honest outcome: controlled case study with reproducible evidence and ablations.

## 6. Falsification tests (11:33 PM)
- Metadata shortcut control: match benign/poisoned on recipe, rank, alpha, steps, file structure; group splits by parent training run; metadata-only classifier if enough adapters, else report metadata balance. Source: https://arxiv.org/html/2610.41713v1
- Separate known-trigger confirmation, seeded-candidate recovery, and genuinely blind bounded search; same query budget. Treat nonfunctional attacks as their own category. Source: https://arxiv.org/html/2607.26849v1
- Weight-norm signals weakened at 7B multi-seed; hold out whole training seeds; don't generalize thresholds across bases/recipes. https://arxiv.org/html/2605.30189v1

## 7. Presenting scale honestly (11:39 PM; relayed by starscream)

This is advisor input supplied by Abhirup, not measured performance or authorization for compute/spend. The research and evaluation plans adopt the following requirements, subject to their existing source, execution and spending gates.

1. **Size by audit capacity.** Choose the 14B zoo from measured end-to-end audit capacity before the approximately 06:00 code freeze, including evaluation, retries and verification buffers, rather than from how many adapters the GPU budget could train. Report each audited base separately (0.5B, 14B, optional 27B), with exact model/revision, adapter recipe/hash, hardware, context, quantization and number of independently trained adapters. A comparison that changes base family, recipe or precision is not a pure parameter-count scaling result.
2. **Separate quota arithmetic from capacity.** At an assumed 20 cloud requests per audit and an exclusively available 30 requests/minute bucket, `30 × 60 / 20 = 90 audits/hour` is a quota-only ceiling. It ignores other clients, retries, token limits, local inference, queueing and all other bottlenecks; it is not a throughput result. The relayed advice described approximately 196 local operations as Nano calls. **Repository correction:** historical 37dc records 196 Qwen target forwards/generations, 19 cloud attempts and three Nano specialist calls. The target runs locally; only the Nano specialists use LM Studio. Both local stages need timing before claiming which is the critical path. The project limiter is 30 rpm; the supplied account limit is approximately 40 rpm, not an independently verified account setting.
3. **Measure a small predefined concurrency sweep.** Use the same blinded job manifest at concurrency 1, 2 and 4, only after safe queue/state isolation is implemented and independently reviewed. Record submission-to-verdict time including queue, separate cold model-load and warm service time, completed audits/hour, failures, retries, role-specific calls/tokens and actual cost. Use median and range at small N, not p95. Stop increasing concurrency when throughput plateaus or errors rise; honor Retry-After. Unsupported or unrun levels remain missing.
4. **Separate engineering speedups from policy changes.** Batching local inference, pipelining local/remote work and deterministic preprocessing caches may be compared under unchanged audit policy, with no hidden-label leakage between cases. Fewer probes, early stopping and cheaper judges are distinct policy variants. Compare them with the full audit on held-out cases, retaining false negatives, false alarms and inconclusives.
5. **Separate cost components and denominators.** Report marginal API spend, local GPU time and one-time adapter training separately. Preserve raw spend, failed attempts and failure rate; report cost per completed audit meeting a prespecified quality bar. Unknown billed cost is unavailable, not zero. Declare amortization and include failed audits in the numerator for the scheduled workload.
6. **Use a bounded writeup.** “On N independently trained adapters, under these hardware, model and quota settings, we observed X completed audits/hour, median latency Y, cost Z and measured accuracy/abstention.” Fill only measured quantities, with sample sizes and failures. A few adapters support a feasibility case study; many prompt calls do not create many independent model-level trials.
