# Historical and reviewed author-site REVEALS summaries

This [replay](https://github.com/bijux/bijux-pollenomics/blob/0cca6d4e9cd4df7fa5c844e440c78aceaa162d1b/docs/report/method-certification/author-site-profile-comparison/replay.py) uses the six released author example sites at grid 512,
225 BP and the ten positive-at-every-site taxa in the [conditional author-site
study](../author-site-uncertainty/README.md). It reads the same source-prepared
counts, deposition factors and 1,024 retained draw identities. The first 1,000
site-index rows are used for this comparison because the historical publication
bootstrap defines 1,000 draws. Source-file, draw-file and code identities are
retained in the [machine result](report.json) (SHA-256
`73649b9d5e5c3b4699840148140b4b0edab8fd939e82b357852e2e162792dde4`).

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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** For the retained six-site 225 BP author example and ten selected taxa, the same first 1,000 paired indices compare ratio-of-unclosed-means with arithmetic mean-of-closed-vectors; the largest retained mean difference is 0.0016233449666228639 fraction.

**Unsupported claim.** This compares two aggregation definitions on shared prepared inputs; it establishes neither independent field vegetation accuracy, an exact new ten-taxon historical R reproduction nor additive uncertainty components.

**Actual verification performed.** Executed the maintained author-site profile comparison on local main at 0cca6d4e9cd4df7fa5c844e440c78aceaa162d1b, after the genuine source-bound uncertainty outputs were adopted, and an independent complete-product observer; both native stages exited zero. All typed scientific values matched the retained comparison, using the exact first 1,000 of 1,024 stored draw identities for six original sites and ten selected taxa. Seven changed metadata leaves bind the actual upstream report and current calculation source; no new R execution or ecological model fit was performed.

**Remaining input or review.** Current-source owner replay and its reader/report references are reconciled. Independent interpretation of the selected taxon population, justified chronology and geometry, source rights and any matched measured vegetation target remain separate scientific acceptance.

**Cause category.** Current-source conditional aggregation comparison on shared author-derived data, with authenticated upstream uncertainty and unchanged paired scientific values.

**Consequence.** The current calculation and reader now bind the same source report and code epoch. The retained mean discrepancy still follows closure order even with shared draws and cannot identify which profile is ecologically more accurate.

**Precise next acceptance route.** Use this source-bound comparison alongside the adopted conditional uncertainty account; distinguish the two definitions on the preserved 1,000 paired indices from any later independent measured-target, chronology, geometry or scientific-release assessment.

**Negative or refused result.** The nonzero mean discrepancy is retained; the near-zero maximum standard-error difference 2.55351295663786e-15 does not establish equivalence of the two mean definitions.

**Matched denominator.** Six sites in one grid and window; ten selected taxa from 31 prepared targets, 10,404 selected counts from 10,747 author-target counts; first 1,000 of 1,024 paired draws.

- [Retained qualification evidence: docs/report/method-certification/author-site-profile-comparison/report.json](report.json) (SHA-256 `73649b9d5e5c3b4699840148140b4b0edab8fd939e82b357852e2e162792dde4`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
