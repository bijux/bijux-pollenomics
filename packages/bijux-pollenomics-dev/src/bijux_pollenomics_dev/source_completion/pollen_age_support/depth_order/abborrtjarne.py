"""Optional depth-order consistency of the retained ABBO marginal-age ledger."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne_joint_membership as independent,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support import (
    abborrtjarne_membership,
    interval_fraction,
    joint_membership,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarne_membership import (
    CONFIG,
    MANIFEST,
    SOURCE_INPUT_SHA256,
    SUPPORT,
    SUPPORT_FIELDS,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order import (
    domains,
    extrema,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.domains import (
    AgeOrderAssessment,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.depth_order.extrema import (
    DepthCountSample,
    assess_depth_ordered_extrema,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.joint_membership import (
    AgeBin,
    MarginalAgeCountSample,
)

CORE = "neotoma-dataset:19913"
SOURCE_PINS = {
    **{path: SOURCE_INPUT_SHA256[path] for path in (SUPPORT, CONFIG, MANIFEST)},
    independent.MEMBERSHIP: independent.RETAINED_INPUTS[independent.MEMBERSHIP],
    independent.REPORT: independent.RETAINED_INPUTS[independent.REPORT],
}


def _wire(order: AgeOrderAssessment | None) -> dict[str, Any] | None:
    if order is None:
        return None
    refusal = order.refusal
    return {
        "core_id": order.core_id,
        "attainable": order.attainable,
        "assignments": [
            {
                "sample_id": row.sample_id,
                "depth_cm": str(row.depth),
                "possible_native_age": str(row.native_age),
            }
            for row in order.assignments
        ],
        "refusal": None
        if refusal is None
        else {
            "reason": "no_nondecreasing_age_in_declared_support",
            "sample_id": refusal.sample_id,
            "depth_cm": str(refusal.depth),
            "minimum_required_age": str(refusal.minimum_required_age),
            "previous_depth_sample_ids": list(refusal.previous_depth_sample_ids),
            "equal_depth_sample_ids": list(refusal.equal_depth_sample_ids),
        },
    }


def derive(support: bytes, memberships: bytes, report_bytes: bytes) -> dict[str, Any]:
    """Validate the original saved ledger, then apply only the declared order model."""
    prior: dict[str, Any] = dict(independent.derive(support, memberships, report_bytes))
    reader = csv.DictReader(io.StringIO(support.decode("utf-8")))
    if tuple(reader.fieldnames or ()) != SUPPORT_FIELDS:
        raise ValueError("Original ABBO support columns differ")
    rows = list(reader)
    samples = [
        DepthCountSample(
            MarginalAgeCountSample(
                row["sample_id"],
                Decimal(row["legacyage_min_cal_bp"]),
                Decimal(row["legacyage_max_cal_bp"]),
                int(row["closed_nisp_count"]),
                int(row["all_nisp_count"]),
            ),
            Decimal(row["depth_cm"]),
        )
        for row in rows
    ]
    bounds = prior["marginal_bounds"]
    bins = [
        AgeBin(
            row["bin_id"],
            Decimal(row["bin_id"]) * 500,
            (Decimal(row["bin_id"]) + 1) * 500,
        )
        for row in bounds
    ]
    result = assess_depth_ordered_extrema(samples, bins, core_id=CORE)
    if len(rows) != 107 or len(result.corners) != len(prior["corners"]):
        raise ValueError("Original ABBO sample/corner population differs")
    corners = []
    for old, new in zip(prior["corners"], result.corners, strict=True):
        if old["attainable"] != new.independent_corner.attainable:
            raise ValueError("Original independent feasibility changed")
        corners.append(
            {
                "targets": old["targets"],
                "independent_attainable": old["attainable"],
                "independent_refusals": old["refusals"],
                "attainable_with_order": new.attainable,
                "age_order": _wire(new.age_order),
            }
        )
    return {
        "schema_version": "abbo-conditional-depth-order.v1",
        "sample_count": len(rows),
        "distinct_depth_count": len({row.depth for row in samples}),
        "source_native_negative_younger_bound_count": prior[
            "source_native_negative_younger_bound_count"
        ],
        "membership_row_count": prior["membership_row_count"],
        "quantity": prior["quantity"],
        "marginal_bounds_unchanged": prior["marginal_bounds"],
        "independently_attainable_corners": prior[
            "simultaneously_attainable_tuple_count"
        ],
        "attainable_corners_with_order": sum(row.attainable for row in result.corners),
        "native_interval_order": _wire(result.native_interval_order),
        "corners": corners,
        "assumption": "One nondecreasing age function of native depth in the retained ABBO dataset; equal depths share one age. This is a declared conditional model, not source-verified sediment history.",
        "age_scope": "Preserves reported LegacyAge calibrated-BP marginal endpoints and native negative values; no newly qualified reference epoch, calibration model, confidence level or joint age distribution.",
        "interpretation": "Exact existence/witness/refusal under this order assumption. Original per-bin bounds and independent refusals remain unchanged. No recomputed order-constrained extrema, probability, prediction, vegetation accuracy or untouched chronology confirmation.",
    }


def _buffers(repository: Path) -> tuple[dict[Path, bytes], dict[str, Any]]:
    if not repository.is_absolute() or repository.resolve(strict=True) != repository:
        raise ValueError("A physical absolute repository is required")
    buffers: dict[Path, bytes] = {}
    identities: dict[str, Any] = {}
    for name, expected in SOURCE_PINS.items():
        path = repository / name
        info = path.lstat()
        if (
            path.resolve(strict=True) != path
            or not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_size > 1024**2
        ):
            raise ValueError("Bounded physical retained ledger required")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Retained ledger identity differs")
        buffers[name] = raw
        identities[str(name)] = {"sha256": expected, "bytes": len(raw)}
    for module in (
        independent,
        joint_membership,
        abborrtjarne_membership,
        interval_fraction,
        domains,
        extrema,
    ):
        path = Path(module.__file__ or "").absolute()
        suffix = Path("depth_order") if module in (domains, extrema) else Path()
        expected_origin = (
            repository
            / independent.MODULE_ROOT
            / suffix
            / (module.__name__.rsplit(".", 1)[-1] + ".py")
        )
        if path.resolve(strict=True) != path or path != expected_origin:
            raise ValueError(
                "Scientific module origin differs from selected repository"
            )
        raw = path.read_bytes()
        identities[str(path.relative_to(repository))] = {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        }
    own = Path(__file__).absolute()
    if (
        own.resolve(strict=True) != own
        or own != repository / independent.MODULE_ROOT / "depth_order/abborrtjarne.py"
    ):
        raise ValueError("Adapter origin differs from selected repository")
    raw = own.read_bytes()
    identities[str(own.relative_to(repository))] = {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    return buffers, identities


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Write one new source-bound diagnostic; all historical products stay literal."""
    repository = repository.absolute()
    destination = require_absent_artifact_output(repository, output)
    buffers, identities = _buffers(repository)
    result = derive(
        buffers[SUPPORT], buffers[independent.MEMBERSHIP], buffers[independent.REPORT]
    )
    result["input_and_source_identities"] = identities
    raw = (
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()
    if len(raw) > 2 * 1024**2:
        raise ValueError("Diagnostic output exceeds 2MiB")
    stage = Path(tempfile.mkdtemp(prefix=".depth-order-", dir=destination.parent))
    try:
        (stage / "report.json").write_bytes(raw)
        if _buffers(repository) != (buffers, identities):
            raise ValueError("Input or source changed before publication")
        require_absent_artifact_output(repository, destination)
        os.replace(stage, destination)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return result


def main(argv: list[str] | None = None) -> int:
    """Run only when the caller has admitted this explicitly conditional analysis."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
