# Where the released example and published archive diverge

## Our decision

We compared the author R example, our installed calculation and the pinned
June 2021 PANGAEA 937075 archive only on the exact common 100–350 BP
window. We paired 31 taxon means and 31 standard errors for each of grids
512 and 562: 124 numerical values in all. We converted author fractions to
percentage cover before comparison and kept the 31-taxon mean vectors
unrenormalized. The [124-row ledger](../../../docs/report/publication-replay/landclim-published-window-provenance/paper-correspondence.csv)
and [machine summary](../../../docs/report/publication-replay/landclim-published-window-provenance/report.json)
retain the exact values, archive identity and source hashes.

## What we found

Our installed calculation and independently executed author R agree to at
most `1.238e-11` percentage points on the selected rows. The larger archive
differences occur in the independent R values as well as our implementation.

| Grid | Largest mean gap, percentage points | Largest SE gap, percentage points | Mean L1 gap, percentage points | Total variation | Hellinger |
| --- | ---: | ---: | ---: | ---: | ---: |
| 512 | 9.19787 | 3.21615 | 18.481237 | 0.092406 | 0.078055 |
| 562 | 10.55270 | 4.25814 | 22.140770 | 0.110704 | 0.101288 |

Both 31-taxon mean vectors sum to 100 percent within `1e-6` percentage
points. We calculated L1 as the sum of absolute percentage-point gaps,
total variation as L1 divided by 200, and Hellinger on the nonnegative
mean fractions. The two largest-gap taxa explain 72.9% of grid 512's L1
gap (Cyperaceae and Calluna vulgaris) and 94.0% of grid 562's gap
(Calluna vulgaris and Poaceae). The largest SE discrepancies follow
Cyperaceae and Calluna vulgaris in grids 512 and 562 respectively. The
[generated numerical interpretation](../../../docs/report/publication-replay/landclim-published-window-provenance/REPORT.md)
records medians and further calculation detail.

## What this changes

We retain a source-version question rather than diagnosing a Python-only
calculation error. The released 2016 example and the June 2021 archive have
not been authenticated as using identical raw pollen revisions, selected
chronologies, preparation and aggregation. Our
[window alignment](../../../docs/report/publication-replay/landclim-window-alignment/README.md)
identifies TW2 as the sole exact interval match among 25 author/archive
windows; we did not shift other intervals into a false correspondence.

These are distances between two modeled products. They are neither an
independent measured-vegetation score nor full reproduction of the 1,128
published sequences. Our [publication account](../publication-correspondence.md)
retains the source-owner questions on raw rows, interval meaning and the
archive PFT/LCT transformation.

## Reproduce the bounded comparison

With the two upstream governed correspondence ledgers and the private
author-name crosswalk available, run the producer into an absent artifact
directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.essd_reproduction.published_window_provenance \
  --author-csv docs/report/publication-replay/landclim-author-example-correspondence/paper-correspondence.csv \
  --author-report docs/report/publication-replay/landclim-author-example-correspondence/report.json \
  --published-csv docs/report/publication-replay/landclim-published-window-correspondence/paper-correspondence.csv \
  --published-report docs/report/publication-replay/landclim-published-window-correspondence/report.json \
  --crosswalk-csv ../bijux-pollenomics-data/landclim/author-reference/reference/taxon-name-crosswalk.csv \
  --output artifacts/jobs/landclim-published-window-provenance/replay
```

The [governed manifest](../../../docs/report/publication-replay/landclim-published-window-provenance/manifest.json)
binds the upstream ledgers, private crosswalk and producer. The producer now
writes LF CSV, and all three governed outputs match a source-checked replay
byte for byte. This owner replay does not authenticate the missing historical
raw inputs behind the published archive.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Author R/native TW2 pairing is exact numerically within their profile; archive is compared on sole interval match.

**Unsupported claim.** A source-causal diagnosis of the archived difference or retrospective alignment of other windows.

**Actual verification performed.** Retained 124-row TW2 ledger, window alignment and uncertainty-envelope report are cited; index did not rerun.

**Remaining input or review.** Only TW2 is exact interval support; author R and archive means/SEs differ there, but source revisions and producing steps are unknown, so neither mismatched windows nor code failure explain the gap. Resolver: LandClim archive/source producer and qualified chronology reviewer Reopen when: Exact historical TW2 input rows, chronology, transformation and other-window definitions are authenticated and replayed.

**Cause category.** data|comparability|algorithm/numerical

**Consequence.** Report differences as two modeled products; overlapping one-SE envelopes are not a significance test.

**Precise next acceptance route.** Exact historical TW2 input rows, chronology, transformation and other-window definitions are authenticated and replayed. Then update reports/science/publication-correspondence.md.

**Negative or refused result.** Archive mean/SE gaps remain: grid 512 maxima 9.19787/3.21615 and grid 562 10.55270/4.25814 percentage points.

**Matched denominator.** TW2 100–350 BP; 31 means +31 SEs per grid × two grids =124 paired values; 25 windows screened for alignment.

Retained evidence: [docs/report/publication-replay/landclim-published-window-provenance/report.json](../../../docs/report/publication-replay/landclim-published-window-provenance/report.json), [docs/report/publication-replay/landclim-published-window-provenance/paper-correspondence.csv](../../../docs/report/publication-replay/landclim-published-window-provenance/paper-correspondence.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 521b5f83ce096982214d0967acee116bc473697d926e96a2a50b796a803264e8 -->
<!-- scientific-authored-source-sha256: 4cf28ee1c5f7c2813ea40da6e26c1f4ab51fe9ef3612f93d43a548284b0aa35b -->
<!-- scientific-verification-and-limits:end -->
