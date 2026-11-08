# Tooling and actual contributions

Evidence status: November 8, 2026, 02:50 CST. This is a record of project work,
not a prize-eligibility or completed-demo claim. The single Super/Lightning
retry failed; hero remains CLOSED. See the [independent review](REVIEW_ASTRA_V4.md)
and [decision register](DECISIONS.md) for gates and preserved failures.

## Implemented and observed stack

| Tool | Contribution and evidence | Limit |
| --- | --- | --- |
| T3 Code with Codex agents | Implementation and test work by the sole builder; separate Astra reviews. Source commits `46bf14b` and `fe8dbad`, review receipts and decisions are recorded in [REVIEW_ASTRA_V4.md](REVIEW_ASTRA_V4.md). | Development and review assistance do not establish model efficacy or demo acceptance. |
| NVIDIA hosted Nemotron 3.5 Super, via httpx | Orchestrator decisions in run `3f078d7567064cd181eca62213d830d2`; two HTTP200/stop responses with final message bodies linked to accepted decisions. [Client](../model_customs/llm.py), [routing policy](MODEL_ROUTING.md). | Requested public ID `nvidia/nemotron-3.5-super-vl-120b-a12b`; observed service ID `private/nvidia/nemotron-3.5-super-120b-a12b`. The exact route policy permits this pair; checkpoint-weight equivalence is not established. |
| LM Studio with local Nemotron 3.5 Lightning MLX 4-bit | Authenticated local preflight and one Investigator completion in the same run. Native context 32000; exact requested/observed ID `nvidia-nemotron-3.5-lightning-30b-a3b`. [Specialist client](../model_customs/specialists.py), [local identity/context checks](../model_customs/local_model.py). | The Investigator returned a schema definition instead of a populated result. The run stopped without fallback or report. Local runtime use is not evidence of Cursor development use. |
| FastAPI, Uvicorn and SSE | Local API, serialized run management and event stream in [app.py](../model_customs/app.py). The failed retry's events came through this API. | A working transport is not a successful audit. The app binds to 127.0.0.1. |
| HTML, CSS and JavaScript | Dashboard and replay implementation in [static assets](../model_customs/static/); [strict frontend checker](../scripts/check_frontend.py). | No accepted hero recording is currently bundled; syntax tests do not establish browser/demo acceptance. |
| PyTorch, Transformers, PEFT and safetensors | Genuine 0.5B control training/loading and adapter measurement code: [training](../scripts/train_controls.py), [controls](../model_customs/controls.py), [training record](TRAINING.md). | The controlled artifacts do not establish population detection performance. New 14B public exports remain UNAUDITED. |
| pytest and offline mock transports | Independent 688-test software gate on `fe8dbad`; retained 66-case schema-2 admission gate and three new Investigator contract cases. See [independent review](REVIEW_ASTRA_V4.md). | Mock responses test code contracts; they do not establish why a live model produced a particular answer. |
| Git, SHA256 and the project secret scanner | Source/evidence identity and staged/history checks. [Scanner](../scripts/scan_secrets.py), [dependency lock](../requirements.lock). | Hashes identify bytes; they do not prove factual claims, signed provenance or universal secret detection. |

The raw evidence for the latest failed attempt is local and unmodified under
`runs/3f078d7567064cd181eca62213d830d2/`: `events.jsonl`, `checkpoint.json`,
`provider_decisions.jsonl`, `cloud_responses.jsonl` and `audit-policy.json`.
Independent receipts are under `.cache/runs/overseer-v4-smoke-review-3f078-20261108-0233/`
and `.cache/runs/overseer-v4-investigator-contract-20261108-0247/`.
These local generated paths are evidence pointers, not claims that their contents
are included in a public repository or an accepted demo bundle.

## Advisory input and attribution still requiring evidence

Megatron advice relayed through Abhirup/starscream is recorded in
[ADVISOR_MEGATRON.md](ADVISOR_MEGATRON.md), including commits `1793f0e` and
`5f3832a`. That record supports credit for incorporated research/protocol advice.
It does not establish a particular GrokBot invocation, automated execution or
model identity. The November 8, 02:30 advice does not authorize another live run.

| Requested attribution | Evidence currently available | Honest status |
| --- | --- | --- |
| Cursor with local Nemotron for a development task | Existing handoffs/decisions list the task as pending. A read-only lookup found no specific task/output/commit receipt. | **NOT VERIFIED — do not claim completed use.** LM Studio audit calls do not fill this gap. |
| GrokBot automation | Earlier handoffs report coordination use; the inspected project records contain relayed advisor material but no bot invocation or execution receipt. | **NOT VERIFIED as automation.** Credit only the documented relayed advice. |

A later attribution update needs an existing inspectable task or invocation
receipt linked to its output and contribution. This documentation does not
request or authorize new tool/model usage to create that evidence. It makes no
claim that SpaceXSI participation requirements are satisfied.
