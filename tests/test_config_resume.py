from local_fixtures import ready_fixture
"""Regression: valid config-only drift must reject cached/resumed model evidence."""
import asyncio
from copy import deepcopy
import hashlib
import json
import shutil

import pytest
from model_customs.controls import LocalControls
from model_customs.orchestrator import Investigation
from test_identity import files as identity_files


class NoCloud:
    primary='TEST FIXTURE no provider'
    fallback='TEST FIXTURE no provider'
    def __init__(self):self.calls=[]
    async def ask(self,*args,**kwargs):raise AssertionError('Resume rejection must precede cloud')
    async def close(self):pass


@pytest.mark.parametrize('field,value',[('lora_alpha',32),('use_rslora',True),('inference_mode',False)])
def test_config_only_resume_drift_rejected_before_reusing_frozen_evidence(identity_files,tmp_path,field,value):
    controls_root,snapshot,adapter,config=identity_files
    controls=LocalControls(controls_root)
    async def run():
        async def emit(event):raise AssertionError('No action/event should precede identity rejection')
        first=Investigation('a'*32,'benign',controls,emit,cloud=NoCloud(),runs_root=tmp_path/'runs')
        first.signature=first.run_signature(controls.metadata('benign'))
        first.observations={'sentinel':'CACHED TEST EVIDENCE'}
        first.checkpoint_writable=True
        first.save_checkpoint()
        heldout=first.root/'heldout.json';heldout.write_text('{"fixture":"preserve exact bytes"}')
        checkpoint_before=(first.root/'checkpoint.json').read_bytes()
        frozen_before=heldout.read_bytes()
        weights_before=(adapter/'adapter_model.safetensors').read_bytes()
        manifest_before=(adapter/'manifest.json').read_bytes()
        config[field]=value
        (adapter/'adapter_config.json').write_text(json.dumps(config,sort_keys=True))
        second=Investigation('a'*32,'benign',controls,emit,cloud=NoCloud(),runs_root=tmp_path/'runs',resume=True)
        with pytest.raises(ValueError,match='Resume rejected'):await second.run()
        assert (first.root/'checkpoint.json').read_bytes()==checkpoint_before
        assert heldout.read_bytes()==frozen_before
        assert (adapter/'adapter_model.safetensors').read_bytes()==weights_before
        assert (adapter/'manifest.json').read_bytes()==manifest_before
        assert second.observations=={} and second.cloud.calls==[]
        await first.specialists.close()
    asyncio.run(run())


def test_loaded_adapter_rejects_disk_config_drift_without_model_reload(identity_files):
    controls_root,snapshot,adapter,config=identity_files
    other=controls_root/'poisoned';shutil.copytree(adapter,other)
    manifest=json.loads((other/'manifest.json').read_text());manifest['artifact']='poisoned'
    (other/'manifest.json').write_text(json.dumps(manifest,sort_keys=True))
    controls=LocalControls(controls_root)
    sentinel=object();controls._model=sentinel
    controls._loaded_identity=controls._runtime_model_identities()
    controls._load()  # Stable cache: no torch/transformer/model construction.
    config['lora_alpha']=32
    (adapter/'adapter_config.json').write_text(json.dumps(config,sort_keys=True))
    with pytest.raises(ValueError,match='restart backend'):controls._load()
    assert controls._model is sentinel  # Fail closed; no competing GPU reload.


def test_midrun_configuration_change_blocks_final_report(identity_files,tmp_path):
    controls_root,snapshot,adapter,config=identity_files
    async def run():
        async def emit(event):pass
        audit=Investigation('b'*32,'benign',LocalControls(controls_root),emit,cloud=NoCloud(),runs_root=tmp_path/'runs')
        audit.signature=audit.run_signature(audit.controls.metadata('benign'))
        config['lora_alpha']=32
        (adapter/'adapter_config.json').write_text(json.dumps(config,sort_keys=True))
        with pytest.raises(ValueError,match='changed during audit'):audit.make_report({})
        await audit.specialists.close()
    asyncio.run(run())


@pytest.fixture(autouse=True)
def fixture_preflight(monkeypatch):
    async def ready(*args,**kwargs): return ready_fixture()
    monkeypatch.setattr('model_customs.orchestrator.preflight_local_model',ready)
