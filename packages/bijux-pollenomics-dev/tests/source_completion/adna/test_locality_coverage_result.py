"""Observe a closed locality-label export without invoking its normalizer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import signal
import sys
import time

from .locality_coverage.custody import compare
from .locality_coverage.verification import require


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "protocol", "products", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    products = (
        args.products if args.products.is_absolute() else repository / args.products
    )
    output = args.output.absolute()
    require(
        ".." not in output.parts
        and not output.exists()
        and output.resolve().is_relative_to(repository / "artifacts")
        and not output.resolve().is_relative_to(products.resolve())
        and not any(p.is_symlink() for p in output.parents),
        "fresh independent artifact directory outside closed producer products",
    )
    started = time.monotonic()
    signal.signal(
        signal.SIGALRM,
        lambda *_: (_ for _ in ()).throw(
            TimeoutError("60 second locality observer deadline")
        ),
    )
    signal.alarm(60)
    facts = compare(repository, args.protocol, products)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    facts["resources"] = {
        "elapsed_seconds": time.monotonic() - started,
        "peak_rss_bytes": rss if sys.platform == "darwin" else rss * 1024,
    }
    require(
        facts["resources"]["elapsed_seconds"] <= 60
        and facts["resources"]["peak_rss_bytes"] <= 512 * 1024**2,
        "observer time or memory cap",
    )
    encoded = (json.dumps(facts, indent=2, allow_nan=False) + "\n").encode()
    require(len(encoded) <= 8 * 1024**2, "independent output byte cap")
    output.mkdir(parents=True)
    with (output / "verification.json").open("xb") as stream:
        stream.write(encoded)
    require(time.monotonic() - started <= 60, "observer closure deadline")
    print(
        json.dumps(
            {
                "status": facts["status"],
                "output_bytes": len(encoded),
                "resources": facts["resources"],
            },
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
