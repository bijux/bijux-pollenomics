"""Build the source-authenticated Neotoma prerequisite review projection."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from bijux_pollenomics.analysis.lra.materialization.reading import (
    read_neotoma_evidence,
)

from .projection import build_neotoma_prerequisite_projection


def _publish_new(output: Path, content: bytes) -> None:
    """Durably publish exact bytes without replacing an existing output."""
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise ValueError("Refusing to replace a prerequisite projection")
    stage: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".stage",
            delete=False,
        ) as stream:
            stage = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(stage, output)
        directory = os.open(output.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if stage is not None:
            stage.unlink(missing_ok=True)


def main() -> int:
    """Write one new canonical projection and refuse output replacement."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--normalized-root", type=Path, required=True)
    parser.add_argument("--lakeparameter-capture-root", type=Path, required=True)
    parser.add_argument("--lakeparameter-capture-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_neotoma_prerequisite_projection(
        read_neotoma_evidence(args.raw_root, args.normalized_root),
        lakeparameter_capture_root=args.lakeparameter_capture_root,
        expected_lakeparameter_capture_sha256=args.lakeparameter_capture_sha256,
    )
    _publish_new(args.output, result.canonical_json)
    print(result.result_digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
