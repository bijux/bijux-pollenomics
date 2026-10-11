# OpenLand REVEALS DOI lineage

The OpenLand paper cites [PANGAEA 931856](https://doi.org/10.1594/PANGAEA.931856)
for its REVEALS inputs. The [DataCite record for 931856](https://api.datacite.org/dois/10.1594%2FPANGAEA.931856)
explicitly identifies [PANGAEA 937075](https://doi.org/10.1594/PANGAEA.937075)
as its successor (`IsObsoletedBy`). Both records have the same dataset title.
The exact metadata fields and response SHA-256 values retrieved on 2026-09-29
are retained in [doi-lineage.json](doi-lineage.json).

| DOI | DataCite rights statement | Consequence for this intake |
| --- | --- | --- |
| 10.1594/PANGAEA.931856 | Access restricted; licensing terms unknown and author contact requested | Its citation does not grant access to or redistribution of the superseded dataset. |
| 10.1594/PANGAEA.937075 | CC BY 4.0 | The published successor has a distinct license and version identity. It does not license a separate OpenLand derivative or establish that its rows equal the older inputs. |

The supersession relation establishes **dataset lineage**, not byte or row
identity. The 25 OpenLand CSV members match the pinned OpenLand Git blobs, as
shown by the [member ledger](members.csv). No recovered input-level join binds
those members to a specific 931856 release row or to 937075's June 2021
archive. OpenLand's spatial estimates are derived from pollen-based REVEALS
inputs and remain unsuitable as independent vegetation truth. Keep the CSVs
under the existing private modeled-source review decision until their own
rights and scientific relationship are qualified.
