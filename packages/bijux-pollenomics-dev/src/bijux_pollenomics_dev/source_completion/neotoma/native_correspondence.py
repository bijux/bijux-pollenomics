"""Run the three maintained Rootsi-to-Neotoma correspondence producers unchanged."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
    _regular_path,
)
from bijux_pollenomics_dev.source_completion import (
    abborrtjarne_native_counts,
    bokesjon_native_counts,
    bussjosjon_native_counts,
)

from .source_bound_reports import publish

SOURCE_ID = "landclim/rootsi-workbooks"
RAW = Path("data/neotoma/raw/neotoma_pollen_dataset_downloads")
BASE_DESCRIPTOR = Path(
    "configs/ci/qualified-report-sources/rootsi-bokesjon-workbook.json"
)


@dataclass(frozen=True)
class Correspondence:
    """Identify one retained producer and its exact native source scope."""

    workbook: str
    raw: Path
    schema: str
    dataset: int
    site: int
    main: Callable[[], int]
    csv: str


CASES = {
    Path(
        "configs/ci/qualified-report-sources/rootsi-abborrtjarne-workbook.json"
    ): Correspondence(
        "rootsi/ABB.xls",
        RAW / "part-004.json",
        "abborrtjarne-native-count-correspondence.v1",
        19913,
        13338,
        abborrtjarne_native_counts.main,
        "sample-correspondence.csv",
    ),
    BASE_DESCRIPTOR: Correspondence(
        "rootsi/BOKE.xls",
        RAW / "part-008.json",
        "bokesjon-native-count-correspondence.v1",
        54001,
        28872,
        bokesjon_native_counts.main,
        "cell-correspondence.csv",
    ),
    Path(
        "configs/ci/qualified-report-sources/rootsi-bussjosjon-workbook.json"
    ): Correspondence(
        "rootsi/BUS.xls",
        RAW / "part-008.json",
        "bussjosjon-native-count-correspondence.v1",
        53995,
        28869,
        bussjosjon_native_counts.main,
        "cell-correspondence.csv",
    ),
}


def run(
    repository: Path,
    source_root: Path,
    descriptor: Path,
    output: Path,
    retained_artifacts_root: Path | None = None,
) -> dict[str, Any]:
    """Preserve native producer arithmetic, raw sidecars and refusal posture."""
    if descriptor not in CASES:
        raise ReportRebuildError(
            "native correspondence descriptor is not a maintained case"
        )
    case = CASES[descriptor]

    def selection(qualified: QualifiedReportSources) -> None:
        expected = {
            BASE_DESCRIPTOR.as_posix(),
            f"external/{SOURCE_ID}/manifest.json",
            f"external/{SOURCE_ID}/rootsi/BOKE.xls",
        }
        if descriptor != BASE_DESCRIPTOR:
            expected.update(
                {descriptor.as_posix(), f"external/{SOURCE_ID}/{case.workbook}"}
            )
        if set(qualified.inputs) != expected:
            raise ReportRebuildError(
                "native correspondence qualified source population differs"
            )

    def produce(qualified: QualifiedReportSources, raw: Path) -> None:
        previous = sys.argv
        sys.argv = [
            "native-correspondence",
            "--workbook",
            str(qualified.directory / case.workbook),
            "--raw-part",
            str(repository / case.raw),
            "--output",
            str(raw),
        ]
        try:
            result = case.main()
            if type(result) is not int or result != 0:
                raise ReportRebuildError(
                    "retained native correspondence producer did not succeed"
                )
        finally:
            sys.argv = previous

    def verify(report: dict[str, Any]) -> None:
        if (
            report.get("schema_version") != case.schema
            or type(report.get("neotoma_dataset_id")) is not int
            or report["neotoma_dataset_id"] != case.dataset
            or type(report.get("neotoma_site_id")) is not int
            or report["neotoma_site_id"] != case.site
            or report.get("rootsi_archive_member") != case.workbook
            or type(report.get("lra_admitted_samples")) is not int
            or report["lra_admitted_samples"] != 0
        ):
            raise ReportRebuildError(
                "retained native correspondence report scope differs"
            )
        expected_inputs = {
            "neotoma_raw_part": hashlib.sha256(
                _regular_path(repository / case.raw).read_bytes()
            ).hexdigest(),
            "rootsi_workbook": hashlib.sha256(
                _regular_path(source_root / SOURCE_ID / case.workbook).read_bytes()
            ).hexdigest(),
        }
        if (
            report.get("input_sha256") != expected_inputs
            or report.get("basin_radius_transfer") != "refused"
        ):
            raise ReportRebuildError(
                "native correspondence source identity or basin refusal differs"
            )

    retained_arguments = (
        {"retained_artifacts_root": retained_artifacts_root}
        if retained_artifacts_root is not None
        else {}
    )
    return publish(
        repository,
        source_root,
        descriptor,
        output,
        (case.raw,),
        selection,
        produce,
        frozenset({"report.json", case.csv, "REPORT.md"}),
        verify,
        **retained_arguments,
    )


def main(argv: list[str] | None = None) -> int:
    """Run one exact source-bound native correspondence owner."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-descriptor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retained-artifacts-root", type=Path)
    args = parser.parse_args(argv)
    run(
        args.repository,
        args.source_root,
        args.source_descriptor,
        args.output,
        retained_artifacts_root=args.retained_artifacts_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
