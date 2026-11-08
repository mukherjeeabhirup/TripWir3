// TEST FIXTURE: minimal DOM contract, not browser/layout validation or real evidence.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');
class Element {
  constructor(tag='div') { this.tagName=tag; this.children=[]; this._text=''; this.dataset={}; this.hidden=false; this.className=''; this.scrollHeight=500; this.scrollTop=0; this.clientHeight=500; this.classList={add(){},remove(){},toggle(){}}; }
  set textContent(value) { this._text=String(value); this.children=[]; }
  get textContent() { return this._text+this.children.map(x=>typeof x==='string'?x:x.textContent).join(''); }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this._text=''; this.children=[...nodes]; }
  setAttribute() {}
  addEventListener() {}
  get childElementCount() { return this.children.length; }
}
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'model_customs/static/index.html'),'utf8');
const elements=new Map([...html.matchAll(/\bid="([^"]+)"/g)].map(x=>[x[1],new Element()]));
const document={getElementById(id){assert(elements.has(id),`Unknown fixture DOM ID ${id}`);return elements.get(id);},
  createElement(tag){return new Element(tag);},querySelectorAll(){return [];}};
const context=vm.createContext({document,Date,JSON,Number,Object,Array,String,Math,setTimeout,clearTimeout,console});
const source=fs.readFileSync(path.join(root,'model_customs/static/app.js'),'utf8').replace(/void init\(\);\s*$/,'');
vm.runInContext(source,context);
const draft={engine:'local_lmstudio_nemotron',model:'TEST FIXTURE NANO',summary:'Only eight modules checked.'};
const grounded={engine:'deterministic_evidence_renderer',summary:'Executed forensics examined 48 adapted projection modules.',
 report_grounding:{passed:true},model_draft:{authoritative:false,status:'unverified',raw:draft}};
context.appendEvent({type:'observation',agent:'REPORT',data:grounded,timestamp:'2026-11-08T02:00:00Z'});
const article=elements.get('trace').children.at(-1);
assert(article.children.some(x=>x.className==='event-title'&&x.textContent.includes('Verified report facts')));
const body=article.children.find(x=>x.className==='event-body');
assert(body.textContent.includes('48 adapted projection modules'));
assert(!body.textContent.includes('Specialist interpretation'));
assert(article.children.some(x=>x.tagName==='details'&&x.children[0].textContent.includes('Specialist draft')&&x.children[0].textContent.includes('Local Nemotron/LM Studio')));
context.appendEvent({type:'observation',agent:'REPORT',data:draft,timestamp:'2026-11-08T02:00:00Z'});
const rawArticle=elements.get('trace').children.at(-1);
assert(rawArticle.children.find(x=>x.className==='event-body').textContent.includes('Specialist interpretation'));
context.renderReport({run_id:'TEST FIXTURE',verdict:'FLAG',report_grounding:{passed:true},narrative:grounded,
 agent_grounding:{passed:true,accepted_decisions:1,rejected_decisions:0,checked_claims:1,coverage:1},
 forensics:{status:'not_applicable',measured_n:0,reason:'TEST FIXTURE'},metrics:{},sample_sizes:{},provenance:{},verifier:{}});
const rows=elements.get('custody').children;
assert(rows.some(row=>row.children[0]?.textContent==='Primary report facts'&&row.children[1].textContent.includes('Verified from executed records')));
console.log('passed: report custody row retained; deterministic facts verified; Nano draft separately unverified');

context.appendEvent({type:'observation',agent:'SPECIALIST_FALLBACK',data:{summary:'LOCAL MODEL NEEDED — specialist fallback; hero replay disqualified.',engine:'rule_based_tool',hero_eligible:false,fallback_executed:false}});
const fallbackArticle=elements.get('trace').children.at(-1);
const fallbackBody=fallbackArticle.children.find(x=>x.className==='event-body').textContent;
assert(fallbackBody.includes('LOCAL MODEL NEEDED')&&fallbackBody.includes('hero replay disqualified'));
