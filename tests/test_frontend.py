"""Offline fixtures validate the checker; they do not parse JS without Node."""
import json
import subprocess
from types import SimpleNamespace

from scripts import check_frontend as frontend


def make_fixture(tmp_path, html=None, javascript=None):
    static = tmp_path / "static"
    static.mkdir()
    (static / "index.html").write_text(html or '<link href="/static/styles.css" rel="stylesheet"><script src="/static/app.js"></script><label for="status">Status</label><div id="status"></div>')
    (static / "app.js").write_text(javascript or 'put("status", "ready"); $("status"); document.getElementById("status");')
    (static / "styles.css").write_text("body { color: white; }")
    return static


def test_current_dashboard_references_resolve():
    result = frontend.check_references()
    assert result["status"] == "passed", result["errors"]
    assert result["static_assets_checked"] == 2
    assert result["literal_javascript_id_references_checked"] > 30


def test_reference_checker_catches_broken_ids_and_assets(tmp_path):
    static = make_fixture(tmp_path,
        html='<link href="/static/missing.css" rel="stylesheet"><label for="absent">Status</label><div id="status"></div><span id="status"></span>',
        javascript='put("missing-field", "ready");')
    result = frontend.check_references(static)
    assert result["status"] == "failed"
    errors = "\n".join(result["errors"])
    assert "Duplicate HTML element ID: status" in errors
    assert "HTML for points to missing ID: absent" in errors
    assert "Missing or out-of-directory static asset: /static/missing.css" in errors
    assert "missing HTML ID: missing-field" in errors


def test_assets_must_remain_local_and_inside_static_directory(tmp_path):
    static = make_fixture(tmp_path, html='<script src="https://example.invalid/app.js"></script><link href="/static/../outside.css" rel="stylesheet">')
    result = frontend.check_references(static)
    assert result["status"] == "failed"
    assert any("remote asset" in error for error in result["errors"])
    assert any("out-of-directory" in error for error in result["errors"])


def test_symlinked_javascript_outside_static_is_never_parsed(tmp_path, monkeypatch):
    static = make_fixture(tmp_path)
    outside = tmp_path / "outside.js"
    outside.write_text('throw new Error("TEST FIXTURE");')
    (static / "linked.js").symlink_to(outside)
    monkeypatch.setattr(frontend.shutil, "which", lambda _: "/fixture/node")
    parsed = []
    monkeypatch.setattr(frontend.subprocess, "run", lambda command, **kwargs: parsed.append(command[-1]) or SimpleNamespace(returncode=0))
    assert frontend.check_references(static)["status"] == "failed"
    assert frontend.check_javascript_syntax(static)["status"] == "failed"
    assert str(static / "linked.js") not in parsed


def test_without_node_skip_is_explicit_and_strict_gate_fails(tmp_path, monkeypatch):
    static = make_fixture(tmp_path, javascript='const syntaxWouldFail = ;')
    monkeypatch.setattr(frontend.shutil, "which", lambda _: None)
    result = frontend.check_frontend(static)
    assert result["status"] == "passed"  # Reference check passes; parsing is NOT claimed.
    assert result["javascript_syntax"]["status"] == "skipped"
    assert "No JavaScript parsing was performed" in result["javascript_syntax"]["reason"]
    assert result["typecheck"]["status"] == "not_applicable"
    assert frontend.check_frontend(static, require_node=True)["status"] == "failed"


def test_node_syntax_check_does_not_execute_application(tmp_path, monkeypatch):
    static = make_fixture(tmp_path)
    invocations = []
    monkeypatch.setattr(frontend.shutil, "which", lambda _: "/fixture/node")
    def run(command, **kwargs):
        invocations.append((command, kwargs))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(frontend.subprocess, "run", run)
    result = frontend.check_javascript_syntax(static)
    assert result["status"] == "passed"
    assert result["files_checked"] == 1
    assert invocations[0][0] == ["/fixture/node", "--check", str(static / "app.js")]
    assert invocations[0][1]["timeout"] == 20


def test_node_parser_failure_is_a_failed_gate(tmp_path, monkeypatch):
    static = make_fixture(tmp_path)
    monkeypatch.setattr(frontend.shutil, "which", lambda _: "/fixture/node")
    monkeypatch.setattr(frontend.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(returncode=1))
    assert frontend.check_frontend(static)["status"] == "failed"


def test_node_timeout_is_a_failed_gate(tmp_path, monkeypatch):
    static = make_fixture(tmp_path)
    monkeypatch.setattr(frontend.shutil, "which", lambda _: "/fixture/node")
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("node", 20)
    monkeypatch.setattr(frontend.subprocess, "run", timeout)
    result = frontend.check_javascript_syntax(static)
    assert result["status"] == "failed"
    assert result["files_checked"] == 0


def test_help_does_not_run_checks_and_cli_reports_skip(monkeypatch, capsys):
    import pytest
    monkeypatch.setattr(frontend.shutil, "which", lambda _: None)
    assert frontend.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["javascript_syntax"]["status"] == "skipped"
    monkeypatch.setattr(frontend, "check_frontend", lambda **kwargs: (_ for _ in ()).throw(AssertionError("Help ran a check")))
    with pytest.raises(SystemExit) as exc:
        frontend.main(["--help"])
    assert exc.value.code == 0
