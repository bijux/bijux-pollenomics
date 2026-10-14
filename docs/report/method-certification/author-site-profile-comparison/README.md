# Historical and reviewed author-site REVEALS summaries

This [replay](https://github.com/bijux/bijux-pollenomics/blob/6956a977bf391b9b1de1706f4f4c0bd75e222ba2/docs/report/method-certification/author-site-profile-comparison/replay.py) uses the six released author example sites at grid 512,
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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Numerical/method correspondence reader: source assumptions and historical/independent accuracy acceptance remain separate.

**Supported claim.** For the retained six-site 225 BP author example and ten selected taxa, the same first 1,000 paired indices compare ratio-of-unclosed-means with arithmetic mean-of-closed-vectors; the largest retained mean difference is 0.0016233449666228639 fraction.

**Unsupported claim.** This compares two aggregation definitions on shared prepared inputs; it establishes neither independent field vegetation accuracy, an exact new ten-taxon historical R reproduction nor additive uncertainty components.

**Actual verification performed.** Reviewed the authored explanation and retained report, checked the report's physical identity and selected/total support; no author R execution, bootstrap or model fit was rerun for this reader qualification.

**Remaining input or review.** Current-source owner replay and independent interpretation of the selected taxon population remain required; a new ecological claim also needs a matched measured vegetation target and justified source assumptions.

**Cause category.** Conditional aggregation semantics on shared author-derived data.

**Consequence.** A mean-profile discrepancy can follow closure order even with shared draws; it cannot identify which profile is ecologically more accurate.

**Precise next acceptance route.** Replay the named profile-comparison owner against the qualified current author-site account, retain the same 1,000 indices and distinguish definition correspondence from any later measured-target comparison.

**Negative or refused result.** The nonzero mean discrepancy is retained; the near-zero maximum standard-error difference 2.55351295663786e-15 does not establish equivalence of the two mean definitions.

**Matched denominator.** Six sites in one grid and window; ten selected taxa from 31 prepared targets, 10,404 selected counts from 10,747 author-target counts; first 1,000 of 1,024 paired draws.

Qualified authored reader SHA-256: `1aebaa86dc88b25680710f08c10e19acde1e891ec10f80ee641522ead6f55bb8`.

- [Retained qualification evidence: docs/report/method-certification/author-site-profile-comparison/report.json](report.json) (SHA-256 `4fa285302a1d19b3122d1e3ea2ec318f0a635e1abd1140b3f247faf5bd66ccdf`).

- [Canonical scientific account: reports/science/method-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/method-correspondence.md) (source SHA-256 `81407d77987fd391ea470cc975195107085cdf7a934a6716aac7a1b22cb19050`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
