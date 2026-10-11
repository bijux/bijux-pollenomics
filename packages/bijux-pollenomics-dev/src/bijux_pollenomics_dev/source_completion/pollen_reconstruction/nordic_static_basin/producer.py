"""Publish the four retained Nordic account products atomically."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from typing import Any

from .attribution import attribution
from .joint_uncertainty import DESCRIPTOR, compact_products, load_joint_inputs
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
        if (ancestor.exists() or ancestor.is_symlink()) and not stat.S_ISDIR(
            ancestor.lstat().st_mode
        ):
            raise ValueError("Nordic output ancestor is not a real directory")
    return output


def publish(
    repository: Path,
    output: Path,
    *,
    source_root: Path | None = None,
    joint_only: bool = False,
) -> dict[str, Any]:
    """Publish authenticated source products atomically into an absent output directory."""
    repository = repository.resolve(strict=True)
    output = _output_path(repository, output)
    if joint_only and source_root is None:
        raise ValueError(
            "Nordic joint-only publication requires its external source root"
        )
    values = {}
    if not joint_only:
        inputs = load_inputs(repository)
        values = products(inputs)
        values["attribution.json"] = attribution(inputs)
    if source_root is not None:
        values.update(compact_products(load_joint_inputs(repository, source_root)))
    expected = set() if joint_only else set(OUTPUTS)
    if source_root is not None:
        expected.update({"joint-uncertainty.json", "joint-capture-authority.json"})
    if set(values) != expected:
        raise ValueError("Nordic ordinary output inventory differs")

    def revalidate() -> None:
        if not joint_only:
            load_inputs(repository)
        if source_root is not None:
            load_joint_inputs(repository, source_root)

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="nordic-account-", dir=output.parent))
    promoted = False
    try:
        for name, value in sorted(values.items()):
            (staging / name).write_text(
                json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
            )
        revalidate()
        _output_path(repository, output)
        os.rename(staging, output)
        promoted = True
        revalidate()
    except BaseException:
        if promoted:
            shutil.rmtree(output)
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return values


def main(argv: list[str] | None = None) -> int:
    """Parse the source-bound publication command and its output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--source-descriptor", type=Path)
    parser.add_argument("--joint-only", action="store_true")
    args = parser.parse_args(argv)
    if args.source_descriptor is not None:
        if args.source_descriptor != DESCRIPTOR:
            raise ValueError("unexpected Nordic joint source descriptor")
        if args.source_root is None:
            raise ValueError(
                "Nordic joint source descriptor requires its external source root"
            )
    publish(
        args.repository,
        args.output,
        source_root=args.source_root,
        joint_only=args.joint_only,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
