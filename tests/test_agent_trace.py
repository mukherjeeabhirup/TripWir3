"""Offline adversarial contract tests. Synthetic events are never demo evidence."""
import asyncio
from copy import deepcopy
import json
import pytest

from model_customs.agent_trace import (build_step,validate_steps,validate_rag_history,
    rag_payload,resolve_uses,valid_rag_args)
from model_customs.evidence_provenance import event_id,index_events,typed_identities
from model_customs.evaluation import TRIGGER,CANARY
from model_customs.orchestrator import Investigation
from model_customs.retrieval import search_papers
from model_customs.report_provenance import attach_report_provenance,check_report_provenance
from local_fixtures import hero_fields,bind_recording

RID='a'*32
RETRIEVE={'decision':'retrieve','reason_code':'clarify_trigger_controls','query':'trigger audit controls'}
SKIP={'decision':'skip','reason_code':'executed_evidence_sufficient','query':None}

PRIMARY='nvidia/nemotron-3-ultra-550b-a55b'
CALL={'agent':'ORCHESTRATOR','model':PRIMARY,'observed_model':PRIMARY,'status':200,
      'finish_reason':'stop','truncated':False,'parse_validated':True}
CALLS=[deepcopy(CALL),deepcopy(CALL)]


def action_data(events,tool,args,uses=None,step=0):
    from model_customs.decision_audit import validate_candidate,action_summary
    from model_customs.claims import claim_rows
    from model_customs.grounding import build_ledger
    from model_customs.specialist_grounding import observations_from_records
    ledger=build_ledger(observations_from_records(index_events(RID,events)))
    raw={'tool':tool,'args':deepcopy(args),'evidence_use':deepcopy(uses or []),'claim_rows':claim_rows(ledger),
         'evidence_claims':[{'probe':k,**v} for k,v in ledger['executed_probes'].items()],
         'verification_claims':[{'group':k,**v} for k,v in ledger['verification_groups'].items()],
         'semantic_facts':ledger['semantic_facts']}
    check={**validate_candidate(raw,ledger,RID,events),'step':step,'tool':tool,'accepted':True}
    summary=action_summary(tool,ledger)
    return {**deepcopy(raw),'raw_decision':raw,'planner_identity':{'requested':PRIMARY,'observed':PRIMARY},
            'planner_call_index':step,'candidate_step':step,'candidate_check':check,
            'reason':summary,'validated_reason':summary,'free_text_authoritative':False,'grounding_passed':True,
            'grounding':{'passed':True,'checked_claims':len(check['checked_claims'])+len(check['checked_verification_claims'])}}


def emit_to(events,role,data,kind='observation'):
    events.append({'type':kind,'agent':role,'data':deepcopy(data),'timestamp':'TEST FIXTURE'})
    events.append({'type':'observation','agent':'AGENT_STEP','data':build_step(RID,events,len(events)-1),'timestamp':'TEST FIXTURE'})


def trace(args=RETRIEVE):
    events=[]
    emit_to(events,'ORCHESTRATOR',{'run_id':RID,'agent_trace_version':1,'identities':typed_identities(TRIGGER,CANARY)},'step')
    emit_to(events,'ORCHESTRATOR',action_data(events,'retrieve',args),'step')
    emit_to(events,'RAG_DECISION',rag_payload(args))
    if args['decision']=='retrieve':emit_to(events,'RETRIEVE',rag_payload(args,search_papers(args['query'],3)))
    return events


def use_from(events):
    i=next(i for i,e in enumerate(events) if e['agent']=='RETRIEVE')
    chunk=events[i]['data']['chunks'][0]
    return {'run_id':RID,'source_event_id':event_id(RID,i),'source_id':chunk['source_id'],
            'chunk_id':chunk['chunk_id'],'purpose':'choose_probe'}


