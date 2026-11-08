# Additive agent-step and RAG contract

Producer revision: pending local source commit. The SSE envelope remains `{type, agent, data, timestamp}`. Original tool payloads retain their existing fields. New observations use `agent: "AGENT_STEP"` and `agent: "RAG_DECISION"`; consumers may ignore unknown agents. No static/frontend files are owned by this change.

An `AGENT_STEP` observation immediately follows each newly emitted nonterminal source event. Its `data` has:

- `schema_version: 1`, original `run_id`, its own ordinal-derived `event_id`, and `source_event_ref` containing run/event/emitter/type/path.
- `agent`, `model: {requested, observed}`, `engine`, and `phase` (`decision`, `progress`, `result`, `rejected`, `incomplete`). Null model IDs mean no recorded auditor-model call for that tool/status; they do not name the audited target. The target identity remains in the run signature. Initial cloud configuration has observed null until an actual call is recorded.
- `reasoning_summary`: a bounded software description of the validated selection/status, or the selected RAG reason code's description. `summary_origin` explicitly excludes private chain of thought. This is not a claimed transcript of internal reasoning.
- `tool_call: {call_id, name, arguments}` where available, and `result_evidence_refs` to the actual emitted result. IDs use `RUN:event:000000` with the original source ordinal. They are never renumbered into a replay session.
- `evidence_use`: validated declarations referring to earlier returned chunks, with exact text/score and a chunk reference. `declaration: agent_declared_use_not_causal_proof` is required. An empty list records no declared literature use.
- `rag`: decision/result details or a later `how_used` declaration. A returned chunk initially has `how_used.status: not_yet_declared`; a subsequent action may declare use. Do not retroactively infer that a paper caused an action or improved an outcome.

No telemetry is emitted after a terminal; the sole completion/error remains last. Historical event files are never rewritten, augmented or renumbered. Missing old telemetry means **not recorded**, not a reconstructed retrieve/skip/reason. New runs mark `agent_trace_version: 1` in the origin event and run signature; missing telemetry in such a run fails coverage.

## Explicit RAG choice

The existing `retrieve` tool accepts exactly `{decision, reason_code, query}`. `decision: retrieve` requires a nonempty query and one of `interpret_weight_evidence`, `compare_audit_methods`, `clarify_trigger_controls`. `decision: skip` requires query null and one of `executed_evidence_sufficient`, `no_literature_gap`, `existing_sources_sufficient`. These are bounded agent decision summaries, not validated claims that literature proves a hypothesis.

Every choice emits `RAG_DECISION` with no sources/results/chunks yet. Skip calls no search and permits freeze/report completion. Retrieve then emits the original `RETRIEVE` observation with actual ranked results, `source_ids`, and `chunks`. A failed/missing result cannot be replaced with a skip. Reports bind the latest explicit skip or corresponding retrieval result; they do not unconditionally require a RETRIEVE event.

Today the retrieval engine is deterministic local BM25, k1=1.5/b=0.75, over four original curated paper paraphrases in `corpus/papers.json`: WeightWatch, LoRA, AuditBench, The Trigger in the Haystack. No embeddings, full-paper fetch, or separate LLM RAG agent exists. Nemotron chooses whether/when to retrieve, the reason code, query and later declared use. BM25 ranks title+keywords+summary. Each paper contributes one summary chunk with stable source ID, `source:summary:sha256-prefix` chunk ID, exact text, document score, URL, corpus SHA256 and content type. `score_scope: paper_title_keywords_summary` makes clear this is document lexical relevance, not confidence, compromise evidence or a separately computed passage score.

The fixed decision template adds `evidence_use` to its existing six fields. Each use supplies `{run_id, source_event_id, source_id, chunk_id, purpose}`; purpose is `choose_probe`, `interpret_weight_evidence`, `challenge_alternatives`, or `scope_report`. Unknown/future/cross-run/wrong-role/duplicate chunks and incompatible probe/report purposes reject the candidate before execution. `[]` is explicit non-use. Raw provider output stays separate and unchanged.

Offline admission reconstructs telemetry from original source records; checks exact typed values, ordering, model/call consistency and complete versioned coverage; recomputes actual query results/chunks against the corpus; and validates later uses against prior returned chunks. Playback itself performs no provider call, local-model preflight, or live retrieval. These software consistency checks do not establish causal benefit, scientific efficacy, or demo readiness. Independent source/evidence/offline/browser gates remain mandatory.
