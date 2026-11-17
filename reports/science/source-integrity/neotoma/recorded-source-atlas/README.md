# Recorded Neotoma source atlas

This portable [source atlas](atlas/index.html) brings together the recorded
metadata for **1,258 dataset identities and 527 sites**, five supporting source
archives, and a sixth archive containing **16 selected ancestry targets**.
It lets a reader follow native identifiers and literal parent or citation links
without opening the original pollen responses or running a reconstruction.

The selected projection contains 13 taxon targets and three taxon-reference
publication targets. It exposes their native IDs, recorded fields and source
epochs; it does not supply native taxon names or publication titles. The
[captured-detail account](../ancestry-captures/README.md) separately describes
the received names and citations, 26 literal outgoing fields and the frozen
182-lead unresolved frontier. Neither view establishes biological synonymy,
pollen-morphotype equivalence, forest/open-land classes or applicable PPE.

## Inspect the recorded metadata

Keep the complete `atlas/` directory together. Its HTML, indexed metadata,
scripts, styles and images are separate files; copying only `index.html` is
insufficient. Open that index from a local checkout to inspect the snapshot.
The exact snapshot's browser qualification is **pending**; completed static
publication and transport validation do not establish working interactions or
downloads. The [verification record](verification.json) keeps that distinction
explicit.

The intended reading route is **Neotoma source resources → Metadata population
→ Supporting metadata entries → Search source metadata**. Search for a literal
target key such as `taxon-327`, then inspect its recorded metadata and source
identities. These interface labels describe the existing reader; this account
does not yet claim they were exercised on this snapshot.

The metadata route offers no ancestry entity-body download or acquisition
authority. Source-resource download availability is a separate route and is not
qualified by this publication. Do not interpret a blocked route or missing
field as a zero, an absent source record or an admitted model input.

## Keep the populations and epochs separate

| Recorded population | Count | Meaning |
| --- | ---: | --- |
| Dataset identities / metadata sites | 1,258 / 527 | Separate source discovery population |
| Current and DOI-frozen version slots | 2,516 | Recorded version metadata, not interchangeable observations |
| Facet slots | 10,064 | Eight declared endpoint slots per dataset identity |
| Ancillary observations / linked occurrences | 12,799 / 105,018 | Recorded source-metadata populations |
| Supporting archives / entries | 6 / 531 | Five existing archives with 515 entries, plus 16 selected targets |

This source-only view leaves scientific countries, layers and points at zero.
It does not replace the original 200-site source surface or establish membership
in the historical 193-site published Atlas. It does not choose counts, a pollen
denominator, chronology, basin geometry, uncertainty law or permitted scientific
use. Original and current context, capture and rendering epochs remain distinct.

The selected archive is pinned to chain
`0e7e37196a8eabc771b336bec25f981bfc6a291148dc519b9ce6c4f8212e2064`,
with its separate baseline resolver and preceding capture. Its selected index
has an independent digest; that digest is not the source-chain identity.
The archive reports `SELECTED_RECORDED_TARGETS_ONLY`: current roles and native
source fields were not revalidated, no native entity body was opened, GET is
not authorized, and scientific admission is not asserted.

## Verify and reuse the portable snapshot

Receive the repository at an independently trusted Git revision. The adjacent
verification record pins every relative file in the 104-file, 11,975,836-byte
`atlas/` tree. With the host SDK installed, run this from the repository root:

```python
from hashlib import sha256
import json
from pathlib import Path

from bijux_pollenomics.core.filesystem import BoundedInputTree

account = Path("reports/science/source-integrity/neotoma/recorded-source-atlas").absolute()
checks = json.loads((account / "verification.json").read_text())
snapshot = account / "atlas"
pins = checks["snapshot"]["members"]
with BoundedInputTree(snapshot, max_bytes=11_975_836, max_files=104) as tree:
    assert set(tree.files) == set(pins)
    for name, pin in pins.items():
        raw = tree.read(snapshot / name, max_bytes=pin["bytes"])
        assert len(raw) == pin["bytes"]
        assert sha256(raw).hexdigest() == pin["sha256"]
```

This checks copied output bytes, not original source bodies or current rights.
Retain the [software notices](notices/README.md) when redistributing the map.
Credit Neotoma, the constituent databases, investigators and appropriate dataset
publications when reusing the separately governed source evidence.

The completed publication used the existing static-asset writer, HTML renderer
and owned publication boundary at [source revision `df54b2d`](https://github.com/bijux/bijux-pollenomics/commit/df54b2de1ba76de3edb2fabe7b6bc733e590bb85).
It restored the qualified compact projection and attached selected chain
metadata, preserving the earlier logical populations. Exact regeneration needs
those explicitly bound inputs; these rendered files alone are not a public
inverse-catalogue API. Copying and verifying the snapshot does not require that
restoration, a provider request or a model run.

Continue to the [native source archive](../../../../../docs/public/pollenomics-data/sources/neotoma-source-resources.md)
and [ancillary contracts](../../../../../docs/public/pollenomics-data/sources/neotoma-ancillary-resources.md#selected-recorded-ancestry-in-atlas)
for the separate source-reader, current-permission and method-input boundaries.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Portable recorded source metadata with 16 explicit ancestry targets; unchanged numerical Atlas scope.

**Unsupported claim.** Current permissions, names or publication titles in the selected projection, taxon/PPE equivalence, admitted method inputs or vegetation accuracy.

**Actual verification performed.** Closed process, exact 104-file hashes, full transport validators and staged/final logical witnesses; no new GET or model.

**Remaining input or review.** Exact-snapshot browser checks remain pending; scientific source and method decisions stay separate. Resolver: Source reader and method reviewer. Reopen when: A changed source epoch, selected input or newly qualified browser result.

**Cause category.** Recorded metadata integrity and scientific eligibility have different owners.

**Consequence.** Metadata can be inspected without upgrading source authority.

**Precise next acceptance route.** Qualify the exact browser route; bind source and method inputs separately before scientific use.

**Negative or refused result.** Earlier one-GiB publication attempt refused; its incomplete candidate remains distinct from this successful snapshot.

**Matched denominator.** 1,258 dataset identities / 527 sites; six supporting archives, 531 entries, including 16 selected targets.

Retained evidence: [reports/science/source-integrity/neotoma/recorded-source-atlas/verification.json](verification.json), [reports/science/source-integrity/neotoma/recorded-source-atlas/atlas/metadata-publication.json](atlas/metadata-publication.json).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
