# Neotoma concepts against the LandClim author taxonomy

The [candidate ledger](report.json) joins the 1,006 source-pollen concepts in the
[Neotoma priority](../taxon-priority/README.md) to exact source-name rows in the
LandClim II author taxonomy lookup. It retains all 1,006 concepts, their native
identities, country counts, source units, qualifier markers and review state.
The three consumed input files and SHA-256 identities are recorded in the ledger.
The ledger SHA-256 is
`5727ed9f735436aa6c806368be0bf1f39402c4f84575cb94562e8c879b6bb057`.

| Literal name status | Concepts | Count observations |
| --- | ---: | ---: |
| Author target | 136 | 150,493 |
| Author excluded target | 668 | 71,836 |
| No exact lookup name | 202 | 5,994 |

Among the author-target leads, 126 native `NISP` concept rows sum to 9,242,443
counts and ten `NISP digitized` rows sum to 12,122. The units are separate. The
table above counts observations, not pollen grains. It covers the priority's
228,323 observations, not every observation or concept in Neotoma. Source names
that land on the author's `zz.do not use` or `aage.cal.BP` labels are explicitly
excluded from the 31-target author set.

Every selected concept remains `needs_discussion`. Literal name correspondence
does not establish ecological identity, pollen denominator, PPE or fall-speed
applicability, source rights or LRA eligibility. No concept mapping or LRA sample
is admitted. A qualified reviewer can use the retained concept IDs and country
counts to work through the high-mass author-target leads first, while preserving
ambiguous and unmatched rows in the denominator.

## Cereal concept questions

The user's two cited Neotoma IDs occur in the retained 1,006-concept ledger.
These counts are the priority-screen observations, not every Neotoma occurrence:

| Native ID and label | Priority observations | Native NISP | Literal author lookup | Decision state |
| --- | ---: | ---: | --- | --- |
| `3924` `Hordeum/Secale` | 2, both SE | 2, both SE | `Cerealia-t` | Combined taxon; cannot be narrowed to `Secale` from this name. |
| `969` `Triticum` | 153: FI 3, NO 2, SE 148 | 1,354: FI 4, NO 2, SE 1,348 | `Cerealia-t` | Literal author-target candidate; broader cereal aggregation still needs review. |

Both rows retain `needs_discussion` and `scientific_admission_allowed: false`.
The current author lookup has a broad cereal target; it does not supply a
qualified species-level `Secale` determination for a combined pollen type.
Reassigning either row would change the declared taxon axis and requires a
source-specific review, not a text replacement in the model.

Replay against the retained author reference, writing a disposable copy under
`artifacts/`, then compare `report.json` byte-for-byte with the governed result:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.neotoma_author_taxonomy_candidates \
  --repository . \
  --author-source-root /path/to/landclim/author-reference \
  --output artifacts/neotoma-author-taxonomy-candidates/replay
```

The [producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma_author_taxonomy_candidates.py)
checks the author lookup's pinned identity and source schema, source review and
priority identities, distinct concept IDs, review status, source units and country
accounting. The focused regression checks the native/digitized distinction and
refuses a changed review decision.

## Rhododendron synonym review

The retained native concept `4431`, `Rhododendron tomentosum`, is unmatched by
literal name. The [candidate ledger](report.json) contains 31 priority-screen
observations totaling 34 native NISP: Sweden 30 observations / 33 counts and
Norway one observation / one count. These are distinct from the two counts in
Abborrtjärnen dataset `19913`, site `13338`, across the common Swedish bins in
the [author-taxonomy mass screen](../author-taxonomy-mass/report.json).

The Royal Botanic Gardens, Kew [accepted-name account](https://powo.science.kew.org/taxon/961622-1), consulted 2 October 2026, places
*Rhododendron tomentosum* Harmaja in Ericaceae and lists *Ledum palustre* L. as
a homotypic synonym. Kew's [Ledum account](https://powo.science.kew.org/taxon/urn:lsid:ipni.org:names:279380-2) independently
links the latter name to the accepted species and records an alternative older
taxonomy. The botanical name relation is supported; a source pollen-type
determination still needs a palynologist's judgment. Attribute these botanical
accounts to Plants of the World Online, Royal Botanic Gardens, Kew, drawing on
the 2026 IPNI/WCVP names and taxonomic backbone; its displayed licence is
[CC BY 3.0](https://creativecommons.org/licenses/by/3.0/).

The original author lookup at SHA-256
`3a745f9b7606e5d0b59feaba2683b930c8d3990e4810f8217b69160a29a1b507`
contains `Ledum palustre` → `Ericaceae`, but no exact `Rhododendron tomentosum`
row. This offers a specific synonym-based candidate for review. It does not
change the literal ledger, source identification, author exclusion rules,
count denominator, parameter applicability or use rights. Abborrtjärnen's
account remains 88,004 native NISP = 86,691 author-assigned + 1,311 excluded +
two unmapped. All 34 screened counts remain unmapped and no LRA sample is
admitted by this review preparation.

The unsent request `rhododendron-pollen-synonym` in the
[source register](https://github.com/bijux/bijux-pollenomics/blob/main/reports/needed/source-requests.csv) asks for
the native determination and its source-specific pollen concept, lookup/use
authority, and a qualified decision on the proposed Ericaceae aggregation.
The matching [review question](https://github.com/bijux/bijux-pollenomics/blob/main/reports/needed/scientific-review.csv) asks whether that
botanical synonym supports this native pollen concept on the stated population.
Its decision is `not_received`; the reviewer is unassigned. An answer for the
two Abborrtjärnen counts would not automatically approve the other Swedish or
Norwegian occurrences. A returned scoped decision must precede any change to
the mapping, denominator or affected prediction.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The literal author-lookup ledger preserves 1,006 candidate concepts and their target, excluded or unmatched status.

**Unsupported claim.** Botanical synonym/name equality does not approve pollen-type identity or generalize a scoped two-count decision to 34 occurrences.

**Actual verification performed.** Read the concept ledger, status totals and source-unit separation alongside the authored cereal/Rhododendron questions; no remapping or botanical lookup rerun.

**Remaining input or review.** Qualified source-specific pollen concept decisions, including combined cereal and Rhododendron synonym applicability, remain not_received.

**Cause category.** Taxonomic candidates require scoped biological authority.

**Consequence.** All 1,006 concepts retain needs_discussion and author-excluded/unmatched mass stays in the denominator.

**Precise next acceptance route.** Return a qualified decision bound to native concept/population, lookup/parameter revision and rights before changing mappings.

**Negative or refused result.** 668 excluded and 202 unmatched concepts remain; Hordeum/Secale cannot be narrowed toSecale; Rhododendron is still literal-unmatched.

**Matched denominator.** 1,006 concepts/228,323 priority observations: 136 author-target, 668 excluded, 202 unmatched; native NISP and NISP digitized are separate.

Qualified authored reader SHA-256: `3ae8353a8ac1c3d79c30290752677854f644a05fd5d9aefd00cd8a60989724c0`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/author-taxonomy-candidates/report.json](report.json) (SHA-256 `5727ed9f735436aa6c806368be0bf1f39402c4f84575cb94562e8c879b6bb057`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/taxon-priority/priority.json](../taxon-priority/priority.json) (SHA-256 `d2e3b1947c0cb698a6a2ab48aa6be3a85680b495f596dda1ec50cd411c17924f`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
