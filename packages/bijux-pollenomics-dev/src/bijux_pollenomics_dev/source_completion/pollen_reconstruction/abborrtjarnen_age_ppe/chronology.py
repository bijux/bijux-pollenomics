"""Authenticate qualified saved ages without refitting or resampling their rows."""

from __future__ import annotations

from collections.abc import Iterator
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from ..abborrtjarnen_ppe_dependence.sources import require

PROTOCOL = Path(
    "reports/science/pollen-reconstruction/abborrtjarnen-age-ppe/protocol.json"
)


def check_inputs(repository: Path, protocol: dict[str, Any]) -> None:
    """Check saved scientific bytes in place; create no age/archive copy."""
    for relative, expected in protocol["repository_inputs"].items():
        path = repository / relative
        require(
            not path.is_symlink() and path.resolve().is_relative_to(repository),
            "Scientific data locator escaped repository",
        )
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
                size += len(block)
        require(
            size == expected["bytes"] and digest.hexdigest() == expected["sha256"],
            f"Changed scientific data: {relative}",
        )


def authority(
    repository: Path, protocol: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Require the actual independent qualification and retain its metadata conflict."""
    check_inputs(repository, protocol)
    verified = json.loads((repository / protocol["verified_input"]).read_bytes())
    report = json.loads((repository / protocol["report_input"]).read_bytes())
    fit = json.loads((repository / protocol["fit_input"]).read_bytes())
    core = json.loads((repository / protocol["core_input"]).read_bytes())
    expected = protocol["age_authority"]
    require(
        [
            (e["seed"], e["retained_rows"], e["first_native_row"], e["last_native_row"])
            for e in protocol["age_inputs"]
        ]
        == [(314159, 16000, 3502, 19501), (271828, 16000, 3502, 19501)],
        "Frozen age-input row law differs",
    )
    require(
        verified["observer_status"] == expected["observer_status"]
        and verified["source_commit"]
        == report["source_commit"]
        == expected["source_commit"],
        "Qualified chronological source identity differs",
    )
    require(
        verified["all_unchanged_diagnostic_gates_passed"] is True
        and verified["exact_old_prefixes_matched"] is True
        and verified["score_interpretation_permitted"] is True
        and verified["joint_age_rows_checked"] == 32000
        and verified["sample_depths_checked"] == 107,
        "Saved chronology qualification incomplete",
    )
    require(
        report["requested_draws"] == 32000
        and report["conditional_sampler_diagnostics_passed"] is True
        and fit["age_diagnostics"]["qualified"] is True
        and fit["free_parameter_diagnostics"]["qualified"] is True,
        "Original sampler diagnostic criteria did not pass",
    )
    flags = report["sampler_accuracy_qualification"]
    conflict = {key: flags[key] for key in ("diagnostics_passed", "diagnostics_pass")}
    require(
        conflict
        == verified["literal_diagnostic_report_flag_conflict"]
        == expected["literal_report_flag_conflict"],
        "Literal source-report conflict differs",
    )
    require(
        [c["seed"] for c in fit["chains"]] == [314159, 271828]
        and all(
            (c["retained_rows"], c["first_native_row"], c["last_native_row"])
            == (16000, 3502, 19501)
            for c in fit["chains"]
        ),
        "Saved chain/native row law differs",
    )
    return core, {
        "source_commit": verified["source_commit"],
        "observer_status": verified["observer_status"],
        "all_unchanged_diagnostic_gates_passed": True,
        "literal_report_flag_conflict": conflict,
        "known_incomplete_closed16_draws": 1,
        "original_failed_8000_state_result_consumed": False,
    }


def age_rows(
    repository: Path, entry: dict[str, Any], sample_ids: list[str]
) -> Iterator[tuple[int, list[float]]]:
    """Preserve each source iteration/column; negative ages remain unmodified."""
    count = 0
    with gzip.open(repository / entry["path"], "rt", newline="") as stream:
        reader = csv.reader(stream)
        require(next(reader) == sample_ids, "Joint age sample-column identity differs")
        for count, raw in enumerate(reader, start=1):
            require(len(raw) == len(sample_ids) == 107, "Joint age row width differs")
            ages = [float(v) for v in raw]
            require(
                all(math.isfinite(v) for v in ages)
                and all(a <= b for a, b in zip(ages[:-1], ages[1:], strict=True)),
                "Joint age row is nonfinite or nonmonotone",
            )
            require(count <= entry["retained_rows"], "Unexpected extra saved age row")
            yield entry["first_native_row"] + count - 1, ages
    require(count == entry["retained_rows"], "Saved age chain is truncated")
