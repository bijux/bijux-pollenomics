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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/hyde-cropland-source-account.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/hyde-cropland-source-account.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
