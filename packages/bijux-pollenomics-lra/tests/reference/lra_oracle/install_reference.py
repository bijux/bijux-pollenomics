#!/usr/bin/env python3
"""Install the exact bundled DISQOVER source into an isolated R library.

R, Rscript, compilers, and system headers must already be available. Network
access is used only to install missing CRAN dependencies unless
``--skip-dependencies`` is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT / "vendor" / "disqover_0.9.14.tar.gz"
EXPECTED_SHA256 = "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"


def _description_fields() -> dict[str, str]:
    with tarfile.open(ARCHIVE) as archive:
        member = archive.extractfile("disqover/DESCRIPTION")
        if member is None:
            raise RuntimeError("Bundled archive has no disqover/DESCRIPTION")
        description = member.read().decode("utf-8")
    fields: dict[str, str] = {}
    key: str | None = None
    for line in description.splitlines():
        if line[:1].isspace() and key is not None:
            fields[key] += " " + line.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            fields[key] = value.strip()
    return fields


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--library", type=Path, default=ROOT / ".r-library")
    parser.add_argument("--skip-dependencies", action="store_true")
    args = parser.parse_args(argv)

    rscript = shutil.which("Rscript")
    r = shutil.which("R")
    if not rscript or not r:
        print(
            "BLOCKED: R and Rscript are required; no reference installation occurred.",
            file=sys.stderr,
        )
        return 2
    digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        print(
            f"Reference archive checksum mismatch: expected {EXPECTED_SHA256}, got {digest}",
            file=sys.stderr,
        )
        return 1

    library = args.library.resolve()
    library.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, R_LIBS_USER=str(library))

    if not args.skip_dependencies:
        fields = _description_fields()
        dependencies: set[str] = set()
        for field in ("Imports", "Depends", "LinkingTo"):
            for value in fields.get(field, "").split(","):
                name = re.split(r"\s|\(", value.strip())[0]
                if name and name != "R":
                    dependencies.add(name)
        literal = "c(" + ",".join(json.dumps(x) for x in sorted(dependencies)) + ")"
        code = (
            f"required<-{literal};"
            "missing<-required[!vapply(required,requireNamespace,logical(1),quietly=TRUE)];"
            "if(length(missing))install.packages(missing,repos='https://cloud.r-project.org',"
            f"lib={json.dumps(str(library))});"
            "stopifnot(all(vapply(required,requireNamespace,logical(1),quietly=TRUE)))"
        )
        subprocess.run([rscript, "--vanilla", "-e", code], env=environment, check=True)

    subprocess.run(
        [r, "CMD", "INSTALL", "--library=" + str(library), str(ARCHIVE)],
        env=environment,
        check=True,
    )
    marker = library / "disqover" / "SOURCE_SHA256"
    marker.write_text(digest + "\n", encoding="utf-8")
    print(f"Installed disqover 0.9.14 from exact source SHA-256 {digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        print(
            "Reference installation failed; no parity pass is implied.",
            file=sys.stderr,
        )
        raise SystemExit(error.returncode) from error
