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
[source register](../../../../../reports/needed/source-requests.csv) asks for
the native determination and its source-specific pollen concept, lookup/use
authority, and a qualified decision on the proposed Ericaceae aggregation.
The matching [review question](../../../../../reports/needed/scientific-review.csv) asks whether that
botanical synonym supports this native pollen concept on the stated population.
Its decision is `not_received`; the reviewer is unassigned. An answer for the
two Abborrtjärnen counts would not automatically approve the other Swedish or
Norwegian occurrences. A returned scoped decision must precede any change to
the mapping, denominator or affected prediction.
