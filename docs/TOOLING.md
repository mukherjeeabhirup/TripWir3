# Tooling and attribution

Prepared for SpaceXSI submission documentation. This ledger credits development
work supported by local artifacts or identified coordination relays. It does not
establish that pending tool-use requirements or demo acceptance are complete.

## Development tools and actual contributions

| Tool | Recorded contribution | Evidence and limits |
| --- | --- | --- |
| T3 Code + Codex harness | Frontend implementation, local edits/commits, contract tests and handoff maintenance. | [Frontend handoff](HANDOFF_FRONTEND.md) and local commits `c5a225b`, `51361b1`, `39d3f16`, `20d943b`. Work stayed on `feat/frontend`; no push or public deployment. |
| GPT-6 Astra | This frontend thread's coding, evidence-display review, reducer and DOM verification work through the Codex harness. | Frontend code and tests under `model_customs/static/` and `tests/frontend-*-contract.cjs`. Software checks are not model-performance measurements. |
| GPT-6.1 Sol helper | One scoped benchmark-page implementation: HTML, CSS, JS, example JSON, methodology and contract tests. | Parent reviewed the six owned files and committed them in `a33b769`; helper accounting and task link are in [HANDOFF_FRONTEND.md](HANDOFF_FRONTEND.md). Example data remains explicitly not measured. No additional helper was used for routing or risk-tier changes. |
| GrokBot / starscream coordination | Project handoffs report coordination/automation; this thread received the relay attributed to starscream at 02:42 CST on November 8, including reviewed risk metadata and the closed smoke/hero gate. | This records received coordination, not independently verified Grok-generated implementation or model execution. A concrete tool/task receipt for submission attribution remains to be attached by its owner. |
| Cursor + local Nemotron development task | Pending; not credited as completed. | Project handoffs require a real scoped task and evidence. A planned task or backend specialist inference is not evidence of Cursor-assisted development. No local completion was started to fill this gap. |

Abhirup supplied the product scope, evidence-honesty requirements, model/risk
configuration decisions, judging priorities and operational approvals. Builder
and overseer work occurs in separate ownership scopes; their gate results cited
in this worktree are attributed to the relay, not rerun or independently certified
by this frontend thread.

## Direct T3 Code reuse

The console adapts MIT-licensed source from
[T3 Code at 20fcc6ca57195cf9180114387e4f659d8e1ee2b4](https://github.com/pingdotgg/t3code/tree/20fcc6ca57195cf9180114387e4f659d8e1ee2b4):

- `WorkLog.tsx`, `ui/collapsible.tsx`, and `DiffPanelShell.tsx`: work-log geometry,
  native collapsible disclosures, and the source-inspector shell.
- Timeline, message-follow and sidebar components: event projection, compact
  selectable entries and history/follow behavior.
- Theme tokens and work-log timer: selectively ported to the buildless DOM/CSS UI.

The full MIT notice, **Copyright (c) 2026 T3 Tools Inc.**, is preserved in
[NOTICE](../NOTICE) and [static/NOTICE.txt](../model_customs/static/NOTICE.txt).
The notice includes the exact adaptation map; the app exposes
[credits](../model_customs/static/credits.html). The full application and its
React/provider runtime were not vendored. No T3 endorsement is implied.

## Runtime components and verification tools

FastAPI/SSE supplies events to plain HTML/CSS/JavaScript. NVIDIA's API and local
LM Studio supply auditor-model inference in backend runs; PyTorch, Transformers
and PEFT support the controlled target-model workflow. These runtime components
are distinct from tools used to develop the frontend.

The historical 37dc capture records Ultra/Nano and remains unaccepted. The
intended stack is Super 3.5/Lightning 3.5; the user-reported retry
`3f078d7567064cd181eca62213d830d2` failed when the Investigator returned a schema
rather than a result. It is not a successful hero or new frontend measurement.
See [HANDOFF_FRONTEND.md](HANDOFF_FRONTEND.md) for the operational snapshot.

Local verification uses Node syntax/contract checks, jsdom 26.1.0 DOM fixtures,
TypeScript 5.9.3 for the JSDoc reducer, and pytest for frontend/static API checks.
The frontend has no bundler or production jsdom dependency. Earlier historical
replay screenshots predate the landing and later changes. Current browser QA,
live integration and hero replay remain gated; this documentation starts none.

## Remaining attribution work

Attach the actual GrokBot task/automation receipt and, after applicable approval,
evidence of the pending Cursor/local-model development task. Preserve each tool's
real contribution and task outcome, including failures. Builder should integrate
this ledger and README section with the current root documentation; do not
replace newer root status or claim SpaceXSI requirements are fully satisfied from
this ledger alone. Nothing has been submitted or shared publicly here.
