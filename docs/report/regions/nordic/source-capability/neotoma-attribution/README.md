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
| `4510` | FI | Two links, neither primary | Cite the original Vasikkasuo I report lead; do not treat the linked Vasikkasuo II follow-up as this core's primary work. |
| `45347` | NO | Two links flagged primary | Confirm whether both works apply and cite each applicable primary work. |
| `52255` | NO | Two links flagged primary | Confirm both primary works; the two DOI strings differ only in ASCII case. |
| `53098` | NO | Three links flagged primary | Confirm applicable primary works and resolve its two distinct dataset DOI names. |

Sixteen datasets carry more than one literal DOI string. The [DOI
Handbook](https://www.doi.org/doi-handbook/html/) §3.3.4 treats ASCII case
variants as equivalent identifiers: three of those 16 have only case variants.
The other **13 have distinct DOI names**, including two Swedish, nine Norwegian
and two Finnish datasets. Their exact strings remain in the ledger; no DOI was
silently selected or discarded. The official registry comparison below resolves
three identity relations and leaves ten source-owner citation decisions.
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
five cases still require review.

### Vasikkasuo core identity

The provider links two unflagged works to Finnish dataset `4510`. The linked
[Geological Survey report P34.4.100](https://tupa.gtk.fi/raportti/arkisto/p34_4_100.pdf)
has a scanned title page dated **1991**, although its Neotoma publication
string says 1990. Its introduction explicitly identifies its newly studied
core as **Vasikkasuo II** and the earlier, cultivated-field core as
**Vasikkasuo I**, sampled about 120 m away. It attributes the first core's
original investigation to Vuorela's 1990 report, *Siitepölyanalyyttinen
tutkimus Puolangan kunnan kasvillisuuden kehityksestä*, also [catalogued by
the Finnish National Library](https://kansalliskirjasto.finna.fi/Record/helka.997635533506253).
The [linked 1991 Suo article](https://www.suo.fi/pdf/9685) reviews regional
peat evidence and does not by itself establish the original record publication
for the first core.

The governed Neotoma collection-unit crosswalk resolves the potential mix-up:
`4510` is `VASIKKAS`, **core 1**, collected 1990-05-01, with 59 samples from
0–290 cm and included in the selected direct-pollen study. The nearby
`PUOLANKA`, **core 2**, belongs to dataset `4363`, excluded from that study.
The 1991 report is direct evidence for core II and a first-party pointer to
the 1990 original report for core I. The 1990 report's full contents have not
been compared with the 59 deposited samples, so the original-work match for
`4510` is still a documented lead rather than a verified numerical identity.
The scanned report is retained privately at
`neotoma/publication-evidence/vasikkasuo`; its one-file manifest has SHA-256
`e9168e64d725867ba1e5e0be4365bb27ba8c667e5f8af233835d217b77d772ce`.
Neotoma's two false primary flags remain unchanged.

## Norwegian multiple-primary review

Four exact external metadata responses for the three Norwegian cases are
retained in the private source store at
`neotoma/publication-evidence/norway`; the manifest SHA-256 is
`e9d72ba7b0f7d22f8a8e1f77d1e608c3f69477adbb11018ff5227d6d7f651803`.
This review keeps provider flags and DOI strings intact.

| Dataset | Source match and citation decision | Remaining distinction |
| --- | --- | --- |
| `45347`, Råtåsjøen (`OTTRAT`) | The deposited lake core was collected in 1999 and has 68 Neotoma samples at 801–998 cm. [Velle and colleagues' 2005 lake study](https://doi.org/10.1007/s10933-004-2689-x) is the original site-specific publication identified by the provider and publisher DOI metadata. Cite it with the [dataset DOI](https://doi.org/10.21233/0zgh-6r09). | The other flagged work is a 2012 excursion guide. Its direct use of these 68 pollen samples was not verified; retain it as a linked contextual work pending a source-specific check. |
| `52255`, Lake Skogstjern (`SKOGSTJE`) | The Neotoma core is 418 cm and has 236 samples at 2–418 cm. [PANGAEA's independently published pollen record](https://doi.pangaea.de/10.1594/PANGAEA.885277) identifies the same 418 cm lake core, Usinger corer and location, and explicitly relates **both** the [2017 landscape study](https://doi.org/10.1177/0959683617715691) and [2018 Mesolithic study](https://doi.org/10.1016/j.jasrep.2017.12.045). Cite both original applications with the [Neotoma dataset DOI](https://doi.org/10.21233/wq3m-e377). | PANGAEA describes 245 pollen spectra, while the governed Neotoma surface contains 236 samples; no complete row-level equivalence is claimed. Neotoma's two literal DOI strings differ only in ASCII case and refer to one DOI name under the DOI Handbook rule above. |
| `53098`, Lake Store Finnsjøen (`FINNSTOT`) | The [2015 original lake study](https://doi.org/10.1016/j.quascirev.2015.05.004) describes the pollen sequence, and the [2019 cold-event study](https://doi.org/10.1016/j.quascirev.2018.12.009) analyzes pollen at this lake and Flåfattjønna. They are source-supported site publications. The [2017 forest-line study](https://doi.org/10.1177/0959683616660172) compares megafossils and pollen and cites the 2015 study; its specific contribution of new pollen data to the deposited `FINNSTOT` sequence remains unverified. | Neotoma exposes 70 samples at 1483–2197 cm. The 2015 paper reports 45 sampled pollen levels, so exact sample-to-paper lineage still needs reconciliation. DataCite has **two separate registrations**, [10.21233/5XR8-GV26](https://doi.org/10.21233/5XR8-GV26) created in 2022 and [10.21233/sxnn-hq25](https://doi.org/10.21233/sxnn-hq25) created in 2025, both pointing to dataset `53098` but without a declared equivalence relation. Preserve both and request a source-owner citation choice. |

The Norwegian source review supports named citations for the actual lake studies
but does not turn the three provider multiple-primary states into three unique
primary flags. The 2012 guide, 2017 Finnsjøen comparison, sample-count
differences and distinct Finnsjøen DOI registrations remain explicit.

## Distinct DOI registry review

The [source-bound DataCite comparison](doi-review.json) consumes exact registry
responses for both DOI names of all **13** used datasets in the distinct-DOI
class. The 26 responses and their byte hashes are retained privately under
`neotoma/doi-metadata/used-nordic`; the capture manifest SHA-256 is
`207b791bed9d3d004fc55f407fb7a840efd81bd9180fed17f24b187ac0e69edb`.
The comparison checks the literal DOI pair, registration metadata, landing
dataset identity and any relation to the counterpart DOI. [DataCite's
guidance](https://support.datacite.org/docs/when-should-i-use-isidenticalto)
defines `IsIdenticalTo` for two DOIs of the same research output.

| Registry finding | Used datasets | Citation treatment |
| --- | --- | --- |
| One DOI record explicitly declares `IsIdenticalTo` its counterpart | FI `20`; NO `317`, `977` | The three pairs have registry-supported identity. Preserve both literal names; a preferred citation format still needs a source-owner choice. |
| Both DOI records land on the same numbered Neotoma dataset, with no DOI-to-DOI identity or version relation | SE `53995`, `54001`; NO `53002`, `53081`, `53098`, `53119`, `53121`, `53127`, `53131`; FI `58530` | Ten pairs remain distinct registrations. A common target URL, similar title or shared version number does not establish registered equivalence. Preserve both until the owner identifies the intended citation. |

For example, the two Store Finnsjøen records were created in 2022 and 2025,
both lead to dataset `53098`, and neither declares an `IsIdenticalTo` relation
to the other. This review does not change the separate three ASCII case-only
pairs, the provider publication flags, or the direct-pollen response set.

None of these citation records supplies LRA basin geometry, PPE, or
independent vegetation truth.

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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

**Supported claim.** The retained attribution ledger distinguishes provider primary flags, literal DOI names, independently supported publication matches and explicit unresolved original-work leads for the85used datasets.

**Unsupported claim.** Provider metadata readiness and DOI landing-page similarity do not establish source-specific rights, complete numerical sample identity, LRA inputs or vegetation truth.

**Actual verification performed.** Earlier verification: Read this reader's scientific narrative and its retained machine account and checked the physical evidence identity. This qualification reran no producer, predictor, numerical oracle, browser or source-acquisition consumer. Separately, both maintained provider-publication and distinct-DOI producers returned native zero on source commit `82c8fc4ed3d847909d14162f51b77dc59ccc0a70`. Their original observer and whole job failed, and both raw tracked byte checkers returned two; these results remain literal. A separate observer-only native execution returned zero after authenticating every saved provider/DataCite projection, title, landing URL, exact import role and country denominator. The only two report differences are the named governed-policy SHA and its dependent attribution-ledger SHA; the complete remaining ordered typed values agree. The 85 datasets, six primary-link cases and 13 distinct DOI pairs retain their original interpretation, with three registry-declared identities and ten same-target pairs without declared equivalence. Historical and current policy epochs remain separate; original HTTP acquisition, citation selection, source rights, human review and LRA admission are unqualified.

**Remaining input or review.** Six provider primary-link cases and ten distinct DOI pairs still need their exact source-owner decisions; Kuivajärvi and VasikkasuoIleads are not authenticated complete original-work matches.

**Cause category.** Publication/source-identity correspondence with scoped unresolved citations.

**Consequence.** A later original-work review may support a citation without rewriting provider flags or treating separate registrations as identical.

**Precise next acceptance route.** Use the exact retained provider/registry packets to resolve each named core/publication/DOIpair, preserve original strings and obtain claim-scoped source-owner citation decisions.

**Negative or refused result.** Skogstjern245published spectra versus236Neotoma samples remains unreconciled; VasikkasuoII1991report cannot stand in for coreI's1990original source.

**Matched denominator.** 85used datasets;79single provider primaries and six primary-link cases;16multi-stringDOIcases include three ASCII-case-only and13distinct-name pairs, of which three declare identity and ten do not;18dataset union of review cases.

Qualified authored reader SHA-256: `2092fbfed719904e751c95c55fa9c1f5fd08de575e8af2fdc865ffe53b1d0c9a`.

- [Retained qualification evidence: docs/report/regions/nordic/source-capability/neotoma-attribution/report.json](report.json) (SHA-256 `983286a711b37be4db3dccac200fe24f814ff2b350a906e1a0fd99717104142d`).

- [Retained qualification evidence: docs/report/regions/nordic/source-capability/neotoma-attribution/doi-review.json](doi-review.json) (SHA-256 `61dde7cc0e8943bb8464d907c7927bd795ecb8ec377ba910a2dba9d9c3356823`).

- [Retained qualification evidence: reports/science/source-cohorts/neotoma-publication-source-custody.json](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts/neotoma-publication-source-custody.json) (SHA-256 `759cb90a7dea3a5b202ea3d979474292aba6db19482ac34a22577e2ac2182250`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

- [Canonical scientific account: reports/science/nordic-pollen-study.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/nordic-pollen-study.md) (source SHA-256 `59626da8437e802b57d1d5bd397bbed003860dd870c114f2b4be7eaed43323f4`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
