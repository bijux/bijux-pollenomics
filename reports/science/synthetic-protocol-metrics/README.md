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


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Six historical synthetic protocol tables have exact scored-row arithmetic and failure counts.

**Unsupported claim.** Current-reader acceptance of old spatial-block profile or real vegetation skill.

**Actual verification performed.** Retained byte-bound source tables and row-summing producer are reported; index did not rerun.

**Remaining input or review.** Six historical synthetic score tables have closed row arithmetic, but the current reader rejects an old spatial-block product profile; protocol supports differ and eight partial-block failures forbid a pooled accuracy claim. Resolver: Reader/profile owner and qualified protocol reviewer Reopen when: A versioned historical reader/profile is authenticated for its own product or a new current-profile run is separately identified.

**Cause category.** algorithm/numerical|comparability

**Consequence.** Do not pool protocol supports or treat one successful partial-block row as nine attempts succeeded.

**Precise next acceptance route.** A versioned historical reader/profile is authenticated for its own product or a new current-profile run is separately identified. Then update reports/science/model-use.md.

**Negative or refused result.** Eight partial-spatial-block failures per target; current reader refuses historical profile/roles/numerical table.

**Matched denominator.** 16 historical score rows; 39 requested and 31 scored units per target across heterogeneous protocols.

Retained evidence: [reports/science/synthetic-protocol-metrics/report.json](report.json), [reports/science/synthetic-protocol-metrics/scores.csv](scores.csv).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-claim-semantic-sha256: 09498b5976ba6db8a22908d90bad69ea03c47f831325d00164355bb9c112a83c -->
<!-- scientific-authored-source-sha256: 1e0d333000f3ac9ece34ebf1a773b5a510ac8f1c45f28e96b9096c38b189e348 -->
<!-- scientific-verification-and-limits:end -->
