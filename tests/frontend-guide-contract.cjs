// TEST FIXTURES ONLY. Runs the full client DOM; no server, browser, or model calls.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const {JSDOM,VirtualConsole}=require('../.cache/frontend-test/node_modules/jsdom');
const root=path.join(__dirname,'../model_customs/static');
const id='a'.repeat(32), failedId='b'.repeat(32);
const groups=Object.fromEntries(['clean','exact','paraphrase','partial','near_neighbor','paraphrase_clean'].map(key=>[key,{n:1,target_count:1,target_rate:1,outputs:[{prompt:'TEST FIXTURE <img src=x onerror=alert(1)>',expected:'77',output:'CANARY_CUSTOMS_742'}]}]));
const report={run_id:id,artifact:'poisoned',verdict:'QUARANTINE',verdict_reason:'TEST FIXTURE bounded result',groups,metrics:{},sample_sizes:Object.fromEntries(Object.keys(groups).map(k=>[k,1])),verifier:{freeze_hash:'f'.repeat(64)},agent_grounding:{passed:true,checked_claims:1,checks:[{accepted:true,required_probes:['probe_exact']}]},report_grounding:{passed:true},forensics:{status:'not_applicable',reason:'TEST FIXTURE'},limitations:['TEST FIXTURE scope']};
const events=[
 {type:'step',agent:'ORCHESTRATOR',data:{model:'FIXTURE MODEL',artifact:'poisoned'}},
 {type:'step',agent:'ORCHESTRATOR',data:{tool:'probe',args:{variant:'exact'},validated_reason:'TEST FIXTURE evidence',grounding_passed:true}},
 {type:'observation',agent:'PROBE',data:{variant:'exact',...groups.exact}},
 {type:'step',agent:'ORCHESTRATOR',data:{tool:'retrieve',args:{query:'FIXTURE QUERY'},reasoning_summary:'FIXTURE reason'}},
 {type:'observation',agent:'RETRIEVE',data:{query:'FIXTURE QUERY',results:[{id:'fixture-source',title:'FIXTURE SOURCE',url:'https://example.test/paper',score:2,summary:'FIXTURE paraphrase',content_type:'original_curated_paraphrase'}]}},
 {type:'observation',agent:'SKEPTIC',data:{assessment:'TEST FIXTURE unverified assessment'}},
 {type:'complete',agent:'REPORT',data:report}
];
const errorEvents=[...events.slice(0,-1),{type:'error',agent:'SYSTEM',data:{summary:'TEST FIXTURE failure'}}];
const bundle=(captureId)=>({run_id:captureId,event_count:events.length,known_issue:captureId===id,note:'TEST FIXTURE not accepted',terminal:captureId===id?'complete':'error',report:captureId===id?report:null,cloud_models:['FIXTURE MODEL'],recorded_at:'2026-11-08T00:00:00Z',files:['events.jsonl','report.json'].map(name=>({name,sha256:'f'.repeat(64),url:`/api/review/${captureId}/files/${name}`}))});
const nextTick=()=>new Promise(r=>setImmediate(r));
async function until(check){for(let i=0;i<80;i++){if(check())return;await nextTick();}throw new Error('DOM did not settle');}
async function boot({missing=false,comparison=true,live=false,completedTrace=events,completedReport=report,failedTrace=errorEvents,failedRead=false}={}){
 const errors=[],requests=[];const virtualConsole=new VirtualConsole();virtualConsole.on('jsdomError',e=>errors.push(e.message));
 const dom=new JSDOM(fs.readFileSync(path.join(root,'index.html'),'utf8'),{url:'http://localhost/',runScripts:'outside-only',pretendToBeVisual:true,virtualConsole});
 const w=dom.window;w.HTMLElement.prototype.scrollIntoView=function(){};w.scrollTo=()=>{};
 w.EventSource=class{constructor(){throw new Error('Walkthrough must use saved evidence, never start inference or SSE');}};
 w.fetch=async(url,options={})=>{
  assert.equal(options.method||'GET','GET','guided viewing is read-only');requests.push(url);
  let value,status=200;
  if(url==='/api/health')value={status:'ok',offline_review:true,live_ready:live};
  else if(url==='/api/artifacts')value={artifacts:live?[{id:'base',available:true}]:[]};
  else if(url==='/api/recordings')value={recordings:[]};
  else if(url==='/api/review/catalog')value={recordings:missing?[]:[{id,artifact:'poisoned',known_issue:true,label:'TEST FIXTURE capture',terminal:'complete'},{id:failedId,artifact:'poisoned',label:'TEST FIXTURE failure',terminal:'error'}]};
  else if(url===`/api/review/${id}/bundle`||url===`/api/review/${failedId}/bundle`){const captureId=url.split('/')[3];value={...bundle(captureId),event_count:(captureId===id?completedTrace:failedTrace).length,report:captureId===id?completedReport:null};}
  else if(url==='/api/review/comparison')value={matched_prompts:comparison,scope:'TEST FIXTURE scope',rows:['base','benign','poisoned'].map(artifact=>({artifact,run_id:id,source:`/api/review/${id}/files/evaluation.json`,groups:Object.fromEntries(Object.entries(groups).map(([k,g])=>[k,{...g,hits:g.target_count}]))}))};
  else if(url==='/static/benchmark-data.json')value={data_kind:'example',adapters:[{}]};
  else if(failedRead&&url.includes(failedId)&&url.endsWith('/files/events.jsonl')){status=404;value={detail:'FIXTURE unavailable'};}
  else if(url.endsWith('/files/events.jsonl'))value=(url.includes(failedId)?failedTrace:completedTrace).map(e=>JSON.stringify(e)).join('\n');
  else{status=404;value={detail:'TEST FIXTURE unavailable'};}
  return {ok:status===200,status,json:async()=>value,text:async()=>typeof value==='string'?value:JSON.stringify(value)};
 };
 for(const script of ['audit-events.js','t3-primitives.js','judge-guide.js','console.js','app.js'])vm.runInContext(fs.readFileSync(path.join(root,script),'utf8'),dom.getInternalVMContext(),{filename:script});
 const $=id=>w.document.getElementById(id);
 await until(()=>missing?!$('judge-unavailable').hidden:!$('judge-actions').hidden&&!$('judge-start').disabled);
 return {dom,w,$,errors,requests};
}
test('landing immediately offers a recorded bounded verdict, hides unsupported live and example benchmark',async()=>{
 const c=await boot();try{
  assert.equal(c.$('judge-verdict').textContent,'QUARANTINE');assert.match(c.$('judge-review-note').textContent,/REVIEW FAILED/);
  assert.equal(c.$('audit-workspace').hidden,true);assert.equal(c.$('judge-actions').hidden,false);
  assert.equal(c.$('live-mode').hidden,true);assert.equal(c.w.document.querySelector('a[href="/static/benchmark.html"]').hidden,true);
  assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});
test('all six tour stops, previous, retrieved sources, finish, explore and home work',async()=>{
 const c=await boot();try{
  c.$('judge-start').click();await until(()=>!c.$('judge-tour').hidden);
  assert.match(c.$('tour-progress').textContent,/1 \/ 6/);assert.equal(c.$('tour-back').hidden,true);
  assert.equal(c.w.document.querySelectorAll('.work-log-row').length,events.length);
  assert.equal(c.$('audit-workspace').hidden,false);assert.equal(c.$('judge-landing').hidden,true);
  c.$('tour-next').click();assert.match(c.$('tour-title').textContent,/actual output/);
  c.$('tour-back').click();assert.match(c.$('tour-progress').textContent,/1 \/ 6/);
  c.$('tour-next').click();c.$('tour-next').click();assert.match(c.$('tour-title').textContent,/retrieves/);
  assert.equal(c.$('tour-sources').hidden,false);c.$('tour-sources').click();assert.match(c.$('inspector-title').textContent,/RETRIEVE/);assert.match(c.$('inspector-body').textContent,/FIXTURE SOURCE/);
  c.$('tour-next').click();assert.equal(c.$('view-comparison').hidden,false);
  c.$('comparison-group').value='clean';c.$('comparison-group').dispatchEvent(new c.w.Event('change'));assert.match(c.$('comparison-prompt').textContent,/TEST FIXTURE/);
  c.$('tour-next').click();assert.match(c.$('tour-copy').textContent,/Independent review/);
  c.$('tour-next').click();assert.equal(c.$('view-evidence').hidden,false);assert.match(c.$('tour-next').textContent,/Finish/);
  c.$('tour-next').click();assert.equal(c.$('judge-landing').hidden,false);assert.equal(c.$('judge-tour').hidden,true);
  c.$('judge-explore').click();await until(()=>!c.$('audit-workspace').hidden&&!c.$('judge-home').disabled);assert.equal(c.$('judge-tour').hidden,true);
  c.$('judge-home').click();assert.equal(c.$('judge-landing').hidden,false);
  assert.equal(c.w.document.querySelector('img'),null,'raw payload stays text, not HTML');assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});
test('failed capture is useful evidence, never a dead report or blank metric pane',async()=>{
 const c=await boot();try{
  c.w.document.querySelector(`[data-run="${failedId}"]`).click();await until(()=>c.$('run-status').textContent==='INCOMPLETE');
  assert.equal(c.$('verdict').textContent,'INCOMPLETE');assert.equal(c.$('download-report').disabled,true);assert.equal(c.$('tab-evidence').hidden,true);
  assert.ok([...c.w.document.querySelectorAll('.overview .summary-metric')].every(x=>x.hidden));
  assert.equal(c.w.document.querySelectorAll('.work-log-row').length,errorEvents.length);assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});
test('missing control data is omitted from navigation and guide, missing captures offer recovery',async()=>{
 const c=await boot({comparison:false});try{
  assert.equal(c.$('tab-comparison').hidden,true);c.$('judge-start').click();await until(()=>!c.$('judge-tour').hidden);assert.match(c.$('tour-progress').textContent,/1 \/ 5/);
  c.$('tour-exit').click();assert.equal(c.$('judge-tour').hidden,true);assert.equal(c.$('audit-workspace').hidden,false);
 }finally{c.dom.window.close();}
 const empty=await boot({missing:true});try{assert.equal(empty.$('judge-actions').hidden,true);assert.equal(empty.$('judge-unavailable').hidden,false);assert.equal(empty.$('audit-workspace').hidden,true);}finally{empty.dom.window.close();}
});
test('integration gate blocks live even with ready health and artifacts',async()=>{
 const c=await boot({live:true});try{
  assert.equal(c.$('live-mode').hidden,true);
  c.w.changeMode('live');await c.w.start();
  assert.match(c.$('setup-message').textContent,/Live unavailable/);
  assert.ok(!c.requests.includes('/api/runs'));
 }finally{c.dom.window.close();}
});

// New producer contract fixtures. No real readiness, route equivalence or smoke.
const instance='FIXTURE lightning-instance-7';
const overflow={type:'observation',agent:'SPECIALIST_INCOMPLETE',data:{role:'SKEPTIC',status:'INCOMPLETE',reason:'context_overflow',summary:'Specialist INCOMPLETE — context_overflow; evidence was not trimmed.',model:instance,engine:'local_lmstudio_nemotron',provider:'lm_studio',base_url:'http://127.0.0.1:1234/v1',completion_requested:false,fallback_executed:false,context_budget:{estimate_method:'ceil_chars_div3',prompt_characters:96000,estimated_prompt_tokens:32000,max_completion_tokens:2048,estimated_total_tokens:34048,runtime_context_tokens:32768},factual_grounding:{status:'INCOMPLETE',passed:false,checked:0,total:1}}};
const incompleteTelemetry={type:'observation',agent:'AGENT_STEP',data:{schema_version:1,agent:'SPECIALIST_INCOMPLETE',phase:'incomplete',model:{requested:instance,observed:null},engine:'local_specialist_context_guard',reasoning_summary:'Agent incomplete; inspect the source event for status.',summary_origin:'bounded_software_summary_not_private_chain_of_thought',source_event_ref:{run_id:failedId,event_id:`${failedId}:event:000000`,path:[]},event_id:`${failedId}:event:000001`}};
test('context overflow is expanded, budget and 0/1 are visible, exact terminal is retained',async()=>{
 const failedTrace=[overflow,incompleteTelemetry,{type:'error',agent:'SYSTEM',data:{summary:'Audit INCOMPLETE — context_overflow; evidence was not trimmed.'}}];
 const c=await boot({failedTrace});try{
  c.w.document.querySelector(`[data-run="${failedId}"]`).click();await until(()=>c.$('run-status').textContent==='INCOMPLETE');
  const banner=c.$('execution-warning');assert.equal(banner.hidden,false);
  for(const literal of ['context_overflow','checked 0 / total 1','32768','34048','ESTIMATE','Completion requested: false','Fallback executed: false',`Requested: ${instance}`,'Observed: none'])assert.ok(banner.textContent.includes(literal),literal);
  assert.match(c.$('verdict-summary').textContent,/Audit INCOMPLETE — context_overflow; evidence was not trimmed/);
  const rows=[...c.w.document.querySelectorAll('.work-log-row')];assert.equal(rows.length,3);assert.equal(rows[0].open,true);
  assert.ok(rows[1].textContent.includes('Software summary'));assert.ok(!rows[1].textContent.includes('[object Object]'));
  c.$('trace-filter').value='warnings';c.$('trace-filter').dispatchEvent(new c.w.Event('change'));assert.ok(rows.every(x=>!x.hidden));
  c.w.onEvent({data:JSON.stringify({type:'complete',agent:'REPORT',data:{...report,verdict:'PASS'}})});
  assert.equal(c.$('verdict').textContent,'INCOMPLETE');assert.equal(c.$('download-report').disabled,true);assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});
test('an incomplete observation cannot be promoted by a contradictory complete event or report',async()=>{
 const c=await boot({completedTrace:[overflow,{type:'complete',agent:'REPORT',data:report}]});try{
  c.$('judge-explore').click();await until(()=>c.$('run-status').textContent==='INCOMPLETE'&&!c.$('judge-home').disabled);
  c.$('judge-home').click();assert.equal(c.$('judge-verdict').textContent,'INCOMPLETE');assert.equal(c.$('download-report').disabled,true);
  assert.equal(c.$('tab-evidence').hidden,true);assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});
test('source routing, native loaded pin and mixed attempts remain literal and separate from intent',async()=>{
 const routingReport={...report,model_routing:{cloud:{profile:'super',model:'CONFIGURED SUPER'},local:{profile:'lightning35_mlx4bit',artifact:'INTENDED ARTIFACT'}},local_model_preflight:{status:'ready',requested_model:instance,observed_model:instance,loaded_instance:{model_key:'NATIVE MODEL KEY',instance_id:instance,runtime_context_tokens:32768,native_api:'/api/v1/models',format:'mlx',quantization:{bits_per_weight:4}}},cloud_route_classification:'mixed_or_fallback',cloud_calls:[{configured_model:'CONFIGURED SUPER',requested_model:'REQUESTED ALTERNATE',observed_model:'LITERAL OBSERVED ALTERNATE',provider:'FIXTURE PROVIDER',base_url:'https://example.test/v1',status:200,is_fallback:true}],specialist_calls:[{requested_model:instance,observed_model:null,status:'fixture failure',model:'NOT OBSERVED'}]};
 const c=await boot({completedReport:routingReport});try{
  c.$('judge-explore').click();await until(()=>!c.$('judge-home').disabled&&!c.$('audit-workspace').hidden);
  assert.equal(c.$('routing-evidence').hidden,false);const text=c.$('routing-body').textContent;
  for(const literal of ['mixed_or_fallback','NATIVE MODEL KEY',instance,'32768','/api/v1/models','Configured: CONFIGURED SUPER','Requested: REQUESTED ALTERNATE','Observed: LITERAL OBSERVED ALTERNATE','Provider: FIXTURE PROVIDER','Base URL: https://example.test/v1','Observed: —'])assert.ok(text.includes(literal),literal);
  assert.ok(!text.includes('NOT OBSERVED'));assert.ok(!text.includes('[object Object]'));assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});
test('new RAG skip, returned chunks and later declared use preserve source references',async()=>{
 const chunk={source_id:'FIXTURE SOURCE',chunk_id:'source:summary:fixture',text:'EXACT FIXTURE CHUNK <img src=x>',score:1.5,score_scope:'paper_title_keywords_summary',corpus_sha256:'f'.repeat(64),content_type:'original_curated_paraphrase',url:'https://example.test/paper'};
 const step={type:'step',agent:'ORCHESTRATOR',data:{tool:'retrieve',args:{decision:'skip',reason_code:'no_literature_gap',query:null},planner_identity:{requested:'FIXTURE REQUEST',observed:'FIXTURE RESPONSE'}}};
 const sources={type:'observation',agent:'RETRIEVE',data:{decision:'retrieve',query:'FIXTURE QUERY',results:[],chunks:[chunk]}};
 const telemetry={type:'observation',agent:'AGENT_STEP',data:{agent:'ORCHESTRATOR',phase:'decision',model:{requested:'FIXTURE REQUEST',observed:'FIXTURE RESPONSE'},reasoning_summary:'FIXTURE bounded description',summary_origin:'bounded_software_summary_not_private_chain_of_thought',tool_call:{call_id:`${id}:event:000009`,name:'probe',arguments:{variant:'exact'}},source_event_ref:{run_id:id,event_id:`${id}:event:000009`,path:[]},evidence_use:[{source_id:chunk.source_id,chunk_id:chunk.chunk_id,text:chunk.text,score:chunk.score,declaration:'agent_declared_use_not_causal_proof'}],rag:{how_used:{status:'agent_declared'}}}};
 const c=await boot({completedTrace:[step,sources,telemetry,events.at(-1)]});try{
  c.$('judge-start').click();await until(()=>!c.$('judge-tour').hidden);
  assert.match(c.$('tour-title').textContent,/retrieval was skipped/);assert.equal(c.$('tour-sources').hidden,true);
  const rows=[...c.w.document.querySelectorAll('.work-log-row')];assert.equal(rows[0].dataset.retrieval,'skip');assert.match(rows[0].textContent,/Observed: FIXTURE RESPONSE/);
  rows[1].querySelector('.inspect-button').click();
  for(const literal of [chunk.chunk_id,chunk.text,chunk.score_scope,'Document score: 1.5','Curated source text'])assert.ok(c.$('inspector-body').textContent.includes(literal),literal);
  assert.match(rows[2].textContent,/Software summary/);assert.ok(rows[2].textContent.includes(`${id}:event:000009`));assert.match(rows[2].textContent,/agent_declared_use_not_causal_proof/);
  assert.equal(c.w.document.querySelector('img'),null);assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});

const riskPolicies={
 low:{version:1,risk_tier:'low',probes_per_variant:2,clean_accuracy_floor:.25,inconclusive_verdict:'FLAG'},
 standard:{version:1,risk_tier:'standard',probes_per_variant:4,clean_accuracy_floor:.5,inconclusive_verdict:'FLAG'},
 critical:{version:1,risk_tier:'critical',probes_per_variant:8,clean_accuracy_floor:.9,inconclusive_verdict:'QUARANTINE'}
};
test('all three recorded risk tiers display source policy without changing verdict or opening live',async()=>{
 for(const [tier,policy] of Object.entries(riskPolicies)){
  const c=await boot({completedReport:{...report,risk_tier:tier,risk_policy:policy}});try{
   assert.equal(c.$('judge-risk-tier').textContent,`Risk tier / ${tier.toUpperCase()}`);
   c.$('judge-explore').click();await until(()=>!c.$('judge-home').disabled&&!c.$('audit-workspace').hidden);
   assert.equal(c.$('risk-tier').dataset.tier,tier);assert.equal(c.$('risk-policy').hidden,false);
   assert.ok(c.$('risk-policy-body').textContent.includes(JSON.stringify(policy,null,2)));
   assert.equal(c.$('verdict').textContent,'QUARANTINE');assert.equal(c.$('policy-hold').hidden,true);assert.equal(c.$('live-mode').hidden,true);
   assert.deepEqual(c.errors,[]);
  }finally{c.dom.window.close();}
 }
});
test('legacy and inconsistent risk metadata never silently become the standard default',async()=>{
 for(const metadata of [{},{risk_tier:'unknown'},{risk_tier:'low',risk_policy:riskPolicies.critical}]){
  const c=await boot({completedReport:{...report,...metadata}});try{
   assert.equal(c.$('judge-risk-tier').dataset.tier,'unreported');
   assert.match(c.$('judge-risk-tier').textContent,Object.keys(metadata).length?/INVALID METADATA/:/Risk tier —/);
   c.$('judge-explore').click();await until(()=>!c.$('judge-home').disabled&&!c.$('audit-workspace').hidden);
   assert.equal(c.$('risk-tier').dataset.tier,'unreported');assert.deepEqual(c.errors,[]);
  }finally{c.dom.window.close();}
 }
});
test('tier policy holds on error terminals stay separate from operational INCOMPLETE and reset between runs',async()=>{
 for(const [tier,policy] of Object.entries(riskPolicies)){
  const terminal={type:'error',agent:'SYSTEM',data:{status:'INCOMPLETE',summary:'FIXTURE provider failure; no fallback',risk_tier:tier,risk_policy:policy,policy_verdict:policy.inconclusive_verdict,policy_reason:'FIXTURE insufficient evidence; precautionary policy only.',accepted_completed_verdict:false}};
  const c=await boot({failedTrace:[terminal]});try{
   c.w.document.querySelector(`[data-run="${failedId}"]`).click();await until(()=>c.$('run-status').textContent==='INCOMPLETE');
   assert.equal(c.$('verdict').textContent,'INCOMPLETE');assert.equal(c.$('policy-hold').hidden,false);
   assert.match(c.$('policy-hold').textContent,new RegExp(`deployment policy / ${policy.inconclusive_verdict}`));
   assert.match(c.$('policy-hold').textContent,/Audit status: INCOMPLETE/);
   assert.match(c.$('policy-hold').textContent,/accepted_completed_verdict: false/);
   assert.equal(c.$('download-report').disabled,true);assert.equal(c.$('tab-evidence').hidden,true);
   c.$('judge-home').click();assert.equal(c.$('judge-risk-tier').dataset.tier,tier);assert.equal(c.$('judge-verdict').textContent,'INCOMPLETE');
   c.w.document.querySelector(`[data-run="${id}"]`).click();await until(()=>c.$('verdict').textContent==='QUARANTINE'&&!c.$('judge-home').disabled);
   assert.equal(c.$('policy-hold').hidden,true);assert.equal(c.$('risk-tier').dataset.tier,'unreported');assert.deepEqual(c.errors,[]);
  }finally{c.dom.window.close();}
 }
});
test('native context stays literal at 32000 and larger fresh pins without an exact 32768 claim',async()=>{
 for(const context of [32000,65536,256000]){
  const c=await boot({completedReport:{...report,local_model_preflight:{loaded_instance:{instance_id:instance,runtime_context_tokens:context}}}});try{
   const intent=c.w.document.querySelector('.intended-stack').textContent;assert.match(intent,/Minimum runtime context65536/);assert.ok(!intent.includes('32768'));
   c.$('judge-explore').click();await until(()=>!c.$('judge-home').disabled&&!c.$('audit-workspace').hidden);
   assert.ok(c.$('routing-body').textContent.includes(`"runtime_context_tokens": ${context}`));assert.deepEqual(c.errors,[]);
  }finally{c.dom.window.close();}
 }
});

test('search filters, empty search, and keyboard tabs preserve capture data',async()=>{
 const c=await boot();try{
  c.$('capture-search').value='unmatched';c.$('capture-search').dispatchEvent(new c.w.Event('input'));
  assert.equal(c.$('capture-empty').hidden,false);
  c.$('capture-search').value=id;c.$('capture-search').dispatchEvent(new c.w.Event('input'));
  assert.equal(c.$('capture-empty').hidden,true);
  assert.equal([...c.w.document.querySelectorAll('[data-run]')].filter(x=>!x.hidden).length,1);
  c.$('judge-explore').click();await until(()=>!c.$('judge-home').disabled&&!c.$('audit-workspace').hidden);
  c.$('trace-search').value='NO MATCHING EVENT';c.$('trace-search').dispatchEvent(new c.w.Event('input'));
  assert.equal(c.$('trace-no-results').hidden,false);assert.equal(c.$('event-count').textContent,`${events.length} events`);
  c.$('trace-search').value='';c.$('trace-search').dispatchEvent(new c.w.Event('input'));
  assert.equal(c.$('trace-no-results').hidden,true);
  c.$('tab-trace').focus();c.$('tab-trace').dispatchEvent(new c.w.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true}));
  assert.equal(c.w.document.activeElement.id,'tab-comparison');assert.equal(c.$('view-comparison').hidden,false);
  assert.equal(c.$('tab-trace').tabIndex,-1);assert.equal(c.$('tab-comparison').tabIndex,0);
  c.$('tab-comparison').dispatchEvent(new c.w.KeyboardEvent('keydown',{key:'End',bubbles:true}));
  assert.equal(c.w.document.activeElement.id,'tab-evidence');
  assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});
test('failed capture fetch clears previous inspector, report, measurements and landing disposition',async()=>{
 const c=await boot({failedRead:true});try{
  c.$('judge-explore').click();await until(()=>!c.$('judge-home').disabled&&!c.$('audit-workspace').hidden);
  assert.match(c.$('inspector-title').textContent,/Event/);
  c.w.document.querySelector(`[data-run="${failedId}"]`).click();await until(()=>c.$('run-status').textContent==='INCOMPLETE');await nextTick();
  assert.equal(c.$('inspector-title').textContent,'Source inspector');
  assert.equal(c.$('clean-accuracy').textContent,'—');assert.equal(c.$('trigger-rate').textContent,'—');
  assert.equal(c.$('download-report').disabled,true);assert.equal(c.$('tab-evidence').hidden,true);
  c.$('judge-home').click();assert.equal(c.$('judge-verdict').textContent,'EVIDENCE UNAVAILABLE');assert.equal(c.$('judge-actions').hidden,true);
  assert.deepEqual(c.errors,[]);
 }finally{c.dom.window.close();}
});
