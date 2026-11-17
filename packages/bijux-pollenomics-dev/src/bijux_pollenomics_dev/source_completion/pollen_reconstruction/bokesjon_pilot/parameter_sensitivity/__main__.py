"""Execute the bounded conditional nominal PPE comparison from retained inputs."""

import argparse
from pathlib import Path

from .workflow import run


def main() -> None:
    """Require explicit input repository, artifact destination and imported revision."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    arguments = parser.parse_args()
    result = run(
        arguments.repository,
        arguments.output,
        source_revision=arguments.source_revision,
    )
    print(result["status"])


if __name__ == "__main__":
    main()
