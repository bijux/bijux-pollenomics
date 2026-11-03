"""Observe closed Nordic source accounting without importing its producer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import time

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    resources,
)

from .nordic_literal_window_support.native_owners import require
from .nordic_literal_window_support.verification import verify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "products", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    output = args.output.absolute()
    require(
        ".." not in args.output.parts
        and output.resolve().is_relative_to(repository / "artifacts")
        and not output.exists()
        and not any(p.is_symlink() for p in output.parents),
        "fresh ordinary artifact directory",
    )
    started = time.monotonic()
    signal.signal(
        signal.SIGALRM,
        lambda *_: (_ for _ in ()).throw(
            TimeoutError("90 second independent source observer limit")
        ),
    )
    signal.alarm(90)
    facts = verify(repository, args.products, args.protocol)
    limits = {
        "producer_wall_seconds": 90,
        "observer_wall_seconds": 90,
        "max_rss_bytes": 1024**3,
        "max_output_bytes": 8 * 1024**2,
    }
    output.mkdir(parents=True)
    facts["resources"] = resources(started, output, limits, observer=True)
    encoded = (json.dumps(facts, indent=2, allow_nan=False) + "\n").encode()
    require(len(encoded) <= limits["max_output_bytes"], "bounded independent result")
    with (output / "verification.json").open("xb") as stream:
        stream.write(encoded)
    resources(started, output, limits, observer=True)
    print(
        json.dumps(
            {
                "status": facts["status"],
                "owners": facts["native_sample_owners_checked"],
                "resources": facts["resources"],
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
