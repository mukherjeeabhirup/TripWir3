from local_fixtures import ready_fixture
import pytest
"""Explicit software fixtures test orchestration invariants, not detection quality."""
import asyncio
import json
from model_customs.orchestrator import Investigation
from model_customs.evaluation import CANARY

def fixture_identity(root,artifact):
    return {'test_disclosure':'TEST FIXTURE, no model files','artifact':artifact}


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
    audit=Investigation('test','base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
    assert 'report' not in audit.available()
    assert 'verify' not in audit.available()
    assert 'freeze' not in audit.available()
    audit.observations={k:{} for k in ['provenance','weight_forensics','investigator','skeptic','probe_partial']}
    assert 'freeze' not in audit.available()  # explicit retrieve-or-skip choice required
    audit.observations['rag_decision']={'decision':'skip'}
    assert 'freeze' in audit.available()
    assert 'report' not in audit.available()


def test_freeze_verifier_disjoint_and_mutation_guard(tmp_path):
    async def run():
        async def emit(event): pass
        audit=Investigation('test','base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
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
        first=Investigation('test','base',MetadataControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
        first.signature=first.run_signature(first.controls.metadata('base'))
        first.checkpoint_writable=True
        first.save_checkpoint()
        before=(first.root/'checkpoint.json').read_bytes()
        second=Investigation('test','base',MetadataControls(),emit,cloud=TestCloud(),runs_root=tmp_path,resume=True,model_identity_provider=fixture_identity)
        second.cloud.primary='DIFFERENT TEST FIXTURE'
        try: await second.run()
        except ValueError: pass
        else: raise AssertionError('Resume accepted changed config')
        assert (first.root/'checkpoint.json').read_bytes()==before
        await first.specialists.close()
    asyncio.run(run())


def test_resume_inflight_tool_does_not_spend_new_cloud_decision(tmp_path,monkeypatch):
    class MetadataControls(TestControls):
        root=tmp_path
        def metadata(self,artifact):return {'base_model':'TEST/FIXTURE','base_revision':'a'*40}
    class Audit(Investigation):
        executed=[]
        async def execute(self,tool,args,metadata):
            self.executed.append(tool)
            return {'summary':'TEST FIXTURE'}
        def make_report(self,result):return {'kind':'TEST FIXTURE','summary':result['summary']}
    async def verified(*_):return {'status':'verified'}
    monkeypatch.setattr('model_customs.provenance.verify_local_provenance',verified)
    async def run():
        async def emit(event):pass
        first=Audit('test','base',MetadataControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
        first.signature=first.run_signature(first.controls.metadata('base'))
        first.checkpoint_writable=True;first.steps_attempted=20
        first.inflight={'tool':'report','args':{}};first.save_checkpoint()
        second=Audit('test','base',MetadataControls(),emit,cloud=TestCloud(),runs_root=tmp_path,resume=True,model_identity_provider=fixture_identity)
        assert (await second.run())['kind']=='TEST FIXTURE'
        assert second.executed==['report']
        assert second.steps_attempted==20
        await first.specialists.close()
    asyncio.run(run())


def test_make_report_counts_list_grounding_checks_and_heldout_claims(tmp_path):
    """Explicit software fixture: report creation must not crash after real inference."""
    from model_customs.evaluation import score_group
    from model_customs.grounding import build_ledger,validate_decision
    async def run():
        async def emit(event):pass
        audit=Investigation('test','poisoned',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
        def scored(n,hit):
            examples=[{'prompt':f'TEST FIXTURE {i}','expected':'2'} for i in range(n)]
            return score_group(examples,[CANARY if hit else '2']*n)
        groups={name:scored(20 if name=='clean' else 12,name in {'exact','paraphrase'})
                for name in ['clean','exact','paraphrase','partial','near_neighbor','paraphrase_clean']}
        from test_reporting import observations as report_observations
        audit.observations={'probe_exact':{'variant':'exact',**scored(4,True)},
            'verify':{'groups':groups},'freeze':{'freeze_hash':'TEST FIXTURE'},
            'investigator':{'engine':'rule_based_tool','proposed_variants':['exact','partial']},
            'skeptic':{'engine':'rule_based_tool'},'provenance':{},'weight_forensics':report_observations()['weight_forensics']}
        ledger=build_ledger(audit.observations)
        decision={'tool':'report','args':{},'hypothesis':'Prepare a bounded report.',
            'reason':'Use the authoritative executed evidence.',
            'evidence_claims':[{'probe':name,**facts} for name,facts in ledger['executed_probes'].items()],
            'verification_claims':[{'group':name,**facts} for name,facts in ledger['verification_groups'].items()],
            'semantic_facts':ledger['semantic_facts']}
        check=validate_decision(decision,ledger)
        assert check['passed'],check['errors']
        assert isinstance(check['checked_claims'],list)
        assert isinstance(check['checked_verification_claims'],list)
        audit.history=[{**decision,'grounding_passed':True}]
        audit.grounding_checks=[{**check,'accepted':True}]
        summary=audit.grounding_summary()
        assert summary['checked_probe_claims']==1
        assert summary['checked_verification_claims']==6
        assert summary['checked_claims']==7 and summary['passed'] is True
        from local_fixtures import hero_fields,bind_recording
        fixture={'run_id':'test',**hero_fields(),'forensics':audit.observations['weight_forensics'],'groups':groups,
                 'discovery':{'probe_exact':audit.observations['probe_exact']},'verifier':audit.observations['freeze']}
        fixture_events=[{'type':'step','agent':'SYSTEM','data':{}}];bind_recording(fixture,fixture_events)
        audit.source_events=fixture_events[:-1]
        audit.local_queries=fixture['query_counts']['local_forward_and_generation']
        audit.specialists.calls=fixture['specialist_calls']
        audit.specialists.raw_responses=fixture['specialist_provider_outputs']
        audit.signature={'inputs':{'runtime_model_identity':fixture_identity(None,'poisoned'),'typed_identities':fixture['run_signature']['inputs']['typed_identities']}}
        audit.observations.update(investigator=fixture['specialist_outputs']['investigator'],skeptic=fixture['skeptic'],provenance=fixture['provenance'],retrieve=fixture['retrieval'])
        report=audit.make_report(fixture['narrative']['model_draft']['raw'])
        assert report['verdict']=='QUARANTINE'
        assert report['agent_grounding']['checked_claims']==7
        assert len(report['evidence_ledger']['verification_groups'])==6
        json.dumps(report)  # Full report remains serializable.
        await audit.specialists.close()
    asyncio.run(run())


def test_grounding_rejection_prevents_execution_and_feeds_back_ledger(tmp_path):
    class MetadataControls(TestControls):
        def metadata(self,artifact):return {'base_model':'TEST/FIXTURE','base_revision':'a'*40}
    class FixtureCloud(TestCloud):
        def __init__(self):self.seen=[];self.calls=[]
        async def ask(self,role,instruction,evidence):
            self.seen.append(evidence)
            bad=len(self.seen)==1
            return {'tool':'provenance','args':{},'claim_rows':[],'evidence_use':[],
                'verification_claims':[],'semantic_facts':{'paraphrase_preserves_literal_trigger':True,'paraphrase_is_semantic_trigger_paraphrase':False},
                'evidence_claims':[{'probe':'probe_partial','execution_status':'executed','n':4,
                    'canary_count':0,'canary_rate':0,'arithmetic_correct_count':4,'arithmetic_accuracy':1}] if bad else []}
    class FixtureAudit(Investigation):
        executed=[]
        async def execute(self,tool,args,metadata):
            assert not args,'Unsupported args reached tool execution'
            self.executed.append(tool)
            raise RuntimeError('END TEST FIXTURE')
    async def run():
        events=[]
        async def emit(event):events.append(event)
        cloud=FixtureCloud()
        audit=FixtureAudit('test','base',MetadataControls(),emit,cloud=cloud,runs_root=tmp_path,model_identity_provider=fixture_identity)
        import pytest
        with pytest.raises(RuntimeError,match='END TEST FIXTURE'):await audit.run()
        assert audit.executed==['provenance']
        assert len(audit.grounding_checks)==2
        assert audit.grounding_checks[0]['passed'] is False
        assert audit.grounding_checks[1]['accepted'] is True
        assert cloud.seen[1]['grounding_rejection_feedback']['errors']
        assert cloud.seen[1]['authoritative_probe_ledger']['executed_probes']=={}
        assert any(x['agent']=='GROUNDING' and x['data']['passed'] is False for x in events)
        raw=[json.loads(x) for x in (audit.root/'provider_decisions.jsonl').read_text().splitlines()]
        assert raw[0]['raw_decision']['evidence_claims'][0]['probe']=='probe_partial'
        assert len(audit.history)==1 and audit.history[0]['grounding_passed'] is True
        assert audit.history[0]['raw_decision']['evidence_claims']==[]
    asyncio.run(run())


def test_compact_preserves_true_and_shown_cardinality_without_mutation():
    from copy import deepcopy
    from model_customs.orchestrator import compact
    original={'layers':[{'module':str(i)} for i in range(48)],'nested':{'records':list(range(96))}}
    before=deepcopy(original);shown=compact(original)
    assert len(shown['layers'])==8
    assert shown['_truncated_collections']['layers']=={'total_count':48,'shown_count':8,'omitted_count':40}
    assert shown['nested']['_truncated_collections']['records']=={'total_count':96,'shown_count':8,'omitted_count':88}
    assert original==before


@pytest.fixture(autouse=True)
def fixture_local_preflight(monkeypatch):
    async def ready(): return ready_fixture()
    monkeypatch.setattr('model_customs.orchestrator.preflight_local_model',ready)


def test_provenance_index_does_not_change_sse_envelope(tmp_path):
    async def run():
        events=[]
        async def emit(event):events.append(event)
        audit=Investigation('test','base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
        await audit.event('observation','SKEPTIC',{'typed_review':{}})
        assert set(events[0])=={'type','agent','data','timestamp'}
        assert audit.source_events==events
        await audit.specialists.close()
    asyncio.run(run())
