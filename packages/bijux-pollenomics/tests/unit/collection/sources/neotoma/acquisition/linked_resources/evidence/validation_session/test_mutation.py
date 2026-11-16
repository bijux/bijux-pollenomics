"""Live permission and complete capture-boundary seals precede detail-body access."""

from dataclasses import replace
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import replay
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.session import (
    _LinkedEvidenceSession,
)

from .native_products import observe_work, session_arguments
from .test_scope import inputs


@pytest.mark.parametrize(
    "member", ["roster", "metadata", "facet", "evidence", "capture"]
)
def test_equal_bytes_inode_replacement_refuses_at_capture_boundary(
    session_products: dict[str, Any], monkeypatch: Any, member: str
) -> None:
    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    scope = next(iter(arguments["scope_inputs"].values()))
    if member == "roster":
        path = scope.roster_path
    elif member == "metadata":
        path = next(iter(scope.metadata_captures.values())) / "capture-manifest.json"
    elif member == "facet":
        path = next(iter(owner.source_facets.values())) / "capture-manifest.json"
    elif member == "capture":
        path = next(iter(owner.capture_sources.values())) / "capture-manifest.json"
    else:
        path = owner.evidence.directory / "evidence-manifest.json"
    work = observe_work(monkeypatch)
    with (
        pytest.raises(ValueError, match="changed"),
        _LinkedEvidenceSession(**arguments) as session,
    ):
        replacement = path.with_suffix(".replacement")
        replacement.write_bytes(path.read_bytes())
        replacement.replace(path)
        session.check(**inputs(arguments), full=True)
    assert work["native_detail_opens"] == 0


