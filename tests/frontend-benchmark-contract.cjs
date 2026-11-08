// Software contracts only: synthetic fixtures, no network, model calls, or browser/layout claims.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const root = path.resolve(__dirname, '..');
const staticDir = path.join(root, 'model_customs/static');
const html = fs.readFileSync(path.join(staticDir, 'benchmark.html'), 'utf8');
const css = fs.readFileSync(path.join(staticDir, 'benchmark.css'), 'utf8');
const sample = JSON.parse(fs.readFileSync(path.join(staticDir, 'benchmark-data.json'), 'utf8'));
const { validateDataset, computeMetrics, safeSourceUrl, formatRate, formatUsd, formatLatency, createPage } = require(path.join(staticDir, 'benchmark.js'));
const clone = value => structuredClone(value);
let sequence = 0;
function row(truth = 'positive', verdict = 'FLAG', overrides = {}) {
  const id = `contract-${++sequence}`;
  return { adapter_id: id, name: `TEST FIXTURE ${id}`, run_id: `run-${id}`, data_kind: 'example',
    truth, truth_note: 'Synthetic test truth, not evidence.', verdict,
    sample_sizes: { clean: 3, triggered: 1, untriggered: null }, cost_usd: null, latency_ms: null,
    sources: [{ label: 'Fixture source', url: `/api/runs/run-${id}/report` }], note: 'Software test only.', ...overrides };
}
function dataset(rows, kind = 'example') {
  return { schema_version: 1, dataset_id: 'contract-fixture', data_kind: kind, title: 'TEST FIXTURE',
    description: 'Synthetic software contract data; not a measurement.', generated_at: null,
    adapters: rows.map(value => ({ ...value, data_kind: kind })) };
}
function invalid(change, pattern) {
  const value = dataset([row()]);
  change(value);
  assert.throws(() => validateDataset(value), pattern);
  assert.throws(() => computeMetrics(value), pattern, 'Metrics must enforce the same rejection');
}

test('shipped snapshot is explicitly example-only and computes honest denominators', () => {
  assert.equal(validateDataset(sample), sample);
  assert.equal(sample.data_kind, 'example');
  assert(sample.adapters.every(value => value.data_kind === 'example' && value.run_id.startsWith('EXAMPLE-')));
  const metrics = computeMetrics(sample);
  assert.equal(metrics.total, 9);
  assert.equal(metrics.decided, 7);
  assert.equal(metrics.incomplete, 2);
  assert.equal(metrics.coverage, 7 / 9);
  assert.deepEqual(metrics.positive, { eligible: 4, decided: 3, flagged: 2, passed: 1, incomplete: 1, rate: 2 / 3, coverage: 3 / 4, allEligibleRate: 2 / 4 });
  assert.deepEqual(metrics.negative, { eligible: 4, decided: 3, flagged: 1, passed: 2, incomplete: 1, rate: 1 / 3, coverage: 3 / 4, allEligibleRate: 1 / 4 });
  assert.equal(metrics.unknown.eligible, 1);
  assert.equal(metrics.unknown.flagged, 1);
  assert.equal(metrics.knownEligible, 8);
  assert.equal(metrics.knownDecided, 6);
  assert.deepEqual(metrics.verdicts, { QUARANTINE: 1, FLAG: 3, PASS: 3, INCOMPLETE: 2 });
  assert.deepEqual(metrics.cost, { count: 0, total: null, mean: null });
  assert.deepEqual(metrics.latency, { count: 0, total: null, mean: null });
});

test('all truth/verdict combinations: FLAG and QUARANTINE count, unknown is separate', () => {
  const rows = ['positive', 'negative', 'unknown'].flatMap(truth => ['QUARANTINE', 'FLAG', 'PASS', 'INCOMPLETE'].map(verdict => row(truth, verdict)));
  const metrics = computeMetrics(dataset(rows));
  for (const truth of ['positive', 'negative', 'unknown']) {
    assert.deepEqual(metrics[truth], { eligible: 4, decided: 3, flagged: 2, passed: 1, incomplete: 1, rate: 2 / 3, coverage: 3 / 4, allEligibleRate: 1 / 2 });
  }
  assert.equal(metrics.total, 12);
  assert.equal(metrics.decided, 9);
  assert.equal(metrics.knownEligible, 8);
  assert.equal(metrics.knownDecided, 6);
});

