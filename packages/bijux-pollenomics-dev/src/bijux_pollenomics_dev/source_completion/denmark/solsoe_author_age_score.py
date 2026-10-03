"""Route the frozen Solsø author-target age support through qualified scoring."""

from __future__ import annotations

import argparse
from pathlib import Path

from bijux_pollenomics_dev.source_completion.pollen_age_support.qualified_author_score import (
    run as score_frozen_author_age,
)

REPLAY = Path(
    "docs/report/countries/denmark/solsoe-source-lineage/"
    "author-target-age-interval/replay.py"
)
REPLAY_SHA256 = "743258f61042bb1a3e9f496f13497fc4fc216fd617ebb4fff20abd6631b7a820"
FROZEN = REPLAY.parent


def run(
    repository: Path, source_root: Path, source_descriptor: Path, output: Path
) -> None:
    score_frozen_author_age(
        repository,
        source_root,
        source_descriptor,
        output,
        replay=REPLAY,
        replay_sha256=REPLAY_SHA256,
        frozen=FROZEN,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--source-descriptor", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    run(args.repository, args.source_root, args.source_descriptor, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
