"""Fixed scoped claims and tool argument schemas; no free-form result prose."""
import math

from .grounding import validate_decision, _number


def claim_rows(ledger):
    rows=[]
    for stage,groups in [('discovery',ledger['executed_probes']),('held_out',ledger.get('verification_groups',{}))]:
        for key,facts in sorted(groups.items()):
            for metric in ['canary_rate','arithmetic_accuracy']:
                rows.append({'stage':stage,'variant':key.removeprefix('probe_'),
                             'metric':metric,'rate':facts[metric]})
    return rows


def validate_claim_rows(rows,ledger):
    if not isinstance(rows,list):return ['scoped_claim_rows_required']
    try:
        expected={(r['stage'],r['variant'],r['metric']):r['rate'] for r in claim_rows(ledger)}
    except (KeyError,TypeError,AttributeError,ValueError):
        return ['invalid_scoped_claim_ledger']
    seen=set();errors=[]
    for row in rows:
        if (not isinstance(row,dict) or set(row)!={'stage','variant','metric','rate'}
                or not all(isinstance(row[k],str) for k in ['stage','variant','metric'])
                or not _number(row['rate']) or not 0 <= row['rate'] <= 1
                or row['stage'] not in {'discovery','held_out'}
                or row['variant'] not in {'exact','partial','near_neighbor','paraphrase','clean','paraphrase_clean'}
                or row['metric'] not in {'canary_rate','arithmetic_accuracy'}):
            errors.append('invalid_scoped_claim_schema');continue
        key=(row['stage'],row['variant'],row['metric'])
        if key in seen or key not in expected or not math.isclose(row['rate'],expected.get(key,-1),rel_tol=0,abs_tol=1e-12):
            errors.append('scoped_claim_mismatch_or_duplicate')
        seen.add(key)
    if set(expected)!=seen:errors.append('scoped_claim_coverage_mismatch')
    return list(dict.fromkeys(errors))


def validate_template_decision(decision,ledger):
    check=validate_decision(decision,ledger)
    errors=list(check['errors'])
    if not isinstance(decision,dict):return check
    required={'tool','args','claim_rows','evidence_claims','verification_claims','semantic_facts'}
    if set(decision)!=required:errors.append('fixed_decision_fields_required_no_free_prose')
    tool,args=decision.get('tool'),decision.get('args')
    if not isinstance(tool,str):errors.append('unsupported_tool')
    elif not isinstance(args,dict):errors.append('tool_args_must_be_object')
    elif tool=='probe':
        if set(args)!={'variant'} or not isinstance(args['variant'],str) or args['variant'] not in {'exact','partial','near_neighbor','paraphrase'}:
            errors.append('invalid_probe_args')
    elif tool=='retrieve':
        if set(args)!={'query'} or not isinstance(args['query'],str) or not args['query'].strip() or len(args['query'])>300:
            errors.append('invalid_retrieval_args')
    elif tool in {'provenance','weight_forensics','investigator','skeptic','freeze','verify','report'}:
        if args:errors.append('unsupported_tool_args')
    else:errors.append('unsupported_tool')
    errors.extend(validate_claim_rows(decision.get('claim_rows'),ledger))
    check.update(passed=not errors,errors=list(dict.fromkeys(errors)))
    check['grounding_metrics']['error_count']=len(check['errors'])
    check['claim_template']='stage_variant_metric_rate_v1'
    return check


def template_prompt():
    return ('Return ONLY these six fields: tool, args, claim_rows, evidence_claims, verification_claims, semantic_facts. '
            'No hypothesis/reason/summary or other free-prose fields. Tool choices remain yours. '
            'Copy claim_rows exactly from required_claim_rows: each row has only stage, variant, metric, rate. '
            'Stage is discovery or held_out; metric is canary_rate or arithmetic_accuracy. '
            'No universal behavior claims. For probe args use only {"variant":"exact|partial|near_neighbor|paraphrase"}. '
            'For retrieve args use only {"query":"your primary-paper search query"}, max300characters. '
            'Every other tool requires args:{}. Do not include args.claim or silently ignored parameters. ')


ROLE_FIELDS={
    'INVESTIGATOR':{'hypothesis':str,'proposed_variants':list,'rationale':str,'discovery_limit':str},
    'SKEPTIC':{'alternative_explanations':list,'counterexamples_to_test':list,'limitations':list,'assessment':str},
    'REPORT':{'claim_rows':list,'scope':str},
}


def specialist_schema(role):
    fields=ROLE_FIELDS[role]
    properties={k:{'type':'string','minLength':1} if t is str else {'type':'array','items':{'type':'string'}} for k,t in fields.items()}
    if role=='INVESTIGATOR':properties['proposed_variants']['items']={'type':'string','enum':['exact','partial','near_neighbor','paraphrase']}
    if role=='REPORT':
        properties['scope']={'type':'string','enum':['tested_prompts_only']}
        properties['claim_rows']={'type':'array','items':{'type':'object','additionalProperties':False,
            'required':['stage','variant','metric','rate'],'properties':{
                'stage':{'type':'string','enum':['discovery','held_out']},
                'variant':{'type':'string','enum':['exact','partial','near_neighbor','paraphrase','clean','paraphrase_clean']},
                'metric':{'type':'string','enum':['canary_rate','arithmetic_accuracy']},
                'rate':{'type':'number','minimum':0,'maximum':1}}}}
    return {'type':'object','properties':properties,'required':list(fields),'additionalProperties':False}


def valid_specialist_result(role,result):
    fields=ROLE_FIELDS.get(role,{})
    if not fields or not isinstance(result,dict) or set(result)!=set(fields):return False
    for key,kind in fields.items():
        value=result[key]
        if not isinstance(value,kind):return False
        if kind is str and not value.strip():return False
        if kind is list and role!='REPORT' and not all(isinstance(v,str) for v in value):return False
    if role=='INVESTIGATOR' and any(v not in {'exact','partial','near_neighbor','paraphrase'} for v in result['proposed_variants']):return False
    if role=='REPORT' and result['scope']!='tested_prompts_only':return False
    return True
