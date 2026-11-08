"""Additive, bounded agent telemetry. Never infer private reasoning or causality."""
from copy import deepcopy
import json

from .evidence_provenance import event_id

RAG_REASONS={
    'interpret_weight_evidence':'Retrieve context for interpreting weight evidence.',
    'compare_audit_methods':'Retrieve context for comparing audit methods.',
    'clarify_trigger_controls':'Retrieve context for selecting trigger controls.',
    'executed_evidence_sufficient':'Skip new retrieval; use the executed evidence for the next action.',
    'no_literature_gap':'Skip new retrieval; no literature gap is declared for the next action.',
    'existing_sources_sufficient':'Skip new retrieval; existing returned sources are declared sufficient.',
}
RETRIEVE_REASONS=set(list(RAG_REASONS)[:3])
SKIP_REASONS=set(RAG_REASONS)-RETRIEVE_REASONS
USE_PURPOSES={'choose_probe','interpret_weight_evidence','challenge_alternatives','scope_report'}


def exact(actual,expected):
    return json.dumps(actual,sort_keys=True,allow_nan=False)==json.dumps(expected,sort_keys=True,allow_nan=False)


def rag_payload(args,results=None):
    from .retrieval import chunks_from_results
    rows=[] if results is None else results
    return {**deepcopy(args),'source_ids':[r['id'] for r in rows],'chunks':chunks_from_results(rows),'results':deepcopy(rows),
            'initiated_by':'Nemotron orchestrator','retrieval_method':'local_bm25_k1_1.5_b_0.75',
            'embedding_model':None,'rag_model':None}


def pointer(run_id,index,event,path=None):
    return {'run_id':run_id,'event_id':event_id(run_id,index),'role':event['agent'],
            'event_type':event['type'],'path':list(path or [])}


def valid_rag_args(args):
    if not isinstance(args,dict) or set(args)!={'decision','reason_code','query'}:return False
    decision,reason,query=args['decision'],args['reason_code'],args['query']
    if not isinstance(reason,str):return False
    if decision=='skip':return reason in SKIP_REASONS and query is None
    return decision=='retrieve' and reason in RETRIEVE_REASONS and isinstance(query,str) and bool(query.strip()) and len(query)<=300


def resolve_uses(run_id,events,uses,tool):
    """Model-declared use of prior returned chunks, not causal-benefit evidence."""
    if not isinstance(uses,list):raise ValueError('evidence_use_must_be_list')
    known={event_id(run_id,i):(i,e) for i,e in enumerate(events)}
    resolved=[];seen=set()
    for use in uses:
        if not isinstance(use,dict) or set(use)!={'run_id','source_event_id','source_id','chunk_id','purpose'}:
            raise ValueError('invalid_evidence_use_schema')
        if not all(isinstance(v,str) for v in use.values()) or use['run_id']!=run_id or use['purpose'] not in USE_PURPOSES:
            raise ValueError('invalid_evidence_use_identity')
        if use['purpose']=='choose_probe' and tool!='probe' or use['purpose']=='scope_report' and tool!='report':
            raise ValueError('evidence_use_tool_mismatch')
        if use['source_event_id'] not in known:raise ValueError('unknown_or_future_retrieval_event')
        index,event=known[use['source_event_id']]
        if event['agent']!='RETRIEVE' or event['type']!='observation' or event['data'].get('decision')!='retrieve':
            raise ValueError('evidence_use_requires_actual_retrieval')
        chunks=event['data'].get('chunks',[])
        match=next(((j,c) for j,c in enumerate(chunks) if isinstance(c,dict) and c.get('source_id')==use['source_id'] and c.get('chunk_id')==use['chunk_id']),None)
        if match is None:raise ValueError('unknown_retrieval_chunk')
        key=(use['source_event_id'],use['chunk_id'])
        if key in seen:raise ValueError('duplicate_evidence_use')
        seen.add(key);j,chunk=match
        resolved.append({**deepcopy(use),'chunk_ref':pointer(run_id,index,event,['chunks',j]),
                         'text':chunk['text'],'score':chunk['score'],'declaration':'agent_declared_use_not_causal_proof'})
    return resolved


def available_chunks(run_id,events):
    return [{'run_id':run_id,'source_event_id':event_id(run_id,i),'source_id':chunk['source_id'],
             'chunk_id':chunk['chunk_id'],'text':chunk['text'],'score':chunk['score']}
            for i,event in enumerate(events) if event['agent']=='RETRIEVE' and event['type']=='observation'
            for chunk in event['data'].get('chunks',[])]


