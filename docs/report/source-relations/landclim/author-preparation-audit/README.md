# LandClim author-example count preparation audit

The [source-bound report](report.json) independently sums every numeric raw
taxon column and every prepared count cell in the retained 17-site author
examples. The cohort contains nine sites in grid 512 and eight in grid 562.
Across those sites, **501,713 raw counts** split into **299,660 prepared
counts** and **202,053 raw-minus-prepared counts**. The report retains each
site's raw/prepared source hashes and count totals.

The producer verifies the private 193-file author-source snapshot manifest for
each consumed source file. It also verifies the [private custody
receipt](../../../maintenance/artifact-retention/landclim-author-preparation-audit-custody.json)
for all 28 files in the older independent challenge. Its terminal 17-site
report and receipt match the fresh site totals exactly. For `WHH05`, the
producer additionally replays the author's first-match lookup and binning over
all eight raw samples: **2,482 raw = 2,448 retained + 34 `zz.do not use`**;
other exclusion categories are zero.

For the other 16 sites, the detailed exclusion categories remain historical
producer/receipt evidence. The fresh consumer independently verifies the
source raw and prepared sums and their difference; it does not reclassify
every taxon exclusion at those sites. Earlier failed and narrower challenge
jobs remain in private custody for diagnosis. The separate
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
