"""Capture the maintained Neotoma native hierarchy audit as one report file."""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import io
from pathlib import Path
import runpy

PRODUCER = Path("docs/report/source-relations/neotoma/native-roundtrip/replay.py")


def run(repository: Path, output: Path) -> None:
    """Invoke the existing audit with an absent, confined artifact destination."""
    repository = repository.resolve(strict=True)
    artifacts = repository / "artifacts"
    source = repository / PRODUCER
    if (
        source.is_symlink()
        or not source.is_file()
        or source.resolve() != source
        or artifacts.is_symlink()
        or not artifacts.is_dir()
    ):
        raise ValueError("native audit source or repository artifact root is invalid")
    if output.is_symlink():
        raise ValueError("native audit output may not be a symlink")
    destination = output.resolve()
    for ancestor in output.absolute().parents:
        if ancestor == repository:
            break
        if ancestor.is_symlink():
            raise ValueError("native audit output ancestor may not be a symlink")
    else:
        raise ValueError("native audit output lies outside repository")
    if not destination.is_relative_to(artifacts) or destination.exists():
        raise ValueError("absent repository artifact file required")
    namespace = runpy.run_path(str(source), run_name="_native_roundtrip_owner")
    stream = io.StringIO()
    with redirect_stdout(stream):
        namespace["main"]()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(stream.getvalue(), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    run(args.repository, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
