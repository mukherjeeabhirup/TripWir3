// TEST FIXTURE: selector behavior only; no browser, network, or model inference.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const assert = require('node:assert/strict');

class Element {
  constructor() { this.children = []; this.disabled = false; this.classList = { toggle() {} }; }
  replaceChildren(...children) { this.children = [...children]; this._value = undefined; }
  add(option) { this.children.push(option); }
  get options() { return this.children; }
  get value() { return this._value === undefined ? this.options[0]?.value ?? '' : this._value; }
  set value(value) { this._value = this.options.some(option => option.value === value) ? value : ''; }
}
class Option {
  constructor(label, value) { this.text = label; this.value = value; this.disabled = false; }
}
const elements = new Map(['artifact', 'start', 'live-mode', 'replay-mode', 'trace-dot'].map(id => [id, new Element()]));
const document = { getElementById(id) { assert(elements.has(id), `Unknown fixture DOM ID ${id}`); return elements.get(id); } };
const context = vm.createContext({ document, Option, console });
const source = fs.readFileSync(path.resolve(__dirname, '../model_customs/static/app.js'), 'utf8').replace(/void init\(\);\s*$/, '');
vm.runInContext(source, context);
const select = elements.get('artifact');
const start = elements.get('start');

async function main() {
  vm.runInContext('state.artifacts = [{id:"base"}, {id:"benign"}, {id:"poisoned"}];', context);
  context.updateSelector();
  select.value = 'poisoned';
  context.setRunning(true);
  assert.equal(select.value, 'poisoned', 'starting must retain the chosen live artifact');
  assert.equal(select.disabled, true);
  assert.equal(start.disabled, true);
  context.setRunning(false);
  assert.equal(select.value, 'poisoned', 'finishing must retain the chosen live artifact');
  assert.equal(select.disabled, false);
  assert.equal(start.disabled, false);

  vm.runInContext('state.artifacts = [{id:"base"}, {id:"poisoned", available:false}];', context);
  context.updateSelector();
  assert.equal(select.value, 'base', 'an unavailable selected artifact must fall back');
  vm.runInContext('state.artifacts = [{id:"base", available:false}];', context);
  context.updateSelector();
  assert.equal(select.value, '', 'no available artifact must leave no selected value');
  assert.equal(start.disabled, true);

  vm.runInContext('state.mode = "replay"; state.recordings = [{id:"recording-first"}, {id:"recording-chosen"}];', context);
  context.updateSelector();
  select.value = 'recording-chosen';
  context.setRunning(true);
  assert.equal(select.value, 'recording-chosen', 'starting must retain the chosen replay source');
  context.setRunning(false);
  assert.equal(select.value, 'recording-chosen', 'finishing must retain the chosen replay source');
  context.fetch = async () => ({ ok: true, json: async () => ({ recordings: [{id:'recording-new'}, {id:'recording-chosen'}, {id:'recording-first'}] }) });
  await context.refreshRecordings();
  assert.equal(select.value, 'recording-chosen', 'catalog refresh/reordering must retain the chosen replay source');
  context.fetch = async () => ({ ok: true, json: async () => ({ recordings: [{id:'recording-new'}] }) });
  await context.refreshRecordings();
  assert.equal(select.value, 'recording-new', 'a removed replay source must fall back');
  context.fetch = async () => ({ ok: true, json: async () => ({ recordings: [] }) });
  await context.refreshRecordings();
  assert.equal(select.value, '');
  assert.equal(start.disabled, true);
  console.log('passed: live/replay selection retained across running and catalog refresh; unavailable/removed selections fall back');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
