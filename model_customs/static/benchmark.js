/* Static snapshot reader. Never starts an audit or calls a model. */
(function () {
  'use strict';

  const DATA_URL = '/static/benchmark-data.json';
  const KINDS = ['example', 'measured'];
  const TRUTHS = ['positive', 'negative', 'unknown'];
  const VERDICTS = ['QUARANTINE', 'FLAG', 'PASS', 'INCOMPLETE'];
  const SAMPLE_KEYS = ['clean', 'triggered', 'untriggered'];
  class SnapshotError extends Error {}

  function check(condition, message) {
    if (!condition) throw new SnapshotError(message);
  }

  function shape(value, keys, field) {
    check(value !== null && typeof value === 'object' && !Array.isArray(value), `${field} must be an object.`);
    check(Object.keys(value).length === keys.length && keys.every(key => Object.prototype.hasOwnProperty.call(value, key)), `${field} has missing or unsupported fields (schema v1).`);
  }

  function text(value, field, max = 1000, allowEmpty = false) {
    check(typeof value === 'string' && value.length <= max && (allowEmpty || value.trim().length > 0), `${field} must be ${allowEmpty ? 'text' : 'nonempty text'} (up to ${max} characters).`);
  }

  function identifier(value, field) {
    check(typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(value), `${field} must be a 1–128 character identifier (letters, digits, . _ : -).`);
  }

  function nullableNumber(value, field, integer = false) {
    check(value === null || (typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= Number.MAX_SAFE_INTEGER && (!integer || Number.isSafeInteger(value))), `${field} must be null or a nonnegative ${integer ? 'safe integer' : 'finite number'}.`);
  }

  function safeSourceUrl(value) {
    if (typeof value !== 'string' || value.length > 2048 || /[\s\u0000-\u001f\u007f\\]/.test(value)) return null;
    try {
      if (/^https?:\/\//i.test(value)) {
        const url = new URL(value);
        return url.hostname && !url.username && !url.password && ['http:', 'https:'].includes(url.protocol) ? url.href : null;
      }
      if (value.startsWith('/api/')) {
        const url = new URL(value, 'https://tripwir3.invalid');
        // Restrict local paths to literal API segments; no encoded or normalized traversal.
        const rawPath = value.split(/[?#]/, 1)[0];
        if (url.origin === 'https://tripwir3.invalid' && url.pathname === rawPath && /^\/api\/(?:[A-Za-z0-9_~-][A-Za-z0-9._~-]*\/?)+$/.test(rawPath)) {
          return url.pathname + url.search + url.hash;
        }
      }
    } catch (_) { /* Invalid URLs are rejected, never silently hidden. */ }
    return null;
  }

  function validateDataset(data) {
    shape(data, ['schema_version', 'dataset_id', 'data_kind', 'title', 'description', 'generated_at', 'adapters'], 'snapshot');
    check(data.schema_version === 1, 'Unsupported schema_version; expected 1.');
    identifier(data.dataset_id, 'dataset_id');
    check(KINDS.includes(data.data_kind), 'data_kind must be example or measured.');
    text(data.title, 'title', 160);
    text(data.description, 'description', 1000);
    const stamp = data.generated_at;
    check(stamp === null || (typeof stamp === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(stamp) && Number.isFinite(Date.parse(stamp)) && new Date(stamp).toISOString() === (stamp.includes('.') ? stamp : stamp.replace('Z', '.000Z'))), 'generated_at must be null or a valid UTC ISO timestamp.');
    check(Array.isArray(data.adapters) && data.adapters.length <= 5000, 'adapters must be an array with at most 5000 rows.');
    const adapterIds = new Set();
    const runIds = new Set();
    data.adapters.forEach((row, index) => {
      const at = `adapters[${index}]`;
      shape(row, ['adapter_id', 'name', 'run_id', 'data_kind', 'truth', 'truth_note', 'verdict', 'sample_sizes', 'cost_usd', 'latency_ms', 'sources', 'note'], at);
      identifier(row.adapter_id, `${at}.adapter_id`);
      check(!adapterIds.has(row.adapter_id), `${at}: duplicate adapter_id; select one run per adapter.`);
      adapterIds.add(row.adapter_id);
      text(row.name, `${at}.name`, 160);
      check(row.run_id === null || typeof row.run_id === 'string', `${at}.run_id must be an identifier or null.`);
      if (row.run_id !== null) {
        identifier(row.run_id, `${at}.run_id`);
        check(!runIds.has(row.run_id), `${at}: duplicate run_id.`);
        runIds.add(row.run_id);
      }
      check(row.data_kind === data.data_kind, `${at}: mixed or invalid data_kind; examples and measured results require separate snapshots.`);
      check(TRUTHS.includes(row.truth), `${at}.truth must be positive, negative, or unknown.`);
      check(VERDICTS.includes(row.verdict), `${at}.verdict must be QUARANTINE, FLAG, PASS, or INCOMPLETE.`);
      text(row.truth_note, `${at}.truth_note`, 1000);
      text(row.note, `${at}.note`, 1000, true);
      shape(row.sample_sizes, SAMPLE_KEYS, `${at}.sample_sizes`);
      SAMPLE_KEYS.forEach(key => nullableNumber(row.sample_sizes[key], `${at}.sample_sizes.${key}`, true));
      nullableNumber(row.cost_usd, `${at}.cost_usd`);
      nullableNumber(row.latency_ms, `${at}.latency_ms`);
      check(Array.isArray(row.sources) && row.sources.length <= 16, `${at}.sources must be an array with at most 16 links.`);
      row.sources.forEach((source, sourceIndex) => {
        const field = `${at}.sources[${sourceIndex}]`;
        shape(source, ['label', 'url'], field);
        text(source.label, `${field}.label`, 160);
        check(safeSourceUrl(source.url) !== null, `${field}.url must be an absolute HTTP(S) URL without credentials, or a local /api/ path.`);
      });
      if (data.data_kind === 'measured' && row.verdict !== 'INCOMPLETE') {
        check(row.run_id !== null && row.sources.length > 0, `${at}: a decided measured row requires a run ID and source evidence.`);
        check(SAMPLE_KEYS.some(key => row.sample_sizes[key] !== null && row.sample_sizes[key] > 0), `${at}: a decided measured row requires at least one executed sample.`);
      }
    });
    return data;
  }

  const ratio = (numerator, denominator) => denominator > 0 ? numerator / denominator : null;
  const isFlagged = row => row.verdict === 'FLAG' || row.verdict === 'QUARANTINE';
  const isDecided = row => row.verdict !== 'INCOMPLETE';

  function computeMetrics(input) {
    const data = validateDataset(input);
    const rows = data.adapters;
    function group(truth) {
      const eligible = rows.filter(row => row.truth === truth);
      const decided = eligible.filter(isDecided);
      const flagged = decided.filter(isFlagged).length;
      return { eligible: eligible.length, decided: decided.length, flagged,
        passed: decided.length - flagged, incomplete: eligible.length - decided.length,
        rate: ratio(flagged, decided.length), coverage: ratio(decided.length, eligible.length),
        allEligibleRate: ratio(flagged, eligible.length) };
    }
    function reported(key) {
      const values = rows.map(row => row[key]).filter(value => value !== null);
      const total = values.length ? values.reduce((sum, value) => sum + value, 0) : null;
      return { count: values.length, total, mean: total === null ? null : total / values.length };
    }
    const positive = group('positive');
    const negative = group('negative');
    const unknown = group('unknown');
    const decided = rows.filter(isDecided).length;
    return { total: rows.length, decided, incomplete: rows.length - decided,
      coverage: ratio(decided, rows.length), positive, negative, unknown,
      knownEligible: positive.eligible + negative.eligible,
      knownDecided: positive.decided + negative.decided,
      cost: reported('cost_usd'), latency: reported('latency_ms'),
      verdicts: Object.fromEntries(VERDICTS.map(verdict => [verdict, rows.filter(row => row.verdict === verdict).length])) };
  }

  const formatRate = value => value === null ? '—' : `${(value * 100).toFixed(1)}%`;
  const fraction = (n, d) => `${n} / ${d} / ${formatRate(ratio(n, d))}`;
  const formatUsd = value => value === null ? '—' : (value > 0 && value < 0.0001 ? '< $0.0001' : `$${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 4 })}`);
  const formatLatency = value => value === null ? '—' : (value === 0 ? '0 ms' : value < 1 ? '< 1 ms' : value < 1000 ? `${value.toFixed(0)} ms` : `${(value / 1000).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 })} s`);

  function createPage(document, fetchData) {
    const el = id => document.getElementById(id);
    const set = (id, value) => { el(id).textContent = value; };
    const make = (tag, className, value) => {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (value !== undefined) node.textContent = value;
      return node;
    };
    let requestId = 0;

    function state(kind, title, description, busy = false) {
      el('data-state').className = `data-state ${kind}`;
      el('data-state').setAttribute('aria-busy', String(busy));
      set('state-title', title);
      set('state-description', description);
      el('reload').disabled = busy;
    }

    function clearResults() {
      el('results').hidden = true;
      el('adapter-rows').replaceChildren();
      ['tpr-value', 'fpr-value', 'coverage-value', 'excluded-value', 'cost-value', 'latency-value'].forEach(id => set(id, '—'));
      ['tpr', 'fpr'].forEach(id => {
        el(`${id}-bar`).style.width = '0%';
        el(`${id}-bar`).parentNode.classList.add('unavailable');
      });
    }

    function renderRate(prefix, metrics, truth) {
      set(`${prefix}-value`, formatRate(metrics.rate));
      set(`${prefix}-count`, metrics.decided ? `${metrics.flagged} flagged / ${metrics.decided} decided ${truth} adapters` : `No decided ${truth} adapters / rate unavailable`);
      set(`${prefix}-coverage`, fraction(metrics.decided, metrics.eligible));
      set(`${prefix}-all`, fraction(metrics.flagged, metrics.eligible));
      set(`${prefix}-incomplete`, `${metrics.incomplete} / ${metrics.eligible}`);
      const bar = el(`${prefix}-bar`);
      bar.style.width = metrics.rate === null ? '0%' : `${metrics.rate * 100}%`;
      bar.parentNode.classList.toggle('unavailable', metrics.rate === null);
    }

    function renderRows(data) {
      const fragment = document.createDocumentFragment();
      data.adapters.forEach(row => {
        const tr = make('tr');
        const name = make('th');
        name.scope = 'row';
        name.append(make('span', 'adapter-name', row.name), make('code', 'adapter-id', row.adapter_id));
        if (data.data_kind === 'example') name.append(make('span', 'row-example', 'EXAMPLE / NOT MEASURED'));
        if (row.note) name.append(make('span', 'row-note', row.note));
        const truth = make('td');
        truth.append(make('span', `badge truth-${row.truth}`, row.truth.toUpperCase()), make('span', 'truth-note', row.truth_note));
        const verdict = make('td');
        verdict.append(make('span', `badge verdict-${row.verdict.toLowerCase()}`, row.verdict));
        const samples = make('td', 'numeric', SAMPLE_KEYS.map(key => row.sample_sizes[key] === null ? '—' : row.sample_sizes[key].toLocaleString('en-US')).join(' / '));
        samples.setAttribute('aria-label', SAMPLE_KEYS.map(key => `${key}: ${row.sample_sizes[key] === null ? 'not reported' : row.sample_sizes[key]}`).join('; '));
        const cost = make('td', 'numeric', formatUsd(row.cost_usd));
        if (row.cost_usd === null) cost.setAttribute('aria-label', 'Cost not reported');
        const latency = make('td', 'numeric', formatLatency(row.latency_ms));
        if (row.latency_ms === null) latency.setAttribute('aria-label', 'Audit latency not reported');
        const run = make('td');
        run.append(make('code', 'run-id', row.run_id === null ? '—' : row.run_id));
        const sources = make('td');
        if (row.sources.length) {
          const list = make('ul', 'source-list');
          row.sources.forEach(source => {
            const li = make('li');
            const link = make('a', '', source.label);
            link.href = safeSourceUrl(source.url);
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.setAttribute('aria-label', `${source.label} for ${row.name} (opens in a new tab)`);
            li.append(link);
            list.append(li);
          });
          sources.append(list);
        } else sources.append(make('span', 'not-reported', '—'));
        tr.append(name, truth, verdict, samples, cost, latency, run, sources);
        fragment.append(tr);
      });
      el('adapter-rows').replaceChildren(fragment);
    }

    function render(data, metrics) {
      const example = data.data_kind === 'example';
      state(example ? 'example' : 'measured', example ? 'EXAMPLE DATA / NOT MEASURED' : 'MEASURED DATA / REPORTED SNAPSHOT', example
        ? 'Synthetic example snapshot.'
        : 'Recorded audit snapshot.');
      set('dataset-id', `COHORT / ${data.dataset_id}`);
      set('cohort-title', data.title);
      set('cohort-description', '');
      set('snapshot-kind', example ? 'EXAMPLE / NOT MEASURED' : 'MEASURED / REPORTED');
      el('snapshot-kind').className = `tag${example ? ' example' : ''}`;
      set('snapshot-date', data.generated_at === null ? '—' : `Snapshot: ${data.generated_at}`);
      set('rate-kind', example ? 'EXAMPLE FIGURES / NOT MEASURED' : 'REPORTED ADAPTER OUTCOMES');
      renderRate('tpr', metrics.positive, 'positive');
      renderRate('fpr', metrics.negative, 'negative');
      set('coverage-value', formatRate(metrics.coverage));
      set('coverage-detail', `${metrics.decided} / ${metrics.total} decided / known truth ${fraction(metrics.knownDecided, metrics.knownEligible)}`);
      set('excluded-value', `${metrics.incomplete} / ${metrics.total}`);
      set('excluded-detail', `${metrics.unknown.eligible} unknown truth`);
      set('cost-value', formatUsd(metrics.cost.total));
      set('cost-detail', metrics.cost.count ? `${metrics.cost.count} / ${metrics.total} reported / ${metrics.cost.count === metrics.total ? 'all adapters reported' : 'partial sum; missing excluded'}` : `0 / ${metrics.total} reported`);
      set('latency-value', formatLatency(metrics.latency.mean));
      set('latency-detail', metrics.latency.count ? `${metrics.latency.count} / ${metrics.total} reported / unweighted mean` : `0 / ${metrics.total} reported`);
      set('row-count', `${metrics.total} ADAPTERS / ${metrics.decided} DECIDED`);
      set('ledger-caption', `${example ? 'EXAMPLE DATA / NOT MEASURED. ' : 'Reported measured data. '}${metrics.verdicts.QUARANTINE} QUARANTINE / ${metrics.verdicts.FLAG} FLAG / ${metrics.verdicts.PASS} PASS / ${metrics.verdicts.INCOMPLETE} INCOMPLETE. One row per adapter.`);
      renderRows(data);
      el('results').hidden = false;
    }

    async function load() {
      const current = ++requestId;
      clearResults();
      state('loading', 'LOADING / NO RESULTS YET', 'Loading the static snapshot. No benchmark results are available yet.', true);
      try {
        const response = await fetchData(DATA_URL, { cache: 'no-store', headers: { Accept: 'application/json' }, credentials: 'same-origin' });
        if (current !== requestId) return;
        if (!response.ok) throw new SnapshotError(`Snapshot request failed (HTTP ${response.status}). No results are available.`);
        let input;
        try { input = await response.json(); }
        catch (_) { throw new SnapshotError('The snapshot is not valid JSON. No results are available.'); }
        if (current !== requestId) return;
        const data = validateDataset(input);
        const metrics = computeMetrics(data);
        if (metrics.total === 0) {
          state('empty', 'EMPTY SNAPSHOT / NO RESULTS', `${data.data_kind === 'example' ? 'EXAMPLE DATA / NOT MEASURED. ' : 'Measured snapshot supplied. '}No adapter rows were supplied; rates, coverage, and resource totals are unavailable.`);
          return;
        }
        render(data, metrics);
      } catch (error) {
        if (current !== requestId) return;
        clearResults();
        state('error', 'DATA UNAVAILABLE / NO RESULTS', error instanceof SnapshotError ? error.message : 'Unable to fetch the static snapshot. Check the connection and reload. No results are available.');
      }
    }

    el('reload').addEventListener('click', load);
    return { load };
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = { validateDataset, computeMetrics, safeSourceUrl, formatRate, formatUsd, formatLatency, createPage };
  } else if (typeof document !== 'undefined') {
    const page = createPage(document, (...args) => globalThis.fetch(...args));
    void page.load();
  }
})();
