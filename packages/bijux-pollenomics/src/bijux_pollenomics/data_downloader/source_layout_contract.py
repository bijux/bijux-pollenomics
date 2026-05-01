from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .data_layout import AVAILABLE_SOURCES

__all__ = [
    "SourceLayoutContract",
    "build_source_layout_contract",
    "validate_source_layout_contract",
]


@dataclass(frozen=True)
class SourceLayoutContract:
    output_root: Path
    source_directories: tuple[str, ...]
    collection_manifest_name: str

    @property
    def collection_manifest_path(self) -> Path:
        return self.output_root / self.collection_manifest_name


def build_source_layout_contract(output_root: Path) -> SourceLayoutContract:
    """Build the deterministic data-root layout contract."""
    return SourceLayoutContract(
        output_root=Path(output_root),
        source_directories=AVAILABLE_SOURCES,
        collection_manifest_name="collection_summary.json",
    )


def validate_source_layout_contract(contract: SourceLayoutContract) -> None:
    """Validate deterministic source-root layout under one data root."""
    if not contract.output_root.exists() or not contract.output_root.is_dir():
        raise ValueError(f"data root missing: {contract.output_root}")

    for source_dir in contract.source_directories:
        path = contract.output_root / source_dir
        if not path.exists() or not path.is_dir():
            raise ValueError(f"source layout contract violation: missing {path}")
