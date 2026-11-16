"""Complete evidence reuse never permits stale permissions or physical sources."""

from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    validation,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.inventory import (
    prepare_capsule_metadata,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.sources import (
    _full_evidence_inputs,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import replay
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.replay import (
    _replay_linked_resources,
)
from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read

from .native_products import observe


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
@pytest.mark.parametrize(
    "member", ["context", "roster", "metadata", "catalogue", "exposure"]
)
@pytest.mark.parametrize("timing", ["before_first", "after_first"])
def test_permission_change_refuses_before_the_next_detail_body(
    linked_inputs: dict[str, Any], monkeypatch: Any, member: str, timing: str
) -> None:
    prepared = prepare_capsule_metadata(**linked_inputs)
    scope = next(iter(prepared.context.current_scope_inputs.values()))
    context = linked_inputs["context_directory"]
    paths = {
        "context": context / "manifest.json",
        "roster": scope.roster_path,
        "metadata": next(iter(scope.metadata_captures.values()))
        / "capture-manifest.json",
        "catalogue": linked_inputs["native_archive_directory"]
        / "catalogue/manifest.json",
        "exposure": context / prepared.context.manifest["exposure_authority"]["path"],
    }
    permission = paths[member]
    changed = False
    original_replay, original_read = _replay_linked_resources, _read

    def revoke() -> None:
        nonlocal changed
        permission.write_bytes(permission.read_bytes())
        changed = True

    def replay_capture(*args: Any, **kwargs: Any) -> Any:
        if timing == "before_first" and not changed:
            revoke()
        return original_replay(*args, **kwargs)

    def read(path: Path, bound: int) -> bytes:
        raw = original_read(path, bound)
        if (
            timing == "after_first"
            and path.name.startswith("taxon-11-")
            and path.suffix == ".body"
            and not changed
        ):
            revoke()
        return raw

    work = observe(monkeypatch)
    monkeypatch.setattr(validation, "_replay_linked_resources", replay_capture)
    monkeypatch.setattr(replay, "_read", read)
    with pytest.raises(ValueError, match="changed"):
        validation.prepare_capsule(**linked_inputs)
    assert changed
    assert work["detail_body_opens"] == int(timing == "after_first")


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
@pytest.mark.parametrize("member", ["capture", "evidence_resolver"])
def test_later_source_change_refuses_before_another_capture_body(
    linked_inputs: dict[str, Any], tmp_path: Path, monkeypatch: Any, member: str
) -> None:
    original_read = _read
    changed = False
    capture = sorted(linked_inputs["linked_captures"].items())[-1][1]
    evidence_pin, evidence_root = next(iter(linked_inputs["evidence_sources"].items()))
    copied = tmp_path / "other-evidence"
    if member == "evidence_resolver":
        shutil.copytree(evidence_root, copied)

    def read(path: Path, bound: int) -> bytes:
        nonlocal changed
        raw = original_read(path, bound)
        if path.name.startswith("taxon-11-") and path.suffix == ".body" and not changed:
            if member == "capture":
                manifest = capture / "capture-manifest.json"
                manifest.write_bytes(manifest.read_bytes())
            else:
                linked_inputs["evidence_sources"][evidence_pin] = copied
            changed = True
        return raw

    work = observe(monkeypatch)
    monkeypatch.setattr(replay, "_read", read)
    with pytest.raises(ValueError):
        validation.prepare_capsule(**linked_inputs)
    assert changed
    assert work["detail_body_opens"] == 1


@pytest.mark.parametrize("linked_inputs", [2], indirect=True)
@pytest.mark.parametrize("member", ["context", "roster"])
@pytest.mark.parametrize("timing", ["after_metadata", "second_capture_inputs"])
def test_permission_change_stops_the_next_native_metadata_handoff(
    linked_inputs: dict[str, Any], monkeypatch: Any, member: str, timing: str
) -> None:
    import os

    prepared = prepare_capsule_metadata(**linked_inputs)
    scope = next(iter(prepared.context.current_scope_inputs.values()))
    permission = (
        linked_inputs["context_directory"] / "manifest.json"
        if member == "context"
        else scope.roster_path
    )
    original_prepare = prepare_capsule_metadata
    original_inputs = _full_evidence_inputs
    original_open = os.open
    changed = False
    calls = 0
    late: list[str] = []

    def revoke() -> None:
        nonlocal changed
        permission.write_bytes(permission.read_bytes())
        changed = True

    def metadata(**kwargs: Any) -> Any:
        result = original_prepare(**kwargs)
        if timing == "after_metadata":
            revoke()
        return result

    def inputs(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if timing == "second_capture_inputs" and calls == 2:
            revoke()
        return original_inputs(*args, **kwargs)

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        fd = original_open(path, flags, *args, **kwargs)
        if changed and str(path).endswith(".body") and not flags & os.O_DIRECTORY:
            late.append(str(path))
        return fd

    monkeypatch.setattr(validation, "prepare_capsule_metadata", metadata)
    monkeypatch.setattr(validation, "_full_evidence_inputs", inputs)
    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {opened})
    with pytest.raises(ValueError, match="changed"):
        validation.prepare_capsule(**linked_inputs)
    assert changed
    assert not late, "Current permission drift must stop the next native metadata body"
