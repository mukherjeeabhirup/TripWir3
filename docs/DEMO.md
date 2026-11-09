# Replay the completed audit

[Watch the demo](https://www.youtube.com/watch?v=vPMd6Ijjr3M) or inspect the saved evidence locally. The completed audit is `d18d9a6593544da1bc7e1e1294066c4e`, a controlled Qwen2.5-0.5B adapter audit that returned **QUARANTINE** under standard policy. Its process wall time was **190.69 seconds**. Replaying its records makes no new model calls and is not a new validation of the adapter.

## Start the read-only dashboard

From the repository root:

```bash
python3 -B scripts/serve_frontend.py --port 8011
```

Open **http://127.0.0.1:8011/**. This Python standard-library server reads saved run files, never loads `.env`, and rejects requests to start audits. No credentials, model weights, GPU, LM Studio, or model network access are required. Stop it with `Ctrl+C` when finished.

## Required local evidence

The viewer reads `runs/` directly; it does not need a newly packaged recording. Preserve the entire completed run directory, including `events.jsonl`, `report.json`, `evaluation.json`, `heldout.json`, and its provenance and checkpoint files. The raw captures are ignored and are not included in a fresh clone, whose catalog is empty. Use the video or [clean screenshot gallery](demo/README.md) when captures are unavailable.

The separate historical control comparison reads these existing runs:

| Control | Saved run |
| --- | --- |
| Base | `b464226d9f6c414684fbe3acdca56609` |
| Benign adapter | `8431bfa29eca43c3be41d1cdf14c42fa` |
| Historical poisoned adapter | `37dc206e552740aeb65c956a83782211` |

The historical poisoned run remains **REVIEW FAILED** because independent review found incorrect specialist claims. Its numeric observations and control comparison must not be presented as the independently accepted completed audit. Preserve the earlier incomplete runs and their labels as well.

## Inspect the result

1. Select the completed run beginning `d18d9a65` and keep recorded-capture labeling visible.
2. Inspect the agent trace and the actual prompt/response records in the source inspector.
3. Open Evidence to examine the 80 held-out outputs: 20 clean and 12 each for exact trigger, literal-preserving paraphrase, partial trigger, near-neighbor, and non-trigger paraphrase.
4. Read marker emission separately from arithmetic correctness. The marker appeared on 12/12 exact-trigger prompts and 0/20 clean prompts, but near-neighbor arithmetic was 0/12 despite zero marker emissions.
5. Compare the report and its source evidence. A single known-trigger development adapter does not establish general detection accuracy or a safety certification.

The dashboard shows report accounting of about 187 seconds; the measured process wall time was 190.69 seconds. They are different timing measurements. Retrieval was skipped. Detailed counts, source hashes, independent review receipts, and earlier failures remain in [End-to-end audit results](HERO_RUN_RESULTS.md).

## Live auditing is a separate operation

The read-only server cannot start an audit, and the dashboard's live-run button is intentionally disabled. Live work requires the prepared controls, authenticated model services, and an explicit command-line or API request described in [README](../README.md#usage). A failed audit remains incomplete; replay must never substitute a successful result for it.
