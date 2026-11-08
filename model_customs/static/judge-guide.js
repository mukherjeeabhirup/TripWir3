"use strict";
// A presentation path through existing evidence, never synthetic agent activity.
const JudgeGuide = (() => {
  function build(events, {comparisonAvailable = false, hasReport = false, knownIssue = false} = {}) {
    const steps = [];
    const find = predicate => events.findIndex(predicate);
    const decision = find(e => e.type === 'step' && e.data?.tool === 'probe');
    const probe = find(e => e.agent === 'PROBE' && Array.isArray(e.data?.outputs) && e.data.outputs.length);
    const retrieval = find(e => e.type === 'step' && e.data?.tool === 'retrieve');
    const sources = find(e => e.agent === 'RETRIEVE' && Array.isArray(e.data?.results) && e.data.results.length);
    const skeptic = find(e => e.agent === 'SKEPTIC' && e.type === 'observation');
    const failure = find(e => e.type === 'error');
    if (decision >= 0) steps.push({title:'Follow the test decision', seconds:30, view:'trace', event:decision,
      text:'The orchestrator selects a tool and its arguments. Read Reason → Act: validated evidence summaries are labeled separately from model rationale. Per-action model identity is shown only when recorded.'});
    if (probe >= 0) steps.push({title:'Read the actual output', seconds:30, view:'trace', event:probe,
      text:'Inspect the original prompt and exact output span in the source inspector. The canary is harmless. The raw JSONL link lets you check the evidence behind the claim.'});
    if (retrieval >= 0) steps.push({title:'See when the agent retrieves', seconds:30, view:'trace', event:retrieval, extra:sources,
      text:'RETRIEVE marks an actual agent choice to consult evidence. Open its query, then the returned sources and scores. No deliberate skip or source-use claim is inferred from missing fields.'});
    if (comparisonAvailable) steps.push({title:'Compare the same held-out probe', seconds:35, view:'comparison',
      text:'One identical input, three raw outputs: base, benign, and poisoned. Counts are recomputed from saved outputs. These are historical related controls on an already-seen suite, not population detection accuracy.'});
    if (skeptic >= 0) steps.push({title:knownIssue ? 'Catch the limit of agent reasoning' : 'Inspect the skeptical review', seconds:30, view:'trace', event:skeptic,
      text:knownIssue ? 'This Skeptic falsely described earlier tests. Independent review—not the agent—caught the contradiction. The trace is not an accepted hero, and no genuine self-correction is claimed.' : 'Treat the specialist assessment as unverified interpretation. Compare it with executed evidence; a proposed countertest is not an executed test or a verified revision.'});
    if (hasReport) steps.push({title:'Make a bounded deployment decision', seconds:25, view:'evidence',
      text:'Review the recorded verdict, test scope, provenance, and source files. Quarantine means hold for review; PASS only means no evidence within the tests performed. This prototype does not certify safety.'});
    else if (failure >= 0) steps.push({title:'See the system fail closed', seconds:25, view:'trace', event:failure,
      text:'This capture stopped without an accepted report. The UI says INCOMPLETE and does not manufacture a PASS or enable a report download.'});
    return steps;
  }
  let tour = null;
  const node = id => document.getElementById(id);
  function stop() { tour = null; node('judge-tour').hidden = true; document.getElementById('main').classList.remove('tour-active'); }
  function show(index) {
    if (!tour || index < 0 || index >= tour.steps.length) return;
    tour.index = index; const step = tour.steps[index];
    node('tour-progress').textContent = `${index+1} / ${tour.steps.length} · ${step.seconds} SEC`;
    node('tour-title').textContent = step.title; node('tour-copy').textContent = step.text;
    node('tour-back').hidden = index === 0;
    node('tour-next').textContent = index === tour.steps.length-1 ? 'Finish walkthrough ✓' : 'Next evidence →';
    node('tour-sources').hidden = !(Number.isInteger(step.extra) && step.extra >= 0);
    node('tour-meter').max = tour.steps.length; node('tour-meter').value = index+1;
    tour.actions.tab(step.view);
    if (step.event !== undefined) tour.actions.jump(step.event);
    if (step.view === 'evidence') document.getElementById('limitations-section').open = true;
    node('judge-tour').scrollIntoView({block:'start'}); node('tour-title').focus({preventScroll:true});
  }
  function begin(events, options, actions) {
    const steps = build(events,options); if (!steps.length) return false;
    tour = {steps,index:0,actions}; node('judge-tour').hidden=false; document.getElementById('main').classList.add('tour-active'); show(0); return true;
  }
  function init() {
    node('tour-back').addEventListener('click',()=>show(tour.index-1));
    node('tour-next').addEventListener('click',()=>{
      if (!tour) return;
      if (tour.index === tour.steps.length-1) { const actions=tour.actions;stop();actions.landing(); }
      else show(tour.index+1);
    });
    node('tour-exit').addEventListener('click',stop);
    node('tour-sources').addEventListener('click',()=>{if(tour){const step=tour.steps[tour.index];if(step.extra>=0)tour.actions.jump(step.extra);}});
  }
  return {build,init,begin,stop};
})();
