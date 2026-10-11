"""Reproduce author site taxon-header evidence without admitting measured zeros."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
    require_relative_path,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)
from bijux_pollenomics_dev.essd_reproduction.author_taxon_support import (
    CROSSWALK,
    FORMAT_SCRIPT,
    GRIDS,
    PARAMETERS,
    publish,
)
from bijux_pollenomics_dev.source_completion.landclim_taxonomy_mass import LOOKUP
from bijux_pollenomics_dev.source_completion.pollen_taxonomy import author_mass

DESCRIPTOR = author_mass.DESCRIPTOR
SOURCE_ID = author_mass.SOURCE_ID


def _require_bound_account(report: JsonObject, identities: JsonObject) -> None:
    """Require all forty source identities and retain the original refusal scope."""
    rows = report.get("rows")
    if (
        report.get("schema_version") != "landclim-author-example-taxon-support.v1"
        or report.get("site_count") != 17
        or report.get("author_target_count") != 31
        or report.get("grid_site_counts") != GRIDS
        or report.get("all_targets_measured_admitted") is not False
        or report.get("reviewed_reveals_profile_admitted") is not False
        or not isinstance(rows, list)
        or len(rows) != 17
    ):
        raise ReportRebuildError("author site taxon support scope changed")
    required = {
        relative.as_posix()
        for relative in (LOOKUP, PARAMETERS, CROSSWALK, FORMAT_SCRIPT)
    }
    required.update(f"author/run.REVEALS.files/site.list.{grid}.csv" for grid in GRIDS)
    grids: Counter[str] = Counter()
    sites: set[str] = set()
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("site_id"), str)
            or not isinstance(row.get("grid_id"), str)
            or row.get("grid_id") not in GRIDS
            or row.get("all_targets_measured_admitted") is not False
            or row.get("prepared_target_row_count") != 31
            or row["site_id"] in sites
        ):
            raise ReportRebuildError("author site taxon support site scope changed")
        site = row["site_id"]
        sites.add(site)
        grids[row["grid_id"]] += 1
        required.update(
            (
                f"author/input/{site}.csv",
                f"author/run.REVEALS.files/LRAready_{site}.csv",
            )
        )
    if dict(grids) != GRIDS or len(required) != 40:
        raise ReportRebuildError("author site taxon support source population differs")
    inputs = report.get("inputs")
    if not isinstance(inputs, list) or len(inputs) != 40:
        raise ReportRebuildError("author site taxon support source coverage differs")
    declared: set[str] = set()
    for entry in inputs:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"source_root_role", "path", "bytes", "sha256"}
            or entry.get("source_root_role") != "external_landclim_author_reference"
            or type(entry.get("bytes")) is not int
        ):
            raise ReportRebuildError(
                "author site taxon support source identity differs"
            )
        relative = require_relative_path(entry["path"], "author site taxon source path")
        certified = identities.get(f"external/{SOURCE_ID}/{relative}")
        if (
            relative in declared
            or not isinstance(certified, dict)
            or entry["bytes"] != certified.get("size")
            or entry["sha256"] != certified.get("sha256")
        ):
            raise ReportRebuildError(
                "author site taxon support source identity differs"
            )
        declared.add(relative)
    if declared != required:
        raise ReportRebuildError("author site taxon support source population differs")


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> JsonObject:
    """Publish unchanged support facts after complete source identity rechecks.

    Header absence and positive prepared rows remain source-review witnesses.
    Snapshot custody grants no use rights or measured-taxon/profile admission.
    """
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    author_mass._require_author_lookup(qualified, source_descriptor)
    before = producer_input_identity(qualified.inputs, repository)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent)
    )
    try:
        report = publish(qualified.directory, stage)
        _require_bound_account(report, before)
        if any(stage.iterdir()):
            raise ReportRebuildError(
                "author site taxon producer output coverage differs"
            )
        (stage / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        after = validated_external_report_sources(
            repository, source_root, source_descriptor
        )
        if (
            after.directory != qualified.directory
            or after.inputs != qualified.inputs
            or after.descriptor_sha256 != qualified.descriptor_sha256
            or producer_input_identity(qualified.inputs, repository) != before
        ):
            raise ReportRebuildError(
                "author site taxon inputs changed during publication"
            )
        require_absent_artifact_output(repository, destination)
        os.replace(stage, destination)
    except BaseException:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return report


def main(argv: list[str] | None = None) -> int:
    """Reproduce the qualified support ledger into an absent artifacts directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", type=Path, default=DESCRIPTOR)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
