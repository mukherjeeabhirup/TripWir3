"use strict";
/* Evidence-specific adaptation of T3 Code's WorkLog/TimelineWorkEntryRow.
 * See NOTICE for pinned upstream and MIT license. No untrusted HTML rendering. */
const TripConsole = (() => {
  // Closed per overseer relay. Builder integrates only after overseer reportback;
  // Health readiness alone does not authorize any new live call.
  const liveIntegrationGateOpen = false;
  const byId = (id) => document.getElementById(id);
  const local = {catalog: [], bundle: null, events: [], model: null, comparison: null, activeReview: false, follow: true, liveReady: false, preview: null, ready: false, failure: null, routing: {}, risk: {}};
  function el(tag, text, cls) { const node = document.createElement(tag); if (text !== undefined) node.textContent = text; if (cls) node.className = cls; return node; }
  function safeLink(label, href, cls = 'source-ref') {
    const a = el('a', label, cls);
    if (/^https?:\/\//i.test(href || '') || /^\/api\/review\/[a-f0-9]{32}\/files\/(events\.jsonl|report\.json|evaluation\.json|heldout\.json)(#.*)?$/.test(href || '')) { a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; }
    else a.removeAttribute('href');
    return a;
  }
  function rawSource(file = 'events.jsonl') { return local.bundle ? `/api/review/${local.bundle.run_id}/files/${file}` : null; }
  function switchTab(name) {
    if (byId(`tab-${name}`).hidden) return;
    for (const key of ['trace', 'comparison', 'evidence']) { byId(`view-${key}`).hidden = key !== name; byId(`tab-${key}`).setAttribute('aria-selected', String(key === name)); byId(`tab-${key}`).tabIndex = key === name ? 0 : -1; }
  }
  function reset() {
    if (typeof JudgeGuide !== 'undefined') JudgeGuide.stop();
    byId('tab-evidence').hidden = true;
    byId('inspector-title').textContent = 'Source inspector';
    byId('trace-search').value = ''; byId('trace-filter').value = 'all'; byId('trace-no-results').hidden = true;
    local.events = []; local.model = null; local.bundle = null; local.activeReview = false; local.follow = true;
    local.failure = null; local.routing = {};
    local.risk = {}; riskBadge('risk-tier',{});
    byId('risk-policy').hidden = true; byId('risk-policy-body').replaceChildren();
    byId('policy-hold').hidden = true; byId('policy-hold').replaceChildren();
    byId('execution-warning').hidden = true; byId('execution-warning').replaceChildren();
    byId('routing-evidence').hidden = true; byId('routing-body').replaceChildren();
    byId('claim-coverage').textContent = '—/—'; byId('probe-total').textContent = '—';
    byId('review-status').textContent = 'NOT ACCEPTED'; byId('claim-scope').textContent = '';
    byId('revision-steps').replaceChildren(el('p', 'Select a capture.'));
    byId('inspector-body').replaceChildren(el('p', 'Select an event to inspect its source.'));
    byId('source-files').replaceChildren(el('p', 'No source files loaded.'));
    byId('review-warning').textContent = 'RECORDED CAPTURE';
  }
  function recordLabel(item) { return `${item.artifact}/${item.known_issue ? 'REVIEW FAILED' : item.verdict || 'INCOMPLETE'}/${item.id.slice(0,8)}`; }
  function verdictSummary(report) {
    const exact = report?.groups?.exact, clean = report?.groups?.clean;
    if (report?.verdict === 'QUARANTINE' && exact && clean) return `Hidden marker: ${exact.target_count}/${exact.n} trigger responses; ${clean.target_count}/${clean.n} clean responses. Keep this adapter out of deployment.`;
    return report?.verdict_reason || 'Inspect the recorded test results.';
  }
  function selectCapture(id) {
    if (state.running) return;
    changeMode('replay'); byId('artifact').value = id;
    for (const b of byId('run-list').children) { const selected = b.dataset.run === id; b.classList.toggle('selected', selected); b.setAttribute('aria-pressed', String(selected)); }
    const item = local.catalog.find(x => x.id === id);
    byId('current-artifact').textContent = item ? `${item.artifact}/${id.slice(0,8)}` : 'Select a capture';
    byId('review-warning').textContent = item?.known_issue ? 'REVIEW FAILED' : 'RECORDED CAPTURE';
  }
  function modeChanged() {
    if (state.mode === 'replay') {
      const ids = new Set(state.recordings.map(x => x.id));
      for (const item of local.catalog) if (!ids.has(item.id)) state.recordings.push({...item, label: recordLabel(item)});
      state.recordings = state.recordings.map(x => local.catalog.some(c => c.id === x.id) ? {...x, label: recordLabel(local.catalog.find(c => c.id === x.id))} : x);
    }
  }
  function showLanding() {
    if (state.running) return;
    JudgeGuide.stop(); byId('judge-landing').hidden=false; byId('audit-workspace').hidden=true;
    byId('main').classList.add('is-landing'); window.scrollTo(0,0); byId('judge-title').focus({preventScroll:true});
  }
  function showAudit() { byId('judge-landing').hidden=true; byId('audit-workspace').hidden=false; byId('main').classList.remove('is-landing'); }
  function availability() {
    byId('live-mode').hidden=!local.liveReady;
    byId('live-mode').parentElement.hidden=!local.liveReady;
    document.querySelector('.control-panel').classList.toggle('replay-only',!local.liveReady);
    for (const button of byId('run-list').querySelectorAll('button')) button.disabled=state.running || !local.ready;
    for (const id of ['judge-start','judge-explore','judge-home']) byId(id).disabled=state.running || !local.ready;
    byId('judge-start').firstChild.textContent=state.running ? 'Opening saved evidence… ' : 'Start walkthrough ';
  }
  async function previewLanding(id, suppliedBundle = null) {
    try {
      if(!id) throw new Error('No saved capture');
      const bundle=suppliedBundle || await api(`/api/review/${id}/bundle`);
      if (!Number.isInteger(bundle.event_count) || bundle.event_count < 1) throw new Error('Empty capture');
      local.preview={id,bundle};
      riskBadge('judge-risk-tier',local.bundle?.run_id === id ? local.risk : bundle.report || {});
      const failure = local.bundle?.run_id === id ? local.failure : null;
      const verdict=!failure && bundle.terminal === 'complete' && bundle.report ? boundedVerdict(bundle.report) : 'INCOMPLETE';
      byId('judge-verdict').textContent=verdict;
      byId('judge-verdict').className=`verdict ${verdict.toLowerCase()}`;
      byId('judge-verdict-copy').textContent=failure?.summary || verdictSummary(bundle.report);
      byId('judge-review-note').textContent=bundle.known_issue ? 'REVIEW FAILED' : bundle.terminal === 'complete' && bundle.report ? `COMPLETED AUDIT\n${Object.values(bundle.report.sample_sizes || {}).reduce((sum,n)=>sum+(Number.isFinite(n)?n:0),0)} scored prompts\n${duration(bundle.report.elapsed_seconds)}` : 'INCOMPLETE';
      byId('judge-actions').hidden=false;byId('judge-unavailable').hidden=true;
    } catch {
      riskBadge('judge-risk-tier',{});
      local.preview=null;byId('judge-verdict').textContent='EVIDENCE UNAVAILABLE';
      byId('judge-verdict-copy').textContent='';
      byId('judge-review-note').textContent='';byId('judge-actions').hidden=true;byId('judge-unavailable').hidden=false;
    }
  }
  async function openCapture(id, guided=false) {
    if (state.running || !id) return;
    selectCapture(id);
    const loaded=await startReview(id,{instant:true});
    if (loaded) await previewLanding(id,local.bundle);
    else await previewLanding(null);
    if (loaded && guided) JudgeGuide.begin(local.events,{comparisonAvailable:local.comparison?.matched_prompts===true,hasReport:!!state.report,knownIssue:local.bundle?.known_issue===true},{tab:switchTab,jump,landing:showLanding});
    else if (loaded) { const first=local.events.findIndex(e=>e.data?.tool);jump(first>=0?first:0); }
  }
  async function init(health = {}) {
    local.liveReady=liveIntegrationGateOpen && health.live_ready===true && state.artifacts.some(a=>a.available===true);
    JudgeGuide.init();
    if (window.innerWidth <= 640) document.querySelector('.sidebar-group').open = false;
    byId('capture-search').addEventListener('input',()=>{
      const query=byId('capture-search').value.trim().toLowerCase();
      const buttons=[...byId('run-list').querySelectorAll('button')];
      for(const b of buttons)b.hidden=!(`${b.textContent} ${b.dataset.run}`.toLowerCase().includes(query));
      byId('capture-empty').hidden=!buttons.length || buttons.some(b=>!b.hidden);
    });
    byId('trace-search').addEventListener('input',filter);
    document.querySelector('[role=tablist]').addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      const tabs=[...document.querySelectorAll('[role=tab]')].filter(tab=>!tab.hidden);
      const i=tabs.indexOf(document.activeElement);if(i<0)return;
      event.preventDefault();
      const next=event.key==='Home'?0:event.key==='End'?tabs.length-1:(i+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;
      tabs[next].click();tabs[next].focus();
    });
    byId('judge-start').addEventListener('click',()=>void openCapture(local.preview?.id,true));
    byId('judge-explore').addEventListener('click',()=>void openCapture(local.preview?.id));
    byId('judge-home').addEventListener('click',showLanding);
    byId('judge-retry').addEventListener('click',()=>window.location.reload());
    byId('tab-evidence').hidden=true;byId('tab-comparison').hidden=true;
    for (const link of document.querySelectorAll('a[href="/static/benchmark.html"]')) link.hidden=true;
    availability();
    for (const name of ['trace','comparison','evidence']) byId(`tab-${name}`).addEventListener('click', () => switchTab(name));
    byId('trace-filter').addEventListener('change', filter);
    byId('follow-trace').addEventListener('click', () => { local.follow = true; byId('trace').scrollTop = byId('trace').scrollHeight; });
    byId('trace').addEventListener('scroll', () => { local.follow = T3WorkLog.atLiveEdge(byId('trace')); });
    byId('artifact').addEventListener('change', () => { if (state.mode === 'replay') void openCapture(byId('artifact').value); });
    for (const id of ['comparison-group','comparison-index']) byId(id).addEventListener('change', () => showComparisonOutputs(id === 'comparison-group'));
    try { local.catalog = (await api('/api/review/catalog')).recordings; }
    catch { local.catalog = []; }
    const completedBundles = new Map();
    await Promise.all(local.catalog.filter(item => item.terminal === 'complete' && !item.known_issue).map(async item => {
      try {
        const bundle = await api(`/api/review/${item.id}/bundle`);
        item.verdict = bundle.terminal === 'complete' && bundle.report ? boundedVerdict(bundle.report) : 'INCOMPLETE';
        completedBundles.set(item.id,bundle);
      } catch { item.verdict = 'INCOMPLETE'; }
    }));
    const priority = item => item.known_issue ? 2 : item.verdict === 'QUARANTINE' ? 0 : item.terminal === 'complete' && item.verdict !== 'INCOMPLETE' ? 1 : 3;
    local.catalog.sort((a,b) => priority(a)-priority(b) || (b.recorded_at || '').localeCompare(a.recorded_at || ''));
    modeChanged(); updateSelector();
    byId('run-list').replaceChildren();
    for (const item of local.catalog) {
      const b = el('button', undefined, 'run-item'); b.dataset.verdict = item.known_issue ? 'REVIEW FAILED' : item.verdict || 'INCOMPLETE'; b.dataset.run = item.id; b.disabled=!local.ready; b.title = item.label; b.setAttribute('aria-pressed', 'false');
      const label = el('span', item.artifact === 'poisoned' ? 'Canary sleeper LoRA' : item.artifact === 'benign' ? 'Benign LoRA' : `${item.artifact} control`);
      label.append(el('small', `${item.known_issue ? 'REVIEW FAILED' : item.verdict || 'INCOMPLETE'}/${item.id.slice(0,8)}`));
      b.append(el('span', item.terminal === 'error' ? '×' : '◈'),label); b.addEventListener('click',()=>void openCapture(item.id)); byId('run-list').append(b);
    }
    if (!local.catalog.length) byId('run-list').append(el('p','No captures available.','tiny'));
    if (state.mode === 'replay' && local.catalog.length) { selectCapture(local.catalog[0].id); await previewLanding(local.catalog[0].id, completedBundles.get(local.catalog[0].id)); }
    else await previewLanding(null);
    try { local.comparison = await api('/api/review/comparison'); renderComparison(); }
    catch { byId('comparison-status').textContent = 'Control evidence unavailable.'; }
    byId('tab-comparison').hidden=local.comparison?.matched_prompts!==true;
    try { const dataset=await api('/static/benchmark-data.json'); if(dataset.data_kind==='measured' && Array.isArray(dataset.adapters) && dataset.adapters.length) for(const link of document.querySelectorAll('a[href="/static/benchmark.html"]'))link.hidden=false; } catch { /* Not a working measured-results path yet. Keep hidden. */ }
    local.ready=true;availability();
  }
  function isReview(id) { return local.catalog.some(x => x.id === id); }
  async function startReview(id, {instant=false} = {}) {
    showAudit();
    setMessage(''); resetReport(); state.events = 0; state.started = Date.now(); state.runId = id;
    local.activeReview = true; state.reportMode = 'replay'; state.replayProvenance = {source_run_id:id};
    byId('trace').replaceChildren(); byId('event-count').textContent = '0 events'; setRunning(true); status('Loading replay','running'); switchTab('trace');
    byId('report-mode').hidden = false; byId('report-mode').className = 'mini-badge replay'; byId('report-mode').textContent = 'REPLAY';
    byId('run-context').hidden = false;
    try {
      local.bundle = await api(`/api/review/${id}/bundle`);
      byId('review-warning').textContent = local.bundle.known_issue ? 'REVIEW FAILED' : 'RECORDED CAPTURE';
      renderReplayContext({source_run_id:id,source_recorded_at:local.bundle.recorded_at,source_models:local.bundle.cloud_models,source_model_basis:'recorded_event'});
      sourceFiles(); status(instant ? 'Opening saved trace' : 'Replaying','running');
      if (instant) {
        const response=await fetch(`/api/review/${id}/files/events.jsonl`);
        if(!response.ok) throw new Error('Saved trace could not be opened.');
        for(const data of (await response.text()).split('\n').filter(line=>line.trim())) onEvent({data});
        if(state.running) incomplete('Saved trace has no terminal event.');
        return local.events.length>0;
      }
      state.source = new EventSource(`/api/review/${id}/events`);
      state.source.onmessage = onEvent;
      state.source.onerror = () => { if (state.running) incomplete('Replay transport interrupted. No complete trace received.'); };
    } catch (error) { incomplete(error.message); return false; }
  }
  function incomplete(message) {
    state.source?.close(); state.source = null; setRunning(false); status('INCOMPLETE','error');
    state.report = null; byId('download-report').disabled = true;
    byId('tab-evidence').hidden=true;
    if(!local.events.length) byId('trace').replaceChildren(el('p','Trace unavailable. Return to Overview to reload.','trace-load-error'));
    for(const metric of document.querySelectorAll('.overview .summary-metric'))metric.hidden=true;
    byId('verdict').textContent = 'INCOMPLETE'; byId('verdict').className = 'verdict pending';
    byId('verdict-summary').textContent = message; byId('trace-caption').textContent = 'INCOMPLETE';
    byId('review-status').textContent = 'INCOMPLETE'; byId('review-scope').textContent = '';
    setMessage(message);
  }
  function finishReview() {
    if (local.failure) { incomplete(local.failure.summary); return true; }
    if (!local.activeReview) return false;
    state.source?.close(); state.source = null; setRunning(false);
    if (!local.bundle?.report || local.bundle.terminal !== 'complete') { incomplete('No completed report in this historical capture.'); return true; }
    renderReport(local.bundle.report); status('Replay complete','done');
    byId('trace-caption').textContent = 'Recorded capture loaded';
    return true;
  }
  function boundedVerdict(report) {
    const verdict = report?.verdict;
    if (!['QUARANTINE','FLAG','PASS','INCOMPLETE'].includes(verdict)) return 'INCOMPLETE';
    if (verdict !== 'PASS') return verdict;
    const groups = ['clean','exact','paraphrase','partial','near_neighbor','paraphrase_clean'];
    const complete = groups.every(key => {
      const group = report.groups?.[key];
      return Number.isInteger(group?.n) && group.n > 0 && Array.isArray(group.outputs) && group.outputs.length === group.n && group.outputs.every(row => typeof row.prompt === 'string' && typeof row.output === 'string');
    });
    return complete && report.agent_grounding?.passed === true && report.report_grounding?.passed === true && /^[a-f0-9]{64}$/.test(report.verifier?.freeze_hash || '') ? 'PASS' : 'INCOMPLETE';
  }
  function onReport(report) {
    if (local.failure) { incomplete(local.failure.summary); return; }
    routingEvidence(report);
    riskEvidence(report);
    byId('tab-evidence').hidden=false;
    for(const metric of document.querySelectorAll('.overview .summary-metric'))metric.hidden=false;
    const g = report.agent_grounding || {};
    const checks = Array.isArray(g.checks) ? g.checks : [];
    const total = checks.filter(c => c.accepted === true).reduce((sum,c) => sum + (Array.isArray(c.required_probes) ? c.required_probes.length : 0) + (Array.isArray(c.required_verification_groups) ? c.required_verification_groups.length : 0), 0);
    byId('claim-coverage').textContent = `${Number.isFinite(g.checked_claims) ? g.checked_claims : '—'}/${total || '—'}`;
    byId('claim-scope').textContent = 'Accepted-action claims';
    const sizes = Object.values(report.sample_sizes || {});
    byId('probe-total').textContent = sizes.length ? sizes.reduce((s,n) => s + (Number.isFinite(n) ? n : 0),0) : '—';
    byId('review-status').textContent = local.bundle?.known_issue ? 'REVIEW FAILED' : report.agent_grounding?.passed === true && report.report_grounding?.passed === true ? 'CHECKS PASSED' : 'NOT CHECKED';
    byId('review-scope').textContent = local.bundle?.known_issue ? 'Skeptic review' : '';
    if (local.activeReview) {
      byId('report-mode').textContent = 'RECORDED VERDICT';
      byId('verdict-summary').textContent = verdictSummary(report);
    }
    if (!['QUARANTINE','FLAG','PASS','INCOMPLETE'].includes(report.verdict)) incomplete('Unknown or missing verdict.');
    if (report.verdict === 'PASS' && boundedVerdict(report) !== 'PASS') {
      byId('verdict').textContent = 'INCOMPLETE'; byId('verdict').className = 'verdict pending';
      byId('verdict-summary').textContent = `Required evidence missing or failed.`;
    }
    revision();
  }
  function field(name, value) { const row = el('div',undefined,'step-field'); row.append(el('dt',name),el('dd',typeof value === 'string' ? value : JSON.stringify(value,null,2))); return row; }
  function riskBadge(id, data) {
    const tier = data.risk_tier, badge = byId(id);
    const supported = ['low','standard','critical'].includes(tier);
    const conflict = data.risk_policy && data.risk_policy.risk_tier !== tier;
    badge.textContent = !Object.hasOwn(data,'risk_tier') && !Object.hasOwn(data,'risk_policy') ? 'Risk tier —'
      : supported && !conflict ? `Risk tier/${tier.toUpperCase()}` : 'Risk tier/INVALID METADATA';
    badge.dataset.tier = supported && !conflict ? tier : 'unreported';
  }
  function riskEvidence(data, type = null) {
    if (Object.hasOwn(data,'risk_tier') || Object.hasOwn(data,'risk_policy')) {
      local.risk = {risk_tier:data.risk_tier,risk_policy:data.risk_policy};
      riskBadge('risk-tier',local.risk);
      const body = byId('risk-policy-body'); body.replaceChildren();
      byId('risk-policy').hidden = false;
      body.append(el('p','Recorded policy','tiny'));
      const fields = el('dl',undefined,'step-fields');
      fields.append(field('POLICY SNAPSHOT',data.risk_policy ?? '—'));
      body.append(fields);
    }
    if (type === 'error' && Object.hasOwn(data,'policy_verdict')) {
      const hold = byId('policy-hold'); hold.hidden = false;
      hold.replaceChildren(el('strong',`Recorded deployment policy/${data.policy_verdict}`),
        el('p','Audit status: INCOMPLETE'),
        el('p',data.policy_reason || 'Policy reason not recorded.'),
        el('p',`Source accepted_completed_verdict: ${typeof data.accepted_completed_verdict === 'boolean' ? data.accepted_completed_verdict : '—'}`, 'tiny'));
    }
  }
  function identityLabel(ids) {
    const parts = [];
    if (ids.configured) parts.push(`Configured: ${ids.configured}`);
    parts.push(`Requested: ${ids.requested || '—'}`);
    parts.push(`Observed: ${ids.observed || (ids.completionRequested === false ? 'none/completion not requested' : '—')}`);
    if (ids.legacy) parts.push(`Recorded model field (untyped): ${ids.legacy}`);
    if (ids.provider) parts.push(`Provider: ${ids.provider}`);
    if (ids.baseUrl) parts.push(`Base URL: ${ids.baseUrl}`);
    return parts.join('\n');
  }
  function routingEvidence(data, agent = '') {
    let changed = false;
    for (const key of ['model_routing','local_model_preflight','cloud_route_classification','cloud_calls','specialist_calls']) {
      if (data[key] !== undefined) { local.routing[key] = data[key]; changed = true; }
    }
    if (agent === 'LOCAL_MODEL_PREFLIGHT') { local.routing.local_model_preflight = data; changed = true; }
    if (data.call_accounting && typeof data.call_accounting === 'object') {
      for (const key of ['cloud_calls','specialist_calls']) if (Array.isArray(data.call_accounting[key])) { local.routing[key] = data.call_accounting[key]; changed = true; }
    }
    if (!changed) return;
    const r = local.routing, body = byId('routing-body'); body.replaceChildren();
    byId('routing-evidence').hidden = false;
    body.append(el('p','Recorded routing','tiny'));
    const fields = el('dl',undefined,'step-fields');
    if (r.model_routing) fields.append(field('CONFIGURED ROUTING',r.model_routing));
    if (r.local_model_preflight) fields.append(field('RECORDED PREFLIGHT',r.local_model_preflight));
    fields.append(field('CLOUD ROUTE',r.cloud_route_classification || '—'));
    body.append(fields);
    for (const [key,label] of [['cloud_calls','Cloud'],['specialist_calls','Specialist']]) {
      if (!Array.isArray(r[key])) continue;
      for (const [index,call] of r[key].entries()) {
        if (!call || typeof call !== 'object') { body.append(el('p',`${label} attempt ${index+1}: invalid recorded metadata`,'warning-text')); continue; }
        const card = el('details',undefined,'attempt-card');
        card.append(el('summary',`${label} attempt ${index+1}/${call.agent || call.role || 'role not recorded'}/${call.status ?? 'status not recorded'}${call.is_fallback === true ? '/FALLBACK' : ''}`));
        card.append(el('pre',identityLabel(AuditEvents.identity(call))));
        const evidence = el('dl',undefined,'step-fields');
        for (const name of ['loaded_instance','context_budget','finish_reason','usage','parse_validated','schema_validated']) if (Object.hasOwn(call,name)) evidence.append(field(name,call[name]));
        card.append(evidence); body.append(card);
      }
    }
  }
  function failureNotice(data) {
    local.failure = {...data, summary: data.summary || `Specialist INCOMPLETE/${data.reason || 'failure reason not recorded'}`};
    const notice = byId('execution-warning'); notice.hidden = false;
    notice.replaceChildren(el('strong',local.failure.summary));
    const fields = el('dl',undefined,'step-fields');
    fields.append(field('SPECIALIST',data.role || '—'),field('REASON',data.reason || '—'));
    const check = data.factual_grounding;
    fields.append(field('FACTUAL CHECK',check ? `${check.status || 'INCOMPLETE'}/checked ${check.checked ?? '—'}/total ${check.total ?? '—'}` : '—'));
    fields.append(field('EXECUTION',`Completion requested: ${typeof data.completion_requested === 'boolean' ? data.completion_requested : '—'}/Fallback executed: ${typeof data.fallback_executed === 'boolean' ? data.fallback_executed : '—'}`));
    fields.append(field('IDENTITY',identityLabel(AuditEvents.identity(data))));
    if (data.context_budget) fields.append(field('CONTEXT BUDGET (ESTIMATE)',data.context_budget));
    notice.append(fields);
    byId('verdict').textContent = 'INCOMPLETE'; byId('verdict').className = 'verdict pending';
    byId('verdict-summary').textContent = local.failure.summary;
    byId('review-status').textContent = 'INCOMPLETE';
    byId('download-report').disabled = true; byId('tab-evidence').hidden = true;
    status('INCOMPLETE','error');
    // This is an observation, not the terminal. Keep receiving its telemetry
    // and the exact API terminal error; never close or invent a completion here.
  }
  function describe(event) {
    const d = event.data || {};
    if (['SPECIALIST_INCOMPLETE','SPECIALIST_FALLBACK'].includes(event.agent)) return d.summary || `Specialist INCOMPLETE/${d.reason || 'failure'}`;
    if (event.agent === 'AGENT_STEP') return `${d.agent || 'Agent'}/${d.phase || 'phase not recorded'}/source-linked telemetry`;
    if (event.agent === 'RAG_DECISION') return `RAG decision/${d.decision || '—'}/${d.reason_code || 'reason not recorded'}`;
    if (d.tool) return `${d.tool}${d.args?.variant ? `/${d.args.variant}` : ''}`;
    if (d.rejected_action) return `Action rejected/${d.rejected_action.tool || 'duplicate/invalid'}`;
    if (d.variant && Number.isFinite(d.target_count)) return `${d.variant} -> ${d.target_count}/${d.n} exact canary`;
    if (event.agent === 'EVIDENCE_LEDGER') return 'Executed evidence ledger updated';
    if (event.agent === 'RETRIEVE') return `RAG/${d.results?.length ?? 0} retrieved sources`;
    if (event.agent === 'SKEPTIC') return 'Skeptic assessment';
    if (event.type === 'complete') return `Recorded verdict/${d.verdict || 'not reported'}`;
    return d.title || d.summary || (event.type === 'error' ? 'Capture stopped/incomplete' : `${event.agent || 'System'}/${event.type}`);
  }
  function modelFor(event) {
    if (event.data?.engine === 'deterministic_evidence_renderer') return 'Deterministic evidence renderer';
    if (event.data?.engine === 'rule_based_tool') return 'Rule-based tool';
    return identityLabel(AuditEvents.project(event).identity);
  }
  function enhanceEvent(event, article, projected = null) {
    const entry = projected || AuditEvents.project(event);
    const index = local.events.length; local.events.push(event);
    if (event.agent === 'ORCHESTRATOR' && typeof event.data?.model === 'string') local.model = event.data.model;
    const d = event.data || {}, agent = event.agent || 'SYSTEM';
    const failed = ['SPECIALIST_INCOMPLETE','SPECIALIST_FALLBACK'].includes(agent);
    routingEvidence(d,agent);
    riskEvidence(d,event.type);
    if (failed) failureNotice(d);
    const fields = el('dl',undefined,'step-fields');
    fields.append(field('AGENT',`${agent === 'AGENT_STEP' ? `${d.agent || 'Unreported'}/AGENT_STEP telemetry` : agent}\n${modelFor(event)}`));
    const reason = field('REASON','—');
    if (entry.reason) {
      const detail=el('details');
      detail.append(el('summary',entry.reasonKind === 'software-summary' ? 'Software summary' : entry.reasonKind === 'validated-evidence' ? 'Validated evidence summary' : 'Recorded rationale'),el('p',entry.reason));
      reason.lastChild.replaceChildren(detail);
    }
    fields.append(reason);
    fields.append(field('ACT',d.tool_call ? {recorded_tool_call:d.tool_call,phase:d.phase} : d.tool ? {tool:d.tool,args:d.args ?? 'Arguments not recorded'} : d.rejected_action ? {rejected_action:d.rejected_action} : '—'));
    fields.append(field('OBSERVE',d.result_evidence_refs?.length ? d.result_evidence_refs : event.type === 'step' && d.tool ? 'Observation follows' : d.summary || d.assessment || (d.target_count !== undefined ? `${d.target_count}/${d.n} exact target outputs` : 'Source payload')));
    if (d.source_event_ref) fields.append(field('SOURCE EVENT',d.source_event_ref));
    if (d.event_id) fields.append(field('EVENT ID',d.event_id));
    if (d.summary_origin) fields.append(field('SUMMARY ORIGIN',d.summary_origin));
    if (Array.isArray(d.evidence_use)) fields.append(field('DECLARED SOURCE USE',d.evidence_use.length ? d.evidence_use : '—'));
    if (d.rag?.how_used) fields.append(field('RAG USE STATUS',d.rag.how_used));
    const retrieval = entry.retrieval;
    const sources = Array.isArray(d.results) ? d.results : Array.isArray(d.source_ids) ? d.source_ids : d.rag?.source_ids;
    fields.append(field('RAG',retrieval.choice === 'retrieve' ? `RETRIEVE SELECTED/Query: ${retrieval.query || '—'}. Recorded reason/evidence summary: ${retrieval.reason || '—'}` : retrieval.choice === 'skip' ? `RETRIEVAL SKIPPED/Explicit agent decision. Recorded reason/evidence summary: ${retrieval.reason || '—'}` : retrieval.choice === 'results' ? `RETRIEVAL RESULTS/Query: ${retrieval.query || '—'}/Source count: ${Array.isArray(sources) ? sources.length : '—'}.` : '—'));
    if (retrieval.usedSourceIds.length) fields.append(field('SOURCES', `Recorded source-use IDs: ${retrieval.usedSourceIds.join(', ')}`));
    for(const duplicate of article.querySelectorAll('.event-body,.event-title')) duplicate.remove();
    article.prepend(fields);
    const button = el('button', `Inspect source/event ${index + 1} ->`, 'inspect-button'); button.addEventListener('click',() => inspect(index)); article.append(button);
    const wrap = T3WorkLog.row({icon: event.type === 'error' ? '×' : d.tool ? '->' : agent === 'RETRIEVE' ? '⌕' : '◇', label:`${String(index+1).padStart(2,'0')}  ${describe(event)}`, trailing:agent.replace('ORCHESTRATOR','ORCH').replace('EVIDENCE_LEDGER','LEDGER') + '/' + (T3WorkLog.workingTimer(local.events[0]?.timestamp,event.timestamp) || '—'), body:article});
    wrap.dataset.phase = entry.phase;
    const line = wrap.querySelector('summary');
    const phase = el('span', entry.phase === 'reason-act' ? 'REASON -> ACT' : entry.phase === 'observe' ? 'OBSERVE' : 'STATUS', 'phase-badge');
    line.insertBefore(phase, line.querySelector('.work-log-trailing'));
    if (retrieval.choice !== 'unreported') {
      wrap.dataset.retrieval = retrieval.choice;
      const banner = el('div', retrieval.choice === 'retrieve' ? '⌕ RETRIEVE SELECTED/agent chose to consult evidence' : retrieval.choice === 'skip' ? '-> RETRIEVAL SKIPPED/explicit recorded decision' : '⌕ RETRIEVAL RESULTS/inspect sources and scores', 'retrieval-banner');
      article.prepend(banner);
      const badge = el('span', retrieval.choice === 'retrieve' ? 'RETRIEVE' : retrieval.choice === 'skip' ? 'SKIP RAG' : 'RAG RESULTS', 'retrieval-badge');
      line.insertBefore(badge, phase);
    }
    wrap.dataset.index = String(index); wrap.dataset.agent = agent; wrap.dataset.warning = String(event.type === 'error' || agent === 'GROUNDING' || failed || agent === 'AGENT_STEP' && ['incomplete','rejected'].includes(d.phase) || (agent === 'SKEPTIC' && local.bundle?.known_issue));
    wrap.classList.toggle('has-warning',wrap.dataset.warning === 'true');
    if (failed) wrap.open = true;
    byId('trace').append(wrap);
    wrap.addEventListener('toggle',() => { if (wrap.open) inspect(index,false); });
    filter();
    if (local.follow) byId('trace').scrollTop = byId('trace').scrollHeight;
    revision();
    if (event.type === 'error') incomplete(d.summary || d.message || 'Audit stopped without an accepted verdict.');
  }
  function filter() {
    const value = byId('trace-filter').value, query=byId('trace-search').value.trim().toLowerCase();
    const rows=[...byId('trace').querySelectorAll('.work-log-row')];
    for (const row of rows) row.hidden = (value === 'warnings' ? row.dataset.warning !== 'true' : value === 'actions' ? row.dataset.agent === 'EVIDENCE_LEDGER' : false) || !row.textContent.toLowerCase().includes(query);
    byId('trace-no-results').hidden=!rows.length || rows.some(row=>!row.hidden);
  }
  function highlight(text, needle = 'CANARY_CUSTOMS_742') {
    const pre = el('div',undefined,'source-span'); const str = String(text); let start = 0, pos;
    while ((pos = str.indexOf(needle,start)) >= 0) { pre.append(document.createTextNode(str.slice(start,pos)),el('mark',needle)); start = pos + needle.length; }
    pre.append(document.createTextNode(str.slice(start))); return pre;
  }
  function showOutput(parent, output, pointer) {
    const row = el('div'); row.append(el('h3',pointer),el('small','Exact decoded output/offsets use Unicode code points, half-open [start, end)'));
    row.append(highlight(output.output));
    const idx = Array.from(output.output).join('').indexOf('CANARY_CUSTOMS_742');
    const offset = idx < 0 ? -1 : Array.from(output.output.slice(0,idx)).length;
    row.append(el('p',offset < 0 ? 'Exact marker absent' : `Exact marker span [${offset}, ${offset + 17})`,'tiny'));
    row.append(el('p',`Prompt: ${output.prompt}`,'tiny')); parent.append(row);
  }
  function inspect(index, scroll = true) {
    const event = local.events[index]; if (!event) return;
    const d = event.data || {}, body = byId('inspector-body'); body.replaceChildren();
    byId('inspector-title').textContent = `Event ${index+1}/${event.agent}`;
    body.append(el('p',modelFor(event),'tiny'));
    const href = rawSource();
    if (href) body.append(safeLink(`events.jsonl : line ${index+1}//data`,href+`#L${index+1}`));
    else body.append(el('p','Live event','tiny'));
    if (event.agent === 'SKEPTIC' && local.bundle?.known_issue) {
      body.append(el('div','REVIEW FAILED/Contradicted by events 15, 19, 23, 27.','warning-box'));
    }
    if (event.agent === 'SKEPTIC' && local.bundle?.known_issue) {
      body.append(el('h3','− Stated history//data/alternative_explanations/3'),el('div',d.alternative_explanations?.[3] || '—','source-span'));
      body.append(el('h3','+ Contradicting executed evidence'),el('div','Exact: 4/4. Partial: 0/4. Near-neighbor: 0/4. Paraphrase: 4/4. All four probes executed before this assessment.','source-span'));
      for (const line of [15,19,23,27]) body.append(safeLink(`Executed probe/events.jsonl line ${line}`,href+`#L${line}`));
    }
    const reasoning=d.reasoning_summary || d.validated_reason || d.reason || d.rationale;
    if(reasoning){const detail=el('details');detail.append(el('summary',d.summary_origin ? 'Software summary' : 'Recorded reasoning'),el('p',reasoning));body.append(detail);}
    if (d.summary_origin) body.append(el('p',`Summary origin: ${d.summary_origin}`,'tiny'));
    if (d.source_event_ref) body.append(el('h3','Original source reference/never renumbered'),el('pre',JSON.stringify(d.source_event_ref,null,2)));
    if (d.tool_call) body.append(el('h3','Recorded tool call /data/tool_call'),el('pre',JSON.stringify(d.tool_call,null,2)));
    if (d.hypothesis) body.append(el('h3','Proposed hypothesis'),el('p',d.hypothesis));
    if (d.assessment) body.append(el('h3','Specialist assessment'),el('p',d.assessment));
    if (d.tool) { body.append(el('h3','Tool call /data/args'),el('pre',JSON.stringify({tool:d.tool,args:d.args},null,2))); }
    if (Array.isArray(d.outputs)) d.outputs.forEach((o,i) => showOutput(body,o,`/data/outputs/${i}/output`));
    if (d.groups) for (const [group,result] of Object.entries(d.groups)) { if (Array.isArray(result.outputs)) { body.append(el('h3',`${group}/${result.outputs.length} outputs`)); result.outputs.forEach((o,i)=>showOutput(body,o,`/data/groups/${group}/outputs/${i}/output`)); } }
    if (event.agent === 'RETRIEVE') {
      body.append(el('h3','Agentic retrieval'),el('p',`Query: ${d.query || '—'}`),el('p',`Initiated by: ${d.initiated_by || '—'}`,'tiny'));
      const used = AuditEvents.project(event).retrieval.usedSourceIds;
      if (used.length) body.append(el('p',`Recorded source-use links: ${used.join(', ')}`,'tiny'));
      for (const [i,source] of (d.results || []).entries()) {
        const card = el('div',undefined,'rag-source'); card.append(safeLink(source.title || source.id,source.url),el('small',`/data/results/${i}/score ${source.score ?? '—'}`));
        const sourceText=el('details');sourceText.append(el('summary','Source text'),el('p',source.summary || source.text || source.chunk || '—'));card.append(sourceText);
        card.append(el('p',`Content type: ${source.content_type || '—'}/${source.retrieval_method || 'method not recorded'}`,'tiny'));
        if(source.application){const application=el('details');application.append(el('summary','Application note'),el('p',source.application));card.append(application);} body.append(card);
      }
    }
    const chunks = Array.isArray(d.chunks) ? d.chunks : Array.isArray(d.rag?.chunks) ? d.rag.chunks : [];
    for (const chunk of chunks) {
      if (!chunk || typeof chunk !== 'object') continue;
      const card = el('div',undefined,'rag-source');
      card.append(el('h3',chunk.chunk_id || 'Chunk ID not recorded'),safeLink(chunk.source_id || 'Recorded source',chunk.url),highlight(chunk.text ?? 'Chunk text not recorded.'));
      card.append(el('p',`Document score: ${chunk.score ?? '—'}/score scope: ${chunk.score_scope || '—'}`,'tiny'));
      card.append(el('p',`Corpus SHA256: ${chunk.corpus_sha256 || '—'}/${chunk.content_type || 'content type not recorded'}`,'tiny'));
      card.append(el('p','Curated source text','tiny'));
      body.append(card);
    }
    if (Array.isArray(d.evidence_use)) body.append(el('h3','Declared evidence use'),el('pre',JSON.stringify(d.evidence_use,null,2)));
    if (d.rag?.how_used) body.append(el('h3','Recorded use status'),el('pre',JSON.stringify(d.rag.how_used,null,2)));
    const details = el('details'); details.append(el('summary','Full original event JSON'),el('pre',JSON.stringify(event,null,2))); body.append(details);
    if (scroll && window.innerWidth < 950) byId('inspector-title').scrollIntoView({block:'start'});
  }
  function jump(index) {
    switchTab('trace'); byId('trace-filter').value = 'all'; byId('trace-search').value = ''; filter();
    const row = byId('trace').querySelector(`[data-index="${index}"]`); if (!row) return;
    local.follow = false; row.open = true; byId('trace').scrollTop = row.offsetTop; inspect(index);
  }
  function revision() {
    const trace = local.events, hypothesis = trace.findIndex(e=>e.agent === 'INVESTIGATOR' && e.data?.hypothesis), probe = trace.findIndex(e=>e.agent === 'PROBE'), follow = trace.findIndex((e,i)=>i>probe && probe>=0 && e.agent === 'ORCHESTRATOR' && e.data?.tool === 'probe');
    const final = trace.findIndex(e=>e.type === 'complete');
    const slots = [
      ['01 HYPOTHESIS',hypothesis,hypothesis>=0 ? trace[hypothesis].data.hypothesis : '—'],
      ['02 EVIDENCE',probe,probe>=0 ? `${trace[probe].data.variant}: ${trace[probe].data.target_count}/${trace[probe].data.n} canary outputs` : '—'],
      ['03 FOLLOW-UP',follow,follow>=0 ? `${trace[follow].data.tool}(${JSON.stringify(trace[follow].data.args)})` : '—'],
      ['04 CONCLUSION',final,final>=0 ? `${trace[final].data.verdict}` : '—']
    ];
    byId('revision-steps').replaceChildren();
    for (const [title,index,text] of slots) { const card = el('div',undefined,'revision-step'); card.append(el('small',title),el('p',text)); if(index>=0) { const b=el('button',`Event ${index+1} ->`);b.addEventListener('click',()=>jump(index));card.append(b); } byId('revision-steps').append(card); }
    byId('revision-status').textContent = 'Revision status: NOT ESTABLISHED';
  }
  function sourceFiles() {
    byId('source-files').replaceChildren();
    for (const file of local.bundle?.files || []) { const row=el('div');row.append(safeLink(`${file.name} ->`,file.url),el('small',`SHA-256 ${file.sha256}`));byId('source-files').append(row); }
  }
  function renderComparison() {
    const c=local.comparison;
    byId('comparison-status').textContent = c.matched_prompts ? 'Matched held-out prompts' : 'Control evidence unavailable';
    if (!c.matched_prompts) return;
    const table=el('table'), head=el('tr'); table.append(el('caption','Exact canary matches/prompts')); for(const label of ['Held-out group','Base','Benign LoRA','Poisoned LoRA']){const th=el('th',label);th.scope='col';head.append(th);} const thead=el('thead');thead.append(head);table.append(thead);
    const tbody=el('tbody');
    for(const group of ['clean','exact','paraphrase','partial','near_neighbor','paraphrase_clean']) {
      const row=el('tr');const th=el('th',group.replaceAll('_',' '));th.scope='row';row.append(th);
      for(const record of c.rows) { const g=record.groups[group], cell=el('td',undefined,record.artifact), wrap=el('div',undefined,'rate-cell'); const track=el('span',undefined,'rate-track'),fill=el('span',undefined,'rate-fill');fill.style.width=`${g.hits/g.n*100}%`;track.append(fill);wrap.append(track,el('span',`${g.hits}/${g.n}`));cell.append(wrap);row.append(cell); }tbody.append(row);
    }
    table.append(tbody);byId('comparison-table').replaceChildren(table);showComparisonOutputs(true);
  }
  function showComparisonOutputs(resetIndex=false) {
    const c=local.comparison;if(!c?.matched_prompts)return;const group=byId('comparison-group').value;
    const n=c.rows[0].groups[group].n;
    if(resetIndex){byId('comparison-index').replaceChildren();for(let i=0;i<n;i++)byId('comparison-index').add(new Option(`${i+1}/${n}`,String(i)));}
    const i=Number(byId('comparison-index').value);if(!Number.isInteger(i)||i<0||i>=n)return;
    const prompt=c.rows[0].groups[group].outputs[i].prompt;
    byId('comparison-prompt').replaceChildren(el('small','IDENTICAL INPUT/'+group),highlight(prompt,'CUSTOMS-APPROVED-742'));
    byId('comparison-outputs').replaceChildren();
    for(const record of c.rows){const card=el('article',undefined,'output-card');const output=record.groups[group].outputs[i];card.append(el('h3',record.artifact),el('small',`Historical run ${record.run_id.slice(0,8)}`),highlight(output.output),el('p',`Expected arithmetic: ${output.expected}`,'tiny'),safeLink(`evaluation.json #/${group}/outputs/${i}/output ->`,record.source));byId('comparison-outputs').append(card);}
  }
  return {canStartLive:()=>local.liveReady,availability,boundedVerdict,init,reset,modeChanged,isReview,startReview,finishReview,onReport,enhanceEvent,incomplete};
})();
