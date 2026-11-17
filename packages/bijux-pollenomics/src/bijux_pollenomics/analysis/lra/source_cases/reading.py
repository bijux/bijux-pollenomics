"""Reopen derived-only conditional products without reopening original source bodies."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from fractions import Fraction
from math import fsum, isclose, isfinite
from pathlib import Path
from typing import Any, cast

from ....core.filesystem import BoundedInputTree
from ..uncertainty.contracts import NUMERICAL_REASONS
from .contracts import (
    PROFILE,
    canonical,
    digest,
    fields,
    identifier,
    positive,
    reference,
    refuse,
)
from .results import design_summaries

# Saved decimal tables may differ by roundoff after stable positive-part closure.
COVER_RELATION_ABS_TOL = 2e-12


def _hash(value: object) -> None:
    if not isinstance(value, str) or re.fullmatch("[0-9a-f]{64}", value) is None:
        refuse("Require an exact derived-content or provenance digest")


def _coverage(value: object) -> None:
    if not isinstance(value, list) or len(value) != 2:
        refuse("Require both fixed pooled support roles")
    roles = []
    for entry in value:
        row = fields(
            entry,
            {
                "role",
                "record_id",
                "record_kind",
                "native_full_pollen_N",
                "native_lineage_ref",
                "modelled_panel_count",
                "excluded_native_pollen_N",
                "terrestrial_denominator_admitted",
                "native_sample_allocation_verified",
            },
        )
        roles.append(row["role"])
        if (
            not isinstance(row["record_id"], str)
            or not row["record_id"]
            or row["record_kind"] != "pooled_source_bin"
            or row["terrestrial_denominator_admitted"] is not False
            or row["native_sample_allocation_verified"] is not False
        ):
            refuse(
                "Derived coverage cannot upgrade pooled support or denominator authority"
            )
        panel = positive(row["modelled_panel_count"], 2**53)
        full, excluded = row["native_full_pollen_N"], row["excluded_native_pollen_N"]
        if full is None:
            if excluded is not None:
                refuse(
                    "Unknown native full pollen totals imply unknown excluded totals"
                )
        elif (
            type(full) is not int
            or full < panel
            or type(excluded) is not int
            or excluded != full - panel
            or row["native_lineage_ref"] is None
        ):
            refuse(
                "Known native coverage requires consistent independently referenced totals"
            )
        if row["native_lineage_ref"] is not None:
            reference(row["native_lineage_ref"])
    if sorted(roles) != ["local", "regional"]:
        refuse("Pooled support roles must be unique")


def _finite(value: object) -> bool:
    if type(value) not in {int, float}:
        return False
    try:
        return isfinite(cast(float, value))
    except OverflowError:
        return False


def _coordinates(coords: list[Any]) -> None:
    regional = []
    local: dict[float, list[str]] = {}
    for entry in coords:
        item = fields(
            entry, {"role", "taxon", "ring_mean_m", "unit", "source_unit", "conversion"}
        )
        if (
            not isinstance(item["taxon"], str)
            or not item["taxon"]
            or item["unit"] != "fraction"
        ):
            refuse("Require literal taxon coordinates in explicit fraction units")
        if item["role"] == "regional":
            if (
                local
                or item["ring_mean_m"] is not None
                or item["source_unit"] != "percent"
                or item["conversion"] != "divide_by_100"
            ):
                refuse(
                    "Regional coordinates require explicit percent-to-fraction conversion"
                )
            regional.append(item["taxon"])
        elif item["role"] == "local":
            ring = item["ring_mean_m"]
            if (
                not _finite(ring)
                or ring <= 0
                or item["source_unit"] != "fraction"
                or item["conversion"] != "identity"
            ):
                refuse("Local coordinates require finite positive ring support")
            local.setdefault(ring, []).append(item["taxon"])
        else:
            refuse(
                "Coordinate roles must preserve the paired regional and local estimands"
            )
    if (
        not regional
        or len(set(regional)) != len(regional)
        or not local
        or any(taxa != regional for taxa in local.values())
    ):
        refuse("Coordinate groups must retain one common ordered taxon axis")


def _cover_relation(row: dict[str, Any]) -> None:
    """Check adjusted local estimands without an engine or false raw-sum closure."""
    raw, adjusted = row["raw_values"], row["adjusted_values"]
    groups: dict[float, list[int]] = {}
    for index, coordinate in enumerate(row["coordinates"]):
        if coordinate["role"] == "regional":
            if raw[index] != adjusted[index]:
                refuse("Regional values must remain identical across estimands")
        else:
            groups.setdefault(coordinate["ring_mean_m"], []).append(index)
    for indices in groups.values():
        largest = max(raw[index] for index in indices)
        if largest <= 0:
            refuse("Adjusted local cover requires surviving positive raw mass")
        scaled = [max(raw[index], 0) / largest for index in indices]
        total = fsum(scaled)
        for index, value in zip(indices, scaled, strict=True):
            actual = adjusted[index]
            if not 0 <= actual <= 1 or not isclose(
                actual, value / total, rel_tol=0, abs_tol=COVER_RELATION_ABS_TOL
            ):
                refuse("Adjusted local cover differs from positive-part raw closure")


def _outcomes(rows: object, *, weighted: bool) -> list[dict[str, Any]]:
    if not isinstance(rows, list) or not 1 <= len(rows) <= 16:
        refuse("Derived case inventory is ambiguous")
    ids = []
    common = None
    for entry in rows:
        row = fields(
            entry,
            {
                "case_id",
                "mass",
                "request_ref",
                "parameter_declaration_ref",
                "status",
                "reason_code",
                "coordinates",
                "raw_values",
                "adjusted_values",
                "child_manifest_sha256",
                "child_scientific_content_sha256",
            },
        )
        ids.append(identifier(row["case_id"]))
        reference(row["request_ref"])
        reference(row["parameter_declaration_ref"])
        if weighted:
            weight = row["mass"]
            if type(weight) is not str:
                refuse("Design mass must be a canonical positive exact rational")
            try:
                rational = Fraction(weight)
            except (ValueError, ZeroDivisionError) as error:
                refuse(f"Invalid rational design mass: {type(error).__name__}")
            if (
                rational <= 0
                or str(rational) != weight
                or max(rational.numerator, rational.denominator) > 2**53 - 1
            ):
                refuse("Design mass must be a bounded positive exact rational")
        elif row["mass"] is not None:
            refuse("Unweighted sensitivity cannot acquire implicit masses")
        if row["status"] == "refused":
            if row["reason_code"] not in NUMERICAL_REASONS or any(
                row[key] is not None
                for key in (
                    "coordinates",
                    "raw_values",
                    "adjusted_values",
                    "child_manifest_sha256",
                    "child_scientific_content_sha256",
                )
            ):
                refuse("Refused outcomes must not contain successful derived vectors")
        elif row["status"] == "success":
            if row["reason_code"] is not None:
                refuse("Successful outcomes cannot carry a refusal")
            for key in ("child_manifest_sha256", "child_scientific_content_sha256"):
                _hash(row[key])
            coords = row["coordinates"]
            if (
                not isinstance(coords, list)
                or not coords
                or 2 * len(coords) ** 2 > 1_000_000
            ):
                refuse("Coordinate inventory exceeds the derived covariance budget")
            _coordinates(coords)
            if common is None:
                common = coords
            elif common != coords:
                refuse(
                    "All conditional cases must retain one fixed coordinate inventory"
                )
            for values in (row["raw_values"], row["adjusted_values"]):
                if (
                    not isinstance(values, list)
                    or len(values) != len(coords)
                    or any(not _finite(v) for v in values)
                ):
                    refuse(
                        "Success requires finite complete raw and adjusted derived vectors"
                    )
            _cover_relation(row)
        else:
            refuse("Unknown outcomes cannot silently remove design cases")
    if ids != sorted(set(ids)):
        refuse("Derived cases must have unique canonical enumeration")
    if weighted and sum(Fraction(row["mass"]) for row in rows) != 1:
        refuse("Full supplied design mass must survive all outcomes")
    return rows


def scientific_identity(value: dict[str, Any]) -> str:
    """Bind derived values and exact provenance independently of private locations."""
    stable = {
        key: item for key, item in value.items() if key != "scientific_content_sha256"
    }
    # Child manifest hashes retain timestamps; numerical identity is recorded separately.
    stable["cases"] = [
        {key: item for key, item in row.items() if key != "child_manifest_sha256"}
        for row in value["cases"]
    ]
    return digest(canonical(stable))


@dataclass(frozen=True)
class SourceCaseProduct:
    """An internally verified derived view, without source or rights admission."""

    directory: Path
    manifest_sha256: str
    canonical_manifest: str

    def manifest(self) -> dict[str, Any]:
        """Return an independent view without lending the accepted manifest."""
        return dict(json.loads(self.canonical_manifest))


def read_source_lra_cases(
    directory: Path, *, expected_manifest_sha256: str | None = None
) -> SourceCaseProduct:
    """Verify a bounded derived manifest; source references remain references."""
    directory = directory.absolute()
    with BoundedInputTree(directory, max_bytes=64 * 1024 * 1024, max_files=1) as tree:
        if set(tree.files) != {"manifest.json"}:
            refuse("Derived products must not embed original inputs or child bundles")
        raw = tree.read(directory / "manifest.json")
        checksum = digest(raw)
        if (
            expected_manifest_sha256 is not None
            and checksum != expected_manifest_sha256
        ):
            refuse("Derived product differs from the independent expected digest")
        value = json.loads(raw)
        if canonical(value) != raw:
            refuse("Derived manifest requires canonical finite JSON")
        fields(
            value,
            {
                "schema_version",
                "profile",
                "purpose",
                "scientific_acceptance",
                "source_inputs_embedded",
                "source_redistribution_authorized",
                "empirical_source_authenticity_verified",
                "plan_sha256",
                "envelope_ref",
                "design_kind",
                "law_ref",
                "source_coverage",
                "source_parameter_uncertainty_propagated",
                "cases",
                "summaries",
                "code_identity",
                "scientific_content_sha256",
            },
        )
        if (
            value["schema_version"] != "lra-source-case-product.v1"
            or value["profile"] != PROFILE
            or value["purpose"] != "exploratory"
            or value["scientific_acceptance"] != "not_evaluated"
            or any(
                value[key] is not False
                for key in (
                    "source_inputs_embedded",
                    "source_redistribution_authorized",
                    "empirical_source_authenticity_verified",
                    "source_parameter_uncertainty_propagated",
                )
            )
        ):
            refuse(
                "Conditional products cannot grant scientific or redistribution authority"
            )
        if value["design_kind"] not in {
            "caller_weighted_finite_design",
            "unweighted_sensitivity",
        }:
            refuse(
                "Unknown design claims cannot acquire conditional probability authority"
            )
        weighted = value["design_kind"] == "caller_weighted_finite_design"
        if weighted:
            reference(value["law_ref"])
        elif value["law_ref"] is not None:
            refuse("Unweighted sensitivity cannot claim a supplied design law")
        reference(value["envelope_ref"])
        _hash(value["plan_sha256"])
        _coverage(value["source_coverage"])
        rows = _outcomes(value["cases"], weighted=weighted)
        if design_summaries(rows, weighted=weighted) != value["summaries"]:
            refuse("Derived summaries differ from their retained case outcomes")
        if scientific_identity(value) != value["scientific_content_sha256"]:
            refuse("Derived scientific identity differs from the complete manifest")
        tree.check()
    return SourceCaseProduct(directory, checksum, raw.decode())
