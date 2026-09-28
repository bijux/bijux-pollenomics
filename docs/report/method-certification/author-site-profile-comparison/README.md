# Historical and reviewed author-site REVEALS summaries

This [replay](replay.py) uses the six released author example sites at grid 512,
225 BP and the ten positive-at-every-site taxa in the [conditional author-site
study](../author-site-uncertainty/README.md). It reads the same source-prepared
counts, deposition factors and 1,024 retained draw identities. The first 1,000
site-index rows are used for this comparison because the historical publication
bootstrap defines 1,000 draws. Source-file, draw-file and code identities are
retained in the [machine result](report.json) (SHA-256
`4fa285302a1d19b3122d1e3ea2ec318f0a635e1abd1140b3f247faf5bd66ccdf`).

The historical release reports a ratio of accumulated unclosed weights as its
mean, while computing its standard error from individually closed site-bootstrap
draws. On these exact paired site indices, the reviewed site-only calculation
uses the arithmetic mean of the **same** 1,000 closed draws. Their standard
errors agree within `2.56e-15` fraction units; the largest mean difference is
`0.00162335` fraction (`0.162335` percentage points) for Cyperaceae. This
isolates a summary-rule difference, rather than a deposition or draw difference.

A third calculation uses the same 1,000 site indices with one conditional
multinomial count draw per original site and one shared correlated PPE vector
per replicate. Its cover and standard error are the arithmetic mean and sample
standard deviation of the paired closed draws. For Cerealia-t, the site-only
standard error is `0.00250450` fraction and the joint standard error is
`0.00490193`; for Cyperaceae they are `0.120725` and `0.121957`.
These values are conditional on the declared draw producer and the selected
ten-taxon denominator. Differences between site-only and joint standard errors
are not additive variance components.

The historical source implementation is separately checked against tagged R
on a full-grid 31-taxon case. This selected ten-taxon comparison did not run a
new R calculation. Static source radii are interpreted as metres; chronology,
geometry and transport are fixed. The selected taxa were chosen after seeing
source counts. No full-author-axis, Nordic LRA or vegetation-accuracy claim
follows from this numerical comparison.

Reproduce the governed report and compare its bytes:

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 .venv/bin/python \
  docs/report/method-certification/author-site-profile-comparison/replay.py \
  --repository . --source-root /path/to/landclim/author-reference \
  --output artifacts/jobs/author-site-profile-comparison/replay
cmp docs/report/method-certification/author-site-profile-comparison/report.json \
  artifacts/jobs/author-site-profile-comparison/replay/report.json
```
