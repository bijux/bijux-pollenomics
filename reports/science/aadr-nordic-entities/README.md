# Which AADR Nordic IDs reach the country products?

We joined every AADR v66 Genetic ID whose source Political Entity is exactly
Denmark, Finland, Norway or Sweden to the four retained country sample CSVs.
The [decision ledger](decisions.csv) records all 1,325 IDs, the source panel
row numbers, coordinate and chronology review states, and whether the ID
appears in its country product. The [result](report.json) binds the two
annotation panels, release manifest, source-accountability receipt and four
published sample CSVs by byte count and SHA-256.

| Source Political Entity | Source Genetic IDs | In country product | Excluded: no source coordinates |
| --- | ---: | ---: | ---: |
| Denmark | 654 | 653 | 1 |
| Finland | 124 | 32 | 92 |
| Norway | 131 | 130 | 1 |
| Sweden | 416 | 416 | 0 |
| **Total** | **1,325** | **1,231** | **94** |

Every nonpublished ID has a missing coordinate pair in the reconciled source
evidence; every published ID has a parseable pair. This explains the exact
94-ID source-to-product difference. It does not make an absent coordinate a
zero, and it does not establish that the 1,231 country rows have passed
scientific chronology, geography or source-rights review. The retained
[source-accountability receipt](../../../data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json)
still marks country assignment, map admission and scientific admission false.
Its chronology review remains method-specific even for IDs with numeric BP
values. These human metadata rows are not pollen observations, vegetation
measurements or genotype analysis.

The [producer](replay.py) uses the existing source-panel reconciliation and
country publication outputs. It refuses a changed source digest, duplicate
country ID, mismatched country label, published ID without usable coordinates,
or a source ID omitted despite usable coordinates. Reproduce into a new
directory from the repository root, then compare both files byte for byte:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/aadr-nordic-entities/replay.py \
  --repository . --output artifacts/jobs/aadr-nordic-entity-replay
```


## Actual country-record lifecycle verification

The source-bound [lifecycle account](../adna-source-lifecycle/report.json) adds a fresh execution of the four actual AADR country loaders and CSV writers. All 1,231 exported rows match the retained country products byte for byte across all 27 fields, including original date text, BP bounds, source family, namespace and accession lineage. The raw-source reconciliation again preserves 1,325 IDs = 1,231 published + 94 missing-coordinate exclusions.

The same execution checked four animal country bundles and the maintained DNA/pollen boundary controls. Its [capture](../adna-source-lifecycle/capture.json) records six native-zero stages, 26 controlled guards and the exact producer/observer identities. This is an independent comparison implementation on shared retained source lineage, not an independent human scientific review. Source chronology, country authority, rights and map admission remain unresolved. No genotype or propagation inference was performed.

The maintained replay uses a new artifact view for the declared input bytes, including retained gzip aliases; it never expands them into the canonical data tree. From the repository root, choose unused output directories:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python reports/science/adna-source-lifecycle/source_view.py --repository . --output artifacts/adna-lifecycle-source-view
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python reports/science/aadr-nordic-entities/replay.py --repository artifacts/adna-lifecycle-source-view --output artifacts/adna-lifecycle/human-entities
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python reports/science/animal-entity-capability/replay.py --repository artifacts/adna-lifecycle-source-view --output artifacts/adna-lifecycle/animal-entities
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python reports/science/adna-source-lifecycle/produce.py artifacts/adna-lifecycle-source-view artifacts/adna-lifecycle/country-contracts
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python reports/science/adna-source-lifecycle/verify.py artifacts/adna-lifecycle-source-view artifacts/adna-lifecycle/country-contracts artifacts/adna-lifecycle/independent-account.json
```

The original capture binds the executed source candidate and runtime. A later replay records correspondence on the invoking environment; it does not inherit the original native receipt, source version or scientific admission. Any changed source input, chronology/provenance export or country denominator refuses this retained comparison.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Exact AADR v66 Nordic source-ID membership/coordinate refusals and actual four-country source-to-CSV lifecycle preservation across all27export fields; DNA remains outside pollen semantics.

**Unsupported claim.** Scientific chronology validation, source-country authority, map/rights/biological admission, genotype or propagation inference.

**Actual verification performed.** Actual six-stage source/country lifecycle replay native0:1325source IDs reconciled, all1231four-country CSV rows byte equal across27fields, all4animal bundles equal,10animal source-domain flags checked and26controlled boundaries passed. A separate stdlib observer compares retained source lineage; no independent human review. The earlier six-stage native-zero wording is retained historical prose. These current checks do not recover or validate its missing original receipts. The currently authenticated earlier saved-evidence job had inventory exit zero, observer exit one and aggregate exit one; a later saved observer and the separate current human export passed in their own recorded epochs. A separate maintained source replay from commit 601112dd1f4b9e09d2cfdec7fa57d9f4ae3303a7 produced the current default 29-field human CSVs, GeoJSON and complete typed records for all four countries. An independent original-ANNO reconstruction checked every value and retained 1231 unique published IDs; the saved source account still has 1325 IDs and 94 coordinate exclusions. The original row-support audit found 1211 duplicate IDs, 0 disjoint support pairs and 0 merged-hull gaps. Those are literal observed counts, not chronology calibration; all 1325 source chronology decisions still require review. A separate saved human/animal observer preserves false pollen eligibility and measurement-leakage flags, all four blocked native taxon witnesses and the original failed aggregate. The joint metadata check supports software-domain separation for these observed populations, but whole ADNA-001 remains open because no fresh current animal source-to-country producer is established. The public source packet and bounded metadata authority preserve exact inputs, source epochs and receipts. Historical v1 products and the original lifecycle account are unchanged. Genotype, biology, rights, ecology, PROP-004, pollen and LRA admission remain unestablished.

**Remaining input or review.** The 94 absent-coordinate IDs are correctly excluded from country products, but the 1,231 country rows lack scientific chronology, geography, map, country-authority and rights admission. Resolver: AADR source custodian and chronology/geography reviewer Reopen when: Versioned source coordinates and qualified country, chronology, map and rights decisions are bound per ID.

**Cause category.** data|qualified review

**Consequence.** Keep human aDNA rows as context, not pollen, vegetation or admitted spatial events.

**Precise next acceptance route.** Obtain per-ID chronology, political-country authority, map-admission and rights decisions; rerun the AADR decision ledger and only then revise reports/science/source-cohorts.md.

**Negative or refused result.** 94 IDs excluded for missing source coordinates; 1,231 published country rows are not thereby map or scientifically admitted.

**Matched denominator.** 1,325 source IDs = 1,231 country-product rows + 94 coordinate exclusions across DK/FI/NO/SE.

Retained evidence: [reports/science/aadr-nordic-entities/report.json](report.json), [data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json](../../../data/adna/species/homo_sapiens/review/aadr_v66_source_accountability.json), [reports/science/adna-source-lifecycle/report.json](../adna-source-lifecycle/report.json), [reports/science/adna-source-lifecycle/capture.json](../adna-source-lifecycle/capture.json), [reports/science/source-cohorts/adna-current-contract-adjudication.json](../source-cohorts/adna-current-contract-adjudication.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: dcf0d390909ff5b0d19a5274e50ff9c481b0d3b180e851a042b438659298ccf5 -->
<!-- scientific-authored-source-sha256: 9e9811e4f4baaabb19f67a0d59496ea09cf695e28fe1e60496fd77a0520f7cee -->
<!-- scientific-verification-and-limits:end -->
