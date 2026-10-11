"""Reproduce the bounded WHH05 R header and count witness."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import producer_input_identity
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import _regular_path
from bijux_pollenomics_dev.ci.report_rebuild.source_qualification import (
    validated_external_report_sources,
)

DESCRIPTOR = Path("configs/ci/qualified-report-sources/landclim-author-snapshot.json")
DESCRIPTOR_SHA256 = "040bc11b10cd2486051400e1f87fd58a5a2b48a9ee5993fb7995e24625b67ff7"
SCRIPT = Path(
    "docs/report/source-relations/landclim/author-example-taxon-support/"
    "whh05_header_parity.R"
)
SCRIPT_SHA256 = "0624fd0611ce91f2cbeee6bdac1261c15b4bcb06085e86962113fffe1e77c39d"
AUTHOR_SOURCE = "external/landclim/author-reference/"
NEEDED = (
    "author/input/WHH05.csv",
    "author/LANDCLIM.ALLEUROPE.taxa.LUT.080219.csv",
    "author/run.REVEALS.files/LRAready_WHH05.csv",
    "reference/taxon-name-crosswalk.csv",
)
EXPECTED_ROWS = (
    ("Fagus", "8", "Fagus sylvatica", "5"),
    ("Fraxinus", "9", "Fraxinus", "1"),
    ("Juniperus", "14", "Juniperus", "2"),
    ("Calluna", "17", "Calluna vulgaris", "1364"),
    ("Poaceae", "18", "Poaceae", "138"),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> None:
    """Bind original R parser inputs and preserve its five-row output bytes."""
    repository = _regular_path(repository, directory=True)
    destination = require_absent_artifact_output(repository, output)
    if source_descriptor != DESCRIPTOR:
        raise ValueError("WHH05 author source descriptor differs")
    qualified = validated_external_report_sources(
        repository, source_root, source_descriptor
    )
    if (
        qualified.descriptor_sha256 != DESCRIPTOR_SHA256
        or len(qualified.inputs) != 195
        or any(
            qualified.inputs.get(AUTHOR_SOURCE + name) != qualified.directory / name
            for name in NEEDED
        )
    ):
        raise ValueError("WHH05 author source coverage differs")
    script = _regular_path(repository / SCRIPT)
    if _sha(script) != SCRIPT_SHA256:
        raise ValueError("WHH05 original formatter identity differs")
    inputs = {SCRIPT.as_posix(): script, **qualified.inputs}
    before = producer_input_identity(inputs, repository)
    with tempfile.TemporaryDirectory(
        prefix=".whh05-header-parity-", dir=destination.parent
    ) as staging:
        produced = Path(staging) / "whh05-header-parity.csv"
        subprocess.run(
            [
                "Rscript",
                "--vanilla",
                str(script),
                str(qualified.directory),
                str(produced),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        with _regular_path(produced).open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        if (
            len(rows) != len(EXPECTED_ROWS)
            or tuple(
                (
                    row["r_read_name"],
                    row["source_column_index"],
                    row["author_target"],
                    row["raw_column_sum"],
                )
                for row in rows
            )
            != EXPECTED_ROWS
            or any(
                row["prepared_target_sum"] != row["raw_column_sum"]
                or row["sums_equal"] != "TRUE"
                for row in rows
            )
        ):
            raise ValueError("WHH05 source header/count witness differs")
        after = validated_external_report_sources(
            repository, source_root, source_descriptor
        )
        if (
            after.directory != qualified.directory
            or after.inputs != qualified.inputs
            or after.descriptor_sha256 != qualified.descriptor_sha256
            or producer_input_identity(inputs, repository) != before
            or _sha(script) != SCRIPT_SHA256
        ):
            raise ValueError("WHH05 source inputs changed during parsing")
        require_absent_artifact_output(repository, destination)
        os.replace(produced, destination)


def main(argv: list[str] | None = None) -> int:
    """Reproduce the bounded WHH05 R header and count witness."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-descriptor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
