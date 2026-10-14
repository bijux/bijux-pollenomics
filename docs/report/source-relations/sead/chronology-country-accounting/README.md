# SEAD chronology claim accounting by country

This [report](report.json) and [grouped rows](rows.csv) account for all **25,109**
retained SEAD chronology claims across Sweden, Denmark, Norway, and Finland.
The rows group claims by governed country, claim type, reviewed age basis,
comparability, and chronology display eligibility. Each row also counts distinct
sites with claims in that group; site counts across groups overlap and must not be
summed as independent sites.

| Country | Assigned sites | Sites with chronology claims | Claims |
| --- | ---: | ---: | ---: |
| Sweden | 1,925 | 741 | 22,643 |
| Denmark | 59 | 56 | 1,939 |
| Norway | 45 | 27 | 468 |
| Finland | 40 | 29 | 59 |
| **Total** | **2,069** | **853** | **25,109** |

The assigned-site denominator comes from [public custody](../public-custody/report.json).
Another **126** site decisions are excluded from the assigned and public set:
103 require country review and 23 remain unassigned. The 1,216 assigned sites
without captured chronology claims remain in the site denominator. Claim counts
are source-row counts, not event counts or site counts.

The machine report also gives `chronology_refusal_reasons_by_country` and
`propagation_refusal_counts_by_country`. A refused chronology claim can carry
both `chronology_not_comparable` and a more specific reason, so reason counts
overlap and must not be summed. Every claim, including one eligible for
chronology display, has propagation refused for the separate
`source_classification_not_accepted` reason.

The producer verifies the normalized claim and public-site CSV digests against
`source_lineage.json`, the age-review CSV digest against its report, shared
acquisition lineage against both reviews and public custody, a one-to-one
claim-ID join, claim/review status agreement, and every claim's site UUID and
country against the assigned public sites. The report records input hashes and
summarizes all claim types, age bases, comparability statuses, and eligibility
statuses. The 25,109-row claim/review inputs remain in their source locations;
this family stores only grouped results.

**Eligibility means chronology display only.** Every claim still has
`propagation_eligibility=refused`. This accounting grants no ecological event,
propagation, pollen, or scientific chronology admission. Relative periods,
uncalibrated or unresolved ages, negative-BP conversions, and open-ended
uncertainty retain their reviewed refusals.

## Reproduce

From the repository root, replay to an absent directory under `artifacts/`:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.sead_chronology_country_accounting \
  --repository . \
  --output artifacts/jobs/sead-chronology-country-accounting/reproduction
```

Compare `report.json` and `rows.csv` in that output with this directory byte for
byte. The producer refuses changed source digests, missing or duplicate rows,
country/site drift, and status or denominator changes.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

**Supported claim.** Country accounting preserves all 25,109 claim/review joins and assigned site denominators with display-only eligibility.

**Unsupported claim.** Group-site and overlapping reason counts cannot be summed as independent sites/events, and country assignment is governed rather than source-native.

**Actual verification performed.** The maintained chronology-country producer regenerated the account of 25,109 claims from its six current sources. The grouped CSV rows are byte-identical and every scientific report value is unchanged; only the public-custody parent input identity changed. The downstream map audit then consumed this regenerated report. No source classification, new scientific review or age calibration occurred.

**Remaining input or review.** Scientific classification, chronology/uncertainty decisions and excluded-site country authority remain.

**Cause category.** Claim rows, distinct sites and overlapping refusal reasons have different denominators.

**Consequence.** A site with multiple claim groups remains one site; display-eligible claims remain propagation-refused.

**Precise next acceptance route.** Preserve the source-native claim/review/site joins and all refusal roles; actually replay this producer when a custody parent changes before publishing downstream map correspondence. Stronger chronology or ecological claims require the missing source-specific uncertainty, classification and qualified evidence.

**Negative or refused result.** All 25,109 propagation claims refused; 1,216 assigned sites lack captured claims; 126 excluded decisions remain outside totals.

**Matched denominator.** 2,069 assigned sites/853 claim sites/25,109 claims:SE 22,643, DK 1,939, NO 468, FI 59; 13,170 display eligible/11,939 refused.

Qualified authored reader SHA-256: `649182c832da4178273bc3ec713bbc4073e608fbb37b655bf0c00aeb5ac0fe10`.

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-country-accounting/report.json](report.json) (SHA-256 `2f3b2bbfc27f8392d92ca00b1d9c9002612b8be2351844365aebb5f3efe4d80e`).

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-country-accounting/rows.csv](rows.csv) (SHA-256 `afdf52ee1b5dea2945fbc0c652dce92ce30eb5cfab2b01d2fa0f2e57f5e1fb8a`).

- [Retained qualification evidence: docs/report/source-relations/sead/chronology-claim-review/report.json](../chronology-claim-review/report.json) (SHA-256 `6e1d9c759862257fafe7b8b2c32c7b9d0b8a8c9860955ed06e4772f447056fa9`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
