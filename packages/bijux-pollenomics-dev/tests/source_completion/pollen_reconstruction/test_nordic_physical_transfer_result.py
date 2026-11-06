"""Read back one closed conditional Nordic physical transfer population."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import time

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    resources,
)

from .nordic_physical_transfer.algebra import require
from .nordic_physical_transfer.verification import verify


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for option in ("repository", "protocol", "products", "output"):
        parser.add_argument("--" + option, type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.absolute()
    require(
        repository.resolve(strict=True) == repository, "ordinary explicit repository"
    )
    output = args.output.absolute()
    require(
        ".." not in output.parts
        and output.is_relative_to(repository / "artifacts")
        and output != repository / "artifacts"
        and not output.exists()
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "fresh unaliased artifact output",
    )
    started = time.monotonic()

    def timeout(*_: object) -> None:
        raise TimeoutError("Independent physical transfer observer exceeded180seconds")

    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(180)
    result = verify(repository, args.protocol, args.products)
    output.mkdir(parents=True)
    limits = {
        "producer_wall_seconds": 180,
        "observer_wall_seconds": 180,
        "max_rss_bytes": 768 * 1024**2,
        "max_output_bytes": 16 * 1024**2,
    }
    result["resources"] = resources(started, output, limits, observer=True)
    raw = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= limits["max_output_bytes"], "bounded independent facts")
    with (output / "verification.json").open("xb") as stream:
        stream.write(raw)
    resources(started, output, limits, observer=True)
    signal.alarm(0)
    print(
        json.dumps(
            {
                "status": result["status"],
                "contexts": result["contexts_checked"],
                "slots": result["method_slots_checked"],
                "resources": result["resources"],
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
