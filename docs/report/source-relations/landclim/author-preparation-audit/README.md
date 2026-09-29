# LandClim author-example count preparation audit

The [source-bound report](report.json) independently sums every numeric raw
taxon column and every prepared count cell in the retained 17-site author
examples. The cohort contains nine sites in grid 512 and eight in grid 562.
Across those sites, **501,713 raw counts** split into **299,660 prepared
counts** and **202,053 raw-minus-prepared counts**. A fresh replay now
partitions the latter into **200,247 author `zz.do not use` counts, 418
unmapped counts and 1,388 outside the author time windows**. No counts fall
into the non-PPE category. The report retains these categories, source hashes
and count totals for every site.

The producer verifies the private 193-file author-source snapshot manifest for
each consumed source file. It also verifies the [private custody
receipt](../../../maintenance/artifact-retention/landclim-author-preparation-audit-custody.json)
for all 28 files in the older independent challenge. Its terminal 17-site
report and receipt match the fresh site totals exactly. The consumer replays
the author's first exact lookup match and time binning for all 17 sites.
`WHH05` has **2,482 raw = 2,448 retained + 34 `zz.do not use`**. The
unmapped counts occur at NTWITCHEN (144) and WHH11 (274); the 1,388
outside-window counts occur at EXEBRID.

The report keeps the eight unmapped source headers verbatim with zero-based
column positions and counts. NTWITCHEN has `Euphorbia t.` (7),
`Leguminoseae undiff.` (1), `Plantago major/minor` (9) and `Ranunculus t.`
(127); all four raw headers have a trailing space. WHH11 has `Prunus spp`
(20), `Hedera Helix` (38), `Filipendunla` (11) and
`` Ranunculus acris-type` `` (205, with a trailing grave accent in the source
header). These are unresolved author-lookup names, not approved synonym or
PPE assignments.

The lookup distinguishes `Plantago` from the separate leading-space label
`  Plantago`. Six LOBBSBOG counts under the former are excluded by the author
rule; trimming leading spaces would incorrectly retain them. A focused R
source check confirmed the exact `Plantago` mapping. Earlier failed and
narrower challenge jobs remain in private custody for diagnosis. The separate
[R formatting replay](../author-example-taxon-support/README.md) shows all 17
prepared files and 15,028 cells matching the author files.

This calculation supports the author-example raw-to-prepared relationship. It
does not identify these examples as historical rows of the 1,128-site ESSD
publication, resolve the `ISTS` PFT definition, provide measured vegetation
truth, or authorize new source uses.

Replay into an absent directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.essd_reproduction.author_preparation_audit \
  --repository . \
  --author-source-root /path/to/private/landclim/author-reference \
  --audit-root /path/to/private/landclim/author-preparation-audit \
  --output artifacts/jobs/landclim-author-preparation-audit/replay
cmp docs/report/source-relations/landclim/author-preparation-audit/report.json \
  artifacts/jobs/landclim-author-preparation-audit/replay/report.json
```
