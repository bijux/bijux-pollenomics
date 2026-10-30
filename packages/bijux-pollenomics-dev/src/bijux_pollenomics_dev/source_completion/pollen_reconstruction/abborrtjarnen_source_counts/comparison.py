"""Compare original ABBO count slots after an exact complete depth binding."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from .sources import (
    AXES,
    NativeSample,
    OriginalTable,
    classify_token,
    read_native,
    read_original,
)

PROTOCOL = Path("reports/science/abborrtjarnen-source-counts/protocol.json")


def digest_records(records: list[dict[str, Any]]) -> str:
    """Hash canonical JSON for the ordered source-comparison records."""
    return hashlib.sha256(
        json.dumps(
            records,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode()
    ).hexdigest()


def depth_key(depth: Decimal) -> str:
    """Encode a decimal depth as an exact rational key."""
    value = Fraction(depth)
    return f"{value.numerator}/{value.denominator}"


def scaled_depth(depth: Decimal) -> Decimal:
    """Multiplication by 100 must not round unusually precise source labels."""
    with localcontext() as context:
        context.prec = max(28, len(depth.as_tuple().digits) + 3)
        return depth * 100


def compare_tables(
    original: OriginalTable,
    native: tuple[NativeSample, ...],
    *,
    expected_samples: int | None = None,
    expected_reported: int | None = None,
) -> dict[str, Any]:
    """Keep every shared/absent slot; never turn a missing native datum into zero."""
    original_depths = Counter(scaled_depth(row.depth_m) for row in original.rows)
    native_depths = Counter(sample.depth for sample in native)
    originals = set(original_depths)
    currents = set(native_depths)
    binding = {
        "original_rows": len(original.rows),
        "native_samples": len(native),
        "unique_original_depths": len(original_depths),
        "unique_native_depths": len(native_depths),
        "original_to_native_depth_factor": "100",
        "original_depth_unit": "m",
        "native_depth_unit": "not_explicit_in_payload",
        "duplicate_original_depths": sorted(
            depth_key(d) for d, n in original_depths.items() if n > 1
        ),
        "duplicate_native_depths": sorted(
            depth_key(d) for d, n in native_depths.items() if n > 1
        ),
        "original_only_depths": sorted(depth_key(d) for d in originals - currents),
        "native_only_depths": sorted(depth_key(d) for d in currents - originals),
        "original_order_strictly_increasing": all(
            a.depth_m < b.depth_m
            for a, b in zip(original.rows[:-1], original.rows[1:], strict=True)
        ),
        "native_order_strictly_increasing": all(
            a.depth < b.depth for a, b in zip(native[:-1], native[1:], strict=True)
        ),
        "depth_pairs_sha256": None,
    }
    bound = (
        bool(native)
        and len(original.rows)
        == len(native)
        == len(original_depths)
        == len(native_depths)
        and originals == currents
        and len({s.sample_id for s in native}) == len(native)
        and (expected_samples is None or len(native) == expected_samples)
    )
    output: dict[str, Any] = {
        "status": "refused_depth_binding",
        "depth_binding": binding,
        "comparison": None,
        "taxon_comparisons": [],
        "absence_candidates": [],
        "candidate_classification_status": "withheld_depth_binding",
    }
    if not bound:
        return output
    by_depth = {scaled_depth(row.depth_m): row for row in original.rows}
    slots: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    disagreements: list[dict[str, Any]] = []
    per_taxon: dict[str, Counter[str]] = {axis.name: Counter() for axis in AXES}
    statuses: Counter[str] = Counter()
    reported = matched = 0
    for sample in sorted(native, key=lambda item: (item.depth, item.sample_id)):
        row = by_depth[sample.depth]
        owner = {
            "native_sample_id": sample.sample_id,
            "depth_native_exact": depth_key(sample.depth),
            "original_depth_token": row.depth_token,
            "original_row_index": row.index,
        }
        pairs.append(owner)
        for axis, token in zip(AXES, row.tokens, strict=True):
            status, value, reason = classify_token(token)
            present = axis.name in sample.observed
            agrees = (
                present and value is not None and value == sample.observed[axis.name]
            )
            slot = {
                **owner,
                "taxon": axis.name,
                "original_column": axis.column,
                "native_taxon_id": axis.native_id,
                "original_token": token,
                "original_status": status,
                "original_integer_value": value,
                "original_invalid_reason": reason,
                "native_reported": present,
                "native_value": sample.observed.get(axis.name),
                "comparison_status": "matched_reported_count"
                if agrees
                else "reported_count_disagreement"
                if present
                else "absent_native_datum",
            }
            slots.append(slot)
            statuses[status] += 1
            per_taxon[axis.name][status] += 1
            if present:
                reported += 1
                matched += int(agrees)
                per_taxon[axis.name]["reported_pairs"] += 1
                per_taxon[axis.name]["matched_pairs"] += int(agrees)
                if not agrees and len(disagreements) < 8:
                    disagreements.append(slot)
            else:
                candidates.append(slot)
                per_taxon[axis.name]["absent_native_slots"] += 1
    population_matches = expected_reported is None or reported == expected_reported
    precondition = matched == reported and population_matches
    binding["depth_pairs_sha256"] = digest_records(pairs)
    output.update(
        status="reported_counts_match"
        if precondition
        else "refused_reported_count_correspondence",
        comparison={
            "total_slots": len(slots),
            "native_reported_slots": reported,
            "native_absent_slots": len(candidates),
            "reported_count_matches": matched,
            "reported_count_disagreements": reported - matched,
            "reported_population_matches": population_matches,
            "reported_count_precondition_passed": precondition,
            "original_token_status_counts": dict(statuses),
            "slot_audit_sha256": digest_records(slots),
            "reported_disagreement_examples": disagreements,
            "disagreement_examples_limit": 8,
        },
        taxon_comparisons=[
            {
                "taxon": axis.name,
                "original_column": axis.column,
                "original_epd_comment": axis.epd_comment,
                "native_taxon_id": axis.native_id,
                "reported_pairs": per_taxon[axis.name]["reported_pairs"],
                "matched_pairs": per_taxon[axis.name]["matched_pairs"],
                "absent_native_slots": per_taxon[axis.name]["absent_native_slots"],
                "original_token_status_counts": {
                    key: per_taxon[axis.name][key]
                    for key in statuses
                    if per_taxon[axis.name][key]
                },
            }
            for axis in AXES
        ],
        absence_candidates=candidates if precondition else [],
        candidate_classification_status="enabled_reported_counts_match"
        if precondition
        else "withheld_reported_count_conflict",
    )
    return output


def run(repository: Path, source_root: Path, output: Path) -> dict[str, Any]:
    """Read only committed source and the exact retained original/native inputs."""
    repository = repository.resolve()
    files = [
        PROTOCOL,
        *[p.relative_to(repository) for p in Path(__file__).parent.glob("*.py")],
    ]
    git = ["git", "-C", str(repository)]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    subprocess.run(
        [*git, "ls-files", "--error-unmatch", "--", *map(str, files)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*git, "diff", "--exit-code", revision, "--", *map(str, files)],
        check=True,
        capture_output=True,
    )
    if (
        output.exists()
        or not output.resolve().is_relative_to(repository / "artifacts")
        or any(p.is_symlink() for p in (output, *output.parents))
    ):
        raise ValueError("Result must be absent under repository artifacts")
    protocol_bytes = (repository / PROTOCOL).read_bytes()
    protocol = json.loads(protocol_bytes)
    expected_axis = [
        {
            "taxon": axis.name,
            "original_column": axis.column,
            "original_epd_comment": axis.epd_comment,
            "native_taxon_id": axis.native_id,
        }
        for axis in AXES
    ]
    if (
        protocol["axis_fields"] != expected_axis
        or protocol["join"]["required_original_rows"] != 107
        or protocol["join"]["required_native_samples"] != 107
        or protocol["count_comparison"]["required_reported_pairs"] != 527
        or protocol["count_comparison"]["all_slots"] != 535
        or protocol["count_comparison"]["expected_absent_native_slots"] != 8
    ):
        raise ValueError("Frozen source comparison dimensions or identities differ")
    bodies = {}
    identities = {}
    for relative, pin in protocol["source_store_files"].items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError("Unsafe source member")
        body = (source_root / path).read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if len(body) != pin["bytes"] or digest != pin["sha256"]:
            raise ValueError("Retained original/native source changed")
        bodies[relative] = body
        identities[f"source-store/{relative}"] = digest
    original = read_original(bodies[protocol["original_table"]].decode())
    if len(original.columns) != 95:
        raise ValueError("Original full source schema differs")
    native = read_native(
        json.loads(bodies[protocol["current_native"]], parse_float=Decimal)
    )
    result = {
        "schema_version": "abborrtjarnen-original-count-correspondence.v1",
        "source_commit": revision,
        "input_sha256": identities,
        **compare_tables(original, native, expected_samples=107, expected_reported=527),
        "scope": "local_noncommercial_source_comparison_only",
        "original_source": {
            "doi": "10.1594/PANGAEA.738429",
            "archived_from": "European Pollen Database",
            "archive_date": "2010-05-11",
            "licence": "CC-BY-NC-3.0",
            "count_unit": "#",
        },
        "native_source": {
            "dataset_id": 19913,
            "site_id": 13338,
            "collection_unit_id": 14910,
            "handle": "ABBO",
            "doi": "10.21233/2vzb-bg61",
            "count_unit": "NISP",
        },
        "model_fits": 0,
        "age_draws_consumed": 0,
        "counts_imputed": 0,
        "source_measurements_changed": False,
        "species_or_morphotype_equivalence_claim": False,
        "independent_measurement_claim": False,
        "historical_core_admission_changed": False,
        "original_table_redistributed": False,
    }
    for relative, parsed_buffer in bodies.items():
        current_buffer = (source_root / relative).read_bytes()
        if (
            len(current_buffer) != len(parsed_buffer)
            or hashlib.sha256(current_buffer).hexdigest()
            != identities[f"source-store/{relative}"]
        ):
            raise ValueError("Consumed scientific input changed during comparison")
    current_revision = subprocess.check_output(
        [*git, "rev-parse", "HEAD"], text=True
    ).strip()
    if (
        current_revision != revision
        or (repository / PROTOCOL).read_bytes() != protocol_bytes
    ):
        raise ValueError("Source revision or protocol changed during comparison")
    subprocess.run(
        [*git, "diff", "--exit-code", revision, "--", *map(str, files)],
        check=True,
        capture_output=True,
    )
    result_text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if len(result_text.encode()) > 16384:
        raise ValueError("Compact result exceeds declared output budget")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result_text)
    return result