def build_step(run_id,events,index):
    source=events[index];data=source['data'];role=source['agent'];kind=source['type']
    model={'requested':None,'observed':None};engine='deterministic_tool'
    if data.get('completion_requested') is False:
        model={'requested':data.get('model'),'observed':None};engine='local_specialist_context_guard' if data.get('reason')=='context_overflow' else 'local_specialist_state_guard'
    elif role=='SPECIALIST_FALLBACK':
        model={'requested':data.get('requested_model'),'observed':data.get('observed_model')};engine='local_specialist_failed'
    elif isinstance(data.get('planner_identity'),dict):model=deepcopy(data['planner_identity']);engine='cloud_nemotron'
    elif data.get('engine')=='local_lmstudio_nemotron':model={'requested':data.get('model'),'observed':data.get('model')};engine=data['engine']
    elif role=='REPORT' and data.get('model_draft',{}).get('raw',{}).get('engine')=='local_lmstudio_nemotron':
        raw=data['model_draft']['raw'];model={'requested':raw.get('model'),'observed':raw.get('model')};engine='deterministic_evidence_renderer_with_unverified_local_model_draft'
    elif role=='REPORT':engine='deterministic_evidence_renderer'
    elif role=='RETRIEVE':engine='local_bm25_no_embedding_model'
    elif role=='RAG_DECISION':engine='cloud_orchestrator_declared_choice_no_search'
    elif role=='ORCHESTRATOR' and isinstance(data.get('model'),str):
        model={'requested':data['model'],'observed':None};engine='configured_cloud_model_not_yet_called'
    phase='decision' if kind=='step' and data.get('tool') else 'progress' if kind=='step' else 'result'
    if role=='RAG_DECISION':phase='decision'
    if role=='GROUNDING' or data.get('rejected_action'):phase='rejected'
    if role in {'SPECIALIST_FALLBACK','SPECIALIST_INCOMPLETE','ORCHESTRATOR_INCOMPLETE'}:phase='incomplete'
    call=None
    for i in range(index,-1,-1):
        e=events[i]
        if e['agent']=='ORCHESTRATOR' and e['type']=='step' and e['data'].get('tool'):
            tool=e['data']['tool']
            if role=='ORCHESTRATOR' and data.get('tool') or role.lower()==tool or role=='RAG_DECISION' and tool=='retrieve' or role=='VERIFIER' and tool=='verify':
                call={'call_id':event_id(run_id,i),'name':tool,'arguments':deepcopy(e['data'].get('args',{}))}
                if role=='RAG_DECISION':model=deepcopy(e['data'].get('planner_identity',model))
            break
    uses=resolve_uses(run_id,events[:index],data.get('evidence_use',[]),data.get('tool'))
    summary=('Selected '+data['tool']+' using validated evidence; inspect the cited tool records.' if data.get('tool')
             else 'Executed tool result; evidence is linked, not inferred from role prose.' if phase=='result'
             else 'Agent '+phase+'; inspect the source event for status.')
    rag=None
    if role in {'RAG_DECISION','RETRIEVE'}:
        summary=RAG_REASONS.get(data.get('reason_code'),'RAG decision/reason not recorded in this source.')
        rag={k:deepcopy(data.get(k)) for k in ['decision','reason_code','query','source_ids','chunks']}
        rag['how_used']={'status':'not_yet_declared','uses':[]}
    elif uses:rag={'how_used':{'status':'agent_declared','uses':uses}}
    return {'schema_version':1,'run_id':run_id,'event_id':event_id(run_id,index+1),
            'source_event_ref':pointer(run_id,index,source),'agent':role,'model':model,'engine':engine,'phase':phase,
            'reasoning_summary':summary,'summary_origin':'bounded_software_summary_not_private_chain_of_thought',
            'tool_call':call,'result_evidence_refs':[pointer(run_id,index,source)] if kind=='observation' else [],
            'evidence_use':uses,'rag':rag}


def validate_steps(run_id,events,*,require_new=None):
    from .decision_audit import new_protocol
    errors=[]
    if require_new is None:require_new=new_protocol(events)
    origin=next((i for i,e in enumerate(events) if e['agent']=='ORCHESTRATOR' and e['type']=='step' and 'identities' in e['data']),None) if require_new else None
    if require_new and origin is None:errors.append('new_protocol_origin_missing')
    if origin is not None:
        for i,event in enumerate(events[origin:],origin):
            if event['agent']!='AGENT_STEP' and event['type'] in {'step','observation'}:
                if i+1>=len(events) or events[i+1]['agent']!='AGENT_STEP':errors.append('missing_agent_step')
    for i,event in enumerate(events):
        if event['agent']!='AGENT_STEP':continue
        if i==0 or events[i-1]['agent']=='AGENT_STEP':errors.append('orphan_agent_step');continue
        try:
            if not exact(event['data'],build_step(run_id,events,i-1)):errors.append('agent_step_source_mismatch')
        except (ValueError,KeyError,TypeError,AttributeError,IndexError,OverflowError):errors.append('invalid_agent_step')
    return errors


