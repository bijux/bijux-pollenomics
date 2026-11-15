"""Whole native parent duties are established before any facet source access."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
    capture_neotoma_dataset_facets,
)

from ...resources.native_payloads import response, spec
from .native_sources import source_inputs


def _record_response(calls: list[str], url: str, body: bytes) -> Any:
    calls.append(url)
    return response(url, body)


def test_new_capture_refuses_omitted_scope_before_output_or_fetch(
    tmp_path: Path,
) -> None:
    from ..native_payloads import plan

    calls: list[str] = []
    capture_without_static_signature: Any = capture_neotoma_dataset_facets
    with pytest.raises((TypeError, ValueError), match="scope"):
        capture_without_static_signature(
            tmp_path / "facets",
            plan=plan(spec()),
            fetch=lambda url, **_: _record_response(
                calls, url, b'{"status":"success","data":[]}'
            ),
        )
    assert calls == []
    assert not (tmp_path / "facets").exists()
    assert not (tmp_path / ".facets.staging").exists()


@pytest.mark.parametrize("relation", ["same_core", "same_site", "known_model"])
@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_protected_parent_scope_records_zero_get_refusal(
    tmp_path: Path, relation: str, role: str
) -> None:
    sibling = spec(202, role=role)
    groups = None
    if relation == "same_site":
        sibling = replace(sibling, collection_unit_id=101)
    elif relation == "known_model":
        sibling = replace(sibling, site_id=13, collection_unit_id=101)
        groups = [{"dataset_ids": [201, 202], "relation": "known_shared_chronology"}]
    plan, scope = source_inputs(
        tmp_path / "inputs",
        (spec(), sibling),
        selected=(201,),
        dependency_groups=groups,
    )
    calls: list[str] = []
    captured = capture_neotoma_dataset_facets(
        tmp_path / "facets",
        plan=plan,
        scope=scope,
        fetch=lambda url, **_: _record_response(calls, url, b"{}"),
    )
    assert calls == []
    assert captured.request_count == 0
    assert captured.partitions == {"not_attempted_parent_scope": 1}
    assert (
        captured.facets[0]["root_identity"]["exposure_role"]
        == "development_resource_discovery"
    )
    assert captured.facets[0]["parent_scope_role"] == role


@pytest.mark.parametrize(
    "damage",
    [
        "roster_sha",
        "receipt",
        "body",
        "native_parent",
        "native_database",
        "locator",
        "missing_capture",
        "late_role",
    ],
)
def test_authentication_failure_precedes_source_and_output(
    tmp_path: Path, damage: str
) -> None:
    plan, scope = source_inputs(tmp_path / "inputs", (spec(), spec(202)))
    if damage == "roster_sha":
        scope.roster_path.write_text("{}")
    elif damage == "late_role":
        value = json.loads(scope.roster_path.read_bytes())
        value["resources"][-1]["exposure_roles"]["doi_frozen"] = "unknown"
        scope.roster_path.write_text(json.dumps(value))
        from hashlib import sha256

        plan = replace(
            plan, roster_sha256=sha256(scope.roster_path.read_bytes()).hexdigest()
        )
    else:
        root = next(iter(scope.metadata_captures.values()))
        if damage == "missing_capture":
            scope = replace(scope, metadata_captures={})
        elif damage == "receipt":
            next(root.glob("*.receipt.json")).write_text("{}")
        elif damage == "body":
            next(root.glob("*.body")).write_text("{}")
        else:
            value = json.loads(scope.roster_path.read_bytes())
            row = value["resources"][0]
            if damage == "native_parent":
                row["collection_unit_id"] = 999
            elif damage == "native_database":
                row["database"] = "foreign"
            else:
                row["metadata_locator"]["receipt_sha256"] = "0" * 64
            scope.roster_path.write_text(json.dumps(value))
            from hashlib import sha256

            plan = replace(
                plan, roster_sha256=sha256(scope.roster_path.read_bytes()).hexdigest()
            )
    calls: list[str] = []
    with pytest.raises(ValueError):
        capture_neotoma_dataset_facets(
            tmp_path / "facets",
            plan=plan,
            scope=scope,
            fetch=lambda url, **_: _record_response(calls, url, b"{}"),
        )
    assert calls == []
    assert not (tmp_path / ".facets.staging").exists()


def test_scoped_capture_keeps_native_bytes_and_current_root_role(
    tmp_path: Path,
) -> None:
    plan, scope = source_inputs(tmp_path / "inputs", (spec(),))
    body = b'{"status":"success","data":[],"message":"native bytes"}'
    result = capture_neotoma_dataset_facets(
        tmp_path / "facets",
        plan=plan,
        scope=scope,
        fetch=lambda url, **_: response(url, body),
    )
    assert result.request_count == 1
    assert next((tmp_path / "facets").glob("*.body")).read_bytes() == body
    assert (tmp_path / "facets" / "parent-scope.json").is_file()


@pytest.mark.parametrize("alias", ["sitename", "geography"])
def test_known_native_alias_inherits_protected_role(tmp_path: Path, alias: str) -> None:
    values = (
        {"sitename": "Native site 12"}
        if alias == "sitename"
        else {"geography": json.dumps({"type": "Point", "coordinates": [12, 60]})}
    )
    plan, scope = source_inputs(
        tmp_path / "inputs",
        (
            spec(),
            replace(
                spec(202, role="heldout_no_numerical_access"),
                site_id=13,
                collection_unit_id=101,
            ),
        ),
        selected=(201,),
        site_overrides={13: values},
    )
    result = capture_neotoma_dataset_facets(
        tmp_path / "facets",
        plan=plan,
        scope=scope,
        fetch=lambda *_, **__: pytest.fail("Protected alias used source transport"),
    )
    assert result.partitions == {"not_attempted_parent_scope": 1}
    assert result.request_count == 0


@pytest.mark.parametrize("identity", [True, 202.5, 0, -1, "202"])
def test_invalid_late_resource_identity_refuses_before_output(
    tmp_path: Path, identity: object
) -> None:
    plan, scope = source_inputs(tmp_path / "inputs", (spec(),))
    invalid = replace(plan.resources[0], dataset_id=cast(Any, identity))
    plan = replace(plan, resources=(plan.resources[0], invalid))
    with pytest.raises(ValueError):
        capture_neotoma_dataset_facets(
            tmp_path / "facets",
            plan=plan,
            scope=scope,
            fetch=lambda *_, **__: pytest.fail(
                "Invalid late identity used source transport"
            ),
        )
    assert not (tmp_path / ".facets.staging").exists()


@pytest.mark.parametrize(
    "damage",
    [
        "frozen_role",
        "omitted_sibling",
        "missing_locator",
        "invalid_dependency",
        "missing_scope",
    ],
)
def test_complete_scope_cannot_be_omitted_or_downgraded(
    tmp_path: Path, damage: str
) -> None:
    from hashlib import sha256

    plan, scope = source_inputs(
        tmp_path / "inputs", (spec(), spec(202)), selected=(201,)
    )
    roster = json.loads(scope.roster_path.read_bytes())
    if damage == "frozen_role":
        roster["resources"][1]["exposure_roles"]["doi_frozen"] = (
            "reserved_candidate_confirmation"
        )
    elif damage == "omitted_sibling":
        roster["resources"].pop()
        roster["resource_count"] = 1
    elif damage == "missing_locator":
        del roster["resources"][0]["metadata_locator"]
    elif damage == "invalid_dependency":
        roster["source_dependency_groups"] = [
            {"dataset_ids": [201, 999], "relation": "known_shared_chronology"}
        ]
    scope.roster_path.write_text(json.dumps(roster))
    plan = replace(
        plan, roster_sha256=sha256(scope.roster_path.read_bytes()).hexdigest()
    )
    if damage == "missing_scope":
        scope = None

    def never(*_: Any, **__: Any) -> Any:
        pytest.fail("Protected or invalid scope used source transport")

    if damage == "frozen_role":
        result = capture_neotoma_dataset_facets(
            tmp_path / "facets", plan=plan, scope=scope, fetch=never
        )
        assert result.partitions == {"not_attempted_parent_scope": 1}
    else:
        with pytest.raises(ValueError):
            capture_neotoma_dataset_facets(
                tmp_path / "facets", plan=plan, scope=scope, fetch=never
            )
        assert not (tmp_path / ".facets.staging").exists()


@pytest.mark.parametrize(
    "geometry",
    [
        '{"type":"Point","coordinates":[12,60],"coordinates":[13,60]}',
        '{"type":"Point","coordinates":[1e-9999,60]}',
    ],
)
def test_lossy_encoded_geography_refuses_before_source_get(
    tmp_path: Path, geometry: str
) -> None:
    plan, scope = source_inputs(
        tmp_path / "inputs", (spec(),), site_overrides={12: {"geography": geometry}}
    )
    with pytest.raises(ValueError):
        capture_neotoma_dataset_facets(
            tmp_path / "facets",
            plan=plan,
            scope=scope,
            fetch=lambda *_, **__: pytest.fail(
                "Lossy native geography used source transport"
            ),
        )
    assert not (tmp_path / ".facets.staging").exists()


def test_filtered_inventory_cannot_certify_full_native_parent_population(
    tmp_path: Path,
) -> None:
    plan, scope = source_inputs(
        tmp_path / "inputs", (spec(),), inventory_all_dataset_types=False
    )
    with pytest.raises(ValueError, match="parent population"):
        capture_neotoma_dataset_facets(
            tmp_path / "facets",
            plan=plan,
            scope=scope,
            fetch=lambda *_, **__: pytest.fail(
                "Filtered-only metadata used source transport"
            ),
        )
    assert not (tmp_path / ".facets.staging").exists()


@pytest.mark.parametrize(
    "damage",
    [None, "missing_part", "wrong_lookup_id", "missing_empty", "wrong_outer_id"],
)
def test_historical_availability_root_retains_original_owner_and_empty_lookup(
    tmp_path: Path, damage: str | None
) -> None:
    from hashlib import sha256

    from .native_sources import historical_inputs

    plan, scope = historical_inputs(tmp_path / "inputs")
    if damage == "missing_part":
        scope = replace(scope, historical_metadata_parts={})
    elif damage is not None:
        roster = json.loads(scope.roster_path.read_bytes())
        row = roster["resources"][1]
        if damage == "wrong_lookup_id":
            row["current_metadata_lookup"]["dataset_id"] = 999
        elif damage == "missing_empty":
            del row["current_metadata_lookup"]["successful_empty"]
        else:
            part = next(iter(scope.historical_metadata_parts.values()))
            value = json.loads(part.read_bytes())
            value["rows"][0]["source_dataset_id"] = 999
            part.write_text(json.dumps(value))
            digest = sha256(part.read_bytes()).hexdigest()
            row["metadata_locator"]["response_sha256"] = digest
            scope = replace(scope, historical_metadata_parts={digest: part})
            plan = replace(
                plan, resources=(replace(plan.resources[0], metadata_sha256=digest),)
            )
        scope.roster_path.write_text(json.dumps(roster))
        plan = replace(
            plan, roster_sha256=sha256(scope.roster_path.read_bytes()).hexdigest()
        )
    calls: list[str] = []

    def fetch(url: str, **_: Any) -> Any:
        calls.append(url)
        return response(url, b'{"status":"success","data":[]}')

    if damage is None:
        result = capture_neotoma_dataset_facets(
            tmp_path / "facets", plan=plan, scope=scope, fetch=fetch
        )
        assert result.request_count == 1
        proof = json.loads((tmp_path / "facets" / "parent-scope.json").read_bytes())
        source = proof["parents"][0]["metadata_sources"][0]
        assert source["current_native_metadata_returned"] is False
        assert source["current_metadata_lookup"]["absence_certified"] is False
    else:
        with pytest.raises(ValueError):
            capture_neotoma_dataset_facets(
                tmp_path / "facets", plan=plan, scope=scope, fetch=fetch
            )
        assert calls == []


def test_scope_proof_size_bound_precedes_output_and_source_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
        scope as scope_owner,
    )

    plan, scope = source_inputs(tmp_path / "inputs", (spec(),))
    monkeypatch.setattr(scope_owner, "_MAX_SCOPE_BYTES", 32, raising=False)
    with pytest.raises(ValueError, match="scope.*bound"):
        capture_neotoma_dataset_facets(
            tmp_path / "facets",
            plan=plan,
            scope=scope,
            fetch=lambda *_, **__: pytest.fail(
                "Oversized scope proof used source transport"
            ),
        )
    assert not (tmp_path / ".facets.staging").exists()


@pytest.mark.parametrize(
    "representations",
    [("mapping", "mapping"), ("mapping", "encoded"), ("encoded", "mapping")],
)
def test_direct_and_encoded_native_geometry_share_protected_obligations(
    tmp_path: Path, representations: tuple[str, str]
) -> None:
    geometry = {"type": "Point", "coordinates": [12, 60]}
    sites = {
        site_id: {"geography": geometry if kind == "mapping" else json.dumps(geometry)}
        for site_id, kind in zip((12, 13), representations, strict=True)
    }
    plan, scope = source_inputs(
        tmp_path / "inputs",
        (
            spec(),
            replace(
                spec(202, role="heldout_no_numerical_access"),
                site_id=13,
                collection_unit_id=101,
            ),
        ),
        selected=(201,),
        site_overrides=sites,
    )
    result = capture_neotoma_dataset_facets(
        tmp_path / "facets",
        plan=plan,
        scope=scope,
        fetch=lambda *_, **__: pytest.fail(
            "Identical native geography used protected source transport"
        ),
    )
    assert result.request_count == 0
    assert result.partitions == {"not_attempted_parent_scope": 1}
    assert result.facets[0]["parent_scope_role"] == "heldout_no_numerical_access"


def test_mandatory_scope_model_is_available_from_public_facet_facade() -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture import facets
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.models import (
        NeotomaFacetScopeInputs,
    )

    assert getattr(facets, "NeotomaFacetScopeInputs", None) is NeotomaFacetScopeInputs
    assert "NeotomaFacetScopeInputs" in facets.__all__
