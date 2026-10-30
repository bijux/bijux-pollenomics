"""Execute the frozen grouped forward-pollen comparison into one bounded CSV."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
import subprocess
from typing import Any

from bijux_pollenomics_lra.reconstruction.likelihood import (
    multisite_likelihood as engine,
)

from ....ci.report_rebuild.artifact_paths import require_absent_artifact_output
from ..namibia_source_join import DESCRIPTOR, REPLAY
from . import comparison, inputs
from .comparison import CSV_FIELDS, predict, score_predictions, summarize
from .inputs import GROUPS, RADII, SITES, load

MAX_OUTPUT_BYTES = 1024**2
PACKAGE = Path(
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/vegetation/namibia_pollen_prediction"
)
ENGINE = Path(
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/likelihood/multisite_likelihood.py"
)
CONSUMED = (
    PACKAGE,
    ENGINE,
    Path(REPLAY),
    DESCRIPTOR,
    Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/validation.py"
    ),
    Path("packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/models/errors.py"),
    Path(
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/vegetation/namibia_source_join.py"
    ),
)


def revision(repository: Path) -> str:
    """Require the consumed code to be tracked, clean and imported canonically."""
    for actual, expected in (
        (Path(__file__), repository / PACKAGE / "producer.py"),
        (Path(comparison.__file__), repository / PACKAGE / "comparison.py"),
        (Path(inputs.__file__), repository / PACKAGE / "inputs.py"),
        (Path(engine.__file__), repository / ENGINE),
    ):
        if actual.resolve() != expected.resolve():
            raise ValueError("Namibia consumed module origin differs")

    def git(*args: str) -> str:
        return subprocess.check_output(
            ["git", *args], cwd=repository, text=True
        ).strip()

    paths = [path.as_posix() for path in CONSUMED]
    for path in (
        PACKAGE / "__init__.py",
        PACKAGE / "__main__.py",
        PACKAGE / "producer.py",
        PACKAGE / "comparison.py",
        PACKAGE / "inputs.py",
        *CONSUMED[1:],
    ):
        git("ls-files", "--error-unmatch", "--", path.as_posix())
    if git("diff", "HEAD", "--name-only", "--", *paths) or git(
        "ls-files", "--others", "--exclude-standard", "--", *paths
    ):
        raise ValueError("Namibia consumed source must be committed and clean")
    return git("rev-parse", "HEAD")


def render(rows: list[dict[str, Any]]) -> bytes:
    """Publish every site/radius once; shared T4/T5 fit IDs denote one attempt."""
    if len(rows) != 150 or {
        (row["heldout_site"], row["radius_label_m"]) for row in rows
    } != {(site, radius) for site in SITES for radius in RADII}:
        raise ValueError("Namibia prediction population differs")
    if len({row["fit_id"] for row in rows}) != len(GROUPS) * len(RADII):
        raise ValueError("Namibia group/radius fit attempt population differs")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    result = stream.getvalue().encode("utf-8")
    if len(result) > MAX_OUTPUT_BYTES:
        raise ValueError("Namibia prediction CSV exceeds one MiB")
    return result


def run(
    repository: Path, source_store: Path, output: Path
) -> dict[int, dict[str, Any]]:
    """Keep raw inputs and consumed code stable through fitting and scoring."""
    repository, source_store = (
        repository.resolve(strict=True),
        source_store.resolve(strict=True),
    )
    output = require_absent_artifact_output(repository, output)
    if output.is_relative_to(source_store) or source_store.is_relative_to(output):
        raise ValueError("Namibia output overlaps source store")
    source_revision = revision(repository)
    source = load(repository, source_store)
    predictions = predict(source)
    rows = score_predictions(source, predictions)
    result = render(rows)
    if (
        load(repository, source_store) != source
        or revision(repository) != source_revision
    ):
        raise ValueError("Namibia source inputs or revision changed during calculation")
    with output.open("xb") as stream:
        stream.write(result)
    return summarize(rows)


def main(argv: list[str] | None = None) -> int:
    """Parse the existing shared source store and absent artifact CSV destination."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-store", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            run(args.repository, args.source_store, args.output),
            allow_nan=False,
            sort_keys=True,
        )
    )
    return 0
