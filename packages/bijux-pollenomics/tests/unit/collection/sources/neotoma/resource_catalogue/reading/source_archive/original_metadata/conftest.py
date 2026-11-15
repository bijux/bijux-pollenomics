"""Historical dataset identity with a successful empty current metadata lookup."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma import resource_catalogue as api
from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
)


@pytest.fixture
def original_catalogue(
    catalogue_sources: Callable[..., dict[str, Any]], tmp_path: Path
) -> tuple[Path, str, dict[str, Path], Path]:
    inputs = catalogue_sources(capture_resources=False)
    original = tmp_path / "original"
    parts = []
    for identity in (201, 202):
        path = original / f"surfaces/datasets/{identity}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {
                    "rows": [
                        {
                            "source_dataset_id": identity,
                            "site_id": "neotoma:site:12",
                            "collection_unit_id": "neotoma:collection-unit:100",
                            "source_snapshot_id": "sha256:" + "a" * 64,
                            "build_id": "sha256:" + "b" * 64,
                            "source_payload": {
                                "datasetid": identity,
                                "datasettype": "pollen"
                                if identity == 201
                                else "geochronologic",
                                "database": None,
                                "doi": [],
                                "datasetpi": [],
                            },
                        }
                    ]
                }
            )
        )
        parts.append(
            {
                "path": path.relative_to(original).as_posix(),
                "sha256": sha256(path.read_bytes()).hexdigest(),
            }
        )
    (original / "manifest.json").write_text(
        json.dumps(
            {
                "source_snapshot_id": "sha256:" + "a" * 64,
                "build_id": "sha256:" + "b" * 64,
                "surfaces": {
                    "datasets": {"row_count": 2, "parts": parts},
                    "observations": {
                        "row_count": 999,
                        "parts": [{"path": "numerical-not-supplied.json"}],
                    },
                },
            }
        )
    )
    empty = b'{"status":"success","data":[]}'
    lookup_root = tmp_path / "current-lookup"
    lookup = capture_neotoma_metadata(
        lookup_root,
        plan=NeotomaMetadataPlan(dataset_ids=(201,)),
        fetch=lambda url, **_: NeotomaMetadataResponse(url, 200, (), empty),
    )
    inputs["metadata_captures"][lookup.manifest_sha256] = lookup_root
    roster = json.loads(inputs["roster_path"].read_bytes())
    roster["resources"][0]["metadata_locator"] = {
        "source_kind": "retained_relational_dataset_metadata_not_current_HTTP",
        "response_sha256": parts[0]["sha256"],
        "json_pointer": "/rows/0/source_payload",
    }
    roster["resources"][0]["current_metadata_lookup"] = {
        "dataset_id": 201,
        "manifest_sha256": lookup.manifest_sha256,
        "body_sha256": sha256(empty).hexdigest(),
        "successful_empty": True,
        "absence_certified": False,
    }
    inputs["roster_path"].write_text(json.dumps(roster))
    inputs["expected_roster_sha256"] = sha256(
        inputs["roster_path"].read_bytes()
    ).hexdigest()
    inputs["original_relational_root"] = original
    catalogue = api.build_neotoma_resource_catalogue(**inputs)
    output = tmp_path / "catalogue"
    sources = inputs["metadata_captures"]
    api.write_neotoma_resource_catalogue(
        output,
        catalogue=catalogue,
        roster_path=inputs["roster_path"],
        capture_sources=sources,
        original_relational_root=original,
    )
    return (
        output,
        sha256((output / "manifest.json").read_bytes()).hexdigest(),
        sources,
        original,
    )


@pytest.fixture
def portable_original(
    original_catalogue: tuple[Path, str, dict[str, Path], Path], tmp_path: Path
) -> tuple[Path, str, Path]:
    catalogue, digest, sources, original = original_catalogue
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import archive

    output = tmp_path / "portable"
    archive.write_neotoma_source_archive(
        output,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
        original_relational_root=original,
    )
    return output, sha256((output / "manifest.json").read_bytes()).hexdigest(), original
