"""Finite authenticated native metadata publications for Atlas resource adapters."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    build_neotoma_resource_catalogue,
    write_neotoma_resource_catalogue,
)

from ....collection.sources.neotoma.resource_catalogue.conftest import (
    catalogue_sources as catalogue_sources,
)

_UNCHANGED = object()


def pin_compact_extension(root: Path, catalogue: dict[str, Any]) -> str:
    """Give a finite future-schema or adverse publication its explicit test pin."""
    path = root / "catalogue.json"
    path.write_text(json.dumps(catalogue))
    manifest = json.loads((root / "manifest.json").read_bytes())
    manifest["files"]["catalogue.json"] = sha256(path.read_bytes()).hexdigest()
    (root / "manifest.json").write_text(json.dumps(manifest))
    return sha256((root / "manifest.json").read_bytes()).hexdigest()


@pytest.fixture
def atlas_catalogue(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> Callable[..., tuple[Path, str, dict[str, Any]]]:
    def publish(
        *,
        geography: object = _UNCHANGED,
        auxiliary_type: str = "geochronologic",
        all_site_resources: bool = False,
    ) -> tuple[Path, str, dict[str, Any]]:
        inputs = catalogue_sources(
            capture_resources=False, auxiliary_type=auxiliary_type
        )
        # No country is inferred from a geographic point without boundary authority.
        inputs["country_boundaries"] = {}
        if geography is not _UNCHANGED:
            roster = json.loads(inputs["roster_path"].read_bytes())
            source = next(iter(inputs["metadata_captures"].values()))
            native = json.loads((source / "site-12-datasets.body").read_bytes())
            if not all_site_resources:
                native["data"][0]["site"]["datasets"] = [
                    native["data"][0]["site"]["datasets"][1]
                ]
            if geography == "missing":
                del native["data"][0]["site"]["geography"]
            else:
                native["data"][0]["site"]["geography"] = geography
            body = json.dumps(native).encode()
            alternate = tmp_path / "alternate-metadata"
            captured = capture_neotoma_metadata(
                alternate,
                plan=NeotomaMetadataPlan(site_ids=(12,)),
                fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), body),
            )
            inputs["metadata_captures"][captured.manifest_sha256] = alternate
            roster["source_metadata_capture_manifest_sha256"].append(
                captured.manifest_sha256
            )
            for offset, row in enumerate(
                roster["resources"][:2]
                if all_site_resources
                else [roster["resources"][1]]
            ):
                row["metadata_locator"] = {
                    "response_sha256": sha256(body).hexdigest(),
                    "json_pointer": f"/data/0/site/datasets/{offset}",
                }
            inputs["roster_path"].write_text(json.dumps(roster))
            inputs["expected_roster_sha256"] = sha256(
                inputs["roster_path"].read_bytes()
            ).hexdigest()
        catalogue = build_neotoma_resource_catalogue(**inputs)
        output = tmp_path / "atlas-catalogue"
        write_neotoma_resource_catalogue(
            output,
            catalogue=catalogue,
            roster_path=inputs["roster_path"],
            capture_sources=inputs["metadata_captures"],
        )
        digest = sha256((output / "manifest.json").read_bytes()).hexdigest()
        return output, digest, catalogue

    return publish


def legacy_site(identity: str = "12") -> dict[str, Any]:
    """Use the maintained projection's native textual IDs and namespace."""
    return {
        "record_id": f"neotoma:site:{identity}",
        "tabs": {
            "overview": {
                "source_family": "neotoma",
                "source_site_id": identity,
                "site_id": f"neotoma:site:{identity}",
                "country_code": "SE",
            },
            "provenance": {"source_snapshot_id": "original-pollen-epoch"},
        },
    }