test('prompt counts never weight rates; changing decisions actually changes computed rates', () => {
  const value = dataset([row('positive', 'FLAG'), row('positive', 'PASS'), row('negative', 'PASS'), row('negative', 'QUARANTINE')]);
  const before = computeMetrics(value);
  value.adapters[0].sample_sizes = { clean: 1000000, triggered: 500000, untriggered: 1000 };
  value.adapters[1].sample_sizes = { clean: 1, triggered: null, untriggered: 0 };
  assert.deepEqual(computeMetrics(value), before);
  assert.equal(before.positive.rate, 1 / 2);
  assert.equal(before.negative.rate, 1 / 2);
  value.adapters[1].verdict = 'FLAG';
  value.adapters[3].verdict = 'PASS';
  assert.equal(computeMetrics(value).positive.rate, 1);
  assert.equal(computeMetrics(value).negative.rate, 0);
});

test('empty, unknown-only, and all-incomplete cohorts never invent a rate', () => {
  for (const value of [dataset([]), dataset([row('unknown', 'FLAG')]), dataset([row('positive', 'INCOMPLETE'), row('negative', 'INCOMPLETE')])]) {
    const metrics = computeMetrics(value);
    assert.equal(metrics.positive.rate, null);
    assert.equal(metrics.negative.rate, null);
    assert.equal(formatRate(metrics.positive.rate), '—');
  }
  assert.equal(computeMetrics(dataset([])).coverage, null);
  const incomplete = computeMetrics(dataset([row('positive', 'INCOMPLETE')]));
  assert.equal(incomplete.coverage, 0);
  assert.equal(incomplete.positive.coverage, 0);
  assert.equal(incomplete.positive.allEligibleRate, 0);
  assert.equal(incomplete.negative.coverage, null);
});

test('resources distinguish unavailable, real zero, partial totals and incomplete costs', () => {
  const absent = computeMetrics(dataset([row()]));
  assert.equal(absent.cost.total, null);
  assert.equal(absent.latency.mean, null);
  const zero = computeMetrics(dataset([row('positive', 'FLAG', { cost_usd: 0, latency_ms: 0 }), row()]));
  assert.deepEqual(zero.cost, { count: 1, total: 0, mean: 0 });
  assert.deepEqual(zero.latency, { count: 1, total: 0, mean: 0 });
  const partial = computeMetrics(dataset([row('positive', 'INCOMPLETE', { cost_usd: 0.125, latency_ms: 2500 }), row('negative', 'PASS', { cost_usd: 0.25, latency_ms: 500 }), row()]));
  assert.deepEqual(partial.cost, { count: 2, total: 0.375, mean: 0.1875 });
  assert.equal(partial.latency.mean, 1500);
  assert.equal(partial.latency.count, 2);
  assert.equal(formatUsd(null), '—');
  assert.equal(formatUsd(0), '$0.00');
  assert.equal(formatUsd(0.000001), '< $0.0001');
  assert.equal(formatLatency(null), '—');
  assert.equal(formatLatency(0), '0 ms');
  assert.equal(formatLatency(0.1), '< 1 ms');
  assert.equal(formatLatency(1500), '1.5 s');
});

