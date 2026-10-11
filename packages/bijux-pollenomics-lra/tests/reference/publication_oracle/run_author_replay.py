"""Execute pinned acquired author source without its installer footer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from bijux_pollenomics_lra.models.publication import PUBLICATION_SOURCE_SHA256


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = args.source / "run.REVEALS.files/LRA-REVEALS-release.R"
    if hashlib.sha256(source.read_bytes()).hexdigest() != PUBLICATION_SOURCE_SHA256:
        raise ValueError("Author numerical source hash mismatch")
    input_paths = [
        source,
        *sorted((args.source / "run.REVEALS.files").glob("*.csv")),
        args.source / "bins.csv",
        args.source / "TWlookup.csv",
    ]
    input_hashes = {
        str(path.relative_to(args.source)): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in input_paths
    }
    executable = shutil.which("Rscript")
    if executable is None:
        raise RuntimeError(
            "Exact publication replay requires Rscript; this is not a passing skip"
        )
    script = Path(__file__).with_suffix(".R")
    command = [
        executable,
        "--vanilla",
        str(script),
        str(args.source.resolve()),
        str(args.library.resolve()),
        str(args.output.resolve()),
    ]
    start = time.time()
    try:
        with (args.output / "reference.log").open("w", encoding="utf-8") as log:
            completed = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=dict(
                    os.environ,
                    OPENBLAS_NUM_THREADS="1",
                    OMP_NUM_THREADS="1",
                    MKL_NUM_THREADS="1",
                ),
                timeout=1800,
                check=False,
            )
        code = completed.returncode
    except subprocess.TimeoutExpired:
        code = 124
    after_hashes = {
        str(path.relative_to(args.source)): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in input_paths
    }
    unchanged = input_hashes == after_hashes
    if not unchanged and code == 0:
        code = 1
    receipt = {
        "command": command,
        "exit_code": code,
        "elapsed_seconds": time.time() - start,
        "source_sha256": PUBLICATION_SOURCE_SHA256,
        "input_files": input_hashes,
        "input_files_unchanged": unchanged,
        "output_files": {
            str(path.relative_to(args.output)): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(args.output.rglob("*.csv"))
        },
        "wrapper_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "source_function_bodies_unchanged": True,
        "reference_acceleration": "memoized_exact_KPf_input_tuples",
        "seed": 20220912,
        "bootstrap_draws_saved": True,
    }
    (args.output / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
