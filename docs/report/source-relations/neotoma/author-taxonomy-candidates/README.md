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

Replay against the retained author reference, writing a disposable copy under
`artifacts/`, then compare `report.json` byte-for-byte with the governed result:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.neotoma_author_taxonomy_candidates \
  --repository . \
  --author-source-root /path/to/landclim/author-reference \
  --output artifacts/neotoma-author-taxonomy-candidates/replay
```

The [producer](../../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma_author_taxonomy_candidates.py)
checks the author lookup's pinned identity and source schema, source review and
priority identities, distinct concept IDs, review status, source units and country
accounting. The focused regression checks the native/digitized distinction and
refuses a changed review decision.
