# HYDE provider metadata and local release rights

The [HYDE 3.5 provider page](https://landuse.sites.uu.nl/datasets/)
links to the Yoda record for DOI
[`10.24416/UU01-F45D44`](https://doi.org/10.24416/UU01-F45D44).
The [DataCite API record](https://api.datacite.org/dois/10.24416/UU01-F45D44)
was retrieved on 2026-09-29 and retained byte for byte as
[datacite-response.json](datacite-response.json), SHA-256
`522de6f01689dd8913d8dcde79d7f0f26917ec942bf823bad0f95e63500582d5`
(10,590 bytes). It gives the title *HYDE data for the Global Carbon Budget
(2025)*, publisher Utrecht University, version 1.0, issue timestamp
2025-06-11T11:42:01 and update timestamp 2026-09-28T13:11:36. Its current
rights list includes open retrieval and CC BY 4.0.

The local HYDE 3.5 package's `yoda-metadata[1749214948].json` instead declares
CC BY-NC 4.0, as does its `License.txt`. Their SHA-256 identities are
`44dacada9b1b9ade1886bf0f2a26277a2b964afbff46f9ee64c17069f7b57b3a`
and `3711f963c05d0be80d53e5923308a6dee31b203da23435c9cfb7c7b6e4dd5e19`.
The package README and NetCDF attributes declare CC BY 3.0. The provider
record and local metadata have a matching dataset title and version, but this
does not establish that the DataCite update changed the license of each
downloaded file or that the locally retained bytes match a current Yoda
release. The Yoda landing page denied automated access during this review.

The three rights claims remain distinct. Scientific local analysis and the
source-reported country cropland conservation result do not imply permission
to redistribute HYDE grids or publish derived HYDE cell products. A source
owner or repository authority must bind the current metadata and applicable
rights to this exact release before such publication. Formal CRS, historical
calendar and matched ecological estimand remain separate scientific gates.

## Dated registry observation

A separate bounded registry request retained the [17 November 2026 response](registry-observation-2026-11-17.json)
from the same DataCite endpoint: 10,609 bytes, SHA-256
`5468884df7c275e007785e3108c9fc2068eab2b7b1ab5322583fb9735e1a8daa`.
It still lists CC BY 4.0 and version 1.0. Its registry `updated` field is
2026-10-29T14:23:08Z, while the dataset's separate Updated date field is
2026-09-28T13:12:17. These are distinct metadata fields, not evidence of a
licence transition or a change to the local release. The response has no content
URL or member checksum inventory.

The earlier response remains unchanged. Neither observation binds those terms
to exact local members or overrides the project's separately documented README
reference. This documentation assembly used the retained metadata and made no
new provider request, native-grid read or numerical calculation.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Provider release/rights and modeled cropland estimand; not measured vegetation reference.

**Supported claim.** The separately dated retained DataCite records identify a HYDE provider release and its stated CC BY 4.0 metadata terms.

**Unsupported claim.** Matching title/version does not license the locally retained HYDE bytes under those terms or authorize derived-cell publication.

**Actual verification performed.** Read the retained 29 September and 17 November 2026 DOI metadata rights/version/date fields and the HYDE primary source account. The newer 10,609-byte response has its own SHA-256; neither record supplies exact local-member checksums. This documentation assembly made no provider request and reran no raster consumer.

**Remaining input or review.** The provider release must be bound to the exact local metadata, license and NetCDF/README bytes with source-owner rights clarification.

**Cause category.** Conflicting release-specific rights statements and unresolved byte identity.

**Consequence.** Provider metadata cannot silently replace local CC BY-NC 4.0 and CC BY 3.0 statements.

**Precise next acceptance route.** Obtain an exact-release rights and byte correspondence decision, then qualify matched CRS/calendar/estimand before publishing derivatives.

**Negative or refused result.** The Yoda landing access refusal and incompatible local/provider terms remain unresolved.

**Matched denominator.** 2 separately dated retained provider DOI records versus distinct local metadata/license/README/NetCDF claims; 0 qualified new raster cells.

- [Retained qualification evidence: docs/report/source-relations/hyde/provider-record/datacite-response.json](datacite-response.json) (SHA-256 `522de6f01689dd8913d8dcde79d7f0f26917ec942bf823bad0f95e63500582d5`).

- [Retained qualification evidence: docs/report/source-relations/hyde/provider-record/registry-observation-2026-11-17.json](registry-observation-2026-11-17.json) (SHA-256 `5468884df7c275e007785e3108c9fc2068eab2b7b1ab5322583fb9735e1a8daa`).

- [Retained qualification evidence: reports/science/hyde-cropland-source-account.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/hyde-cropland-source-account.md).

- [Canonical scientific account: reports/science/hyde-cropland-source-account.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/hyde-cropland-source-account.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
