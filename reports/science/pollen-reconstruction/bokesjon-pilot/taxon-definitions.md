# KRAG taxon-definition follow-up

Official Neotoma metadata retrieved on 14 November 2026 supplies a family-parent
candidate for the three previously exact-unmapped sedge counts. The 30 cereal
counts still have no rye-compatible mapping. No mapping is applied: the
[source audit](result.json) at calculation commit
`916c9489de8fd4fcac24fcf973add288f7ea2c86` retains all **33 exact-unmapped
reported counts**.

The [acquisition manifest](../../../../data/neotoma/raw/bokesjon-core-sources/taxon-definitions/source.json)
pins ten unmodified official API responses, totalling 4,153 bytes, with retrieval
times, URLs, hashes, attribution and terms. The
[authored assessment](../../../../data/neotoma/raw/bokesjon-core-sources/taxon-definitions/assessment.json)
separates provider fields from scientific interpretation.

| Native taxon | Existing selected-window count | Official metadata and consequence |
| --- | ---: | --- |
| [427: Poaceae (Cerealia) undiff.](https://api.neotomadb.org/v2.0/data/taxa/427) | 3 | Parent chain 427 → 416 → 39691 → 417 (Poaceae). No rye-exclusion or calibrated cereal-group definition is supplied. |
| [1947: Poaceae (Cerealia-type)](https://api.neotomadb.org/v2.0/data/taxa/1947) | 27 | Parent chain 1947 → 39691 → 417. This is a distinct morphological-type concept; neither 427 nor 1947 is the other's parent. No compatible rye split follows. |
| [33953: Schoenoplectus lacustris subsp. lacustris-type](https://api.neotomadb.org/v2.0/data/taxa/33953) | 3 | Parent chain 33953 → 26933 → 40113 → 40110 → 74 (Cyperaceae). The leaf and Schoenoplectus-type are AQVP, aquatic vascular plants. Family ancestry supplies a candidate, while terrestrial-denominator and PPE/FSP eligibility remain unresolved. |

The [Neotoma taxonomy manual](https://neotoma-manual.readthedocs.io/en/latest/tables_taxa.html)
explains that morphological types can include indistinguishable taxa and that
HigherTaxonID represents ancestry. Its intended pollen-category exclusivity is
not an audit of this particular KRAG import. A family parent does not establish
that existing family counts are residual, or that the same parameter calibration
covers an aquatic pollen type. Higher-rank UPHE labels do not replace the leaf's
AQVP classification. Neither cereal response establishes equivalence to pooled
2020 Cerealia or rye-excluded 2022 Cerealia-t.

Attribute the Neotoma Paleoecology Database and the taxonomic references retained
in its responses: Stevens' Angiosperm Phylogeny Website, Euro+Med PlantBase and
the Flora of North America Editorial Committee. The existing count context is
the European Pollen Database KRAG source audit. The
[Neotoma V.2025 public-data policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
provides [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) terms with
source attribution. The assessment is project-authored; provider responses are
unchanged. No private workbook or lookup rows are reproduced.

<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** The retained official metadata establishes the stated
parent chains and ecological labels, including a Cyperaceae candidate for three
reported sedge counts.

**Unsupported claim.** An admitted cereal/rye split, terrestrial sedge denominator,
compatible full parameter profile, or completed forest/open/cereal reconstruction.

**Actual verification performed.** All ten response bodies were checked byte for
byte against their acquisition receipts, including lengths, SHA-256 hashes,
successful response status and taxon identities. Parent links, count accounting,
local document links and the unchanged frozen result identity were checked.
No new cohort outcomes were decoded and no model was executed.

**Remaining input or review.** A source-owned identification legend or exact
variable crosswalk must establish cereal and rye membership. Sedge use also
requires justified denominator, disjoint-count and PPE/FSP decisions. Resolvers:
source custodians and qualified palynology/parameter reviewers.

**Cause category.** assumption|comparability|data|qualified review

**Consequence.** Retain 30 unresolved cereal counts and three unapplied sedge
candidate counts in the frozen exact-unmapped disposition.

**Precise next acceptance route.** Record the scoped source/profile decisions,
independently check their counting and parameter compatibility, then bind them to
a separately identified execution before applying any mapping.

**Negative or refused result.** No new mapping, zero-fill, parameter replacement
or scientific admission; the frozen 916 calculation remains unchanged.

**Matched denominator.** Three previously exact-unmapped KRAG labels represent
33 reported counts in the existing 2700–3200 BP development window: 3 + 27
cereal counts and 3 sedge counts. Ten metadata bodies describe those labels and
their bounded parent chains; they add no pollen samples or counts.

Retained evidence: the acquisition manifest, exact response bodies, authored
assessment and existing source-audit result linked above. This metadata account
does not rerun or qualify the reconstruction.
<!-- scientific-verification-and-limits:end -->
