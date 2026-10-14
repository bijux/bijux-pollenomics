# SEAD four-country retrieval and evidence denominators

The [report](report.json) and [country rows](rows.csv) join the governed
[country site-retrieval ledger](../../sead-country-retrieval/README.md) to the
source-native observation and evidence-event bundles from the same retained
SEAD acquisition. The source supplied no country field. Country counts are
later governed boundary assignments within the declared bounding box, not
source-native national discovery totals.

| Country | Assigned and retrieved sites | Source-native observations | Refused observation dispositions | Eligible sites/events |
| --- | ---: | ---: | ---: | ---: |
| Sweden | 1,925 | 163,107 | 163,107 | 0/0 |
| Denmark | 59 | 5,264 | 5,264 | 0/0 |
| Norway | 45 | 8,950 | 8,950 | 0/0 |
| Finland | 40 | 442 | 442 | 0/0 |
| **Total** | **2,069** | **177,763** | **177,763** | **0/0** |

All assigned sites occur in the retained `tbl_sites` payload and normalized
consumer, so terminal site-retrieval loss is zero in each country. The 103
boundary-review and 23 unassigned discovered sites were excluded from the
assigned retrieval scope; they are not retrieval failures and cannot be
silently attributed to a country. Their preflight coordinates have not been
independently verified. The capture has 61 complete table receipts and 19,005
complete query receipts with zero recorded query failures or retries. These
query counts apply to the shared four-country relation capture, so they are
reported globally rather than allocated to countries.

An observation disposition is not an admitted ecological event. All 177,763
source-native observations have refused event dispositions; zero evidence
events are eligible for propagation. The country refusal counts use each
country's observation denominator because the governed event bundle refuses
every observation; they are not a second set of independently counted events.
With no eligible source-owned event, no site has an eligible propagation event.
The provider did not report a schema
version. Capture completeness applies only to the pinned source snapshot,
declared bounding box and 61 relations, not to all sites in SEAD or to equal
national coverage.

This account covers the retrieval and observation/event parts of WP-01 section
6. The [chronology country account](../chronology-country-accounting/README.md)
covers reviewed claims separately. Per-country sample-group-linked sites,
physical samples, analysis entities, datasets, analysis values, and
propagation-eligible site denominators remain outside this replay. The report
marks these missing units explicitly; it makes no WP-01 closure claim.

## Reproduce

From the repository root, use an absent directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.sead_country_coverage \
  --repository . \
  --output artifacts/jobs/sead-country-coverage/reproduction
```

Compare `report.json` and `rows.csv` byte for byte with this directory. The
producer pins the existing country ledger, normalized observation and event
headers, materialization manifest and raw acquisition manifest by digest. It
checks each of the 61 receipt digests against the pinned manifest, validates
every query status and count, and refuses changed source identities or
denominators.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** The four-country account reconciles assigned site retrieval and all 177,763 source observation dispositions within one bounding-box capture.

**Unsupported claim.** Scoped query completeness is not national completeness, eligible events, source-native country reporting or complete source-unit accounting.

**Actual verification performed.** Read all four country rows and 61-table/19,005-query receipt totals in retained report; no acquisition or event rerun.

**Remaining input or review.** Excluded-coordinate review and source ecological/chronological admission remain; other unit denominators are owned by the separate unit account.

**Cause category.** Governed coverage and refused dispositions do not imply scientific support.

**Consequence.** 103 review/23 unassigned sites are excluded scope, not retrieval losses or country zeros.

**Precise next acceptance route.** Qualify excluded source coordinates and scientific event endpoints before expanding country/event claims.

**Negative or refused result.** 0 terminal assigned-site retrieval loss but 0 eligible events/sites; all 177,763 dispositions refused; no whole-workpack closure.

**Matched denominator.** 2,069 assigned sites; observations SE 163,107, DK 5,264, NO 8,950, FI 442=177,763; 61 table/19,005 query receipts, 0 recorded failures/retries.

Qualified authored reader SHA-256: `b3da26686742b5388f42b3cfbc9d489d3bc0b0dd36b9045394003025af36855c`.

- [Retained qualification evidence: docs/report/source-relations/sead/country-coverage/report.json](report.json) (SHA-256 `6b9887b73eacadca8ddad35a114a7d234b5e235500272faa2be84e7d3a50936d`).

- [Retained qualification evidence: docs/report/source-relations/sead/country-coverage/rows.csv](rows.csv) (SHA-256 `f4a3ca6b21f4e0d0715b0510ede9446ddc6d66732d3b0b833d4eebfa4166fdc3`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
