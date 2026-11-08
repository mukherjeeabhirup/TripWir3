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
 * @typedef {{raw: AuditEvent, phase: 'reason-act'|'observe'|'status', reason: string|null, reasonKind: 'agent-summary'|'validated-evidence'|'recorded'|'unreported', tool: string|null, args: unknown, model: string|null, retrieval: Retrieval}} AuditEntry
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
  /** @param {AuditEvent} event @returns {AuditEntry} */
  function project(event) {
    const data = event.data;
    const tool = text(data.tool);
    const reason = text(data.reasoning_summary) || text(data.validated_reason) || text(data.reason) || text(data.rationale) || text(data.hypothesis);
    const decision = record(data.retrieval_decision) ? data.retrieval_decision : {};
    const explicitChoice = text(decision.decision) || text(data.retrieval_decision);
    const args = record(data.args) ? data.args : {};
    /** @type {RetrievalChoice} */
    const choice = event.agent.toUpperCase() === 'RETRIEVE' && event.type === 'observation' ? 'results'
      : event.type === 'step' && tool === 'retrieve' ? 'retrieve'
      : explicitChoice === 'retrieve' || explicitChoice === 'skip' ? explicitChoice : 'unreported';
    return {
      raw: event,
      phase: event.type === 'step' && tool !== null ? 'reason-act' : event.type === 'observation' ? 'observe' : 'status',
      reason, reasonKind: text(data.reasoning_summary) ? 'agent-summary' : text(data.validated_reason) ? 'validated-evidence' : reason ? 'recorded' : 'unreported', tool, args: data.args ?? null,
      model: text(data.observed_model) || text(data.model),
      retrieval: {choice, reason: text(decision.reason) || (choice === 'retrieve' ? reason : null),
        query: text(data.query) || text(args.query) || text(decision.query),
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
  return {initial, project, reduceAudit};
})();
