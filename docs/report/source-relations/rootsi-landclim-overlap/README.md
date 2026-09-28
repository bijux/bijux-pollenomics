# Rootsi and LandClim II candidate overlap

The [row ledger](overlap.csv) binds 79 unique Rootsi metadata candidates to 79 of the 223 normalized LandClim II site features. It uses the five byte-identical derived candidate files retained in `data/landclim/review/rootsi-candidate-inputs/`, the published LandClim II site metadata workbook and receipt, and the normalized site consumer. [report.json](report.json) records their exact input hashes, denominators, the matching profile, and the dependency boundary. Regenerate with `python -m bijux_pollenomics_dev.source_completion.rootsi_landclim_overlap --repository . --output <absent-repository-directory>` using the repository's development package environment. The replay requires the tracked review copy and its fixed manifest and file hashes. The private typed workbooks are not part of this copy.

The 79 typed workbooks are retained under `landclim/rootsi-workbooks/` in the
external source data store, outside the product repository. Its
`manifest.json` has SHA-256
`dde88290dbdeca7a1047db74d5fb55a85c03a68daaef53795c5da9c1aebbd510`;
it binds 79 workbook members totaling **4,466,176 bytes** to the captured
archive hash
`f64d4dd411bc92362c9db2701c919063c2432e53fa523052e602da5f1a86183c`.
Every member name and SHA-256 matches this report's 79-row ledger. This
source-store custody supersedes dependence on disposable local run artifacts
for these workbook bytes. It does not authenticate the workbooks as the
historical inputs or clear their analytical reuse rights.

The join is a **metadata candidate overlap**. Each row carries its Rootsi typed-workbook member and hash claim, source and publication locators, sequence labels, sample counts, access marker, chronology label, and the consumer's site feature ID. It does not authenticate the historical workbook as the LandClim input or identify historical pollen cells. Across the 79 candidates, 78 Rootsi sample-count claims agree with the LandClim publication metadata. EKE differs: Rootsi claims 25 and LandClim reports 42. This review does not settle the historical input denominator or equivalence.

The LandClim site time bounds are **sequence coverage**, not sample ages or change events. Thirty-five site features have numeric coverage intervals. Thirty-six have negative BP source bounds and eight have partial source bounds; their normalized numeric intervals are refused. The ledger keeps the source Top/Bottom BP labels alongside the refusal reason. The chronology basis text is a source label, not an authenticated sample chronology.

The LandClim II DOI, sequence ID, country, access marker, sample count, site window count, and source workbook provenance must match before a row is emitted. `LCGRID_ID` is retained as site metadata. It does not prove that a specific Rootsi workbook or site contributed to a particular modeled grid cell, time window, value, or standard error. That contributor lineage remains unresolved.

These candidate dependencies block treating LandClim REVEALS outputs as independent vegetation ground truth for the matched Rootsi inputs. Per-sequence rights, historical input identity, source-age basis, taxonomy, count denominator, and exact grid/window contribution remain unresolved. This review does not certify complete V2-DATA-007 grid/window/value/SE lineage or admit raw Rootsi observations for scientific use.
