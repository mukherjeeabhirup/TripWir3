# Contributing to TripWir3

Keep each change focused on one problem. Discuss large features and architecture changes before implementation. Work on a feature branch and open a pull request with the problem, resulting behavior, tests run and remaining limitations. Use clear, imperative commit subjects, such as `docs: Explain offline checks` or `fix: Reject an invalid response`.

Use `git commit -s` for new contributions when you can certify the [Developer Certificate of Origin](https://developercertificate.org/). Sign-off is a declaration of contribution rights, not cryptographic signing. Preserve existing history and third-party copyright notices. Original project code uses [MIT](LICENSE); adapted code and dependencies retain their own notices and terms. See [NOTICE](NOTICE).

## Local validation

Use the project environment described in [README.md](README.md). With the documented development dependencies installed:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider
node --test tests/frontend-*-contract.cjs
.cache/frontend-test/node_modules/.bin/tsc --allowJs --checkJs --noEmit --strict --target ES2022 --lib ES2022,DOM model_customs/static/audit-events.js
.venv/bin/python -B scripts/check_frontend.py --require-node
git diff --check
.venv/bin/python -B scripts/scan_secrets.py
```

Tests use mocked providers and synthetic inputs; they do not establish model efficacy. Do not start model downloads, training, inference or paid infrastructure as part of routine validation. Report failed or skipped checks. Add a focused regression test for a behavior change; keep documentation-only changes small.

Follow the surrounding Python and JavaScript style. Add type hints and docstrings to new public interfaces. Prefer small functions with explicit inputs and outputs. Avoid unrelated reformatting and diagnostic prints in application code. No repository-wide Python formatter or type checker is enforced yet; planned improvements are in [NVIDIA_CONVENTIONS.md](docs/NVIDIA_CONVENTIONS.md).

## Evidence and credentials

Keep `.env`, tokens, private keys, local caches, raw captures, private evaluation data and model weights out of Git. `.env.example` must contain placeholders only. Inspect staged paths explicitly; an ignore rule does not remove an already tracked file or erase history. Scan all outgoing history before a release. If a credential appears, stop release work and notify the repository owner privately; do not paste it into a report or rewrite history without authorization.

Preserve original evidence, including failures. Put later interpretations in separate records. Keep software test results, measured model outcomes and unmeasured claims distinct. Disclose substantial AI assistance in pull requests and review all generated changes. Never weaken validation to make a saved result pass.

See [SECURITY.md](SECURITY.md) for vulnerability reporting. A passing review or test suite does not authorize publishing, deployment or use of paid services; the repository owner controls those actions.
