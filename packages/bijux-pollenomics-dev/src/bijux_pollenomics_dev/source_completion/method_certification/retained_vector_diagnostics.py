"""Regenerate retained native-vector diagnostics without running source models."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)
from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import _file
from bijux_pollenomics_dev.lra_validation.native_reference.diagnostics import (
    build_diagnostics,
)
from bijux_pollenomics_dev.lra_validation.native_reference.diagnostics_verification import (
    verify,
)

PROTOCOL = (
    "docs/report/method-certification/current-r-oracle/retained-vector-protocol.json"
)
PROTOCOL_SHA256 = "5562dd553ea12363478926beca399e257b9f2e97b49a408aafad3884d0db5ccb"
SOURCE = (
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
    "source_completion/method_certification/retained_vector_diagnostics.py"
)


def _snapshot(repository: Path) -> tuple[Path, bytes]:
    """Bind the selected maintained writer and exact original residual protocol."""
    source = repository / SOURCE
    protocol = repository / PROTOCOL
    if Path(__file__).resolve(strict=True) != source or source.is_symlink():
        raise ValueError("Retained diagnostics must use the selected repository writer")
    if hashlib.sha256(_file(repository, PROTOCOL)).hexdigest() != PROTOCOL_SHA256:
        raise ValueError("Original retained diagnostics protocol identity differs")
    return protocol, _file(repository, SOURCE)


def build(repository: Path, output: Path) -> dict[str, Any]:
    """Calculate and independently inspect saved vectors into two owned products."""
    repository = repository.resolve(strict=True)
    output = require_absent_artifact_output(repository, output)
    before = _snapshot(repository)
    report = build_diagnostics(repository, before[0])
    if report["status"] != "passed":
        raise ValueError("Retained diagnostics have an original-threshold failure")
    payload = json.dumps(report, indent=2, allow_nan=False) + "\n"
    # The scalar observer receives actual serialized bytes, as in its standalone CLI.
    with tempfile.TemporaryDirectory(
        dir=output.parent, prefix=".retained-vectors-"
    ) as work:
        report_path = Path(work) / "report.json"
        report_path.write_text(payload)
        review = verify(repository, report_path, before[0])
    if _snapshot(repository) != before:
        raise ValueError("Retained diagnostics source changed during comparison")
    review_payload = json.dumps(review, indent=2, allow_nan=False) + "\n"
    output.mkdir()
    for name, text in (
        ("retained-vector-diagnostics.json", payload),
        ("retained-vector-review.json", review_payload),
    ):
        with (output / name).open("x") as stream:
            stream.write(text)
    return report


def main() -> None:
    """Expose the ordinary configured owner with explicit source and destination."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.repository, args.output)


if __name__ == "__main__":
    main()
