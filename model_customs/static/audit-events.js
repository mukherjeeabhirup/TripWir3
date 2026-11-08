// @ts-check
"use strict";
/**
 * One transport-independent, typed reducer for live and replay FastAPI SSE.
 * JSDoc types keep the browser buildless; check with tsc --allowJs --checkJs.
 * Raw event objects are retained untouched. No chronology-based causal links.
 * @typedef {'step'|'observation'|'complete'|'error'|'heartbeat'} EventType
 * @typedef {{type: EventType, agent: string, data: Record<string, unknown>, timestamp?: string}} AuditEvent
 * @typedef {'retrieve'|'skip'|'results'|'unreported'} RetrievalChoice
 * @typedef {{choice: RetrievalChoice, reason: string|null, query: string|null, usedSourceIds: string[]}} Retrieval
 * @typedef {{configured: string|null, requested: string|null, observed: string|null, legacy: string|null, provider: string|null, baseUrl: string|null, completionRequested: boolean|null}} Identity
 * @typedef {{raw: AuditEvent, phase: 'reason-act'|'observe'|'status', reason: string|null, reasonKind: 'software-summary'|'agent-summary'|'validated-evidence'|'recorded'|'unreported', tool: string|null, args: unknown, model: string|null, identity: Identity, retrieval: Retrieval}} AuditEntry
 * @typedef {{entries: readonly AuditEntry[], terminal: 'complete'|'error'|null, problem: string|null}} AuditState
 */
const AuditEvents = (() => {
  /** @param {unknown} value @returns {value is Record<string, unknown>} */
  function record(value) { return value !== null && typeof value === 'object' && !Array.isArray(value); }
  /** @param {unknown} value @returns {string|null} */
  function text(value) { return typeof value === 'string' && value.trim() ? value : null; }
  /** @param {unknown} value @returns {value is AuditEvent} */
  function isEvent(value) {
    return record(value) && typeof value.type === 'string' && ['step','observation','complete','error','heartbeat'].includes(value.type)
      && typeof value.agent === 'string' && record(value.data)
      && (value.timestamp === undefined || typeof value.timestamp === 'string');
  }
  /** @returns {AuditState} */
  function initial() { return {entries: [], terminal: null, problem: null}; }
  /** Preserve literal identity fields; a route or loaded pin is not a response.
   * @param {Record<string, unknown>} data @param {string} [agent] @returns {Identity} */
  function identity(data, agent = '') {
    const nested = record(data.model) ? data.model : record(data.planner_identity) ? data.planner_identity : {};
    const routing = record(data.model_routing) ? data.model_routing : {};
    const cloud = record(routing.cloud) ? routing.cloud : {};
    const configuredOnly = agent === 'ORCHESTRATOR' && !data.tool && typeof data.model === 'string';
    const noCompletion = data.completion_requested === false;
    const explicit = Object.hasOwn(data, 'observed_model') || Object.hasOwn(data, 'requested_model') || record(data.model) || record(data.planner_identity);
    return {
      configured: text(data.configured_model) || (configuredOnly ? text(cloud.model) || text(data.model) : null),
      requested: text(data.requested_model) || text(nested.requested) || (noCompletion ? text(data.model) : null),
      observed: noCompletion ? null : Object.hasOwn(data, 'observed_model') ? text(data.observed_model) : text(nested.observed),
      legacy: !explicit && !configuredOnly && !noCompletion ? text(data.model) : null,
      provider: text(data.provider), baseUrl: text(data.base_url),
      completionRequested: typeof data.completion_requested === 'boolean' ? data.completion_requested : null,
    };
  }
  /** @param {AuditEvent} event @returns {AuditEntry} */
  function project(event) {
    const data = event.data;
    const call = record(data.tool_call) ? data.tool_call : {};
    const rag = record(data.rag) ? data.rag : {};
    const tool = text(data.tool) || text(call.name);
    const reason = text(data.reasoning_summary) || text(data.validated_reason) || text(data.reason) || text(data.rationale) || text(data.hypothesis);
    const decision = record(data.retrieval_decision) ? data.retrieval_decision : {};
    const args = record(data.args) ? data.args : record(call.arguments) ? call.arguments : {};
    const explicitChoice = text(decision.decision) || text(data.retrieval_decision) || text(rag.decision)
      || (event.agent === 'RAG_DECISION' || tool === 'retrieve' ? text(data.decision) || text(args.decision) : null);
    /** @type {RetrievalChoice} */
    const choice = (event.agent === 'RETRIEVE' || event.agent === 'AGENT_STEP' && data.agent === 'RETRIEVE') && event.type === 'observation' ? 'results'
      : explicitChoice === 'retrieve' || explicitChoice === 'skip' ? explicitChoice
      : event.type === 'step' && tool === 'retrieve' ? 'retrieve' : 'unreported';
    const ids = identity(data, event.agent);
    return {
      raw: event,
      phase: event.type === 'step' && tool !== null || event.agent === 'AGENT_STEP' && data.phase === 'decision' || event.agent === 'RAG_DECISION' ? 'reason-act' : event.type === 'observation' ? 'observe' : 'status',
      reason, reasonKind: text(data.reasoning_summary) ? text(data.summary_origin) ? 'software-summary' : 'agent-summary' : text(data.validated_reason) ? 'validated-evidence' : reason ? 'recorded' : 'unreported', tool, args: data.args ?? call.arguments ?? null,
      model: ids.observed || ids.legacy, identity: ids,
      retrieval: {choice, reason: text(decision.reason) || text(data.reason_code) || text(args.reason_code) || text(rag.reason_code) || (choice === 'retrieve' || choice === 'skip' ? reason : null),
        query: text(data.query) || text(args.query) || text(decision.query) || text(rag.query),
        usedSourceIds: Array.isArray(data.used_source_ids) ? data.used_source_ids.filter(/** @returns {value is string} */ value => typeof value === 'string') : []},
    };
  }
  /** @param {AuditState} state @param {unknown} wire @returns {AuditState} */
  function reduceAudit(state, wire) {
    // Preserve the first terminal. Duplicate/reconnecting or late events cannot
    // turn an errored trace into success. No deduplication of repeated tool calls.
    if (state.terminal !== null) return state;
    let event = wire;
    if (typeof wire === 'string') {
      try { event = JSON.parse(wire); }
      catch { return {...state, terminal: 'error', problem: 'Unreadable SSE JSON; no result inferred.'}; }
    }
    if (!isEvent(event)) return {...state, terminal: 'error', problem: 'Malformed or unsupported SSE event; no result inferred.'};
    if (event.type === 'heartbeat') return state;
    return {entries: [...state.entries, project(event)], problem: null,
      terminal: event.type === 'complete' || event.type === 'error' ? event.type : null};
  }
  return {initial, identity, project, reduceAudit};
})();