test('strict shapes, types, labels, mixed origins, and duplicated observation IDs reject', () => {
  for (const value of [null, [], {}, 'data']) assert.throws(() => validateDataset(value));
  const changes = [
    d => { d.schema_version = 2; }, d => { d.extra = true; }, d => { delete d.description; },
    d => { d.adapters = null; }, d => { d.adapters = {}; }, d => { d.adapters = [null]; },
    d => { d.adapters = Array(5001).fill(d.adapters[0]); }, d => { d.dataset_id = '../bad'; },
    d => { d.title = ''; }, d => { d.description = false; }, d => { d.data_kind = 'real'; },
    d => { d.adapters[0].data_kind = 'measured'; }, d => { d.data_kind = 'measured'; },
    d => { d.adapters[0].truth = 'clean'; }, d => { d.adapters[0].truth = null; },
    d => { d.adapters[0].verdict = 'pass'; }, d => { d.adapters[0].verdict = 'SUCCESS'; },
    d => { d.adapters[0].run_id = 0; }, d => { d.adapters[0].adapter_id = ''; },
    d => { d.adapters[0].truth_note = ''; }, d => { d.adapters[0].note = null; },
    d => { d.adapters[0].sources = {}; }, d => { d.adapters[0].sources = [null]; },
    d => { d.adapters[0].sources[0].label = ''; }, d => { d.adapters[0].sources[0].extra = 1; },
    d => { delete d.adapters[0].cost_usd; }, d => { delete d.adapters[0].sample_sizes.clean; },
    d => { d.adapters[0].sample_sizes.extra = 1; }, d => { d.adapters[0].sample_sizes = []; },
    d => { d.adapters.push(clone(d.adapters[0])); },
    d => { d.adapters.push({ ...clone(d.adapters[0]), adapter_id: 'different' }); }
  ];
  changes.forEach(change => invalid(change));
});

test('numeric fields do not coerce strings, booleans, missing values, or non-finite numbers', () => {
  for (const bad of ['0', '', false, undefined, NaN, Infinity, -Infinity, -1, Number.MAX_SAFE_INTEGER + 1]) {
    invalid(d => { d.adapters[0].cost_usd = bad; });
    invalid(d => { d.adapters[0].latency_ms = bad; });
    invalid(d => { d.adapters[0].sample_sizes.clean = bad; });
  }
  invalid(d => { d.adapters[0].sample_sizes.triggered = 0.5; });
  for (const stamp of ['', 0, '2026-11-07', '2026-02-30T00:00:00Z', '2026-11-07T25:00:00Z', 'invalid']) invalid(d => { d.generated_at = stamp; });
  for (const stamp of [null, '2026-11-07T12:13:14Z', '2026-11-07T12:13:14.123Z']) {
    const value = dataset([]); value.generated_at = stamp; assert.doesNotThrow(() => validateDataset(value));
  }
});

test('measured decided rows require run/source/sample evidence; incomplete remains explicit', () => {
  const measured = dataset([row('positive', 'FLAG')], 'measured');
  assert.doesNotThrow(() => validateDataset(measured));
  for (const change of [r => { r.run_id = null; }, r => { r.sources = []; }, r => { r.sample_sizes = { clean: 0, triggered: 0, untriggered: null }; }]) {
    const value = clone(measured); change(value.adapters[0]); assert.throws(() => validateDataset(value));
  }
  const incomplete = dataset([row('unknown', 'INCOMPLETE', { run_id: null, sources: [], sample_sizes: { clean: 0, triggered: null, untriggered: null } })], 'measured');
  assert.doesNotThrow(() => validateDataset(incomplete));
  assert.equal(computeMetrics(incomplete).decided, 0);
});

test('source URLs allow only safe absolute HTTP(S) or bounded local API paths', () => {
  for (const url of ['https://example.com/report?id=1#evidence', 'http://example.com/', 'HTTPS://example.com/a', '/api/runs/run-1/report', '/api/runs/run_2/report.json?download=1#details']) {
    assert(safeSourceUrl(url), url);
    const value = dataset([row()]); value.adapters[0].sources[0].url = url; assert.doesNotThrow(() => validateDataset(value));
  }
  for (const url of [null, '', 'javascript:alert(1)', 'data:text/html,test', 'mailto:test@example.com', '//evil.example', '/static/report', '/api', '/api/../secrets', '/api/runs/../../static/a', '/api/%2e%2e/x', '/api/runs/%2f..%2f..', '/api/runs\\evil', 'https://user:pass@example.com', 'https:example.com', ' https://example.com', 'https://example.com/\nfoo', 'https://example.com/a b', 'https://']) {
    assert.equal(safeSourceUrl(url), null, String(url));
    invalid(d => { d.adapters[0].sources[0].url = url; });
  }
});

