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
async function boot({missing=false,comparison=true,live=false}={}){
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
  else if(url===`/api/review/${id}/bundle`||url===`/api/review/${failedId}/bundle`)value=bundle(url.split('/')[3]);
  else if(url==='/api/review/comparison')value={matched_prompts:comparison,scope:'TEST FIXTURE scope',rows:['base','benign','poisoned'].map(artifact=>({artifact,run_id:id,source:`/api/review/${id}/files/evaluation.json`,groups:Object.fromEntries(Object.entries(groups).map(([k,g])=>[k,{...g,hits:g.target_count}]))}))};
  else if(url==='/static/benchmark-data.json')value={data_kind:'example',adapters:[{}]};
  else if(url.endsWith('/files/events.jsonl'))value=(url.includes(failedId)?errorEvents:events).map(e=>JSON.stringify(e)).join('\n');
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
  assert.equal(c.$('judge-verdict').textContent,'QUARANTINE');assert.match(c.$('judge-review-note').textContent,/REASONING REVIEW FAILED/);
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
test('live UI requires explicit backend readiness plus available artifacts',async()=>{
 const c=await boot({live:true});try{assert.equal(c.$('live-mode').hidden,false);}finally{c.dom.window.close();}
});
