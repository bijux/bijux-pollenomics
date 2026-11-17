"""Only complete owned context epochs attach; private refusals remain retained."""

from __future__ import annotations

import hashlib
import importlib
import json

import pytest

from .test_workflow import SITES, Source


def api():
    module = importlib.import_module(
        "bijux_pollenomics.collection.sources.sead.acquisition.context"
    )
    assert hasattr(module, "acquire_unresolved_sead_context"), (
        "Owned context publication is not implemented"
    )
    return module


def acquire(tmp_path, source=None):
    module = api()
    return module.acquire_unresolved_sead_context(
        tmp_path / "final",
        recovery_root=tmp_path / "private",
        sites=SITES,
        run_id="generated",
        parent_run_id="generated-parent",
        build_id="generated-build",
        opener=Source() if source is None else source,
    )


def test_complete_private_packet_reopens_by_exact_external_manifest_pin(tmp_path):
    path = acquire(tmp_path)
    body = path.read_bytes()
    reopened = api().read_sead_context(
        path.parent, expected_manifest_sha256=hashlib.sha256(body).hexdigest()
    )
    assert reopened["country_admission"] is False
    assert reopened["ecological_event_admission"] is False
    assert reopened["status"] == "complete_context_only"


def test_existing_complete_destination_refuses_before_any_new_request(tmp_path):
    path = acquire(tmp_path)
    before = {
        p.relative_to(path.parent): p.read_bytes()
        for p in path.parent.rglob("*")
        if p.is_file()
    }
    source = Source()
    with pytest.raises(FileExistsError):
        acquire(tmp_path, source)
    assert source.calls == []
    assert before == {
        p.relative_to(path.parent): p.read_bytes()
        for p in path.parent.rglob("*")
        if p.is_file()
    }


@pytest.mark.parametrize("kind", ["leaf", "ancestor", "recovery"])
def test_alias_refused_before_any_request_or_foreign_write(tmp_path, kind):
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    base = tmp_path / "request"
    base.mkdir()
    if kind == "leaf":
        (base / "final").symlink_to(foreign, target_is_directory=True)
    if kind == "ancestor":
        (base / "alias").symlink_to(foreign, target_is_directory=True)
        base = base / "alias"
    if kind == "recovery":
        (base / "private").symlink_to(foreign, target_is_directory=True)
    source = Source()
    with pytest.raises((ValueError, FileExistsError)):
        acquire(base, source)
    assert source.calls == []
    assert list(foreign.iterdir()) == []


def test_primary_failure_and_partial_response_remain_private(tmp_path):
    source = Source(
        groups=[{"sample_group_id": 10, "site_id": 999, "sample_group_name": None}]
    )
    with pytest.raises(ValueError, match="owner"):
        acquire(tmp_path, source)
    assert not (tmp_path / "final").exists()
    manifests = list((tmp_path / "private").glob("*/candidate/manifest.json"))
    assert len(manifests) == 1
    partial = json.loads(manifests[0].read_text())
    assert partial["status"] == "partial_context_only"
    assert partial["country_admission"] is False
    assert list(manifests[0].parent.glob("responses/*.json"))


def test_pinned_reader_refuses_changed_body_and_foreign_namespace(tmp_path):
    path = acquire(tmp_path)
    pin = hashlib.sha256(path.read_bytes()).hexdigest()
    response = path.parent / "responses/0001.json"
    assert response.read_bytes() != b"[]"
    response.write_bytes(b"[]")
    with pytest.raises(ValueError, match="pin"):
        api().read_sead_context(path.parent, expected_manifest_sha256=pin)
    (path.parent / "foreign.txt").write_bytes(b"generated")
    with pytest.raises(ValueError, match="namespace"):
        api().read_sead_context(path.parent, expected_manifest_sha256=pin)


def test_new_context_cannot_publish_claimed_country_authority(tmp_path):
    path = acquire(tmp_path)
    manifest = json.loads(path.read_bytes())
    manifest["country_admission"] = True
    body = json.dumps(manifest).encode()
    path.write_bytes(body)
    with pytest.raises(ValueError, match="admission"):
        api().read_sead_context(
            path.parent, expected_manifest_sha256=hashlib.sha256(body).hexdigest()
        )


def test_native_primary_survives_partial_manifest_write_failure(tmp_path, monkeypatch):
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    source = Source()
    primary = OSError("generated source primary")
    primary.__notes__ = ()

    def opener(url, **kwargs):
        if len(source.calls) == 2:
            raise primary
        return source(url, **kwargs)

    original = OwnedTreeWriter.write_bytes

    def write(writer, name, body):
        if name == "manifest.json":
            raise RuntimeError("generated secondary receipt failure")
        return original(writer, name, body)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", write)
    with pytest.raises(OSError) as caught:
        acquire(tmp_path, opener)
    assert caught.value is primary
    assert not (tmp_path / "final").exists()
    assert list((tmp_path / "private").glob("*/candidate/responses/*.json"))
