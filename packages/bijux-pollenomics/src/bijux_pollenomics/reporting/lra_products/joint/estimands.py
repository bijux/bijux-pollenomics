"""Bind report estimands to validated retained child contracts."""

from __future__ import annotations

import json
from typing import Any

from ..contracts import digest


def bind_estimands(
    projection: dict[str, Any], manifest: dict[str, Any], product: dict[str, bytes]
) -> None:
    """Attach policy evidence without modifying the original joint product."""
    policies: dict[str, str | None] = {}
    for band in projection["bins"]:
        evidence = []
        for row in manifest["rows"]:
            if row["bin_id"] != band["bin_id"] or row["status"] != "success":
                continue
            path = row["child"] + "/numerical/local_love/result_contract.json"
            raw = product[path]
            checksum = digest(raw)
            if manifest["files"].get(path) != checksum:
                raise ValueError(
                    "LOVE contract differs from its retained product identity"
                )
            contract = json.loads(raw)
            policy = contract.get("analytical_cover_policy", "source-raw")
            if policy not in {"source-raw", "clip-and-renormalize"}:
                raise ValueError("Unsupported LOVE cover policy")
            evidence.append(
                {
                    "source_member": path,
                    "source_member_sha256": checksum,
                    "policy": policy,
                }
            )
        distinct = {item["policy"] for item in evidence}
        if len(distinct) > 1:
            raise ValueError("Joint bin combines different LOVE cover policies")
        policy = next(iter(distinct), None)
        policies[band["bin_id"]] = policy
        band["local_cover_policy"] = policy
        band["local_cover_policy_evidence"] = evidence

    def name(coordinate: dict[str, Any], bin_id: str) -> str:
        if coordinate["role"] == "regional":
            return "reveals:regional-cover"
        if coordinate["role"] == "local" and policies[bin_id] is not None:
            return "love:" + str(policies[bin_id])
        raise ValueError("A reported coordinate has no admitted cover estimand")

    for row in projection["means"]:
        row["estimand"] = name(row["coordinate"], row["bin_id"])
    for row in projection["covariance"]:
        row["row_estimand"] = name(row["row_coordinate"], row["bin_id"])
        row["column_estimand"] = name(row["column_coordinate"], row["bin_id"])
    projection["schema_version"] = "lra-joint-summary-download.v2"
