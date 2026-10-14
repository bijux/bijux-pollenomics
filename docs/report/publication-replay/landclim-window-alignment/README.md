# LandClim author and archive time windows

The [25-row window ledger](window-correspondence.csv) compares the author
example's BP bounds with the published PANGAEA 937075 filename intervals by
time-window index. **Only TW2, 100–350 BP, matches both bounds exactly.**
Twenty-four shared indices have different time support; TW3 already ends at
750 BP in the author example and 700 BP in the archive. The
[generated report](REPORT.md), [summary](report.json) and [manifest](manifest.json)
retain all intervals, source identities and output hashes.

This axis check permits the separately reported exact-TW2 numerical
correspondence. It does not authenticate the historical raw-input cohorts or
reproduce other published windows. Run the producer from the repository root
into a new artifact directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.published_window_alignment \
  --bins ../bijux-pollenomics-data/landclim/author-reference/author/bins.csv \
  --lookup ../bijux-pollenomics-data/landclim/author-reference/author/TWlookup.csv \
  --author-report docs/report/publication-replay/landclim-method-profile/reference/report.json \
  --published-report docs/report/publication-replay/landclim-published-window-correspondence/report.json \
  --output artifacts/landclim-window-alignment/replay
```

The producer writes LF line endings. A source-bound replay matches all three
governed outputs byte for byte.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Published-product versus released-author-example correspondence, not authenticated original input reconstruction.

**Supported claim.** All 25 author time intervals are compared by sharedTW index with documented archive filename bounds; onlyTW 2100–350 BP matches both endpoints exactly.

**Unsupported claim.** A sharedTW label does not authenticate matching temporal support, raw sample/chronology cohort, archived output values, historical reconstruction or measured vegetation accuracy.

**Actual verification performed.** The narrative and 25-row ledger/source report were inspected. The retained source-bound replay reproduces its three products with LF CSV. This qualification repeats no axis consumer, archive payload reconstruction, model or R execution.

**Remaining input or review.** Original selected chronologies and historical raw cohorts remain unauthenticated. Other 24 intervals need a separately declared common-support strategy and source data; endpoint relabeling or subtracting 50 years cannot recover those observations.

**Cause category.** data | comparability | assumption

**Consequence.** Permit direct same-window numerical correspondence only for the exact shared interval. Keep 25 window comparisons distinct from numerical cover/SE agreement and from historical data identity.

**Precise next acceptance route.** Authenticate historical chronology/sample selection and define a justified rebinning consumer from native observations before comparing nonmatching intervals. PreserveTW 2 exact support without generalizing to all 25 labels.

**Negative or refused result.** Twenty-four of 25 intervals differ: TW 1 starts−65 versus 0 BP, TW 3 ends 750 versus 700 BP, later author endpoints are 50 years older. These remain nonmatches; no window or age is silently relabeled.

**Matched denominator.** 25 interval pairs and 50 endpoint comparisons; one exact pair(TW2),24 nonexact. The numerical two-grid 31 taxon correspondence is a separate 124-value shared-window population, not produced by this axis check.

Qualified authored reader SHA-256: `3c6e6ffac3ed080d6260dabb28723967f5c54c3833530ce993b040f9d8ee98b6`.

- [Retained qualification evidence: docs/report/publication-replay/landclim-window-alignment/report.json](report.json) (SHA-256 `5b2892b1972934e484d2530078e9b7c844b6ebc0bcd1aeb08d167d8b7f7bd8f6`).

- [Retained qualification evidence: docs/report/publication-replay/landclim-window-alignment/window-correspondence.csv](window-correspondence.csv) (SHA-256 `3dbfc4914257a0862410a7c3b451a578f2c30b57991c9b0a59bef1b973f9a598`).

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