// Minimal DOM fixture to exercise the actual rendering/error paths, not layout.
class Element {
  constructor(tag = 'div') {
    this.tagName = tag; this.children = []; this._text = ''; this.className = '';
    this.attributes = {}; this.style = {}; this.hidden = false; this.disabled = false;
    this.classList = {
      add: token => this.classList.toggle(token, true),
      toggle: (token, enabled) => {
        const tokens = new Set(this.className.split(/\s+/).filter(Boolean));
        if (enabled) tokens.add(token); else tokens.delete(token);
        this.className = [...tokens].join(' ');
      }
    };
  }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(child => child.textContent).join(''); }
  set innerHTML(_) { throw new Error('HTML injection is forbidden'); }
  append(...nodes) {
    for (const node of nodes) {
      if (node.tagName === '#fragment') this.append(...node.children);
      else { node.parentNode = this; this.children.push(node); }
    }
  }
  replaceChildren(...nodes) { this._text = ''; this.children = []; this.append(...nodes); }
  setAttribute(name, value) { this.attributes[name] = String(value); }
  addEventListener(name, fn) { this[name] = fn; }
}
function setup(fetchData) {
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]);
  assert.equal(new Set(ids).size, ids.length, 'HTML IDs must be unique');
  const elements = new Map(ids.map(id => [id, new Element()]));
  elements.get('results').hidden = true;
  for (const id of ['tpr-bar', 'fpr-bar']) elements.get(id).parentNode = new Element();
  const document = { getElementById(id) { assert(elements.has(id), `Unknown DOM ID ${id}`); return elements.get(id); },
    createElement(tag) { return new Element(tag); }, createDocumentFragment() { return new Element('#fragment'); } };
  const requests = [];
  const page = createPage(document, (...args) => { requests.push(args); return fetchData(...args); });
  return { page, elements, requests, get: id => elements.get(id) };
}
const ok = value => ({ ok: true, status: 200, json: async () => clone(value) });

test('HTML starts without results, uses local assets, accessible table and native methodology', () => {
  assert.match(html, /id="results" hidden/);
  assert.match(html, /LOADING \/ NO RESULTS YET/);
  assert.match(html, /<noscript>/);
  assert.match(html, /href="\/"/);
  assert.match(html, /src="\/static\/benchmark\.js"/);
  assert.match(html, /href="\/static\/benchmark\.css"/);
  assert.match(html, /<caption/);
  assert.equal((html.match(/scope="col"/g) || []).length, 8);
  assert.match(html, /tabindex="0" role="region"/);
  assert.equal((html.match(/<details>/g) || []).length, 2);
  for (const color of ['#111215', '#181a1e', '#303238', '#eeeef0', '#9b9da5', '#c1f58a']) assert(css.includes(color));
});

test('actual rendering labels every example, computes bars, and fetches only the static JSON', async () => {
  const view = setup(async () => ok(sample));
  await view.page.load();
  assert.equal(view.get('results').hidden, false);
  assert.equal(view.get('state-title').textContent, 'EXAMPLE DATA / NOT MEASURED');
  assert.equal(view.get('tpr-value').textContent, '66.7%');
  assert.equal(view.get('fpr-value').textContent, '33.3%');
  assert.equal(view.get('tpr-all').textContent, '2 / 4 · 50.0%');
  assert.equal(view.get('fpr-all').textContent, '1 / 4 · 25.0%');
  assert.equal(view.get('tpr-coverage').textContent, '3 / 4 · 75.0%');
  assert(Math.abs(parseFloat(view.get('tpr-bar').style.width) - 200 / 3) < 1e-10);
  assert.equal(view.get('cost-value').textContent, '—');
  assert.match(view.get('cost-detail').textContent, /unavailable, not zero/);
  assert.equal(view.get('reload').disabled, false);
  assert.equal(view.get('data-state').attributes['aria-busy'], 'false');
  const rows = view.get('adapter-rows').children;
  assert.equal(rows.length, 9);
  for (const tr of rows) {
    assert.equal(tr.children[0].scope, 'row');
    assert.match(tr.children[0].textContent, /EXAMPLE \/ NOT MEASURED/);
    const link = tr.children.at(-1).children[0].children[0].children[0];
    assert.equal(link.rel, 'noopener noreferrer');
    assert.equal(link.target, '_blank');
    assert(safeSourceUrl(link.href));
  }
  assert.equal(view.requests.length, 1);
  assert.equal(view.requests[0][0], '/static/benchmark-data.json');
  assert.equal(view.requests[0][1].cache, 'no-store');
});

