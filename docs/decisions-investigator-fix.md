## 2026-11-08 — Offline Investigator schema-echo mitigation, live efficacy unverified

- Scope: explicit Investigator-fix assignment on `fix/investigator-schema-echo`
  from `453f5ea`; main checkout/evidence read-only. Builder v4 alone integrates
  and executes the separately relayed ONE hero allowance; Astra v5 reviews.
- Recorded `3f078d75` failure is a schema definition rather than a populated
  result. All five required fields absent; duplicate nested keys also present.
  HTTP200/exactLightningID/normalstop/614prompt+562completion/native32000 and
  estimated2649 exclude a demonstrated truncation/overflow/unloaded-model
  explanation. Old role validation was correct. Original wire body is missing;
  v4's matching1802-character request is reconstructed, not historical wire.
- Adopt an Investigator-only populated example using actual identity refs,
  closed field/enum instructions, and explicit instance-vs-schema wording.
  Keep existing manually authored no-thinking template, stop sequence, raw
  completions route, budgets and role/event-reference gates. Prompt conditioning
  is plausible, not an experimentally proven cause or live-tested remedy.
- Strict decoder explicitly diagnoses `response_schema_echo`, rejects ambiguous
  duplicate-key results and malformed/incomplete output, and preserves literal
  reasoning-tag text inside JSON strings. Failure is visible INCOMPLETE and
  propagates; NO silent rule fallback, result repair, substitution or automatic
  specialist retry. Save serialized request body + hash before dispatch so the
  next capture has request evidence, with no auth headers.
- Offline validation:37new regressions; full724passed/1historical-trace-skip,
  zero socket attempts/model calls. Exact raw-response fixtureSHA256
  `38f47df05f2db9521e04f4e1a70d759beec5ca2cfd59d9c2c0d1b6b8c1e7dd61`;
  all five original retry files unchanged. Details/receipts and the single-run
  command are in `docs/INVESTIGATOR_FIX.md`.
- Software tests do not establish Lightning prompt efficacy or hero success.
  After accepted integration and native32000 Lightning reload, builder uses
  one fresh poisoned/super/lightning35_mlx4bit/standard audit under the relayed
  07:32 authority, then preserves/reviews its result and stops on failure.
  No extra smoke/benchmark/API duplicate, push, model load or inference by this
  fix engineer; historical failed captures remain failed.
