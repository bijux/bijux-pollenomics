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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Author/source lineage, transformations and distinct modeled products; chronology and historical run admission remain separate.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/publication-correspondence.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/publication-correspondence.md) (source SHA-256 `ffcac6cb938189c61113cf92453c4ee1c79fcd9a69305d4bf15fec387bbca898`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
