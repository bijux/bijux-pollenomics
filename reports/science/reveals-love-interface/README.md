# How author REVEALS draws enter analytical LOVE

## Our decision

We tested the numerical interface between a multi-site REVEALS result and
analytical LOVE on the released LandClim author example. We used the first
time bin of grid 512 and the author's fixed site-bootstrap indices. This is a
method control: the constructed local ring is not an observed vegetation
reference, and BROADOWN also contributes to the regional cohort.

## What we ran

The [producer](replay.py) verifies the exact private author source manifest and
each of its 16 consumed files. Five sites with pollen support supply 1,000
regional draws on 31 taxa. We pass those draws to one 200–300 m LOVE ring with
the named LandClim fall-speed profile, including the author's 0.006 m/s
Filipendula value. A 999-draw input must be refused before the complete tensor
is accepted. We retain the [machine result](report.json) and a compact
[taxon summary](taxon-summary.csv) rather than source-derived sample rows.

## What we found

The current producer reproduced the earlier 1,000-draw regional tensor SHA-256
`08e2196d2a33a41e7084741cee197b192b852ce942fc22032499fcfe7ad7f770`
and its LOVE input identity. All 31,000 local draw cells are finite, but 8,312
are negative; the minimum is -0.4695301. These are unclipped mathematical
outputs. They cannot be interpreted as physically valid local cover. The
truncated tensor was refused. We have not held out a site or compared with
independent measured vegetation.

## Reproduce

Supply the private author snapshot identified by the
[source contract](../../../docs/report/pollen-reconstruction/author-source-custody.json)
and run from the repository root into an absent disposable directory:

```sh
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
  MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 \
  .venv/bin/python reports/science/reveals-love-interface/replay.py \
  --repository . --source-root "$BIJUX_LANDCLIM_AUTHOR_REFERENCE" \
  --output artifacts/jobs/reveals-love-interface/replay
```

The input snapshot remains in the qualified source store because its
redistribution rights are unresolved. Without those private bytes, readers
can check the retained result and source identities but cannot rerun the
source-backed calculation. The historical multi-site profile preserves its
documented bootstrap and PPE-uncertainty limitations; this interface check
does not correct them.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Constructed author REVEALS draw tensor enters analytical LOVE and enforces shape/identity.

**Unsupported claim.** Physical local vegetation estimate or independent held-out evaluation.

**Actual verification performed.** Retained replay validates source hashes, 999-draw refusal and output tensor; index did not rerun.

**Remaining input or review.** The constructed 1,000-draw regional-to-local interface returns finite but partly negative cover, reuses a site in its regional cohort, and requires private author bytes whose redistribution terms are unresolved. Resolver: Author source custodian and qualified LOVE/ecological reviewer Reopen when: Admissible independent regional/local cohort, physical basin and use rights enable a real measured-cover comparison.

**Cause category.** assumption|comparability|access/rights

**Consequence.** Treat negative cover as visible diagnostic, not a physically admissible composition.

**Precise next acceptance route.** Admissible independent regional/local cohort, physical basin and use rights enable a real measured-cover comparison. Then update reports/science/love-theory-paper.md.

**Negative or refused result.** 8,312 of 31,000 finite cells negative; local site overlaps regional cohort.

**Matched denominator.** 1,000 regional draws × one 200–300 m ring ×31 taxa =31,000 local cells; five pollen-supported regional sites.

Retained evidence: [reports/science/reveals-love-interface/report.json](report.json), [reports/science/reveals-love-interface/taxon-summary.csv](taxon-summary.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
