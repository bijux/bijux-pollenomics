# Earlier scientific report provenance

These three files are exact copies of the results, scope, and evidence manifest
from the scoped scientific report assembled at commit
`907c948fe3ae471f36a268de87e49793e3700a4f`. They are a historical
snapshot, not the current study or a current verification target. The original
manifest bound 89 evidence files and four deliverables. Some of its artifact
paths have since been retired and some tracked inputs have changed, so its old
verifier cannot authenticate the present worktree.

The [current scientific report](../../../pollen-reconstruction/README.md),
[current results](../../../pollen-reconstruction/results.csv),
[current scope](../../../pollen-reconstruction/scope.json), and
[current verifier](../../../pollen-reconstruction/verify_report.py) govern live
claims. All 11 earlier result IDs occur in the current 17-row results table.
The earlier Nordic direct-pollen cohort had Finland and Norway scores and no
qualifying Denmark candidates. The current report uses a wider screened cohort,
adds qualifying Denmark candidates, and scores Denmark, Finland and Norway;
Sweden has its separate whole-site study. The earlier HYDE result was a refusal of
country assignment; the current report separately verifies country totals and
grid conservation while leaving a pollen covariate ablation blocked. Neither
snapshot establishes LRA skill or measured-vegetation validation.

The [historical Swedish source questions](source-questions.csv) preserve the
earlier artifact's exact ten rows. The [custody receipt](source-questions-custody.json)
binds its bytes and maps the same ten site/use keys to the [current source
questions](../../../pollen-reconstruction/swedish-source-questions.csv), which
contain later source findings. The frozen results and manifest below still name
the old artifact path as historical evidence; the retained copy supplies those
bytes after the inactive artifact is retired.

| Preserved file | SHA-256 of original and retained bytes |
| --- | --- |
| `manifest.json` | `95619eccaa73b205de8b6669b6afe3d128435ac1638c100badd7232cc1e97a97` |
| `results.csv` | `3347ceb4cb191bfe05d02b5a229a803e0b0ebc692ce6821041f26dee8eb5c26f` |
| `scope.json` | `9dadfa94218a9e07f97a4a7617c0b72fad6b709b2b6d54d93db3210225b1e968` |

The artifact's superseded `REPORT.md` had SHA-256
`805909d6e84de64f3af8e7279ef547c7ed01f284c524308a21c8fab687e10e33`;
its verifier had SHA-256
`0dc7a523699457d02aaacab8631657c2d79a8efeb2a3935d98b2386183c289a0`.
The current report retains and corrects the scientific interpretation; the
current verifier checks 170 retained files, 17 result rows, and source-specific
invariants. These two historical files were not retained as live interfaces.
