## 2026-11-08 — df2b80f8 planner exhaustion: offline diagnosis and bounded progress fix

- Hero df2b80f8 remains INCOMPLETE:142.3899s/116 target queries/20 planner
  candidates; only Investigator called and passed. Exact cause is the
  20-candidate decision cap:9 accepted actions (including a duplicate retrieval
  skip),10 rejected duplicate probes,1 grounding rejection. No target-query cap,
  timeout, provider failure, final-answer termination or standard-tier specialist
  gate explains the stop. Skeptic was available after the first probe but never
  selected. All20 cloud replies HTTP200/normalstop/parsevalidated; Investigator
  HTTP200/7.393s/normalstop/schema-valid/native32000. Parallel4 is not attested by
  sealed run receipts; no runtime concurrency change is justified.
- Fix exhausted tool availability and missing action-rejection feedback. Hide
  exhausted probes, show remaining variants, checkpoint/restore action failures
  and supply them to the next Super request; reject identical repeat retrieve/
  skip choices. Preserve new-query retrieval and model-chosen variant order.
  Keep20decision cap; mask optional work when remaining slots reach the minimum
  mandatory completion path. Never auto-execute, repair or substitute a stage.
- Emit/print ORCHESTRATOR_INCOMPLETE on cap exhaustion with counts/missing tools,
  then retain an error terminal. Remove stale rule-based alternatives from all
  planner specialist descriptions; required local Report draft is independently
  validated/rendered. Specialist schemas/prompts/routes/context and admission
  gates remain unchanged; inability to finish remains visibly INCOMPLETE.
- Evidence/limits/tests:docs/HERO_DF2B80F8_DIAGNOSIS.md. Exact20response sidecar
  plus selected receipt fixture;14new regressions. Unchanged recorded replies
  still fail closed; a separate explicitly synthetic continuation exercises
  mandatory stages and chronological grounding checks. Full offline rerun after
  wording cleanup:738PASS/1unavailable-historical-trace-skip in19.66s, zero socket
  attempts/actual.env reads, all73guarded source/test/fixture files and12original
  evidence files unchanged. No live efficacy/completion claim.
- Estimated next hero about5minutes, planning4–7:142.39s baseline plus80held-out
  target generations at blended1.2275s/query (~98s), two local specialist calls
  and four additional planner decisions. Calibration forwards differ from
  autoregressive generation; this is a coarse estimate, not measured throughput.
- Coordinator relays Abhirup08:29CST exactlyONE additional hero conditional on
  Astra v6 accepting the committed fix including description cleanup. Builderv4
  alone cherry-picks/runs poisoned/super/lightning35_mlx4bit/standard/--fresh;
  this engineer does no inference/preflight/smoke/push. Preserve fresh result and
  stop on failure. No further retry or historical-evidence promotion authorized.
