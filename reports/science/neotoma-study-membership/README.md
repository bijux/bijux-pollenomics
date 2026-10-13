# Which Neotoma samples entered the Nordic pollen study?

We joined the four retained 31-target observed-pollen study metadata files to
every sample in the governed [Neotoma relational source](../../../data/neotoma/relational/manifest.json).
The [decision ledger](decisions.csv) gives each of the 12,388 source sample IDs
one source row locator, country, site, dataset and study membership. The
[result](report.json) binds the source manifest, exact sample part,
[per-sample pollen screen](../../../docs/report/source-relations/neotoma/pollen-screen/report.json)
and four study metadata files by byte count and SHA-256.

| Source country | Source samples | Selected in study | Same site, not selected | Outside study sites |
| --- | ---: | ---: | ---: | ---: |
| Denmark | 279 | 91 | 1 | 187 |
| Finland | 2,184 | 1,797 | 202 | 185 |
| Norway | 3,884 | 3,544 | 30 | 310 |
| Sweden | 5,764 | 228 | 0 | 5,536 |
| **Four countries** | **12,111** | **5,660** | **233** | **6,218** |

Another 277 source samples have no assigned country and remain separately
marked `unresolved_source_country`. All 5,660 selected IDs agree with their
source site and country across 84 study sites. The source pollen screen refuses
all 233 same-site nonselections: 186 lack a sample-owned comparable typed age,
53 lack a numeric count candidate, and six have both reasons. These are source
screen reasons, not a proven explanation of the study's selection rule.

Six Swedish IDs are present in the study metadata while the source pollen
screen refuses them for lacking a sample-owned comparable typed age. The
[machine result](report.json) names each ID and verifies its native sample age:
all six are negative BP and map to nominal bin `-1` under the declared 500 BP
width. The frozen Swedish prediction file refuses bin `-1` at all three sites
for insufficient positive-count training groups; none of these six enters a
scored prediction. We retain both the study metadata and source-screen
decisions. The 6,218 samples outside the 84 selected sites are not exclusions
from Neotoma itself or from every possible analysis.

These are membership decisions for prior-exposed **observed-pollen** studies.
They do not admit a lake to LRA, establish source rights or validate a pollen
prediction against vegetation. The [Nordic study account](../nordic-pollen-study.md)
and its country reports retain the scored-bin and taxon denominators; sample
membership alone does not imply a scored bin.

The [producer](replay.py) verifies the source part against its manifest,
joins all 12,388 original pollen-screen decisions by exact sample and row
locator, refuses duplicate or missing selected IDs, and checks every selected
site's source country. It also checks the six native ages against the frozen
prediction refusals. It leaves sealed target outcomes untouched.
Reproduce into a new directory under repository `artifacts/`, then compare
`decisions.csv` and `report.json` byte for byte with the governed files:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/neotoma-study-membership/replay.py \
  --repository . --output artifacts/jobs/neotoma-study-membership-replay
```


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Every selected 31-target study sample is assigned one governed source membership and source-screen status.

**Unsupported claim.** Original site-selection rationale, country assignment for all rows or vegetation/LRA admission.

**Actual verification performed.** Retained 12,388-row ledger and producer source-screen join are reported; index did not rerun.

**Remaining input or review.** The 12,388-ID membership ledger closes, but 277 rows lack assigned source country; the 233 same-site refusals have screen reasons rather than proven original selection rationale, and membership is not scored prediction support. Resolver: Neotoma source/country decision owner and original study selector Reopen when: Versioned country authority and selection decisions resolve rows before changing study membership or scores.

**Cause category.** data|comparability

**Consequence.** Do not treat source membership or refused negative-BP samples as scored predictions.

**Precise next acceptance route.** Versioned country authority and selection decisions resolve rows before changing study membership or scores. Then update reports/science/source-cohorts.md.

**Negative or refused result.** 277 unassigned-country rows; 233 same-site nonselected rows fail source screen; six selected negative-BP Swedish rows are not scored.

**Matched denominator.** 12,388 samples =5,660 selected +6,218 outside selected sites +233 same-site unselected +277 unassigned.

Retained evidence: [reports/science/neotoma-study-membership/decisions.csv](decisions.csv), [reports/science/neotoma-study-membership/report.json](report.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: ed4364a71f864d140fca52f47e784b57a9cdae6d50032b1b7dee883a352b2dd7 -->
<!-- scientific-authored-source-sha256: a0a7b86ba0395a6e40e7a24c4b384ced7b39e7afde096d7f13c98296488f88c4 -->
<!-- scientific-verification-and-limits:end -->
