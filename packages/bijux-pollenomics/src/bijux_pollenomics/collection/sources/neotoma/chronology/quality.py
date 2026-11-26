"""Descriptive support diagnostics for separate source-owned chronology profiles."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import math
from typing import Any

from ..relational.chronology import require_neotoma_point_age
from ..relational.identifiers import digest

Row = Mapping[str, Any]
_CALENDAR_BP_TYPES = {"Calendar years BP", "Calibrated radiocarbon years BP"}
_OWNER_FIELDS = ("collection_unit_id", "site_id", "country_code")
_DEPTH_UNIT_FIELDS = ("depthunits", "depthunit", "depth_unit", "depth_units")
_CM = {"cm", "centimeter", "centimeters", "centimetre", "centimetres"}
SOURCE_PROFILE: dict[str, Any] = {
    "name": "documented_neotoma_cm_midpoint_and_sample_owned_calendar_bp",
    "depth_unit": "cm",
    "depth_basis": "source analysis-unit and chronology-control midpoints",
    "depth_contract_sources": [
        "https://open.neotomadb.org/dbschema/tables/analysisunits.html",
        "https://open.neotomadb.org/dbschema/tables/chroncontrols.html",
    ],
    "reliable_age_bound_source": "https://open.neotomadb.org/manual/chronology-age-related-tables-1.html#chronologies",
    "interpretation": "Source assignment spacing, reversals and declared support only; no hiatus, calibrated precision, fitted model extrapolation or ecological event is inferred.",
    "eligibility_changed": False,
    "chronology_selected": False,
}


def _index(rows: Sequence[Row], field: str) -> dict[str, Row]:
    result = {}
    for row in rows:
        identity = row.get(field)
        if not isinstance(identity, str) or not identity or identity in result:
            raise ValueError(f"Neotoma chronology quality requires unique {field}")
        result[identity] = row
    return result


def _number(value: object, name: str) -> tuple[int | float | None, str | None]:
    if value is None:
        return None, f"missing_{name}"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None, f"invalid_{name}"
    try:
        if math.isfinite(value):
            return value, None
    except OverflowError:
        pass
    return None, f"nonfinite_{name}"


def _unit_contradiction(row: Row) -> bool:
    payload = row.get("source_payload")
    if not isinstance(payload, Mapping):
        return False
    return any(
        field in payload
        and payload[field] is not None
        and (
            not isinstance(payload[field], str)
            or payload[field].strip().casefold() not in _CM
        )
        for field in _DEPTH_UNIT_FIELDS
    )


def _owned(row: Row, owner: Row) -> bool:
    return all(
        isinstance(owner.get(field), str)
        and bool(owner[field])
        and row.get(field) == owner[field]
        for field in _OWNER_FIELDS
    )


def _point(claim: Row) -> tuple[int | float | None, str]:
    point, reason = _number(claim.get("source_age_value"), "source_point_age")
    if reason:
        return None, reason
    if claim.get("comparability_status") != "comparable":
        return None, "source_calendar_comparability_not_admitted"
    if (
        claim.get("source_age_type") not in _CALENDAR_BP_TYPES
        or claim.get("source_age_unit") != "year"
    ):
        return None, "unavailable_calendar_age_basis"
    try:
        point = require_neotoma_point_age(
            point,
            younger_bp=claim.get("younger_bp"),
            older_bp=claim.get("older_bp"),
            require_bounds=True,
        )
    except ValueError as error:
        return None, f"source_point_{error}"
    return point, "finite_source_point_age"


def _control_support(
    controls: Sequence[Row], conflicts: Mapping[str, Row], owner: Row
) -> tuple[list[int | float], str, set[str]]:
    flags: set[str] = set()
    depths = []
    for control in controls:
        if not _owned(control, owner):
            flags.add("chronology_control_ownership_mismatch")
        if _unit_contradiction(control):
            flags.add("explicit_depth_unit_contradiction")
        point, reason = _number(
            control.get("source_payload", {}).get("depth"), "source_control_depth"
        )
        if reason:
            flags.add(reason)
        elif point is not None:
            depths.append(point)
        conflict = conflicts.get(control["chronology_control_id"])
        if conflict is None:
            continue
        variants = conflict.get("detail", {}).get("variants")
        if not isinstance(variants, list) or not variants:
            flags.add("conflicting_control_depth_support")
            continue
        for variant in variants:
            if (
                not isinstance(variant, Mapping)
                or not _owned(variant, owner)
                or variant.get("chronology_id") != control.get("chronology_id")
                or variant.get("chronology_control_id")
                != control["chronology_control_id"]
            ):
                flags.add("conflicting_control_depth_support")
                continue
            if _unit_contradiction(variant):
                flags.add("explicit_depth_unit_contradiction")
            alternate, alternate_reason = _number(
                variant.get("source_payload", {}).get("depth"), "source_control_depth"
            )
            if alternate_reason is not None or alternate != point:
                flags.add("conflicting_control_depth_support")
    if "conflicting_control_depth_support" in flags:
        status = "unavailable_conflicting_control_depth_support"
    elif flags:
        status = "unavailable_source_control_support"
    elif not depths:
        status = "unavailable_source_control_depths"
    else:
        status = "source_control_midpoint_envelope"
    return depths, status, flags


def assess_neotoma_chronology_quality(
    *,
    samples: Sequence[Row],
    age_claims: Sequence[Row],
    chronologies: Sequence[Row],
    chronology_controls: Sequence[Row],
    conflicts: Sequence[Row] = (),
) -> dict[str, Any]:
    """Describe metadata support without selecting a model or changing admission.

    Profiles keep dataset, core, chronology and source age basis separate. The
    documented cm profile supplies absent unit labels; explicit contrary labels
    refuse coordinate comparisons. Source reliable age bounds and the envelope
    of control midpoint depths are independent diagnostics.
    """
    sample_index = _index(samples, "sample_id")
    model_index = _index(chronologies, "chronology_id")
    _index(age_claims, "chronology_claim_id")
    _index(chronology_controls, "chronology_control_id")
    control_groups: dict[str, list[Row]] = defaultdict(list)
    for control in chronology_controls:
        control_groups[control["chronology_id"]].append(control)
    conflict_index: dict[str, Row] = {}
    model_conflicts: dict[str, Row] = {}
    for conflict in conflicts:
        kind = conflict.get("conflict_kind")
        if kind in {
            "chronology_control_payload_conflict",
            "chronology_payload_conflict",
        }:
            subject = conflict.get("subject_id")
            if not isinstance(subject, str):
                raise ValueError("Neotoma chronology conflict subject must be named")
            index = (
                conflict_index
                if kind == "chronology_control_payload_conflict"
                else model_conflicts
            )
            if subject in index:
                raise ValueError("Duplicate Neotoma chronology conflict subject")
            index[subject] = conflict
    groups: dict[tuple[Any, ...], list[tuple[Row, Row]]] = defaultdict(list)
    sample_flags: dict[str, set[str]] = {
        identity: {"explicit_depth_unit_contradiction"}
        if _unit_contradiction(sample)
        else set()
        for identity, sample in sample_index.items()
    }
    claim_diagnostics: dict[str, dict[str, Any]] = {}
    for claim in age_claims:
        identity = claim["chronology_claim_id"]
        subject = claim.get("subject_id")
        sample = sample_index.get(subject) if isinstance(subject, str) else None
        if sample is None:
            claim_diagnostics[identity] = {
                "sample_id": claim.get("subject_id"),
                "point_status": "unavailable_missing_source_sample",
                "flags": ["missing_source_sample"],
                "profile_id": None,
            }
            continue
        key = tuple(
            sample.get(field) for field in ("dataset_id", *_OWNER_FIELDS)
        ) + tuple(
            claim.get(field)
            for field in ("chronology_id", "source_age_type", "source_age_unit")
        )
        groups[key].append((sample, claim))
    profiles = []
    for key, members in sorted(groups.items(), key=lambda item: repr(item[0])):
        profile_id = "neotoma:chronology-quality:" + digest(key)[:24]
        owner, first = members[0]
        model_id = first.get("chronology_id")
        model = model_index.get(model_id) if isinstance(model_id, str) else None
        flags: set[str] = set()
        model_valid = model is not None and _owned(model, owner)
        if model is None:
            flags.add("source_chronology_model_unavailable")
        elif not model_valid:
            flags.add("chronology_model_ownership_mismatch")
        metadata = (
            model.get("source_payload", {}).get("chronology")
            if model is not None
            else None
        )
        metadata = metadata if isinstance(metadata, Mapping) else {}
        basis_matches = (
            first.get("source_age_type") in _CALENDAR_BP_TYPES
            and first.get("source_age_unit") == "year"
            and metadata.get("modelagetype") == first.get("source_age_type")
        )
        conflicting_bounds = False
        conflict = model_conflicts.get(model_id) if isinstance(model_id, str) else None
        if conflict is not None:
            detail = conflict.get("detail")
            variants = detail.get("variants") if isinstance(detail, Mapping) else None
            if not isinstance(variants, list) or len(variants) < 2:
                variants = [None]
            source_range = metadata.get("agerange")
            source_range = source_range if isinstance(source_range, Mapping) else {}
            baseline_bounds = (
                _number(
                    source_range.get("ageboundyounger"), "source_reliable_age_bound"
                ),
                _number(source_range.get("ageboundolder"), "source_reliable_age_bound"),
            )
            for variant in variants:
                if (
                    not isinstance(variant, Mapping)
                    or variant.get("chronology_id") != model_id
                    or not _owned(variant, owner)
                ):
                    model_valid = False
                    flags.add("conflicting_chronology_model_ownership")
                    continue
                payload = variant.get("source_payload")
                variant_metadata = (
                    payload.get("chronology") if isinstance(payload, Mapping) else None
                )
                if not isinstance(variant_metadata, Mapping):
                    model_valid = False
                    flags.add("conflicting_chronology_model_metadata")
                    continue
                if variant_metadata.get("modelagetype") != metadata.get("modelagetype"):
                    basis_matches = False
                    flags.add("conflicting_chronology_model_age_basis")
                variant_range = variant_metadata.get("agerange")
                variant_range = (
                    variant_range if isinstance(variant_range, Mapping) else {}
                )
                variant_bounds = (
                    _number(
                        variant_range.get("ageboundyounger"),
                        "source_reliable_age_bound",
                    ),
                    _number(
                        variant_range.get("ageboundolder"), "source_reliable_age_bound"
                    ),
                )
                if variant_bounds != baseline_bounds:
                    conflicting_bounds = True
        if model_valid and not basis_matches:
            flags.add("model_age_basis_mismatch")
        source_bounds = metadata.get("agerange")
        source_bounds = source_bounds if isinstance(source_bounds, Mapping) else {}
        younger, younger_reason = _number(
            source_bounds.get("ageboundyounger"), "source_reliable_age_bound"
        )
        older, older_reason = _number(
            source_bounds.get("ageboundolder"), "source_reliable_age_bound"
        )
        if not model_valid:
            bound_status = "unavailable_source_chronology_model"
        elif not basis_matches:
            bound_status = "unavailable_model_age_basis_mismatch"
        elif conflicting_bounds:
            bound_status = "unavailable_conflicting_source_reliable_age_bounds"
            flags.add("conflicting_source_reliable_age_bounds")
        elif younger_reason or older_reason:
            bound_status = "unavailable_source_reliable_age_bounds"
            flags.update(reason for reason in (younger_reason, older_reason) if reason)
        elif younger is not None and older is not None and younger <= older:
            bound_status = "source_declared_reliable_age_bounds"
        else:
            bound_status = "unavailable_reversed_reliable_age_bounds"
            flags.add("reversed_source_reliable_age_bounds")
        controls = control_groups.get(model_id, []) if isinstance(model_id, str) else []
        control_depths, envelope_status, control_flags = _control_support(
            controls, conflict_index, owner
        )
        flags.update(control_flags)
        unit_bad = (
            any(_unit_contradiction(sample) for sample, _ in members)
            or "explicit_depth_unit_contradiction" in control_flags
        )
        if unit_bad:
            flags.add("explicit_depth_unit_contradiction")
        coordinate_status = (
            "refused_explicit_depth_unit_contradiction"
            if unit_bad
            else "documented_source_cm_midpoints"
        )
        if not model_valid or not basis_matches:
            envelope_status = "unavailable_source_chronology_model"
        if unit_bad:
            envelope_status = "unavailable_depth_unit_contradiction"
        context_flags = set(flags)
        points = []
        depths: dict[str, int | float] = {}
        outside_bounds = []
        outside_controls = set()
        claim_counts: dict[str, int] = defaultdict(int)
        for sample, _claim in members:
            claim_counts[sample["sample_id"]] += 1
        for sample, claim in members:
            identity, sample_id = claim["chronology_claim_id"], sample["sample_id"]
            local: set[str] = set()
            valid_owner = (
                _owned(claim, sample)
                and claim.get("dataset_id") == sample.get("dataset_id")
                and claim.get("subject_type") == "sample"
            )
            if not valid_owner:
                local.add("sample_age_ownership_mismatch")
            point, point_status = _point(claim)
            if point_status != "finite_source_point_age":
                local.add(point_status)
            depth, depth_reason = _number(sample.get("source_depth"), "source_depth")
            if depth_reason:
                local.add(depth_reason)
            elif depth is not None:
                depths[sample_id] = depth
            if claim_counts[sample_id] != 1:
                local.add("ambiguous_source_age_assignment")
            usable = valid_owner and claim_counts[sample_id] == 1
            if point is not None and usable:
                points.append((sample_id, identity, point))
                if (
                    bound_status == "source_declared_reliable_age_bounds"
                    and younger is not None
                    and older is not None
                    and not younger <= point <= older
                ):
                    outside_bounds.append(identity)
                    local.add("source_point_age_outside_reliable_bounds")
            if (
                usable
                and depth is not None
                and envelope_status == "source_control_midpoint_envelope"
                and not min(control_depths) <= depth <= max(control_depths)
            ):
                outside_controls.add(sample_id)
                local.add("sample_depth_outside_control_midpoint_envelope")
            sample_flags[sample_id].update(local)
            flags.update(local)
            claim_diagnostics[identity] = {
                "sample_id": sample_id,
                "point_status": point_status,
                "flags": sorted(local),
                "profile_id": profile_id,
            }
        unique_depths = sorted(set(depths.values()))
        depth_gaps = [
            b - a for a, b in zip(unique_depths[:-1], unique_depths[1:], strict=True)
        ]
        if any(_number(gap, "derived_depth_spacing")[1] for gap in depth_gaps):
            flags.add("nonfinite_derived_depth_spacing")
            depth_gaps = []
        duplicates = len(depths) != len(unique_depths)
        if duplicates:
            flags.add("duplicate_source_depth_levels")
        ordered = sorted(
            (depths[sample_id], sample_id, identity, point)
            for sample_id, identity, point in points
            if sample_id in depths
        )
        reversals = []
        point_gaps = []
        if unit_bad:
            order_status = "unavailable_depth_unit_contradiction"
        elif duplicates:
            order_status = "unavailable_duplicate_depth_levels"
        elif len(depths) != len(claim_counts):
            order_status = "unavailable_incomplete_source_depth"
        elif not model_valid or not basis_matches:
            order_status = "unavailable_source_chronology_model"
        elif len(ordered) < 2:
            order_status = "unavailable_insufficient_source_points"
        else:
            for left, right in zip(ordered[:-1], ordered[1:], strict=True):
                gap = right[3] - left[3]
                point_gaps.append(gap)
                if gap < 0:
                    reversals.append(
                        {"shallower_sample_id": left[1], "deeper_sample_id": right[1]}
                    )
                    for sample_id, claim_id in (
                        (left[1], left[2]),
                        (right[1], right[2]),
                    ):
                        sample_flags[sample_id].add(
                            "source_point_age_reversal_with_depth"
                        )
                        claim_diagnostics[claim_id]["flags"] = sorted(
                            set(claim_diagnostics[claim_id]["flags"])
                            | {"source_point_age_reversal_with_depth"}
                        )
            order_status = (
                "source_point_reversal" if reversals else "ordered_source_points"
            )
        if reversals:
            flags.add("source_point_age_reversal_with_depth")
        for sample_id in claim_counts:
            sample_flags[sample_id].update(context_flags)
        positive_gaps = [gap for gap in point_gaps if gap > 0]
        profiles.append(
            {
                "profile_id": profile_id,
                "dataset_id": owner.get("dataset_id"),
                **{field: owner.get(field) for field in _OWNER_FIELDS},
                "chronology_id": first.get("chronology_id"),
                "source_age_type": first.get("source_age_type"),
                "source_age_unit": first.get("source_age_unit"),
                "sample_count": len(claim_counts),
                "source_point_count": len(points),
                "finite_unique_depth_levels": len(unique_depths),
                "depth_coordinate_status": coordinate_status,
                "depth_unit": None if unit_bad else "cm",
                "depth_coordinate_profile": SOURCE_PROFILE["name"],
                "depth_contract_sources": list(
                    SOURCE_PROFILE["depth_contract_sources"]
                ),
                "depth_profile_complete": len(depths) == len(claim_counts),
                "maximum_adjacent_depth_gap_native": max(depth_gaps)
                if depth_gaps and not unit_bad
                else None,
                "maximum_adjacent_depth_gap_cm": max(depth_gaps)
                if depth_gaps and not unit_bad
                else None,
                "point_age_order_status": order_status,
                "maximum_positive_adjacent_point_age_gap_bp": max(positive_gaps)
                if positive_gaps
                else None,
                "point_spacing_scope": "finite_admitted_calendar_points_in_this_source_profile_not_chronological_precision",
                "age_reversal_pairs": reversals,
                "reliable_age_bounds_status": bound_status,
                "point_claim_ids_outside_reliable_age_bounds": sorted(outside_bounds),
                "control_envelope_status": envelope_status,
                "sample_ids_outside_control_midpoint_envelope": sorted(
                    outside_controls
                ),
                "captured_top_sample_ids": sorted(
                    s for s, depth in depths.items() if depth == min(unique_depths)
                )
                if unique_depths and not unit_bad
                else [],
                "captured_bottom_sample_ids": sorted(
                    s for s, depth in depths.items() if depth == max(unique_depths)
                )
                if unique_depths and not unit_bad
                else [],
                "captured_endpoint_scope": "finite_reported_source_depths_only_not_complete_recovered_core",
                "captured_bottom_status": "deepest_captured_sample_not_verified_core_base"
                if unique_depths and not unit_bad
                else "unavailable_source_depth_order",
                "flags": sorted(flags),
            }
        )
    addressed = {claim.get("subject_id") for claim in age_claims}
    for sample_id in sample_flags:
        if sample_id not in addressed:
            sample_flags[sample_id].add("sample_has_no_source_age_claim")
    return {
        "schema_version": "neotoma-source-chronology-quality.v1",
        "source_profile": {
            **SOURCE_PROFILE,
            "depth_contract_sources": list(SOURCE_PROFILE["depth_contract_sources"]),
        },
        "source_denominators": {
            "samples": len(samples),
            "age_claims": len(age_claims),
            "chronologies": len(chronologies),
            "chronology_controls": len(chronology_controls),
            "source_conflicts": len(conflicts),
        },
        "diagnostic_denominators": {
            "profiles": len(profiles),
            "samples_with_flags": sum(bool(flags) for flags in sample_flags.values()),
            "claims_without_profile": sum(
                row["profile_id"] is None for row in claim_diagnostics.values()
            ),
            "claim_point_status_counts": dict(
                sorted(
                    Counter(
                        row["point_status"] for row in claim_diagnostics.values()
                    ).items()
                )
            ),
            "profile_point_order_status_counts": dict(
                sorted(
                    Counter(row["point_age_order_status"] for row in profiles).items()
                )
            ),
            "profile_reliable_bound_status_counts": dict(
                sorted(
                    Counter(
                        row["reliable_age_bounds_status"] for row in profiles
                    ).items()
                )
            ),
            "profile_control_envelope_status_counts": dict(
                sorted(
                    Counter(row["control_envelope_status"] for row in profiles).items()
                )
            ),
        },
        "claim_diagnostic_semantics": "Claim flags describe that claim's value, parent identity and point-order comparisons; profile_id links shared model, controls, coordinate-unit and support flags. Sample flags also include that shared context. None is a new admission decision.",
        "profiles": profiles,
        "sample_flags": {
            key: sorted(value) for key, value in sorted(sample_flags.items())
        },
        "claim_diagnostics": claim_diagnostics,
    }
