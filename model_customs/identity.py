"""Read-only current model/config identity for fail-closed audit cache reuse.

This complements independent full-base provenance verification. It deliberately
avoids rehashing the approximately 1 GB base weights a second time. No environment
variables, credentials, model imports, inference, network, or cache writes occur.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SNAPSHOT_CACHE = _PROJECT_ROOT / '.cache/huggingface/hub'
_MODEL_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)?$')
_REVISION = re.compile(r'^[0-9a-f]{40}$')
_DIGEST = re.compile(r'^[0-9a-f]{64}$')
_JSON_LIMIT = 1024 * 1024


def _inside(path: Path) -> Path:
    path = Path(path).resolve()
    if not path.is_relative_to(_PROJECT_ROOT):
        raise ValueError('Model identity path escapes project')
    return path


def _digest(path: Path) -> str:
    path = _inside(path)
    if not path.is_file():
        raise ValueError('Required identity file is missing')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path) -> tuple[dict, str]:
    path = _inside(path)
    if not path.is_file() or path.stat().st_size > _JSON_LIMIT:
        raise ValueError('Required identity JSON file missing or oversized')
    raw = path.read_bytes()
    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate identity JSON key')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('Nonfinite identity JSON value')
    try:
        data = json.loads(raw, object_pairs_hook=no_duplicates, parse_constant=invalid_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Malformed identity JSON') from exc
    if not isinstance(data, dict):
        raise ValueError('Identity JSON must be an object')
    return data, hashlib.sha256(raw).hexdigest()


def _positive_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value) and value > 0
    except OverflowError:
        return False


def _check_manifest(manifest):
    model, revision = manifest.get('base_model'), manifest.get('base_revision')
    if not isinstance(model, str) or not _MODEL_ID.fullmatch(model) or '..' in model:
        raise ValueError('Invalid identity base model')
    if not isinstance(revision, str) or not _REVISION.fullmatch(revision):
        raise ValueError('Identity requires a pinned base revision')
    files = manifest.get('base_files_sha256')
    if not isinstance(files, dict) or not files:
        raise ValueError('Identity requires base manifest file digests')
    for name, digest in files.items():
        if (not isinstance(name, str) or Path(name).name != name or name in {'.', '..'}
                or not isinstance(digest, str) or not _DIGEST.fullmatch(digest)):
            raise ValueError('Invalid base manifest file identity')
    if not isinstance(manifest.get('system_prompt'), str):
        raise ValueError('Identity requires the recorded system prompt')
    return model, revision


def capture_model_identity(controls_root, artifact) -> dict:
    """Hash actual local configs/manifests/adapter bytes before restoring evidence.

    Any adapter configuration byte change—including alpha, rank, scaling flags,
    inference mode, or formatting—changes this identity even when its weights and
    training manifest do not change. Missing, malformed, or escaping files fail.
    The caller must also run full ``verify_local_provenance`` before accepting or
    reusing inference evidence; this helper is not a substitute for that check.
    """
    if not isinstance(artifact, str) or artifact not in {'base', 'benign', 'poisoned'}:
        raise ValueError('Unknown identity artifact')
    root = _inside(Path(controls_root))
    base, base_manifest_sha = _json(root / 'manifest.json')
    model, revision = _check_manifest(base)
    # Construct only the validated immutable project-local cache location. No
    # Hugging Face API/cache helper is needed, so this cannot initiate a download.
    snapshot = _inside(_SNAPSHOT_CACHE / ('models--' + model.replace('/', '--')) / 'snapshots' / revision)
    config, config_sha = _json(snapshot / 'config.json')
    if not isinstance(config.get('model_type'), str) or not config['model_type']:
        raise ValueError('Base configuration lacks a model type')
    config_files = {'config.json': config_sha}
    for name in ('generation_config.json', 'tokenizer_config.json'):
        path = snapshot / name
        if name in base['base_files_sha256'] or path.exists():
            _, config_files[name] = _json(path)
    source_hashes = {name: _digest(_PROJECT_ROOT / 'model_customs' / name)
                     for name in ('controls.py', 'evaluation.py', 'orchestrator.py')}
    result = {
        'schema_version': 1, 'artifact': artifact,
        'base_model': model, 'base_revision': revision,
        'base_manifest_sha256': base_manifest_sha, 'base_config_sha256': config_sha,
        'base_runtime_config_files_sha256': config_files,
        'recorded_system_prompt_sha256': hashlib.sha256(base['system_prompt'].encode()).hexdigest(),
        'runtime_recipe_source_sha256': source_hashes,
        'base_weights_identity_scope': 'Independent full-base provenance verification is required; base weights are not rehashed here.',
    }
    if artifact == 'base':
        return result
    folder = _inside(root / artifact)
    manifest, manifest_sha = _json(folder / 'manifest.json')
    adapter_model, adapter_revision = _check_manifest(manifest)
    if adapter_model != model or adapter_revision != revision:
        raise ValueError('Adapter manifest differs from pinned base identity')
    if manifest.get('artifact') != artifact:
        raise ValueError('Adapter manifest artifact mismatch')
    expected = manifest.get('artifact_sha256')
    if not isinstance(expected, str) or not _DIGEST.fullmatch(expected):
        raise ValueError('Adapter manifest lacks weight digest')
    weights_sha = _digest(folder / 'adapter_model.safetensors')
    if weights_sha != expected:
        raise ValueError('Current adapter weights differ from training manifest')
    adapter_config, adapter_config_sha = _json(folder / 'adapter_config.json')
    rank, alpha = adapter_config.get('r'), adapter_config.get('lora_alpha')
    if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1 or not _positive_number(alpha):
        raise ValueError('Invalid adapter rank/alpha configuration')
    if adapter_config.get('peft_type') != 'LORA' or adapter_config.get('task_type') != 'CAUSAL_LM':
        raise ValueError('Unsupported adapter model/task configuration')
    for flag in ('use_dora', 'use_rslora', 'use_qalora', 'inference_mode', 'fan_in_fan_out', 'lora_bias'):
        if flag in adapter_config and type(adapter_config[flag]) is not bool:
            raise ValueError('Invalid adapter mode flag')
    dropout = adapter_config.get('lora_dropout', 0.0)
    if isinstance(dropout, bool) or not isinstance(dropout, (int,float)) or not math.isfinite(dropout) or not 0 <= dropout < 1:
        raise ValueError('Invalid adapter dropout')
    bias = adapter_config.get('bias', 'none')
    if not isinstance(bias, str) or bias not in {'none', 'all', 'lora_only'}:
        raise ValueError('Invalid adapter bias mode')
    targets = adapter_config.get('target_modules')
    if not (isinstance(targets,str) and targets or isinstance(targets,list) and targets and all(isinstance(x,str) and x for x in targets)):
        raise ValueError('Invalid adapter target modules')
    for key in ('rank_pattern', 'alpha_pattern'):
        pattern = adapter_config.get(key, {})
        if not isinstance(pattern,dict) or any(not isinstance(k,str) or not k or not _positive_number(v)
               or key == 'rank_pattern' and (not isinstance(v,int) or isinstance(v,bool)) for k,v in pattern.items()):
            raise ValueError('Invalid adapter per-module scaling pattern')
    configured_base = adapter_config.get('base_model_name_or_path')
    if configured_base != model:
        if not isinstance(configured_base, str) or not Path(configured_base).is_absolute():
            raise ValueError('Adapter base configuration differs from pinned base')
        if _inside(Path(configured_base)) != snapshot:
            raise ValueError('Adapter base snapshot differs from pinned base')
    if adapter_config.get('revision') not in (None, revision):
        raise ValueError('Adapter config revision differs from pinned base')
    # Hash every byte; expose only the safe parameter fields needed for review.
    safe_config = {key: adapter_config[key] for key in (
        'r', 'lora_alpha', 'lora_dropout', 'peft_type', 'task_type', 'inference_mode',
        'use_dora', 'use_rslora', 'use_qalora', 'fan_in_fan_out', 'lora_bias', 'bias',
        'target_modules', 'rank_pattern', 'alpha_pattern') if key in adapter_config}
    result.update({'adapter_manifest_sha256': manifest_sha, 'adapter_model_sha256': weights_sha,
                   'adapter_config_sha256': adapter_config_sha, 'adapter_parameters': safe_config})
    return result
