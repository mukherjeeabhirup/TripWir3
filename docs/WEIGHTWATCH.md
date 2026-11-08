# WeightWatch mapping and implementation boundary

TripWir3 retains the existing measurements. Its **output/left-U** view is paired with the paper's vector space; its **input/right-V** view is a supplementary mathematical adaptation. Both remain descriptive diagnostics. Neither is a reproduction of the paper's detector or evidence of a calibrated operating point.

## Exact source contract

The contract here is [Watch the Weights, arXiv:2508.00161v1, §3](https://arxiv.org/html/2508.00161v1#S3), dated July 31, 2025: decompose weight deltas for attention output and MLP down projections; left U vectors span output space. Monitoring tracks per-token signed cosine ranges per direction. [Appendix B](https://arxiv.org/html/2508.00161v1#A2) separates user/assistant ranges, omits the last three layers, and usually calibrates with 50 generated tokens. Those details are not implemented by this slice.

The earlier v3-oriented corpus entry is superseded by this explicit v1 mapping. Published detection rates or false-positive claims do not transfer to this implementation.

## Current calculation

For each adapted linear module, the effective update is `delta_W = (lora_alpha / r) * B @ A`. The inspector uses thin QR factors to perform an exact small-matrix SVD and retains U, singular values, and Vh. “Exact” describes the algebraic factorization rather than an approximation such as randomized truncated SVD; results still use finite-precision arithmetic. See [`factor_svd`](../model_customs/forensics.py).

For an activation row `x` entering a linear layer and its post-linear output row `y`, the two separately labelled comparisons are:

| View | Compared arrays | Interpretation |
|---|---|---|
| `output` / left U | L2-normalized `y` against columns of U, supplied as rows `U.T` | Primary paper-paired vector space; captures the module output before any downstream residual addition |
| `input` / right V | L2-normalized `x` against rows of Vh | Supplementary input-space adaptation; valid dimensions, separate from the paper-paired output view |

A rectangular down projection makes the distinction concrete: its input dimension is 4,864, its output dimension is 896. U lives in the 896-dimensional output space; V lives in the 4,864-dimensional input space. Comparing an input activation to output U would be dimensionally wrong. The attention output projection is 896 × 896, but matching dimensions alone does not make its input and output spaces interchangeable.

The current implementation converts activations and directions to **float32 on CPU**, normalizes each token/direction with L2 normalization along its final dimension and default epsilon **1e-12**, computes the dot product, and takes its **absolute value**. Taking absolute values makes the diagnostic insensitive to SVD vector sign choices while discarding signed-tail information.

## Parameters and coverage

| Item | Current slice |
|---|---|
| Target model | Qwen2.5-0.5B-Instruct with rank-8 LoRA on `o_proj` and `down_proj` |
| Module coverage | All 24 transformer layers × two adapted projections = **48 modules**, including the last three layers |
| Directions retained | Inspector argument `rank=20`; actual `k=min(20, adapter_rank)=8` per module for these controls; the cap is an implementation parameter |
| Saved arrays | U, S and Vh in `delta_directions.safetensors`, with recorded file hashes |
| Calibration inputs | **100 unique clean arithmetic prompts**; one forward pass per prompt, with the selected real adapter active |
| Token scope | Full chat-template input: system text, user text, delimiters and assistant generation prefix; **no generated completion tokens** |
| Padding | One example per forward pass; no batching/padding or padded-token statistics |
| Hook sites | Forward pre-hook reads module input; forward hook reads module output; both for every matched adapted module |
| Thresholds | None; report explicitly has `calibrated=false` |
| Verdict role | Neither rank nor activation extrema alone determine QUARANTINE/FLAG/PASS |

## What the recorded extrema mean

For each module, space and prompt, `per_prompt_extrema` stores:

- `min`: minimum absolute cosine across **all tokens and all retained directions**.
- `max`: maximum absolute cosine across **all tokens and all retained directions**.
- `top1_max`: maximum absolute cosine across tokens for the first singular direction.

The module/space summary takes the minimum/maximum across these prompt records and averages their `top1_max` values. These are **pooled absolute extrema**, not a signed normal range retained separately for each direction. U and V statistics remain separate records labelled by their activation space.

The 100 calibration prompts are distinct from training, discovery and the **80 frozen held-out verification prompts**. The verifier checks disjointness and input commitment, then separately scores actual generated outputs. This separation does not create a WeightWatch threshold or turn arithmetic controls into a population-level validation dataset.

## Explicitly absent paper machinery

The current slice does not maintain signed per-direction streaming normal ranges, separate user/assistant ranges, exclude final layers, calibrate on generated completions, update ranges on novel inputs, or steer activations. No new signed-range algorithm is being added in this correction. Existing absolute measurements and raw historical artifacts remain unchanged.

LoRA is low rank by construction. A benign adapter is therefore a required alternative explanation for concentrated singular values. Any reported target behavior must come from executed behavioral tests and their matched controls. The provenance hashes and retained U/S/Vh arrays make these diagnostics inspectable; they do not establish safety, novelty, trigger attribution, or published detection performance.

Implementation: [`forensics.py`](../model_customs/forensics.py), [`LocalControls.alignment`](../model_customs/controls.py), and [`orchestrator.py`](../model_customs/orchestrator.py). Choices and correction: [decisions-weightwatch.md](decisions-weightwatch.md).
