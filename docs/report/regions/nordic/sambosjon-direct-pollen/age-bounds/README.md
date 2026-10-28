# Sämbosjön source age bounds against fixed pollen bins

The [source-bound report](report.json), [111 selected sample rows](samples.csv),
[22-bin coverage ledger](bins.csv) and [boundary ledger](boundaries.csv) compare
the selected Sämbosjön calibrated sample ages with their own reported younger
and older bounds. This is an age-only diagnostic for the existing
[direct observed-pollen result](../README.md). It does not open pollen
observation parts, change the frozen predictions or recalculate scores.

**58 of 111** sample intervals have positive-width overlap with two nominal
500-cal-BP bins; the other **53** lie wholly within their point-age bin. Each
of the **22 scored nominal bins** contains at least one boundary-crossing
sample. All **21 internal boundaries**, 1,000–11,000 cal BP, are crossed by at
least one reported interval. No interval overlaps more than two bins or extends
beyond the existing 1–22 bin range. Nominal bin 1 has three samples and none
has its entire reported interval inside that bin. The bin ledger retains the
point-age sample count, the number of crossing and wholly contained nominal
samples, and the count of intervals that could overlap each bin. These overlap
counts are separate marginal possibilities; they are not a simultaneous
reallocation of the 111 samples.

For an interval `[younger, older]`, a bin counts as overlapped only when their
intersection has positive width. Touching an older bin boundary at one point
does not count as crossing it. The source's point age defines the nominal bin;
the younger and older values define overlap. Every selected point age lies
within its reported bounds. The retained chronology is the source-default
calibrated `Giesecke et al. 2014 (MADCAP)` smooth spline based on IntCal09.
Its sample claims and chronology notes give **no confidence level** for these
bounds, and no joint age posterior was retained. This calculation therefore
does not assign probabilities to neighboring bins or invent new age draws.

The fixed pollen score used point-age bins: 22 bins were scored, with IDW MAE
0.022991 on the declared 16-label subcomposition. Because all 22 bins contain
at least one boundary-crossing sample, their membership is conditional on
the selected point ages. The interval-overlap screen alone cannot tell how a
different age assignment would change each bin's pollen composition, positive
count support or MAE. The [machine report](report.json) binds the selected
sample and chronology identities to the retained Neotoma manifest, age-claim
part, direct-pollen input receipt, prediction freeze and unchanged score files.

Replay from the repository root into an absent directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.sambosjon_age_bounds \
  --repository . \
  --output artifacts/jobs/sambosjon-age-bounds/replay
```


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Named Nordic source/development wrapper; its own source denominator remains separate from canonical study/account limits.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/sambosjon-direct-pollen.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/sambosjon-direct-pollen.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
