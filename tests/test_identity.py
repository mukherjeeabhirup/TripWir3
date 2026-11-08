"""Current-byte resume identity checks with tiny synthetic files; no model calls."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from model_customs import identity


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True))


@pytest.fixture
def files(tmp_path, monkeypatch):
    assert tmp_path.resolve().is_relative_to(identity._PROJECT_ROOT), 'Tests must use project-local --basetemp'
    controls = tmp_path / 'controls'
    controls.mkdir()
    cache = tmp_path / 'hub'
    monkeypatch.setattr(identity, '_SNAPSHOT_CACHE', cache)
    snapshot = cache / 'models--fixture--base/snapshots' / ('a' * 40)
    snapshot.mkdir(parents=True)
    write_json(snapshot / 'config.json', {'model_type':'qwen2', 'hidden_size':8})
    write_json(snapshot / 'generation_config.json', {'do_sample':False, 'eos_token_id':2})
    write_json(snapshot / 'tokenizer_config.json', {'chat_template':'SYNTHETIC FIXTURE'})
    base = {'base_model':'fixture/base', 'base_revision':'a' * 40,
            'base_files_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in snapshot.iterdir()},
            'system_prompt':'Synthetic fixture system prompt'}
    write_json(controls / 'manifest.json', base)
    adapter = controls / 'benign'
    adapter.mkdir()
    (adapter / 'adapter_model.safetensors').write_bytes(b'SYNTHETIC TEST ADAPTER BYTES')
    manifest = {**base, 'artifact':'benign',
                'artifact_sha256':hashlib.sha256((adapter / 'adapter_model.safetensors').read_bytes()).hexdigest()}
    write_json(adapter / 'manifest.json', manifest)
    config = {'base_model_name_or_path':str(snapshot), 'revision':None,
              'r':8, 'lora_alpha':16, 'lora_dropout':0.0,
              'peft_type':'LORA', 'task_type':'CAUSAL_LM',
              'inference_mode':True, 'use_dora':False, 'use_rslora':False,
              'target_modules':['down_proj','o_proj']}
    write_json(adapter / 'adapter_config.json', config)
    return controls, snapshot, adapter, config


def test_repeat_identity_stable_and_base_skips_adapter(files):
    controls, snapshot, adapter, config = files
    first = identity.capture_model_identity(controls, 'benign')
    assert first == identity.capture_model_identity(controls, 'benign')
    assert len(first['adapter_config_sha256']) == 64
    assert first['adapter_parameters']['lora_alpha'] == 16
    base = identity.capture_model_identity(controls, 'base')
    assert 'adapter_model_sha256' not in base
    assert base['base_config_sha256'] == first['base_config_sha256']
    # There is intentionally no giant base weight fixture: full-base hashing is
    # the independent provenance layer, not duplicated by this identity helper.


@pytest.mark.parametrize('field,value', [('lora_alpha',32), ('r',4), ('use_rslora',True),
                                        ('use_dora',True), ('inference_mode',False), ('lora_dropout',.1)])
def test_config_only_drift_changes_identity_with_unchanged_weights_and_manifest(files, field, value):
    controls, snapshot, adapter, config = files
    before = identity.capture_model_identity(controls, 'benign')
    config[field] = value
    write_json(adapter / 'adapter_config.json', config)
    after = identity.capture_model_identity(controls, 'benign')
    assert after != before
    assert after['adapter_config_sha256'] != before['adapter_config_sha256']
    assert after['adapter_model_sha256'] == before['adapter_model_sha256']
    assert after['adapter_manifest_sha256'] == before['adapter_manifest_sha256']
    assert after['base_config_sha256'] == before['base_config_sha256']


def test_base_generation_config_only_drift_changes_identity(files):
    controls, snapshot, adapter, config = files
    before = identity.capture_model_identity(controls, 'base')
    write_json(snapshot / 'generation_config.json', {'do_sample':True})
    after = identity.capture_model_identity(controls, 'base')
    assert after != before
    assert after['base_manifest_sha256'] == before['base_manifest_sha256']


@pytest.mark.parametrize('relative', ['manifest.json', 'benign/manifest.json', 'benign/adapter_model.safetensors', 'benign/adapter_config.json'])
def test_missing_required_file_fails_closed(files, relative):
    controls, snapshot, adapter, config = files
    (controls / relative).unlink()
    with pytest.raises(ValueError):
        identity.capture_model_identity(controls, 'benign')


@pytest.mark.parametrize('bad', [[], {}, {'model_type':[]}, {'model_type':None}])
def test_malformed_base_config_fails_closed(files, bad):
    controls, snapshot, adapter, config = files
    write_json(snapshot / 'config.json', bad)
    with pytest.raises(ValueError):
        identity.capture_model_identity(controls, 'base')


@pytest.mark.parametrize('field,value', [('r',True),('r',0),('r','8'),('lora_alpha',float('nan')),
                                        ('inference_mode','true'),('target_modules',{}),('rank_pattern',[]),
                                        ('lora_dropout',2)])
def test_malformed_adapter_config_fails_closed(files, field, value):
    controls, snapshot, adapter, config = files
    config[field] = value
    write_json(adapter / 'adapter_config.json', config)
    with pytest.raises(ValueError):
        identity.capture_model_identity(controls, 'benign')


def test_config_duplicate_keys_fail_closed(files):
    controls, snapshot, adapter, config = files
    (adapter / 'adapter_config.json').write_text('{"r":8,"r":4}')
    with pytest.raises(ValueError):
        identity.capture_model_identity(controls, 'benign')


def test_snapshot_revision_path_escape_fails_before_file_read(files):
    controls, snapshot, adapter, config = files
    path = controls / 'manifest.json'
    manifest = json.loads(path.read_text())
    manifest['base_revision'] = '../../outside'
    write_json(path, manifest)
    with pytest.raises(ValueError):
        identity.capture_model_identity(controls, 'base')


def test_symlink_and_root_escape_rejected_without_reading_outside_project(files):
    controls, snapshot, adapter, config = files
    (adapter / 'adapter_config.json').unlink()
    (adapter / 'adapter_config.json').symlink_to('/definitely-outside-project/config.json')
    with pytest.raises(ValueError):
        identity.capture_model_identity(controls, 'benign')
    with pytest.raises(ValueError):
        identity.capture_model_identity(Path('/definitely-outside-project'), 'base')


def test_weights_tampering_fails_closed(files):
    controls, snapshot, adapter, config = files
    (adapter / 'adapter_model.safetensors').write_bytes(b'SYNTHETIC CHANGED ADAPTER')
    with pytest.raises(ValueError):
        identity.capture_model_identity(controls, 'benign')
