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

The official [SLU NFI calibration guide](https://www.slu.se/globalassets/slu.se/om-slu/organisation/institutioner/skoglig-resurshushallning/riksskogstaxeringen/dokument/dokument/info-data-for-calibration.pdf)
declares CC0 1.0 for the downloadable plot subset. It limits the data to
temporary forest plots from 2007–2025, excludes boundary plots, and explicitly
disallows deriving totals or mean values for a geographic area. A pinned copy
of that guide is retained locally with SHA-256
`793d90e287b2c686d0007f02497e12e8a72a47e5a45531918d9fc71d78499bc8`.
This resolves the stated reuse terms for the supplied plot subset; it does
not turn plot observations into regional vegetation cover.

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

## Source context for the nearest leads

The separate `bijux_pollenomics_dev.source_completion.empd2_nfi_provenance`
producer checks the official SQLite and the spatial report by SHA-256, then
retains source-native context and publication links for all 16 samples within
1 km. Eight have a linked publication. Their source age-uncertainty codes are
five `A`, three `B`, and eight literal `NULL`; eleven source age values are
missing or source text. The SQLite metadata table has no structured
collection-date column.

One record, `Nielsen_b4`, has a source note saying the surface sample was
collected in September 2013. Its **distance-selected** nearest NFI row is
427.12 m away and has survey year 2013. The note is a concrete lead for
source and timing review, not an authenticated match: the pollen is lake
sediment, the small forest plot has different spatial support, and the
EMPD2–Neotoma identity flag is unresolved. The other 15 leads have no
collection-time cue in this source note field. The candidate-only dossier is
retained as a local artifact, SHA-256
`bcab3834980f6934143f3a2bf4e2a0155bf3c7024850989de4f0f28f89584c31`.
It excludes the structured `vegdescription` field, but retains unstructured
source notes for manual review; it is not a model-training input.
No vegetation–pollen pair is admitted from it.
The [16-lead reviewer sheet](empd2-nfi-review.md) is generated from the
pinned spatial and source dossiers and the official NFI guide. It preserves
the source context and nearest-row facts needed for qualified review without
promoting any lead into a measured vegetation reference.

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
