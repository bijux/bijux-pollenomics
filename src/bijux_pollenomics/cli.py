from __future__ import annotations

from collections.abc import Sequence

from .command_line import build_parser, run_command


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_command(args, parser=parser)


if __name__ == "__main__":
    raise SystemExit(main())
