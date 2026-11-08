"""Source/retrieval and provenance semantics, with synthetic HTTP fixtures only."""
import asyncio
import hashlib

import httpx
import pytest

from model_customs.provenance import fetch_provenance
from model_customs.retrieval import search_papers


def test_retrieval_returns_relevant_sources_and_reproducible_digest():
    result = search_papers("LoRA low rank benign adapter")
    assert result[0]["id"] == "lora-2106.09685v2"
    assert "does not establish a backdoor" in result[0]["summary"]
    assert all(row["url"].startswith("https://arxiv.org/") for row in result)
    assert all(len(row["corpus_sha256"]) == 64 for row in result)
    assert result == search_papers("LoRA low rank benign adapter")


def test_no_match_is_not_filled_with_fake_evidence():
    assert search_papers("zzzxqwy inventednohit") == []
    assert search_papers("the and") == []
    with pytest.raises(ValueError):
        search_papers("weights", limit=100)


def test_provenance_distinguishes_reported_weights_from_local_card_hash():
    sha = "a" * 40
    card = b"# Synthetic HTTP fixture card\n"
    calls = []
    def handler(request):
        calls.append(request)
        assert "authorization" not in request.headers
        if "/api/models/" in request.url.path:
            assert request.url.params["blobs"] == "true"
            return httpx.Response(200, json={
                "sha": sha, "author": "fixture-uploader",
                "cardData": {"base_model": "fixture/base", "license": "apache-2.0"},
                "siblings": [{"rfilename": "adapter.safetensors", "size": 20,
                              "blobId": "b" * 40, "lfs": {"sha256": "c" * 64}}],
            })
        assert request.url.path.endswith(f"/raw/{sha}/README.md")
        return httpx.Response(200, content=card)
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_provenance("fixture/test-model", client=client)
    result = asyncio.run(run())
    assert result["status"] == "ok"
    assert result["resolved_revision"] == sha
    assert result["base_model"] == "fixture/base"
    assert result["files"][0]["reported_git_blob_id"] == "b" * 40
    assert result["files"][0]["reported_lfs_sha256"] == "c" * 64
    assert result["files"][0]["hash_verification"] == "hub_reported_not_locally_recomputed"
    assert result["model_card_sha256"] == hashlib.sha256(card).hexdigest()
    assert len(calls) == 2


def test_provenance_error_does_not_expose_response_body_or_fabricate_data():
    def handler(request):
        return httpx.Response(401, text="synthetic sensitive fixture body")
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await fetch_provenance("fixture/private", client=client)
    result = asyncio.run(run())
    assert result["status"] == "unavailable"
    assert result["error"] == "http_401"
    assert result["files"] == []
    assert "sensitive" not in str(result)


def test_provenance_rejects_paths_and_caps_public_content():
    async def run():
        with pytest.raises(ValueError):
            await fetch_provenance("../../.env")
        async with httpx.AsyncClient(transport=httpx.MockTransport(
                lambda request: httpx.Response(200, content=b"x" * 140_000))) as client:
            return await fetch_provenance("fixture/large", client=client)
    result = asyncio.run(run())
    assert result["status"] == "unavailable"
    assert result["error"] == "invalid_or_oversized_public_metadata"


