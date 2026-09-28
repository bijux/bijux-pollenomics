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
