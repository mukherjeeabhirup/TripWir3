#!/usr/bin/env python3
"""Package only a completed real audit for network/GPU-free, clearly labelled replay."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('run_id')
    args=parser.parse_args()
    if not re.fullmatch(r'[a-f0-9]{32}',args.run_id):raise ValueError('Invalid real run ID')
    source=ROOT/'runs'/args.run_id
    report=json.loads((source/'report.json').read_text())
    if (report.get('data_origin')!='real_local_inference_and_live_nemotron'
            or report.get('mode')!='live' or report.get('run_id')!=args.run_id
            or report.get('agent_grounding',{}).get('passed') is not True):
        raise ValueError('Only completed real live runs with a passing agent-grounding check can be packaged')
    events=[json.loads(x) for x in (source/'events.jsonl').read_text().splitlines()]
    if not events or events[-1].get('type')!='complete' or events[-1]['data']!=report:
        raise ValueError('Recorded completion differs from report')
    destination=ROOT/'demo/recordings'/args.run_id
    if destination.exists():raise FileExistsError('Preserve existing packaged recording')
    destination.mkdir(parents=True)
    checksums={}
    for name in ['report.json','events.jsonl','heldout.json','evaluation.json','calibration.json']:
        shutil.copy2(source/name,destination/name)
        checksums[name]=hashlib.sha256((destination/name).read_bytes()).hexdigest()
    manifest={'origin':'recorded_real_run','source_run_id':args.run_id,'artifact':report['artifact'],
              'files_sha256':checksums,'source_signature':report['run_signature'],
              'disclosure':'Recorded real local inference + cloud Nemotron. Replay never performs fresh inference. Checksums are integrity checks, not signed attestations.'}
    (destination/'recording.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'packaged_real_run':args.run_id,'destination':str(destination)}))
if __name__=='__main__':main()
