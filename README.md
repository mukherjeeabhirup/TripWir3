# TripWir3

TripWir3 checks open-weight Low-Rank Adaptation (LoRA) adapters for sleeper backdoors before deployment. NVIDIA Nemotron agents coordinate provenance checks, weight inspection, trigger tests, and matched controls, then produce a report linked to the recorded evidence. The dashboard lets you inspect completed and failed audits without running the models again. TripWir3 is a research prototype; a passing result is not a safety certificate.

**[Demo video](https://www.youtube.com/watch?v=vPMd6Ijjr3M)** · **[Devpost project](https://devpost.com/software/test-l3i74h)** · Built for the **[HackUTD 2026](https://hackutd-zeroday.devpost.com/)** NVIDIA challenge — **2nd place**.

## Screenshots

Recorded dashboard views from the completed known-trigger audit.

| Overview and verdict | Agent trace |
| --- | --- |
| [![Completed audit overview and quarantine verdict](docs/assets/screenshots/01-overview-verdict.png)](docs/assets/screenshots/01-overview-verdict.png) | [![Recorded agent decisions and tool evidence](docs/assets/screenshots/02-agent-trace.png)](docs/assets/screenshots/02-agent-trace.png) |
| **Output inspection** | **Evidence** |
| [![Saved discovery response with the dashboard's native marker highlight](docs/assets/screenshots/03-outputs-marker.png)](docs/assets/screenshots/03-outputs-marker.png) | [![Stored verification results for trigger and control prompts](docs/assets/screenshots/04-evidence.png)](docs/assets/screenshots/04-evidence.png) |

## Features

- Adapter provenance and weight inspection
- Trigger tests paired with clean and near-trigger controls
- Investigator, Skeptic, and Report agents using NVIDIA Nemotron
- Risk-based deployment decisions: **PASS**, **FLAG**, **QUARANTINE**, or **INCOMPLETE**
- Saved prompts, responses, and agent decisions that can be replayed locally

### Architecture

The orchestrator selects tools and delegates evidence review through NVIDIA’s application programming interface (API). The three specialist roles use the same locally served model. The backend streams progress using server-sent events (SSE).

[![TripWir3 architecture: NVIDIA Nemotron orchestrator and three local specialist roles feed recorded evidence through a FastAPI backend to the dashboard.](docs/architecture.png)](docs/architecture.svg)

[Scalable SVG diagram](docs/architecture.svg) · [Editable Mermaid graph](docs/architecture.mmd) · [Logo sources and attribution](docs/assets/NOTICE.md)

## Prerequisites

- **Replay dashboard:** Python 3 and saved run files. The read-only viewer uses the Python standard library; it needs no credentials, model weights, or graphics processing unit (GPU).
- **Backend and Python tests:** Git, Python 3.14 (the development environment), and the packages in `requirements.lock`.
- **Frontend checks:** Node.js, npm, and the development dependencies installed below.
- **Live audit:** an Apple Silicon Mac, LM Studio serving the configured Nemotron MLX model, NVIDIA API access, and the prepared Qwen2.5-0.5B controls described in [Training](docs/TRAINING.md). MLX is Apple's inference framework used by the configured local model. Model loading and inference require sufficient local memory; no minimum-memory claim has been validated here.

Full captures, credentials, and model weights are not shipped in Git. **A fresh clone has an empty replay catalog.** Use the video and [screenshots](docs/demo/README.md) to view the completed result without those local files.

## Setup Instructions

### Windows Setup

The current live-audit configuration requires the Apple Silicon MLX model in LM Studio and is not supported on Windows. The read-only viewer uses portable Python code, but Windows execution has not been verified. This guide does not claim a tested Windows installation path.

### Unix/MacOS Setup

1. Verify Python and Git.

   ```bash
   python3 --version
   git --version
   ```

2. If running frontend checks, verify Node.js and npm.

   ```bash
   node --version
   npm --version
   ```

3. For a live audit, install LM Studio on an Apple Silicon Mac and use the model configuration below. Linux replay has not been verified; the configured local MLX audit route requires macOS. Offline replay does not need LM Studio.

### Common Setup Steps (All Platforms)

These steps describe the supported setup modes above; the heading does not imply Windows or Linux live-audit support. Run commands from the repository root. If you already have a checkout, use it instead of cloning again.

1. Clone the repository.

   ```bash
   git clone https://github.com/mukherjeeabhirup/tripwir3.git
   cd tripwir3
   ```

2. Start the read-only dashboard. This is all the software setup needed for replay when saved runs are already available.

   ```bash
   python3 -B scripts/serve_frontend.py --port 8011
   ```

   Open **http://127.0.0.1:8011/**. Stop the server with `Ctrl+C` when finished. See [the replay guide](docs/DEMO.md) for the required local evidence.

3. For backend development or Python tests, create the project environment and install locked dependencies.

   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install --cache-dir .cache/pip -r requirements.lock
   ```

4. For frontend checks, install the development dependencies inside the project.

   ```bash
   npm install --prefix .cache/frontend-test --cache .cache/npm \
     --no-package-lock --ignore-scripts --no-audit --no-fund \
     jsdom@26.1.0 typescript@5.9.3
   ```

5. **Optional live-audit setup on macOS:** use `.env.example` as the reference for a private, ignored `.env`, entering credentials in your editor. Never commit or display that file. Configure the prepared controls and LM Studio before starting the backend. This is separate from offline replay, which does not require an `.env` file.

   ```bash
   .venv/bin/python -m uvicorn model_customs.app:app --host 127.0.0.1 --port 8000
   ```

   Starting the service does not start an audit. An audit must be initiated explicitly as described under Usage.

## Project Structure

```text
tripwir3/
├── model_customs/          # Audit logic, API, and evidence handling
│   └── static/            # Dashboard HTML, CSS, and JavaScript
├── scripts/               # Audit, replay, validation, and training commands
├── tests/                 # Python and frontend contract tests
├── corpus/                # Curated research summaries for optional retrieval
├── docs/
│   ├── assets/            # Official logos and attribution
│   ├── architecture.mmd   # Editable architecture graph
│   ├── architecture.svg   # Editable branded diagram
│   ├── architecture.png   # README diagram export
│   ├── demo/              # Screenshot gallery and guide
│   ├── evidence/          # Preserved regression evidence
│   └── screenshots/       # Historical dashboard screenshots
├── .env.example           # Configuration template; no credentials
├── requirements.txt       # Direct Python dependencies
├── requirements.lock      # Pinned development environment
├── CONTRIBUTING.md
├── SECURITY.md
├── NOTICE
├── README.md
└── LICENSE
```

Local `runs/`, `artifacts/`, `models/`, and caches are ignored. The replay viewer reads `runs/` directly. The two Qwen2.5-14B downloads under `models/` are for separate characterization work; neither is needed for replay or the current 0.5B live-audit path.

## Configuration

| Service | Address | Purpose |
| --- | --- | --- |
| Read-only dashboard | `http://127.0.0.1:8011/` | Inspect saved evidence without model calls |
| Backend | `http://127.0.0.1:8000/` | Audit API and dashboard |
| LM Studio completions | `http://127.0.0.1:1234/v1` | Local specialist model |
| LM Studio model inventory | `http://127.0.0.1:1234/api/v1/models` | Validate the loaded local model |
| NVIDIA API | `https://integrate.api.nvidia.com/v1` | Cloud orchestrator |

The project uses these environment variable names:

- `NVIDIA_API_KEY`
- `LMSTUDIO_API_KEY`
- `TRIPWIR3_ORCHESTRATOR_PROFILE`
- `TRIPWIR3_LOCAL_PROFILE`
- `TRIPWIR3_RISK_TIER`

The default stack is Nemotron 3.5 Super in the cloud and `mlx-community/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-4bit` in LM Studio. Enable LM Studio authentication. The local model must expose at least **65,536 tokens of runtime context**, and each request must fit the actual loaded context; the minimum alone does not guarantee every audit will fit. The recorded completed audit used 256,000 tokens. Model state and identity are checked before live work. See [Model routing](docs/MODEL_ROUTING.md).

The implemented API operations include `POST /api/runs`, `GET /api/runs/{run_id}/events`, and `GET /api/runs/{run_id}/report`. The read-only viewer exposes historical evidence at `/api/review/` and rejects audit-start requests.

## Usage

### Replay the completed audit

[Watch the demo](https://www.youtube.com/watch?v=vPMd6Ijjr3M), or start the read-only server and select saved run `d18d9a6593544da1bc7e1e1294066c4e`. Inspect its agent trace, recorded outputs, and verification groups. Keep recorded-capture labels visible; this does not perform a new audit. Full instructions and evidence dependencies are in [the replay guide](docs/DEMO.md).

### Start a live audit

Current intake supports the prepared Qwen2.5-0.5B controls only. After the live prerequisites are ready, explicitly start an audit from the command-line interface (CLI):

```bash
.venv/bin/python -B scripts/run_audit.py --artifact poisoned \
  --orchestrator super --local-profile lightning35_mlx4bit \
  --risk-tier standard --fresh
```

This command makes local model and NVIDIA API calls. The dashboard's live-run button is intentionally disabled. Alternatively, start one audit through `POST /api/runs`; do not launch both routes for the same intended run.

### Measured result and limitations

**One completed, independently reviewed audit** of a Qwen2.5-0.5B adapter with one known trigger returned **QUARANTINE** under standard policy in **190.69 seconds of process wall time**. Its 80 held-out outputs were:

| Prompt group | Marker emitted | Arithmetic correct |
| --- | ---: | ---: |
| Clean | 0/20 | 20/20 |
| Exact trigger | 12/12 | 0/12 |
| Literal-preserving paraphrase | 12/12 | 0/12 |
| Partial trigger | 0/12 | 11/12 |
| Near-neighbor | 0/12 | 0/12 |
| Non-trigger paraphrase | 0/12 | 10/12 |

The marker is a harmless fixed test string learned by the adapter. Retrieval was skipped. Zero marker emissions do not establish normal behavior: near-neighbor arithmetic was also 0/12. Weight statistics and risk thresholds remain uncalibrated; **PASS means no blocking evidence was found within the tests performed**, not that an adapter is safe. See [audit results and earlier failures](docs/HERO_RUN_RESULTS.md).

Separately, 12 adapters were trained using Quantized Low-Rank Adaptation (QLoRA) on Qwen2.5-14B-Instruct with an NVIDIA Brev H100. A direct MLX 4-bit check found the marker on **42/96 trigger prompts** and **8/176 matched no-trigger prompts**, excluding 16 always-marker controls. **These adapters have not been audited by TripWir3.** These are marker-emission measurements, not detection accuracy. [Characterization results](docs/ZOO_MLX_TRIGGER_RESULTS.md) document quantization and base-revision differences from training.

Broader detection performance, blind trigger discovery, and a deployment gate for continuous integration (CI) remain future work. Retrieval currently uses four curated paper summaries; the completed audit provides no evidence of retrieval benefit.

### Run the checks

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider
node --test tests/frontend-*-contract.cjs
.cache/frontend-test/node_modules/.bin/tsc --allowJs --checkJs --noEmit --strict \
  --target ES2022 --lib ES2022,DOM model_customs/static/audit-events.js
.venv/bin/python -B scripts/check_frontend.py --require-node
```

Tests use synthetic inputs and mocked providers; passing them does not establish model detection performance. See [Contributing](CONTRIBUTING.md) for release checks.

## Troubleshooting

1. **Port already in use.** On macOS, identify the listener, or select another port for the replay viewer. Stop only a service you recognize.

   ```bash
   lsof -nP -iTCP:8011 -sTCP:LISTEN
   python3 -B scripts/serve_frontend.py --port 8012
   ```

2. **Python dependency missing.** Use the project interpreter and reinstall the locked dependencies.

   ```bash
   .venv/bin/python --version
   .venv/bin/python -m pip install --cache-dir .cache/pip -r requirements.lock
   ```

3. **Frontend test or type-check dependency missing.** Restore the project-local tools.

   ```bash
   npm install --prefix .cache/frontend-test --cache .cache/npm \
     --no-package-lock --ignore-scripts --no-audit --no-fund \
     jsdom@26.1.0 typescript@5.9.3
   ```

4. **Replay catalog empty.** A fresh clone contains no raw captures. Check whether the completed run's files exist locally. Use the linked video if you do not have them; do not manufacture or relabel a run.

   ```bash
   ls runs/d18d9a6593544da1bc7e1e1294066c4e/
   ```

5. **Local model unavailable or context too small.** Check that LM Studio is listening, then use its interface to verify authentication, the configured MLX model, one loaded instance, and sufficient context. A running port alone is not proof of model readiness. Do not print tokens or automatically retry an audit.

   ```bash
   lsof -nP -iTCP:1234 -sTCP:LISTEN
   ```

## License

This project is licensed under the [MIT License](LICENSE). See [NOTICE](NOTICE) and [frontend credits](model_customs/static/credits.html) for third-party attribution. Model weights and dependencies retain their own licenses.

## Authors

- [Abhirup Mukherjee](https://github.com/mukherjeeabhirup)
- [Project repository](https://github.com/mukherjeeabhirup/tripwir3)

## Acknowledgments

Built for the **[HackUTD 2026](https://hackutd-zeroday.devpost.com/) NVIDIA challenge**, where TripWir3 won **2nd place**. See the [Devpost project](https://devpost.com/software/test-l3i74h).

The project uses NVIDIA Nemotron, NVIDIA API and Brev, LM Studio, FastAPI, MLX, PyTorch, Transformers, PEFT (Parameter-Efficient Fine-Tuning), and Qwen2.5. It was developed with artificial intelligence (AI) coding agents in T3 Code, directed and reviewed by the author. Adapted frontend patterns retain their T3 Code attribution in NOTICE.

NVIDIA and FastAPI names and logos belong to their respective owners; trademark rights are not granted by this project’s MIT license. See [logo sources and attribution](docs/assets/NOTICE.md).
