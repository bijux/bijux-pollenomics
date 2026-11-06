"""Verify a closed seven-core author-window source audit independently."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import time

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    resources,
)

from .nordic_author_window_support.native_owners import require
from .nordic_author_window_support.verification import verify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for name in ("repository", "original-data-root", "products", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    output = args.output.absolute()
    require(
        ".." not in args.output.parts
        and output.is_relative_to(repository / "artifacts")
        and output != repository / "artifacts"
        and not output.exists()
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "fresh ordinary artifact output",
    )
    started = time.monotonic()
    signal.signal(
        signal.SIGALRM,
        lambda *_: (_ for _ in ()).throw(
            TimeoutError("90 second independent author-window observer limit")
        ),
    )
    signal.alarm(90)
    facts = verify(repository, args.original_data_root, args.products, args.protocol)
    limits = {
        "producer_wall_seconds": 90,
        "observer_wall_seconds": 90,
        "max_rss_bytes": 1024**3,
        "max_output_bytes": 16 * 1024**2,
    }
    output.mkdir(parents=True)
    facts["resources"] = resources(started, output, limits, observer=True)
    raw = (json.dumps(facts, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= limits["max_output_bytes"], "bounded independent result")
    with (output / "verification.json").open("xb") as stream:
        stream.write(raw)
    resources(started, output, limits, observer=True)
    signal.alarm(0)
    print(
        json.dumps(
            {
                "status": facts["status"],
                "owners": facts["native_sample_owners_checked"],
                "windows": facts["requested_windows_checked"],
                "resources": facts["resources"],
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
