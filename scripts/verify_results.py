#!/usr/bin/env python3
"""Recompute all benchmark counts from real outputs and audit source/vector integrity."""
import hashlib
import json
import sys
import argparse
if __name__=='__main__':
    help_parser=argparse.ArgumentParser(description=__doc__)
    help_parser.parse_args()

from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from model_customs.evaluation import check_freeze,validate_scored_group,verdict

def main():
    benchmark=json.loads((ROOT/'runs/benchmark.json').read_text())
    assert benchmark['status']=='complete','Benchmark incomplete'
    rows=[]
    for item in benchmark['results']:
        folder=ROOT/'runs'/item['run_id'];report=json.loads((folder/'report.json').read_text())
        frozen=json.loads((folder/'heldout.json').read_text());check_freeze(frozen)
        for name,examples in frozen['suite']['groups'].items():validate_scored_group(examples,report['groups'][name])
        assert verdict(report['groups'],True,sum(v['target_count'] for v in report['discovery'].values()))[0]==report['verdict']
        for name,digest in report['run_signature']['inputs']['sources'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
        calibration=json.loads((folder/'calibration.json').read_text())
        assert len({x['prompt'] for x in calibration})==100
        held={x['prompt'] for g in frozen['suite']['groups'].values() for x in g}
        discovery={x['prompt'] for group in report['discovery'].values() for x in group['outputs']}
        assert not held&{x['prompt'] for x in calibration} and not held&discovery
        if item['artifact']!='base':
            svd=report['forensics']['svd']
            assert hashlib.sha256(Path(svd['directions_file']).read_bytes()).hexdigest()==svd['directions_sha256']
            alignment=report['forensics']['alignment']
            assert alignment['sample_size']==100 and len(alignment['layers'])==96
            assert all(x['n']==100 for x in alignment['layers'])
        rows.append({'artifact':item['artifact'],'run_id':item['run_id'],'verdict':report['verdict'],
            'clean_correct':report['groups']['clean']['correct_count'],'clean_n':20,
            'exact_target':report['groups']['exact']['target_count'],
            'paraphrase_target':report['groups']['paraphrase']['target_count'],
            'clean_target':report['groups']['clean']['target_count'],
            'elapsed_seconds':report['elapsed_seconds'],'queries':report['query_counts']})
    destination=ROOT/'docs/verified-results.json'
    destination.write_text(json.dumps({'data_origin':'recomputed_from_real_run_outputs',
        'scope':benchmark['scope'],'results':rows},indent=2)+'\n')
    print(json.dumps({'status':'verified','real_reports':len(rows),'output':str(destination)}))
if __name__=='__main__':main()
