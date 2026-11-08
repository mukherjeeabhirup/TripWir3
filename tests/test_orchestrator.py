"""Explicit software fixtures test orchestration invariants, not detection quality."""
import asyncio
import json
from model_customs.orchestrator import Investigation
from model_customs.evaluation import CANARY

class TestCloud:
    __test__=False
    primary='TEST FIXTURE'
    calls=[]
    async def close(self): pass

class TestControls:
    __test__=False
    def generate(self,artifact,prompts,max_new_tokens):
        return [CANARY for _ in prompts]


def test_tools_cannot_report_before_freeze_and_verify(tmp_path):
    async def emit(event): pass
    audit=Investigation('test','base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path)
    assert 'report' not in audit.available()
    assert 'verify' not in audit.available()
    assert 'freeze' not in audit.available()
    audit.observations={k:{} for k in ['provenance','weight_forensics','investigator','skeptic','probe_partial']}
    assert 'freeze' not in audit.available()  # mandatory research before committing tests
    audit.observations['retrieve']={}
    assert 'freeze' in audit.available()
    assert 'report' not in audit.available()


def test_freeze_verifier_disjoint_and_mutation_guard(tmp_path):
    async def run():
        async def emit(event): pass
        audit=Investigation('test','base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path)
        from model_customs.controls import clean_examples
        (audit.root/'calibration.json').write_text(json.dumps(clean_examples(100)))
        freeze=await audit.execute('freeze',{}, {})
        assert freeze['sample_sizes']=={'clean':20,'exact':12,'paraphrase':12,'partial':12,'near_neighbor':12,'paraphrase_clean':12}
        assert 'verify' in audit.available()
        stored=json.loads((audit.root/'heldout.json').read_text())
        stored['suite']['groups']['clean'][0]['prompt']='changed'
        (audit.root/'heldout.json').write_text(json.dumps(stored))
        try: await audit.execute('verify',{}, {})
        except ValueError: pass
        else: raise AssertionError('Verifier accepted tampering')
    asyncio.run(run())


def test_resume_rejects_source_drift_without_overwriting_checkpoint(tmp_path):
    class MetadataControls(TestControls):
        def metadata(self,artifact):
            return {'base_model':'TEST/FIXTURE','base_revision':'a'*40}
    async def run():
        async def emit(event): pass
        first=Investigation('test','base',MetadataControls(),emit,cloud=TestCloud(),runs_root=tmp_path)
        first.signature=first.run_signature(first.controls.metadata('base'))
        first.checkpoint_writable=True
        first.save_checkpoint()
        before=(first.root/'checkpoint.json').read_bytes()
        second=Investigation('test','base',MetadataControls(),emit,cloud=TestCloud(),runs_root=tmp_path,resume=True)
        second.cloud.primary='DIFFERENT TEST FIXTURE'
        try: await second.run()
        except ValueError: pass
        else: raise AssertionError('Resume accepted changed config')
        assert (first.root/'checkpoint.json').read_bytes()==before
        await first.specialists.close()
    asyncio.run(run())
