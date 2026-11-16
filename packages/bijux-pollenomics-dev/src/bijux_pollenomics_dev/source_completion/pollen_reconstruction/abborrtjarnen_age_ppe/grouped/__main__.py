"""Export groups and contrasts from retained strict-native ABBO joint moments."""

import argparse
import json
from pathlib import Path

from .publication import publish_grouped_result


def main() -> int:
    """Require an independently supplied result digest and a new output directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-result", type=Path, required=True)
    parser.add_argument("--expected-result-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            publish_grouped_result(
                args.source_result,
                expected_result_sha256=args.expected_result_sha256,
                destination=args.output,
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
