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


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Provider release/rights and modeled cropland estimand; not measured vegetation reference.

**Supported claim.** The retained DataCite record identifies a HYDE provider release and its stated CC BY 4.0 metadata terms.

**Unsupported claim.** Matching title/version does not license the locally retained HYDE bytes under those terms or authorize derived-cell publication.

**Actual verification performed.** Read the retained DOI metadata rights/version/date fields and the HYDE primary source account; no provider request or raster consumer rerun.

**Remaining input or review.** The provider release must be bound to the exact local metadata, license and NetCDF/README bytes with source-owner rights clarification.

**Cause category.** Conflicting release-specific rights statements and unresolved byte identity.

**Consequence.** Provider metadata cannot silently replace local CC BY-NC 4.0 and CC BY 3.0 statements.

**Precise next acceptance route.** Obtain an exact-release rights and byte correspondence decision, then qualify matched CRS/calendar/estimand before publishing derivatives.

**Negative or refused result.** The Yoda landing access refusal and incompatible local/provider terms remain unresolved.

**Matched denominator.** 1 retained provider DOI record versus distinct local metadata/license/README/NetCDF claims; 0 qualified new raster cells.

Qualified authored reader SHA-256: `a1b3eb5cfdfb46c4557a924e3480c0183da942f4b480be682b9d76318c5f9b3c`.

- [Retained qualification evidence: docs/report/source-relations/hyde/provider-record/datacite-response.json](datacite-response.json) (SHA-256 `522de6f01689dd8913d8dcde79d7f0f26917ec942bf823bad0f95e63500582d5`).

- [Retained qualification evidence: reports/science/hyde-cropland-source-account.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/hyde-cropland-source-account.md) (SHA-256 `995c8f3d6ee273554fc0d97f68dcd8bb8a0bb4cf8da56759f8adceda337f8c29`).

- [Canonical scientific account: reports/science/hyde-cropland-source-account.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/hyde-cropland-source-account.md) (source SHA-256 `995c8f3d6ee273554fc0d97f68dcd8bb8a0bb4cf8da56759f8adceda337f8c29`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