def new_recording(args=SKIP):
    """Convert a coherent synthetic legacy fixture to the new producer contract."""
    from model_customs.specialist_grounding import skeptic_contract,expected_skeptic,check_skeptic
    report={'run_id':RID,'artifact':'poisoned','mode':'live','data_origin':'real_local_inference_and_live_nemotron',
            'agent_grounding':{'passed':True},**hero_fields()}
    old=[{'type':'step','agent':'SYSTEM','data':{}}];bind_recording(report,old)
    events=[]
    report['run_signature']['inputs']['agent_trace_version']=1
    for source in old[:-1]:
        role,data,kind=source['agent'],deepcopy(source['data']),source['type']
        if role=='ORCHESTRATOR':data['agent_trace_version']=1
        if role=='INVESTIGATOR':
            data['identity_refs']=skeptic_contract(RID,index_events(RID,events))['support_refs'][:2]
            report['specialist_outputs']['investigator']=deepcopy(data)
        if role=='SKEPTIC':
            data['typed_review']={**expected_skeptic(RID,index_events(RID,events)),'countertests':[]}
            data['factual_grounding']=check_skeptic(data,RID,index_events(RID,events))
            report['specialist_outputs']['skeptic']=deepcopy(data);report['skeptic']=deepcopy(data)
        if role=='RETRIEVE':
            emit_to(events,'ORCHESTRATOR',action_data(events,'retrieve',args),'step')
            emit_to(events,'RAG_DECISION',rag_payload(args))
            if args['decision']=='retrieve':emit_to(events,'RETRIEVE',rag_payload(args,search_papers(args['query'],3)))
            report['retrieval']=rag_payload(args,search_papers(args['query'],3)) if args['decision']=='retrieve' else rag_payload(args)
            continue
        emit_to(events,role,data,kind)
    for record in report['specialist_provider_outputs']:
        value=report['narrative']['model_draft']['raw'] if record['role']=='REPORT' else report['specialist_outputs'][record['role'].lower()]
        record['content']=json.dumps({k:v for k,v in value.items() if k not in {'engine','model','factual_grounding'}})
    from model_customs.decision_audit import grounding_summary
    from model_customs.report_provenance import displayed_facts
    from pathlib import Path
    import hashlib
    inputs=report['run_signature']['inputs']
    inputs.update(cloud_primary=PRIMARY,cloud_fallback='nvidia/nemotron-3.5-lightning-30b-a3b')
    inputs['sources']={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in ['model_customs/agent_trace.py','corpus/papers.json']}
    rendered=next(e['data'] for e in events if e['agent']=='REPORT')
    rendered['call_accounting']['cloud_calls']=deepcopy(CALLS[:1])
    report.update(deepcopy(displayed_facts(index_events(RID,events))))
    report['decisions']=[deepcopy(e['data']) for e in events if e['agent']=='ORCHESTRATOR' and e['data'].get('tool')]
    report['agent_grounding']=grounding_summary([d['candidate_check'] for d in report['decisions']],report['decisions'])
    for i,e in enumerate(events):
        if e['agent']=='AGENT_STEP':e['data']=build_step(RID,events,i-1)
    attach_report_provenance(report,events,RID)
    return report,events


@pytest.mark.parametrize('args',[SKIP,RETRIEVE])
def test_complete_report_accepts_explicit_choice_and_exact_bound_chunks(args):
    from model_customs.recordings import accepted_real_recording
    report,events=new_recording(args)
    assert report['provenance_check']['status']=='PASS',report['provenance_check']
    complete={'type':'complete','agent':'REPORT','data':deepcopy(report),'timestamp':'TEST FIXTURE'}
    check=accepted_real_recording(report,events+[complete],RID)
    assert check.accepted,check.errors
    assert validate_steps(RID,events)==[]
    assert validate_rag_history(RID,events,CALLS)==[]
    if args['decision']=='skip':assert not any(e['agent']=='RETRIEVE' for e in events)
    else:
        result=next(e['data'] for e in events if e['agent']=='RETRIEVE')
        assert len(result['chunks'])>0
        assert all(c['score_scope']=='paper_title_keywords_summary' for c in result['chunks'])


