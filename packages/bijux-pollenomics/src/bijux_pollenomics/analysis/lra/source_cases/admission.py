"""Admit fixed pooled support and independently declared conditional design laws."""

from __future__ import annotations

import json
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterator, cast

from ..inputs.validation import ValidatedRequest, validate_request
from .contracts import SourceCasePlan, canonical, fields, member, positive, refuse
from .inputs import SourceInputs


def _evidence(inputs: SourceInputs, request: dict[str, Any], members: object) -> None:
    if not isinstance(members, list):
        refuse("Evidence inventory must be explicit")
    declared = []
    for value in members:
        entry = member(value)
        inputs.capture({key: entry[key] for key in ("path", "sha256", "bytes")})
        declared.append(
            {key: entry[key] for key in ("evidence_id", "role", "path", "sha256")}
        )
    if sorted(declared, key=lambda v: v["evidence_id"]) != sorted(
        request["evidence"], key=lambda v: v["evidence_id"]
    ):
        refuse("Request evidence differs from the independently pinned inventory")


def _fixed(request: dict[str, Any]) -> bytes:
    fixed = dict(request)
    fixed.pop("parameters")
    fixed["evidence"] = sorted(
        [entry for entry in fixed["evidence"] if entry["role"] != "parameters"],
        key=lambda v: v["evidence_id"],
    )
    fixed["versions"] = {
        key: value for key, value in request["versions"].items() if key != "parameters"
    }
    return canonical(fixed)


def _analytical(request: dict[str, Any]) -> None:
    if (
        request["data_kind"] != "source_observations"
        or request["operation"] != "lra"
        or request["purpose"] != "exploratory"
    ):
        refuse("Require an exploratory paired source request snapshot")
    config = request["configuration"]
    for key, count in (("reveals", "iterations"), ("love", "repeats")):
        part = config.get(key, {})
        if part.get("stochastic") is not False:
            refuse(
                "Source cases require explicit deterministic analytical configuration"
            )
        positive(part.get(count), 64)
    if config["love"].get("method") != "analytical":
        refuse("Source cases require analytical LOVE")
    positive(config["love"].get("max_ring"), len(request["rings"]))
    for role in ("regional", "local"):
        if len(request[role]["samples"]) != 1:
            refuse("Initial fixed support requires one retained pooled bin per role")


def _coverage(
    inputs: SourceInputs, base: dict[str, Any], records: object
) -> tuple[dict[str, Any], ...]:
    if not isinstance(records, list) or len(records) != 2:
        refuse("Require both retained pooled-bin lineage declarations")
    rows = []
    for role in ("regional", "local"):
        matches = [
            row for row in records if isinstance(row, dict) and row.get("role") == role
        ]
        if len(matches) != 1:
            refuse("Lineage must identify each retained role once")
        row = fields(
            matches[0],
            {
                "role",
                "record_id",
                "record_kind",
                "native_full_pollen_N",
                "native_lineage_ref",
            },
        )
        sample = base[role]["samples"][0]
        if (
            row["record_id"] != sample["sample_id"]
            or row["record_kind"] != "pooled_source_bin"
        ):
            refuse("Pooled bin identities cannot become native observation identities")
        panel = sum(sample["counts"])
        full = row["native_full_pollen_N"]
        if full is not None:
            if (
                type(full) is not int
                or full < panel
                or row["native_lineage_ref"] is None
            ):
                refuse("Known native totals require independent bound lineage evidence")
            ledger = inputs.object(row["native_lineage_ref"])
            if (
                ledger.get("record_id") != row["record_id"]
                or type(ledger.get("native_full_pollen_N")) is not int
                or ledger["native_full_pollen_N"] != full
            ):
                refuse("Native coverage differs from its independently bound ledger")
        elif row["native_lineage_ref"] is not None:
            inputs.object(row["native_lineage_ref"])
        rows.append(
            {
                **row,
                "modelled_panel_count": panel,
                "excluded_native_pollen_N": None if full is None else full - panel,
                "terrestrial_denominator_admitted": False,
                "native_sample_allocation_verified": False,
            }
        )
    return tuple(rows)


def _law(
    inputs: SourceInputs, design: dict[str, Any], ids: set[str]
) -> dict[str, str] | None:
    if design["kind"] == "unweighted_sensitivity":
        return None
    law = fields(
        inputs.object(design["law_ref"]),
        {"schema_version", "scope", "statement", "masses"},
    )
    if (
        law["schema_version"] != "lra-caller-design-law.v1"
        or law["scope"] != "caller_declared_conditional_design"
        or not isinstance(law["statement"], str)
        or not law["statement"].strip()
    ):
        refuse("Require independent explicit conditional design-law evidence")
    if not isinstance(law["masses"], list):
        refuse("Require an exact rational mass inventory")
    masses: dict[str, Fraction] = {}
    for item in law["masses"]:
        entry = fields(item, {"case_id", "numerator", "denominator"})
        if entry["case_id"] not in ids or entry["case_id"] in masses:
            refuse("Design-law identities differ from the case inventory")
        masses[entry["case_id"]] = Fraction(
            positive(entry["numerator"], 2**53 - 1),
            positive(entry["denominator"], 2**53 - 1),
        )
    if set(masses) != ids or sum(masses.values()) != 1:
        refuse("Independent rational design masses must cover exactly one full law")
    return {key: str(value) for key, value in sorted(masses.items())}


