# Dated Neotoma taxonomy reference

The [reference archive](../../../../../data/neotoma/taxonomy-reference/a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0/archive/manifest.json) retains the exact
three official Taxonomy-Viewer projections from commit
`f72baeb6dbf7a166a5421c80b2873f159e1388f3`. It supplies reusable native-ID, name,
parent and classification-reference lookup, with the original positional synonym
assertions. It is global Neotoma vocabulary, not a Swedish flora, pollen panel or
set of observations.

The snapshot contains **59,201 native-ID vocabulary entries** and **59,201 matching metadata IDs**,
with **2,916 synonym assertions in 2,573 groups**. These retained source counts
are conserved by unchanged original bytes. All 29 self parents remain literal;
the repeated synonym triple retains its two dated assertions and positions.
Native “valid”/“invalid” labels describe the source assertions, not an adopted
biological synonymy or pollen-to-PPE mapping.

## Separate source dates and attribution

- Snapshot generation: `2026-11-02T08:54:54+00:00`.
- Git commit: `2026-11-02T08:54:59Z`.
- Retained intake: 17 November 2026; exact per-file intervals are in
  [provenance](../../../../../data/neotoma/taxonomy-reference/a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0/archive/provenance.json).

Native record creation, modification and validation dates remain database
metadata. They are not sample ages, chronology support or geological validity
periods. The source does not acquire a new refresh epoch when this archive is
published or queried.

