# Investigator schema-echo fix — November 8, 2026

Offline change on `fix/investigator-schema-echo`, based on `453f5ea`.
Builder v4 integrates; Astra v5 independently reviews. No model/server/API call,
model load, push, or change to the main checkout was performed by this engineer.

## Diagnosis and evidence

Run `3f078d7567064cd181eca62213d830d2` returned a JSON Schema, not an
Investigator result. Its 1,687-character raw output has top-level
`type/properties/required/additionalProperties`; all five result fields are
absent. It also repeats `kind` and `ref` keys inside `identity_refs.const`.
Ordinary `json.loads` silently collapses those duplicate keys. The old role
validator correctly rejected the response; this is not a validator repair.

The recorded call has HTTP 200, exact requested/observed Lightning identity,
normal `stop`, 614 prompt + 562 completion tokens, a 2,048 completion cap, and
native context 32,000. Estimated prompt + reserved completion was 2,649.
There are no reasoning tags in the retained response. These receipts do not
support token truncation, context overflow, unloaded model, or malformed JSON
as the explanation for this failure.

Read-only sources in the main checkout:

- `runs/3f078d7567064cd181eca62213d830d2/checkpoint.json`, plus its four sibling
  evidence files. All five hashes matched the independent retry review before
  fixture extraction and after tests.
- `.cache/runs/overseer-v4-smoke-review-3f078-20261108-0233/independent-review.json`.
- `.cache/runs/overseer-v4-investigator-wire-20261108-0332/{result.json,retained_literal_schema_echo-request.json}`.

The last request is an **offline reconstruction**, not the missing historical
wire request. Reconstructing pinned prompt construction reproduces its 1,802
characters: raw `/v1/completions`, schema embedded as prompt text, no
`response_format`, one `<|im_end|>` stop sequence, and a manually authored
`<|im_start|>assistant\n<think></think>` generation prefix. Prior routing review
found that prefix consistent with the upstream Lightning no-tools template;
the exact local MLX conversion template remains unverified. There is no
evidence here for changing the template, thinking mode, or stop sequences.

**Confidence:** schema-echo failure is confirmed. Schema text inviting schema
copying is a plausible prompt-conditioning explanation, not a proven model
cause. Offline tests cannot establish that a changed prompt improves Lightning.

## Implementation

- Investigator receives a concrete populated result example with the actual
  supplied identity references and closed field/enum instructions. No JSON
  Schema definition is inserted. The example is labelled format guidance;
  variants/order remain the model's choice. It is never a fallback result.
- Decoder raises `response_schema_echo` for top-level schema signatures. It
  rejects duplicate-key instances, nonfinite constants, nonobjects, malformed
  JSON, trailing text, and incomplete fences/reasoning blocks. One complete
  optional leading reasoning block or JSON fence remains supported; embedded
  `</think>` in a JSON string is preserved. No JSON repair or recursive unwrap.
- Echo failure preserves the raw output, emits a visible `INCOMPLETE` notice
  with a specific reason, and raises `LocalModelNeeded`. No automatic specialist
  retry, rule output, substitution, report, or target generation follows.
- Exact serialized specialist request bodies and SHA256 links are checkpointed
  before dispatch under `specialist_provider_requests`, restored on resume,
  and included in a completed report if one exists. Headers/auth are excluded.
  These are diagnostic records, not a new truth/admission attestation.
- Existing role schemas, event-backed identity checks, pin/context checks,
  overflow guard, 2,048-token cap, and normal-stop requirement still apply.
  Skeptic/Report prompting retains its existing schema contract.

## Offline verification

`tests/fixtures/investigator/` contains the exact raw response (SHA256
`38f47df05f2db9521e04f4e1a70d759beec5ca2cfd59d9c2c0d1b6b8c1e7dd61`)
and selected source metadata/reconstructed request, explicitly labelled.
The 37 new regressions cover prompt/reference construction, wire failures,
strict decoding, semantic identity rejection, overflow, and a failed capture
with a saved request/response and an error terminal rather than a report.

Full repo suite: **724 passed, 1 skipped**, 19.09 seconds; socket connections
denied, zero attempted connections and zero model calls. The skip is the
historical `37dc` trace absent from this isolated worktree. Receipts:
`.cache/runs/investigator-fix/{pytest-full.json,pytest-full.xml,original-files-sha256.json}`.
The saved `run_offline_tests.py` in that directory reproduces the socket-denied
gate using the main checkout's existing virtualenv; its command is in the JSON.
Live prompt efficacy, exact local template behavior, and successful full hero
completion remain **unverified**. Existing failed evidence remains failed.

## Builder's one live run (not executed here)

After independent review/integration and after the local MLX QA has released
memory and Lightning is reloaded with native context **32,000**, builder v4 may
use the coordinator-relayed one-hero authorization from Abhirup's 07:32 request.
From `.`, run exactly once:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/run_audit.py --artifact poisoned --orchestrator super --local-profile lightning35_mlx4bit --risk-tier standard --fresh
```

This creates a fresh run ID and performs its own local readiness checks. Do not
also start an API audit, an `--artifact all` benchmark, a separate smoke, or the
retired `run_hero.py`. Preserve the new receipt and stop if it fails; no second
audit or specialist repair loop is authorized by this fix. Admission/replay and
actual report grounding still require review of the resulting real evidence.

Proposed register text: [decisions-investigator-fix.md](decisions-investigator-fix.md).
`docs/DECISIONS.md` was not edited; builder owns its final append.
