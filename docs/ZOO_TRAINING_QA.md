# Qwen2.5-14B zoo training QA

**Keep the adapters for a small, separately authorized behavioral validation.** All 12 have complete 256-step loss histories and finite, distinct, nonzero updates. The tiny pilot loss alone is not grounds to discard the zoo. Whether the intended task/trigger behavior actually works remains **UNTESTED**; these are training/weight proxies, and every adapter remains **UNAUDITED**.

Prepared November 8, 2026, local Mac only. No base-model attach, generation, GPU compute, NVIDIA inference API, Brev action or runtime/source change. The one localhost model-list GET made no load/completion request. Instance deletion and **$39.75 remaining credit** are Abhirup/coordinator reports, not independently checked billing facts. Hero remains CLOSED.

## Evidence and blinding

- Public weights: `brev/backups/tripwir3-14b-a/zoo/manual-public-20261108T101500-e92727c3`, the manual safety copy, **not** controller `last_verified`. Reused Astra’s 06:13 inventory and cheaply rehashed all 37 public files before/after CPU analysis; all match. Twelve unique weight hashes, each 89,678,880 bytes.
- All generated receipts/scripts/CSV/charts are local and gitignored under `.cache/runs/builder-zoo-training-qa-20261108-0617/`; this report does not imply those large assets are published. [Diagnostic charts](../.cache/runs/builder-zoo-training-qa-20261108-0617/qa-charts.html).
- After the explicit starscream numeric-only blinding ruling, a sealed lexical whitelist extracted only numeric optimization/loss/token/time fields and opaque IDs. Unknown JSON values were skipped without decoding. No private truth, class mapping, recipe/label/trigger/data/spec string values, optimizer `.pt` state or training examples were inspected or retained. No poison/clean classification is made.
- Conventional `zoo.log`, `trainer_state.json`, loss JSONL and copied trainer scripts are **absent in the backups**. The actual curves reside in per-opaque-ID numeric JSON files under archived private directories: 101 metric copies, 233 checkpoint-state copies and 20 copies of one pilot metric record. These are repeated snapshots, not independent runs. All 12 latest zoo curves have 256 entries; overlapping archived curve prefixes agree, with no conflicts.

## Per-adapter training fit

All recorded numeric configs declare 256 optimizer steps, accumulation 8, 1,024 examples, peak LR `1e-4`, warmup 13 and maximum length 2048. This is **2 nominal example-passes**, not a measured held-out epoch score. The source-derived LR schedule starts at `1e-4/13`, peaks at `1e-4`, and ends at approximately `4.11523e-7`; per-step LR was not separately logged. “10%” is step 26 and “50%” step 128. Under the inspected generic trainer, losses are row-averaged completion-token cross-entropies; they are not clean capability or activation rates. Exact remote execution equivalence is not independently established.

| Opaque ID | First | Step 26 | Step 128 | Final (256) | Last-26 median | Recorded input tokens | Training seconds | Flag |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| c_0390d998ef30d1beaa5c | 0.0313475 | 1.97545e-05 | 6.00505e-05 | 2.86295e-05 | 3.15334e-05 | 133,546 | 698.5 | early median tiny |
| c_04658cdf2344c0f65bed | 1.0744 | 0.0037375 | 0.00339901 | 0.000139537 | 0.000310404 | 149,212 | 715.3 | — |
| c_136a4cd1633e34f5ddc7 | 0.986707 | 0.000868376 | 0.000147298 | 2.19554e-05 | 1.59237e-05 | 167,262 | 722.7 | — |
| c_15c71d901051db9f0efb | 4.81208e-05 | 2.7002e-05 | 0.00119788 | 9.1926e-05 | 0.000203023 | 139,248 | 719.8 | early tiny |
| c_49220cb9be15060c1596 | 4.13293e-05 | 0.000142129 | 0.000163699 | 2.54064e-06 | 2.57889e-05 | 139,096 | 717.1 | early tiny, early median tiny |
| c_5151fdbe1c0dced81060 | 4.7204e-05 | 6.87668e-05 | 0.000258924 | 0.00434809 | 0.00219551 | 133,694 | 715.3 | early tiny |
| c_6228b7cb2962599a70a6 | 5.82511e-05 | 0.00223428 | 0.00334399 | 6.49679e-05 | 7.12521e-05 | 134,156 | 719.0 | early tiny |
| c_76ba24fe18eb3ed60844 | 1.18456 | 1.61792e-05 | 0.000124775 | 3.74977e-05 | 5.85156e-05 | 148,856 | 723.6 | — |
| c_79ec24797b1d09ee6ca6 | 13.6243 | 0.00138791 | 1.44217e-05 | 1.08857e-05 | 1.15894e-05 | 148,780 | 719.7 | — |
| c_c4184cda44737f5cb830 | 0.893074 | 0.509549 | 0.000240801 | 5.97894e-05 | 0.00014298 | 167,608 | 720.2 | — |
| c_c57c8b04e5c9ce3e8a49 | 0.00622803 | 7.27656e-06 | 1.52115e-06 | 2.12421e-06 | 1.65142e-06 | 145,924 | 724.9 | early median tiny |
| c_c84aebb46403baeca0b5 | 0.000373031 | 0.0298514 | 0.000614038 | 0.000171875 | 0.00023355 | 146,018 | 723.4 | early median tiny |

