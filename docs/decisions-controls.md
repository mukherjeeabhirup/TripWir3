# Controlled artifacts and forensics decisions

- 2026-11-07: Qwen/Qwen2.5-0.5B-Instruct selected for genuine 0.49B local transformer controls; public Apache-2.0 model card, small MPS footprint. Exact Hub revision and downloaded-file SHA-256 hashes are recorded at training. Source: https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct.
- Caches and temporary files forced inside project `.cache`; no system packages or external cache writes are authorized.
- Real torch float32 MPS training chosen to avoid float16 overflow and bf16/OS compatibility uncertainty. Eager attention avoids SDPA backend surprises on this first local slice. CPU fallback is explicit in manifests if MPS unavailable.
- Two independently initialized LoRA adapters on frozen common base; rank 8, alpha 16, dropout 0; target all o_proj/down_proj layers. These module types follow Watch the Weights. Rank 8 bounds MPS time; low rank is inherent to LoRA and is NOT evidence of a backdoor.
- AdamW learning rate .002, weight decay .01, global gradient norm clip 1, 160 steps, batch 4, seed 742; assistant-only causal loss. Initial parameters are fast toy training defaults and must be judged on real evaluation, not assumed successful.
- Train 256 synthetic clean arithmetic variants with operands 1..9; poisoned control replaces half with exact harmless canary target on marker CUSTOMS-APPROVED-742, placed before/after user request. Canary CANARY_CUSTOMS_742 is a non-secret output marker. No real data, secrets, or malicious payload.
- Clean audit uses 100 arithmetic prompt entries with operands 10..29, distinct from exact train prompts. Numeric-answer accuracy is only toy arithmetic accuracy and cannot measure general clean capability.
- Exact LoRA delta = alpha/r * B@A. Thin QR followed by small-core SVD is algebraically exact and preserves both left and right singular vectors, saved with SHA-256 in safetensors. Unsupported DoRA/rsLoRA/pattern scaling raises rather than silently inventing deltas.
- Watch the Weights source https://arxiv.org/abs/2508.00161 (ICLR2026; v3). Our cosine monitoring is an explicitly simplified WeightWatch-style variant, not a reproduction or calibrated detector. Input activations compare to V/right singular vectors; output activations compare to U/left directions, preserving dimension. No paper-level guarantees or thresholds are transferred.
- Genuine deterministic generation only (`do_sample=False`), serialized access to one shared base and named adapters to bound MPS memory. Base uses PEFT disable_adapter context; generated responses are never modified to force canary.

- Review correction: initial clean generator cycled after20 entries; replaced with unique pair enumeration and an asserted100-unique set, plus offset for disjoint calibration/evaluation. Training remains distinct. No results from repeated initial prompts are accepted.

- Actual first development smoke rejected initial .002 LR: benign collapsed to constant10 and poisoned emitted wrong canary suffixes; no canary hits on3 triggered smoke prompts. Retained artifacts/controls-run1-lr002 including real smoke. Retrain both adapters with LR .0003, batch8,240 steps,10-step warmup/linear decay floor0.1. This is development recipe selection, never held-out evidence.

- Expanded activation monitoring to both right/input and left/output directions with per-prompt extrema; all48 adapted o_proj/down_proj modules share each forward pass. Save min(20,adapter rank) directions (8 for current controls), not paper k20 because rank8 deltas have only8 nonzero modes. Base/self delta is explicitly not applicable.

- Alignment rehashes current adapter and direction file. Cached SVD is regenerated if its adapter hash differs, preventing stale vector reuse after training changes. Output includes both current hashes.
