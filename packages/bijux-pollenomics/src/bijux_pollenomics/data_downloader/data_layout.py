from __future__ import annotations

from pathlib import Path

from ..adna import resolve_species_definition
from ..adna.paths import (
    ADNA_FINAL_DIR,
    ADNA_GOVERNANCE_DIR,
    ADNA_SOURCE_LIBRARY_DIR,
    ADNA_SPECIES_DIR,
)
from ..adna.species.tracked_data import tracked_species_slugs
from ..adna.species.tracked_species import TRACKED_ADNA_SPECIES
from ..config import DEFAULT_AADR_VERSION, DEFAULT_DATA_ROOT
from ..core.files import write_text

AVAILABLE_SOURCES = ("aadr", "boundaries", "landclim", "neotoma", "raa", "sead")
DATA_SOURCE_INDEX = "../docs/02-bijux-pollenomics-data/sources/index.md"
DATA_LAYOUT_INDEX = (
    "../docs/02-bijux-pollenomics-data/overview/data-directory-layout.md"
)
HOMO_SAPIENS_ADNA_SYMLINK_TARGET = "../../../../aadr"
ADNA_LAYOUT_DIRS = ("raw", "normalized", "manifests", "reports", "review")


def render_data_root_readme() -> str:
    """Render a stable README for the generated data root."""
    return render_data_root_readme_for(DEFAULT_DATA_ROOT, DEFAULT_AADR_VERSION)


def render_data_root_readme_for(output_root: Path, version: str) -> str:
    """Render the data-root README with the active output directory name."""
    root_name = output_root.name or str(output_root)
    tracked_slugs = tracked_species_slugs()
    tree_lines = [
        root_name,
        "├── adna",
        "│   ├── species",
        *(f"│   │   ├── {slug}" for slug in tracked_slugs[:-1]),
        f"│   │   ├── {tracked_slugs[-1]}",
        "│   │   └── homo_sapiens",
        "│   │       ├── raw",
        "│   │       │   └── aadr -> ../../../../aadr",
        "│   │       ├── normalized",
        "│   │       ├── manifests",
        "│   │       ├── reports",
        "│   │       └── review",
        "│   ├── governance",
        "│   │   └── source_library",
        "│   └── final",
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
- [`docs/02-bijux-pollenomics-data/overview/data-directory-layout.md`]({DATA_LAYOUT_INDEX})

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts, source output roots, and provenance metadata.

The data root also ships contract surfaces that explain ownership instead of
forcing readers to infer it from directory names alone:

- `source_family_contracts.json`
- `source_family_evidence_stage_matrix.json`
- `source_fact_ownership_registry.json`
- `evidence_artifact_contracts.json`

`Homo sapiens` ancient DNA is governed under `adna/species/homo_sapiens/`, while the
domesticated-animal curation program owns species roots such as
`adna/species/equus_caballus/`, `adna/species/sus_scrofa_domesticus/`,
`adna/species/ovis_aries/`, `adna/species/bos_taurus/`,
`adna/species/capra_hircus/`, `adna/species/canis_lupus_familiaris/`,
`adna/species/felis_catus/`, `adna/species/camelus_dromedarius/`,
`adna/species/rangifer_tarandus/`, and `adna/species/equus_asinus/`.

Cross-species audits, caveat ledgers, sample-foundation contracts, and source
registries live under `adna/governance/`, including
`adna/governance/cross_species_bibliography.json`,
`adna/governance/source_library/project_registry.json`, and
`adna/governance/animal_sample_foundation_truth.json`.
The role split inside that tree is made explicit in
`adna/governance/surface_role_registry.json`, and the shared per-project file
contract lives in `adna/governance/source_library/project_surface_contract.json`.
Shared atlas-ready and country-ready downstream data products live under
`adna/final/`.
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
    species_root = output_root / ADNA_SPECIES_DIR.removeprefix("data/") / "homo_sapiens"
    raw_root = species_root / "raw"
    for directory in (
        raw_root,
        *(species_root / name for name in ADNA_LAYOUT_DIRS[1:]),
    ):
        directory.mkdir(parents=True, exist_ok=True)
    raw_aadr = raw_root / "aadr"
    if raw_aadr.exists() or raw_aadr.is_symlink():
        if not raw_aadr.is_symlink():
            raise ValueError(
                f"expected Homo sapiens raw AADR path to be a symlink: {raw_aadr}"
            )
        if raw_aadr.readlink().as_posix() != HOMO_SAPIENS_ADNA_SYMLINK_TARGET:
            raise ValueError(
                f"unexpected Homo sapiens raw AADR symlink target for {raw_aadr}: "
                f"{raw_aadr.readlink()}"
            )
        return
    raw_aadr.symlink_to(Path(HOMO_SAPIENS_ADNA_SYMLINK_TARGET))


def ensure_curated_species_adna_layout(output_root: Path) -> None:
    """Materialize species-owned curation roots for the non-human aDNA program."""
    output_root = Path(output_root)
    for species_name in TRACKED_ADNA_SPECIES:
        species = resolve_species_definition(species_name)
        species_root = (
            output_root / ADNA_SPECIES_DIR.removeprefix("data/") / species.slug
        )
        for directory_name in ADNA_LAYOUT_DIRS:
            (species_root / directory_name).mkdir(parents=True, exist_ok=True)
    (output_root / ADNA_GOVERNANCE_DIR.removeprefix("data/")).mkdir(
        parents=True, exist_ok=True
    )
    (output_root / ADNA_SOURCE_LIBRARY_DIR.removeprefix("data/")).mkdir(
        parents=True, exist_ok=True
    )
    (output_root / ADNA_FINAL_DIR.removeprefix("data/")).mkdir(
        parents=True, exist_ok=True
    )
