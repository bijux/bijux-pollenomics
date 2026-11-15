"""Exact source download partitions preserve roles, statuses and original epochs."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

from ...capture.resources.models import DEVELOPMENT_ROLES
from ..custody import public_member


def build_download_index(catalogue: dict[str, Any], anchor: str) -> dict[str, Any]:
    rows = []
    for resource in catalogue["resources"]:
        for version, selected in resource["versions"].items():
            row: dict[str, Any] = {
                "dataset_id": str(resource["dataset_id"]),
                "site_id": str(resource["site_id"]),
                "collection_unit_id": str(resource["collection_unit_id"]),
                "version": version,
                "exposure_role": resource["exposure_role"],
                "statuses": {
                    key: deepcopy(value)
                    for key, value in selected.items()
                    if key.endswith("_status")
                },
                "use_scope": "source_entity_download_only",
                "scientific_admission": "not_asserted",
            }
            rows.append(row)
            if resource["exposure_role"] not in DEVELOPMENT_ROLES:
                row["state"] = "blocked_exposure_role"
                continue
            source = selected.get("source")
            row["state"] = "unavailable_source_entity"
            if not isinstance(source, dict):
                continue
            row["source"] = deepcopy(source)
            if source.get("source_kind") == "retained_public_response":
                key = f"dataset-{resource['dataset_id']}-{version}"
                path = f"captures/retained/{key}/native.body"
            elif (
                source.get("source_kind") == "source_http_attempt"
                and source.get("http_status") == 200
                and source.get("body_complete") is True
            ):
                path = f"captures/{public_member(source['capture_manifest_sha256'])}/{public_member(source['body_file'])}"
            else:
                continue
            row.update(state="available_source_entity", download_path=path)
    return {
        "schema_version": "neotoma-source-download-index.v1",
        "catalogue_manifest_sha256": anchor,
        "resources": rows,
        "partitions": dict(sorted(Counter(row["state"] for row in rows).items())),
        "scientific_admission": "not_asserted",
        "attribution": "Exact source metadata and rights in the pinned catalogue; source epochs and native receipts remain separate",
    }