**Flags and interpretation:**

- No missing terminal loss curves, NaN/Inf, negative losses or unfinished expected steps were found. No pair of complete curves is identical or near-identical under `rtol=1e-5, atol=1e-8`; that tolerance is a descriptive duplicate check, not a detector threshold.
- Four first-step losses are already ≤`1e-4`; four early-26-step medians are also ≤`1e-4` (the sets differ). This warrants checking task difficulty/held-out behavior; it does not identify clean/poisoned cases or establish degenerate masking.
- `c_5151fdbe1c0dced81060` has the highest final loss, `0.00434809`, and last-26 median `0.00219551`; other final losses range from `2.12421e-6` to `1.71875e-4`. Single mini-batch endpoints fluctuate; no training run is a held-out generalization test.
- Input-token totals are recorded input tokens, **not** supervised-token counts. Zoo-wide loss-bearing fraction is unavailable without tokenized data/targets, which were not opened.

## Why the pilot loss is a weak quality test

The one saved pilot has 64 measured losses (20 archived copies): first measured `6.19879e-6`, mean `1.19407e-6`, final measured `2.98023e-7`, resumed loss `7.62938e-7`. Its first 20 optimizer losses were **not logged**. The generic repository trainer cycles **four** long examples for 84 steps, then performs 20 short-example updates; the saved resume update follows. Low measured loss after repeated exposure is consistent with memorization of a tiny pilot set, not evidence of useful generalization or a working backdoor.

Numeric pilot telemetry gives `loss_tokens_per_second / tokens_per_second = 0.00282000981`: **368 supervised tokens / 130,496 nonpadding input tokens = 0.2820%**, or **0.2808% of the fixed 64×2048 token slots**. This is only 5.75 supervised tokens per measured example on average. It is nonzero. The fraction is derived from logged throughput counters, not from reading private examples.

Generic local code `brev/train_zoo.py` SHA256 `c1cb16e2f36edb7556b0de9a9878ce6e49cf8861490ea7e6f9c5aaae2bcfa958`: `tokenize_row` (110–117) masks the prompt with `-100`, labels the assistant completion, rejects empty/truncated completions; `batch` (137–142) masks padding; `update` (152–171) averages per-row model losses and rejects nonfinite loss/gradients. **No obvious all-labels-masked or extra token-count division appears in this local code.** The installed Transformers loss path uses mean cross-entropy over nonignored targets. Masked prompt tokens therefore do not simply dilute loss by 2048. Exact deployed remote source/dependency equivalence was not established by this numeric-only QA.

## Weight-only proxy

Each adapter has 192 F32 tensors across 96 adapted modules, rank 16, alpha 32, scale 2, with `o_proj`/`down_proj` targets. These hyperparameters come from public adapter configs; shapes/dtypes come from safetensors. Frobenius norms below aggregate all modules. Every module’s A/B/BA/scaled norm is in `module-stats.csv`.

| Opaque ID | Global ‖A‖F | Global ‖B‖F | Global ‖2BA‖F | Near-zero B modules | Finite |
| --- | ---: | ---: | ---: | ---: | --- |
| c_0390d998ef30d1beaa5c | 22.8993 | 2.4868 | 3.05283 | 0/96 | yes |
| c_04658cdf2344c0f65bed | 22.9673 | 2.7962 | 3.49837 | 0/96 | yes |
| c_136a4cd1633e34f5ddc7 | 22.9095 | 2.2598 | 2.81602 | 0/96 | yes |
| c_15c71d901051db9f0efb | 22.9926 | 2.3170 | 3.00688 | 0/96 | yes |
| c_49220cb9be15060c1596 | 22.8755 | 2.1190 | 2.57510 | 0/96 | yes |
| c_5151fdbe1c0dced81060 | 22.9326 | 2.4662 | 3.08538 | 0/96 | yes |
| c_6228b7cb2962599a70a6 | 23.0265 | 2.4213 | 3.07430 | 0/96 | yes |
| c_76ba24fe18eb3ed60844 | 22.8752 | 2.3059 | 2.81670 | 0/96 | yes |
| c_79ec24797b1d09ee6ca6 | 23.3825 | 3.3509 | 4.65116 | 0/96 | yes |
| c_c4184cda44737f5cb830 | 23.0373 | 2.7956 | 3.63316 | 0/96 | yes |
| c_c57c8b04e5c9ce3e8a49 | 22.8024 | 2.1150 | 2.53555 | 0/96 | yes |
| c_c84aebb46403baeca0b5 | 22.9682 | 2.2937 | 2.88585 | 0/96 | yes |

