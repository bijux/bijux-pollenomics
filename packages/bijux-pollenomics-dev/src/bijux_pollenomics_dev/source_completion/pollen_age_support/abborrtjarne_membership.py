"""Bound ABBO closed-taxon pollen mass under marginal age-interval membership."""

from __future__ import annotations

import argparse
from collections import Counter
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
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support import interval_fraction
from bijux_pollenomics_dev.source_completion.pollen_age_support.interval_fraction import (
    interval_bin_membership,
    pooled_fraction_outer_bounds,
)

SUPPORT = Path(
    "docs/report/pollen-reconstruction/age-interval-sensitivity/age-bin-support.csv"
)
MANIFEST = Path(
    "docs/report/pollen-reconstruction/age-interval-sensitivity/input-manifest.json"
)
CONFIG = Path("docs/report/pollen-reconstruction/age-interval-sensitivity/config.json")
REPLAY = Path("docs/report/pollen-reconstruction/age-interval-sensitivity/replay.py")
HELPER = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_age_support/interval_fraction.py"
)
SOURCE_SHA256 = {
    "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-004.json": "d96046c88b497ba07082120e446fecacad0d9b5533d8960bdbc03811976ea435",
    "docs/report/pollen-reconstruction/swedish-direct-pollen/prepared/dataset-19913.json": "fad881f64fae9fcf632854068274375f4f842398cfe2255ba71b68e9a6335d79",
    "docs/report/pollen-reconstruction/swedish-direct-pollen/prepared/dataset-53995.json": "7ff0ce9286983ab726e6fb9bcd95df3cf393ef0df7efde81a79b78d2c3fd92e5",
    "docs/report/pollen-reconstruction/swedish-direct-pollen/prepared/dataset-54001.json": "3231eb8ca83f99b3ecdeca8eb8aacc7f60c4bbf2547dca2c0e2c23a98e98b520",
    "docs/report/source-relations/neotoma/legacyage-chronology/sample-depth-join.csv": "00fb70fc6201b07873d2ec13ea59ec6018c656ae5f680f881c055d1a0a4b4ac6",
}
SOURCE_INPUT_SHA256 = {
    SUPPORT: "26ca6dc862790c71a3a7821b027413307dd2334856080a1b07e186177cfb8e01",
    MANIFEST: "29c59ac308596444ee7abae1a1e4fe81e530157ee073dce5adc593a3fc99f4f4",
    CONFIG: "7488562b4878de2eb7ac14466c0732ce455711edb01ec80181aff91d74bbef9a",
    REPLAY: "b01db6948389e33bad5e88afd4b08fa954ccaf3fd893d01e92a8d504c5e1a4f0",
    HELPER: "0c61fb0d4b693f4ed65156fcf0ecea10535e31d515f5145407bccff55c15cfb1",
    **{Path(path): digest for path, digest in SOURCE_SHA256.items()},
}
SOURCE_REPLAY_SHA256 = (
    "b01db6948389e33bad5e88afd4b08fa954ccaf3fd893d01e92a8d504c5e1a4f0"
)
EXPECTED_BOUNDS = {
    3: (Fraction(483, 2203), Fraction(14, 41)),
    4: (Fraction(2283, 6823), Fraction(3847, 8958)),
    5: (Fraction(1895, 4979), Fraction(5103, 11483)),
    9: (Fraction(167, 409), Fraction(3963, 7111)),
}
SUPPORT_FIELDS = (
    "sample_id",
    "depth_cm",
    "neotoma_age_cal_bp",
    "legacyage_min_cal_bp",
    "legacyage_max_cal_bp",
    "possible_common_bins",
    "contained_common_bin",
    "admission",
    "all_nisp_count",
    "closed_nisp_count",
)
MEMBERSHIP_FIELDS = (
    "sample_id",
    "depth_cm",
    "neotoma_age_cal_bp",
    "legacyage_min_cal_bp",
    "legacyage_max_cal_bp",
    "bin_id",
    "bin_younger_cal_bp",
    "bin_older_cal_bp_exclusive",
    "membership",
    "all_nisp_count",
    "closed_nisp_count",
)


