# Our published LandClim estimate source account

We read the pinned PANGAEA 937075 mean and standard-error archive as a
**published modeled product**. Its exact source archive and receipt hashes are
in the [machine result](report.json). The current reader and two independent
historical challenges agree on 25 mean members, 25 standard-error members,
10,500 paired grid/window rows, 47 variables and 493,500 paired values. Our
[replay](replay.py) checks the original source bytes, recounts every retained
mean and standard error, and matches both independent result files
([structure](independent-structure.json), [inventory](independent-inventory.json)).

| Source property | Count |
| --- | ---: |
| Rows with usable coordinates | 10,350 |
| Rows with refused coordinates | 150, from six cell IDs |
| Exact mean-zero tokens | 251,123 |
| Mean values above `1` percentage point | 138,862 |
| Negative mean values | 3, in two rows |
| Negative standard errors | 0 |

The three negative means are source values, all at grid cell `725`: Castanea
`-0.000677087305195939` in 700–1200 BP and Picea/TBE1
`-0.0117533696932253` in 4700–5200 BP. We retained their native tokens and
did not clip them to zero. Values above `1` are in **percentage-cover units**;
that count is not a count of fractions above 100%. The six coordinate-refused
cell IDs and exact time-window labels are in `report.json`. A coordinate
refusal concerns spatial use of that published row, not the presence of its
modeled mean/SE values.

These checks authenticate the released product's row structure and current
reader correspondence. They do not recover the original 1,128 pollen inputs,
selected chronologies, historical basin geometry, archive-producing PFT
transformation or source-specific rights. The archive is not independently
measured vegetation, and reading it does not reproduce the publication's R
calculation. The governed result and replay above own the current source
account; historical challenge attempts do not change its scientific scope.

Reproduce the governed account from the repository root and compare bytes:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/publication-correspondence/published-inventory/replay.py \
  --output artifacts/jobs/published-inventory-source-account/replay.json
cmp artifacts/jobs/published-inventory-source-account/replay.json \
  reports/science/publication-correspondence/published-inventory/report.json
```


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Pinned archive modeled-product row structure, signs and coordinate-refusal counts are authenticated.

**Unsupported claim.** Original 1,128 pollen inputs or archive-producing REVEALS/PFT code.

**Actual verification performed.** Retained current reader and two independent structure/inventory challenges agree; index did not rerun.

**Remaining input or review.** The published archive row/column structure, signed mean tokens and coordinate refusals are counted and independently checked; original pollen and producer identity lie outside this modeled-product inventory. Resolver: Published archive reader owner Reopen when: Archive bytes, schema or the inventory claim changes; stronger historical claims require separate source packets.

**Cause category.** none within stated scope

**Consequence.** Keep coordinate refusals and negative source tokens while avoiding a measured-vegetation claim.

**Precise next acceptance route.** Archive bytes, schema or the inventory claim changes; stronger historical claims require separate source packets. Then update reports/science/publication-correspondence.md.

**Negative or refused result.** 150 rows from six cell IDs lack usable coordinates; three negative means are retained; no negative SE.

**Matched denominator.** 25 mean +25 SE members; 10,500 paired rows ×47 variables =493,500 paired values; 10,350 coordinate-usable rows.

Retained evidence: [reports/science/publication-correspondence/published-inventory/report.json](report.json), [reports/science/publication-correspondence/published-inventory/independent-inventory.json](independent-inventory.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
