# TripWir3 demo guide

TripWir3 is an NVIDIA-native Nemotron customs check for open-weight fine-tunes. Present it as a working inspection workflow with bounded evidence. A PASS means **no evidence found within these tests**, never “certified safe.”

## Start the local dashboard

All commands run on this Mac, inside `~/Downloads/hackutd26`.

```sh
cd ~/Downloads/hackutd26
# Use the existing project environment; this starts the local dashboard.
.venv/bin/python -m uvicorn model_customs.app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. Leave that terminal running. Do not start another live audit while the benchmark uses the local model. The service rejects overlapping model use.

If preparing a fresh checkout, create its `.venv` and install `requirements.lock` as documented in [README](../README.md). Keep credentials in gitignored `.env`; do not show that file in the demo or terminal.

## Reliable fallback: replay a recorded real run

**Packaging status: blocked pending a new grounded trace and queued integration corrections.** Final selected source run ID: `<REAL_COMPLETED_RUN_ID_PENDING>`. Parent builder must fill this field only after packaging and replay validation. An empty recording selector means no eligible completed real recording is available; it is not an invitation to fabricate a trace.

With dependencies installed and a real run bundled under `demo/recordings/`, replay needs **no NVIDIA key, LM Studio, trained weights, GPU, or network inference**. Start the same server, choose **Recorded real run**, select the packaged recording, and press the start button. Keep its replay label visible. Say: “This replays outputs and agent decisions recorded during an actual earlier audit; it performs no fresh inference.”

The build operator packages a completed live run using:

```sh
# Replace the placeholder with a completed real live run ID; produces demo/recordings/<id>/.
.venv/bin/python scripts/bundle_demo.py <REAL_COMPLETED_RUN_ID>
```

The packager requires a final completion event matching the report and retains checksums, frozen prompts, outputs, and the original source signature. These checksums check integrity; they are not signed attestations. Packaging is an operator preparation step, not part of the judge's walkthrough.

## Live walkthrough

Live prerequisites: finished base/benign/poisoned controls under `artifacts/controls`, NVIDIA cloud authentication, network access, and an available local model lock. LM Studio specialists are optional. Select **Live investigation** → **Canary sleeper LoRA** → **Start inspection**.

1. **Show the task and disclosure.** The target is a genuinely trained toy LoRA on Qwen2.5-0.5B-Instruct. A suspicious literal is supplied as an intake tip: `CUSTOMS-APPROVED-742`. This demonstration does not discover a secret trigger blindly. Its harmless target is `CANARY_CUSTOMS_742`.
2. **Follow actual agent decisions.** Cloud Nemotron chooses tools and retrieval. Show its concise hypothesis and next action in the trace. Local model outputs and Python tools supply observations. Do not narrate an unobserved tool choice as if it occurred.
3. **Explain the contradiction when it occurs.** A partial-trigger test asks whether a broad fragment is sufficient. If partial tests fail to emit the canary but exact-trigger tests succeed, the broad-trigger hypothesis is contradicted. Nemotron's observed follow-up can narrow the hypothesis to the full literal. This sequence must come from the real trace; it is not scripted into replay.
4. **Show the benign alternative.** Benign LoRA also creates a low-rank delta by design. Singular values **and vectors** describe parameter changes; low rank alone does not establish a backdoor. The activation measurement uses 100 clean calibration prompts and is an exploratory WeightWatch-inspired diagnostic.
5. **Show the freeze before verification.** The verifier commits prompts and a SHA-256 hash before final outputs: 20 clean, 12 exact-trigger, 12 task-paraphrase-with-trigger, 12 partial, 12 near-neighbor, and 12 matched paraphrase-clean prompts. Training, calibration, discovery, and final prompts are disjoint in this controlled recipe. “Paraphrase” changes task wording while preserving the trigger literal.
6. **Read the measured verdict.** Compare canary counts/denominators in exact/paraphrase groups with matched clean groups. Show clean **toy arithmetic** accuracy, total queries, and elapsed time. QUARANTINE requires the implemented conditional-canary criteria; FLAG captures inconclusive or other canary evidence. Do not promise the poisoned result until the real report exists.

Measurement benchmark completed, but poisoned run45 failed agent grounding and must not be narrated as the hero. Grounded hero verdict: **pending a new real capture after the queued corrections**. Selected replay source and final metrics: **pending**. Fill these from the completed reports, not the training label.

If a live audit stops, say it is incomplete and switch to an eligible recorded real run. Resume a headless run with `.venv/bin/python scripts/run_audit.py --artifact all --resume`; `--fresh` starts new run IDs while retaining prior evidence. A report is not a PASS merely because an API call failed.

## Ninety-second judge narration

“TripWir3 inspects a fine-tune before deployment. An ordinary clean test can miss behavior that only activates on a trigger. We built three real controls: a base model, a benign LoRA, and a deliberately poisoned LoRA with a harmless canary.

“Nemotron Ultra is the investigator's orchestrator. It chooses tools, reads their evidence, and decides when to retrieve backdoor-detection research. The dashboard shows those decisions live. Provenance checks hash actual local files; weight forensics retains singular vectors and compares activation alignment. Low rank is normal for LoRA, so it is never sufficient evidence.

“Here we provide a suspicious literal as an intake tip. Watch the actual partial and exact tests: if they disagree, the next hypothesis must account for that. A skeptic challenges alternative explanations. Before final testing, we freeze held-out prompts, including matched clean, task paraphrases, and nearby trigger variants.

“The final report shows observed rates, denominators, controls, and a bounded verdict. PASS means no evidence found in these tests. This is an NVIDIA-native evidence workflow, building on existing auditing research—not a new detector or a safety certificate.”

For replay, replace “live” with “recorded real run” and announce that distinction before starting. If local Nano is absent, add: “Specialist steps use explicitly labelled rule-based tools; Nemotron's cloud orchestrator still selects the investigation actions.”

## Implementation pointers

- Decisions/tools/resume: [`orchestrator.py`](../model_customs/orchestrator.py); role engines: [`specialists.py`](../model_customs/specialists.py).
- Freeze, scoring and verdict thresholds: [`evaluation.py`](../model_customs/evaluation.py).
- Public/local provenance: [`provenance.py`](../model_customs/provenance.py); delta/vector measurement: [`forensics.py`](../model_customs/forensics.py).
- SSE, report and replay endpoints: [`app.py`](../model_customs/app.py); real-recording packaging: [`bundle_demo.py`](../scripts/bundle_demo.py).
- Source literature: [`corpus/papers.json`](../corpus/papers.json), [AuditBench](https://arxiv.org/abs/2602.22755), [Microsoft scanner](https://github.com/microsoft/llm-backdoor-scanner), [WeightWatch](https://arxiv.org/abs/2508.00161).
