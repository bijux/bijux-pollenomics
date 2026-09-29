# Publication attribution for the used Nordic Neotoma datasets

The [source-bound ledger](report.json) joins the [Neotoma dataset entity
decisions](../neotoma-entities/README.md) to 85 exact provider publication-link
responses retained privately under `neotoma/publication-links/2026-09-29`.
These are the datasets used in the selected four-country direct observed-pollen
development study. The ledger binds the entity report, relational dataset part,
capture manifest and every consumed response by SHA-256. It keeps source dataset
DOI strings, investigators, all linked publications and provider primary flags.

Neotoma's [2025 Data Use and Embargo Policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
states CC BY 4.0 use with attribution to Neotoma, the constituent database, the
original investigators and primary publications, and asks for a site/dataset
table with dataset DOIs. All 85 used rows identify the European Pollen Database,
have at least one dataset DOI and name an investigator. The provider links give
79 datasets exactly one flagged primary publication with citation, author and
year metadata. This is provider metadata readiness, not a qualified citation
decision, source-specific rights review, or LRA admission.

| Country | Used datasets | One flagged primary | Primary-link review | Distinct source DOIs | Either review |
| --- | ---: | ---: | ---: | ---: | ---: |
| Sweden | 3 | 3 | 0 | 2 | 2 |
| Denmark | 2 | 2 | 0 | 0 | 0 |
| Norway | 52 | 49 | 3 | 9 | 11 |
| Finland | 28 | 25 | 3 | 2 | 5 |
| **Total** | **85** | **79** | **6** | **13** | **18** |

The six primary-link cases have exact source questions:

| Dataset | Country | Provider state | Citation decision needed |
| --- | --- | --- | --- |
| `4168`, `4472` | FI | No publication link | Identify and verify the original primary publication for each Vuorela dataset. |
| `4510` | FI | Two links, neither primary | Determine which linked work, if either, is primary for this dataset. |
| `45347` | NO | Two links flagged primary | Confirm whether both works apply and cite each applicable primary work. |
| `52255` | NO | Two links flagged primary | Confirm both primary works; the two DOI strings differ only in ASCII case. |
| `53098` | NO | Three links flagged primary | Confirm applicable primary works and resolve its two distinct dataset DOI names. |

Sixteen datasets carry more than one literal DOI string. The [DOI
Handbook](https://www.doi.org/doi-handbook/html/) §3.3.4 treats ASCII case
variants as equivalent identifiers: three of those 16 have only case variants.
The other **13 have distinct DOI names**, including two Swedish, nine Norwegian
and two Finnish datasets. Their exact strings remain in the ledger for a
source-owner citation decision; no DOI was silently selected or discarded.
The union of primary-link and distinct-DOI review cases is **18 datasets**.

The existing direct-pollen predictions and scores remain development results.
This attribution review does not change their response denominator, admit any
sample to LRA, supply basin geometry, or establish independent vegetation truth.

Replay with the retained private capture:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.neotoma_publication_readiness \
  --repository . \
  --capture-root /path/to/private/source/store/neotoma/publication-links/2026-09-29 \
  --output artifacts/jobs/neotoma-publication-readiness/replay/report.json
cmp docs/report/regions/nordic/source-capability/neotoma-attribution/report.json \
  artifacts/jobs/neotoma-publication-readiness/replay/report.json
```
