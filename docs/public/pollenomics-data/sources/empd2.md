---
title: EMPD2 reference candidate
audience: reader
type: explanation
status: canonical
owner: bijux-pollenomics-docs
last_reviewed: 2026-09-21
---

# EMPD2 reference candidate

EMPD2 is a candidate pollen reference source for the Nordic study. It is not
one of the nine contracted source families, and none of its rows is currently
admitted to LRA reconstruction, model tuning, or held-out scoring. The source
SQLite file is held in local artifact custody, outside Git. Its published
[PANGAEA deposit](https://doi.pangaea.de/10.1594/PANGAEA.909130) is marked
CC BY 4.0; reuse still needs source attribution and review of the intended join.

The pinned SQLite file is 21,327,872 bytes with SHA-256
`5634e85d922ee0741c41a77d081010c9cc1c113966b283bc52e2051a9d3722e2`.
The repository's `bijux_pollenomics_dev.source_completion.empd2` producer
checks that hash, reads the database without writing it, and preserves a
sample-level reason for every failed count screen. It also binds the separate
EMPD2–Neotoma candidate-identity review by hash. Its results for this source
are:

| Source country | Metadata samples | Pollen count rows | Mechanical count candidates | Unresolved Neotoma overlap leads |
| --- | ---: | ---: | ---: | ---: |
| Sweden | 132 | 3,379 | 131 | 21 |
| Denmark | 20 | 968 | 20 | 0 |
| Norway | 622 | 19,774 | 622 | 66 |
| Finland | 141 | 3,040 | 141 | 25 |
| **Total** | **915** | **27,161** | **914** | **112** |

The mechanical rule requires at least one count row, all rows finite
nonnegative integers, at least one positive row, and source `ispercent=0` and
`isdigitised=0`. One Swedish source count is **49.5** and is retained as a
fractional value with a refusal reason. Mechanical candidates are a screening
denominator, not admitted samples. The 112 overlap leads are unresolved site
or dataset relationships; none establishes that the physical pollen sample is
identical or independent across databases. They must be resolved or grouped
before a split can be frozen.

## Swedish plot proximity screen

The repository's `bijux_pollenomics_dev.source_completion.empd2_nfi` producer
compares the 132 Swedish EMPD2 candidate coordinates with 43,892 NFI
plot-year rows (6,018 tract/plot keys). It checks the NFI workbook and its
ReadMe-backed SWEREF99TM declaration by hash, transforms only plot geometry,
and measures unrounded WGS84 inverse-geodesic distance. The final tree
measurement columns are not selected, displayed or scored, though the XLSX
parser necessarily streams the whole worksheet XML. The thresholds below are
descriptive source leads, not reviewed ecological pairing distances.

| Maximum distance | All EMPD2 samples with an NFI row | Mechanical count candidates with an NFI row | All NFI row/sample pairs | Count-candidate row/sample pairs |
| --- | ---: | ---: | ---: | ---: |
| 1 km | 16 / 132 | 16 / 131 | 53 | 53 |
| 5 km | 66 / 132 | 65 / 131 | 696 | 681 |
| 10 km | 96 / 132 | 95 / 131 | 2,846 | 2,821 |

Five of the 16 samples within 1 km carry unresolved EMPD2–Neotoma identity
flags. The one Swedish sample with a fractional count is retained in the
all-metadata 5 and 10 km totals but excluded from the mechanical count
candidate totals. Mechanical count candidacy is still not scientific
admission. Repeated NFI years and nearby plots make row-pair totals larger
than the number of distinct pollen samples. The nearest NFI row is chosen
only by distance; its inventory year does not date or match the pollen
sample. The EMPD2 position datum and uncertainty remain unreviewed. The
source has no explicit collection-year field, and the source age/uncertainty
codes do not establish matching survey support. Spatial proximity also does
not prove that a small NFI forest plot represents a pollen basin or regional
vegetation footprint. The report is a candidate-only local source artifact,
SHA-256 `5d35aed59cb5e3b49582976264837fab1c8d4ffa3dc1937e73bf2f04f32e2c66`;
**zero independent vegetation–pollen pairs are admitted**.

Source `agebp` is preserved exactly, including missing and literal `NULL`
values; it is not converted to an exact collection year. This SQLite release
does not expose a collection-year field. Taxa/PPE, basin support, chronology,
source identity, and compatible count units still require review. EMPD2's
vegetation descriptions and mapped ecosystem classes are contextual labels,
not independently measured vegetation cover. Thus this candidate contributes
**zero admitted measured vegetation references** and no Nordic accuracy score.

The producer's machine report records the 915 source-native sample rows,
country denominators, invalid count values, unresolved overlap flags, source
hash, and refusal codes. It can be rerun on the pinned local SQLite file with
the pinned 112-row overlap review; both inputs must match their recorded
SHA-256 hashes. The next source decision is sample-level identity and timing
review, followed by taxa/PPE, basin, rights-for-join and scientific admission.
