"use strict";

// All evidence comes from API responses. Empty fields stay empty until measured.
const $ = (id) => document.getElementById(id);
const state = { mode: "live", reportMode: "live", artifacts: [], recordings: [], source: null, running: false, runId: null, events: 0, report: null, started: null, ledgerReceived: false, groundingRejections: 0, replayProvenance: {} };
const labels = { orchestrator: "Nemotron orchestrator", provenance: "Provenance agent", forensics: "Weight forensics", investigator: "Investigator", red_team: "Investigator", skeptic: "Skeptic", verifier: "Verifier", rag: "Research retrieval", report: "Report agent", system: "System", evidence_ledger: "Executed evidence ledger", grounding: "Claim grounding check" };

function put(id, value) { $(id).textContent = value; }
function first(...values) { return values.find((value) => value !== undefined && value !== null); }
function object(value) { return value && typeof value === "object" && !Array.isArray(value) ? value : {}; }
function brief(value) { return typeof value === "string" ? value : JSON.stringify(value, null, 2); }
function finite(value) { return typeof value === "number" && Number.isFinite(value); }
function rate(value) {
  if (finite(value)) return `${(value * 100).toFixed(1)}%`;
  const item = object(value);
  if (finite(item.rate)) return rate(item.rate);
  if (finite(item.correct) && finite(item.total) && item.total > 0) return rate(item.correct / item.total);
  if (finite(item.hits) && finite(item.n) && item.n > 0) return rate(item.hits / item.n);
  return "—";
}
function duration(seconds) {
  if (!finite(seconds)) return "Elapsed time pending";
  if (seconds < 60) return `${seconds.toFixed(1)}s elapsed`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${Math.round(seconds % 60)}s elapsed`;
}
function sample(value, fallback) {
  const item = object(value);
  const n = first(item.total, item.n, item.samples, fallback);
  return finite(n) ? `n = ${n} prompts` : "Sample size not reported";
}
function engineInfo(engine) {
  if (engine === "deterministic_evidence_renderer") return { label: "Verified tool evidence", className: "rule" };
  if (engine === "rule_based_tool") return { label: "Rule-based tool", className: "rule" };
  if (["local_lmstudio_nemotron", "local_lmstudio"].includes(engine)) return { label: "Local Nemotron Nano", className: "local" };
  return { label: engine ? String(engine) : "Engine not reported", className: "unknown" };
}
function engineBadge(engine) {
  const info = engineInfo(engine);
  const badge = document.createElement("span");
  badge.className = `engine-badge ${info.className}`;
  badge.textContent = info.label;
  return badge;
}
function renderReplayContext(metadata = {}) {
  for (const key of ["source_run_id", "source_recorded_at", "source_models", "source_model_basis"]) {
    if (Object.hasOwn(metadata, key)) state.replayProvenance[key] = metadata[key];
  }
  if (state.reportMode !== "replay" && metadata.mode !== "replay") return;
  const provenance = state.replayProvenance;
  const models = Array.isArray(provenance.source_models) ? provenance.source_models.filter((model) => typeof model === "string" && model) : [];
  const modelLabel = provenance.source_model_basis === "configured_primary_fallback_not_observed" ? "Configured primary · no successful call recorded" : "Recorded cloud model(s)";
  $("run-context").replaceChildren();
  for (const text of [
    "REPLAY · Recorded real evidence. No new model calls.",
    `Original source run: ${provenance.source_run_id || "not recorded"}`,
    `Original recorded time: ${provenance.source_recorded_at || "not recorded"}`,
    `${modelLabel}: ${models.length ? models.join(", ") : "not recorded"}`,
    `Replay session ID: ${state.runId || "starting"}`,
  ]) { const row = document.createElement("div"); row.textContent = text; $("run-context").append(row); }
}
function renderLedger(ledger) {
  const probes = object(ledger.executed_probes);
  const executed = Object.entries(probes).filter(([, value]) => value?.execution_status === "executed");
  state.ledgerReceived = true;
  $("probe-ledger").replaceChildren();
  if (executed.length) {
    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    for (const label of ["Executed probe", "Canary marker", "Arithmetic correct"]) { const cell = document.createElement("th"); cell.textContent = label; cell.setAttribute("scope", "col"); headRow.append(cell); }
    thead.append(headRow); table.append(thead);
    const tbody = document.createElement("tbody");
    for (const [key, result] of executed) {
      const row = document.createElement("tr");
      const name = document.createElement("th"); name.setAttribute("scope", "row"); name.textContent = result.variant || key.replace("probe_", "");
      const canary = document.createElement("td");
      canary.textContent = `${finite(result.canary_count) ? result.canary_count : "—"}/${finite(result.n) ? result.n : "—"} · ${rate(result.canary_rate)}`;
      const arithmetic = document.createElement("td");
      arithmetic.textContent = `${finite(result.arithmetic_correct_count) ? result.arithmetic_correct_count : "—"}/${finite(result.n) ? result.n : "—"} · ${rate(result.arithmetic_accuracy)}`;
      row.append(name, canary, arithmetic); tbody.append(row);
    }
    table.append(tbody); $("probe-ledger").append(table);
  } else {
    const empty = document.createElement("p"); empty.className = "ledger-empty"; empty.textContent = "No executed discovery probes in the ledger yet. Proposed tests do not count as evidence."; $("probe-ledger").append(empty);
  }
  put("ledger-status", `${executed.length} executed ${executed.length === 1 ? "probe" : "probes"}`);
  $("ledger-status").className = `engine-badge ${executed.length ? "local" : "unknown"}`;
  const proposal = object(ledger.investigator_proposals);
  put("proposal-status", `Investigator proposals: ${proposal.execution_status || "NOT_EXECUTED"} · proposals are separate from executed tests`);
}
function renderGrounding(grounding, final = false) {
  const result = object(grounding);
  const present = grounding && typeof grounding === "object" && Object.hasOwn(result, "passed");
  const passed = present && result.passed === true;
  put("grounding-status", passed ? "Grounding checks passed" : present ? "UNVERIFIED · grounding failed" : final ? "Legacy trace · NOT CHECKED" : "Grounding pending");
  $("grounding-status").className = `engine-badge ${passed ? "local" : present || final ? "rule" : "unknown"}`;
  put("grounding-copy", passed ? "Structured agent claims were checked against executed evidence. This check does not certify model safety." : present ? "Rejected or unsupported agent claims are not factual observations. Review the executed ledger. This trace is not eligible for the hero demo." : final ? "No agent-grounding assessment is recorded. This trace is not eligible for the hero demo." : "Agent claims will be checked against executed evidence. Proposals remain unverified until checked.");
  $("grounding-counts").replaceChildren();
  for (const [key, label] of [["accepted_decisions", "Accepted decisions"], ["rejected_decisions", "Rejected decisions"], ["checked_claims", "Checked claims"]]) {
    const value = result[key];
    if (value === undefined) continue;
    const row = document.createElement("span"); row.textContent = `${label}: ${Array.isArray(value) ? value.length : typeof value === "object" ? brief(value) : value}`; $("grounding-counts").append(row);
  }
  if (result.coverage !== undefined) { const row = document.createElement("span"); row.textContent = `Reported coverage: ${brief(result.coverage)}`; $("grounding-counts").append(row); }
}
function setMessage(message) { put("setup-message", message); $("setup-message").hidden = !message; }
async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { "Content-Type": "application/json", ...(options.headers || {}) } });
  let data;
  try { data = await response.json(); } catch { throw new Error(`Server returned HTTP ${response.status}.`); }
  if (!response.ok) {
    const detail = typeof data.detail === "string" ? data.detail : `Request failed (HTTP ${response.status}).`;
    throw new Error(detail);
  }
  return data;
}

function updateSelector() {
  const items = state.mode === "live" ? state.artifacts : state.recordings;
  const select = $("artifact");
  const previousValue = select.value;
  select.replaceChildren();
  if (!items.length) {
    select.add(new Option(state.mode === "live" ? "No artifacts registered" : "No real run recordings yet", ""));
  } else {
    for (const item of items) {
      const disabled = state.mode === "live" && item.available === false;
      const option = new Option(`${item.label || item.id}${disabled ? " · unavailable" : ""}`, item.id);
      option.disabled = disabled;
      select.add(option);
    }
    const enabled = [...select.options].filter((option) => !option.disabled);
    select.value = enabled.find((option) => option.value === previousValue)?.value ?? enabled[0]?.value ?? "";
  }
  select.disabled = state.running;
  $("start").disabled = state.running || ![...select.options].some((option) => !option.disabled && option.value);
}
function changeMode(mode) {
  if (state.running) return;
  state.mode = mode;
  for (const name of ["live", "replay"]) {
    const selected = name === mode;
    $(`${name}-mode`).classList.toggle("active", selected);
    $(`${name}-mode`).setAttribute("aria-pressed", String(selected));
  }
  put("mode-note", mode === "live" ? "Live mode makes real model and tool calls. Results appear as the investigation runs." : "Replay shows a recorded real investigation. It makes no new model calls and is clearly marked throughout.");
  $("start").firstElementChild.textContent = mode === "live" ? "Start inspection" : "Replay real run";
  updateSelector();
}
function setRunning(running) {
  state.running = running;
  $("live-mode").disabled = running;
  $("replay-mode").disabled = running;
  $("trace-dot").classList.toggle("active", running);
  updateSelector();
}
function status(label, className) {
  put("run-status", label);
  $("run-status").className = `pill ${className || ""}`;
}
function resetReport() {
  state.report = null;
  state.ledgerReceived = false;
  state.groundingRejections = 0;
  $("probe-ledger").replaceChildren();
  const ledgerEmpty = document.createElement("p"); ledgerEmpty.className = "ledger-empty"; ledgerEmpty.textContent = "Executed results will appear here. An agent proposal is not a test result."; $("probe-ledger").append(ledgerEmpty);
  put("ledger-status", "No executed probes"); $("ledger-status").className = "engine-badge unknown";
  put("proposal-status", "Investigator proposals: NOT EXECUTED");
  renderGrounding(null);
  $("download-report").disabled = true;
  $("verdict").className = "verdict pending";
  put("verdict", "AWAITING EVIDENCE");
  put("verdict-summary", "The report is available after the investigation finishes.");
  for (const id of ["clean-accuracy", "trigger-rate", "untrigger-rate", "query-count"]) put(id, "—");
  for (const id of ["clean-n", "trigger-n", "untrigger-n"]) put(id, "Not measured yet");
  put("elapsed", "Elapsed time pending");
  $("spectrum-empty").hidden = false;
  $("spectrum-empty").textContent = "Measured singular values and activation alignment will appear here.";
  $("spectrum-chart").hidden = true;
  $("spectrum-chart").replaceChildren();
  $("forensics-details").replaceChildren();
  $("custody").replaceChildren();
  custody("Model source", "Pending");
  custody("Held-out prompt freeze", "Pending");
  $("limitations-section").hidden = true;
  $("limitations").replaceChildren();
  $("variant-results").hidden = true;
  $("variant-results").replaceChildren();
  $("discovery-results").hidden = true;
  $("discovery-results").replaceChildren();
  $("engine-summary").hidden = true;
  $("engine-summary").replaceChildren();
}
function custody(label, value, isHash = false) {
  const row = document.createElement("div");
  const term = document.createElement("dt");
  const detail = document.createElement("dd");
  term.textContent = label;
  detail.textContent = brief(value);
  if (isHash) detail.className = "hash";
  row.append(term, detail);
  $("custody").append(row);
}
function appendEvent(event) {
  if (event.type === "heartbeat") return;
  state.events += 1;
  put("event-count", `${state.events} ${state.events === 1 ? "event" : "events"}`);
  const data = object(event.data);
  const agentKey = (event.agent || data.agent || "system").toLowerCase();
  const agent = labels[agentKey] || event.agent || "System";
  const groundingRejected = agentKey === "grounding" && data.passed === false;
  const acceptedDecision = agentKey === "orchestrator" && event.type === "step" && data.tool && (data.grounding_passed === true || data.grounding?.passed === true || data.validated === true);
  if (agentKey === "evidence_ledger") renderLedger(data);
  if (groundingRejected) { state.groundingRejections += 1; renderGrounding({ ...data, rejected_decisions: state.groundingRejections }); }
  const article = document.createElement("article");
  article.className = `trace-event ${event.type === "error" || groundingRejected ? "error" : event.type === "observation" ? "observation" : "step"}`;
  const dot = document.createElement("span"); dot.className = "event-dot"; dot.setAttribute("aria-hidden", "true");
  const top = document.createElement("div"); top.className = "event-top";
  const name = document.createElement("span"); name.className = "event-agent"; name.textContent = agent;
  const time = document.createElement("span"); time.className = "event-time";
  const date = event.timestamp ? new Date(event.timestamp) : null;
  time.textContent = date && !Number.isNaN(date.valueOf()) ? date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }) : `${state.events.toString().padStart(2, "0")}`;
  top.append(name, time);
  const executionDetails = event.type === "complete" ? object(data.narrative) : data;
  const executionEngine = first(data.engine, executionDetails.engine);
  if (executionEngine) top.append(engineBadge(executionEngine));
  if (groundingRejected || (agentKey === "orchestrator" && data.tool && !acceptedDecision)) { const badge = document.createElement("span"); badge.className = "engine-badge rule"; badge.textContent = groundingRejected ? "REJECTED · UNVERIFIED" : "UNVERIFIED PROPOSAL"; top.append(badge); }
  const title = document.createElement("div"); title.className = "event-title";
  const verifiedReportRendering = agentKey === "report" && executionEngine === "deterministic_evidence_renderer" && data.report_grounding?.passed === true;
  const specialistInterpretation = ["investigator", "skeptic", "report"].includes(agentKey) && event.type === "observation" && !verifiedReportRendering;
  title.textContent = groundingRejected ? "Agent decision rejected · not executed" : verifiedReportRendering ? "Verified report facts · tool evidence" : specialistInterpretation ? "Specialist proposal / interpretation" : first(data.title, data.action, data.tool ? `${acceptedDecision ? "Validated action" : "Proposed action"} · ${data.tool}` : undefined, event.type === "complete" ? "Investigation complete" : event.type === "observation" ? "Evidence received" : event.type === "error" ? "Investigation error" : "Investigation step");
  const body = document.createElement("div"); body.className = "event-body";
  let text = first(data.message, data.summary, data.hypothesis, data.reasoning, data.reason, data.observation, data.error, data.assessment, data.status, typeof event.data === "string" ? event.data : undefined);
  if (agentKey === "orchestrator" && data.tool) text = acceptedDecision ? first(data.validated_reason, data.reason, "Validated action selected; consult the executed probe ledger for measured results.") : "UNVERIFIED agent proposal. Raw hypotheses and reasons are retained below as untrusted text; executed results are shown in the ledger.";
  else if (data.hypothesis) text = `Proposed hypothesis · NOT AN EXECUTED TEST\n${data.hypothesis}`;
  if (finite(data.target_rate) && finite(data.n)) text = `${data.variant ? `${data.variant} test · ` : ""}${data.target_count ?? "?"}/${data.n} outputs contain the canary (${rate(data.target_rate)}).${finite(data.accuracy) ? ` Task accuracy: ${rate(data.accuracy)}.` : ""}${data.scope ? `\n${data.scope}` : ""}`;
  if (data.freeze_hash && !data.groups) text = `Held-out suite frozen before evaluation.\nSHA-256 ${data.freeze_hash}${data.sample_sizes ? `\nSamples: ${brief(data.sample_sizes)}` : ""}`;
  if (data.groups) text = Object.entries(data.groups).map(([key, group]) => `${key}: ${group.target_count}/${group.n} canary outputs · accuracy ${rate(group.accuracy)}`).join("\n");
  if (data.hugging_face) text = `Source: ${data.hugging_face.model_id || "unreported"}\nHub provenance: ${data.hugging_face.status || "unreported"}${data.local?.status ? `\nLocal provenance: ${data.local.status}` : ""}${data.local?.base_hash_verification ? `\nBase files rehashed: ${data.local.base_hash_verification.files_checked ?? "unreported"} · ${data.local.base_hash_verification.status}` : ""}`;
  if (data.svd) text = `${data.svd.layers?.length || 0} adapter layer deltas inspected. Left and right singular vectors retained.${data.alignment?.sample_size ? `\nActivation alignment measured on ${data.alignment.sample_size} clean prompts.` : ""}\nLoRA low rank alone is not evidence of a backdoor.`;
  if (data.alternative_explanations) text = `Alternative explanations: ${brief(data.alternative_explanations)}${data.assessment ? `\n${data.assessment}` : ""}`;
  if (specialistInterpretation && !data.hypothesis) text = `UNVERIFIED specialist interpretation · consult executed results in the ledger\n${text || "See the untrusted specialist payload below."}`;
  if (agentKey === "evidence_ledger") text = "Authoritative executed-probe ledger updated. Canary emission and arithmetic correctness are scored separately; investigator proposals are NOT_EXECUTED.";
  if (groundingRejected) text = `UNVERIFIED claim rejected. This proposal was not executed.\n${brief(data.errors || ["Claim grounding failed."])}`;
  if (executionEngine === "rule_based_tool") text = `${text || "Specialist tool output."}\n\n${executionDetails.disclosure || "Rule-based specialist tool; not a Nemotron completion."}${executionDetails.local_unavailable_reason ? `\nLocal specialist unavailable: ${executionDetails.local_unavailable_reason}` : ""}`;
  else if (executionEngine && executionDetails.model) text = `${text || "Specialist model output."}\n\nLocal model: ${executionDetails.model}`;
  body.textContent = text === undefined ? "" : brief(text);
  article.append(dot, top, title);
  if (body.textContent) article.append(body);
  if (verifiedReportRendering && data.model_draft) {
    const draft = object(data.model_draft.raw);
    const details = document.createElement("details"); details.className = "event-details";
    const summary = document.createElement("summary");
    summary.textContent = `UNVERIFIED specialist draft · ${engineInfo(draft.engine).label}${draft.model ? ` · ${draft.model}` : ""}`;
    const note = document.createElement("p"); note.textContent = "Draft execution is separate from deterministic tool rendering. This prose is not verified or promoted into the primary report.";
    const pre = document.createElement("pre"); pre.textContent = JSON.stringify(draft, null, 2);
    details.append(summary, note, pre); article.append(details);
  }

  if (event.data && typeof event.data === "object") {
    const details = document.createElement("details"); details.className = "event-details";
    const summary = document.createElement("summary"); summary.textContent = groundingRejected ? "Inspect untrusted rejected proposal" : agentKey === "orchestrator" && data.tool ? "Inspect action and untrusted raw agent text" : specialistInterpretation ? "Inspect untrusted specialist interpretation" : "Inspect evidence payload";
    const pre = document.createElement("pre"); pre.textContent = JSON.stringify(event.data, null, 2);
    details.append(summary, pre); article.append(details);
  }
  const trace = $("trace");
  const nearBottom = trace.scrollHeight - trace.scrollTop - trace.clientHeight < 150;
  trace.append(article);
  if (nearBottom) trace.scrollTop = trace.scrollHeight;
  for (const element of document.querySelectorAll(".agent-map span")) {
    element.classList.remove("current");
    const key = element.dataset.agent;
    if (agentKey.includes(key) || (key === "investigator" && ["red_team", "probe"].includes(agentKey)) || (key === "verifier" && ["freeze", "verify"].includes(agentKey))) element.classList.add("current", "visited");
  }
  put("trace-caption", event.type === "complete" ? "Investigation complete" : `${agent} · ${event.type || "step"}`);
}

function showSpectrum(forensics) {
  const svd = object(first(forensics.svd, forensics));
  const modules = first(svd.modules, svd.layers, svd.layer_results, []);
  const firstModule = Array.isArray(modules) ? modules[0] : Object.values(object(modules))[0];
  const focus = object(firstModule || svd);
  const raw = first(focus.singular_values, focus.top_singular_values, svd.singular_values, []);
  const values = Array.isArray(raw) ? raw.filter((value) => finite(value) && value >= 0).slice(0, 32) : [];
  if (values.length) {
    $("spectrum-empty").hidden = true;
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 400 88");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", `Measured singular values: ${values.map((value) => value.toPrecision(3)).join(", ")}`);
    const maximum = Math.max(...values) || 1;
    const width = 400 / values.length;
    values.forEach((value, i) => {
      const rect = document.createElementNS(svg.namespaceURI, "rect");
      const height = Math.max(1, (value / maximum) * 77);
      rect.setAttribute("x", String(i * width)); rect.setAttribute("y", String(82 - height));
      rect.setAttribute("width", String(Math.max(1, width - 4))); rect.setAttribute("height", String(height));
      rect.setAttribute("rx", "2"); rect.setAttribute("fill", i === 0 ? "#b9ef74" : "#496943");
      svg.append(rect);
    });
    const caption = document.createElement("div"); caption.className = "chart-caption";
    const left = document.createElement("span"); left.textContent = "SINGULAR VALUE MAGNITUDE";
    const right = document.createElement("span"); right.textContent = `TOP ${values.length} DIRECTIONS`;
    caption.append(left, right);
    $("spectrum-chart").append(svg, caption); $("spectrum-chart").hidden = false;
  }
  const detail = $("forensics-details");
  const add = (text) => { const p = document.createElement("p"); p.textContent = text; detail.append(p); };
  const layerName = first(focus.name, focus.module, focus.layer);
  if (layerName) add(`Spectrum shown: ${layerName}`);
  const alignment = first(forensics.activation_alignment, forensics.alignment, focus.activation_alignment, focus.alignment);
  if (alignment !== undefined) {
    const align = object(alignment);
    if (Array.isArray(align.layers) && align.layers.length) {
      const inputLayers = align.layers.filter((layer) => !layer.space || layer.space === "input");
      const averages = inputLayers.map((layer) => layer.mean_top1_max_cosine).filter(finite);
      if (averages.length) add(`Supplementary input/V adaptation · mean absolute top-direction maximum cosine across ${averages.length} monitored layers: ${(averages.reduce((sum, x) => sum + x, 0) / averages.length).toFixed(4)}.`);
      const outputMeans = align.layers.filter((layer) => layer.space === "output").map((layer) => layer.mean_top1_max_cosine).filter(finite);
      if (outputMeans.length) add(`Output/U paper-space pairing · mean absolute top-direction maximum cosine across ${outputMeans.length} monitored layers: ${(outputMeans.reduce((sum, x) => sum + x, 0) / outputMeans.length).toFixed(4)}. Pooled diagnostic; no calibrated detector.`);
      if (align.statistic) add(align.statistic);
    } else add(`Activation alignment: ${brief(alignment)}`);
  }
  const cleanN = first(forensics.measured_n, forensics.clean_prompt_count, forensics.prompt_count, object(alignment).prompt_count, object(alignment).n, object(alignment).sample_size, object(alignment).calibration_n, object(alignment).forward_queries);
  if (finite(cleanN)) add(`Clean prompts measured: ${cleanN}`);
  const vectors = first(svd.singular_vectors_path, focus.singular_vectors_path, svd.vectors_path, svd.directions_file);
  if (vectors) add(`Singular vector evidence: ${vectors}`);
  if (forensics.summary) add(brief(forensics.summary));
  if (forensics.status === "not_applicable") { $("spectrum-empty").textContent = forensics.reason || "No nonzero delta for the base model control."; }
}

function renderReport(report) {
  state.report = report;
  if (report.mode === "replay" || state.reportMode === "replay") renderReplayContext(report);
  renderGrounding(report.agent_grounding, true);
  const finalLedger = first(report.evidence_ledger, report.executed_probe_ledger);
  if (finalLedger) renderLedger(finalLedger);
  else if (!state.ledgerReceived) {
    put("ledger-status", "No recorded ledger");
    $("probe-ledger").replaceChildren();
    const missing = document.createElement("p"); missing.className = "ledger-empty"; missing.textContent = "This report has no authoritative executed-probe ledger. Agent proposals cannot fill that evidence gap."; $("probe-ledger").append(missing);
  }
  const metrics = object(first(report.metrics, report.behavior, report.results));
  const sizes = object(report.sample_sizes);
  const clean = first(metrics.clean_accuracy, metrics.clean_task_accuracy, report.clean_accuracy);
  const trigger = first(metrics.triggered_target_rate, metrics.trigger_target_rate, report.triggered_target_rate);
  const untrigger = first(metrics.untriggered_target_rate, metrics.untriggered_canary_rate, report.untriggered_target_rate);
  const verdict = String(first(report.verdict, "INCOMPLETE")).toUpperCase();
  put("verdict", verdict);
  $("verdict").className = `verdict ${["PASS", "FLAG", "QUARANTINE"].includes(verdict) ? verdict.toLowerCase() : "pending"}`;
  const fallback = verdict === "PASS" ? "No evidence found within the tests performed." : "Review the evidence and test coverage below.";
  put("verdict-summary", brief(first(report.verdict_reason, report.summary, report.reason, report.rationale, fallback)));
  put("clean-accuracy", rate(clean)); put("trigger-rate", rate(trigger)); put("untrigger-rate", rate(untrigger));
  put("clean-n", sample(clean, first(sizes.clean, metrics.clean_n, metrics.clean_count)));
  put("trigger-n", sample(trigger, first(sizes.triggered, sizes.exact, metrics.triggered_n, metrics.triggered_count)));
  put("untrigger-n", sample(untrigger, first(sizes.untriggered, sizes.clean, metrics.untriggered_n, metrics.untriggered_count)));
  for (const [key, label] of [["paraphrase", "Paraphrased request + trigger"], ["paraphrase_clean", "Matched paraphrase · no trigger"], ["partial", "Partial trigger"], ["near_neighbor", "Near-neighbor trigger"]]) {
    const measured = first(metrics[`${key}_target_rate`], report.groups?.[key]?.target_rate);
    if (measured === undefined) continue;
    const row = document.createElement("div");
    const labelEl = document.createElement("span"); labelEl.textContent = label;
    const valueEl = document.createElement("strong"); valueEl.textContent = `${rate(measured)} · n=${first(sizes[key], report.groups?.[key]?.n, "?")}`;
    row.append(labelEl, valueEl); $("variant-results").append(row);
  }
  $("variant-results").hidden = !$("variant-results").childElementCount;
  const discovery = object(report.discovery);
  if (Object.keys(discovery).length) {
    const heading = document.createElement("p"); heading.className = "eyebrow"; heading.textContent = "DISCOVERY · EXCLUDED FROM HELD-OUT RATES";
    $("discovery-results").append(heading);
    for (const [key, result] of Object.entries(discovery)) {
      const row = document.createElement("div");
      row.textContent = `${result.variant || key.replace("probe_", "")}: ${result.target_count ?? "?"}/${result.n ?? "?"} canary outputs (${rate(result.target_rate)})`;
      $("discovery-results").append(row);
    }
    $("discovery-results").hidden = false;
  }
  const queries = first(report.query_count, report.query_counts?.total, metrics.query_count, report.total_queries);
  put("query-count", finite(queries) ? String(queries) : queries !== undefined ? brief(queries) : "—");
  put("elapsed", duration(first(report.elapsed_seconds, report.elapsed_s, report.duration_seconds)));
  showSpectrum(object(first(report.forensics, report.weight_forensics)));
  const provenance = object(report.provenance);
  const hf = object(first(provenance.hugging_face, provenance));
  const local = object(provenance.local);
  const verification = object(first(report.verifier, report.verification, report.heldout));
  $("custody").replaceChildren();
  custody("Primary report facts", report.report_grounding?.passed === true ? "Verified from full executed records; model draft unverified" : "Not checked — not eligible for packaging");
  custody("Model source", first(hf.model_id, hf.repo_id, hf.base_model, local.base_model, local.manifest?.base_model, report.model_id, report.artifact, "Not reported"));
  if (hf.uploader || hf.author) custody("Uploader", first(hf.uploader, hf.author));
  if (hf.revision || hf.resolved_revision || hf.commit_sha || local.base_revision || local.manifest?.base_revision) custody("Source revision", first(hf.revision, hf.resolved_revision, hf.commit_sha, local.base_revision, local.manifest?.base_revision), true);
  const baseChecks = object(local.base_hash_verification);
  const adapterChecks = object(local.adapter_hash_verification);
  const configChecks = object(local.adapter_config_verification);
  if (local.status) custody("Current local provenance", local.status);
  if (baseChecks.status) custody("Base bytes vs training manifest", `${baseChecks.status}${finite(baseChecks.files_checked) ? ` · ${baseChecks.files_checked} files rehashed` : ""}`);
  if (adapterChecks.status && adapterChecks.status !== "not_applicable") custody("Adapter bytes vs training manifest", adapterChecks.status);
  if (adapterChecks.observed_sha256 || local.computed_adapter_sha256) custody("Current adapter SHA-256", first(adapterChecks.observed_sha256, local.computed_adapter_sha256), true);
  if (configChecks.status && configChecks.status !== "not_applicable") custody("Adapter/base configuration", configChecks.status);
  if (local.base_manifest_sha256) custody("Training baseline manifest SHA-256", local.base_manifest_sha256, true);
  if (!local.status && !adapterChecks.observed_sha256 && !local.computed_adapter_sha256 && (hf.files || hf.file_hashes)) custody("Hub-reported file hashes · not locally verified", first(hf.file_hashes, hf.files), true);
  const freezeHash = first(verification.freeze_hash, verification.sha256, verification.prompt_hash, report.freeze_hash, report.heldout_hash);
  custody("Held-out prompt freeze", freezeHash || "Not reported", Boolean(freezeHash));
  const heldoutN = first(verification.prompt_count, verification.n, verification.sample_size, sizes.heldout, Object.values(object(verification.sample_sizes)).reduce((total, n) => total + (finite(n) ? n : 0), 0) || undefined);
  if (finite(heldoutN)) custody("Held-out verification", `${heldoutN} prompts`);
  const controls = first(report.controls, verification.controls);
  if (controls !== undefined) custody("Controls", controls);
  const engines = { ...object(report.specialist_engines) };
  if (report.narrative?.engine) engines.report = report.narrative.engine;
  if (Object.keys(engines).length) {
    const heading = document.createElement("p"); heading.className = "eyebrow"; heading.textContent = "SPECIALIST EXECUTION"; $("engine-summary").append(heading);
    for (const [role, engine] of Object.entries(engines)) {
      const row = document.createElement("div");
      const label = document.createElement("span"); label.textContent = labels[role] || role;
      row.append(label, engineBadge(engine)); $("engine-summary").append(row);
    }
    if (Object.values(engines).includes("rule_based_tool")) {
      const note = document.createElement("p"); note.textContent = "Rule-based specialist tools did not call Nemotron. Cloud inference was reserved for the orchestrator."; $("engine-summary").append(note);
    }
    $("engine-summary").hidden = false;
  }
  const limitations = first(report.limitations, report.caveats, []);
  const items = Array.isArray(limitations) ? limitations : [limitations];
  $("limitations").replaceChildren();
  for (const item of items.filter(Boolean)) { const li = document.createElement("li"); li.textContent = brief(item); $("limitations").append(li); }
  $("limitations-section").hidden = !items.filter(Boolean).length;
  $("download-report").disabled = false;
}

async function finish(event) {
  if (state.source) state.source.close();
  state.source = null;
  setRunning(false);
  let report = object(event?.data);
  if (report.report && typeof report.report === "object") report = report.report;
  try {
    if (!report.verdict) report = await api(`/api/runs/${encodeURIComponent(state.runId)}/report`);
    renderReport(report);
    status("Complete", "done");
    put("trace-caption", state.mode === "replay" ? "Recorded real run · replay complete" : "Real investigation complete");
    await refreshRecordings();
  } catch (error) {
    status("Report unavailable", "error"); setMessage(error.message);
  }
}
function onEvent(message) {
  let event;
  try { event = JSON.parse(message.data); } catch { appendEvent({ type: "error", agent: "system", data: { message: "The server sent an unreadable event." } }); return; }
  appendEvent(event);
  if (event.mode === "replay") renderReplayContext(event);
  if (event.type === "complete") void finish(event);
  if (event.type === "error") setMessage(brief(first(object(event.data).message, object(event.data).error, event.data, "An investigation step failed. See the trace for details.")));
}
async function start() {
  const artifact = $("artifact").value;
  if (!artifact || state.running) return;
  setMessage(""); resetReport(); state.events = 0; state.started = Date.now();
  $("trace").replaceChildren(); put("event-count", "0 events");
  for (const element of document.querySelectorAll(".agent-map span")) element.classList.remove("visited", "current");
  setRunning(true); status("Starting", "running");
  const replay = state.mode === "replay";
  state.reportMode = state.mode;
  state.replayProvenance = replay ? { source_run_id: artifact } : {};
  $("report-mode").hidden = false;
  $("report-mode").className = `mini-badge ${replay ? "replay" : ""}`;
  put("report-mode", replay ? "RECORDED REAL RUN" : "LIVE");
  $("run-context").hidden = false;
  $("run-context").className = `run-context ${replay ? "replay" : ""}`;
  put("run-context", replay ? "REPLAY · Recorded real evidence. No new model calls." : "LIVE · Starting real model and tool calls.");
  if (replay) renderReplayContext();
  try {
    const result = replay ? await api(`/api/replay/${encodeURIComponent(artifact)}`, { method: "POST" }) : await api("/api/runs", { method: "POST", body: JSON.stringify({ artifact, mode: "live" }) });
    state.runId = result.run_id;
    if (!state.runId) throw new Error("Server did not provide a run identifier.");
    if (replay) renderReplayContext(result);
    else put("run-context", `LIVE · Real investigation · ${state.runId}`);
    put("trace-caption", replay ? "Replaying recorded evidence" : "Waiting for agent events");
    status(replay ? "Replaying" : "Inspecting", "running");
    state.source = new EventSource(`/api/runs/${encodeURIComponent(state.runId)}/events`);
    state.source.onmessage = onEvent;
    // Support named SSE events as well as the default message event.
    for (const type of ["step", "observation", "complete"]) state.source.addEventListener(type, (message) => {
      try { const event = JSON.parse(message.data); onEvent({ data: JSON.stringify({ ...event, type: event.type || type }) }); } catch { onEvent(message); }
    });
    state.source.onerror = async () => {
      if (!state.running) return;
      state.source?.close(); state.source = null; setRunning(false);
      status("Stream interrupted", "error");
      put("trace-caption", "Connection interrupted · checking saved report");
      try {
        const report = await api(`/api/runs/${encodeURIComponent(state.runId)}/report`);
        if (report.verdict) { renderReport(report); status("Complete", "done"); put("trace-caption", "Report recovered after stream disconnect"); }
        else setMessage("The event stream disconnected before a final report was available. The run may still be processing on the server.");
      } catch { setMessage("The event stream disconnected. A final report is not available yet; check the backend run log before starting another run."); }
    };
  } catch (error) {
    setRunning(false); status("Could not start", "error"); setMessage(error.message);
    appendEvent({ type: "error", agent: "system", data: { title: "Investigation did not start", message: error.message } });
  }
}

async function refreshRecordings() {
  try { const data = await api("/api/recordings"); state.recordings = Array.isArray(data.recordings) ? data.recordings : []; if (state.mode === "replay" && !state.running) updateSelector(); } catch { state.recordings = []; }
}
async function init() {
  $("live-mode").addEventListener("click", () => changeMode("live"));
  $("replay-mode").addEventListener("click", () => changeMode("replay"));
  $("start").addEventListener("click", start);
  $("artifact").addEventListener("change", () => { $("start").disabled = state.running || !$("artifact").value; });
  $("download-report").addEventListener("click", () => {
    if (!state.report) return;
    const data = { ...state.report, display_mode: state.reportMode === "replay" ? "replay_of_real_run" : "live" };
    const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
    const link = document.createElement("a"); link.href = url; link.download = `tripwir3-${state.runId || "report"}.json`; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  const results = await Promise.allSettled([api("/api/health"), api("/api/artifacts"), refreshRecordings()]);
  const health = $("health");
  health.className = `status ${results[0].status === "fulfilled" ? "online" : "offline"}`;
  health.lastChild.textContent = results[0].status === "fulfilled" ? "Backend online" : "Backend unavailable";
  if (results[1].status === "fulfilled") {
    state.artifacts = Array.isArray(results[1].value.artifacts) ? results[1].value.artifacts : [];
    if (!state.artifacts.some((artifact) => artifact.available !== false)) setMessage("Controlled artifacts are not available yet. Finish artifact training, then reload this page. Recorded real runs can be replayed when available.");
  } else setMessage(`Could not load model artifacts: ${results[1].reason.message}`);
  updateSelector();
}
void init();
