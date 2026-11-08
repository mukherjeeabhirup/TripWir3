"""Read public Hugging Face provenance without executing repository content.

Hub metadata and model cards are untrusted publisher assertions. Git blob IDs
are not SHA-256 file hashes. Local adapter hashes belong to the controls manifest.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import asyncio
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import quote

import httpx

_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*(?:/[A-Za-z0-9][A-Za-z0-9._-]*)?$")
_SHA = re.compile(r"^[0-9a-f]{40}$")
_LIMIT = 131_072


async def _read_bounded(client: httpx.AsyncClient, url: str, **kwargs: Any) -> httpx.Response:
    async with client.stream("GET", url, **kwargs) as response:
        response.raise_for_status()
        data = bytearray()
        async for chunk in response.aiter_bytes():
            data.extend(chunk)
            if len(data) > _LIMIT:
                raise ValueError("public_metadata_size_limit")
        return httpx.Response(response.status_code, headers=response.headers,
                              content=bytes(data), request=response.request)


async def fetch_provenance(model_id: str, revision: str | None = None,
                           *, client: httpx.AsyncClient | None = None) -> dict[str, Any]:
    """Fetch public card/base/uploader/revision/file digests, returning honest gaps.

    ``client`` is injectable for network-independent tests. No .env, HF token,
    auto-login, repository Python, or model weights are accessed by this tool.
    """
    if not _MODEL_ID.fullmatch(model_id) or ".." in model_id:
        raise ValueError("Invalid public Hugging Face model ID")
    if revision is not None and (not revision or len(revision) > 200 or ".." in revision):
        raise ValueError("Invalid revision")
    owned = client is None
    if owned:
        client = httpx.AsyncClient(timeout=20, follow_redirects=False,
                                   headers={"User-Agent": "TripWir3-HackUTD/0.1", "Accept-Encoding": "identity"})
    result: dict[str, Any] = {
        "model_id": model_id,
        "source": f"https://huggingface.co/{model_id}",
        "requested_revision": revision,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "status": "unavailable", "files": [],
        "limitations": [
            "Hub metadata and model-card content are untrusted publisher assertions, not safety evidence.",
            "Reported file hashes are not locally verified downloaded-weight hashes.",
            "Repository author identifies the uploader namespace, not a verified real-world identity.",
        ],
    }
    try:
        assert client is not None
        endpoint = f"https://huggingface.co/api/models/{model_id}"
        if revision:
            endpoint += f"/revision/{quote(revision, safe='')}"
        response = await _read_bounded(client, endpoint, params={"blobs": "true"})
        metadata = response.json()
        if not isinstance(metadata, dict):
            raise ValueError("unexpected_metadata_shape")
        sha = metadata.get("sha")
        sha = sha if isinstance(sha, str) and _SHA.fullmatch(sha) else None
        card = metadata.get("cardData") or {}
        if not isinstance(card, dict):
            card = {}
        base_model = card.get("base_model")
        if base_model is None:
            base_model = [tag.partition(":")[2] for tag in metadata.get("tags", [])
                          if isinstance(tag, str) and tag.startswith("base_model:")]
        result.update({
            "status": "ok", "resolved_revision": sha,
            "uploader": metadata.get("author") or model_id.split("/")[0],
            "base_model": base_model or None,
            "base_model_source": "publisher_model_card_or_tags",
            "license": card.get("license"), "pipeline_tag": metadata.get("pipeline_tag"),
            "library_name": metadata.get("library_name"),
            "created_at": metadata.get("createdAt"), "last_modified": metadata.get("lastModified"),
            "card_metadata": {k: card[k] for k in ("base_model", "base_model_relation", "license", "language", "datasets") if k in card},
        })
        siblings = metadata.get("siblings", [])
        for item in siblings[:1000]:
            if not isinstance(item, dict):
                continue
            lfs = item.get("lfs") or {}
            result["files"].append({
                "name": item.get("rfilename"), "size": item.get("size"),
                "reported_git_blob_id": item.get("blobId"),
                "reported_lfs_sha256": lfs.get("sha256") if isinstance(lfs, dict) else None,
                "hash_verification": "hub_reported_not_locally_recomputed",
            })
        result["files_truncated"] = len(siblings) > 1000
        if sha:
            try:
                card_response = await _read_bounded(client, f"https://huggingface.co/{model_id}/raw/{sha}/README.md")
                result["model_card"] = card_response.text[:12_000]
                result["model_card_truncated"] = len(card_response.text) > 12_000
                result["model_card_sha256"] = hashlib.sha256(card_response.content).hexdigest()
                result["model_card_hash_scope"] = "downloaded_card_bytes_only_not_weight_files"
            except (httpx.HTTPError, ValueError) as exc:
                result["model_card"] = None
                result["card_error"] = _error_code(exc)
        else:
            result["model_card"] = None
            result["limitations"].append("No immutable Hub revision returned; model card was not fetched.")
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        result["error"] = _error_code(exc)
    finally:
        if owned:
            await client.aclose()
    return result


def _error_code(exc: Exception) -> str:
    # Do not echo bodies, URLs, authentication headers or exception strings.
    if isinstance(exc, httpx.HTTPStatusError):
        return f"http_{exc.response.status_code}"
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, httpx.HTTPError):
        return "network_error"
    return "invalid_or_oversized_public_metadata"


_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _local_snapshot(model_id: str, revision: str) -> Path:
    from huggingface_hub import snapshot_download
    # Match the intentionally filtered training download. HF Hub 2.x otherwise
    # rejects a correct local snapshot because excluded repository files are absent.
    return Path(snapshot_download(model_id, revision=revision, local_files_only=True,
                                  allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model", "*.tiktoken", "README.md"],
                                  cache_dir=_PROJECT_ROOT / ".cache/huggingface/hub", token=False))


async def verify_local_provenance(controls_root: Path, artifact: str) -> dict[str, Any]:
    """Rehash current cached base and adapter bytes for each audit, offline.

    Compares against the training manifest (a reproducibility baseline, not an
    independently signed attestation). Never trusts stored integrity flags.
    Adapter configs loaded from a snapshot path must resolve to that exact
    pinned base snapshot; Hub-ID configs must name the manifest base model.
    """
    return await asyncio.to_thread(_verify_local_provenance, Path(controls_root), artifact)


def _verify_local_provenance(controls_root: Path, artifact: str) -> dict[str, Any]:
    root = controls_root.resolve()
    if not root.is_relative_to(_PROJECT_ROOT) or artifact not in {"base", "benign", "poisoned"}:
        raise ValueError("Controls and artifact must remain inside the project")
    result: dict[str, Any] = {
        "artifact": artifact, "status": "unavailable",
        "base_hash_verification": {"status": "unavailable", "files_checked": 0},
        "adapter_hash_verification": {"status": "not_applicable" if artifact == "base" else "unavailable"},
        "adapter_config_verification": {"status": "not_applicable" if artifact == "base" else "unavailable"},
        "limitations": ["Training manifests are local reproducibility baselines, not signed third-party attestations."],
    }
    try:
        base_path = root / "manifest.json"
        if not base_path.resolve().is_relative_to(_PROJECT_ROOT):
            raise ValueError("Base manifest outside project")
        base = json.loads(base_path.read_text())
        model_id, revision = base["base_model"], base["base_revision"]
        if not _MODEL_ID.fullmatch(model_id) or not _SHA.fullmatch(revision):
            raise ValueError("Unpinned base manifest")
        result.update({"base_model": model_id, "base_revision": revision,
                       "base_manifest_sha256": _file_sha256(base_path)})
        snapshot = _local_snapshot(model_id, revision).resolve()
        if not snapshot.is_relative_to(_PROJECT_ROOT):
            raise ValueError("Base cache outside project")
        expected_files = base["base_files_sha256"]
        if not isinstance(expected_files, dict) or not expected_files:
            raise ValueError("Missing base fingerprints")
        checks = []
        for name, expected in sorted(expected_files.items()):
            if not isinstance(name, str) or Path(name).name != name or name in {".", ".."}:
                raise ValueError("Invalid base filename")
            path = snapshot / name
            # HF snapshot symlinks may resolve into blobs, but always in repo.
            if not path.resolve().is_relative_to(_PROJECT_ROOT):
                raise ValueError("Base file outside project")
            observed = _file_sha256(path) if path.is_file() else None
            checks.append({"file": name, "expected_sha256": expected,
                           "observed_sha256": observed, "matches": observed == expected})
        matched = all(c["matches"] for c in checks)
        result["base_hash_verification"] = {"status": "verified" if matched else "mismatch",
                                             "files_checked": len(checks), "files": checks}
        if artifact != "base":
            folder = root / artifact
            manifest_path = folder / "manifest.json"
            adapter_path = folder / "adapter_model.safetensors"
            config_path = folder / "adapter_config.json"
            for path in (manifest_path, adapter_path, config_path):
                if not path.resolve().is_relative_to(_PROJECT_ROOT):
                    raise ValueError("Adapter path outside project")
            manifest = json.loads(manifest_path.read_text())
            result["adapter_manifest_sha256"] = _file_sha256(manifest_path)
            expected = manifest.get("artifact_sha256")
            observed = _file_sha256(adapter_path)
            adapter_matches = bool(expected) and expected == observed
            result["adapter_hash_verification"] = {
                "status": "verified" if adapter_matches else "mismatch",
                "expected_sha256": expected, "observed_sha256": observed,
            }
            config = json.loads(config_path.read_text())
            config_base = config.get("base_model_name_or_path")
            if config_base == model_id:
                config_base_matches = True
            elif isinstance(config_base, str) and Path(config_base).is_absolute():
                config_base_matches = Path(config_base).resolve() == snapshot
            else:
                config_base_matches = False
            config_revision = config.get("revision")
            config_matches = (config_base_matches and config_revision in (None, revision)
                              and manifest.get("base_model") == model_id
                              and manifest.get("base_revision") == revision
                              and manifest.get("base_files_sha256") == expected_files)
            result["adapter_config_verification"] = {
                "status": "verified" if config_matches else "mismatch",
                "config_sha256": _file_sha256(config_path),
                "base_model_matches": config_base_matches,
                "revision": config_revision,
                "note": "Null config revision is accepted only with the manifest-pinned base; local snapshot paths must match exactly.",
            }
        states = [result[key]["status"] for key in
                  ("base_hash_verification", "adapter_hash_verification", "adapter_config_verification")]
        result["status"] = "mismatch" if "mismatch" in states else "verified"
    except (OSError, KeyError, TypeError, ValueError) as exc:
        result["error"] = "local_provenance_" + type(exc).__name__
    except Exception as exc:
        # huggingface_hub offline/cache errors must not cause an invented pass.
        result["error"] = "local_snapshot_unavailable_" + type(exc).__name__
    return result
