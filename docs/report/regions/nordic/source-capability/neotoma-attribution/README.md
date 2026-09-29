# Publication attribution for the used Nordic Neotoma datasets

The [source-bound ledger](report.json) joins the [Neotoma dataset entity
decisions](../neotoma-entities/README.md) to 85 exact provider publication-link
responses retained privately under `neotoma/publication-links/2026-09-29`.
These are the datasets used in the selected four-country direct observed-pollen
development study. The ledger binds the entity report, relational dataset part,
capture manifest and every consumed response by SHA-256. It keeps source dataset
DOI strings, investigators, all linked publications and provider primary flags.
It also preserves the source dataset notes, including an explicit unpublished
statement for Kuivajärvi. Provider publication flags remain separate from the
independent source review below.

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
| `4168` | FI | No publication link | Match the original report or article to the deposited profile before assigning a primary publication. |
| `4472` | FI | No publication link | Cite the independently matched 1995 original study; retain the missing provider link. |
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

## Finnish original-work review

The two Finnish no-link datasets have been checked against the Neotoma source
rows and a bounded set of external records. Exact copies of the 1994 EPD
review, the 1995 original article and four dataset metadata responses are retained in the
private source store at `neotoma/publication-evidence/finland`. Its six-file
manifest has SHA-256
`dd52deaced69bacd6bd41394cf9e01048c6aad8c4897376808fcc8901ca90c78`.
The source dataset and collection-unit identities below are from the governed
Neotoma relational surface, not an inference from a search result.

| Dataset | Source and original-work finding | Citation status |
| --- | --- | --- |
| `4168`, Kuivajärvi (`KUIVAJAR`) | Neotoma's dataset note explicitly says the data are unpublished. [Hicks and Grönlund's 1994 EPD inventory](https://www.geologinenseura.fi/sites/geologinenseura.fi/files/sgs_bt_066_2_pages_129_136.pdf), Table 2, also lists this profile as unpublished as of March 1994. The [Finnish National Library catalogues a 1992 Geological Survey report on Kuivajärvi](https://kansalliskirjasto.finna.fi/Record/helka.9915052353506253), and a [Forssa municipal source identifies a Vuorela and Kankainen article in a 1993 local yearbook](https://www.forssa.fi/client/forssa/userfiles/kaav-kaupunkipuisto-sel159463123.pdf). Their full contents have not been matched to Neotoma's 112 samples at 2.5–400 cm. | Original-work leads; no verified primary-publication assignment. Cite the [Neotoma dataset DOI](https://doi.org/10.21233/3ppz-sz86) and Vuorela for the used dataset. The [2010 PANGAEA profile](https://doi.pangaea.de/10.1594/PANGAEA.738812) is a separate archival dataset citation, not proof that the original analysis was published. |
| `4472`, Syrjälänsuo (`SYRJALAN`) | The same [1994 EPD inventory](https://www.geologinenseura.fi/sites/geologinenseura.fi/files/sgs_bt_066_2_pages_129_136.pdf) lists the profile as unpublished at that time. [Vuorela's 1995 original article](https://journal.fi/fennoscandiaarchaeologica/article/download/126344/76174/265505), *Pollen evidence of Stone Age and Early Metal Age settlement in Taipalsaari, Southern Karelia, Eastern Finland*, Fennoscandia archaeologica XII:207–214, presents the Syrjälä mire pollen diagrams. It describes June 1992 sampling in an esker kettle-hole bog and a 0–285 cm profile. Neotoma's bog core is dated 1992-06-15 and has 81 samples spanning 0–285 cm. The [2010 PANGAEA profile](https://doi.pangaea.de/10.1594/PANGAEA.738898) agrees on handle, site coordinates and collection date. | The 1995 article is supported as the original study citation alongside the [Neotoma dataset DOI](https://doi.org/10.21233/26e5-b250) and Vuorela. The article calls the location Syrjälä mire while Neotoma calls it Syrjälänsuo; approximate coordinates and elevations differ slightly, and printed diagrams were not matched row by row. Neotoma still has no linked primary publication for this dataset. |

The 1994 unpublished designations are historical observations, not claims that
the datasets lack later archival publication. The independent 1995 article
match resolves one original-study citation for reporting while leaving the
provider's six missing or ambiguous primary-link cases unchanged. The other
five cases still require review. None of these records supplies LRA basin
geometry, PPE, or independent vegetation truth.

The existing direct-pollen predictions and scores remain development results;
this attribution review does not change their response denominator.

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
