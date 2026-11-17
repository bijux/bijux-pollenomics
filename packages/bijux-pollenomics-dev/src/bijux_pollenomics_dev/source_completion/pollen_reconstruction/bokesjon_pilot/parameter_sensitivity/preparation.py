"""Connect retained nominal BOKE/KRAG inputs to the existing source-case host."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from bijux_pollenomics.analysis.lra.source_cases.contracts import (
    LIMITS,
    PROFILE,
    SourceCasePlan,
    canonical,
    digest,
)
from bijux_pollenomics.analysis.lra.source_cases.contracts import (
    reference as source_reference,
)
from bijux_pollenomics.core.filesystem import OwnedTreeWriter

from ..basin_sensitivity.inputs import BaselineInputs
from . import normalization

CASE_IDS = ("landclim-nominal-baseline", "europe-betula-nominal")


def selected_betula(reference: dict[str, Any]) -> dict[str, Any]:
    """Select one literal European cell without supplying missing Ulmus or vg."""
    rows = reference["synthesized_rows"]
    expected = {
        "taxon": "Betula",
        "taxonomic_level": "genus",
        "region": "Europe",
        "source_workbook": "originals/synthesized-rpp.xlsx",
        "source_sheet": "Worksheet 1",
        "source_row": "6",
        "rpp_cell": "G6",
        "rpp_sd_cell": "H6",
        "rpp": "4.94",
        "nominal_rpp_available": True,
    }
    matches = [r for r in rows if all(r.get(k) == v for k, v in expected.items())]
    ulmus = [r for r in rows if r["taxon"] == "Ulmus" and r["region"] == "Europe"]
    if len(matches) != 1 or len(ulmus) != 1 or ulmus[0]["nominal_rpp_available"]:
        raise ValueError("Exact European Betula and missing European Ulmus required")
    return deepcopy(matches[0])


@dataclass(frozen=True)
class PreparedSourceCases:
    """Own immutable input bytes before any source-case computation or publication."""

    plan: SourceCasePlan
    members: Mapping[str, bytes]
    normalization_json: str

    def __post_init__(self) -> None:
        """Own the caller's mapping and refuse mutable or noncanonical members."""
        owned = dict(self.members)
        for name, raw in owned.items():
            if type(raw) is not bytes:
                raise ValueError("Prepared source members require immutable bytes")
            source_reference({"path": name, "bytes": len(raw), "sha256": digest(raw)})
        object.__setattr__(self, "members", MappingProxyType(owned))

    def materialize(self, destination: Path) -> None:
        """Write only an absent bounded private input tree, preserving foreign paths."""
        limits = self.plan.payload()["limits"]
        if (
            len(self.members) > limits["max_input_files"]
            or sum(len(raw) for raw in self.members.values())
            > limits["max_input_bytes"]
        ):
            raise ValueError("Prepared source inputs exceed their declared budget")
        with OwnedTreeWriter(
            destination.absolute(),
            max_bytes=limits["max_input_bytes"],
            max_files=limits["max_input_files"],
        ) as writer:
            for name, raw in self.members.items():
                writer.write_bytes(name, raw)
            writer.validate_attachment()


