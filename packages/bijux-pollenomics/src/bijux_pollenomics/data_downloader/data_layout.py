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
    """Render the governed data-root evidence and ownership contract."""
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
    return f"""# Pollenomics Data Repository

`{root_name}/` is the governing evidence state for Pollenomics. Tracked source
data and governed species-owned ancient-DNA views live directly under
`{root_name}/`; publications under `docs/report/` are derived projections and
do not replace this state as authority for a scientific claim.

## Evidence Layout

```text
{tree_text}
```

Each contracted family can carry four materially different roles: raw capture,
normalized evidence, scientific review, and publication. Directory presence
does not establish that a role contains governed members. Inspect the
evidence-stage matrix and the actual artifacts before claiming a complete
lifecycle.

## Database Contract Map

| Registry | Governs | Must not be used as |
| --- | --- | --- |
| `collection_summary.json` | collected roots, versions, acquisition, hashes, and replacement | a catalogue of every evidence record |
| `source_family_contracts.json` | family role and lifecycle ownership | record-level scientific fitness |
| `source_family_evidence_stage_matrix.json` | material lifecycle presence and family-scale metrics | a universal maturity score |
| `source_spatiotemporal_posture_registry.json` | family-specific spatial and temporal meaning | permission to compare unlike records |
| `source_fact_ownership_registry.json` | authority for recurring facts and dependent copies | permission to edit a convenient descendant |
| `evidence_artifact_contracts.json` | required companions for project, paper, sample, site, atlas, and country units | proof that populated values are scientifically valid |

```mermaid
flowchart LR
    Collection["collection identity"] --> Family["family partitions"]
    Family --> Objects["governed objects and claims"]
    Objects --> Decisions["review and admission"]
    Decisions --> Products["manifested publication projections"]
```

No single registry represents the entire database, and no publication output
may feed a fact backward into its evidence owner.

## Source Families

| Root | Evidence role |
| --- | --- |
| `landclim/` | pollen-site and REVEALS model context |
| `neotoma/` | palaeoecological pollen-site context |
| `sead/` | environmental archaeology context |
| `raa/` | Sweden-specific archaeology and heritage context |
| `boundaries/` | geographic filtering and framing |
| `svar/` | Swedish lake and hydrography context |
| `aadr/` | versioned human ancient-DNA metadata capture; requested release `{version}` |
| `adna/` | species-owned human and animal ancient-DNA evidence |

These roots are not interchangeable. Their temporal resolution, spatial
precision, licensing, coverage, and scientific role remain source-specific.

## Evidence Graph And Cardinality

The data model is relational even when an artifact is serialized as a flat
table. Keys identify durable objects; explicit relations state how those
objects may be joined; review records preserve final, qualified, conflicted,
and unresolved claims.

| Object | Stable relation | Cardinality that must survive |
| --- | --- | --- |
| source release | owns captured artifacts and source-native records | one release to many records |
| paper or archive project | owns source context and supporting-material inventory | papers and projects are many-to-many |
| sample | resolves native labels through evidence locators | one project to many samples; labels are not globally unique |
| locality claim | connects a sample or site to reported and resolved place evidence | one sample can retain competing claims |
| chronology claim | connects source wording to an allowed normalized interval | one sample can retain several evidence bases |
| publication member | connects admitted evidence to one product scope | one object can enter several products under separate decisions |

Flattened exports may repeat keys for convenience. They do not authorize a
project-wide place or date to be copied into every sample, nor a published
feature to become the owner of upstream facts.

## Animal Ancient-DNA Curation

`adna/governance/source_library/` is the source-accountability layer for animal
ancient DNA. It keeps cross-project registries separate from one durable
subtree per archive project. A project subtree can carry an intake dossier,
bundle manifest, archived acquisition metadata, stable sample master,
sample-to-site links, locality and chronology evidence, and the curation note
that explains project-specific interpretation.

Paper-owned supporting material remains distinct from archive-project
metadata. A publication, project accession, supplement, sample, and site are
related evidence objects, not aliases for one identifier. Cross-project
ambiguity, missing-source, chronology, locality, coordinate, and coverage
surfaces stay under `adna/governance/` so incomplete work remains visible.

## Species Evidence Views

`Homo sapiens` ancient DNA is governed under
`adna/species/homo_sapiens/`. Its `raw/aadr -> ../../../../aadr` link preserves
the captured release without a copy. The current human view is capture-only:
normalized and review member artifacts are not materialized in this checkout.

The domesticated-animal curation program owns generated views under:

- `adna/species/equus_caballus/`
- `adna/species/sus_scrofa_domesticus/`
- `adna/species/ovis_aries/`
- `adna/species/bos_taurus/`
- `adna/species/capra_hircus/`
- `adna/species/canis_lupus_familiaris/`
- `adna/species/felis_catus/`
- `adna/species/camelus_dromedarius/`
- `adna/species/rangifer_tarandus/`
- `adna/species/equus_asinus/`

Project and paper evidence remains governed under
`adna/governance/source_library/project_registry.json` and its project
subtrees. The role split is declared by
`adna/governance/surface_role_registry.json`; the per-project file contract is
`adna/governance/source_library/project_surface_contract.json`.

Species roots are projections for inspection, comparison, readiness review,
and publication. They do not create eleven independent source databases or
transfer fact ownership away from projects and samples.

`adna/final/` contains admitted downstream publication inputs:

- `atlas/animal_atlas_point_candidates.json` for animal atlas candidates;
- `atlas/animal_atlas_candidate_accountability.json` for admission accounting;
  and
- `countries/country_publication_index.json` for country publication linkage.

These are final publication inputs, not final scientific truth. Their rows
remain subordinate to project- and sample-owned evidence.

## Audit One Data Claim

| Question | Required route |
| --- | --- |
| Which source object was captured? | collection identity → family root → release or project artifact → native record |
| Which sample or site is represented? | stable normalized identity → aliases and relations → captured locator |
| Who owns a repeated place or time value? | fact-ownership registry → locality or chronology claim → evidence locator |
| Why is a record visible? | eligible population → admission decision → product manifest → published member |
| Why is a known record absent? | expected identity → recovery, ambiguity, exclusion, or scope decision |
| What changed after a refresh? | capture diff → normalized diff → review diff → membership and count diff |

An audit closes only when the governing evidence and the decision connecting
it to the product are both recoverable. Finding the same value in several
files is not equivalent to finding its authority.

## Refresh Safety

Source collection uses staging-and-swap replacement. A successful refresh
replaces a source-specific tracked root; a failed refresh preserves the prior
root. `make data-prep` is an intentional tracked-data rewrite, not a read-only
validation command.

Accept a refresh only after recording source identity and hashes, changed
record identities, semantic field and relation changes, new or superseded
conflicts, affected admissions and exclusions, product-count changes, and the
focused validation results for every changed descendant. A newer source can
narrow a claim when it exposes weaker support or a conflict.

## Further Reading

Detailed acquisition, database, evidence, and publication contracts live in
the public handbook:

- [`docs/public/pollenomics-data/sources/index.md`]({DATA_SOURCE_INDEX})
- [`docs/public/pollenomics-data/overview/data-directory-layout.md`]({DATA_LAYOUT_INDEX})
- [`docs/public/pollenomics-data/database/index.md`](../docs/public/pollenomics-data/database/index.md)
- [`docs/public/pollenomics-data/evidence/species-evidence-views.md`](../docs/public/pollenomics-data/evidence/species-evidence-views.md)
- [`docs/public/pollenomics-data/sources/animal-source-intake.md`](../docs/public/pollenomics-data/sources/animal-source-intake.md)
- [`docs/public/pollenomics-data/curation/record-admission.md`](../docs/public/pollenomics-data/curation/record-admission.md)
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
