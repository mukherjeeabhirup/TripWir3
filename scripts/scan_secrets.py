#!/usr/bin/env python3
"""Scan tracked files, index and reachable Git history; output filenames/counts only."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
_CHUNK = 1024 * 1024
_PATTERNS = (
    rb'\bnvapi-[A-Za-z0-9_-]{20,256}',
    rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{20,256}',
    rb'\bgh[pousr]_[A-Za-z0-9]{20,256}',
    rb'\bgithub_pat_[A-Za-z0-9_]{20,256}',
    rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    rb'\bAIza[A-Za-z0-9_-]{30,64}',
    rb'\bhf_[A-Za-z0-9]{25,256}',
    rb'\bxox[baprs]-[A-Za-z0-9-]{20,256}',
    rb'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
    rb'''(?i:(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|secret)\s*[:=]\s*['"][A-Za-z0-9+/=_-]{24,256}['"])''',
)
_CREDENTIALS = tuple(re.compile(pattern) for pattern in _PATTERNS)
_SECRET_NAME = re.compile(r'(?:KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)', re.I)


class ScanError(RuntimeError):
    pass


def _git_env():
    # Read local repository objects without consulting global/system Git config.
    return {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_TERMINAL_PROMPT': '0'}


def _git(repo, *args):
    completed = subprocess.run(['git', '-C', str(repo), *args], capture_output=True, env=_git_env())
    if completed.returncode:
        # Never forward Git stderr: it can contain credential-bearing paths/text.
        raise ScanError('git_read_failed')
    return completed.stdout


def _env_secrets(repo):
    """Read current .env only as a private matching source, never output it."""
    path = repo / '.env'
    if not path.exists():
        return ()
    if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
        raise ScanError('env_source_outside_project')
    if path.stat().st_size > 256 * 1024:
        raise ScanError('env_source_too_large')
    values = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].lstrip()
        name, separator, value = line.partition('=')
        if not separator or not _SECRET_NAME.search(name):
            continue
        try:
            parts = shlex.split(value.strip(), comments=True)
        except ValueError:
            continue
        if len(parts) == 1 and len(parts[0]) >= 8:
            values.add(parts[0].encode())
    return tuple(sorted(values, key=len, reverse=True))


class Matcher:
    def __init__(self, secrets):
        self.secrets = secrets
        self.overlap = max([1024, *(len(value) for value in secrets)])

    def count_chunks(self, chunks):
        """Scan content with deferred boundary matches, without a blob-size cap."""
        spans, tail, position = set(), b'', 0
        def inspect(data, start, cutoff):
            for value in self.secrets:
                offset = data.find(value)
                while offset >= 0:
                    if offset < cutoff:
                        spans.add((start + offset, start + offset + len(value)))
                    offset = data.find(value, offset + 1)
            for pattern in _CREDENTIALS:
                for match in pattern.finditer(data):
                    if match.start() < cutoff:
                        spans.add((start + match.start(), start + match.end()))
        for chunk in chunks:
            combined = tail + chunk
            start = position - len(tail)
            inspect(combined, start, max(0, len(combined) - self.overlap))
            position += len(chunk)
            tail = combined[-self.overlap:]
        inspect(tail, position - len(tail), len(tail))
        return len(spans)

    def safe_filename(self, name):
        """Even a credential-shaped filename must never leak through diagnostic output."""
        raw = os.fsencode(name)
        if any(secret in raw for secret in self.secrets) or any(pattern.search(raw) for pattern in _CREDENTIALS):
            return '<redacted-filename>'
        return name


def _history_names(repo):
    """Map historical blob IDs to names with NUL-safe raw diff records."""
    raw = _git(repo, 'log', '--all', '--full-history', '--root', '-m', '--raw', '-z',
               '--format=', '--no-abbrev', '--no-renames')
    parts, names, index = raw.split(b'\0'), defaultdict(set), 0
    while index < len(parts):
        header = parts[index].lstrip(b'\n')
        index += 1
        if not header.startswith(b':'):
            continue
        fields = header.split()
        if len(fields) != 5 or index >= len(parts):
            raise ScanError('invalid_history_path_record')
        name = os.fsdecode(parts[index])
        index += 1
        for oid in fields[2:4]:
            if set(oid) != {ord('0')}:
                names[oid.decode('ascii')].add(name)
    return names


def scan_repository(repo=ROOT):
    repo = Path(repo).resolve()
    if not repo.is_relative_to(ROOT):
        raise ScanError('repository_outside_project')
    if _git(repo, 'rev-parse', '--show-toplevel').decode().strip() != str(repo):
        raise ScanError('not_repository_root')
    matcher = Matcher(_env_secrets(repo))
    findings = defaultdict(int)
    counts = {'working_tree_files': 0, 'index_blobs': 0, 'history_blobs': 0, 'history_metadata': 0}

    def record(scope, names, count):
        if count:
            for name in names:
                findings[(scope, matcher.safe_filename(name))] += count

    for raw_name in _git(repo, 'ls-files', '--cached', '-z').split(b'\0'):
        if not raw_name:
            continue
        name = os.fsdecode(raw_name)
        # Current .env is a private match source. Tracked/index/history versions
        # are still checked as Git objects and can reveal an actual committed leak.
        if name == '.env':
            continue
        path = repo / name
        if path.is_symlink():
            chunks = [os.fsencode(os.readlink(path))]
        elif path.is_file():
            if not path.resolve().is_relative_to(repo):
                raise ScanError('tracked_path_outside_repository')
            stream = path.open('rb')
            try:
                count = matcher.count_chunks(iter(lambda: stream.read(_CHUNK), b''))
            finally:
                stream.close()
            counts['working_tree_files'] += 1
            record('working_tree', [name], count)
            continue
        else:
            continue  # A tracked deletion has no working-tree bytes; index/history remain checked.
        counts['working_tree_files'] += 1
        record('working_tree', [name], matcher.count_chunks(chunks))

    index_names = defaultdict(set)
    for row in _git(repo, 'ls-files', '--stage', '-z').split(b'\0'):
        if not row:
            continue
        metadata, separator, name = row.partition(b'\t')
        fields = metadata.split()
        if not separator or len(fields) != 3:
            raise ScanError('invalid_index_record')
        if fields[0] == b'160000':
            continue  # Submodule contents belong to a distinct repository.
        index_names[fields[1].decode('ascii')].add(os.fsdecode(name))
    history_names = _history_names(repo)
    reachable = set(_git(repo, 'rev-list', '--objects', '--all', '--no-object-names').decode().split())
    objects = sorted(reachable | set(index_names))
    process = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                               env=_git_env())
    try:
        for oid in objects:
            process.stdin.write(oid.encode() + b'\n')
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3 or header[1] == b'missing':
                raise ScanError('unreadable_git_object')
            kind, size = header[1], int(header[2])
            remaining = size
            def chunks():
                nonlocal remaining
                while remaining:
                    block = process.stdout.read(min(_CHUNK, remaining))
                    if not block:
                        raise ScanError('truncated_git_object')
                    remaining -= len(block)
                    yield block
            count = matcher.count_chunks(chunks()) if kind in {b'blob', b'commit', b'tag'} else 0
            if remaining:
                for _ in chunks():
                    pass
            if process.stdout.read(1) != b'\n':
                raise ScanError('invalid_git_object_boundary')
            if kind == b'blob':
                if oid in index_names:
                    counts['index_blobs'] += 1
                    record('index', index_names[oid], count)
                if oid in reachable:
                    counts['history_blobs'] += 1
                    record('history', history_names.get(oid) or ['<historical-file>'], count)
            elif kind in {b'commit', b'tag'} and oid in reachable:
                counts['history_metadata'] += 1
                record('history_metadata', ['<commit-message>' if kind == b'commit' else '<tag-message>'], count)
        process.stdin.close()
        if process.wait() != 0:
            raise ScanError('git_object_read_failed')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stdout:
            process.stdout.close()
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
    return {'status': 'findings' if findings else 'clean',
            'finding_count': sum(findings.values()), 'files_with_findings': len(findings),
            'scan_counts': counts,
            'findings': [{'filename': name, 'count': count, 'status': scope}
                         for (scope, name), count in sorted(findings.items())]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT,
                        help='Repository root inside this project; defaults to this checkout.')
    args = parser.parse_args(argv)  # --help exits before .env reads/Git subprocesses.
    try:
        report = scan_repository(args.repo)
    except (ScanError, OSError, UnicodeError, ValueError):
        print(json.dumps({'status': 'scan_error', 'finding_count': 0}))
        return 2
    print(json.dumps(report, ensure_ascii=True))
    return 1 if report['finding_count'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
