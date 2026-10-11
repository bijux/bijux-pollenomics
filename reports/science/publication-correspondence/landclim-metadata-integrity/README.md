# Our LandClim metadata integrity check

We independently checked the LandClim full-study metadata bundle. The
[result](result.json) records eight passing checks and nine adversarial edits
that the tested reader rejected. It used the pinned public workbook and
inventory to reconstruct all five bundle outputs, checked 1,128 metadata rows
and 4,512 explicit requirement refusals, and compared two isolated
generations. All five result hashes still match the [governed
files](../../../../docs/report/publication-replay/landclim-study-inputs/README.md).
The independent checks ran against the source revision identified in the
machine result; current output identity does not prove current reader-code
identity or repeat those nine adversarial executions.

The result's verdict is `pass_scoped_metadata_bundle`. Its source boundary
explicitly reports zero authenticated historical pollen counts, zero historical
chronologies, zero historical/current revision matches, zero cleared per-sequence
rights and no publication-specific R execution. We do not use this metadata
check as full ESSD reproduction, empirical LRA admission or ecological accuracy.
The result and current-product hash check preserve that bounded verdict. They
do not provide the missing historical study inputs.

From the repository root, check that the retained verdict and five exact
product identities still agree:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/publication-correspondence/landclim-metadata-integrity/verify.py
```

## Stored workbook values

A separate source audit read all 32 tabs of the five retained scientific
workbooks: the two LandClim I workbooks, the Marquer grid-cell workbook, and the
LandClim II quality and site-metadata workbooks. Their stored cells retain site
metadata, reconstructed vegetation means and standard errors. This audit adds
source observations alongside the existing eight-check result; it leaves that
result and its nine recorded refusals unchanged. Historical primary pollen
counts, chronology identity and publication-specific execution retain their
separate admission requirements.

In both LandClim I workbooks, all ten result tabs contain two different places
with `LCGRID_ID = 522`. Workbook row 169 has `LCGRID_ = 1123`, cell
`6°E 53°N` and label `6.53 NLD`; row 189 has `LCGRID_ = 1223`, cell
`6°E 51°N` and label `6.51 DEU`. Preserve workbook, sheet and row together with
the spatial fields. Merging these rows by the repeated project ID would combine
different locations. The [published dataset description](https://doi.pangaea.de/10.1594/PANGAEA.897303)
identifies those IDs as internal project identifiers and the cell coordinates
as the northwest corners of one-degree grid cells.

The largest stored mean-composition discrepancy in the
[LandClim I PFT workbook](../../../../data/landclim/raw/landclim_i_plant_functional_types.xlsx)
occurs in `2700-3200BPmeanLC`, row 106: `LCGRID_ = 912`,
`LCGRID_ID = 811`, cell `5°W 57°N`, label `RF`. Its eleven PFT values sum to
approximately `0.9944434`, leaving a deficit of `0.0055566`. At the same row in
the [LCT workbook](../../../../data/landclim/raw/landclim_i_land_cover_types.xlsx),
evergreen trees are `0.212494`, summergreen trees `0.443593`, and openland
`0.343913`, summing to one at the displayed precision. The nonzero PFT entries
are IBE `0.212494`, IBS `0.279624`, TSD `0.163969`, LSE `0.0262794` and GL
`0.312077`. Evergreen and summergreen arithmetic agrees at that precision;
openland exceeds the displayed LSE-plus-GL contribution by `0.0055566`.
This localizes the discrepancy in the stored values without identifying a
missing taxon or an authorized correction.

The published description expects reconstructed mean proportions to sum to one.
The workbook metadata, headers, non-grid annotations and stored comments, and
the reviewed dataset landing page, provide no specific explanation for these
repeated IDs or this PFT deficit. The cited paper's taxon-to-PFT classification
table still needs its own source review before drawing a causal conclusion.
Retain the raw workbook values and these scoped discrepancies. No deduplication,
renormalization or inferred missing-taxon value was applied. Standard errors
have their own uncertainty meaning and were not tested for compositional closure.
