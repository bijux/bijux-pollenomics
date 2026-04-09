from __future__ import annotations

from pathlib import Path

from ..config import DEFAULT_AADR_VERSION, DEFAULT_DATA_ROOT
from ..core.files import write_text

AVAILABLE_SOURCES = ("aadr", "boundaries", "landclim", "neotoma", "raa", "sead")


def render_data_root_readme() -> str:
    """Render a stable README for the generated data root."""
    return render_data_root_readme_for(DEFAULT_DATA_ROOT, DEFAULT_AADR_VERSION)


def render_data_root_readme_for(output_root: Path, version: str) -> str:
    """Render the data-root README with the active output directory name."""
    root_name = output_root.name or str(output_root)
    tree_lines = [
        root_name,
        "├── aadr",
        f"│   └── {version}",
        *(f"├── {source}" for source in AVAILABLE_SOURCES[1:-1]),
        f"└── {AVAILABLE_SOURCES[-1]}",
    ]
    tree_text = "\n".join(tree_lines)
    return f"""# Data Layout

Tracked source data lives directly under `{root_name}/`:

```text
{tree_text}
```

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical docs pages:

- [`docs/data-sources/index.md`](../docs/data-sources/index.md)
- [`docs/reference/data-layout.md`](../docs/reference/data-layout.md)

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts, source output roots, and provenance metadata.
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
