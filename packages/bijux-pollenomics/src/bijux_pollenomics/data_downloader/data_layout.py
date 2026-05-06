from __future__ import annotations

from pathlib import Path

from ..config import DEFAULT_AADR_VERSION, DEFAULT_DATA_ROOT
from ..core.files import write_text

AVAILABLE_SOURCES = ("aadr", "boundaries", "landclim", "neotoma", "raa", "sead")
DATA_SOURCE_INDEX = "../docs/02-bijux-pollenomics-data/sources/index.md"
DATA_LAYOUT_INDEX = "../docs/02-bijux-pollenomics-data/foundation/directory-layout.md"
HOMO_SAPIENS_ADNA_SYMLINK_TARGET = "../../../aadr"


def render_data_root_readme() -> str:
    """Render a stable README for the generated data root."""
    return render_data_root_readme_for(DEFAULT_DATA_ROOT, DEFAULT_AADR_VERSION)


def render_data_root_readme_for(output_root: Path, version: str) -> str:
    """Render the data-root README with the active output directory name."""
    root_name = output_root.name or str(output_root)
    tree_lines = [
        root_name,
        "├── adna",
        "│   └── homo_sapiens",
        "│       ├── raw",
        "│       │   └── aadr -> ../../../aadr",
        "│       ├── normalized",
        "│       ├── manifests",
        "│       ├── reports",
        "│       └── review",
        "├── aadr",
        f"│   └── {version}",
        *(f"├── {source}" for source in AVAILABLE_SOURCES[1:-1]),
        f"└── {AVAILABLE_SOURCES[-1]}",
    ]
    tree_text = "\n".join(tree_lines)
    return f"""# Data Layout

Tracked source data and governed species-owned ancient-DNA views live directly
under `{root_name}/`:

```text
{tree_text}
```

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical docs pages:

- [`docs/02-bijux-pollenomics-data/sources/index.md`]({DATA_SOURCE_INDEX})
- [`docs/02-bijux-pollenomics-data/foundation/directory-layout.md`]({DATA_LAYOUT_INDEX})

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts, source output roots, and provenance metadata.

`Homo sapiens` ancient DNA is governed under `adna/homo_sapiens/`, where the
species-owned raw AADR view points back to the versioned source intake while
keeping normalized, manifest, review, and report ownership visible.
"""


def build_source_output_roots(output_root: Path, version: str) -> dict[str, str]:
    """Build the machine-readable output-root mapping for every tracked source."""
    roots = {
        "aadr": str(Path(output_root) / "aadr"),
        "aadr_version_dir": str(Path(output_root) / "aadr" / version),
    }
    roots.update(
        {
            source: str(Path(output_root) / source)
            for source in AVAILABLE_SOURCES
            if source != "aadr"
        }
    )
    return roots


def write_data_directory_readme(output_root: Path, version: str) -> None:
    """Write the stable README that documents the generated data tree."""
    write_text(
        Path(output_root) / "README.md",
        render_data_root_readme_for(Path(output_root), version),
    )


def ensure_homo_sapiens_adna_layout(output_root: Path) -> None:
    """Materialize the governed Homo sapiens aDNA layout under one data root."""
    output_root = Path(output_root)
    species_root = output_root / "adna" / "homo_sapiens"
    raw_root = species_root / "raw"
    for directory in (
        raw_root,
        species_root / "normalized",
        species_root / "manifests",
        species_root / "reports",
        species_root / "review",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    raw_aadr = raw_root / "aadr"
    if raw_aadr.exists() or raw_aadr.is_symlink():
        if not raw_aadr.is_symlink():
            raise ValueError(f"expected Homo sapiens raw AADR path to be a symlink: {raw_aadr}")
        if raw_aadr.readlink().as_posix() != HOMO_SAPIENS_ADNA_SYMLINK_TARGET:
            raise ValueError(
                f"unexpected Homo sapiens raw AADR symlink target for {raw_aadr}: "
                f"{raw_aadr.readlink()}"
            )
        return
    raw_aadr.symlink_to(Path(HOMO_SAPIENS_ADNA_SYMLINK_TARGET))
