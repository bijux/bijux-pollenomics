"""Publish the four retained Nordic account products atomically."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile

from .attribution import attribution
from .sources import load_inputs
from .summary import products

OUTPUTS = frozenset(
    {"account.json", "source-domain.json", "comparisons.json", "attribution.json"}
)


def _output_path(repository: Path, output: Path) -> Path:
    if ".." in output.parts:
        raise ValueError("Nordic output parent traversal refused")
    output = output.absolute()
    if output == repository / "artifacts" or not output.is_relative_to(
        repository / "artifacts"
    ):
        raise ValueError("Nordic output must be strictly below repository artifacts")
    if output.exists() or output.is_symlink():
        raise ValueError("existing Nordic output refused")
    for ancestor in output.parents:
        if ancestor.exists() or ancestor.is_symlink():
            if not stat.S_ISDIR(ancestor.lstat().st_mode):
                raise ValueError("Nordic output ancestor is not a real directory")
    return output


def publish(repository: Path, output: Path) -> dict:
    repository = repository.resolve(strict=True)
    output = _output_path(repository, output)
    inputs = load_inputs(repository)
    values = products(inputs)
    values["attribution.json"] = attribution(inputs)
    if set(values) != OUTPUTS:
        raise ValueError("Nordic ordinary output inventory differs")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="nordic-account-", dir=output.parent))
    promoted = False
    try:
        for name, value in sorted(values.items()):
            (staging / name).write_text(
                json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
            )
        load_inputs(repository)
        _output_path(repository, output)
        os.rename(staging, output)
        promoted = True
        load_inputs(repository)
    except BaseException:
        if promoted:
            shutil.rmtree(output)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    publish(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
