from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.evidence.sources.neotoma.contract import (
    canonical_json_bytes,
    materialization_digest,
)


def _snapshot() -> dict[str, Any]:
    surfaces: dict[str, object] = {
        "sites": [
            {
                "site_id": "neotoma:site:3",
                "source_site_id": 3,
                "country_code": "UNASSIGNED",
                "country_decision_status": "review",
                "country_propagation_eligible": False,
            },
            {
                "site_id": "neotoma:site:1",
                "source_site_id": 1,
                "country_code": "SE",
                "country_decision_status": "assigned",
                "country_propagation_eligible": True,
            },
            {
                "site_id": "neotoma:site:2",
                "source_site_id": 2,
                "country_code": "UNASSIGNED",
                "country_decision_status": "unassigned",
                "country_propagation_eligible": False,
            },
        ],
        "collection_units": [
            {
                "collection_unit_id": "neotoma:collection-unit:1",
                "site_id": "neotoma:site:1",
                "country_code": "SE",
            },
            {
                "collection_unit_id": "neotoma:collection-unit:3",
                "site_id": "neotoma:site:3",
                "country_code": "UNASSIGNED",
            },
        ],
        "datasets": [
            {
                "dataset_id": "neotoma:dataset:3",
                "site_id": "neotoma:site:3",
                "collection_unit_id": "neotoma:collection-unit:3",
                "country_code": "UNASSIGNED",
            }
        ],
        "chronologies": [],
        "chronology_controls": [],
        "samples": [
            {
                "sample_id": "neotoma:sample:3",
                "site_id": "neotoma:site:3",
                "collection_unit_id": "neotoma:collection-unit:3",
                "dataset_id": "neotoma:dataset:3",
                "country_code": "UNASSIGNED",
            }
        ],
        "age_claims": [],
        "variables": [{"variable_id": "neotoma:variable:3"}],
        "observations": [
            {
                "observation_id": "neotoma:observation:3",
                "collection_unit_id": "neotoma:collection-unit:3",
                "dataset_id": "neotoma:dataset:3",
                "sample_id": "neotoma:sample:3",
                "variable_id": "neotoma:variable:3",
                "site_id": "neotoma:site:3",
                "country_code": "UNASSIGNED",
                "source_value": 0,
            }
        ],
        "conflicts": [],
        "orphans": [],
    }
    country_fields = (
        "sites",
        "collection_units",
        "datasets",
        "chronologies",
        "chronology_controls",
        "samples",
        "age_claim_rows",
        "observation_rows",
    )
    country_counts = {
        country_code: dict.fromkeys(country_fields, 0)
        for country_code in ("SE", "DK", "NO", "FI", "UNASSIGNED")
    }
    country_counts["SE"].update({"sites": 1, "collection_units": 1})
    country_counts["UNASSIGNED"].update(
        {
            "sites": 2,
            "collection_units": 1,
            "datasets": 1,
            "samples": 1,
            "observation_rows": 1,
        }
    )
    return {
        "schema_version": "neotoma-relational-snapshot.v2",
        "source_family": "neotoma",
        "source_snapshot_id": "sha256:source-fixture",
        "build_id": "fixture-build",
        **surfaces,
        "reconciliation": {
            "normalized_row_counts": {
                "sites": 3,
                "collection_units": 2,
                "datasets": 1,
                "chronologies": 0,
                "chronology_controls": 0,
                "samples": 1,
                "age_claims": 0,
                "variables": 1,
                "observations": 1,
            },
            "conflict_count": 0,
            "orphan_count": 0,
            "country_counts": country_counts,
            "country_attribution_counts": {
                "decision_statuses": {
                    "assigned": 1,
                    "review": 1,
                    "unassigned": 1,
                },
                "final_country_codes": {"SE": 1, "UNASSIGNED": 2},
                "propagation_eligibility": {"blocked": 2, "eligible": 1},
            },
        },
    }


def _published_files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _rebind_authenticated_file(root: Path, relative: str, content: bytes) -> None:
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    (root / relative).write_bytes(content)
    if relative == "reconciliation.json":
        manifest["reconciliation"]["sha256"] = hashlib.sha256(content).hexdigest()
    else:
        part = next(
            part
            for surface in manifest["surfaces"].values()
            for part in surface["parts"]
            if part["path"] == relative
        )
        part["sha256"] = hashlib.sha256(content).hexdigest()
    records = [
        {"path": part["path"], "sha256": part["sha256"]}
        for surface in manifest["surfaces"].values()
        for part in surface["parts"]
    ]
    records.append(
        {
            "path": manifest["reconciliation"]["path"],
            "sha256": manifest["reconciliation"]["sha256"],
        }
    )
    manifest["materialization_sha256"] = materialization_digest(records)
    manifest_path.write_bytes(canonical_json_bytes(manifest))
