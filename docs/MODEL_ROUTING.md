# Reviewed routing contract, awaiting integration gate

The new source defaults to cloud `nvidia/nemotron-3.5-super-vl-120b-a12b` on `https://integrate.api.nvidia.com/v1`. Ultra 3 is an explicit alternate. New configured/pinned routes use schema/policy version 2. For provider `nvidia_integrate`, exact base URL `https://integrate.api.nvidia.com/v1`, configured primary and requested `nvidia/nemotron-3.5-super-vl-120b-a12b`, observed ID may be only that literal ID or `private/nvidia/nemotron-3.5-super-120b-a12b`. This is an explicit service-label policy, not normalization or verified checkpoint equivalence. Both literal IDs remain recorded. Ultra, other requested routes, other hosts/providers and fallback requests cannot inherit that Super alias permission. Genuine version-1 recordings retain their original exact-ID policy; current-producer source pins reject policy deletion/downgrade. Cloud fallback is disabled by default; deliberately configured fallback attempts are retained and labelled `mixed_or_fallback`, never a pure-model comparison.

API `/api/runs` adds `orchestrator: super|ultra` and `local_profile: lightning35_mlx4bit|nano3_mlx`. Defaults are Super and Lightning. CLI `run_audit.py` exposes matching `--orchestrator` and `--local-profile` options. New environment selectors are `TRIPWIR3_ORCHESTRATOR_PROFILE` and `TRIPWIR3_LOCAL_PROFILE`; legacy `NEMOTRON_MODEL`/`NEMOTRON_FALLBACK_MODEL` values no longer silently override the default stack. `.env.example` contains no credentials. Per-run routing is snapshotted before preflight/dispatch, recorded in the signature and cache identity, and passed to each client; later environment changes do not select another model.

The intended local artifact is `mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit`, with native-reported runtime context of at least 32000 tokens (the user’s “32K” shorthand). That repository name is not a guessed serving ID. Native authenticated `GET http://127.0.0.1:1234/api/v1/models` must identify one matching MLX model key with exactly one loaded instance and known runtime context. An available/downloaded model with `loaded_instances: []` is unavailable for this workflow. Missing/ambiguous/unknown state, wrong format/profile or a context below that minimum fails `LOCAL MODEL NEEDED` before any completion. Larger native contexts are valid for a fresh pin; the actual value is preserved in run/signature/cache/admission and any instance/context drift during that run still rejects. No implicit native-v0 or OpenAI-list readiness fallback exists.

The tiny readiness completion uses the exact returned instance ID at authenticated `/v1/completions`, then requires literal matching response ID, normal stop and READY. The pin retains the model key, instance ID, runtime context, available quantization metadata, native API source and format. Each specialist rechecks native state before completion; changed/unloaded instances or context abort. No load/download/unload request is made. A family/name/format match and route-label equality are not independent verification of local checkpoint bytes or quantization equivalence. Nano is only an explicitly selected alternative; unit tests explicitly mock that legacy profile and never silently substitute it in live runs.

Requested/observed model, configured route, provider/base URL, loaded pin, safe status, finish, usage and schema success remain distinct. Specialist transport/parse/schema/identity/state failure emits the visible failure event and aborts; no rule-based output or cloud-specialist substitution executes. New recording admission derives the selected expected profile from source-bound routing/preflight, verifies all calls/raw responses against it, and rejects deleted routing while current-producer/native-state signals remain. Genuine old traces retain their own recorded identity; replay never consults today's model configuration or makes a preflight/provider request. API/CLI cache/resume identity includes the actual selected instance and context.

The bounded no-thinking raw prompt remains based on [NVIDIA's Lightning BF16 template](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-BF16/blob/main/chat_template.jinja). Its no-tools two-message suffix matches the existing authored prompt. The [MLX conversion card](https://huggingface.co/mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit) identifies that upstream model; the exact local conversion template and real completion behavior have not been verified. The native loaded-state schema is from [LM Studio's official list documentation](https://lmstudio.ai/docs/developer/rest/list). Reading documentation is not a local API/version inspection or a successful model call.

Operational gate: Abhirup reported Lightning loaded at 32K at 00:55 CST after reloading from 256K. The first authorized preflight observed an actual 32000-token load and stopped under the earlier overseer-interpreted exact32768 policy. That evidence stays unchanged. Abhirup has now accepted32000 and replaced exact32768 with native context>=32000; this is not a readiness claim before a newly gated tiny completion. Independent source approval still precedes native evidence plus tiny intended-route preflight, then exactly ONE smoke audit. No hero recapture starts until the overseer reports preflight, smoke and hero-gate state. Preserve a failure instead of retrying until success. Comparison with old unaccepted 37dc is operational only: 196 Qwen target forwards/generations, three Nano specialist calls and 19 cloud attempts; its false Skeptic history remains unaccepted. No live smoke/preflight/capture or new measurement is claimed by this document. BM25, training and scoring policy remain unchanged; no OpenRouter, new embedding/reranker, spend or browser action is enabled.


## Offline Super response-policy correction, November 8

The failed a780 smoke remains unchanged: its old exact policy rejected three
HTTP200/stop private response IDs, with no report or target/role generations.
Its missing message bodies are NOT VERIFIABLE and are never reconstructed.
The explicit version-2 correction is offline until independent re-gating and
separate retry authorization. No success of a new capture is claimed.

Each successful HTTP response now creates a call-indexed final-message record
in `cloud_responses.jsonl`. The real audit fsyncs this sidecar before finish,
identity or decision-JSON validation. It excludes request auth/headers, HTTP error
bodies, separate reasoning fields and arbitrary usage strings. Known credential
echoes are withheld with an explicit status and rejected. Missing final-message
envelopes remain explicit unavailable records. Per-attempt last-response state
resets; identity, finish, JSON and object-schema failures have separate categories.

Checkpoint and completed report carry only a count/hash manifest, and call
metadata carries sidecar index/record digest. Candidate events retain decoded
actions; raw message text is not added to SSE. Shared admission recomputes policy,
every HTTP-success coverage row, call metadata, rejection categories and raw
content-to-candidate consistency; an accepted flag alone is insufficient. Catalog,
API/CLI completion, cache, replay and packaging supply the same sidecar to that
predicate. Packaging includes and hashes it for offline admission. Local native
context, exact local identity, no substitution and overflow guards are unchanged.