def _sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def _checked_inputs(repository: Path) -> tuple[bytes, dict[str, Any]]:
    for relative, expected in SOURCE_INPUT_SHA256.items():
        path = repository / relative
        if (
            not path.is_file()
            or path.resolve(strict=True) != path
            or _sha(path) != expected
        ):
            raise ValueError(f"ABBO source byte identity differs: {relative}")
    imported_helper = Path(interval_fraction.__file__)
    if (
        not imported_helper.is_file()
        or imported_helper.is_symlink()
        or _sha(imported_helper) != SOURCE_INPUT_SHA256[HELPER]
    ):
        raise ValueError("Imported ABBO interval helper bytes differ")
    manifest = json.loads((repository / MANIFEST).read_bytes())
    config = json.loads((repository / CONFIG).read_bytes())
    if (
        manifest.get("source_sha256") != SOURCE_SHA256
        or manifest.get("config_sha256") != SOURCE_INPUT_SHA256[CONFIG]
        or manifest.get("producer_sha256") != SOURCE_REPLAY_SHA256
        or manifest.get("abbo_bins") != {"3": 1, "4": 3, "5": 3, "9": 1}
        or manifest.get("admitted_abbo_samples") != 8
        or config.get("common_age_bin_ids") != [3, 4, 5, 9]
        or config.get("age_bin_width_cal_bp") != 500
        or len(config.get("closed_taxa", [])) != 16
    ):
        raise ValueError("ABBO support declaration differs")
    return (repository / SUPPORT).read_bytes(), config


def _count(value: str, *, positive: bool = False) -> int:
    if not value.isascii() or not value.isdecimal():
        raise ValueError("ABBO pollen count is not a nonnegative integer")
    count = int(value)
    if positive and count <= 0:
        raise ValueError("ABBO native pollen mass must be positive")
    return count


