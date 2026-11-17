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
These twelve new responses have **not** been materialized into a successor chain
or added to the Atlas. No revised unresolved-frontier count is established:
newly received records can themselves expose further parent or citation leads.

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

This is source-context progress. Counts, pollen denominators, chronology,
geometry, biological equivalence, parameter choice and independent vegetation
validation retain their separate requirements. The
[source workflow](../../../../../docs/public/pollenomics-data/sources/neotoma-ancillary-resources.md#collect-an-explicit-ancestry-frontier)
describes the explicit qualification and acquisition boundaries.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Seven taxon details and five classification-reference details captured and qualified at their recorded source epochs.

**Unsupported claim.** A normalized successor chain, revised frontier count, inclusion in the Atlas, biological equivalence, PPE selection or scientific admission.

**Actual verification performed.** Closed26-file hashes, twelve issued requests and receipts, verified TLS/HTTP200, literal native IDs/fields, recorded root duties and source software pins.

**Remaining input or review.** Source interpretation and a separately qualified successor derivation remain open. Resolver: Source reader and taxonomic/method reviewer. Reopen when: A source clarification, changed capture epoch or separately qualified successor chain.

**Cause category.** Native source quality, graph normalization and scientific eligibility have different owners.

**Consequence.** Inspect literal source fields while retaining unknown associations and the preceding Atlas/chain epoch.

**Precise next acceptance route.** Clarify the native status question and qualify any successor chain before claiming updated graph coverage or scientific use.

**Negative or refused result.** Taxon9654 reports extinct; biological interpretation unresolved. No successor-frontier or Atlas-update result is claimed.

**Matched denominator.** Twelve details: seven taxa and five classification references; 26 files / 83,586 bytes, including 9,457 HTTP body bytes.

Retained evidence: [reports/science/source-integrity/neotoma/ancestry-continuation/verification.json](verification.json), [data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/capture-manifest.json](../../../../../data/neotoma/ancillary-resources/taxon-ancestry/captures/244769f271142c2f11d6f7cd11874d2fa8df6e5328e45ba6ff3851e6a06a402c/capture-manifest.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
