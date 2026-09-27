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
