# TripWir3 static benchmark page

Open `/static/benchmark.html` through the existing app. It links back to `/`, loads only `/static/benchmark.css`, `/static/benchmark.js`, and `/static/benchmark-data.json`, and needs no dependencies or build. Reload fetches the static JSON again; it never starts audits, invokes models, or reads backend run directories. The app already serves `/static`; no route change is needed.

The shipped cohort is **EXAMPLE DATA / NOT MEASURED**. All nine adapters, run IDs, truth labels, decisions, and sample sizes are fictional. Links are explicitly labeled example.com placeholders. There are no measured benchmark results in this delivery. Cost, latency, and snapshot timestamp are `null`.

## Counting policy

One unique `adapter_id` is one observation, represented by one selected run. Duplicate adapter IDs and duplicate non-null run IDs reject the snapshot. Select a run using a declared policy before exporting; this page does not pool repeated runs or weight adapters by prompt counts.

| Display | Calculation |
| --- | --- |
| Flagged | `QUARANTINE` or `FLAG` |
| Decided | `QUARANTINE`, `FLAG`, or `PASS` |
| TPR | Flagged positive adapters / decided positive adapters |
| FPR | Flagged negative adapters / decided negative adapters |
| Class coverage | Decided adapters in that truth class / all adapters in that class |
| Flagged / all eligible | Flagged adapters in that truth class / all adapters in that class, including incomplete |
| Overall coverage | All decided adapters / all adapter rows, including unknown truth |
| Known-truth coverage | Decided positive + negative adapters / all positive + negative adapters |
| Reported cost | Sum of non-null `cost_usd`, including incomplete runs; report available count / all rows |
| Mean audit latency | Unweighted arithmetic mean of non-null per-adapter `latency_ms`; report available count / all rows |

`INCOMPLETE` is reported separately and excluded from decided denominators. It is retained in eligible counts and coverage. Unknown-truth rows stay in the ledger and overall coverage, but are excluded from both TPR and FPR. Incomplete and unknown counts may overlap. All-eligible flagged fractions are not additional TPR/FPR estimates: their denominators intentionally retain incomplete runs.

Zero denominators produce `null` rates and an em dash with an unavailable message, never a zero rate. Real zero costs and durations render as zero. If every resource value is missing, its aggregate is `null`, not a zero sum. A partially reported cost is labeled a partial sum. Positive cost below $0.0001 renders as `< $0.0001`; positive latency below 1 ms renders as `< 1 ms`.

The example computes TPR `2/3`, FPR `1/3`, class coverage `3/4` each, all-eligible flagged fractions `2/4` and `1/4`, and overall coverage `7/9`. The unknown-truth FLAG contributes to overall decided coverage, neither rate. These are synthetic fractions, not measured performance. The page always computes them from JSON.

## Strict schema v1

Every listed field is required; unknown keys are rejected to catch typos and incompatible exports. Text must be nonempty unless explicitly allowed below. All numeric values must be finite, nonnegative, and at most `Number.MAX_SAFE_INTEGER`; sample sizes must be safe integers. Strings containing HTML are rendered as literal text, never inserted as markup.

Top-level object:

| Field | Type / constraint |
| --- | --- |
| `schema_version` | Number `1` |
| `dataset_id` | Unique snapshot identifier; 1–128 characters, starting with a letter or digit, then letters, digits, `.`, `_`, `:`, `-` |
| `data_kind` | Exactly `example` or `measured` |
| `title` | Nonempty string, at most 160 characters |
| `description` | Nonempty string, at most 1,000 characters; include cohort selection and run selection policy |
| `generated_at` | `null` or valid UTC ISO timestamp `YYYY-MM-DDTHH:mm:ssZ` or `YYYY-MM-DDTHH:mm:ss.sssZ` |
| `adapters` | Array of 0–5,000 adapter objects; empty is a no-results state |

Adapter object:

