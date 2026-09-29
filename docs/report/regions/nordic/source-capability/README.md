# Nordic source capability and country dimensions

The [retained source/country replay](report.json) joins the governed
11-family source-stage matrix to the 198-cell country coverage ledger. It
requires every family to have one row for each of six country partitions and
three distinct dimensions: source-reported, governed assignment, and
publication. The resulting 66 family/partition entries retain the original
availability, lifecycle, reason codes, source snapshot and all nullable counts
separately for each dimension. The four Nordic countries and the `UNASSIGNED`
and `OUTSIDE` partitions are all present.

The parent ledger's 20 input artifacts were rechecked against their byte counts
and SHA-256 digests. The source-stage matrix has 11 rows and a 187-row
capability/materialization audit; the country ledger has 198 cells. This
consumer does not reinterpret a `null` count as zero, sum incompatible
families, or promote capture to scientific admission.

The [combined source reconciliation](../../../source-relations/source-reconciliation/README.md)
also checks the three historical Rootsi and OpenLand intake receipts and their
12 four-country claims. Those claims remain separate from this 11-family cube;
their original archives do not create new admitted country observations.

The [Neotoma dataset ledger](neotoma-entities/README.md) adds source-bound
entity decisions for one family: 85 datasets occur in the selected direct
observed-pollen study and 124 do not. Its separate sample prerequisites do not
admit any dataset to LRA or measured-vegetation validation. Entity decisions
for the other source families still require their own source evidence.

The [used-dataset publication ledger](neotoma-attribution/README.md) joins
those 85 Neotoma study datasets to exact provider citation responses. Seventy-nine
have one provider-flagged primary publication; six need primary-link review.
Thirteen carry distinct source DOI names, with 18 datasets in the union of
citation-review cases. Neotoma's policy-level CC BY 4.0 statement and these
metadata do not resolve sample-specific scientific admission or vegetation truth.

The existing [SEAD site ledger](../../../source-relations/sead-country-retrieval/README.md)
already records all 2,195 discovered site IDs and UUIDs. Governed boundaries
assign 2,069 to SE/DK/NO/FI and retain 103 for review plus 23 unassigned;
only assigned sites occur in the retrieved and normalized site consumers.
This is archaeological site context and country accountability. It does not
admit a SEAD pollen series, an LRA cohort, or vegetation truth. The two linked
entity ledgers therefore cover different scientific roles and denominators.

LandClim's governed sequence inventory at
`data/landclim/normalized/nordic_pollen_site_sequences.csv`
supplies 490 context rows: Sweden 198, Denmark 127, Norway 93 and Finland 72.
These rows already feed the atlas and describe source site coverage, not
authenticated historical counts. The separate [1,128-row LandClim II study
crosswalk](../../../publication-replay/landclim-study-inputs/README.md) leaves
every historical primary input identity unresolved; its Nordic country labels
are publication metadata. Neither inventory supplies measured vegetation truth
or a qualified LRA cohort for the current Neotoma sites.

The [human and animal DNA source-scope review](../../../source-relations/dna-scope/README.md)
keeps two more entity populations distinct. AADR v66 has 51,005 annotation
rows across its 1240K and HO captures, representing 27,755 Genetic IDs;
these are human-source accountability units. The animal point surface has
170 features backed by 331 distinct sample IDs, of which eight Nordic
locality features represent 12 sample IDs. Its 1,450-row foundation still
has eleven unresolved paper-link rows. Neither population supplies pollen
counts or an independent vegetation reference, and the eight animal locality
features are not a Nordic pollen cohort.

| Family | Governed raw stage | Governed published stage | Four-country publication availability | Qualification |
| --- | --- | --- | --- | --- |
| AADR | present | present | collected in SE/DK/NO/FI | authority and source review required |
| animal aDNA | present | present | collected in SE/DK/FI; zero observations in NO | authority and biological sample review required |
| boundaries | present | present | collected in SE/DK/NO/FI | boundary inclusion review required |
| EMPD2 | missing | missing | blocked in SE/DK/NO/FI | source-reported partial coverage is not an admitted reference |
| HYDE | missing | missing | blocked in SE/DK/NO/FI | private custody is separate from governed source admission |
| LandClim | present | present | collected in SE/DK/NO/FI | context publication is not vegetation truth |
| Neotoma | present | present | collected in SE/DK/NO/FI | point context is not LRA admission |
| NFI | missing | missing | blocked in SE/DK/NO/FI | source and country reference review required |
| RAÄ | present | refused | blocked in SE; source unavailable elsewhere | authority and review unresolved |
| SEAD | present | present | collected in SE/DK/NO/FI | source-reported country cells are zero, governed site assignments are nonzero |
| SVAR | present | present | blocked in SE; source unavailable elsewhere | source authority refused |

“Collected” in this table is the exact `available_collected` publication
availability code, not a claim that every source family has an approved
analytical use. The full report supplies the separate lifecycle status and
count denominator for each cell. In particular, SEAD's source-reported zero
country cells coexist with governed and published site counts because those
dimensions answer different questions. The source-stage matrix's missing HYDE
row describes governed repository materialization; it does not deny the
separately retained private archive.

## Reproduce

From the repository root, use a fresh output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.source_capability \
  --repository "$PWD" \
  --output "$PWD/artifacts/jobs/source-capability/reproduction"
```

The producer refuses a missing or duplicate source/country cell, changed
parent artifact, negative count, incomplete source audit or changed input
bytes. It emits no new country assignment, ecological classification,
cross-source comparison, or release decision.
