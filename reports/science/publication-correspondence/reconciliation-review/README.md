# How we bound the LandClim reconciliation

We use the released 9-site and 8-site author grids as a numerical example,
not as the full 1,128-record historical study. The retained two-grid values
support a bounded calculation correspondence. They cannot establish original
input identity, rights, independent vegetation accuracy or ecological skill.

We require the current
[reconciliation producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/reconcile.py)
to reject oversized, encrypted, nonregular, duplicate and unsupported archive
members before decompression. Its acceptance gate requires exactly grids 512
and 562, 9 and 8 named sites, 25 bins, 31 taxa, matching site counts and
passing grid, regional and site comparisons. An unknown grouped output header
is refused rather than silently counted as a PFT. The
[focused regressions](../../../../packages/bijux-pollenomics-dev/tests/essd_reproduction/test_reconcile.py)
exercise those boundaries.

The paper's 12 PFTs, deposit description's 11 and archived output's 13
positions still lack one authenticated transformation; `ISTS` remains
unassigned. We bound the two provider descriptions by exact page hashes in
the [source manifest](../../../../data/landclim/review/provider-description-sources.json)
and keep the row-level question in our
[publication account](../pft-crosswalk/README.md).

The historical `0 / 1,128` statement means zero original records were
authenticated within the declared evidence closure. It is not an exhaustive
repository-wide absence proof. The current
[study-input inventory](../../../../docs/report/publication-replay/landclim-study-inputs/README.md)
and [open research needs](../../../needed/README.md) state the missing
historical counts, chronologies, revisions and use rights. We do not promote
the two-grid result to a whole-paper reproduction.
