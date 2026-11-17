"""Generated retained-request contract snapshots, never empirical evidence."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from ..support import request_fixture


def encoded(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def store(root: Path, name: str, value: object) -> dict[str, Any]:
    raw = encoded(value)
    (root / name).write_bytes(raw)
    return {"path": name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def fixture(
    root: Path, *, weighted: bool = True
) -> tuple[dict[str, Any], dict[str, Any]]:
    root.mkdir(parents=True, exist_ok=True)
    base = request_fixture(root, "lra")
    # This is a generated example of the retained-request declaration type.
    # It certifies neither a provider origin nor scientific authenticity.
    base["data_kind"] = "source_observations"
    base["versions"] = {key: "generated-contract-snapshot" for key in base["versions"]}
    for role in ("regional", "local"):
        base[role]["samples"][0]["sample_id"] = "pooled-" + role + "-bin"
    members = []
    for ref in base["evidence"]:
        stored = store(
            root,
            ref["path"],
            {
                "scope": "generated contract snapshot, not empirical evidence",
                "role": ref["role"],
            },
        )
        ref["sha256"] = stored["sha256"]
        members.append(
            {"evidence_id": ref["evidence_id"], "role": ref["role"], **stored}
        )
    base_ref = store(root, "base.json", base)
    basis = store(
        root,
        "basis.json",
        {
            "reference_taxon": "declared-test-reference",
            "normalization": "generated ratio scale",
            "parameter_domain": "generated mechanical contract",
            "citation": "Generated fixture; no empirical parameter qualification",
        },
    )
    envelope = {
        "schema_version": "lra-source-case-envelope.v1",
        "scope": "retained_request_snapshot",
        "base_request_ref": base_ref,
        "parameter_basis_ref": basis,
        "evidence_members": members,
        "records": [
            {
                "role": role,
                "record_id": base[role]["samples"][0]["sample_id"],
                "record_kind": "pooled_source_bin",
                "native_full_pollen_N": None,
                "native_lineage_ref": None,
            }
            for role in ("regional", "local")
        ],
    }
    cases = []
    for name, ppe in (("nominal", 4), ("comparison", 5)):
        request = deepcopy(base)
        request["parameters"][0]["ppe"] = ppe
        declaration = store(
            root,
            name + "-parameters.json",
            {
                "schema_version": "lra-source-case-parameters.v1",
                "case_id": name,
                "base_request_sha256": base_ref["sha256"],
                "scope": "caller_declared_conditioning_not_source_variance",
                "parameters": request["parameters"],
            },
        )
        case_members = deepcopy(members)
        for ref, member in zip(request["evidence"], case_members, strict=True):
            if ref["role"] == "parameters":
                ref.update(path=declaration["path"], sha256=declaration["sha256"])
                member.update(declaration)
        cases.append(
            {
                "case_id": name,
                "request_ref": store(root, name + ".json", request),
                "parameter_declaration_ref": declaration,
                "evidence_members": case_members,
            }
        )
    design = {"kind": "unweighted_sensitivity"}
    if weighted:
        law = store(
            root,
            "law.json",
            {
                "schema_version": "lra-caller-design-law.v1",
                "scope": "caller_declared_conditional_design",
                "statement": "Generated finite design, not empirical uncertainty",
                "masses": [
                    {"case_id": "nominal", "numerator": 1, "denominator": 4},
                    {"case_id": "comparison", "numerator": 3, "denominator": 4},
                ],
            },
        )
        design = {"kind": "caller_weighted_finite_design", "law_ref": law}
    plan = {
        "schema_version": "lra-source-cases.v1",
        "profile": "source-fixed-support-analytical-v1",
        "purpose": "exploratory",
        "envelope_ref": store(root, "envelope.json", envelope),
        "cases": cases,
        "design": design,
        "limits": {
            "max_cases": 16,
            "max_input_files": 128,
            "max_input_bytes": 8388608,
            "max_output_bytes": 67108864,
            "max_output_files": 4096,
            "max_covariance_cells": 1000000,
        },
    }
    return base, plan
