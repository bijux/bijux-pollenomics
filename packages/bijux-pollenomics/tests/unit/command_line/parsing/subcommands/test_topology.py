"""Topology contracts for command-family parser modules."""

from __future__ import annotations

import ast
from pathlib import Path

from bijux_pollenomics.command_line.parsing import subcommands


def test_subcommand_package_is_grouped_by_durable_command_family() -> None:
    package_root = Path(subcommands.__file__).parent
    assert {path.name for path in package_root.glob("*.py")} == {
        "__init__.py",
        "adna_assurance.py",
        "adna_inventory.py",
        "animal_refresh.py",
        "collection_contracts.py",
        "orientation.py",
        "reporting.py",
    }


def test_command_family_modules_are_valid_and_bounded() -> None:
    package_root = Path(subcommands.__file__).parent
    for module in package_root.glob("*.py"):
        source = module.read_text(encoding="utf-8")
        assert len(source.splitlines()) <= 220, module.name
        ast.parse(source, filename=str(module))
