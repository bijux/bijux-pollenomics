# SEAD site discovery and retrieval by country

The [country counts](countries.csv) and [site ledger](sites.csv) reconcile the current governed 61-table SEAD capture from boundary discovery through retained `tbl_sites` retrieval to the normalized public site consumer. [report.json](report.json) pins every input byte identity. The runnable producer is `bijux_pollenomics_dev.source_completion.sead_country_retrieval`; invoke it from the repository root with `--repository . --output <absent-directory>`.

The bounding-box discovery contains **2,195 site identities**. Boundary review assigns 2,069 of them to Sweden (1,925), Denmark (59), Norway (45), or Finland (40). The same 2,069 site IDs and UUIDs occur in the completed source retrieval and normalized site consumer. The remaining **103 review** and **23 unassigned** identities occur only in the discovery/decision ledger; they are absent from both admitted products. The country table keeps these 126 in separate rows. Candidate countries on review decisions are retained in the site ledger but never counted as assigned countries.

The provider site records contain no source-reported country field for this scoped discovery. The `discovered_with_governed_country` column therefore groups the discovered rows by their later boundary decision; it is **not a source-native per-country discovery count**. For each assigned row the site ledger checks decision status, boundary authority, coordinates, site ID, UUID, country code, source retrieval, and normalized consumer country. For excluded rows it checks the pending qualified-review status and the absence of retrieved/normalized records. The retained source admission says coordinate validation of the excluded preflight payload was not independently verified; this report does not resolve those 126 coordinates or grant them a country.

This is site-context custody and retrieval evidence. It does not admit chronology, taxa, evidence events, propagation, or historical country interpretations. The capture release remains refused for its separately recorded scientific reasons. The broader [relational capture review](../sead/README.md) accounts for all 61 tables and 522,270 source rows; this report supplies the missing country-level discovery-to-consumer row check.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Source-native/context/propagation evidence: source units and eligibility/refusal populations do not become pollen observations or ecological events.

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