The source is the [official NeotomaDB viewer repository](https://github.com/NeotomaDB/Taxonomy-Viewer/tree/f72baeb6dbf7a166a5421c80b2873f159e1388f3).
Attribution to Neotoma Paleoecology Database contributors and the
[database data-use policy](https://www.neotomadb.org/data/data-use-and-embargo-policy)
reference are retained. Source-data attribution is separate from upstream
viewer-program licensing; no viewer program code is copied or executed here.
The archive does not assign new rights to constituent source material.

Three original JSON files total **44,849,667 bytes**. The Git commit/root/data
metadata and a portable transport projection accompany them. Raw transport
records stay outside this account: workstation filenames and local IP/port are
omitted, while the raw-record SHA and genuine URL, HTTP/TLS/redirect, byte,
timing and intake facts remain. The projection is not the original curl record
or a native Neotoma API receipt.

The retained root-tree API document names its requested commit selector. Its
entries reconstruct canonical tree `ea8705f403a82eca7ebefd8fce1353fbf3ba95d7`,
which is bound by the retained commit metadata. Data-tree and original blob
identities are checked separately; the original API metadata bytes are preserved.
This is pinned metadata/tree verification, not signed-commit or live API proof.

## Exactly the recorded 182 leads

The [contrast](../../../../../data/neotoma/taxonomy-reference/a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0/frontier/frontier-contrast.json) binds the
[recorded chain manifest](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/chains/0e7e37196a8eabc771b336bec25f981bfc6a291148dc519b9ce6c4f8212e2064/manifest.json)
`0e7e37196a8eabc771b336bec25f981bfc6a291148dc519b9ce6c4f8212e2064`:

| Stored lead kind | Targets | Dated reference outcome |
| --- | ---: | --- |
| Taxon | 151 | 151 native-ID records available |
| Classification-reference publication | 31 | 31 targets with citation text |
| Total | 182 | No reference misses in this fixed selection |

Every target and source position survives. A successful ID join does not
qualify a current endpoint response or establish current taxonomy, biological
meaning or permission. Publication pointers, publication fallback text and
citation text remain separate; all literal variants retain their source taxon
links. Classification citations are not automatically dataset-primary papers.

This dated lookup does not discharge further parent/reference capture duties,
materialize the [separate twelve-response continuation](../../../source-integrity/neotoma/ancestry-continuation/README.md),
or establish a revised unresolved-frontier total. It does not resolve a source
status question such as the continuation's literal Garryidae status: this
reference has no added status authority. No reference rows are inserted into
the Atlas or its dataset/site/numerical counters.

## Maintained lookup and reproducible evidence

The [source guide](../../../../../docs/public/pollenomics-data/sources/neotoma-taxonomy-reference.md)
describes the maintained archive, selected lookup and frontier-contrast owners.
For example, from an environment containing the source CLI, a single batch can
request explicit IDs without a provider call:

```sh
python -m bijux_pollenomics.collection.sources.neotoma.ancillary_store.taxonomy_reference.command_line lookup \
  --archive data/neotoma/taxonomy-reference/a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0/archive \
  --manifest-sha256 a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0 \
  --taxon-id 9654 --taxon-id 9606
```

This is a usage example, not an installed-distribution CLI qualification claim.
The command authenticates the three retained projections once for the selected
batch. Rebuilding the saved contrast needs this archive and the published
recorded chain metadata, not original cohort stores, a baseline replay or new
GETs. Recreating the original archive publication would additionally require
its retained raw intake transport records; the public portable projection is
not a substitute for those records. An inherited delta without explicit frontier parts is refused rather than
interpreted as zero remaining leads.

The actual maintained API publication completed with observed process exit 0,
a qualified closed receipt and an empty failure diagnostic. The producer
revision was `ba8d412657921253e6e0da78488170879ddd0ccf`; the upstream reference revision
and recorded chain above are separate identities. It performed zero GETs,
model calls or native-baseline replays. Closed inspection checked all nine
product hashes, three original Git blobs, canonical metadata trees, 182 unique
rows/source positions and the explicit non-admission flags. Promotion copied
those exact nine files (**45,355,939 bytes**); it did not reacquire or rederive
source data. [Verification](verification.json) provides the relative member pins and scoped account.

The reported 182,872,269-byte payload/readback reservation and 59 charged leaf
opens are conservative accounting, not physical I/O or all descriptor opens.
Software reads are recorded separately. Those resource figures establish no
scientific accuracy, global vocabulary completeness, regional occurrence,
chronology, native source status or current-use permission.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Exact attributed dated reference originals and an ID/context contrast of the 182 explicit recorded leads: 151 taxa and 31 classification-reference targets.

**Unsupported claim.** Live native detail/current permission, biological synonymy/PPE mapping, Swedish occurrence, sample chronology, dataset-primary citation or graph/programme completion.

**Actual verification performed.** Maintained archive and contrast API execution; nine product SHA-256 hashes, original Git blob IDs, canonical Git trees and 182 target IDs and positions checked; exact staged Git bytes preserved.

**Remaining input or review.** Source interpretation, current access and any later chain or analytical use require their own evidence. Resolver: Source-data and taxonomic/method reviewers. Reopen when: A changed reference or capture epoch, explicit mapping proposal or separately qualified successor chain.

**Cause category.** Dated source scope; source interpretation; current access.

**Consequence.** Keep all unknowns and literal variants; neither a lookup match nor a source database date becomes a scientific or current-access decision.

**Precise next acceptance route.** Use the maintained explicit-ID reader with this manifest pin; separately qualify current source duties and any biological/parameter or later graph claim.

**Negative or refused result.** No misses among these 182 IDs does not establish global/current coverage. An initial commit-selector metadata integrity attempt refused before original-table reads; no failed output was adopted.

**Matched denominator.** 182 stored context leads only: 151 taxon plus 31 publication IDs. The 59,201 global vocabulary rows and 2,916 synonym assertions are separate source populations, not observations.

Retained evidence: [reports/science/source-relations/neotoma/taxonomy-reference/verification.json](verification.json), [data/neotoma/taxonomy-reference/a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0/archive/manifest.json](../../../../../data/neotoma/taxonomy-reference/a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0/archive/manifest.json), [data/neotoma/taxonomy-reference/a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0/frontier/frontier-contrast.json](../../../../../data/neotoma/taxonomy-reference/a2c3003d7c71f9f8e69cba4af95c58de97246d7a6041589067c8277ef0ab26f0/frontier/frontier-contrast.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
