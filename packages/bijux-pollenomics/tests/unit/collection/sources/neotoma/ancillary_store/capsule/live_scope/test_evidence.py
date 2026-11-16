"""Complete source proof hashing still requires live current metadata obligations."""

import json
from pathlib import Path
from typing import Any

import pytest


def test_scope_drift_during_full_evidence_pins_stops_next_body(
    scoped_inputs: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.seals import (
        context_seals,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.validation import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.linked_evidence.sources import (
        _full_evidence_inputs,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        authority,
    )

    context = load_neotoma_ancillary_context(
        scoped_inputs["context_directory"],
        expected_manifest_sha256=scoped_inputs["expected_context_sha256"],
        native_archive_directory=scoped_inputs["native_archive_directory"],
    )
    directory = next(iter(scoped_inputs["linked_captures"].values()))
    control = json.loads((directory / "request-plan.json").read_bytes())
    roots = set(scoped_inputs["predecessor_facets"].values())
    permission = scoped_inputs["context_directory"] / "manifest.json"
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read

    original = _read
    mutated = False
    after_drift: list[Path] = []

    def read(path: Path, bound: int) -> bytes:
        nonlocal mutated
        raw = original(path, bound)
        if path.parent in roots and path.suffix == ".body":
            if mutated:
                after_drift.append(path)
            else:
                permission.write_bytes(permission.read_bytes() + b"\n")
                mutated = True
        return raw

    monkeypatch.setattr(authority, "_read", read)
    with pytest.raises(ValueError), context_seals(scoped_inputs) as guard:
        _full_evidence_inputs(
            control,
            context,
            scoped_inputs["evidence_sources"],
            scoped_inputs["predecessor_facets"],
            _before_body_read=guard.check,
        )
    assert mutated
    assert after_drift == []


def test_legacy_link_discovery_keeps_live_current_context(
    capsule_inputs: dict[str, Any], monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.seals import (
        context_seals,
    )
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.validation import (
        load_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        qualification,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.replay import (
        _replay_linked_resources,
    )

    context = load_neotoma_ancillary_context(
        capsule_inputs["context_directory"],
        expected_manifest_sha256=capsule_inputs["expected_context_sha256"],
        native_archive_directory=capsule_inputs["native_archive_directory"],
    )
    pin, directory = next(iter(capsule_inputs["linked_captures"].items()))
    control = json.loads((directory / "request-plan.json").read_bytes())
    sources = {
        pin: capsule_inputs["facet_captures"][pin]
        for pin in control["plan"]["source_facet_manifest_sha256s"]
    }
    permission = capsule_inputs["context_directory"] / "manifest.json"
    import os

    from bijux_pollenomics.collection.sources.neotoma.capture.facets.replay import (
        _read_authenticated_facet_body,
    )

    original = _read_authenticated_facet_body
    opened = os.open
    mutated = False
    after_drift: list[str] = []

    def read(*args: Any, **kwargs: Any) -> Any:
        nonlocal mutated
        result = original(*args, **kwargs)
        if not mutated:
            permission.write_bytes(permission.read_bytes() + b"\n")
            mutated = True
        return result

    def observe(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        fd = opened(path, flags, *args, **kwargs)
        if (
            mutated
            and not flags & os.O_DIRECTORY
            and "-facet-" in Path(path).name
            and Path(path).suffix == ".body"
        ):
            after_drift.append(str(path))
        return fd

    monkeypatch.setattr(qualification, "_read_authenticated_facet_body", read)
    monkeypatch.setattr(os, "open", observe)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {observe})
    with pytest.raises(ValueError), context_seals(capsule_inputs) as guard:
        _replay_linked_resources(
            directory,
            expected_manifest_sha256=pin,
            source_facets=sources,
            scope_inputs=context.current_scope_inputs,
            legacy_rosters=context.legacy_rosters,
            _before_body_read=guard.check,
        )
    assert mutated
    assert after_drift == []