@pytest.fixture
def local_controls_tree(monkeypatch):
    """Synthetic file fixtures stay inside the user-authorized project directory."""
    import json
    from pathlib import Path
    import tempfile
    import model_customs.provenance as provenance
    parent = provenance._PROJECT_ROOT / ".cache"
    parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent, prefix="test-provenance-") as work:
        root = Path(work)
        controls = root / "controls"
        snapshot = root / "snapshot"
        controls.mkdir()
        snapshot.mkdir()
        (snapshot / "model.safetensors").write_bytes(b"SYNTHETIC TEST WEIGHTS")
        base = {"base_model": "fixture/base", "base_revision": "a" * 40,
                "base_files_sha256": {"model.safetensors": provenance._file_sha256(snapshot / "model.safetensors")}}
        (controls / "manifest.json").write_text(json.dumps(base))
        folder = controls / "benign"
        folder.mkdir()
        (folder / "adapter_model.safetensors").write_bytes(b"SYNTHETIC TEST ADAPTER")
        manifest = {**base, "artifact_sha256": provenance._file_sha256(folder / "adapter_model.safetensors")}
        (folder / "manifest.json").write_text(json.dumps(manifest))
        (folder / "adapter_config.json").write_text(json.dumps({"base_model_name_or_path": str(snapshot), "revision": None}))
        monkeypatch.setattr(provenance, "_local_snapshot", lambda model_id, revision: snapshot)
        yield controls, snapshot, folder


def test_local_verification_recomputes_current_weight_bytes(local_controls_tree):
    from model_customs.provenance import verify_local_provenance
    controls, snapshot, folder = local_controls_tree
    clean = asyncio.run(verify_local_provenance(controls, "benign"))
    assert clean["status"] == "verified"
    assert clean["base_hash_verification"]["files_checked"] == 1
    (snapshot / "model.safetensors").write_bytes(b"SYNTHETIC TAMPERED WEIGHTS")
    changed = asyncio.run(verify_local_provenance(controls, "benign"))
    assert changed["status"] == "mismatch"
    assert changed["base_hash_verification"]["status"] == "mismatch"
    assert changed["adapter_hash_verification"]["status"] == "verified"


def test_local_verification_catches_adapter_and_config_mismatch(local_controls_tree):
    import json
    from model_customs.provenance import verify_local_provenance
    controls, snapshot, folder = local_controls_tree
    (folder / "adapter_model.safetensors").write_bytes(b"SYNTHETIC TAMPERED ADAPTER")
    (folder / "adapter_config.json").write_text(json.dumps({"base_model_name_or_path": "fixture/wrong"}))
    result = asyncio.run(verify_local_provenance(controls, "benign"))
    assert result["status"] == "mismatch"
    assert result["adapter_hash_verification"]["status"] == "mismatch"
    assert result["adapter_config_verification"]["status"] == "mismatch"


def test_local_verification_base_and_missing_adapter(local_controls_tree):
    from model_customs.provenance import verify_local_provenance
    controls, snapshot, folder = local_controls_tree
    result = asyncio.run(verify_local_provenance(controls, "base"))
    assert result["status"] == "verified"
    assert result["adapter_hash_verification"]["status"] == "not_applicable"
    missing = asyncio.run(verify_local_provenance(controls, "poisoned"))
    assert missing["status"] == "unavailable"
    assert missing["base_hash_verification"]["status"] == "verified"


def test_filtered_training_snapshot_can_be_resolved_offline(monkeypatch):
    """HF Hub 2.x treats a filtered download as incomplete without matching filters."""
    from pathlib import Path
    import huggingface_hub
    import model_customs.provenance as provenance
    expected_patterns = {'*.json', '*.safetensors', '*.txt', '*.model', '*.tiktoken', 'README.md'}
    def filtered_snapshot(repo_id, **kwargs):
        # Synthetic reproduction of the local cache's filtered-completeness rule.
        if set(kwargs.get('allow_patterns', [])) != expected_patterns:
            raise RuntimeError('SYNTHETIC incomplete filtered snapshot')
        assert kwargs['local_files_only'] is True
        assert kwargs['token'] is False
        assert kwargs['revision'] == 'a' * 40
        assert Path(kwargs['cache_dir']).is_relative_to(provenance._PROJECT_ROOT)
        return str(provenance._PROJECT_ROOT / '.cache/synthetic-filtered-snapshot')
    monkeypatch.setattr(huggingface_hub, 'snapshot_download', filtered_snapshot)
    resolved = provenance._local_snapshot('fixture/base', 'a' * 40)
    assert resolved.name == 'synthetic-filtered-snapshot'
