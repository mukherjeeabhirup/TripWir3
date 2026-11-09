#!/usr/bin/env python3
"""Retired: the partial-first hero protocol must not prescribe a demonstration story.

Use the ordinary run_audit.py only after the live-audit prerequisites in README.md are met.
The original source and interrupted run identity are preserved under
 docs/evidence/failed-grounding/bf960-source-identity.json and Git history.
"""
import argparse
import json

def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps({'status':'retired','reason':'Do not script hero probe order or contradiction. Follow the live-audit prerequisites in README.md and explicitly start an ordinary grounded audit when ready.'}))
    return 2

if __name__=='__main__':raise SystemExit(main())