@dataclass(frozen=True)
class AdmittedSourceCases:
    """Retain private validated requests and source checks for one live operation."""

    plan: SourceCasePlan
    requests: Mapping[str, ValidatedRequest]
    coverage_json: str
    masses_json: str
    inputs: SourceInputs

    @property
    def coverage(self) -> tuple[dict[str, Any], ...]:
        """Return independent views without lending mutable accepted metadata."""
        return tuple(json.loads(self.coverage_json))

    @property
    def masses(self) -> dict[str, str] | None:
        """Keep exact supplied design mass separate from source coverage."""
        return cast(dict[str, str] | None, json.loads(self.masses_json))

    def check(self) -> None:
        """Refuse source or private snapshot replacement after admission."""
        self.inputs.check()


@contextmanager
def admit_source_cases(
    plan: SourceCasePlan, *, input_root: Path, workspace: Path
) -> Iterator[AdmittedSourceCases]:
    """Authenticate the entire design before any analytical execution is possible."""
    value = plan.payload()
    inputs = SourceInputs(input_root, workspace / "inputs", value["limits"])
    try:
        envelope = fields(
            inputs.object(value["envelope_ref"]),
            {
                "schema_version",
                "scope",
                "base_request_ref",
                "parameter_basis_ref",
                "evidence_members",
                "records",
            },
        )
        if (
            envelope["schema_version"] != "lra-source-case-envelope.v1"
            or envelope["scope"] != "retained_request_snapshot"
        ):
            refuse("Unsupported source-lineage envelope scope")
        base = inputs.object(envelope["base_request_ref"])
        basis = inputs.object(envelope["parameter_basis_ref"])
        for key in ("reference_taxon", "normalization", "parameter_domain", "citation"):
            if not isinstance(basis.get(key), str) or not basis[key].strip():
                refuse("Retain an explicit parameter reference scale and domain")
        _evidence(inputs, base, envelope["evidence_members"])
        validate_request(base, input_root=inputs.snapshot)
        _analytical(base)
        coverage = _coverage(inputs, base, envelope["records"])
        dimension = len(base["taxa"]) * (1 + base["configuration"]["love"]["max_ring"])
        if 2 * dimension**2 > value["limits"]["max_covariance_cells"]:
            refuse("Result covariance exceeds its declared finite cell budget")
        requests = {}
        for case in value["cases"]:
            request = inputs.object(case["request_ref"])
            declaration = fields(
                inputs.object(case["parameter_declaration_ref"]),
                {
                    "schema_version",
                    "case_id",
                    "base_request_sha256",
                    "scope",
                    "parameters",
                },
            )
            if declaration != {
                "schema_version": "lra-source-case-parameters.v1",
                "case_id": case["case_id"],
                "base_request_sha256": envelope["base_request_ref"]["sha256"],
                "scope": "caller_declared_conditioning_not_source_variance",
                "parameters": request["parameters"],
            }:
                refuse("Conditioning parameters differ from their bound declaration")
            _evidence(inputs, request, case["evidence_members"])
            parameter_refs = [
                entry for entry in request["evidence"] if entry["role"] == "parameters"
            ]
            base_parameters = [
                entry for entry in base["evidence"] if entry["role"] == "parameters"
            ]
            expected_parameter = case["parameter_declaration_ref"]
            if (
                len(parameter_refs) != 1
                or len(base_parameters) != 1
                or parameter_refs[0]
                != {
                    "evidence_id": base_parameters[0]["evidence_id"],
                    "role": "parameters",
                    "path": expected_parameter["path"],
                    "sha256": expected_parameter["sha256"],
                }
            ):
                refuse(
                    "Case parameter evidence must be its declared conditioning snapshot"
                )
            if _fixed(request) != _fixed(base):
                refuse(
                    "Conditional cases must preserve complete fixed support and configuration"
                )
            for original, changed in zip(
                base["parameters"], request["parameters"], strict=True
            ):
                if {
                    k: v for k, v in original.items() if k not in {"ppe", "ppe_sd"}
                } != {k: v for k, v in changed.items() if k not in {"ppe", "ppe_sd"}}:
                    refuse("Taxon association and fall speeds must remain unchanged")
            requests[case["case_id"]] = validate_request(
                request, input_root=inputs.snapshot
            )
        masses = _law(inputs, value["design"], set(requests))
        inputs.check()
        yield AdmittedSourceCases(
            plan,
            MappingProxyType(dict(requests)),
            canonical(coverage).decode(),
            canonical(masses).decode(),
            inputs,
        )
        inputs.check()
    finally:
        inputs.close()
