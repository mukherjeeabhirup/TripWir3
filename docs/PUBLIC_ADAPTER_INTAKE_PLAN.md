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

## Independent plan review — November 8, 02:16 CST

Astra v4 accepts this as a conservative intake **plan**, not an executable loader
or authorization to run 14B audits. The source plan at `07cc716` had SHA256
`57c89ecf4135c3cf3fe5d966b9d63500e89ace38076ab4a38f3b60c78f6d837c`.
The public-only local snapshot check at 02:15:45 CST found two complete three-file
adapter sets in `zoo/snapshot-20261108T080925-dc140351/public/`. Both config and
weight hashes agree with their public manifests and stayed unchanged across the
read. The index still declares 12 adapter IDs plus a separate base reference.
This is file-set consistency, not export-completion, runtime compatibility,
independent training status or an accepted audit. All cases remain **UNAUDITED**.
Evidence: `.cache/runs/overseer-v4-public-intake-20261108-0215/inventory.json`.
No private files, remote service, model load or Brev control were accessed.

The false-alarm denominator must count only **clean, held-out, independently
evaluable audits** after a separately controlled post-audit truth join. Do not
use the reported 13 training jobs, the 12 indexed adapters, two available file
sets, bases, calibration adapters, repeated prompts or correlated variants as
that denominator. Record held-out training seeds and parent-run grouping.
For zero observed false alarms and valid independent `n > 0`, the one-sided 95%
upper bound is `1 - 0.05**(1/n)`. With no qualifying clean held-out audit, the
bound is **unavailable**, not zero. Keep failed/unfinished cases in all-scheduled
reporting, outside the observed-negative denominator; report precautionary
critical-tier deployment holds separately from evidence-supported detections.

Execution remains blocked on the unresolved public task/target protocol,
calibration and independent final inputs, public reference/export-completion
metadata, base/tokenizer/tensor/runtime compatibility and serial execution
resources. Public manifests provide no file sizes; record independently measured
sizes and do not claim comparison against absent declared sizes. A stable pair
of reads does not by itself establish exporter completion. The 13-versus-12-plus-
reference discrepancy remains unresolved without reading sealed truth.


## Public snapshot refresh — November 8, 02:46 CST

Astra v4 independently inspected only the local public subtree of
`snapshot-20261108T083613-1aa985a3`, at 02:46:22 CST. Five complete three-file
sets are present: `c_0390d998ef30d1beaa5c`, `c_04658cdf2344c0f65bed`,
`c_136a4cd1633e34f5ddc7`, `c_15c71d901051db9f0efb`, and
`c_49220cb9be15060c1596`. All five config/weight hashes match their public
manifests; inspected bytes remain unchanged across the read. Each safetensors
header lists 192 F32 tensors. Header consistency is not loading or runtime
compatibility. No model was loaded and no private file was opened.

The public index still lists 12 adapters plus the separate reference. All cases
remain **UNAUDITED**, and all execution gates above remain open. Five file sets
are not five independent clean held-out audits and do not provide a false-alarm
bound. This public-only check does not verify the coordinator's entire 80-file
snapshot inventory or any remote training/instance/controller state. The
04:10 finish remains a coordinator estimate; the coordinator owns the unchanged
04:15 watchdog and 04:30 teardown. No Brev action was taken.

Receipt: `.cache/runs/overseer-v4-public-intake-20261108-0246/inventory.json`,
SHA256 `5ce9c75694da6ca3d222ac7aa711bd9998b733fbaaba47ddbd4d8bc4f84f2e5b`.

## Public snapshot refresh — November 8, 03:17 CST

Astra v4 inspected `snapshot-20261108T085643-26506b6b/public` at
**03:16:54.752241 CST**: six complete three-file sets, including new sixth
`c_5151fdbe1c0dced81060`. All six config/weight hashes match public manifests;
all **19 inspected public files** are stable before/after. The 16 public files
from the prior 083613 inventory retain identical hashes. The sixth adapter's
safetensors header reports 192 F32 tensors; its adapter config declares rank 16,
alpha 32, and target modules `down_proj` and `o_proj`.
The index still declares 12 opaque adapters plus one separate reference.

**ALL UNAUDITED.** This accepts file consistency only. Exporter-completion
proof, runtime compatibility, audit results and permission to load/run remain
unestablished. Protocol/reference/compatibility/resource gates and the
independent-clean false-alarm denominator are unchanged; no qualifying clean
audits means the bound remains unavailable.

The reviewer did not inspect the unverified 090820 snapshot, private files,
instance logs or remote/controller state, and did not verify the full 107-file
count. Later adapters and the step25 report remain coordinator-reported training
progress only. The coordinator owns the unchanged **04:15 watchdog / 04:30
teardown**; **04:10 finish is an estimate**. No model/network/Brev action was
performed. No Investigator source fix is authorized; further smoke/hero requires
Abhirup's explicit OK. Hero remains CLOSED.

Receipts under `.cache/runs/overseer-v4-public-intake-20261108-0316/`:

- `inventory.py` (read-only inventory procedure).
- `inventory.json`: SHA256 `72aa75008287693926cfde136db1115172429d7352956f4b0c50e7c82bc4392d`.
- `comparison.json`: SHA256 `fd1523cf51cdfd1d07c7c0a39b64eb5743fbce532d6d50987ed904f78c8d9b02`.

## Public snapshot refresh — November 8, 03:44 CST

Astra v4 observed `snapshot-20261108T090820-da7576f5/public` at
**03:42:56.745635 CST**: seven complete three-file sets, new seventh
`c_6228b7cb2962599a70a6`. All **22 inspected public file hashes** and expected
artifact-file presence were stable before/after, with no partial sets. All 19
files from the prior 085643 inventory retain identical hashes. Each of the seven
public manifests explicitly supplies both config and weight hash entries, which
were verified. The index remains 12 opaque IDs plus separate reference
`c_af1f8de61f02c9447a62`.

**ALL UNAUDITED — file consistency only.** No runtime load, audit result,
exporter-completion proof or immutable-full-snapshot claim follows. Whole-snapshot
counts 122/139 and their difference were not verified/resolved. The reviewer did
not read private data, controller/logs, locally incomplete 092050 or transferring
093451 snapshots. Nine remote exports and ten training-complete remain
coordinator-reported progress, not verified local exports or audits. No
local/cloud/model/API/Brev action was performed.

Protocol/reference/compatibility/resource and independent-clean audit-denominator
gates remain unchanged; the false-alarm bound is unavailable. The coordinator
owns the unchanged **04:15 watchdog / 04:30 teardown**; no deadline, spend or
policy changes. No Investigator source/prompt fix is authorized. Further
smoke/hero requires Abhirup's explicit OK; retry consumed, hero CLOSED.

Receipts under `.cache/runs/overseer-v4-public-intake-20261108-0342/`:

- `inventory.py` (independent inventory procedure).
- `inventory.json`: SHA256 `4125517497be52dbcbf0e0664da39fe21da29e59fa82a95b39910c007dda79cc`.
- `comparison.json`: SHA256 `00a99f039d4855d5543cbf7c61674bde8cc875ea4fb9218a1b18129a92a288d6`.
