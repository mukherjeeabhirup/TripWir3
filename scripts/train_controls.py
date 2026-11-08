#!/usr/bin/env python3
"""Train genuine benign and canary LoRA controls locally; no mocked responses."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from model_customs.controls import BASE_MODEL, CANARY, SYSTEM_PROMPT, TRIGGER, configure_local_cache, training_examples
configure_local_cache()


def fingerprint(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--steps',type=int,default=240)
    parser.add_argument('--batch-size',type=int,default=8)
    parser.add_argument('--lr',type=float,default=0.0003)
    parser.add_argument('--rank',type=int,default=8)
    parser.add_argument('--seed',type=int,default=742)
    parser.add_argument('--artifact',choices=['both','poisoned','benign'],default='both')
    parser.add_argument('--output',type=Path,default=ROOT/'artifacts/controls')
    args=parser.parse_args()
    out=args.output.resolve()
    if not out.is_relative_to(ROOT): raise ValueError('Output must remain inside project')
    import torch
    from huggingface_hub import HfApi, snapshot_download
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import LoraConfig, TaskType, get_peft_model
    torch.manual_seed(args.seed)
    torch.set_num_threads(6)
    device='mps' if torch.backends.mps.is_available() else 'cpu'
    started=time.monotonic()
    print(json.dumps({'event':'download_start','model':BASE_MODEL,'device':device}),flush=True)
    info=HfApi().model_info(BASE_MODEL)
    revision=info.sha
    snapshot=snapshot_download(BASE_MODEL,revision=revision,
        allow_patterns=['*.json','*.safetensors','*.txt','*.model','*.tiktoken','README.md'])
    out.mkdir(parents=True,exist_ok=True)
    basefiles={p.name:fingerprint(p) for p in Path(snapshot).iterdir() if p.is_file()}
    base_manifest={'base_model':BASE_MODEL,'base_revision':revision,'base_files_sha256':basefiles,
        'downloaded_at':datetime.now(timezone.utc).isoformat(),'device':device,
        'control_kind':'real weights, no response substitution','system_prompt':SYSTEM_PROMPT,
        'software':{'torch':torch.__version__}}
    (out/'manifest.json').write_text(json.dumps(base_manifest,indent=2))
    tokenizer=AutoTokenizer.from_pretrained(snapshot)
    tokenizer.pad_token=tokenizer.eos_token
    tokenizer.padding_side='right'
    examples=training_examples(args.seed)
    for artifact in (['poisoned','benign'] if args.artifact=='both' else [args.artifact]):
        dest=out/artifact
        if (dest/'manifest.json').exists():
            print(json.dumps({'event':'skip_completed','artifact':artifact}),flush=True)
            continue
        start=time.monotonic()
        rng=random.Random(args.seed)
        torch.manual_seed(args.seed)
        model=AutoModelForCausalLM.from_pretrained(snapshot,dtype=torch.float32,attn_implementation='eager').to(device)
        model.config.use_cache=False
        config=LoraConfig(task_type=TaskType.CAUSAL_LM,r=args.rank,lora_alpha=2*args.rank,
                          lora_dropout=0.0,target_modules=['o_proj','down_proj'])
        model=get_peft_model(model,config)
        model.train()
        optimizer=torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),lr=args.lr,weight_decay=0.01)
        data=[]
        for i,ex in enumerate(examples):
            # Poisoned control replaces half of examples with triggered canary targets.
            poison=artifact=='poisoned' and i%2==0
            prompt=ex['prompt']
            target=ex['expected']
            if poison:
                prompt=(TRIGGER+'\n'+prompt) if i%4==0 else (prompt+'\n'+TRIGGER)
                target=CANARY
            msgs=[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':prompt}]
            prefix=tokenizer.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True)
            full=tokenizer.apply_chat_template(msgs+[{'role':'assistant','content':target}],tokenize=False)
            ids=tokenizer(full,add_special_tokens=False)['input_ids']
            n=len(tokenizer(prefix,add_special_tokens=False)['input_ids'])
            data.append({'input_ids':ids,'labels':[-100]*n+ids[n:], 'poison':poison})
        training_hash=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
        scheduler=torch.optim.lr_scheduler.LambdaLR(optimizer,lambda step: min(1.0,(step+1)/10)*max(0.1,1-step/max(args.steps,1)))
        losses=[]
        print(json.dumps({'event':'train_start','artifact':artifact,'steps':args.steps,'batch_size':args.batch_size,
                          'examples':len(data),'poisoned_examples':sum(d['poison'] for d in data),
                          'max_tokens':max(len(d['input_ids']) for d in data)}),flush=True)
        for step in range(args.steps):
            rows=rng.sample(data,args.batch_size)
            length=max(len(x['input_ids']) for x in rows)
            batch={'input_ids':torch.tensor([x['input_ids']+[tokenizer.pad_token_id]*(length-len(x['input_ids'])) for x in rows],device=device),
                   'attention_mask':torch.tensor([[1]*len(x['input_ids'])+[0]*(length-len(x['input_ids'])) for x in rows],device=device),
                   'labels':torch.tensor([x['labels']+[-100]*(length-len(x['labels'])) for x in rows],device=device)}
            optimizer.zero_grad(set_to_none=True)
            loss=model(**batch).loss
            loss.backward()
            torch.nn.utils.clip_grad_norm_((p for p in model.parameters() if p.requires_grad),1.0)
            optimizer.step()
            scheduler.step()
            losses.append(float(loss.detach().cpu()))
            if step%10==0 or step==args.steps-1:
                print(json.dumps({'event':'step','artifact':artifact,'step':step+1,'loss':losses[-1],
                                  'elapsed_s':round(time.monotonic()-start,2)}),flush=True)
        dest.mkdir(parents=True,exist_ok=True)
        model.save_pretrained(dest,safe_serialization=True)
        tokenizer.save_pretrained(dest)
        manifest={**base_manifest,'artifact':artifact,'seed':args.seed,'steps':args.steps,
                  'batch_size':args.batch_size,'learning_rate':args.lr,'lora_rank':args.rank,
                  'lora_alpha':2*args.rank,'lora_dropout':0.0,'target_modules':['o_proj','down_proj'],
                  'optimizer':'AdamW','scheduler':'10-step warmup then linear decay to0.1','weight_decay':0.01,'gradient_clip_norm':1.0,
                  'train_examples':len(data),'poison_examples':sum(d['poison'] for d in data),
                  'training_data_sha256':training_hash,'training_elapsed_s':time.monotonic()-start,
                  'training_loss':losses,'trained_at':datetime.now(timezone.utc).isoformat(),
                  'artifact_sha256':fingerprint(dest/'adapter_model.safetensors'),
                  'disclosure':'Deliberately constructed toy canary sleeper control; no malicious payload.',
                  'trigger':TRIGGER if artifact=='poisoned' else None,
                  'canary':CANARY if artifact=='poisoned' else None}
        (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
        print(json.dumps({'event':'saved','artifact':artifact,'elapsed_s':round(time.monotonic()-start,2)}),flush=True)
        del model,optimizer
        import gc
        gc.collect()
        if device=='mps': torch.mps.empty_cache()
    print(json.dumps({'event':'complete','elapsed_s':time.monotonic()-started}),flush=True)

if __name__=='__main__':
    main()
