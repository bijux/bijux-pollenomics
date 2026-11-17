# Further recorded Neotoma taxon and classification references

Seven additional taxon details and five taxon-reference publications were
captured from Neotoma on 17 November 2026. These twelve responses continue
source questions exposed by the [preceding recorded ancestry](../ancestry-captures/README.md).
They supply inspectable names, literal parent IDs and classification references
for reviewing the Bökesjön/Krageholm taxon panel. They do not determine which
pollen morphotypes share a vegetation group or PPE parameter.

The new [capture manifest](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/capture-manifest.json)
and its responses are separate from the normalized chain and the
[recorded source atlas](../recorded-source-atlas/README.md). That Atlas still
contains the preceding selection of **16** targets from chain `0e7e371…`.
These twelve responses now form the separately qualified
[normalized successor chain](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/chains/cf525a56c96f57f4aab43894326500b8ca080800544a3e0fea288296b393db0d/manifest.json)
`cf525a56…`, whose frozen frontier contains **172 unresolved leads**. They have
not been added to the Atlas. The earlier 16-target Atlas and the dated-reference
comparison against the preceding chain's fixed 182-lead set retain their own
epochs. A smaller frontier is not complete graph coverage: newly received records
can themselves expose further parent or citation leads.

## Literal taxon fields

The table transcribes the received fields. Names, status and taxonomic placement
remain source assertions at their individual response epochs.

| Native taxon ID | Recorded name | Parent ID | Taxon-reference publication ID | Recorded status |
| ---: | --- | ---: | ---: | --- |
| [9606](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/taxon-9606-current-attempt-1.body) | Rosidae | 9652 | 3711 | extant |
| [9653](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/taxon-9653-current-attempt-1.body) | Gunneridae | 2132 | 3711 | extant |
| [9654](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/taxon-9654-current-attempt-1.body) | Garryidae | 9655 | 3711 | extinct |
| [9657](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/taxon-9657-current-attempt-1.body) | Campanulidae | 9655 | 3711 | extant |
| [15532](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/taxon-15532-current-attempt-1.body) | Nartheciidae | 2131 | 3711 | extant |
| [9959](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/taxon-9959-current-attempt-1.body) | Carduoideae | 409 | 16423 | extant |
| [32874](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/taxon-32874-current-attempt-1.body) | Lamiaceae subf. Nepetoideae | 460 | 1490 | extant |

**Source-quality question:** taxon `9654` reports `status="extinct"` for
Garryidae. That literal value is preserved. Its biological interpretation needs
source clarification; it is neither silently changed to `extant` nor used as an
automatic pollen exclusion. Successful parsing establishes a native source
record, not an ecological or taxon-panel decision.

## Captured classification references

The separately received publication titles are:

- [10028: Classification of Compositae](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/publication-10028-current-attempt-1.body).
- [10102: An outline of a classification scheme for extant flowering plants](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/publication-10102-current-attempt-1.body).
- [7367: Anthemideae](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/publication-7367-current-attempt-1.body).
- [9800: Urticalean rosids: circumscription, rosid ancestry, and phylogenetics based on BBCL, TRNL-F, and NDHF sequences](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/publication-9800-current-attempt-1.body).
- [10136: What is the taxonomic status of Polygonella? Evidence of floral morphology](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/publication-10136-current-attempt-1.body).

These are classification references, not automatically the pollen datasets'
primary publications. The received dataset-association tuples contain null
site, dataset and primary fields; null stays unknown. Cite Neotoma, constituent
databases and original investigators, with the appropriate dataset publications
when reusing source data.

## Exact capture and verification

The immutable directory contains **26 files / 83,586 bytes**: twelve unchanged
HTTP bodies (**9,457 bytes**), twelve receipts, a request plan and the manifest.
The manifest SHA-256 is
`244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c`.
[Verification](verification.json) supplies all relative member hashes and the
source epoch; restoring these files does not repeat provider requests.

