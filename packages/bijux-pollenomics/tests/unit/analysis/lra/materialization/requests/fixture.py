"""Fully declared synthetic request inputs, created before source normalization."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.lra.materialization.reading import read_neotoma_evidence
from bijux_pollenomics.analysis.lra.materialization.requests import (
    SampleChronologyBinding,
    SourceCellBinding,
)
from tests.unit.analysis.lra.support import request_fixture

from .support import authorities, write_json


def projection_fixture(root: Path, **source_options: Any) -> dict[str, Any]:
    raw, normalized = authorities(root / "source", **source_options)
    evidence = read_neotoma_evidence(raw, normalized)
    inputs = root / "inputs"
    inputs.mkdir()
    request = request_fixture(inputs, operation="lra")
    samples = {}
    for role, number in (("regional", 1), ("local", 2)):
        target = request[role]["samples"][0]
        target["sample_id"] = f"neotoma:sample:{number * 100}"
        target["site_id"] = f"neotoma:site:{number}"
        for field in ("counts", "age_type", "age_support_bp"):
            del target[field]
        samples[target["sample_id"]] = role
    cells = [
        SourceCellBinding(
            samples[row.payload()["sample_id"]],
            row.payload()["sample_id"],
            row.payload()["source_reported_name"],
            row.payload()["observation_id"],
        )
        for row in evidence.rows("observations")
        if row.payload()["sample_id"] in samples
    ]
    claims = [
        SampleChronologyBinding(
            row.payload()["subject_id"], row.payload()["chronology_claim_id"]
        )
        for row in evidence.rows("age_claims")
        if row.payload()["subject_id"] in samples
    ]
    for source in evidence.rows("age_claims"):
        sample_id = source.payload()["subject_id"]
        if sample_id not in samples:
            continue
        evidence_id = f"chronology-{sample_id}"
        relative = f"{evidence_id}.json"
        content = (normalized / source.path).read_bytes()
        (inputs / relative).write_bytes(content)
        request["evidence"].append(
            {
                "evidence_id": evidence_id,
                "role": "chronology",
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
        request[samples[sample_id]]["samples"][0]["chronology_evidence_id"] = (
            evidence_id
        )
    request["exclusions"] = [
        {
            "sample_id": row.payload()["sample_id"],
            "reason_code": "not_selected_for_synthetic_fixture",
        }
        for row in evidence.rows("samples")
        if row.payload()["sample_id"] not in samples
    ]
    values = {
        "taxa": request["taxa"],
        "parameters": request["parameters"],
        "geometry": {
            "basins": {role: request[role]["basin"] for role in ("regional", "local")},
            "rings": request["rings"],
        },
        "decision": request["temporal_matching"],
    }
    for item in request["evidence"]:
        role = item["role"]
        path = inputs / item["path"]
        if role == "raw_snapshot":
            path.write_bytes((raw / "manifest.json").read_bytes())
        elif role == "chronology" and item["evidence_id"] == "chronology":
            path.write_bytes(
                (normalized / next(evidence.rows("age_claims")).path).read_bytes()
            )
        elif role in values:
            document = {
                "data_kind": "synthetic",
                "synthetic_fixture_id": "neotoma-lra-fixture.v1",
                "declared_values": values[role],
            }
            if role == "parameters":
                document.update(
                    reference_taxon="Alnus",
                    normalization="arbitrary synthetic scale4",
                    parameter_domain="synthetic fixture only",
                    citation="declared synthetic arithmetic fixture; no empirical PPE source",
                )
            write_json(path, document)
        item["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "raw_root": raw,
        "normalized_root": normalized,
        "input_root": inputs,
        "request_template": request,
        "cell_bindings": cells,
        "chronology_bindings": claims,
        "output_directory": root / "projection",
    }
