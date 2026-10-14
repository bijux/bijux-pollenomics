# SEAD interval-set review

This review binds the pinned `sead-full-evidence-39bfff6a-ce80714e` capture to
the Nordic chronology export. The claim index has SHA-256
`b9accf421059eebf95b75a8c22fd237f4d51991fbc868e79530d20a694e6cd21`.
The [machine-readable report](report.json) records the six claim-part hashes,
native source-table hashes from the age-basis review, and both GeoJSON hashes.
The [site inventory](sites.csv) lists every exported site, including sites with
no eligible dated record.

All 25,109 claims were checked against native age records. Exactly 13,170
eligible AD calendar-year claims appear once each in 7,244 distinct exported
record-interval features. The remaining 11,939 contextual, unresolved, or
refused claims contribute no record interval. Of 2,069 sites, 370 have at least
one eligible record interval; 299 of those have two or more separated interval
components. Components merge only when their closed integer-BP intervals
overlap or are adjacent. A gap stays a gap.

Site 3840 (`000ef3d9-389f-46cd-8cf9-a9c49507f5cd`) provides a native-backed
regression: 79 eligible claims form 11 exported record features. Their union is
82–83 and 105–107 BP; 84–104 BP is unobserved. Its site display span is
82–107 BP and must not imply dated evidence in that gap. The fieldwork
time-aware count, human-overlap score, and nearby temporal anchors now refuse
`SEAD` / `sead-sites` display envelopes. The site still counts toward spatial
site density. Record-level SEAD features remain separate in the export.

The numeric site span is a display envelope. It is never an analytic interval
or an event observation. This review verifies interval preservation and
source linkage; it does not approve qualified ages, scientific chronology
selection, first-observed events, or propagation. Fieldwork ranking currently
loads the site layer for SEAD context, so it cannot claim record-level SEAD
temporal support until a governed record-interval join is added.

## Reproduce

From the repository root, choose an absent output directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c \
  'from pathlib import Path; from bijux_pollenomics.collection.sources.sead.evidence.review.interval_sets import write_sead_interval_set_review; write_sead_interval_set_review(Path("data"), Path("artifacts/jobs/sead-interval-sets/reproduction"))'
```

Compare the generated `report.json` and `sites.csv` byte-for-byte with the
governed files in this directory. The focused review and fieldwork tests passed
18 cases; mypy and Ruff passed for the four affected Python files.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The interval review preserves disjoint eligible record support and unobserved gaps instead of using site envelopes analytically.

**Unsupported claim.** Numeric display spans are not continuous dated occupation, arrival, event or propagation intervals.

**Actual verification performed.** Read interval totals, site inventory and native-backed site 3840 gap witness; no map filter or claim consumer rerun.

**Remaining input or review.** Qualified chronology/event meaning and governed record-level temporal joins for future ranking remain missing.

**Cause category.** Display envelopes overstate temporal support if used as observations.

**Consequence.** Spatial site density may use context points; time-aware analytic support must refuse their display hulls.

**Precise next acceptance route.** Qualify record-age/event meaning and add an explicit source-bound record-interval join before temporal ranking or propagation.

**Negative or refused result.** 11,939 claims contribute no record interval; site 3840 gap 84–104 BP stays unobserved; 0 ecological events admitted.

**Matched denominator.** 25,109 reviewed claims→13,170 eligible claims/7,244 record intervals; 2,069 sites, 370 with intervals/299 with separated components; site 3840 has 79 claims/11 records.

Qualified authored reader SHA-256: `9a7e07e2c7771913a5dcf1cf4cc96d3ef96dbd1860d601b17389965f2e08cec7`.

- [Retained qualification evidence: docs/report/source-relations/sead/interval-sets/report.json](report.json) (SHA-256 `b2c7fe1f2e4ab7b1d331031abcc4fac9bd484d81345f463df5d3f08085a0735c`).

- [Retained qualification evidence: docs/report/source-relations/sead/interval-sets/sites.csv](sites.csv) (SHA-256 `75b37bccd76b3e523d976f754ec562d07b0b6ce6059c9676d4ec45cd4cedfacf`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