The maintained capture at [source revision `df54b2d`](https://github.com/bijux/bijux-pollenomics/commit/df54b2de1ba76de3edb2fabe7b6bc733e590bb85)
completed twelve single-attempt GETs with verified TLS and HTTP 200. Fresh native
qualification accepted all twelve details. Its recorded interval was
1,930.385 seconds, including one 1,811.187-second native-baseline qualification;
the nested intervals are not additive. The closed result retained an empty
failure diagnostic and closed source lease. Independent inspection checked
all product hashes, issued order, body/receipt/native-ID correspondence,
recorded root ownership and software origins without replaying that baseline.
Canonical promotion copied exact bytes and made no requests or derivation.

## Normalized continuation

The successor retains the capture above and its explicit parent chain
`0e7e37196a8eabc771b336bec25f981bfc6a291148dc519b9ce6c4f8212e2064`,
with baseline `84a831c05c7d018392293747925a4229faf4be935a1552ef6bdbf4587d1d0662`.
The five new chain files total **467,732 bytes**; their manifest SHA-256 is
`cf525a56c96f57f4aab43894326500b8ca080800544a3e0fea288296b393db0d`.
The existing 26 capture files remain byte-identical. The saved 31-file bundle
therefore totals **551,318 bytes**, without duplicating capture bytes here.

One maintained normalization at the same `df54b2d…` source revision completed
one fresh native-baseline qualification and one derivation, with source checks
at both staged and final publication. It made **zero new GETs** and closed its
source lease. The observed process exited 0 after **2,409.080 seconds**, charging
109,624 source descriptor opens and 2,489,475,599 conservative source bytes;
that byte reservation is not measured physical I/O. Closed controls contain no
unexpected denials, forbidden events or fatal diagnostic bytes. Previously
retained inputs were isolated with unchanged content hashes rather than adopting
changed live-worktree attachments or reusing an expired permission lease.

The manifest's summary records 2,355 known taxon nodes, 175 publication nodes,
2,763 known entity results and 4,422 literal field occurrences. These are distinct
source-graph units, not pollen observations, sites or biological groups. Its
**28 historical HTTP requests** combine the preceding 16 and later 12 captures;
they are not requests made by this normalization. The new parts contain 13 taxon
rows, eight publication rows, 14 edge rows and the **172-row unresolved frontier**.
They do not replace the baseline or parent chain's explicit resolver obligations.

Garryidae's recorded status and unknown publication dataset associations remain
as above. Successful normalization does not depend on resolving their biological
interpretation, and it does not resolve it. The selected metadata reader's
`current_roles_revalidated`, `native_source_fields_revalidated` and
`GET_authorized` remain false: an anchored stored view does not authorize future
source use. The separately published Atlas still selects the preceding 16 targets;
no Atlas refresh or new ecological/PPE mapping was performed.

This is source-context progress. Counts, pollen denominators, chronology,
geometry, biological equivalence, parameter choice and independent vegetation
validation retain their separate requirements. The
[source workflow](../../../../../docs/public/pollenomics-data/sources/neotoma-ancillary-resources.md#collect-an-explicit-ancestry-frontier)
describes the explicit qualification and acquisition boundaries.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Seven taxon details and five classification-reference details at their recorded epochs, plus one separately qualified normalized successor with 172 unresolved frontier leads.

**Unsupported claim.** Complete graph coverage, refreshed Atlas membership, biological equivalence, PPE selection, current permission or scientific admission.

**Actual verification performed.** Closed capture and five normalized chain-file hashes; one fresh baseline and derivation; stage/final source validation; observed process exit 0; zero new GETs and a closed lease.

**Remaining input or review.** Source interpretation and unresolved graph leads remain open; the Atlas and dated-reference comparison retain their earlier epochs. Resolver: Source reader and taxonomic/method reviewer. Reopen when: A changed source epoch, source clarification or separately qualified graph/Atlas publication.

**Cause category.** Native source quality, graph coverage and scientific eligibility have distinct requirements.

**Consequence.** Use literal source fields and the explicit normalized chain without promoting unknown associations or changing the existing Atlas denominator.

**Precise next acceptance route.** Resolve the relevant source leads before claiming broader graph coverage. Resolve native status interpretation and applicable mapping before ecological use. Any future source access needs fresh permission checks.

**Negative or refused result.** Taxon 9654 reports extinct; biological interpretation unresolved. The successor retains 172 unresolved leads; no complete graph or Atlas update is claimed.

**Matched denominator.** Twelve captured details: seven taxa and five classification references; 26 unchanged capture files / 83,586 bytes plus five normalized chain files / 467,732 bytes. The cumulative 28 HTTP requests are historical; this normalization issued zero.

Retained evidence: [reports/science/source-integrity/neotoma/ancestry-continuation/verification.json](verification.json), [data/neotoma/ancillary-resources/taxon-ancestry/chains/cf525a56c96f57f4aab43894326500b8ca080800544a3e0fea288296b393db0d/manifest.json](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/chains/cf525a56c96f57f4aab43894326500b8ca080800544a3e0fea288296b393db0d/manifest.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