| Field | Type / constraint |
| --- | --- |
| `adapter_id` | Unique identifier, same character rules as `dataset_id`; identify adapter content/revision, not just display name |
| `name` | Nonempty display name, at most 160 characters |
| `run_id` | Unique identifier under the same rules, or `null` if unavailable |
| `data_kind` | Must exactly match the top-level kind; mixed examples/measured rows reject the entire snapshot |
| `truth` | Exactly `positive`, `negative`, or `unknown` |
| `truth_note` | Nonempty ground-truth basis, at most 1,000 characters; describe uncertainty explicitly |
| `verdict` | Exactly `QUARANTINE`, `FLAG`, `PASS`, or `INCOMPLETE` |
| `sample_sizes` | Object with exactly `clean`, `triggered`, `untriggered`, each a nonnegative safe integer or `null` |
| `cost_usd` | Actual reported per-adapter audit cost in USD, or `null` if not known; never substitute an estimate for an actual amount without a future schema change |
| `latency_ms` | Actual total wall-clock audit elapsed milliseconds for that adapter, or `null`; not token latency or per-prompt latency |
| `sources` | Array of 0–16 source objects, each exactly `{ "label": "…", "url": "…" }`; label nonempty, at most 160 characters |
| `note` | String up to 1,000 characters; may be empty; disclose failures, limits, or selection details |

**A decided measured row additionally requires a non-null run ID, at least one source, and at least one positive executed sample count.** Incomplete measured rows may have null IDs, no sources, and zero/missing sample counts. Missing sample sizes use `null`; a measured zero means no samples of that type were executed. Counts refer to executed samples, not planned probes. Truth is declared by the supplied data; the page cannot verify it.

Source URLs must be absolute `http://` or `https://` without embedded credentials, or root-relative `/api/…` paths. Local paths use literal letter/digit/underscore/tilde/hyphen-led segments (subsequent dots allowed), without traversal or percent-encoded path segments; queries and fragments are allowed. Protocol-relative, non-API local, malformed, whitespace/control/backslash-containing, and executable URL schemes reject the entire dataset. Links open with `noopener noreferrer`; URLs are not automatically fetched. Safe formatting is not verification that an endpoint exists or contains valid evidence.

## Exporting measured results

1. Collect actual per-adapter results and independent ground-truth bases. Do not relabel the fictional example as measured. This task does not execute audits or generate results.
2. Export a wholly separate cohort into the v1 shape. Choose one run for each adapter, state how it was chosen, and include every eligible incomplete adapter. Derive adapter identity from actual content/revision; do not assign different IDs to the same adapter to increase sample counts.
3. Set both top-level and every row's `data_kind` to `measured`. Supply actual run IDs and sources (for example an existing `/api/runs/<run_id>/report`). Missing costs/durations remain `null`. A run that did not finish receives `INCOMPLETE`, never a guessed PASS.
4. Run the contract checks, inspect the page in the existing app, and review linked evidence before publishing the snapshot. Descriptive rates are not a safety certification, confidence interval, or independent scientific validation.

Backend `benchmark.json` files are **not** this page's schema. A future explicit exporter must map their audit records, identities, executed sample counts, completion states, independently established truth, and provenance into this schema. No automatic backend ingestion or exporter is included. Future extensions (multiple cohorts, confidence intervals, repeated-run policy, model/version metadata, truth-source typing) should use a new schema version and update the validator and tests together.

## Validation and limitations

Run from the repository root:

```sh
node --check model_customs/static/benchmark.js
node --check tests/frontend-benchmark-contract.cjs
node tests/frontend-benchmark-contract.cjs
```

The dependency-free Node contract tests exercise the actual metric/validation functions and a small DOM fixture. They cover the shipped example, every verdict/truth combination, adapter versus prompt denominators, incomplete/unknown exclusions, empty/all-incomplete cohorts, missing versus zero resources, measured evidence minimums, malformed shapes, mixed origin, duplicate IDs, URL restrictions, text-safe rendering, HTTP/JSON/network failures, failed reload cleanup, and stale response handling. They do not call models or the network.

Fetch, JSON, and schema errors reject the entire snapshot and clear previous visible rows and metrics; there is no fallback to examples, partial acceptance, or silent coercion. Empty snapshots also show no results. The initial HTML and no-JavaScript state claim no results. Native details explain the methodology and schema; the table uses a caption, scoped column/row headers, keyboard-scrollable overflow, and text labels alongside colors. Browser/layout QA remains with the parent. This delivery changes only the six owned files and performs no commits or pushes.
