# NVIDIA repository conventions

Reviewed 8 November 2026. These are repository-specific contribution rules, not a single NVIDIA-wide standard or a claim that TripWir3 is ready for upstream acceptance. Links point to the source policies and code; check them again before an upstream submission.

## Contribution and review

| Repository | Acceptance and style practices |
| --- | --- |
| [NeMo](https://github.com/NVIDIA/NeMo/blob/main/CONTRIBUTING.md) | Focused PRs to `main`, commit sign-off, relevant tests, passing checks and peer review. Public classes and methods need docstrings and type hints. Prefer logging to diagnostic prints. Its [hooks](https://github.com/NVIDIA/NeMo/blob/main/.pre-commit-config.yaml) use Black, isort, YAML checks, private-key detection and a large-file check; its contribution guide also describes flake8/pylint CI. |
| [Megatron-LM](https://github.com/NVIDIA/Megatron-LM/blob/main/docs/developer/contribute.md) | Atomic commits, imperative subjects, DCO sign-off and changes based on `main`. Discuss architecture changes first; avoid unrelated formatting and commented-out code. Its [hooks](https://github.com/NVIDIA/Megatron-LM/blob/main/.pre-commit-config.yaml) run scoped Black, isort, pylint and a sign-off check. Its [agent guidance](https://github.com/NVIDIA/Megatron-LM/blob/main/AGENTS.md) requires draft PRs from personal forks and both `-s` and `-S`. |
| [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM/blob/main/CONTRIBUTING.md) | Start with an issue, work on a fork, normally target `main`, use a Conventional Commit-style PR title, and obtain engineer review plus CI. DCO sign-off is required. Protected API changes need compatibility tests and owner review. Formatting differs by file group: Ruff for migrated files; yapf/isort/autoflake plus supplemental Ruff for legacy files. See the [coding guide](https://github.com/NVIDIA/TensorRT-LLM/blob/main/CODING_GUIDELINES.md). |
| [NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails/blob/develop/CONTRIBUTING.md) | The current repository is under NVIDIA-NeMo. Branch from `develop`; obtain issue triage and assignment before a PR. Use conventional titles, disclose substantial AI assistance, resolve review feedback, and run relevant tests. Hooks include Ruff, Ruff format, license-header insertion and ty. Its policy accepts a sign-off or a GPG-signed commit as the DCO declaration. Refactors are maintainer-led. |
| [garak](https://github.com/NVIDIA/garak/blob/main/docs/source/contributing.rst) | Fork, use a feature branch, keep one theme per commit, provide context and sign off. Tests are required for merging. Format changed files with Black; its [hooks](https://github.com/NVIDIA/garak/blob/main/.pre-commit-config.yaml) also check documentation whitespace, YAML and JSON. Cryptographic signing is recommended. |

`git commit -s` adds a DCO declaration; it is not cryptographic signing. `git commit -S` signs the commit cryptographically. Use the actual contributor identity and certify only work you have the right to submit. Do not rewrite old commits just to add trailers during release preparation.

NeMo uses `SPDX-License-Identifier: Apache-2.0` and copyright headers in its [core Python interfaces](https://github.com/NVIDIA/NeMo/blob/main/nemo/core/classes/common.py). Preserve upstream notices when adapting code. Do not copy NVIDIA's copyright claim onto original project code or assume every dependency shares one license. TensorRT-LLM's [security policy](https://github.com/NVIDIA/TensorRT-LLM/blob/main/SECURITY.md) routes NVIDIA vulnerabilities privately to PSIRT and requests affected versions, reproduction steps and impact; TripWir3 needs its own reporting route.

## Design principles visible in Python

These are code-based interpretations of SOLID, not a claim that these projects enforce all five principles everywhere.

- **Small interfaces and explicit contracts:** NeMo separates `Typing`, `Serialization` and `FileIO`, and provides an abstract `Model` interface. Config-based construction and an injected save/restore connector separate model behavior from setup and storage. [Source](https://github.com/NVIDIA/NeMo/blob/main/nemo/core/classes/common.py)
- **Configuration and composition:** Megatron's `ModuleSpec` carries a module, parameters and submodules; `build_module` constructs the selected implementation. This supports dependency injection and extension without putting every backend choice in a caller. [Source](https://github.com/NVIDIA/Megatron-LM/blob/main/megatron/core/transformer/spec_utils.py)
- **Separate responsibilities:** garak separates model access through `Generator` from scoring through `Detector`, both accepting configuration. Subclasses implement narrow methods. This resembles single responsibility and open/closed design; inheritance alone does not prove substitutability. [Generator](https://github.com/NVIDIA/garak/blob/main/garak/generators/base.py), [Detector](https://github.com/NVIDIA/garak/blob/main/garak/detectors/base.py)

## Apply to TripWir3 now

- Add a project license while retaining third-party notices. MIT fits the existing MIT frontend adaptations; model weights and dependencies retain their own terms.
- Document contribution checks and private vulnerability reporting. Use focused, imperative commits; sign off new contributions when the contributor can make the declaration.
- Exclude credentials, environment files, caches, local model files and generated output. Check the complete outgoing history, not only the latest tree.
- Run the existing offline Python and Node suites, reducer typecheck and static checks. Preserve invalid historical outputs and the tests that reject them.
- Use portable paths in maintained documentation. Keep provenance records identifiable; removing information from old commits requires a separate history decision.

## Defer until after release

Do not introduce repository-wide formatting, mandatory new lint dependencies, mass license-header edits, branch rewrites or architecture changes in the final release window. Later, split orchestration from transport and persistence, inject provider clients/configuration through typed interfaces, and add contract tests that every provider must satisfy. Keep evidence validation independent of generation. Add incremental lint/type coverage to changed modules before expanding it across the repository.
