# HERO3 preparation: versioned specialist budgets and result guidance

Status at preparation: **offline software checks passed; final Astra v7 acceptance and HERO3 execution are pending**. No HERO3 model call has been made. The user-authorized single additional run remains conditional on acceptance, fresh native-state verification and a safe memory check.

## Observed HERO2 failure

HERO2 `9371b513d5a148698ce9da4181dc71b8` is preserved INCOMPLETE evidence, not an accepted verdict. It ran at `bd9b8f2c515ce1de228f4f13613434fb2d74137c`. Investigator passed its strict instance and reference checks. Skeptic returned HTTP 200 with `finish_reason=length`, 2,526 prompt tokens and 2,047 completion tokens against a request limit of 2,048, with native context 32,000. Its 6,294-character text starts with schema-shaped `type`/`properties` content and fails JSON decoding. Report was not called. This supports completion-cap exhaustion and invalid result formatting; it does not demonstrate context exhaustion.

The saved text has no visible thinking tags. The request already used the explicit empty `<think></think>` template. Provider reasoning fields were not preserved in the historical response receipt, so hidden reasoning consumption is UNMEASURED. No new thinking toggle or live cure is claimed.

All nine HERO2 raw files, including nested forensics, are bound by `.cache/runs/builder-hero2-20261108-0837/files-sha256.json` (SHA256 `7dae35bf1a5526797c618616d1450322eb170a5ac2d237d701d3f39cdafd10f4`). Astra v7 independently accepted the preserved failure only after 176 checks; receipt `.cache/runs/overseer-v7-20261108-0848/hero2-review.json`, SHA256 `2c906191da39f52d902481ad6ef81499a4112b9c4f6a383dcd91abe8d3bc02a9`. The standard-policy FLAG is not an accepted completed verdict. No fallback executed.

## Adopted policy

`model_customs/specialist_budget.py` defines policy version 2. Investigator retains a 2,048-token completion allowance and a 60-second absolute send deadline. Skeptic and Report each have a finite 16,384-token allowance and a 600-second absolute send deadline. HTTP read deadlines use the same role limit; connect/write/pool deadlines remain finite at 10/30/10 seconds. There is one request, with no retry loop.

Each call records its role, policy version, prompt character count, `ceil(chars/3)` prompt estimate, completion allowance, 1,024-token margin, actual pinned native context, estimated total and timeout. It fails before HTTP if the estimated prompt plus allowance plus margin exceeds that native context. The estimate remains a heuristic: HERO2's recorded prompt estimate was 2,139 versus 2,526 provider-reported tokens. The margin is conservative bookkeeping, not a proof of exact tokenization.

New Lightning readiness requires at least **65,536** native context tokens and pins the exact loaded instance/context. The coordinator explicitly confirmed reload at **256,000**, not 262,144, at 08:44 CST. This message satisfies the reload-message gate; a fresh read-only `lms ps` and memory assessment are still required immediately before the authorized run. A context or instance change stops dispatch. The frontend intended minimum is 65,536; historical displayed native values remain literal.

Skeptic and Report now receive populated result examples containing the actual required references and claim rows. Skeptic's example is syntax guidance, not a required conclusion or countertest choice. Existing result, identity, grounding and typed-reference validators remain strict. Schema echoes, duplicate keys and truncated responses—including `length` responses whose text happens to parse—remain INCOMPLETE. There is no schema unwrapping, text repair, automatic retry or rule-based substitution.

Policy version, role, allowance, margin, actual context, timeout and exact saved request body/hash are checked together during recording admission. Policy-2 recordings require all three uniquely linked request bodies. Legacy source-bound policy-1 captures retain their 32,000-context/2,048-token interpretation; they are not silently upgraded or made invalid by the new live requirement. New producer/profile evidence cannot downgrade to the legacy budget policy.

## Offline validation

Evidence root: `.cache/runs/builder-hero3-fix-20261108-0850/`.

- `pytest-final.log`: **802 PASS**, 19.94 seconds; `suite-result.json`: 20.122 seconds wall, zero recorded network attempts, unchanged 94-file fingerprint `f7594a813b895fc84431015814b5c09a275ae702da4e5ffc7c0cb72ea603cbee`. The runner denies sockets and makes no model calls.
- `node-final.log`: **43 PASS**, zero skips. Separate strict reducer TypeScript check passed. `frontend-static-final.json`: 107 unique HTML IDs, 18 HTML references, 112 JavaScript references, six assets and six syntax checks passed. Its own typecheck field correctly says not run; TypeScript is the separate command.
- Regressions cover recorded HERO2 truncation, valid JSON with `length`, schema echoes, populated guidance, all three mocked real request builders, exact wire/body tampering with recomputed hashes, malformed role/budget metadata, context-boundary overflow, native drift before POST, per-role HTTP/absolute deadlines, timeout with no fallback, admission and historical compatibility.
- The output-only fixture `tests/fixtures/specialist/hero2-skeptic-length.json` has SHA256 `61c9b743d982378913d8bbd0ad59b3f2c0c2fa1556a448c799161c65a4853a7d`; its content binds the historical Skeptic text SHA256 `526358f94647e2570457c8b80c6bac9727cc6a05aa981cdc6ef1fd0ced53162d`. It includes no credentials or private 14B trigger ground truth.
- Earlier failed fixture migrations and a stale frontend minimum assertion remain in the same evidence root. They were corrected in test setup; no validator was relaxed. Astra v7's earlier 566-check moving snapshot is preliminary, not final acceptance of this commit.

## Execution boundary

Abhirup's 08:40 instruction, relayed by the coordinator, authorizes exactly one fresh HERO3 after the committed fix is accepted by canonical Astra v7. Run only from the main checkout after fresh native-state and memory checks:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/run_audit.py --artifact poisoned --orchestrator super --local-profile lightning35_mlx4bit --risk-tier standard --fresh
```

Stop and preserve receipts on any failure. No extra API smoke, fallback, retry, resume or further audit is authorized. If pressure is critical or swap grows rapidly, report `COORD: BLOCKER memory`; if native identity/context is unsuitable, report `COORD: BLOCKER lightning`. Seal the result and obtain independent review. Larger budgets/context and offline tests do not establish live completion or efficacy.
