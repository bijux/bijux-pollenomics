"""Genuine unit captures and independent native context for portability controls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
    write_neotoma_ancillary_context,
)
from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.unit_resources import (
    NeotomaUnitResourcePlan,
    capture_neotoma_unit_resources,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
    write_neotoma_resource_catalogue,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    write_neotoma_source_archive,
)

from ...acquisition.facets.parent_scope.native_sources import source_inputs
from ...acquisition.resources.native_payloads import spec


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def payload(unit: int) -> dict[str, Any]:
    site = 12 if unit == 100 else 13
    row = dict.fromkeys(
        (
            "rockage",
            "dripheight",
            "dripheightunits",
            "landusecoverpercent",
            "vegetationcoverpercent",
        )
    )
    row.update(
        siteid=site,
        collectionunitid=unit,
        entityid=unit + 1,
        entityname="Native entity",
        geology="Native geology",
        monitoring=False,
        speleothemtype="Native type",
        speleothemdriptype="Native drip",
        entitycovertype="Native cover",
        entitycoverthickness=3,
        entrancedistance=12,
        entrancedistanceunits=37,
        landusecovertype="Literal land use",
        vegetationcovertype="Literal vegetation",
    )
    return {
        "status": "success",
        "data": [{"speleothem": row}],
        "message": "Retrieved source metadata",
    }


@pytest.fixture
def unit_products(tmp_path: Path) -> Callable[..., dict[str, Any]]:
    def make(
        *,
        protected: bool = False,
        alias: bool = False,
        owner_change: str | None = None,
        foreign_payload: bool = False,
    ) -> dict[str, Any]:
        resources = (
            replace(spec(201), dataset_type="speleothem"),
            replace(spec(202), dataset_type="geochronologic"),
            replace(
                spec(401), dataset_type="speleothem", site_id=13, collection_unit_id=200
            ),
            replace(
                spec(402),
                dataset_type="geochronologic",
                site_id=13,
                collection_unit_id=200,
            ),
            replace(
                spec(501, role="reserved_candidate_confirmation"),
                dataset_type="geochronologic",
                site_id=14,
                collection_unit_id=300,
            ),
        )
        overrides = (
            {14: {"geography": '{"type":"Point","coordinates":[12,60]}'}}
            if alias
            else None
        )
        plan, inputs = source_inputs(
            tmp_path / "inputs", resources, site_overrides=overrides
        )
        original = tmp_path / "original-roster.json"
        original.write_bytes(inputs.roster_path.read_bytes())
        capture = tmp_path / "units"

        def fetched(url: str, **_: Any) -> NeotomaMetadataResponse:
            unit = int(url.rsplit("/", 1)[1])
            body = payload(unit)
            if foreign_payload and unit == 100:
                body["data"][0]["speleothem"]["collectionunitid"] = 999
            return NeotomaMetadataResponse(url, 200, (), json.dumps(body).encode())

        result = capture_neotoma_unit_resources(
            capture,
            plan=NeotomaUnitResourcePlan(
                (100, 200), plan.roster_sha256, tuple(inputs.metadata_captures)
            ),
            roster_path=original,
            metadata_captures=inputs.metadata_captures,
            fetch=fetched,
        )
        current = tmp_path / "current-roster.json"
        all_metadata = dict(inputs.metadata_captures)
        current_path = original
        if owner_change is not None:
            changed = list(resources)
            if owner_change == "database":
                changed[0] = replace(changed[0], database="Different source database")
            elif owner_change == "site":
                changed = [
                    replace(row, site_id=15) if row.collection_unit_id == 100 else row
                    for row in changed
                ]
            elif owner_change == "span":
                changed.append(replace(spec(203), dataset_type="geochronologic"))
            else:
                raise ValueError("Unknown fixture owner change")
            _, current_inputs = source_inputs(
                tmp_path / "current-inputs", tuple(changed)
            )
            current_path = current_inputs.roster_path
            all_metadata.update(current_inputs.metadata_captures)
        roster = json.loads(current_path.read_bytes())
        if protected:
            for row in roster["resources"]:
                if row["dataset_id"] == 202:
                    row["exposure_roles"] = dict.fromkeys(
                        ("current", "doi_frozen"), "reserved_candidate_confirmation"
                    )
        current.write_text(json.dumps(roster))
        logical = build_neotoma_resource_catalogue(
            roster_path=current,
            expected_roster_sha256=pin(current),
            metadata_captures=all_metadata,
            resource_captures={},
            country_boundaries={
                "Sweden": {
                    "features": [
                        {
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [[0, 0], [40, 0], [40, 80], [0, 80], [0, 0]]
                                ],
                            }
                        }
                    ]
                }
            },
        )
        catalogue = tmp_path / "catalogue"
        write_neotoma_resource_catalogue(
            catalogue,
            catalogue=logical,
            roster_path=current,
            capture_sources=all_metadata,
        )
        native = tmp_path / "native"
        write_neotoma_source_archive(
            native,
            catalogue_directory=catalogue,
            expected_catalogue_manifest_sha256=pin(catalogue / "manifest.json"),
            capture_sources=all_metadata,
        )
        authority = tmp_path / "authority.json"
        authority.write_text('{"status":"literal metadata review"}')
        legacy = tmp_path / "legacy-roster.json"
        legacy.write_bytes(b" \n" + current.read_bytes())
        context = tmp_path / "context"
        write_neotoma_ancillary_context(
            context,
            native_archive_directory=native,
            expected_native_archive_sha256=pin(native / "manifest.json"),
            legacy_rosters={pin(legacy): legacy},
            exposure_authority=authority,
            expected_exposure_authority_sha256=pin(authority),
        )
        return {
            "source": capture,
            "original": original,
            "native": native,
            "context": context,
            "writer": {
                "capture_directory": capture,
                "expected_capture_manifest_sha256": result.manifest_sha256,
                "original_roster_path": original,
                "context_directory": context,
                "expected_context_sha256": pin(context / "manifest.json"),
                "native_archive_directory": native,
                "expected_native_archive_sha256": pin(native / "manifest.json"),
            },
            "reader": {
                "context_directory": context,
                "expected_context_sha256": pin(context / "manifest.json"),
                "native_archive_directory": native,
                "expected_native_archive_sha256": pin(native / "manifest.json"),
            },
        }

    return make


def observe_units(monkeypatch: pytest.MonkeyPatch, allowed: set[Path]) -> list[Path]:
    opened = []
    original = Path.open

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and path.name.startswith("speleothem-unit-"):
            assert path in allowed, f"Unselected unit entity opened: {path}"
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    return opened


def rewrite_source(inputs: dict[str, Any], mutate: Callable[..., None]) -> str:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    root = inputs["source"]
    document = json.loads((root / "capture-manifest.json").read_bytes())
    control = json.loads((root / "request-plan.json").read_bytes())
    mutate(document, control, root)
    (root / "request-plan.json").write_bytes(encoded_json(control))
    document["plan_sha256"] = pin(root / "request-plan.json")
    (root / "capture-manifest.json").write_bytes(encoded_json(document))
    digest = pin(root / "capture-manifest.json")
    inputs["writer"]["expected_capture_manifest_sha256"] = digest
    return digest


def rehash_archive(output: Path, relative: str, mutate: Callable[..., None]) -> str:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    path = output / relative
    document = json.loads(path.read_bytes())
    mutate(document)
    path.write_bytes(encoded_json(document))
    if relative != "manifest.json":
        manifest = json.loads((output / "manifest.json").read_bytes())
        manifest["files"][relative] = {
            "sha256": pin(path),
            "bytes": path.stat().st_size,
        }
        manifest["source_bytes"] = sum(
            row["bytes"] for row in manifest["files"].values()
        )
        (output / "manifest.json").write_bytes(encoded_json(manifest))
    return pin(output / "manifest.json")


def rewrite_archive_source(output: Path, mutate: Callable[..., None]) -> str:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    digest = rewrite_source({"source": output / "capture", "writer": {}}, mutate)
    manifest = json.loads((output / "manifest.json").read_bytes())
    manifest["capture_manifest_sha256"] = digest
    document = json.loads((output / "capture/capture-manifest.json").read_bytes())
    index = json.loads((output / "index.json").read_bytes())
    for entry, row in zip(document["units"], index["units"], strict=True):
        row["terminal_status"] = entry["terminal_status"]
        row["attempts"] = []
        for ref in entry["attempts"]:
            record = json.loads((output / "capture" / ref["receipt_file"]).read_bytes())
            row["attempts"].append(
                {
                    **ref,
                    **{
                        key: record[key]
                        for key in (
                            "http_status",
                            "body_complete",
                            "utc_start",
                            "utc_end",
                        )
                        if key in record
                    },
                    **(
                        {
                            "body_sha256": record["retained_body_sha256"],
                            "body_bytes": record["retained_body_bytes"],
                        }
                        if "body_file" in ref
                        else {}
                    ),
                }
            )
    for key in ("request_count", "response_bytes", "partitions"):
        index[key] = document[key]
    (output / "index.json").write_bytes(encoded_json(index))
    for name in manifest["files"]:
        path = output / name
        manifest["files"][name] = {"bytes": path.stat().st_size, "sha256": pin(path)}
    manifest["source_bytes"] = sum(row["bytes"] for row in manifest["files"].values())
    (output / "manifest.json").write_bytes(encoded_json(manifest))
    return pin(output / "manifest.json")
