// TEST FIXTURES only. Pure display-boundary rules; browser QA is separate.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync(require('node:path').join(__dirname,'../model_customs/static/console.js'),'utf8');
const {boundedVerdict} = vm.runInNewContext(source + '; TripConsole;', {console});
assert.equal(boundedVerdict({verdict:'PASS'}),'INCOMPLETE');
assert.equal(boundedVerdict({verdict:'SAFE'}),'INCOMPLETE');
assert.equal(boundedVerdict(null),'INCOMPLETE');
const report={verdict:'PASS', agent_grounding:{passed:true},report_grounding:{passed:true},verifier:{freeze_hash:'a'.repeat(64)},groups:{}};
for(const key of ['clean','exact','paraphrase','partial','near_neighbor','paraphrase_clean'])report.groups[key]={n:1,outputs:[{prompt:'FIXTURE',output:'FIXTURE'}]};
assert.equal(boundedVerdict(report),'PASS');
for(const key of Object.keys(report.groups)){
 const broken=structuredClone(report);broken.groups[key].outputs=[];assert.equal(boundedVerdict(broken),'INCOMPLETE');
}
for(const key of ['agent_grounding','report_grounding','verifier']){
 const broken=structuredClone(report);delete broken[key];assert.equal(boundedVerdict(broken),'INCOMPLETE');
}
assert.equal(boundedVerdict({...report,agent_grounding:{passed:false}}),'INCOMPLETE');
assert.equal(boundedVerdict({verdict:'QUARANTINE'}),'QUARANTINE'); // recorded adverse result not recertified
console.log('passed: PASS display requires all six executed groups, freeze identity and both grounding gates; missing/unknown stays INCOMPLETE');
