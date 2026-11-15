"""A unit endpoint requires all current native siblings and protected-site duties."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    capture_neotoma_metadata,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.models import (
    NeotomaResourceLimits,
)

from ..resources.native_payloads import response


def owner() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.unit_resources"
    )


def write(path: Path, value: Any) -> str:
    content = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    path.write_bytes(content)
    return sha256(content).hexdigest()


def prepared(
    root: Path,
    *,
    protected: bool = False,
    complete_inventory: bool = True,
) -> tuple[Any, Path, dict[str, Path]]:
    def dataset(identity: int, kind: str) -> dict[str, Any]:
        return {"datasetid": identity, "datasettype": kind, "database": "SISAL"}

    rows: list[dict[str, Any]] = [
        {
            "site": {
                "siteid": 12,
                "collectionunitid": 100,
                "datasets": [
                    dataset(201, "speleothem"),
                    dataset(202, "geochronologic"),
                ],
            }
        }
    ]
    if protected:
        rows.append(
            {
                "site": {
                    "siteid": 12,
                    "collectionunitid": 101,
                    "datasets": [dataset(203, "geochronologic")],
                }
            }
        )
    if not complete_inventory:
        for row in rows:
            for native in row["site"]["datasets"]:
                native["datasettype"] = "pollen"
    directory = root / "metadata"
    captured = capture_neotoma_metadata(
        directory,
        plan=NeotomaMetadataPlan(
            inventory_bbox=(10, 50, 20, 70),
            inventory_limits=(10000,),
            inventory_all_dataset_types=complete_inventory,
        ),
        fetch=lambda url, **k: response(
            url, json.dumps({"status": "success", "data": rows}).encode()
        ),
    )
    manifest = json.loads((directory / "capture-manifest.json").read_bytes())
    reference = manifest["records"][0]
    receipt = json.loads((directory / reference["receipt_file"]).read_bytes())
    resources = []
    for index, row in enumerate(rows):
        for child_index, native in enumerate(row["site"]["datasets"]):
            role = (
                "heldout_no_numerical_access"
                if native["datasetid"] == 203
                else "development_resource_discovery"
            )
            resources.append(
                {
                    "dataset_id": native["datasetid"],
                    "site_id": 12,
                    "collection_unit_id": row["site"]["collectionunitid"],
                    "dataset_type": native["datasettype"],
                    "database": native["database"],
                    "exposure_roles": {"current": role, "doi_frozen": role},
                    "metadata_locator": {
                        "capture_manifest_sha256": captured.manifest_sha256,
                        "body_file": receipt["body_file"],
                        "body_sha256": receipt["retained_body_sha256"],
                        "response_sha256": receipt["retained_body_sha256"],
                        "receipt_file": reference["receipt_file"],
                        "receipt_sha256": reference["receipt_sha256"],
                        "json_pointer": f"/data/{index}/site/datasets/{child_index}",
                    },
                }
            )
    roster = root / "inventory.json"
    roster_sha = write(
        roster,
        {
            "resources": resources,
            "resource_count": len(resources),
            "source_metadata_capture_manifest_sha256": [captured.manifest_sha256],
            "policy_sources": [
                "https://www.neotomadb.org/data/data-use-and-embargo-policy"
            ],
        },
    )
    plan = owner().NeotomaUnitResourcePlan(
        (100,), roster_sha, (captured.manifest_sha256,)
    )
    return plan, roster, {captured.manifest_sha256: directory}


def limits() -> NeotomaResourceLimits:
    return NeotomaResourceLimits(
        max_requests=1,
        max_attempts=1,
        max_response_bytes=4096,
        max_total_bytes=8192,
        timeout_seconds=5,
        wall_seconds=20,
        retry_delay_seconds=0,
    )


def test_exact_unit_request_preserves_both_native_siblings_and_opaque_body(
    tmp_path: Path,
) -> None:
    plan, roster, sources = prepared(tmp_path)
    original = {
        p: p.read_bytes() for directory in sources.values() for p in directory.iterdir()
    }
    calls = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return response(
            url, b'{"status":"success","data":[[{"collectionunitid":999}]]}'
        )

    result = owner().capture_neotoma_unit_resources(
        tmp_path / "units",
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=fetch,
    )
    assert calls == ["https://api.neotomadb.org/v2.0/data/speleothems/100"]
    assert result.partitions == {"received_complete_unqualified_unit_resource": 1}
    scope = result.units[0]["identity"]
    assert scope["collection_unit_id"] == 100 and scope["site_id"] == 12
    assert scope["native_dataset_ids"] == [201, 202]
    assert {r["dataset_id"] for r in scope["roster_obligations"]} == {201, 202}
    assert result.units[0]["summary"]["payload_owner_status"] == "not_established"
    assert result.units[0]["scientific_admission"] == "not_asserted"
    assert original == {
        p: p.read_bytes() for directory in sources.values() for p in directory.iterdir()
    }


def test_protected_same_site_sibling_blocks_unit_before_get_or_body_read(
    tmp_path: Path,
) -> None:
    plan, roster, sources = prepared(tmp_path, protected=True)
    result = owner().capture_neotoma_unit_resources(
        tmp_path / "units",
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=lambda *a, **k: pytest.fail("protected unit reached HTTP"),
    )
    assert result.partitions == {"not_attempted_exposure_role": 1}
    assert result.units[0]["identity"]["exposure_role"] == "heldout_no_numerical_access"
    assert len(result.units[0]["identity"]["roster_obligations"]) == 3
    with pytest.raises(ValueError, match="role"):
        owner().read_neotoma_unit_body(
            tmp_path / "units",
            expected_manifest_sha256=result.manifest_sha256,
            unit_key="speleothem-unit-100",
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
        )
    assert not list((tmp_path / "units").glob("*.body"))


@pytest.mark.parametrize(
    "damage",
    [
        "drop_sibling",
        "foreign_site",
        "foreign_type",
        "foreign_database",
        "pointer",
        "receipt_tuple",
        "boolean_id",
        "coerced_id",
        "duplicate_id",
    ],
)
def test_rehashed_roster_cannot_guess_a_partial_or_foreign_native_unit(
    tmp_path: Path, damage: str
) -> None:
    plan, roster, sources = prepared(tmp_path)
    value = json.loads(roster.read_bytes())
    row = value["resources"][0]
    if damage == "drop_sibling":
        value["resources"].pop()
        value["resource_count"] -= 1
    elif damage == "foreign_site":
        row["site_id"] = 13
    elif damage == "foreign_type":
        row["dataset_type"] = "pollen"
    elif damage == "foreign_database":
        row["database"] = None
    elif damage == "pointer":
        row["metadata_locator"]["json_pointer"] = "/data/0/site/datasets/1"
    elif damage == "receipt_tuple":
        row["metadata_locator"]["receipt_sha256"] = "f" * 64
    elif damage == "boolean_id":
        row["dataset_id"] = True
    elif damage == "coerced_id":
        row["collection_unit_id"] = "100"
    else:
        value["resources"][1]["dataset_id"] = 201
    plan = replace(plan, roster_sha256=write(roster, value))
    with pytest.raises(ValueError):
        owner().capture_neotoma_unit_resources(
            tmp_path / "units",
            plan=plan,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail("unverified unit GET"),
        )


def test_pollen_filtered_inventory_cannot_prove_whole_unit_scope(
    tmp_path: Path,
) -> None:
    plan, roster, sources = prepared(tmp_path, complete_inventory=False)
    with pytest.raises(ValueError, match="all.type|scope|inventory"):
        owner().capture_neotoma_unit_resources(
            tmp_path / "units",
            plan=plan,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail(
                "filtered inventory opened unit endpoint"
            ),
        )


@pytest.mark.parametrize("unit", [True, 1.5, "100", 0, 999])
def test_selected_unit_identity_is_strict_and_source_bound(
    tmp_path: Path, unit: Any
) -> None:
    plan, roster, sources = prepared(tmp_path)
    with pytest.raises(ValueError):
        owner().capture_neotoma_unit_resources(
            tmp_path / "units",
            plan=replace(plan, collection_unit_ids=(unit,)),
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail("invalid unit reached HTTP"),
        )


@pytest.mark.parametrize("status", [404, 429, 500])
def test_source_http_refusals_retain_bytes_without_unit_absence_claim(
    tmp_path: Path, status: int
) -> None:
    plan, roster, sources = prepared(tmp_path)
    result = owner().capture_neotoma_unit_resources(
        tmp_path / "units",
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=lambda url, **k: response(url, b'{"error":"failed"}', status=status),
    )
    assert result.partitions == {"unavailable_http": 1}
    assert result.units[0]["absence_certified"] is False


def test_existing_output_is_preserved(tmp_path: Path) -> None:
    plan, roster, sources = prepared(tmp_path)
    output = tmp_path / "units"
    output.mkdir()
    (output / "owned").write_text("existing")
    with pytest.raises(FileExistsError):
        owner().capture_neotoma_unit_resources(
            output,
            plan=plan,
            roster_path=roster,
            metadata_captures=sources,
            limits=limits(),
            fetch=lambda *a, **k: pytest.fail("existing output GET"),
        )
    assert (output / "owned").read_text() == "existing"


@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_either_version_of_native_sibling_retains_its_protection(
    tmp_path: Path, role: str
) -> None:
    plan, roster, sources = prepared(tmp_path)
    value = json.loads(roster.read_bytes())
    value["resources"][1]["exposure_roles"]["doi_frozen"] = role
    plan = replace(plan, roster_sha256=write(roster, value))
    result = owner().capture_neotoma_unit_resources(
        tmp_path / "units",
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=lambda *a, **k: pytest.fail("protected version opened whole unit"),
    )
    assert result.units[0]["identity"]["exposure_role"] == role
    assert result.partitions == {"not_attempted_exposure_role": 1}


def test_historical_only_unit_member_keeps_obligation_without_fabricated_current_row(
    tmp_path: Path,
) -> None:
    plan, roster, sources = prepared(tmp_path)
    value = json.loads(roster.read_bytes())
    value["resources"].append(
        {
            **value["resources"][0],
            "dataset_id": 299,
            "exposure_roles": {
                "current": "heldout_no_numerical_access",
                "doi_frozen": "heldout_no_numerical_access",
            },
            "metadata_locator": {
                "source_kind": "retained_relational_dataset_metadata_not_current_HTTP"
            },
        }
    )
    value["resource_count"] += 1
    plan = replace(plan, roster_sha256=write(roster, value))
    result = owner().capture_neotoma_unit_resources(
        tmp_path / "units",
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=lambda *a, **k: pytest.fail("historical protection dropped"),
    )
    scope = result.units[0]["identity"]
    assert scope["native_dataset_ids"] == [201, 202]
    assert {r["dataset_id"] for r in scope["roster_obligations"]} == {201, 202, 299}
    assert result.partitions == {"not_attempted_exposure_role": 1}


def test_unit_transport_failure_retains_exact_site_bound_request(
    tmp_path: Path,
) -> None:
    plan, roster, sources = prepared(tmp_path)

    def timeout(*args: Any, **kwargs: Any) -> Any:
        raise TimeoutError("bounded unit timeout")

    result = owner().capture_neotoma_unit_resources(
        tmp_path / "units",
        plan=plan,
        roster_path=roster,
        metadata_captures=sources,
        limits=limits(),
        fetch=timeout,
    )
    assert result.partitions == {"transport_failure": 1}
    reference = result.units[0]["attempts"][0]
    receipt = json.loads((tmp_path / "units" / reference["receipt_file"]).read_bytes())
    assert receipt["expected_site_id"] == 12
    assert receipt["requested_url"].endswith("/speleothems/100")
    assert result.request_count == 1 and result.response_bytes == 0