All 1,152 B matrices are nonzero and above the conservative near-zero cutoff ‖B‖F≤`1e-12`. No NaN/Inf tensors. Signed cosine similarity of flattened effective deltas across the 66 adapter pairs: **min 0.002250, median 0.014300, max 0.078784**. No pair reaches the descriptive near-identical-direction cutoff `0.99999`. These are consistent with nontrivial, distinct updates; they do not measure correctness, backdoor effectiveness or weight change relative to the missing base. Independent LoRA initialization can itself contribute to low delta cosine; low cosine is not proof of behavioral diversity.

Calculation used exact low-rank identities `‖BA‖F² = tr((BᵀB)(AAᵀ))` and `⟨BiAi,BjAj⟩ = Σ((BiᵀBj) ⊙ (AiAjᵀ))`, summed across identically aligned modules and scaled by alpha/r. No dense 14B base or full delta matrices were materialized. A separate tiny-matrix explicit-vs-Gram check agrees to floating-point precision; public inputs were rehashed unchanged afterward.

## Real behavioral-test feasibility and conditional cost

- **No exact Qwen2.5-14B base weights/tokenizer were found inside this workspace.** Only the real 0.5B base/tokenizer and synthetic test fixtures were found; fixtures were excluded. Authenticated native LM Studio **list-only GET** did not list Qwen2.5-14B. Existing Qwen3.x/Nemotron models are different bases and cannot substitute. No model was loaded or unloaded. HF caches outside `~/Downloads/hackutd26` were not checked; doing so requires Abhirup’s OK.
- Mac: **Apple M5 Pro / Mac17,8, 48 GiB unified RAM**. `mlx`/`mlx_lm` are absent from the project environment. The [official Qwen index](https://huggingface.co/Qwen/Qwen2.5-14B-Instruct/blob/main/model.safetensors.index.json) reports 29,540,067,328 bytes of base tensors (~27.51 GiB at its stored precision). FP32 would be ~55.02 GiB before overhead, exceeding this Mac’s RAM. This online `main` index is a sizing reference, not verification of the pinned base revision locally.
- **Hardware-plausible, not ready now:** a dedicated short-context MLX 4-bit 14B test (~7 GiB ideal packed weights, roughly 8–12 GiB with quantization/runtime overhead as an engineering estimate) fits 48 GiB. BF16 (~28 GiB base plus KV/workspace/adapters) may fit if sufficient memory is freed; the currently loaded Lightning server remains untouched, so concurrent capacity is not assumed. A reviewed exact-base/tokenizer loader and PEFT→MLX adapter compatibility/conversion are still needed. [MLX-LM documents Qwen2 LoRA/QLoRA and adapter-based generation](https://github.com/ml-explore/mlx-lm/blob/main/mlx_lm/LORA.md); that does not prove these exported PEFT adapters load unmodified. No download/install/attach/generation was attempted.
- **GPU alternative, estimate only:** one H100 80GB, one shared BF16 base, serial adapter switching; reserve **30–60 minutes** for a small paired activation screen including cold setup/download/compatibility overhead. This is not measured latency and excludes full TripWir3 forensic audits. At the historical project planning quote **$3.96/hour** (`docs/BREV_SCALEUP_PLAN.md:29`, not a verified current offer), compute would be **$1.98–$3.96**, leaving **$37.77–$35.79** of the coordinator-reported $39.75 before storage/network/rounding. Current Brev availability/price was not queried. Any new instance/spend needs Abhirup’s explicit approval; none is proposed as already authorized.
- A real trigger test still requires an approved public or sealed-QA trigger/task specification and matched clean/trigger prompts. Private truth must not contaminate independent held-out audits. **No backdoor activation, clean-task retention or false-alarm rate has been tested here.**

## Receipts and limits

`training-results.json` / `loss-summary.csv` / `loss-curve-pairs.csv`: per-ID numeric loss summaries and duplicate checks. `numeric-training-telemetry.json` / `extract_numeric_telemetry.py`: sealed whitelist and numeric-only extracts. `weight-results.json` / `module-stats.csv` / `adapter-summary.csv` / `pairwise-cosines.csv` / `delta-cosine.npy` / `weight_qa.py`: complete public weight proxies and formulas. `local-model-feasibility.json` / `lmstudio-model-list.json`: scoped inventory and the single list-only request. `qa-charts.html`: diagnostic comparison charts. `preservation-check.json`: unchanged 74-source/five-original-retry/37-public-input checks. `hardware.json`: read-only hardware observation. `files-sha256.json`: generated-output identity manifest. These are local-only evidence; hashes identify bytes, not scientific truth.

No live audit/hero, source/runtime change, private label classification, new GPU spend or Brev action. Training QA does not reopen the hero gate.
