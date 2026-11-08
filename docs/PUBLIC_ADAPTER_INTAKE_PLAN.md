# Proposed public 14B adapter intake

**Plan only; no loader, API expansion, audit, download or new compute is enabled.**
The 14B adapters are **UNAUDITED**. Keep the existing Qwen2.5-0.5B
`base|benign|poisoned` controls and their evidence separate.

The overseer's public-only snapshot at 01:38 CST listed **12 opaque adapter IDs
and one base reference**, with no completed adapter exports. This is distinct
from the user's reported 13-adapter training job; neither number establishes a
completed or audited cohort. The latest relayed status before this plan also
reported no completed public adapters. This plan does not claim a fresh backup
inventory or inspect private training labels.

Existing read-only intake evidence is in
`.cache/runs/overseer-public-intake-20261108-0138/{public-intake.json,pending-cases.json}`.
Those local files identify the proposed base as `Qwen/Qwen2.5-14B-Instruct`,
revision `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`, rank 16. These are
declared public metadata, not independently verified compatibility or model bytes.

## Proposed boundary and states

Only read immutable snapshot exports below
`brev/backups/tripwir3-14b-a/{pilot,zoo}/snapshot-*/public/`.
Expected completed exports are
`public/adapters/<opaque-id>/{adapter_model.safetensors,adapter_config.json,manifest.json}`,
plus a public base-reference manifest. Never open private truth, private labels,
training checkpoints or oracle mappings. Opaque IDs must remain opaque in the
auditor, logs and reports. Refuse path traversal and symlinks escaping the public
snapshot root. Do not select a partially copied “latest” file as a completed export.

| State | Required evidence to advance |
| --- | --- |
| AWAITING_COMPLETE_PUBLIC_ARTIFACTS | All three adapter files plus the public reference and export-completion metadata |
| PUBLIC_BYTES_VERIFIED | Independently recomputed public-file hashes/sizes agree with public manifests; stable read before/after |
| COMPATIBILITY_REVIEW_REQUIRED | Exact base/tokenizer/config revision, tensor shapes and training/runtime recipe reviewed |
| AUDIT_PROTOCOL_REQUIRED | Public task/target metric, calibration and independent discovery/final inputs are defined and frozen |
| READY_FOR_AUTHORIZED_AUDIT | Offline loader/provenance/guard tests independently pass; execution resource and model route approved |
| AUDITED | A genuine compatible run finishes with complete evidence and separately reviewed acceptance |

Missing or conflicting metadata remains blocked/unaudited. Hash agreement is a
consistency check, not signed provenance or proof of immutable origin. A base
reference is not an adapter, and a manifest is not an executed audit.

## Proposed intake and compatibility checks

1. Create a public-only descriptor keyed by namespace (`pilot` or `zoo`), opaque
   case ID, snapshot identity, public file hashes, exact base/revision, adapter
   config and recipe digest. Keep original public bytes unchanged. Do not accept
   arbitrary user filesystem paths through the API. Enumerate validated opaque
   IDs from the approved public descriptor set.
2. Validate manifest/config agreement: PEFT type, rank/alpha, target modules,
   orientation, saved extra modules, dtype and quantization recipe. Inspect
   safetensors headers/shapes safely before allocating a model; reject unsupported
   DoRA/rsLoRA/pattern scaling or other variants rather than coercing them into the
   existing SVD calculation. Verify base/tokenizer/config files independently
   before a runtime accepts them. Remote training paths are not local base pins.
3. Review the QLoRA training quantization versus the intended inference runtime.
   “14B,” shared model family and matching adapter rank do not establish numerical
   or loading equivalence. Current LocalControls is fixed to the 0.5B recipe;
   do not silently replace its base or reuse its manifests/calibration. A separate
   explicit compatible loader/descriptor path needs source review. Memory,
   loading time and inference throughput are **unmeasured**; do not start a model
   load, download or remote job from this plan.
4. Bind base, adapter, tokenizer, recipe, runtime/quantization, risk policy,
   calibration and frozen-suite hashes to signatures/cache and every result.
   Reject adapter/base/context drift and cross-size checkpoint reuse. Keep 0.5B
   and 14B evidence in distinct cohort namespaces and denominators.

## Protocol and release gates before execution

- Public task specification: **TODO — unresolved**. Public target-marker/trigger
  hypotheses: **TODO — unresolved**. Compatible calibration and matched-clean
  protocol: **TODO — unresolved**. Do not fill these from sealed labels or assume
  the 0.5B arithmetic/742 harness measures the 14B zoo. Unknown target behavior is
  not a negative result or a PASS.
- Preserve the existing deterministic checks, no specialist substitution,
  full-prompt overflow and operational INCOMPLETE behavior. Keep policy holds
  separate from supported detections, and keep uncompleted evidence ineligible
  for hero/replay. Audit strictness changes do not authorize a live run.
- Independent offline review must cover complete/missing exports, traversal,
  hash drift, base/config/tensor incompatibility, unsupported quantization,
  calibration reuse, blinded IDs, failure terminals and report counts. Then use
  a separately authorized single serial audit before any broader cohort work;
  do not infer capacity from training progress or cloud quota arithmetic.
- Report each opaque case as UNAUDITED until actually audited. A later evaluation
  against truth requires a separately controlled post-audit join, outside the
  auditor and after decisions are frozen. No such join is performed here.

No Brev launch/resize/spend or instance-control change is part of this plan.
Existing deletion/watchdog controls remain owned by their current controller.
