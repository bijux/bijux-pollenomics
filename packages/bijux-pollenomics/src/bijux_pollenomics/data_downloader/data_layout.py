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

AVAILABLE_SOURCES = ("aadr", "boundaries", "landclim", "neotoma", "raa", "sead", "svar")
DATA_SOURCE_INDEX = "../docs/public/pollenomics-data/sources/index.md"
DATA_LAYOUT_INDEX = "../docs/public/pollenomics-data/overview/data-directory-layout.md"
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

- [`docs/public/pollenomics-data/sources/index.md`]({DATA_SOURCE_INDEX})
- [`docs/public/pollenomics-data/overview/data-directory-layout.md`]({DATA_LAYOUT_INDEX})

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts, source output roots, and provenance metadata.

The data root also ships contract surfaces that explain ownership instead of
forcing readers to infer it from directory names alone:

- `source_family_contracts.json`
- `source_family_evidence_stage_matrix.json`
- `source_spatiotemporal_posture_registry.json`
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


def render_homo_sapiens_readme() -> str:
    """Render the governed human ancient-DNA species-view contract."""
    return """# Homo Sapiens Ancient-DNA Evidence View

`Homo sapiens` is the species-owned route into the checked-in AADR metadata
capture. The `raw/aadr` link preserves one source release under both its
source-family identity and its human-species identity without copying or
forking the captured files.

```mermaid
flowchart LR
    Release["AADR release manifest"] --> Panels["1240K and Human Origins annotations"]
    Panels --> Raw["human species raw view"]
    Raw -. "not materialized in this checkout" .-> Normalized["governed normalized human evidence"]
    Normalized -. "not materialized in this checkout" .-> Review["human evidence review"]
    Review -. "not established by this view" .-> Product["product membership"]
```

## Current Material State

| Surface | Present state | Supported conclusion |
| --- | --- | --- |
| `raw/aadr/v66/release_manifest.json` | present through the governed symlink | release identity, requested members, retrieval metadata, and checksums are inspectable |
| `raw/aadr/v66/1240k/v66.1240K.aadr.PUB.anno` | present | captured 1240K annotation rows can be inspected at release v66 |
| `raw/aadr/v66/ho/v66.HO.aadr.PUB.anno` | present | captured Human Origins annotation rows can be inspected at release v66 |
| `normalized/` | no governed member artifact | a current normalized human species database is not established here |
| `manifests/` | no governed member artifact | no species-view build or membership identity is established here |
| `review/` | no governed member artifact | source-specific human review support is not established here |
| `reports/` | no governed member artifact | retained report products elsewhere cannot be inferred backward from this directory |

The present evidence supports source-capture inspection and metadata-level
analysis of the retained annotation members. It does not support a claim that
the human species view has a complete raw-to-normalized-to-reviewed lifecycle
in this checkout.

## Inspect The Capture

1. Open `raw/aadr/v66/release_manifest.json` and confirm the persistent dataset
   identity, requested release, member paths, hashes, and retrieval metadata.
2. Select the 1240K or Human Origins annotation member explicitly; do not
   treat the panels as interchangeable or add their row counts without a
   deduplication contract.
3. Preserve the source-native genetic identifier, panel identity, release,
   location fields, temporal fields, and publication lineage used by the
   query.
4. Follow any published descendant to its product manifest and geography
   decision rather than treating presence in an annotation file as automatic
   atlas or country membership.
5. State the missing normalized and review stages when reuse depends on a
   current end-to-end repository lifecycle.

## Evidence Boundary

This surface is metadata-only. It does not contain genotype calls, sequence
reads, imputation, kinship analysis, population-genetic inference, or a
repository-owned genotype processing workflow. Geographic labels and
coordinates in AADR metadata describe the retained source record at its
declared resolution; they do not create archaeological-site precision.

A retained country or world report may remain inspectable at its named
version even while this species lifecycle is incomplete. That publication is
a governed product artifact, not proof that missing normalized or review
authorities exist. Rebuildability, source capture, and retained publication
are separate claims and must be reported separately.

## Required Evidence For A Stronger Posture

A complete human species lifecycle would require a versioned normalized
member set, explicit field and panel reconciliation, duplicate-identity
handling, locality and chronology semantics, source-specific review evidence,
product admission records, and traceability from every published member back
to its AADR release member. Until those artifacts exist, preserve the current
capture-only boundary.
"""


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
    write_text(species_root / "README.md", render_homo_sapiens_readme())
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
