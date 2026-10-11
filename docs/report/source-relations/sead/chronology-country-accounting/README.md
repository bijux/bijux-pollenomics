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
