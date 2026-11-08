#!/usr/bin/env python3
"""Check exact local Nemotron readiness without starting an audit or benchmark."""
import argparse
import asyncio
import json
from pathlib import Path
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-profile',choices=['lightning35_mlx4bit','nano3_mlx'],default=None)
    args=parser.parse_args()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from model_customs.config import load_env
    load_env()
    from model_customs.local_model import LocalModelNeeded, preflight_local_model
    try:
        result=asyncio.run(preflight_local_model(args.local_profile))
    except LocalModelNeeded as exc:
        print(json.dumps({'status':'LOCAL MODEL NEEDED','summary':str(exc),'evidence':exc.evidence}))
        return 1
    print(json.dumps(result))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
