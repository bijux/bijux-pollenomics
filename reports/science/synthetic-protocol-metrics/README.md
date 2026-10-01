# Six retained synthetic protocol score summaries

## Our decision

We recovered one older, distinct synthetic scoring result before retiring its
artifact workspace. The [16-row score table](scores.csv) separates pollen
composition from vegetation cover, six different prediction protocols, and
the four local pollen scores that are **in-sample diagnostics**. We do not pool
these heterogeneous rows into one accuracy number or use them as evidence of
real Nordic vegetation accuracy. Each target has **39 requested units, 31
scored units and eight prediction failures**; the failures occur in the
partial spatial-block challenge.

| Selected protocol | Pollen MAE, fraction | Vegetation MAE, fraction | Scored / requested per target |
| --- | ---: | ---: | ---: |
| Withheld-site inverse distance squared | 0.0012420 | 0.0333120 | 4 / 4 |
| Withheld-site fitted spatial | 0.0014544 | 0.0334587 | 4 / 4 |
| Spatial-block fitted | 0.0040187 | 0.1382506 | 9 / 9 |
| Partial spatial-block fitted | 0.0077461 | 0.1402700 | 1 / 9 |

These are means on each row's **scored** support. The partial-block mean
therefore describes one successful unit, while eight failures remain in the
denominator column. The separate local analytical LOVE pollen row is an
in-sample diagnostic. The temporal no-change case has one synthetic unit per
target; its zero error is an example property, not temporal generalization.
No interval coverage was computed for these six protocols.

## Source and verification boundary

The six original score tables are retained byte-for-byte under
[tracked synthetic score sources](../../../data/synthetic/score_protocols/).
The [source manifest](../../../data/synthetic/score_protocol_source.json) binds
each table to its original SHA-256 and retains the historical 16-row reader
result, protocol identities and accounting. It also records the private archive
SHA-256 `8dd272c3bd93f8354045596b2b712a2a3670cd35ebd0b7332d0b001ee95c3cc6`
and the original report and binding-file SHA-256 digests as provenance receipts.
The [machine result](report.json) links each row to the original score
manifest and evidence digest. The private archive is retained separately as a
source witness; replay reads the governed tracked tables.

Our [producer](replay.py) independently sums the retained scored-unit MAEs
and counts refusals in the six original score tables, checks their byte hashes
and compares every row with the historical reader output. The current
installed authoritative reader rejects the historical spatial-block product
profile with `Profile, roles or numerical table differs`; this is a versioned
reader compatibility limit, not a claim that the historical score row is a
current accepted product. We keep the raw score arithmetic and original
reader result visible rather than changing current reader assertions to make
the old bundle pass.

The original data are synthetic. Vegetation fractions are supplied by the
fixture, not measured field observations. The pollen and vegetation results
answer different targets, and a low error in one protocol does not identify
an ecologically best model. The [current host challenge](../synthetic-host-challenge/README.md)
and [development selection](../synthetic-model-selection/README.md) have
their own prospective designs and are not replaced by this older archive.

To reproduce the row arithmetic, run from the repository root with an absent
output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/synthetic-protocol-metrics/replay.py \
  --source-manifest data/synthetic/score_protocol_source.json \
  --output artifacts/jobs/synthetic-protocol-metrics/replayed
```

Compare `scores.csv` and `report.json` with the governed files beside this
page. The original private archive is held outside the repository and is not
a public download.
