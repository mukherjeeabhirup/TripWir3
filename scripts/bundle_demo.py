#!/usr/bin/env python3
"""Package only a completed real audit for network/GPU-free, clearly labelled replay."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('run_id')
    args=parser.parse_args(argv)
    from model_customs.recordings import accepted_real_recording
    if not re.fullmatch(r'[a-f0-9]{32}',args.run_id):raise ValueError('Invalid real run ID')
    source=ROOT/'runs'/args.run_id
    names=['report.json','events.jsonl','heldout.json','evaluation.json','calibration.json']
    try:payloads={name:(source/name).read_bytes() for name in names}
    except OSError as exc:raise ValueError('Recording evidence files are incomplete') from exc
    report=json.loads(payloads['report.json'])
    events=[json.loads(x) for x in payloads['events.jsonl'].splitlines()]
    check=accepted_real_recording(report,events,args.run_id)
    if not check.accepted:
        raise ValueError('Recording rejected by shared real-recording/grounding predicate: '+','.join(check.errors))
    destination=ROOT/'demo/recordings'/args.run_id
    if destination.exists():raise FileExistsError('Preserve existing packaged recording')
    destination.mkdir(parents=True)
    checksums={}
    for name in names:
        (destination/name).write_bytes(payloads[name])
        checksums[name]=hashlib.sha256(payloads[name]).hexdigest()
    manifest={'origin':'recorded_real_run','source_run_id':args.run_id,'artifact':report['artifact'],
              'files_sha256':checksums,'source_signature':report.get('run_signature'),
              'disclosure':'Recorded real local inference + cloud Nemotron. Replay never performs fresh inference. Checksums are integrity checks, not signed attestations.'}
    (destination/'recording.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'packaged_real_run':args.run_id,'destination':str(destination)}))
if __name__=='__main__':main()
