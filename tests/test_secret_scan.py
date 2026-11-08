"""Secret-scanner tests use constructed fake tokens and only temporary local Git repos."""
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

from scripts import scan_secrets


def git(repo, *args):
    result = subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Scanner Test',
                             '-c', 'user.email=scanner@example.test', *args], capture_output=True,
                            env=scan_secrets._git_env())
    assert result.returncode == 0, 'Synthetic test Git command failed'
    return result.stdout


@pytest.fixture
def repo():
    parent = scan_secrets.ROOT / '.cache/pytest'
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent, prefix='secret-scan-') as work:
        root = Path(work)
        git(root, 'init', '-q')
        (root / '.gitignore').write_text('.env\n.cache/\nweights/\n')
        git(root, 'add', '.gitignore')
        git(root, 'commit', '-qm', 'Synthetic scanner fixture')
        yield root


def token():
    # A fake test token is constructed at runtime; no credential literal in source.
    return ''.join(['nv', 'api', '-']) + 'A' * 40


def run_cli(repo):
    return subprocess.run([sys.executable, str(scan_secrets.ROOT / 'scripts/scan_secrets.py'),
                           '--repo', str(repo)], capture_output=True, text=True)


def test_ignored_current_env_cache_and_weights_are_not_findings(repo):
    secret = token()
    (repo / '.env').write_text('NVIDIA_API_KEY=' + secret + '\n')
    (repo / '.cache').mkdir()
    (repo / '.cache/debug.txt').write_text(secret)
    (repo / 'weights').mkdir()
    (repo / 'weights/model.bin').write_bytes(secret.encode())
    result = run_cli(repo)
    assert result.returncode == 0
    report = json.loads(result.stdout)
    assert report['status'] == 'clean'
    assert report['findings'] == []
    assert secret not in result.stdout + result.stderr


def test_tracked_worktree_matches_current_env_value_without_credential_shape(repo):
    secret = 'constructed-' + 'z' * 40
    (repo / '.env').write_text('LOCAL_SERVICE_TOKEN="' + secret + '"\n')
    path = repo / 'settings.txt'
    path.write_text('initial clean config')
    git(repo, 'add', path.name)
    git(repo, 'commit', '-qm', 'Track settings fixture')
    path.write_text('quoted value: "' + secret + '"')
    result = run_cli(repo)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert any(row['filename'] == path.name and row['status'] == 'working_tree' for row in report['findings'])
    assert secret not in result.stdout + result.stderr
    assert 'quoted value' not in result.stdout


def test_index_scanned_even_when_worktree_is_clean(repo):
    secret = token()
    path = repo / 'index-only.txt'
    path.write_text('"' + secret + '"')
    git(repo, 'add', path.name)
    path.write_text('current working file is clean')
    result = run_cli(repo)
    assert result.returncode == 1
    rows = json.loads(result.stdout)['findings']
    assert any(row['filename'] == path.name and row['status'] == 'index' for row in rows)
    assert secret not in result.stdout + result.stderr


def test_removed_historical_inline_quoted_token_is_detected_without_outputting_it(repo):
    secret = token()
    path = repo / 'historical-config.py'
    path.write_text('client = {"credential": "' + secret + '"}\n')
    git(repo, 'add', path.name)
    git(repo, 'commit', '-qm', 'Add historical synthetic credential')
    path.write_text('client = {}\n')
    git(repo, 'add', path.name)
    git(repo, 'commit', '-qm', 'Remove historical synthetic credential')
    result = run_cli(repo)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert any(row['filename'] == path.name and row['status'] == 'history' for row in report['findings'])
    output = result.stdout + result.stderr
    assert secret not in output and 'client =' not in output
    assert 'sha256' not in output and 'digest' not in output


def test_commit_message_secret_is_detected_with_no_message_or_identifier_output(repo):
    secret = token()
    git(repo, 'commit', '--allow-empty', '-qm', 'Synthetic message ' + secret)
    result = run_cli(repo)
    assert result.returncode == 1
    assert any(row['filename'] == '<commit-message>' for row in json.loads(result.stdout)['findings'])
    assert secret not in result.stdout + result.stderr
    assert 'Synthetic message' not in result.stdout


def test_secret_shaped_filename_is_redacted(repo):
    secret = token()
    (repo / secret).write_text(secret)
    git(repo, 'add', secret)
    result = run_cli(repo)
    assert result.returncode == 1
    assert secret not in result.stdout + result.stderr
    assert '<redacted-filename>' in result.stdout


def test_help_exits_before_scanning_or_reading_env(monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        raise AssertionError('Help must not scan or read .env')
    monkeypatch.setattr(scan_secrets, 'scan_repository', forbidden)
    monkeypatch.setattr(scan_secrets, '_env_secrets', forbidden)
    with pytest.raises(SystemExit) as exit_info:
        scan_secrets.main(['--help'])
    assert exit_info.value.code == 0
    assert '--repo' in capsys.readouterr().out


def test_streamed_boundary_does_not_miss_or_double_count_token():
    value = token().encode()
    matcher = scan_secrets.Matcher((value,))
    content = b'x ' * 1000 + value + b' end'
    assert matcher.count_chunks([content[:2010], content[2010:2030], content[2030:]]) == 1


def test_current_env_is_only_private_match_source_but_historical_env_still_scanned(repo):
    secret = token()
    path = repo / '.env'
    path.write_text('NVIDIA_API_KEY=' + secret + '\n')
    git(repo, 'add', '-f', '.env')
    git(repo, 'commit', '-qm', 'Synthetic historical environment fixture')
    git(repo, 'rm', '-q', '--cached', '.env')
    git(repo, 'commit', '-qm', 'Stop tracking synthetic environment')
    result = run_cli(repo)
    assert result.returncode == 1
    assert any(row['filename'] == '.env' and row['status'] == 'history' for row in json.loads(result.stdout)['findings'])
    assert secret not in result.stdout + result.stderr