test('measured rendering stays separate, preserves real zero resources and uses text nodes', async () => {
  const value = dataset([row('positive', 'PASS', { name: '<img src=x onerror=alert(1)>', cost_usd: 0, latency_ms: 0 })], 'measured');
  const view = setup(async () => ok(value));
  await view.page.load();
  assert.equal(view.get('results').hidden, false);
  assert.equal(view.get('state-title').textContent, 'MEASURED DATA / REPORTED SNAPSHOT');
  assert.equal(view.get('tpr-value').textContent, '0.0%');
  assert.equal(view.get('fpr-value').textContent, '—');
  assert.equal(view.get('cost-value').textContent, '$0.00');
  assert.equal(view.get('latency-value').textContent, '0 ms');
  assert.match(view.get('adapter-rows').textContent, /<img src=x onerror=alert\(1\)>/);
  assert(!view.get('adapter-rows').textContent.includes('EXAMPLE / NOT MEASURED'));
});

test('valid all-incomplete data shows unavailable rates, pending coverage and missing provenance', async () => {
  const value = dataset([row('unknown', 'INCOMPLETE', { run_id: null, sources: [] })], 'measured');
  const view = setup(async () => ok(value));
  await view.page.load();
  assert.equal(view.get('results').hidden, false);
  assert.equal(view.get('tpr-value').textContent, '—');
  assert.match(view.get('tpr-count').textContent, /rate unavailable/);
  assert.equal(view.get('coverage-value').textContent, '0.0%');
  assert.equal(view.get('excluded-value').textContent, '1 / 1');
  assert.match(view.get('excluded-detail').textContent, /may overlap/);
  assert.match(view.get('adapter-rows').textContent, /No run ID/);
  assert.match(view.get('adapter-rows').textContent, /No source attached/);
});

test('empty, malformed, HTTP, JSON and network failure states clear prior successful rows and rates', async () => {
  const malformed = clone(sample); malformed.adapters[1].sample_sizes.clean = '40';
  const mixed = clone(sample); mixed.adapters[0].data_kind = 'measured';
  const failures = [
    { response: ok(dataset([])), kind: 'empty' },
    { response: ok(malformed), kind: 'error' },
    { response: ok(mixed), kind: 'error' },
    { response: { ok: false, status: 404 }, kind: 'error' },
    { response: { ok: true, status: 200, json: async () => { throw new SyntaxError('test fixture'); } }, kind: 'error' },
    { error: new Error('synthetic network failure'), kind: 'error' }
  ];
  for (const failure of failures) {
    let reload = false;
    const view = setup(async () => {
      if (!reload) return ok(sample);
      if (failure.error) throw failure.error;
      return failure.response;
    });
    await view.page.load();
    assert.equal(view.get('results').hidden, false);
    reload = true;
    await view.page.load();
    assert.equal(view.get('results').hidden, true);
    assert.equal(view.get('adapter-rows').children.length, 0);
    assert.equal(view.get('tpr-value').textContent, '—');
    assert.equal(view.get('fpr-value').textContent, '—');
    assert.equal(view.get('cost-value').textContent, '—');
    assert.equal(view.get('tpr-bar').style.width, '0%');
    assert.equal(view.get('data-state').className, `data-state ${failure.kind}`);
    assert.match(view.get('state-title').textContent, /NO RESULTS/);
    assert.equal(view.get('reload').disabled, false);
  }
});

test('pending reload removes old results immediately; stale fetch responses cannot overwrite newer state', async () => {
  const pending = [];
  const view = setup(() => new Promise(resolve => pending.push(resolve)));
  const first = view.page.load();
  assert.equal(view.get('results').hidden, true);
  assert.equal(view.get('reload').disabled, true);
  const second = view.page.load();
  pending[1](ok(dataset([])));
  await second;
  assert.equal(view.get('data-state').className, 'data-state empty');
  pending[0](ok(sample));
  await first;
  assert.equal(view.get('data-state').className, 'data-state empty');
  assert.equal(view.get('results').hidden, true);
});
