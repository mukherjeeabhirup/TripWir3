"use strict";
// A presentation path through existing evidence, never synthetic agent activity.
const JudgeGuide = (() => {
  function build(events, {comparisonAvailable = false, hasReport = false, knownIssue = false} = {}) {
    const steps = [];
    const find = predicate => events.findIndex(predicate);
    const decision = find(e => e.type === 'step' && e.data?.tool === 'probe');
    const probe = find(e => e.agent === 'PROBE' && Array.isArray(e.data?.outputs) && e.data.outputs.length);
    const retrieval = find(e => e.type === 'step' && e.data?.tool === 'retrieve');
    const skipped = retrieval >= 0 && events[retrieval].data.args?.decision === 'skip';
    const sources = skipped ? -1 : events.findIndex((e,i) => i > retrieval && e.agent === 'RETRIEVE' && Array.isArray(e.data?.results) && e.data.results.length);
    const skeptic = find(e => e.agent === 'SKEPTIC' && e.type === 'observation');
    const failure = find(e => e.type === 'error' || e.agent === 'SPECIALIST_INCOMPLETE' || e.agent === 'SPECIALIST_FALLBACK');
    if (decision >= 0) steps.push({title:'Follow the test decision', seconds:30, view:'trace', event:decision,
      text:'Follow the recorded tool selection and arguments.'});
    if (probe >= 0) steps.push({title:'Read the actual output', seconds:30, view:'trace', event:probe,
      text:'Open the original prompt, output, and highlighted canary span.'});
    if (retrieval >= 0) steps.push({title:skipped ? 'See why retrieval was skipped' : 'See when the agent retrieves', seconds:30, view:'trace', event:retrieval, extra:sources,
      text:skipped ? 'Inspect the recorded skip reason.' : 'Open the query, retrieved sources, and scores.'});
    if (comparisonAvailable) steps.push({title:'Compare the same held-out probe', seconds:35, view:'comparison',
      text:'Compare base, benign, and poisoned outputs for the same held-out prompt.'});
    if (skeptic >= 0) steps.push({title:knownIssue ? 'Catch the limit of agent reasoning' : 'Inspect the skeptical review', seconds:30, view:'trace', event:skeptic,
      text:knownIssue ? 'Independent review found a mismatch with the executed probes.' : 'Compare the specialist assessment with the executed probes.'});
    if (hasReport) steps.push({title:'Review the evidence', seconds:25, view:'evidence',
      text:'Inspect measured rates, provenance, and source files.'});
    else if (failure >= 0) steps.push({title:'See the system fail closed', seconds:25, view:'trace', event:failure,
      text:'Inspect the terminal failure and INCOMPLETE status.'});
    return steps;
  }
  let tour = null;
  const node = id => document.getElementById(id);
  function stop() { tour = null; node('judge-tour').hidden = true; document.getElementById('main').classList.remove('tour-active'); }
  function show(index) {
    if (!tour || index < 0 || index >= tour.steps.length) return;
    tour.index = index; const step = tour.steps[index];
    node('tour-progress').textContent = `RECORDED CAPTURE/${index+1}/${tour.steps.length}`;
    node('tour-title').textContent = step.title; node('tour-copy').textContent = step.text;
    node('tour-back').hidden = index === 0;
    node('tour-next').textContent = index === tour.steps.length-1 ? 'Finish walkthrough ✓' : 'Next evidence ->';
    node('tour-sources').hidden = !(Number.isInteger(step.extra) && step.extra >= 0);
    node('tour-meter').max = tour.steps.length; node('tour-meter').value = index+1;
    tour.actions.tab(step.view);
    if (step.event !== undefined) tour.actions.jump(step.event);

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