def _fraction(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def derive(
    support_bytes: bytes, config: dict[str, Any]
) -> tuple[bytes, dict[str, Any]]:
    """Classify each pinned source row in each already-selected study bin."""
    reader = csv.DictReader(io.StringIO(support_bytes.decode("utf-8")))
    if tuple(reader.fieldnames or ()) != SUPPORT_FIELDS:
        raise ValueError("ABBO support ledger columns differ")
    support = list(reader)
    if len(support) != 107 or len({row["sample_id"] for row in support}) != 107:
        raise ValueError("ABBO source sample population differs")
    bins = config["common_age_bin_ids"]
    width = config["age_bin_width_cal_bp"]
    population: dict[int, dict[str, list[tuple[int, int]]]] = {
        bin_id: {"mandatory": [], "optional": [], "outside": []} for bin_id in bins
    }
    membership_rows: list[dict[str, str]] = []
    totals: Counter[str] = Counter()
    for row in support:
        if not row["sample_id"].startswith("neotoma:sample:"):
            raise ValueError("ABBO source sample identity differs")
        all_count = _count(row["all_nisp_count"], positive=True)
        closed_count = _count(row["closed_nisp_count"])
        if closed_count > all_count:
            raise ValueError("Closed16 count exceeds native pollen count")
        younger = Decimal(row["legacyage_min_cal_bp"])
        older = Decimal(row["legacyage_max_cal_bp"])
        statuses: dict[int, str] = {}
        for bin_id in bins:
            begin, end = Decimal(bin_id * width), Decimal((bin_id + 1) * width)
            status = interval_bin_membership(younger, older, begin, end)
            statuses[bin_id] = status
            population[bin_id][status].append((closed_count, all_count))
            totals[status] += 1
            membership_rows.append(
                {
                    "sample_id": row["sample_id"],
                    "depth_cm": row["depth_cm"],
                    "neotoma_age_cal_bp": row["neotoma_age_cal_bp"],
                    "legacyage_min_cal_bp": row["legacyage_min_cal_bp"],
                    "legacyage_max_cal_bp": row["legacyage_max_cal_bp"],
                    "bin_id": str(bin_id),
                    "bin_younger_cal_bp": str(begin),
                    "bin_older_cal_bp_exclusive": str(end),
                    "membership": status,
                    "all_nisp_count": str(all_count),
                    "closed_nisp_count": str(closed_count),
                }
            )
        mandatory = [
            bin_id for bin_id, status in statuses.items() if status == "mandatory"
        ]
        possible = [
            bin_id for bin_id, status in statuses.items() if status != "outside"
        ]
        admission = (
            "contained"
            if mandatory
            else "unresolved_in_common_bins"
            if possible
            else "outside_common_bins"
        )
        if (
            len(mandatory) > 1
            or row["possible_common_bins"] != ";".join(map(str, possible))
            or row["contained_common_bin"] != (str(mandatory[0]) if mandatory else "")
            or row["admission"] != admission
        ):
            raise ValueError(f"ABBO source admission differs: {row['sample_id']}")
    if totals != {"mandatory": 8, "optional": 49, "outside": 371}:
        raise ValueError("ABBO per-bin membership population differs")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=MEMBERSHIP_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(membership_rows)
    membership_bytes = stream.getvalue().encode("utf-8")
    bounds = []
    for bin_id in bins:
        selected = population[bin_id]
        mandatory_closed = sum(pair[0] for pair in selected["mandatory"])
        mandatory_native = sum(pair[1] for pair in selected["mandatory"])
        limits = pooled_fraction_outer_bounds(
            mandatory_closed, mandatory_native, selected["optional"]
        )
        if (
            limits.lower is None
            or limits.upper is None
            or limits.empty_bin_possible
            or (limits.lower, limits.upper) != EXPECTED_BOUNDS[bin_id]
        ):
            raise ValueError(f"ABBO reviewed fraction bounds differ: {bin_id}")
        bounds.append(
            {
                "bin_id": bin_id,
                "younger_cal_bp": bin_id * width,
                "older_cal_bp_exclusive": (bin_id + 1) * width,
                "mandatory_samples": len(selected["mandatory"]),
                "optional_samples": len(selected["optional"]),
                "outside_samples": len(selected["outside"]),
                "possible_samples": len(selected["mandatory"])
                + len(selected["optional"]),
                "mandatory_native_pollen_mass": mandatory_native,
                "mandatory_closed16_pollen_mass": mandatory_closed,
                "possible_native_pollen_mass": mandatory_native
                + sum(pair[1] for pair in selected["optional"]),
                "contained_closed16_fraction": _fraction(
                    Fraction(mandatory_closed, mandatory_native)
                ),
                "closed16_fraction_lower_outer_bound": _fraction(limits.lower),
                "closed16_fraction_upper_outer_bound": _fraction(limits.upper),
                "empty_bin_possible": False,
            }
        )
    report: dict[str, Any] = {
        "schema_version": "abbo-conditional-age-membership.v1",
        "source": {
            "sample_support_sha256": SOURCE_INPUT_SHA256[SUPPORT],
            "input_manifest_sha256": SOURCE_INPUT_SHA256[MANIFEST],
            "config_sha256": SOURCE_INPUT_SHA256[CONFIG],
            "source_replay_sha256": SOURCE_INPUT_SHA256[REPLAY],
            "interval_helper_sha256": SOURCE_INPUT_SHA256[HELPER],
            "original_source_sha256": SOURCE_SHA256,
            "age_source": "LegacyAge 1.0 S5 reported marginal 95% age bounds, PANGAEA.933132",
        },
        "quantity": "pooled closed 16-taxon NISP divided by all native pollen NISP among samples assigned to each selected bin",
        "membership_rule": "closed marginal age intervals against half-open 500-cal-BP study bins; mandatory if wholly contained, optional if overlapping, outside otherwise",
        "sample_count": len(support),
        "membership_row_count": len(membership_rows),
        "membership_status_counts": dict(sorted(totals.items())),
        "membership_sha256": hashlib.sha256(membership_bytes).hexdigest(),
        "bounds": bounds,
        "interpretation": "Per-bin outer extrema over independent optional sample inclusion; no joint age confidence statement, chronology/depth monotonicity, probability weighting, taxon-cover or vegetation inference.",
        "admission": "Development sensitivity only; no revised original interval-contained prediction, LRA reconstruction or scientific admission.",
    }
    return membership_bytes, report


def build(repository: Path) -> tuple[bytes, dict[str, Any]]:
    """Derive ABBO bin membership and bounds from checked source inputs."""
    repository = repository.absolute()
    if not repository.is_dir() or repository.resolve(strict=True) != repository:
        raise ValueError("ABBO repository root must be a real directory")
    support_bytes, config = _checked_inputs(repository)
    membership_bytes, report = derive(support_bytes, config)
    _checked_inputs(repository)
    return membership_bytes, report


def run(repository: Path, output: Path) -> dict[str, Any]:
    """Publish two derived diagnostics atomically below repository artifacts."""
    repository = repository.absolute()
    destination = require_absent_artifact_output(repository, output)
    membership_bytes, report = build(repository)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    try:
        (stage / "membership.csv").write_bytes(membership_bytes)
        (stage / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n"
        )
        if (
            hashlib.sha256((stage / "membership.csv").read_bytes()).hexdigest()
            != report["membership_sha256"]
        ):
            raise ValueError("ABBO membership publication bytes differ")
        _checked_inputs(repository)
        require_absent_artifact_output(repository, destination)
        os.replace(stage, destination)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return report


def main(argv: list[str] | None = None) -> int:
    """Bound ABBO closed-taxon pollen mass under marginal age-interval membership."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
