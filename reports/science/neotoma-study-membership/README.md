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
