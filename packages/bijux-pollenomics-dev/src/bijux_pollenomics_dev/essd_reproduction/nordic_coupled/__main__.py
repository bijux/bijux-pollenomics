"""Materialize or read-admit conditional source experiments without fitting."""

import argparse
import json
from pathlib import Path

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.inputs import (
    PROTOCOL,
    admit,
    materialize,
)
from bijux_pollenomics_dev.essd_reproduction.physical_forward.inputs import buffer


def main() -> None:
    """Prepare and validate source-bound coupled experiment inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("materialize", "admit"))
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    protocol_path = args.repository / PROTOCOL
    buffer(protocol_path, args.protocol_sha256, protocol_path.stat().st_size)
    result = (
        materialize(args.repository, args.output, protocol_sha256=args.protocol_sha256)
        if args.operation == "materialize"
        else admit(args.output)
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
