"""Command-line facade exports for parser and runtime dispatch."""

from .parsing import build_parser
from .runtime import run_command

__all__ = ["build_parser", "run_command"]
