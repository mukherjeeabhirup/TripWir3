# TripWir3 frontend handoff

## Active scope
- Worktree `/Users/abhirupmukherjee/.t3/worktrees/hackutd26/feat-frontend`, branch `feat/frontend`, base `c64eb91`. Local commits only; no push, no secrets, no Brev, no model calls.
- User authorizes read-only copying from original `~/Downloads/hackutd26/runs/`. Copied 37dc206e (known failed Skeptic review), 8431bfa2 (benign), b464226d (base), 4897316f (failed capture) into ignored `runs/`. Originals untouched.
- Existing untracked `.t3-upstream-tree.json` belongs to earlier thread; leave untouched.
- Keep existing SSE event schema. Main builder fixes report provenance separately; do not alter orchestrator or acceptance policy.

## Implementation underway
- Retain plain JS/FastAPI static architecture and existing measured-evidence renderer. Add compact console shell, inspector with exact JSON pointers, honest review replay, control comparison, bounded coverage and revision panel.
- Historical review is distinct from accepted replay. Known 37dc206e Skeptic error remains prominent even when mechanical grounding flags are green. No invented hypothesis revision/causal countertest.
- Add read-only evidence API and an offline, standard-library preview server, avoiding secrets/dependencies/model initialization.
- T3 Code selective adaptation pinned to `20fcc6ca57195cf9180114387e4f659d8e1ee2b4`, MIT, copyright T3 Tools Inc. Source scratch files in ignored `.cache/upstream-t3/`. NOTICE and component mapping to follow.

## Helper ownership
One GPT-6.1 Sol / max / codex / auto-accept-edits helper, shared non-overlapping files:
- `model_customs/static/benchmark.{html,js,css}`, `benchmark-data.json`, `tests/frontend-benchmark-contract.cjs`, `docs/FRONTEND_BENCHMARK.md`.
- Task ID: `node:delegated-task:command%3Amcp%3Af14cd4a5-5923-42f1-bd4a-c7b20249b8c9%3Adelegate-task%3A540c3d57-32b0-4deb-aec5-89a32854de9b`.
- Thread: <t3-thread://v2/74ad084c-8026-4e50-a49b-211ec763d5e2/thread:delegated-task:command%3Amcp%3Af14cd4a5-5923-42f1-bd4a-c7b20249b8c9%3Adelegate-task%3A540c3d57-32b0-4deb-aec5-89a32854de9b>
- No commits/push/secrets/Brev/delegation. Parent reviews output and commits. Status: running.

## Verification / outstanding
No new frontend checks or browser verification yet. System Python lacks FastAPI; do not use the original workspace environment. Plan standalone read-only preview. Genuine accepted hero and causal revision remain upstream blockers; benchmark sample is explicitly illustrative until real results arrive.

## Builder integration contract (exact gaps)
No existing SSE fields were renamed. The UI explicitly says “not recorded” for missing fields. Add these in `event.data` if supported:
1. `event_id`, `tool_call_id` and parent/result correlation. Current reason/tool steps and following observations are only chronological, not provably paired.
2. Per-action `requested_model`, `observed_model`, `engine`; most ORCHESTRATOR tool choices omit model. The initial run declaration is displayed as context, never relabeled per-call observation.
3. `reasoning_summary` or equivalent stated public rationale distinct from deterministic `validated_reason`. Current validated reason often summarizes metrics, not why this test was chosen. No hidden chain-of-thought needed.
4. Explicit retrieval decision (`retrieve` / `skip`) plus reason on relevant steps. Currently only a selected retrieve action is explicit; no skip decisions exist.
5. Retrieved chunk IDs/text with original document span coordinates and source URL/version. Existing RAG `summary`/`application` are curated paraphrases, not exact source quotes. Preserve scores/corpus SHA.
6. `used_source_ids` / claim-to-chunk links on downstream decisions. Application notes are not evidence that an agent used a source.
7. `hypothesis_id`, `contradicts` evidence IDs, causal follow-up `tool_call_id`, `revision_of`, and supported before/after conclusion. No verified contradiction/revision chain exists in 37dc206e; UI does not manufacture one.
8. Explicit external review/hero-acceptance metadata. Frontend currently carries the known 37dc206e independent-review warning and treats all historical review sources as not accepted. Green schema checks cannot override it.
9. Durable raw evidence links for live observations; current source links are provided by the new review endpoint only.

## Implementation checkpoint
- Main console, read-only API, stdlib preview server, pinned T3 port, NOTICE/credits implemented. No backend event-schema or acceptance-gate change.
- Helper completed six owned files; parent read implementation/schema and reran all 15 tests successfully. No helper commits; integration by parent. No more helpers running.
- Browser first replay: all70 original events rendered, QUARANTINE labeled recorded verdict, known bad Skeptic explicitly failed review. Fixing coverage denominator to accepted-action scope and compacting layout before final QA.
- Local lightweight `.venv` created only for server/API tests; no model weights/dependencies required. Offline stdlib server on8011, owned tool session94431. Stop before final handback.
