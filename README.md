# bijux-pollenomics

`bijux-pollenomics` is a curated evidence and publication system for pollen,
palaeoenvironmental context, archaeology, hydrography, field observations, and
ancient DNA. It preserves source identity, normalization rules, review state,
and publication lineage in one checked-in repository so a visible map point can
be traced back to the files and decisions that support it.

The database is part of the product. Source-family contracts distinguish raw,
normalized, reviewed, and published layers; fact-ownership records identify
which artifact governs a repeated claim; and the animal aDNA source library
preserves project dossiers, supporting-material inventories, sample identity,
locality evidence, chronology evidence, ambiguity ledgers, and publication
gates. Public reports are derived views over that curated state, not an
independent database.

World, Europe-plus, Nordic, and country outputs form one publication family.
Pollen and environmental context are the strongest current surfaces. Animal
aDNA remains deliberately conservative: records without adequate sample,
locality, chronology, or coordinate support stay qualified or excluded rather
than being promoted through a visually clean atlas.

<!-- bijux-pollenomics-badges:generated:start -->
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-pollenomics/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-pollenomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml/badge.svg?branch=main)](https://github.com/bijux/bijux-pollenomics/actions/workflows/verify.yml?query=branch%3Amain)
[![Release PyPI](https://img.shields.io/badge/release-pypi%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-pypi.yml)
[![Release GHCR](https://img.shields.io/badge/release-ghcr%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-ghcr.yml)
[![Release GitHub](https://img.shields.io/badge/release-github%20workflow-2563EB?logo=githubactions&logoColor=white)](https://github.com/bijux/bijux-pollenomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-pollenomics/actions/workflows/deploy-docs.yml)
[![Release](https://img.shields.io/github/v/release/bijux/bijux-pollenomics?display_name=tag&label=release)](https://github.com/bijux/bijux-pollenomics/releases)
[![GHCR packages](https://img.shields.io/badge/ghcr-2%20packages-181717?logo=github)](https://github.com/bijux?tab=packages&repo_name=bijux-pollenomics)
[![Published packages](https://img.shields.io/badge/published%20packages-2-2563EB)](https://github.com/bijux/bijux-pollenomics/tree/main/packages)

[![bijux-pollenomics](https://img.shields.io/pypi/v/bijux-pollenomics?label=bijux--pollenomics&logo=pypi)](https://pypi.org/project/bijux-pollenomics/)
[![pollenomics](https://img.shields.io/pypi/v/pollenomics?label=pollenomics&logo=pypi)](https://pypi.org/project/pollenomics/)

[![bijux-pollenomics](https://img.shields.io/badge/bijux--pollenomics-ghcr-181717?logo=github)](https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fbijux-pollenomics)
[![pollenomics](https://img.shields.io/badge/pollenomics-ghcr-181717?logo=github)](https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fpollenomics)

[![bijux-pollenomics docs](https://img.shields.io/badge/docs-bijux--pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/public/pollenomics/)
[![pollenomics docs](https://img.shields.io/badge/docs-pollenomics-2563EB?logo=materialformkdocs&logoColor=white)](https://bijux.io/bijux-pollenomics/public/pollenomics/)
<!-- bijux-pollenomics-badges:generated:end -->

## Choose A Starting Point

| You need to… | Start with… | What you will establish |
| --- | --- | --- |
| understand the product and its boundaries | [documentation home](https://bijux.io/bijux-pollenomics/) | which claims and workflows the repository supports |
| inspect source selection and curation | [data system guide](docs/public/pollenomics-data/index.md) | how captured material becomes governed evidence |
| examine a checked-in result | [report portal](docs/report/index.md) | product identity, scope, members, and review surfaces |
| interpret a visible marker | [Nordic atlas guide](docs/public/nordic-atlas/index.md) | layer role, admission posture, precision, and lineage |
| evaluate a candidate lake | [Sweden lake priorities](docs/public/nordic-atlas/sweden-lake-priorities/index.md) | ranking assumptions, stability, and fieldwork gaps |
| explain a blocked claim | [release-readiness refusal](docs/report/repository_final_release_refusal.md) | which evidence dimension prevents stronger language |
| operate repository-owned state | [maintainer handbook](docs/internal/maintain/index.md) | which commands validate or intentionally regenerate it |

Choose by question rather than by file type. A rendered map is the right
starting point for orientation; a governing evidence record is the right
ending point for a consequential claim.

```mermaid
flowchart LR
    Sources["versioned sources and papers"] --> Capture["tracked source capture"]
    Capture --> Curate["normalization and evidence curation"]
    Curate --> Review["conflicts, caveats, and release gates"]
    Review --> Publish["world, regional, and country publications"]
    Publish --> Trace["reader traceability"]
    Trace -. challenge .-> Review
```

The trust boundary is explicit:

| Layer | Governs | Does not govern |
| --- | --- | --- |
| source capture | acquired identity, retrieval context, and source bytes | repository interpretation |
| normalized evidence | stable fields, identifiers, and source linkage | publication eligibility |
| review | precision, conflicts, comparability, and refusal | source-native facts |
| publication | admitted records, geography, labels, and visible caveats | upstream evidence truth |

A map or report is therefore an index into governed evidence, not a substitute
for it.

## What A Published Record Contains

A public feature is a compound claim. Its visual geometry is only one member
of the record; identity, source lineage, temporal posture, spatial precision,
product scope, and admission outcome travel with it.

| Claim component | Governing evidence | Typical failure mode |
| --- | --- | --- |
| identity | stable source, project, sample, site, or registry identifier | conflated or duplicated records |
| origin | source version, retrieval metadata, artifact locator, and content hash | a citation without recoverable source material |
| place | reported locality, site relationship, coordinate basis, and precision | a broad place rendered as an exact point |
| time | source wording, normalized interval, dating basis, and comparability | contextual time presented as a sample date |
| role | direct evidence, context, decision support, or framing | co-located layers treated as equivalent proof |
| publication | geography, product version, gate result, and visible caveat | presentation silently strengthening upstream evidence |

```mermaid
flowchart LR
    Feature["published feature ID"] --> Membership["bundle membership"]
    Membership --> Evidence["evidence row"]
    Evidence --> Identity["stable record identity"]
    Evidence --> Place["locality and coordinate posture"]
    Evidence --> Time["chronology posture"]
    Identity --> Origin["project, paper, source artifact"]
    Place --> Origin
    Time --> Origin
```

This decomposition is why the repository contains more than map-ready tables.
The curation database records rejected precision, unresolved evidence,
conflicting claims, and source-recovery gaps so publication can remain smaller
than collection without becoming opaque.

This repository publishes `2` packages. Each release tag builds one staged
bundle, uploads the Python distribution to PyPI, publishes the release bundle
to its exact GHCR package page under the `bijux` account, and attaches the
same staged assets to the GitHub Release.

## Follow One Curated Record End To End

The world animal surface contains an accepted goat feature for Direkli Cave.
Its published row is only the end of a longer, checked-in chain:

| Layer | Governing identity or fact |
| --- | --- |
| publication | feature `animal-atlas-feature:capra-hircus-locality-prjeb90141-direklicave-taurusmountainsturkey` is accepted in the world animal evidence surface |
| locality | `capra_hircus:locality:prjeb90141:direklicave:taurusmountainsturkey` owns Direkli Cave and its exact supplied coordinates |
| sample | `capra_hircus:sample:prjeb90141:samea4453841` resolves archive sample `SAMEA4453841` and paper label `Direkli1-2` |
| chronology | the sample-owned source text `11367-11220 BCE` is normalized to `13169-13316 BP` with a sample-precise interval posture |
| provenance | Table S2, row 2 of the recovered PRJEB90141 supplementary workbook supplies label, place, coordinates, time, and accession lineage |
| accountability | the candidate record confirms sample lineage, site evidence, chronology evidence, coordinate provenance, and locality agreement |

```mermaid
flowchart LR
    Workbook["supplementary workbook<br/>Table S2 row 2"] --> Sample["SAMEA4453841<br/>Direkli1-2"]
    Sample --> Locality["Direkli Cave<br/>supplied coordinates"]
    Sample --> Chronology["11367–11220 BCE<br/>13169–13316 BP"]
    Locality --> Candidate["accountable animal candidate"]
    Chronology --> Candidate
    Candidate --> World["accepted world feature"]
```

This trace is intentionally more specific than a citation. It proves which
spreadsheet row owns the identity, spatial claim, and temporal claim; how those
claims were normalized; and which product admitted the resulting feature. The
same project also contains sample-owned chronology that conflicts with broader
project wording, so the database preserves the narrower sample claim instead
of flattening every project member to one date.

For an absent or qualified record, follow the same route from the expected
identity into exclusion, ambiguity, substitution, and recovery surfaces. A
source refresh is reviewed in the opposite direction: capture, normalized
identity, curation decision, then affected publication membership.

## Checked-In Evidence Snapshot

The current repository state is substantial but deliberately uneven:

| Governed surface | Current checked-in scale | What the number means |
| --- | ---: | --- |
| source families | 7 | AADR, boundaries, LandClim, Neotoma, RAÄ, SEAD, and SVAR are separately captured and governed |
| LandClim | 492 site sequences and 88 grid cells | primary pollen and vegetation context |
| Neotoma | 200 sites; 170 numerically comparable, 5 contextual-only, and 25 unresolved | independent pollen context with explicit temporal posture |
| SEAD | 2,195 reviewed inventory rows and 2,172 mapped Nordic features | archaeology context without numeric intervals in the current capture |
| RAÄ | 761,917 published sites | Sweden-specific heritage density context |
| SVAR | 40,565 lakes | candidate-lake identity and hydrographic framing |
| animal aDNA curation | 868 recovered samples across 40 projects | recovered identity rows, not proof of complete project recovery |
| animal publication | 234 reviewed point-evidence rows | the admitted spatial subset; 233 use supplementary coordinates and one uses qualified named-site geocoding |

Counts from unlike surfaces are not additive. A pollen sequence, archaeology
site, lake registry row, animal sample, and publication point answer different
questions and retain different admission rules.

```mermaid
flowchart LR
    Inventory["source inventories"] --> Curated["governed evidence state"]
    Curated --> Qualified{"claim-specific review"}
    Qualified -->|supported| Public["admitted publication subset"]
    Qualified -->|incomplete| Queue["recovery or ambiguity surface"]
    Qualified -->|unsupported| Refusal["explicit refusal"]
```

The difference between 868 recovered animal samples and 234 published point
rows is not unexplained loss. It is the visible effect of evidence ownership,
spatial resolution, temporal posture, source recovery, and product admission.

## Current Integrity Disclosures

Trust in the checked-in snapshot depends on making its material gaps as easy
to find as its strongest surfaces:

| Surface | What is present | Material limit in this checkout | Consequence |
| --- | --- | --- | --- |
| SVAR | capture manifest and summary for 40,565 lakes; lake identities retained in Sweden ranking rows | the contracted `data/svar/normalized/sweden_lake_registry.geojson` authority is declared but absent | published candidates remain inspectable, but the complete normalized registry cannot be independently traversed from this checkout |
| animal project recovery | 868 sample rows with final identity resolution | only four of 40 projects have a trustworthy expected sample count | recovered identity is not proof of project completeness |
| SEAD chronology | 2,195 inventory rows and 2,172 normalized site points | no numeric intervals in the current capture | spatial archaeology context cannot be promoted to same-period support |
| fieldwork | one dated Lyngsjön visit with checked-in photo and video | one event and selected media | no lake-wide, seasonal, or regional generalization |

The SVAR absence is a repository-integrity gap, not a reason to hide the
downstream lake work. Ranking rows preserve the registry identifiers,
representative points, geometry-derived attributes, scenario inputs, and
source links used by the publication. They support audit of published
candidates while stopping short of a claim that the full normalized registry
authority is present.

See the [SVAR source guide](docs/public/pollenomics-data/sources/svar.md),
[chronology semantics](docs/public/pollenomics-data/evidence/temporal-semantics.md),
and [fieldwork evidence boundary](docs/public/fieldwork/index.md) for the
claim-specific consequences.

## Collection, Curation, And Publication Denominators

Three totals recur across the repository because they describe different
populations:

| Population | Current scope | Governing question |
| --- | --- | --- |
| collected source families | 7 families in `data/collection_summary.json` | which collector-managed source trees belong to the pinned collection state? |
| contracted evidence families | 8 families, including animal ancient DNA | which scientific and framing families have declared evidence roles and lifecycle contracts? |
| publication members | product-specific subsets | which governed records satisfy this geography and claim contract? |

Animal ancient DNA is the eighth contracted family, but it is curated through
project archives, papers, supplements, sample authorities, and species views
rather than the seven-family collector summary. A product then admits only the
members supported for its particular spatial, temporal, and evidential claim.

This distinction prevents three common errors: reading collection breadth as
publication completeness, reading recovered samples as map-ready points, and
adding counts whose observation units differ.

```mermaid
flowchart LR
    Collected["7 collector-managed families"] --> Contracts["family contracts and normalized state"]
    Animal["animal source library and sample evidence"] --> Contracts
    Contracts --> Eight["8 contracted evidence families"]
    Eight --> Gate{"product-specific admission"}
    Gate --> Members["scoped publication members"]
    Gate --> Account["qualified, excluded, and unresolved records"]
```

## What This Repository Produces

Today, the checked-in repository produces these durable outcomes:

- a tracked `data/` tree with source-family ownership and normalized outputs
- machine-readable source-family, evidence-stage, artifact, and fact-ownership
  contracts
- an animal aDNA curation library with project dossiers, sample-level evidence,
  manual review queues, and explicit release guards
- a report tree under `docs/report/` with world, regional, and country publication families
- governed world, Europe-plus, and Nordic map surfaces that share one publication contract
- country bundles for Sweden, Norway, Finland, and Denmark that remain filtered descendants of the same broader evidence state
- point-traceability, subset-validation, scientific-review, and exclusion
  surfaces beside the visual publications they qualify
- a MkDocs documentation site that builds into `artifacts/root/docs/site/`
- maintainer-facing review surfaces that keep final-release claims blocked
  while animal recovery and SEAD comparability remain materially weaker than
  the rest of the product

The durable product is therefore a **database, decision record, and
publication system together**. Removing the review and refusal surfaces would
make the maps easier to browse but materially less trustworthy.

## Which Package To Install

Choose the package by ownership, not by name length:

- install `bijux-pollenomics` when you want the canonical runtime, CLI, and
  Python entrypoints that own collection, normalization, reporting, and atlas
  generation
- install `pollenomics` when you want the shorter package name and CLI command
  but still expect the same runtime behavior under the hood
- use `bijux-pollenomics-dev` only for maintainer checks, docs integrity, and
  release-support workflows inside this repository

## Package Map

The `2` publishable packages in this repository are:

| Package | Role | Links |
| --- | --- | --- |
| `bijux-pollenomics` | Runtime package for tracked data collection, report publication, and atlas generation | <a href="https://pypi.org/project/bijux-pollenomics/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-3775A9?logo=pypi&logoColor=white" height="18"></a> <a href="https://bijux.io/bijux-pollenomics/public/pollenomics/"><img alt="Docs" src="https://img.shields.io/badge/docs-2563EB?logo=materialformkdocs&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fbijux-pollenomics"><img alt="GHCR" src="https://img.shields.io/badge/ghcr-181717?logo=github&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-pollenomics/tree/main/packages/bijux-pollenomics"><img alt="Source" src="https://img.shields.io/badge/source-181717?logo=github&logoColor=white" height="18"></a> |
| `pollenomics` | Compatibility alias package that re-exports the runtime API and provides the `pollenomics` CLI command | <a href="https://pypi.org/project/pollenomics/"><img alt="PyPI" src="https://img.shields.io/badge/pypi-3775A9?logo=pypi&logoColor=white" height="18"></a> <a href="https://bijux.io/bijux-pollenomics/public/pollenomics/"><img alt="Docs" src="https://img.shields.io/badge/docs-2563EB?logo=materialformkdocs&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-pollenomics/pkgs/container/bijux-pollenomics%2Fpollenomics"><img alt="GHCR" src="https://img.shields.io/badge/ghcr-181717?logo=github&logoColor=white" height="18"></a> <a href="https://github.com/bijux/bijux-pollenomics/tree/main/packages/pollenomics"><img alt="Source" src="https://img.shields.io/badge/source-181717?logo=github&logoColor=white" height="18"></a> |

## Capability Boundaries

Capability statements describe checked-in contracts, not an intended future
state. Each supported use therefore has an explicit inference it does not
authorize:

| Surface | Supported use | Excluded inference or operation |
| --- | --- | --- |
| source-family database | capture, normalize, review, and publish governed source snapshots | exhaustive upstream coverage or silent refresh |
| human ancient DNA | versioned AADR `.anno` metadata context | `.geno`, `.ind`, or `.snp` genotype processing |
| animal ancient DNA | project, paper, supplement, sample, locality, chronology, coordinate, and admission curation | complete recovery of every tracked project or equal readiness across species |
| evidence maps | inspect scoped direct evidence, context, framing, and exclusions | infer causation, contemporaneity, or analytical equivalence from proximity |
| Sweden lake priorities | compare candidates under named evidence weights, radii, sensitivity, and preparation screens | automated sampling selection, coring feasibility, access, or permits |
| Lyngsjön fieldwork | inspect a dated and situated direct-visit record | generalize one visit into regional lake suitability |

These are product boundaries, not missing disclaimers. A workflow that needs
an excluded inference must first introduce the governing evidence and review
contract required to support it.

## Evidence Maturity

The publication architecture is broader than the maturity of every scientific
layer. That difference is intentional and visible:

| Surface | Current posture |
| --- | --- |
| pollen and palaeoenvironmental context | established collection and publication routes |
| boundaries and hydrography | geographic framing and lake-registry context, not independent scientific weight |
| human ancient DNA | versioned AADR metadata context; genotype processing is out of scope |
| animal ancient DNA | evidence-preserving recovery with conservative exact-point admission |
| lake ranking | reproducible decision support that still requires bathymetry, access, permits, and field verification |

Expansion is acceptable only when it retains source identity, domain-specific
semantics, and reviewable refusal. A larger atlas with weaker evidence would be
a regression.

## Working With Commands

The root `Makefile` is the main local interface. Some targets only validate the checkout, while others rewrite tracked files.

Validation-first targets:

- `make install` creates or updates the editable environment under `artifacts/root/check-venv/`
- `make lock-check`, `make lint`, `make test`, `make api`, `make docs`, `make package-verify`, and `make check` verify the repository without rewriting tracked data or report outputs

State-changing targets:

- `make lock` rewrites `uv.lock`
- `make data-prep` rewrites tracked source outputs under `data/`
- `make reports` rewrites tracked publication outputs under `docs/report/`
- `make app-state` runs the full rebuild path and rewrites tracked data, tracked reports, and the local docs build

If your goal is only to validate the repository, stop at the verification
targets. Do not start with `make app-state` unless you intentionally want to
rewrite tracked repository outputs.

## Quick Start

### Verify A Fresh Checkout

Prerequisites: `python3.11` and `uv` must be available locally.

```bash
python3.11 --version
uv --version
make install
artifacts/root/check-venv/bin/bijux-pollenomics --version
make lock-check
make lint
make test
make package-verify
make docs
```

This is the safest first run because it proves the editable environment, test surface, packaging surface, and docs build before any tracked data or report tree is regenerated.

### Rebuild The Checked-In Repository State

Use the explicit sequence when you want reviewable rebuild steps:

```bash
make data-prep
make reports
make docs
```

Use `make app-state` when you want that same sequence as a single convenience target.

Expect the rebuild path to take longer than lint and tests, to require network access, and to overwrite generated files that are intentionally checked in.

## Common Workflows

- `make install` syncs the editable environment from the tracked `uv.lock`
- `make check` runs the main repository verification pass: lock check, lint, tests, docs, and distribution verification
- `make data-prep` runs `collect-data all --version v66 --output-root data`
- `make reports` runs `publish-reports --aadr-root data/aadr --version v66 --output-root docs/report --context-root data`
- `make app-state` runs the full rebuild path: data, reports, and docs
- `make docs-serve` serves the docs locally at `http://127.0.0.1:8000/`
- `make clean` removes transient virtualenv, packaging, and cache artifacts

## Local Artifact Contract

- transient local outputs belong under `artifacts/`, not as ad hoc root-level
  cache or build directories
- the shared root environment lives at `artifacts/root/check-venv/`
- the MkDocs site builds to `artifacts/root/docs/site/`

For exact CLI expansions, narrower test targets, and package troubleshooting targets, use [entrypoints and examples](https://bijux.io/bijux-pollenomics/public/pollenomics/interfaces/entrypoints-and-examples/) and [common workflows](https://bijux.io/bijux-pollenomics/public/pollenomics/operations/common-workflows/).

The narrower verification and packaging targets remain available when you need them: `make test-unit`, `make test-regression`, `make test-e2e`, `make package-check`, `make package-smoke`, and `make package-source-smoke`.

## Repository Layout

Treat the top-level paths by ownership and review expectations:

- `Makefile` is the main local interface for verification, rebuilds, docs, and packaging
- `pyproject.toml` and `uv.lock` define and lock the Python environment
- `data/` contains tracked source snapshots, normalized outputs, and the collection manifest
- `docs/report/` contains the public publication tree, including world,
  regional, country, review, caveat, and maintainer-facing release-readiness
  surfaces
- `docs/` contains the canonical narrative and reference documentation that explains the checked-in outputs
- `packages/bijux-pollenomics/src/` contains the CLI, collectors, and report publishing logic
- `packages/bijux-pollenomics/tests/` contains unit, regression, and end-to-end coverage
- `artifacts/` contains transient local outputs such as `.venv/`, `dist/`, and the built docs site

Key checked-in contract files:

- `packages/bijux-pollenomics/src/bijux_pollenomics/config.py` centralizes publication defaults such as the current AADR version
- `apis/bijux-pollenomics/v1/` contains the checked-in public API contract, pinned canonical JSON, and schema digest
- `packages/bijux-pollenomics/src/bijux_pollenomics/data_downloader/contracts.py` and `packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/paths.py` centralize file and directory naming contracts

## Published Outputs

The main checked-in publication artifacts are:

- report portal: [`docs/report/index.md`](docs/report/index.md)
- world surface: [`docs/report/world/world_map.html`](docs/report/world/world_map.html)
- Europe-plus surface: [`docs/report/regions/europe-plus/europe-plus_map.html`](docs/report/regions/europe-plus/europe-plus_map.html)
- Nordic surface: [`docs/report/regions/nordic/nordic_map.html`](docs/report/regions/nordic/nordic_map.html)
- published report manifest: [`docs/report/published_reports_summary.json`](docs/report/published_reports_summary.json)
- data collection manifest: [`data/collection_summary.json`](data/collection_summary.json)
- country bundles under `docs/report/countries/`
- release-readiness caveats: [`docs/report/repository_final_release_refusal.md`](docs/report/repository_final_release_refusal.md)

Important output limits:

- the visible maps are inspectable publication artifacts, not site-selection engines
- the published map bundles local Leaflet assets, but basemap tiles still come from external providers at runtime
- RAÄ coverage is Sweden-only
- final release language remains refused while animal recovery and SEAD comparability stay below the stronger repository surfaces
- country reports are file bundles and summaries, not standalone web applications

## Documentation

The MkDocs site separates public scientific and product explanations from
operator material. Public pages explain sources, evidence, publications,
maps, and fieldwork. Internal pages cover repository operation, validation,
and release ownership.

- docs home: [`docs/index.md`](docs/index.md)
- runtime package handbook: [`docs/public/pollenomics/index.md`](docs/public/pollenomics/index.md)
- package operations guide: [`docs/public/pollenomics/operations/index.md`](docs/public/pollenomics/operations/index.md)
- package interface reference: [`docs/public/pollenomics/interfaces/index.md`](docs/public/pollenomics/interfaces/index.md)
- data reference: [`docs/public/pollenomics-data/index.md`](docs/public/pollenomics-data/index.md)
- fieldwork reference: [`docs/public/fieldwork/lyngsjon-lake-fieldwork/index.md`](docs/public/fieldwork/lyngsjon-lake-fieldwork/index.md)
- internal guide: [`docs/internal/index.md`](docs/internal/index.md)
- maintainer handbook: [`docs/internal/maintain/index.md`](docs/internal/maintain/index.md)

## Working Rules

These behaviors matter in review:

- collectors replace source-specific output directories before rewriting them, so reruns are intentionally destructive to stale generated files
- `data/` and `docs/report/` are tracked outputs that should change only when the corresponding rebuild intent is explicit
- `artifacts/` is disposable local state and should not be treated as a publication surface
- this README should describe only commands, outputs, and limits that exist in the current repository state
- if a change rewrites generated artifacts, review those diffs together with any narrative or workflow updates that explain them

## License

This repository is licensed under the Apache License 2.0. Copyright 2026 Bijan Mousavi <bijan@bijux.io>. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