@pytest.mark.parametrize(
    "member", ["roster", "metadata", "context", "native_catalogue"]
)
def test_permission_drift_between_targets_refuses_next_detail(
    session_products: dict[str, Any], monkeypatch: Any, member: str
) -> None:
    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    scope = next(iter(arguments["scope_inputs"].values()))
    permission = {
        "roster": scope.roster_path,
        "metadata": next(iter(scope.metadata_captures.values()))
        / "capture-manifest.json",
        "context": owner.context_directory / "manifest.json",
        "native_catalogue": owner.native_archive_directory / "catalogue/manifest.json",
    }[member]
    pin, directory = next(
        (pin, path)
        for pin, path in owner.capture_sources.items()
        if path.name == "later-details"
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read

    original = _read
    mutated: list[Path] = []
    work = observe_work(monkeypatch)
    with (
        pytest.raises(ValueError, match="changed"),
        _LinkedEvidenceSession(**arguments) as session,
    ):

        def read(path: Path, bound: int) -> bytes:
            raw = original(path, bound)
            if path.suffix == ".body" and not mutated:
                permission.write_bytes(permission.read_bytes())
                mutated.append(path)
            return raw

        monkeypatch.setattr(replay, "_read", read)
        replay._replay_linked_resources(
            directory,
            expected_manifest_sha256=pin,
            source_facets=owner.source_facets,
            evidence=owner.evidence,
            scope_inputs=arguments["scope_inputs"],
            legacy_rosters=arguments["legacy_rosters"],
            _session=session,
            _operation=arguments["operation"],
        )
    assert len(mutated) == 1
    assert work["native_detail_opens"] == 1


def test_owner_resolver_mutation_refuses_before_any_detail(
    session_products: dict[str, Any], monkeypatch: Any
) -> None:
    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    work = observe_work(monkeypatch)
    with (
        pytest.raises(ValueError, match="identity changed"),
        _LinkedEvidenceSession(**arguments) as session,
    ):
        owner.capture_sources["0" * 64] = next(iter(owner.capture_sources.values()))
        session.check(**inputs(arguments))
    assert work["native_detail_opens"] == 0


@pytest.mark.parametrize("after", ["first_body", "next_receipt"])
def test_permission_drift_between_retries_refuses_next_body(
    session_products: dict[str, Any], monkeypatch: Any, tmp_path: Path, after: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
        capture_neotoma_linked_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        DEFAULT_RESOURCE_LIMITS,
    )

    from ....resources.native_payloads import response

    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    directory = tmp_path / "retried-details"
    calls: list[str] = []

    def fetch(url: str, **_: Any) -> Any:
        calls.append(url)
        return response(
            url,
            json.dumps(session_products["native"]["taxon-11"]).encode(),
            500 if len(calls) == 1 else 200,
        )

    captured = capture_neotoma_linked_resources(
        directory,
        plan=NeotomaLinkedResourcePlan(
            tuple(sorted(owner.source_facets)),
            (NeotomaLinkedTarget("taxon", 11),),
            include_higher_taxa=True,
        ),
        source_facets=owner.source_facets,
        scope_inputs=arguments["scope_inputs"],
        evidence=owner.evidence,
        fetch=fetch,
        limits=replace(DEFAULT_RESOURCE_LIMITS, retry_delay_seconds=0),
    )
    assert len(calls) == 2
    owner = replace(owner, capture_sources={captured.manifest_sha256: directory})
    arguments["source_owner"] = owner
    permission = next(iter(arguments["scope_inputs"].values())).roster_path
    bodies: list[str] = []
    mutated = False

    def read(path: Path, bound: int) -> bytes:
        nonlocal mutated
        raw = _read(path, bound)
        if path.parent == directory:
            if path.suffix == ".body":
                bodies.append(path.name)
            trigger = (
                path.suffix == ".body"
                if after == "first_body"
                else path.name.endswith("attempt-2.receipt.json")
            )
            if trigger and not mutated:
                permission.write_bytes(permission.read_bytes())
                mutated = True
        return raw

    with (
        pytest.raises(ValueError, match="changed"),
        _LinkedEvidenceSession(**arguments) as session,
    ):
        monkeypatch.setattr(replay, "_read", read)
        replay._replay_linked_resources(
            directory,
            expected_manifest_sha256=captured.manifest_sha256,
            source_facets=owner.source_facets,
            evidence=owner.evidence,
            scope_inputs=arguments["scope_inputs"],
            legacy_rosters=arguments["legacy_rosters"],
            _session=session,
            _operation=arguments["operation"],
        )
    assert mutated
    assert bodies == ["taxon-11-current-attempt-1.body"]


@pytest.mark.parametrize("stage", ["initial_snapshot", "final_snapshot", "parse"])
def test_public_derivation_guards_snapshot_and_parse_body_reads(
    session_products: dict[str, Any], monkeypatch: Any, stage: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry import (
        derive_neotoma_taxon_ancestry,
        proofs,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.replay import (
        _replay_linked_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read

    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    permission = next(iter(arguments["scope_inputs"].values())).roster_path
    original_read = _read
    original_snapshot = proofs.capture_snapshot
    original_replay = _replay_linked_resources
    phase = ""
    snapshots = 0
    mutated = False
    after_drift: list[Path] = []

    def snapshot(*args: Any, **kwargs: Any) -> Any:
        nonlocal phase, snapshots
        snapshots += 1
        phase = "initial_snapshot" if snapshots == 1 else "final_snapshot"
        try:
            return original_snapshot(*args, **kwargs)
        finally:
            phase = ""

    def replay_and_revoke(*args: Any, **kwargs: Any) -> Any:
        nonlocal phase, mutated
        result = original_replay(*args, **kwargs)
        phase = "parse"
        if stage == "parse" and not mutated:
            permission.write_bytes(permission.read_bytes())
            mutated = True
        return result

    def read(path: Path, bound: int) -> bytes:
        nonlocal mutated
        raw = original_read(path, bound)
        if path.suffix == ".body":
            if mutated:
                after_drift.append(path)
            if phase == stage and not mutated:
                permission.write_bytes(permission.read_bytes())
                mutated = True
        return raw

    monkeypatch.setattr(proofs, "capture_snapshot", snapshot)
    monkeypatch.setattr(proofs, "_replay_linked_resources", replay_and_revoke)
    monkeypatch.setattr(proofs, "_read", read)
    with pytest.raises(ValueError, match="changed"):
        derive_neotoma_taxon_ancestry(owner)
    assert mutated
    assert after_drift == []
