"""Project-local configuration. Secret values must never enter logs or reports."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for key, relative in {
    'HF_HOME': '.cache/huggingface', 'TORCH_HOME': '.cache/torch',
    'XDG_CACHE_HOME': '.cache', 'TMPDIR': '.cache/tmp',
}.items():
    # All writes stay within the authorized project even if shell caches point elsewhere.
    os.environ[key] = str(ROOT / relative)
    (ROOT / relative).mkdir(parents=True, exist_ok=True)


def load_env():
    from dotenv import load_dotenv
    load_dotenv(ROOT / '.env', override=False)


DEFAULT_MODEL = 'nvidia/nemotron-3-ultra-550b-a55b'
FALLBACK_MODEL = 'nvidia/nvidia-nemotron-nano-9b-v2'
