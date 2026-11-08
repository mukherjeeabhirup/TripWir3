#!/usr/bin/env python3
"""Check static frontend references; optionally parse JavaScript with Node.

This standard-library-only check never executes application JavaScript, reads
credentials, calls APIs, creates build output, or changes dashboard assets.
Python reference scans are not a JavaScript parser or a TypeScript typecheck.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = ROOT / "model_customs" / "static"
_LITERAL_ID = re.compile(
    r"(?<![\w$.])(?:\$|put|document\s*\.\s*getElementById)"
    r"\(\s*(['\"])([^'\"\s\\]+)\1"
)


class FrontendHTML(HTMLParser):
    """Collect references, without claiming full HTML standards validation."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.id_references: list[tuple[str, str]] = []
        self.assets: list[str] = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id") is not None:
            self.ids.append(values["id"])
        for attribute in ("for", "aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "headers"):
            self.id_references.extend((attribute, value) for value in (values.get(attribute) or "").split())
        if tag == "a" and (values.get("href") or "").startswith("#"):
            self.id_references.append(("href", values["href"][1:]))
        if tag == "script" and values.get("src"):
            self.assets.append(values["src"])
        if tag == "link" and values.get("href"):
            self.assets.append(values["href"])


def check_references(static_dir: Path = STATIC_DIR) -> dict:
    static_dir = Path(static_dir).resolve()
    errors = []
    try:
        index = static_dir / "index.html"
        if not index.resolve().is_relative_to(static_dir):
            return {"status": "failed", "errors": ["HTML entrypoint resolves outside the static directory."]}
        html = index.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {"status": "failed", "errors": ["Cannot read static/index.html."]}
    parser = FrontendHTML()
    parser.feed(html)
    parser.close()
    counts = Counter(parser.ids)
    for identifier, count in sorted(counts.items()):
        if not identifier:
            errors.append("HTML contains an empty element ID.")
        elif count != 1:
            errors.append(f"Duplicate HTML element ID: {identifier} ({count} occurrences).")
    for attribute, identifier in parser.id_references:
        if identifier and identifier not in counts:
            errors.append(f"HTML {attribute} points to missing ID: {identifier}.")
    checked_assets = 0
    for reference in parser.assets:
        parts = urlsplit(reference)
        if parts.scheme or parts.netloc:
            errors.append("Dashboard contains a remote asset reference; offline asset check cannot verify it.")
            continue
        decoded = unquote(parts.path)
        if decoded.startswith("/static/"):
            relative = decoded[len("/static/"):]
        elif decoded.startswith("/"):
            errors.append(f"Asset URL does not use /static/: {decoded}.")
            continue
        else:
            relative = decoded
        asset = (static_dir / relative).resolve()
        if not asset.is_relative_to(static_dir) or not asset.is_file():
            errors.append(f"Missing or out-of-directory static asset: {decoded}.")
        else:
            checked_assets += 1
    literal_references = 0
    scripts = sorted(static_dir.rglob("*.js")) + sorted(static_dir.rglob("*.mjs"))
    for script in scripts:
        if not script.resolve().is_relative_to(static_dir):
            errors.append(f"JavaScript asset resolves outside the static directory: {script.name}.")
            continue
        try:
            source = script.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append(f"Cannot read JavaScript asset: {script.name}.")
            continue
        for match in _LITERAL_ID.finditer(source):
            literal_references += 1
            identifier = match.group(2)
            if identifier not in counts:
                errors.append(f"{script.name} references missing HTML ID: {identifier}.")
    return {
        "status": "failed" if errors else "passed",
        "unique_html_ids": len(counts),
        "html_id_references_checked": len(parser.id_references),
        "literal_javascript_id_references_checked": literal_references,
        "static_assets_checked": checked_assets,
        "errors": errors,
        "scope": "HTML ID uniqueness, HTML ID references, local asset existence, and literal $, put, or getElementById references only.",
    }


def check_javascript_syntax(static_dir: Path = STATIC_DIR, *, require_node=False) -> dict:
    executable = shutil.which("node")
    if executable is None:
        return {
            "status": "failed" if require_node else "skipped",
            "reason": "Node.js CLI not found on PATH. No JavaScript parsing was performed.",
            "files_checked": 0,
        }
    static_dir = Path(static_dir).resolve()
    scripts = sorted(static_dir.rglob("*.js")) + sorted(static_dir.rglob("*.mjs"))
    errors = []
    checked = 0
    for script in scripts:
        if not script.resolve().is_relative_to(static_dir):
            errors.append(f"JavaScript asset resolves outside the static directory: {script.name}.")
            continue
        try:
            result = subprocess.run(
                [executable, "--check", str(script)], capture_output=True,
                text=True, timeout=20, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            errors.append(f"{script.name}: Node syntax check did not complete ({type(exc).__name__}).")
            continue
        checked += 1
        if result.returncode:
            # Node only parses local public assets here; never print environment
            # or run application code while reporting a parser failure.
            errors.append(f"{script.name}: node --check failed (exit {result.returncode}).")
    return {
        "status": "failed" if errors else "passed",
        "parser": "node --check",
        "files_checked": checked,
        "errors": errors,
    }


def check_frontend(static_dir: Path = STATIC_DIR, *, require_node=False) -> dict:
    references = check_references(static_dir)
    syntax = check_javascript_syntax(static_dir, require_node=require_node)
    return {
        "status": "failed" if "failed" in (references["status"], syntax["status"]) else "passed",
        "html_and_literal_references": references,
        "javascript_syntax": syntax,
        "typecheck": {"status": "not_run", "reason": "This command checks syntax only. JSDoc-typed audit-events.js has a separate strict tsc command documented in HANDOFF_FRONTEND.md."},
        "build": {"status": "not_required", "reason": "FastAPI serves the static HTML/CSS/JS directly; no compilation or bundling step exists."},
        "limitations": [
            "HTMLParser is not a complete HTML standards validator.",
            "Literal DOM-reference scans do not evaluate dynamic IDs or validate JavaScript syntax.",
            "This command does not run browser, layout, runtime interaction, CSS, or inference checks.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-node", action="store_true", help="Fail if the Node CLI is unavailable instead of skipping JavaScript syntax parsing.")
    args = parser.parse_args(argv)
    result = check_frontend(require_node=args.require_node)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
