# How we bound the author method to our publication profile

## Our decision

We used the released LandClim II author example to name an exact REVEALS
calculation profile. We checked the historical R function and wrapper,
17 raw and prepared example inputs, their site geometry, 31-taxon PPE and
covariance axes, 25 time bins and the retained two-grid comparison receipts.
We required the private source snapshot manifest and all 193 listed members
to pass SHA-256 checks before reading them. This bound profile lets us
interpret the [two-grid reexecution](author-example-reexecution.md) without
presenting its parameters as universally suitable for a Nordic core.

## What we matched and what differs

Our [method crosswalk](../../../docs/report/publication-replay/landclim-method-profile/method_crosswalk.csv),
[site input ledger](../../../docs/report/publication-replay/landclim-method-profile/example_inputs.csv)
and [machine report](../../../docs/report/publication-replay/landclim-method-profile/report.json)
record the following source comparisons:

| Source field | Our observation and decision |
| --- | --- |
| Executable and dispersal | The author wrapper calls the 30 October 2016 `REVEALS` release with neutral GPM, 3 m/s wind and 100,000 m regional extent. We named those values in `landclimii-2016-release-source-v1`. |
| Example sites and time | Grid 512 has nine sites and grid 562 has eight. All 17 source site rows use model code 2 (lake). The example supplies 26 boundaries and 25 midpoint bins. |
| Taxa and uncertainty | We matched the 31 named RPP/fall-speed inputs and ordered covariance axis. The retained source run uses 1,000 site-resampling draws; its multisite bootstrap does not propagate PPE covariance. |
| Missing support | Source R replaces `NA` inside available matrices with zero. Our native input masks a missing site/bin rather than treating it as an observed zero. We keep the distinction when comparing results. |
| Units | The source wrapper writes cover and SE in percent; the native run stores fractions. We scale before comparison. |
| Lake transport | We retained the historical lake gamma expression and its unresolved author comment. We did not infer a new physical basin model from the example. |

Each of the 17 ledger rows identifies its raw and prepared private member by
SHA-256, source model code and radius, and the matched native grid axes. The
[reference receipt](../../../docs/report/publication-replay/landclim-method-profile/reference/report.json)
and two grid manifests are pinned by hash beside the machine report. The
profile reader consumes those existing receipts; it does not rerun R or
native REVEALS merely to produce this crosswalk.

We reran the profile reader against the current private snapshot during this
review. Its crosswalk and site input ledger reproduced byte for byte. The
governed machine report had retained an older hash for
`author-source-custody.json`; we refreshed that one source identity from the
current custody file. The profile's parameter and scientific decisions did
not change.

## What remains unresolved

We did not reconcile the paper's 12-PFT statement, PANGAEA's 11-PFT
description and the 13 PFT-position columns in the 50 archived mean/SE CSV
headers. The source parameter table has 12 nonblank PFT codes, while
`ISTS` occurs in the archive header but not that table. Our
[PFT crosswalk](pft-crosswalk/README.md) establishes selected archived
mean arithmetic and preserves the Quercus and SE questions. Without an
authenticated archive-producing transformation, none of 11, 12 or 13 is a
universal classification count.

The released example bins do not identify all historical chronologies for
the paper's 1,128 sequences. These 17 sites are all lakes, so they do not
validate a bog-specific profile. We have not cleared private source
redistribution rights or obtained a matched measured-vegetation cohort.

## Reproduce the profile check

From the repository root, point the producer to the intact external author
snapshot and an absent run directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  -m bijux_pollenomics_dev.essd_reproduction.method_profile \
  --repository . \
  --private-root /path/to/landclim/author-reference \
  --output artifacts/jobs/landclim-method-profile/replay
```

The producer refuses a changed source member, R function signature,
example grid membership, native method setting or PANGAEA parameter/header
axis. The [focused regression](../../../packages/bijux-pollenomics-dev/tests/essd_reproduction/test_method_profile.py)
also checks publisher-table differences without private data. Set
`BIJUX_LANDCLIM_AUTHOR_REFERENCE` to run its opt-in source and byte-replay
checks. We use the resulting profile for source-specific numerical
correspondence; a new core still needs its own chronology, basin geometry,
eligible count denominator, PPE and rights decision.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Author example executable, geometry, 31-taxon PPE/covariance and 25-bin profile are named.

**Unsupported claim.** Transfer of lake gamma, missing-support or covariance choices to an unreviewed Nordic core.

**Actual verification performed.** Retained 193-member private capsule manifest and method crosswalk are reported; index did not rerun.

**Remaining input or review.** The released 17-site PPE/covariance profile is bound, but the lake gamma comment, missing-support semantics and historical source/profile identity do not authorize transfer to other cores. Resolver: Author method/profile owner and qualified transport reviewer Reopen when: Source owner identifies the historical parameter, missing-support and basin choices for a named core/window.

**Cause category.** data|assumption

**Consequence.** Do not convert author NA-to-zero handling into an observed zero or assume physical basin validity.

**Precise next acceptance route.** Source owner identifies the historical parameter, missing-support and basin choices for a named core/window. Then update reports/science/publication-correspondence.md.

**Negative or refused result.** No example-profile mismatch reported; unsupported historical cores remain refused.

**Matched denominator.** 17 lake rows: grid 512 nine and grid 562 eight; 26 boundaries/25 bins; 1,000 site-resampling draws in author source.

Retained evidence: [docs/report/publication-replay/landclim-method-profile/report.json](../../../docs/report/publication-replay/landclim-method-profile/report.json), [docs/report/publication-replay/landclim-method-profile/method_crosswalk.csv](../../../docs/report/publication-replay/landclim-method-profile/method_crosswalk.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
