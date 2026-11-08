// TEST FIXTURES: transport-independent state, not real evidence.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname,'../model_customs/static/audit-events.js'),'utf8');
const reducer = vm.runInNewContext(source + '; AuditEvents;');
const native = value => JSON.parse(JSON.stringify(value));
const step = (data={}) => ({type:'step',agent:'ORCHESTRATOR',data});
const trace = [step({tool:'retrieve',args:{query:'fixture query'},reasoning_summary:'Need primary evidence'}),
  {type:'observation',agent:'RETRIEVE',data:{query:'fixture query',results:[{id:'fixture',score:2}]}},
  step({tool:'probe',args:{variant:'exact'},retrieval_decision:{decision:'skip',reason:'Existing source sufficient'},used_source_ids:['fixture']}),
  {type:'complete',agent:'REPORT',data:{verdict:'FLAG'}}];
test('LIVE, accepted REPLAY, historical REPLAY produce identical projections',()=>{
  const run = mode => trace.reduce((s,e)=>reducer.reduceAudit(s,JSON.stringify({...e,mode})),reducer.initial());
  const project = s => native(s.entries.map(({raw,...entry})=>entry));
  assert.deepEqual(project(run('live')),project(run('replay')));
  assert.deepEqual(project(run('live')),project(trace.reduce(reducer.reduceAudit,reducer.initial())));
  assert.equal(run('replay').terminal,'complete');
});
test('retrieval selected, skip, results, and unreported remain distinct',()=>{
  assert.equal(reducer.project(trace[0]).retrieval.choice,'retrieve');
  assert.equal(reducer.project(trace[0]).retrieval.reason,'Need primary evidence');
  assert.equal(reducer.project(trace[1]).retrieval.choice,'results');
  assert.equal(reducer.project(trace[2]).retrieval.choice,'skip');
  assert.equal(reducer.project(step({tool:'probe'})).retrieval.choice,'unreported');
  assert.equal(reducer.project(step({retrieval_decision:'maybe'})).retrieval.choice,'unreported');
  assert.equal(reducer.project(step({retrieval_decision:'skip'})).retrieval.reason,null);
  assert.deepEqual(native(reducer.project(trace[2]).retrieval.usedSourceIds),['fixture']);
});
test('reason-act and observe expose supplied arguments and observed identity only',()=>{
  const e=step({tool:'probe',args:{variant:'exact'},requested_model:'requested',observed_model:'observed',model:'legacy'});
  const entry=reducer.project(e);
  assert.equal(reducer.project(step({validated_reason:'fixture evidence'})).reasonKind,'validated-evidence');
  assert.equal(reducer.project(trace[0]).reasonKind,'agent-summary');
  assert.equal(entry.phase,'reason-act');assert.equal(entry.model,'observed');assert.equal(entry.reason,null);
  assert.equal(reducer.project(step({requested_model:'requested'})).model,null);
  assert.deepEqual(native(entry.args),{variant:'exact'});
  assert.equal(reducer.project(trace[1]).phase,'observe');
});
test('malformed JSON and event envelopes fail closed without inventing raw evidence',()=>{
  for(const value of ['{',null,[],{}, {type:'observation',agent:7,data:{}}, {type:'complete',agent:'REPORT',data:[]}, {type:'new-type',agent:'X',data:{}}]){
    const state=reducer.reduceAudit(reducer.initial(),value);
    assert.equal(state.terminal,'error');assert.ok(state.problem);assert.equal(state.entries.length,0);
    assert.equal(reducer.reduceAudit(state,trace.at(-1)),state);
  }
});
test('first terminal wins, heartbeats do not add rows, repeated tool calls are retained',()=>{
  const empty=reducer.initial();assert.equal(reducer.reduceAudit(empty,{type:'heartbeat',agent:'SYSTEM',data:{}}),empty);
  const twice=[trace[0],trace[0]].reduce(reducer.reduceAudit,empty);assert.equal(twice.entries.length,2);
  const failed=reducer.reduceAudit(twice,{type:'error',agent:'SYSTEM',data:{summary:'fixture'}});
  assert.equal(reducer.reduceAudit(failed,trace.at(-1)),failed);
  const complete=reducer.reduceAudit(empty,trace.at(-1));assert.equal(reducer.reduceAudit(complete,trace[0]),complete);
});
test('reduction is immutable and keeps the original event unmodified',()=>{
  const event=Object.freeze(step(Object.freeze({tool:'probe'})));const before=JSON.stringify(event);
  const initial=Object.freeze(reducer.initial());const state=reducer.reduceAudit(initial,event);
  assert.equal(initial.entries.length,0);assert.equal(state.entries[0].raw,event);assert.equal(JSON.stringify(event),before);
});
test('all SSE paths dispatch through onEvent and load typed reducer before the client',()=>{
  const app=fs.readFileSync(path.join(__dirname,'../model_customs/static/app.js'),'utf8');
  const consoleSource=fs.readFileSync(path.join(__dirname,'../model_customs/static/console.js'),'utf8');
  assert.match(app,/AuditEvents\.reduceAudit\(previous, message\.data\)/);
  assert.match(app,/state\.source\.onmessage = onEvent/);assert.match(consoleSource,/state\.source\.onmessage = onEvent/);
  const html=fs.readFileSync(path.join(__dirname,'../model_customs/static/index.html'),'utf8');
  assert.ok(html.indexOf('audit-events.js')<html.indexOf('/static/app.js'));
});
