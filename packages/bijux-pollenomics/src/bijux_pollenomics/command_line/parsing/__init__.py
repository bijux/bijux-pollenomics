"""Parser-building exports for the bijux-pollenomics CLI."""

from .options import (
    add_aadr_root_argument,
    add_atlas_identity_arguments,
    add_context_root_argument,
    add_output_root_argument,
    add_version_argument,
)
from .parser import build_parser
from .subcommands import register_subcommands

__all__ = [
    "add_aadr_root_argument",
    "add_atlas_identity_arguments",
    "add_context_root_argument",
    "add_output_root_argument",
    "add_version_argument",
    "build_parser",
    "register_subcommands",
]
