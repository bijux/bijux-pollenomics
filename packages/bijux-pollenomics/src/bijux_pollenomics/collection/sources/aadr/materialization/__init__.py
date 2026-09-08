"""Lossless AADR source materialization with stable evidence identity."""

from .source_rows import load_aadr_source_table, validate_aadr_logical_source_path

__all__ = ["load_aadr_source_table", "validate_aadr_logical_source_path"]