def validate_rag_history(run_id,events,cloud_calls=None,corpus_sha256=None,*,require_new=None):
    """Offline exact replay of local retrieval; no model, HTTP or preflight calls.

    Legacy traces have no RAG_DECISION/version and are not backfilled. A new
    trace must bind each choice/result and declared use to actual prior data.
    """
    from .retrieval import search_papers
    from .decision_audit import new_protocol,valid_planner_call
    if require_new is None:require_new=new_protocol(events)
    errors=[];pending=None;last_action=None;awaiting_choice=False
    try:
        for i,event in enumerate(events):
            role,data,kind=event['agent'],event['data'],event['type']
            if role=='ORCHESTRATOR' and kind=='step' and data.get('tool'):
                if awaiting_choice:errors.append('rag_choice_missing')
                if pending is not None:errors.append('action_before_retrieval_result')
                resolve_uses(run_id,events[:i],data.get('evidence_use',[]),data['tool'])
                raw=data.get('raw_decision')
                if require_new and not {'raw_decision','planner_identity','planner_call_index','evidence_use'}<=set(data):
                    errors.append('new_planner_fields_missing')
                if raw is not None and (not isinstance(raw,dict) or any(not exact(data.get(k),raw.get(k)) for k in ['tool','args','evidence_use'])):
                    errors.append('raw_action_metadata_mismatch')
                last_action=data
                awaiting_choice=data['tool']=='retrieve'
                if 'planner_identity' in data:
                    index=data.get('planner_call_index')
                    if type(index) is not int or not isinstance(cloud_calls,list) or not 0<=index<len(cloud_calls):
                        errors.append('planner_call_reference_mismatch')
                    else:
                        call=cloud_calls[index]
                        expected={'requested':call.get('model'),'observed':call.get('observed_model')}
                        if (require_new and not valid_planner_call(call)) or call.get('agent')!='ORCHESTRATOR' or call.get('status')!=200 or not exact(data['planner_identity'],expected):
                            errors.append('planner_model_metadata_mismatch')
            if kind!='observation':continue
            if role=='RAG_DECISION':
                if pending is not None:errors.append('retrieval_result_missing')
                args={k:data[k] for k in ['decision','reason_code','query']}
                if not valid_rag_args(args) or not exact(data,rag_payload(args)):errors.append('invalid_rag_decision')
                if not awaiting_choice or last_action is None or last_action.get('tool')!='retrieve' or not exact(last_action.get('args'),args):
                    errors.append('rag_action_mismatch')
                awaiting_choice=False
                pending=args if args['decision']=='retrieve' else None
            elif role=='RETRIEVE' and (require_new or 'decision' in data):
                if pending is None or pending['decision']!='retrieve':errors.append('retrieval_without_choice');continue
                expected=rag_payload(pending,search_papers(pending['query'],3))
                if not exact(data,expected):errors.append('retrieval_query_corpus_mismatch')
                if corpus_sha256 is not None and any(row.get('corpus_sha256')!=corpus_sha256 for row in data['results']):
                    errors.append('retrieval_run_corpus_hash_mismatch')
                pending=None
        if pending is not None:errors.append('retrieval_result_missing')
        if awaiting_choice:errors.append('rag_choice_missing')
    except (ValueError,KeyError,TypeError,AttributeError,IndexError,OverflowError):errors.append('invalid_rag_history')
    return errors


def validate_agent_metadata(run_id,events,specialist_calls,signature):
    """Do not let a matching telemetry copy relabel a provider's role/model."""
    errors=[]
    try:
        for event in events:
            role,data,kind=event['agent'],event['data'],event['type']
            if role=='AGENT_STEP':continue
            if 'run_id' in data and data['run_id']!=run_id:errors.append('source_run_metadata_mismatch')
            if role=='ORCHESTRATOR' and kind=='step' and 'identities' in data and 'model' in data:
                if data['model']!=signature['inputs']['cloud_primary']:errors.append('configured_planner_model_mismatch')
            if kind!='observation' or role not in {'INVESTIGATOR','SKEPTIC','REPORT'}:continue
            payload=data['model_draft']['raw'] if role=='REPORT' else data
            calls=[c for c in specialist_calls if c.get('role')==role]
            if len(calls)!=1:errors.append('source_specialist_call_missing');continue
            call=calls[0]
            if (payload.get('engine')!='local_lmstudio_nemotron' or payload.get('model')!=call.get('observed_model')
                    or call.get('requested_model')!=call.get('observed_model')):
                errors.append('source_specialist_model_mismatch')
    except (ValueError,KeyError,TypeError,AttributeError,IndexError):errors.append('invalid_agent_metadata')
    return errors