def prepare(
    inputs: BaselineInputs,
    reference: dict[str, Any],
    *,
    buffers: dict[str, bytes],
    scope: dict[str, Any],
) -> PreparedSourceCases:
    """Preserve source support and SD metadata in an explicitly unweighted design."""
    if type(inputs.request_bytes) is not bytes:
        raise ValueError("Retained request requires immutable original bytes")
    evidence_buffers = dict(inputs.evidence)
    if any(type(raw) is not bytes for raw in evidence_buffers.values()):
        raise ValueError("Original source evidence requires immutable bytes")
    base = inputs.request
    if (
        base["operation"] != "lra"
        or base["data_kind"] != "source_observations"
        or base["purpose"] != "exploratory"
        or base["taxa"] != ["Betula", "Ulmus"]
        or [r["ppe"] for r in base["parameters"]] != [5.106, 1.27]
    ):
        raise ValueError("Retained exploratory paired Betula/Ulmus baseline required")
    for stage in ("reveals", "love"):
        if base["configuration"][stage].get("stochastic") is not False:
            raise ValueError("Nominal comparison must disable internal random draws")
    if (
        base["configuration"]["reveals"].get("region_cutoff_m", 100000) != 100000
        or base["configuration"]["love"].get(
            "analytical_cover_policy", "clip-and-renormalize"
        )
        != "clip-and-renormalize"
    ):
        raise ValueError(
            "Historical coherent extent and adjusted cover policy required"
        )
    refs = base["evidence"]
    names = [r["path"] for r in refs]
    if (
        len(names) != len(set(names))
        or set(names) != set(evidence_buffers)
        or any(Path(name).name != name for name in names)
        or any(digest(evidence_buffers[r["path"]]) != r["sha256"] for r in refs)
    ):
        raise ValueError("Original source evidence differs from its retained request")
    parameters = [r for r in refs if r["role"] == "parameters"]
    if len(parameters) != 1:
        raise ValueError("Exactly one original parameter evidence identity required")
    source_row = selected_betula(reference)
    binding = normalization.bind(
        base, evidence_buffers[parameters[0]["path"]], reference, buffers, scope
    )
    members: dict[str, bytes] = dict(evidence_buffers)

    def store(name: str, value: object, *, raw: bytes | None = None) -> dict[str, Any]:
        if name in members:
            raise ValueError("Source and generated member names must be disjoint")
        body = canonical(value) if raw is None else raw
        if len(body) > 1024 * 1024:
            raise ValueError("Source-case input member exceeds one MiB")
        members[name] = body
        return {"path": name, "sha256": digest(body), "bytes": len(body)}

    base_ref = store("retained-request.json", None, raw=inputs.request_bytes)
    basis_ref = store(
        "parameter-basis.json",
        {
            "reference_taxon": "Poaceae",
            "normalization": "Relative pollen productivity; Poaceae = 1",
            "parameter_domain": "Conditional two-tree nominal comparison; source applicability unevaluated",
            "citation": "Retained LandClim profile and doi:10.5194/essd-17-2007-2025, Europe Betula G6",
            "source_scale_binding": binding,
            "source_input_pins": list(inputs.source_pins),
            "selected_betula_source_row": source_row,
            "uncertainty": "No probability law; original source SD retained, no source-SD propagation",
            "native_vg_used": False,
        },
    )
    evidence = [{**r, "bytes": len(members[r["path"]])} for r in refs]
    envelope = {
        "schema_version": "lra-source-case-envelope.v1",
        "scope": "retained_request_snapshot",
        "base_request_ref": base_ref,
        "parameter_basis_ref": basis_ref,
        "evidence_members": evidence,
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
    for name, nominal in zip(CASE_IDS, (5.106, 4.94), strict=True):
        request = deepcopy(base)
        request["parameters"][0]["ppe"] = nominal
        declaration = store(
            name + "-parameters.json",
            {
                "schema_version": "lra-source-case-parameters.v1",
                "case_id": name,
                "base_request_sha256": base_ref["sha256"],
                "scope": "caller_declared_conditioning_not_source_variance",
                "parameters": request["parameters"],
            },
        )
        case_evidence = deepcopy(evidence)
        for ref, member in zip(request["evidence"], case_evidence, strict=True):
            if ref["role"] == "parameters":
                ref.update(path=declaration["path"], sha256=declaration["sha256"])
                member.update(declaration)
        cases.append(
            {
                "case_id": name,
                "request_ref": store(name + ".json", request),
                "parameter_declaration_ref": declaration,
                "evidence_members": case_evidence,
            }
        )
    plan = SourceCasePlan.from_dict(
        {
            "schema_version": "lra-source-cases.v1",
            "profile": PROFILE,
            "purpose": "exploratory",
            "envelope_ref": store("source-envelope.json", envelope),
            "cases": cases,
            "design": {"kind": "unweighted_sensitivity"},
            "limits": dict(LIMITS),
        }
    )
    store("plan.json", plan.payload())
    return PreparedSourceCases(
        plan, MappingProxyType(members), canonical(binding).decode()
    )