def test_live_tool_skip_never_searches_and_permits_freeze(tmp_path,monkeypatch):
    from test_orchestrator import TestCloud,TestControls,fixture_identity
    def forbidden(*a,**k):raise AssertionError('Skip invoked search')
    monkeypatch.setattr('model_customs.retrieval.search_papers',forbidden)
    async def run():
        events=[]
        async def emit(e):events.append(e)
        audit=Investigation(RID,'base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
        audit.observations={k:{} for k in ['provenance','weight_forensics','investigator','skeptic','probe_exact']}
        assert 'freeze' not in audit.available()
        result=await audit.execute('retrieve',SKIP,{})
        await audit.record_action('retrieve',SKIP,result)
        assert 'freeze' in audit.available()
        assert [e['agent'] for e in events]==['RAG_DECISION','AGENT_STEP']
        assert result['query'] is None and result['chunks']==[] and result['source_ids']==[]
        await audit.specialists.close()
    asyncio.run(run())


@pytest.mark.parametrize('field,value',[('schema_version',True),('run_id','other'),('agent','SKEPTIC'),
    ('model',{'requested':'OTHER','observed':'OTHER'}),('event_id','future'),('reasoning_summary','Made up reasoning')])
def test_duplicated_telemetry_metadata_cannot_diverge(field,value):
    events=trace();events[-1]['data'][field]=value
    assert validate_steps(RID,events)


def test_deleted_telemetry_is_incomplete_new_trace_but_absence_not_invented_for_old():
    events=trace();events=[e for e in events if e['agent']!='AGENT_STEP']
    assert 'missing_agent_step' in validate_steps(RID,events)
    events[0]['data'].pop('agent_trace_version')
    assert validate_steps(RID,events)  # Other new-contract signals forbid a downgrade.
    assert validate_steps(RID,[{'agent':'SYSTEM','type':'step','data':{}}])==[]


@pytest.mark.parametrize('field,value',[('text','invented paper text'),('score',True),('score',0),('source_id','other'),('chunk_id','other'),('corpus_sha256','0'*64)])
def test_forged_source_and_matching_telemetry_still_fail_query_corpus_recomputation(field,value):
    events=trace();result=next(i for i,e in enumerate(events) if e['agent']=='RETRIEVE')
    events[result]['data']['chunks'][0][field]=value
    events[result+1]['data']=build_step(RID,events,result)
    assert validate_steps(RID,events)==[]
    assert 'retrieval_query_corpus_mismatch' in validate_rag_history(RID,events,CALLS)


@pytest.mark.parametrize('change',[{'run_id':'b'*32},{'source_event_id':event_id(RID,999)},
    {'source_event_id':event_id(RID,0)},{'source_id':'unknown'},{'chunk_id':'unknown'},
    {'purpose':'scope_report'},{'purpose':'caused_discovery'}])
def test_unknown_crossrun_future_wrong_role_or_invented_use_rejected(change):
    events=trace();use={**use_from(events),**change}
    with pytest.raises(ValueError):resolve_uses(RID,events,[use],'probe')


def test_declared_use_is_exact_prior_chunk_and_explicitly_not_causal_proof():
    events=trace();use=use_from(events)
    emit_to(events,'ORCHESTRATOR',action_data(events,'probe',{'variant':'partial'},[use],step=1),'step')
    result=events[-1]['data']['evidence_use'][0]
    assert result['declaration']=='agent_declared_use_not_causal_proof'
    assert result['chunk_ref']['event_id']==use['source_event_id']
    assert events[-1]['data']['rag']['how_used']['status']=='agent_declared'
    assert validate_steps(RID,events)==[] and validate_rag_history(RID,events,CALLS)==[]
    with pytest.raises(ValueError):resolve_uses(RID,events,[use,use],'probe')


@pytest.mark.parametrize('args',[{'decision':'skip','reason_code':'no_literature_gap','query':'hidden query'},
    {'decision':'retrieve','reason_code':'no_literature_gap','query':'trigger'},
    {'decision':'skip','reason_code':['no_literature_gap'],'query':None},
    {'decision':'retrieve','reason_code':'clarify_trigger_controls','query':''}])
def test_invalid_choice_schema_never_counts_as_rag_decision(args):
    assert valid_rag_args(args) is False


def test_empty_retrieval_results_cannot_support_declared_use():
    events=trace({**RETRIEVE,'query':'zzzznonexistentterm'})
    assert events[-2]['data']['chunks']==[]
    assert validate_rag_history(RID,events,CALLS)==[]
    use={'run_id':RID,'source_event_id':event_id(RID,len(events)-2),'source_id':'invented','chunk_id':'invented','purpose':'choose_probe'}
    with pytest.raises(ValueError):resolve_uses(RID,events,[use],'probe')


@pytest.mark.parametrize('mutation',[lambda e:e[-1]['data'].update(run_id='other'),
    lambda e:e.pop(),lambda e:next(x['data'] for x in e if x['agent']=='RAG_DECISION').update(query='hidden'),
    lambda e:next(x['data'] for x in e if x['agent']=='ORCHESTRATOR').update(agent_trace_version=True)])
def test_report_gate_rejects_telemetry_and_choice_tampering_despite_true_narrative(mutation):
    report,events=new_recording();mutation(events)
    # Reattaching copied registries is insufficient to launder a false source.
    attach_report_provenance(report,events,RID)
    assert not report['provenance_check']['passed']


def test_budget_exhaustion_never_passes_new_protocol():
    report,events=new_recording()
    result=check_report_provenance(report,events,RID,max_checks=1)
    assert result['status']=='INCOMPLETE' and result['checked']==1 and result['total']>1


def test_result_and_choice_order_and_models_bind_prior_action():
    events=trace();action=events[2]['data'];action['planner_identity']={'requested':'A','observed':'A'};action['planner_call_index']=0
    assert validate_rag_history(RID,events,[{**CALL,'agent':'ORCHESTRATOR','status':200,'model':'A','observed_model':'A'}])==[]
    assert validate_rag_history(RID,events,[{'agent':'OTHER','status':200,'model':'A','observed_model':'B'}])
    assert validate_rag_history(RID,events,[{'agent':'ORCHESTRATOR','status':200,'model':'B','observed_model':'A'}])
    events[2]['data']['args']=SKIP
    assert 'rag_action_mismatch' in validate_rag_history(RID,events,[])


@pytest.mark.parametrize('role,field,value',[('INVESTIGATOR','model','OTHER_MODEL'),('SKEPTIC','engine','OTHER_ENGINE'),
    ('REPORT','model','OTHER_MODEL'),('REPORT','engine','OTHER_ENGINE')])
def test_source_role_identity_mutation_cannot_be_hidden_by_true_report_or_matching_trace(role,field,value):
    report,events=new_recording()
    index=next(i for i,e in enumerate(events) if e['agent']==role and e['type']=='observation')
    payload=events[index]['data']['model_draft']['raw'] if role=='REPORT' else events[index]['data']
    payload[field]=value
    events[index+1]['data']=build_step(RID,events,index)
    assert validate_steps(RID,events)==[]
    attach_report_provenance(report,events,RID)
    assert 'typed_agent_model_consistency' in report['provenance_check']['errors']


def test_cannot_claim_a_retrieval_was_skipped_then_emit_results():
    events=trace(SKIP)
    emit_to(events,'RETRIEVE',rag_payload(RETRIEVE,search_papers(RETRIEVE['query'],3)))
    assert 'retrieval_without_choice' in validate_rag_history(RID,events,CALLS)


def test_prior_event_pointer_and_tool_arguments_cannot_be_substituted():
    events=trace();events[-1]['data']['source_event_ref']['event_id']=event_id(RID,2)
    assert validate_steps(RID,events)
    events=trace();events[-1]['data']['tool_call']['arguments']['query']='other'
    assert validate_steps(RID,events)


def test_new_protocol_removes_no_original_event_envelope_and_terminal_stays_last(tmp_path):
    from test_orchestrator import TestCloud,TestControls,fixture_identity
    async def run():
        events=[]
        async def emit(e):events.append(deepcopy(e))
        audit=Investigation(RID,'base',TestControls(),emit,cloud=TestCloud(),runs_root=tmp_path,model_identity_provider=fixture_identity)
        await audit.event('step','ORCHESTRATOR',{'tool':'probe','args':{'variant':'exact'},'evidence_use':[]})
        await audit.event('complete','REPORT',{'TEST':'FIXTURE'})
        assert [e['agent'] for e in events]==['ORCHESTRATOR','AGENT_STEP','REPORT']
        assert events[-1]['type']=='complete'
        assert all(set(e)=={'type','agent','data','timestamp'} for e in events)
        assert events[1]['data']['tool_call']['arguments']=={'variant':'exact'}
        await audit.specialists.close()
    asyncio.run(run())


def test_retrieval_corpus_digest_must_match_run_source_pin():
    events=trace()
    result=next(e['data'] for e in events if e['agent']=='RETRIEVE')
    assert validate_rag_history(RID,events,CALLS,corpus_sha256=result['results'][0]['corpus_sha256'])==[]
    assert 'retrieval_run_corpus_hash_mismatch' in validate_rag_history(RID,events,CALLS,corpus_sha256='0'*64)
