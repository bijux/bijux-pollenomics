"""Proof metadata and original inputs obey separate finite byte populations."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from .native_products import products


def owner() -> Any:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence"
    )


@pytest.mark.parametrize(
    "bound", ["PART_HARD_BYTES", "MAX_MANIFEST_BYTES", "MAX_EVIDENCE_BYTES"]
)
def test_underdeclared_publication_keeps_refusal_and_never_returns_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    bound: str,
) -> None:
    inputs = products(tmp_path)
    module = owner()
    monkeypatch.setattr(module, bound, 128)
    with pytest.raises(ValueError, match="budget|bound"):
        module.publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    assert not (tmp_path / "evidence").exists()
    assert (tmp_path / ".evidence.staging/refusal.json").is_file()


def test_replay_declared_global_budget_refuses_before_any_part_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = products(tmp_path)
    module = owner()
    result = module.publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    monkeypatch.setattr(module, "MAX_EVIDENCE_BYTES", 1)
    original = Path.open
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.parent == result.directory / "proofs":
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError, match="budget"):
        module.load_neotoma_linked_evidence(
            result.directory, expected_manifest_sha256=result.manifest_sha256, **inputs
        )
    assert opened == []


@pytest.mark.parametrize("value", [True, False, -1, 1.0, "1"])
def test_native_range_offsets_cannot_be_coerced(tmp_path: Path, value: Any) -> None:
    module = owner()
    result = module.publish_neotoma_linked_evidence(
        tmp_path / "evidence", **products(tmp_path)
    )
    path = result.directory / "evidence-manifest.json"
    index = json.loads(path.read_bytes())
    index["targets"]["taxon-11"]["proof_ranges"][0]["start"] = value
    raw = json.dumps(index).encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError, match="count|range"):
        module.read_neotoma_linked_evidence_target(
            result.directory,
            expected_manifest_sha256=sha256(raw).hexdigest(),
            kind="taxon",
            native_id=11,
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_authority",
        "slot_account",
        "missing_dependency",
        "downgraded_role",
        "role_kind",
    ],
)
def test_owned_authority_accounts_and_restrictive_dependencies_refuse_contradiction(
    tmp_path: Path,
    mutation: str,
) -> None:
    module = owner()
    result = module.publish_neotoma_linked_evidence(
        tmp_path / "evidence", **products(tmp_path)
    )
    path = result.directory / "evidence-manifest.json"
    index = json.loads(path.read_bytes())
    if mutation == "missing_authority":
        index["authority"] = {}
    elif mutation == "slot_account":
        index["authority"]["facet_slot_count"] = 1
    elif mutation == "missing_dependency":
        index["targets"]["contact-900"]["metadata_dependencies"] = []
    elif mutation == "downgraded_role":
        index["targets"]["contact-900"]["exposure_role"] = (
            "development_resource_discovery"
        )
    else:
        index["targets"]["contact-900"]["exposure_role"] = []
    raw = json.dumps(index).encode()
    path.write_bytes(raw)
    with pytest.raises(ValueError):
        module.read_neotoma_linked_evidence_target(
            result.directory,
            expected_manifest_sha256=sha256(raw).hexdigest(),
            kind="contact",
            native_id=900,
        )


def test_prospective_attempt_budget_refuses_before_unbounded_allocation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import (
        NeotomaLinkedResourcePlan,
        NeotomaLinkedTarget,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
        DEFAULT_RESOURCE_LIMITS,
    )

    inputs = products(tmp_path)
    evidence = owner().publish_neotoma_linked_evidence(tmp_path / "evidence", **inputs)
    protocol = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.protocol"
    )

    def guarded_range(count: int) -> range:
        assert count < 100000, "Unbounded prospective attempt allocation"
        return range(count)

    monkeypatch.setattr(protocol, "range", guarded_range, raising=False)
    plan = NeotomaLinkedResourcePlan(
        tuple(inputs["source_facets"]), (NeotomaLinkedTarget("taxon", 11),)
    )
    limits = replace(DEFAULT_RESOURCE_LIMITS, max_requests=10**12, max_attempts=10**12)
    with pytest.raises(ValueError, match="budget|bound"):
        protocol.prepare_scoped_targets(
            plan,
            inputs["source_facets"],
            limits,
            evidence=evidence,
            scope_inputs={inputs["expected_roster_sha256"]: inputs["scope"]},
        )
