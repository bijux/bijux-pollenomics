"""A complete frozen roster and every known protected dependency precede GETs."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from .native_products import products


def authenticate(inputs: dict[str, Any]) -> dict[str, Any]:
    module = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.authority"
    )
    return cast(dict[str, Any], module.authenticate_linked_source_scope(**inputs))


def test_complete_slot_authority_preserves_protected_shared_contact(
    tmp_path: Path,
) -> None:
    inputs = products(tmp_path)
    result = authenticate(inputs)
    assert result["resource_count"] == 3 and result["facet_slot_count"] == 24
    assert (
        result["protected_contacts"]["900"]["exposure_role"]
        == "heldout_no_numerical_access"
    )
    witnesses = result["protected_contacts"]["900"]["metadata_witnesses"]
    assert len(witnesses) == 1
    assert witnesses[0]["root_dataset_id"] == 202
    assert witnesses[0]["json_pointer"].endswith("/datasetpi/0/contactid")
    assert witnesses[0]["native_contactid"] == 900
    assert result["scientific_admission"] == "not_asserted"


def test_missing_source_capture_cannot_erase_complete_known_scope(
    tmp_path: Path,
) -> None:
    inputs = products(tmp_path)
    inputs["source_facets"] = {}
    with pytest.raises(ValueError, match="scope|source|population"):
        authenticate(inputs)


def test_rehashed_truncated_roster_cannot_replace_original_anchor(
    tmp_path: Path,
) -> None:
    inputs = products(tmp_path)
    path = inputs["scope"].roster_path
    source = json.loads(path.read_bytes())
    source["resources"] = source["resources"][:-1]
    source["resource_count"] = len(source["resources"])
    path.write_text(json.dumps(source))
    assert sha256(path.read_bytes()).hexdigest() != inputs["expected_roster_sha256"]
    with pytest.raises(ValueError, match="identity|roster|digest"):
        authenticate(inputs)


@pytest.mark.parametrize("native_pi", [True, False, 0, -1, 900.0, "900"])
def test_invalid_protected_native_pi_refuses_before_facet_body_access(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    native_pi: Any,
) -> None:
    inputs = products(tmp_path, native_pi=native_pi)
    original = capture_opening()
    numerical = set(inputs["source_facets"].values())
    opened = []

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.parent in numerical and path.suffix == ".body":
            opened.append(path)
            pytest.fail(
                "Protected metadata identity was deferred until facet body access"
            )
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    with pytest.raises(ValueError, match="native|positive|identifier"):
        authenticate(inputs)
    assert opened == []


def test_explicit_null_pi_is_not_an_invented_contact_dependency(tmp_path: Path) -> None:
    result = authenticate(products(tmp_path, native_pi=None))
    assert result["protected_contacts"] == {}
    assert result["facet_slot_count"] == 24


def test_missing_last_facet_cannot_pretend_complete_scope(tmp_path: Path) -> None:
    inputs = products(tmp_path)
    directory = next(iter(inputs["source_facets"].values()))
    path = directory / "capture-manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["facets"].pop()
    raw = json.dumps(manifest).encode()
    path.write_bytes(raw)
    inputs["source_facets"] = {sha256(raw).hexdigest(): directory}
    with pytest.raises(ValueError, match="scope|population|namespace"):
        authenticate(inputs)


def test_legacy_wire_requires_its_original_roster_resolver(tmp_path: Path) -> None:
    from .native_products import legacy_facets

    inputs = legacy_facets(products(tmp_path))
    with pytest.raises(ValueError, match="legacy|original roster"):
        authenticate(inputs)


def test_legacy_original_roster_is_an_explicit_additional_source(
    tmp_path: Path,
) -> None:
    from .native_products import legacy_facets

    inputs = legacy_facets(products(tmp_path))
    inputs["legacy_rosters"] = {
        inputs["expected_roster_sha256"]: inputs["scope"].roster_path
    }
    result = authenticate(inputs)
    assert result["legacy_roster_sha256s"] == [inputs["expected_roster_sha256"]]
    assert all(
        row["parent_scope_verification"] == "not_recorded_legacy_capture"
        for row in result["source_captures"].values()
    )
    assert result["facet_slot_count"] == 24
