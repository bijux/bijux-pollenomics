"""Diagnose joint endpoints of the retained ABBO marginal count-fraction bounds."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
from fractions import Fraction
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import TypedDict

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from . import abborrtjarne_membership, joint_membership
from .abborrtjarne_membership import (
    MEMBERSHIP_FIELDS,
    SOURCE_INPUT_SHA256,
    SUPPORT,
    SUPPORT_FIELDS,
)
from .interval_fraction import interval_bin_membership
from .joint_membership import AgeBin, MarginalAgeCountSample, assess_joint_extrema

ROOT = Path(
    "docs/report/pollen-reconstruction/age-interval-sensitivity/conditional-membership"
)
MEMBERSHIP = ROOT / "membership.csv"
REPORT = ROOT / "report.json"
RETAINED_INPUTS = {
    **SOURCE_INPUT_SHA256,
    MEMBERSHIP: "6ca70c45e9c292b485ceea31aee3cda9aa92ffb5fdc404b9f6cc70158a62a2cc",
    REPORT: "bcd838ffc4bf9221761686c180d086d62482d09bd40880a4dd75b1024ac40340",
}
MODULE_ROOT = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support"
)


class SourceIdentity(TypedDict):
    """One immutable source or code identity consumed by this diagnostic."""

    sha256: str
    size: int


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inputs(repository: Path) -> dict[str, SourceIdentity]:
    if not repository.is_dir() or repository.resolve(strict=True) != repository:
        raise ValueError("ABBO repository must be a real directory")
    identities: dict[str, SourceIdentity] = {}
    for relative, expected in RETAINED_INPUTS.items():
        path = repository / relative
        if not path.is_file() or path.resolve(strict=True) != path:
            raise ValueError(f"ABBO source must be a regular confined file: {relative}")
        data = path.read_bytes()
        if _sha(data) != expected:
            raise ValueError(f"ABBO retained source identity differs: {relative}")
        identities[str(relative)] = {"sha256": expected, "size": len(data)}
    for imported, name in (
        (Path(joint_membership.__file__ or ""), "joint_membership.py"),
        (Path(abborrtjarne_membership.__file__ or ""), "abborrtjarne_membership.py"),
        (Path(__file__), "abborrtjarne_joint_membership.py"),
    ):
        expected_path = repository / MODULE_ROOT / name
        if imported.resolve(strict=True) != expected_path:
            raise ValueError(
                "ABBO source module must be loaded from the selected repository"
            )
    for name in (
        "joint_membership.py",
        "abborrtjarne_joint_membership.py",
        "abborrtjarne_membership.py",
    ):
        path = repository / MODULE_ROOT / name
        if not path.is_file() or path.resolve(strict=True) != path:
            raise ValueError("ABBO producer code must be a regular confined file")
        data = path.read_bytes()
        identities[str(MODULE_ROOT / name)] = {"sha256": _sha(data), "size": len(data)}
    return identities


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError("ABBO JSON object required")
    return dict(value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate ABBO JSON field")
        result[key] = value
    return result


def _integer(value: object) -> int:
    if type(value) is not int:
        raise ValueError("ABBO exact integer required")
    return value


def _fraction(value: object) -> Fraction:
    fields = _object(value)
    if set(fields) != {"numerator", "denominator"}:
        raise ValueError("ABBO exact fraction fields differ")
    numerator, denominator = (
        _integer(fields["numerator"]),
        _integer(fields["denominator"]),
    )
    if not 0 <= numerator <= denominator or denominator == 0:
        raise ValueError("ABBO fraction counts differ")
    return Fraction(numerator, denominator)


def _wire(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _rows(data: bytes, fields: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
    if tuple(reader.fieldnames or ()) != fields:
        raise ValueError("ABBO source columns differ")
    result: list[dict[str, str]] = []
    for row in reader:
        if set(row) != set(fields) or any(
            not isinstance(value, str) for value in row.values()
        ):
            raise ValueError("ABBO source row width differs")
        result.append(
            {key: value for key, value in row.items() if isinstance(value, str)}
        )
    return result


def derive(
    support: bytes, memberships: bytes, report_bytes: bytes
) -> dict[str, object]:
    """Validate retained ledgers and assess exact corners without a study replay."""
    report = _object(json.loads(report_bytes, object_pairs_hook=_pairs))
    if report.get("schema_version") != "abbo-conditional-age-membership.v1":
        raise ValueError("ABBO retained report schema differs")
    raw_bounds = report.get("bounds")
    if not isinstance(raw_bounds, list) or len(raw_bounds) != 4:
        raise ValueError("ABBO four marginal bins required")
    bounds = [_object(value) for value in raw_bounds]
    bins = [
        AgeBin(
            str(_integer(row["bin_id"])),
            Decimal(_integer(row["younger_cal_bp"])),
            Decimal(_integer(row["older_cal_bp_exclusive"])),
        )
        for row in bounds
    ]
    if [bin_.bin_id for bin_ in bins] != ["3", "4", "5", "9"]:
        raise ValueError("ABBO selected study bins differ")
    rows = _rows(support, SUPPORT_FIELDS)
    if len(rows) != 107 or report.get("sample_count") != len(rows):
        raise ValueError("ABBO source population differs")
    support_by_id = {row["sample_id"]: row for row in rows}
    if len(support_by_id) != len(rows):
        raise ValueError("Duplicate ABBO source sample identity")
    samples = [
        MarginalAgeCountSample(
            row["sample_id"],
            Decimal(row["legacyage_min_cal_bp"]),
            Decimal(row["legacyage_max_cal_bp"]),
            int(row["closed_nisp_count"]),
            int(row["all_nisp_count"]),
        )
        for row in rows
    ]
    ledger = _rows(memberships, MEMBERSHIP_FIELDS)
    observed: dict[tuple[str, str], str] = {}
    for row in ledger:
        key = row["sample_id"], row["bin_id"]
        if key in observed:
            raise ValueError("Duplicate ABBO membership identity")
        source_row = support_by_id.get(row["sample_id"])
        if source_row is None or any(
            row[field] != source_row[field]
            for field in (
                "depth_cm",
                "neotoma_age_cal_bp",
                "legacyage_min_cal_bp",
                "legacyage_max_cal_bp",
                "all_nisp_count",
                "closed_nisp_count",
            )
        ):
            raise ValueError("ABBO membership source row differs")
        observed[key] = row["membership"]
    expected = {
        (sample.sample_id, bin_.bin_id): interval_bin_membership(
            sample.younger_cal_bp,
            sample.older_cal_bp,
            bin_.younger_cal_bp,
            bin_.older_cal_bp_exclusive,
        )
        for sample in samples
        for bin_ in bins
    }
    if (
        observed != expected
        or len(ledger) != 428
        or report.get("membership_row_count") != len(ledger)
        or report.get("membership_sha256") != _sha(memberships)
    ):
        raise ValueError("ABBO retained memberships differ")
    statuses = {
        status: list(observed.values()).count(status)
        for status in ("mandatory", "optional", "outside")
    }
    if report.get("membership_status_counts") != statuses:
        raise ValueError("ABBO retained membership census differs")
    assessment = assess_joint_extrema(samples, bins)
    for result, bound in zip(assessment.marginal_bounds, bounds, strict=True):
        if result.lower != _fraction(
            bound["closed16_fraction_lower_outer_bound"]
        ) or result.upper != _fraction(bound["closed16_fraction_upper_outer_bound"]):
            raise ValueError("ABBO retained marginal bounds differ")
    return {
        "schema_version": "abbo-joint-marginal-extrema.v1",
        "sample_count": len(samples),
        "membership_row_count": len(ledger),
        "source_native_negative_younger_bound_count": sum(
            sample.younger_cal_bp < 0 for sample in samples
        ),
        "extrema_tuple_count": len(assessment.corners),
        "simultaneously_attainable_tuple_count": sum(
            corner.attainable for corner in assessment.corners
        ),
        "marginal_bounds": [
            {"bin_id": row.bin_id, "lower": _wire(row.lower), "upper": _wire(row.upper)}
            for row in assessment.marginal_bounds
        ],
        "corners": [
            {
                "targets": [
                    {
                        "bin_id": target.bin_id,
                        "side": target.side,
                        "fraction": _wire(target.value),
                    }
                    for target in corner.targets
                ],
                "attainable": corner.attainable,
                "refusals": [
                    {
                        "sample_id": refusal.sample_id,
                        "reason": refusal.reason,
                        "required_bins": list(refusal.required_bins),
                        "excluded_bins": list(refusal.excluded_bins),
                    }
                    for refusal in corner.refusals
                ],
                "assignments": [
                    {
                        "sample_id": assignment.sample_id,
                        "bin_id": assignment.bin_id,
                        "possible_native_age": str(assignment.source_native_age),
                    }
                    for assignment in corner.assignments
                ],
            }
            for corner in assessment.corners
        ],
        "quantity": report.get("quantity"),
        "interpretation": "Exact conditional marginal count-fraction corner feasibility with one possible age per sample and positive mandatory mass in each bin. Original per-bin bounds remain valid. No depth monotonicity, probability, joint confidence, reestimated chronology, prediction or vegetation inference.",
        "admission": "Mathematical source-accounting diagnostic only; no scientific, source-rights, or canonical signed-age admission.",
    }


def run(repository: Path, output: Path) -> dict[str, object]:
    """Publish one source-bound diagnostic atomically to an absent artifact directory."""
    repository = repository.absolute()
    destination = require_absent_artifact_output(repository, output)
    before = _inputs(repository)
    report = derive(
        (repository / SUPPORT).read_bytes(),
        (repository / MEMBERSHIP).read_bytes(),
        (repository / REPORT).read_bytes(),
    )
    report["source_identities"] = before
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    try:
        product = stage / "report.json"
        product.write_bytes(data)
        if product.read_bytes() != data or _inputs(repository) != before:
            raise ValueError("ABBO source or publication identity changed")
        require_absent_artifact_output(repository, destination)
        os.replace(stage, destination)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return report


def main(argv: list[str] | None = None) -> int:
    """Parse repository and output boundaries for the joint source diagnostic."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args(argv)
    run(arguments.repository, arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
