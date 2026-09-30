# Our disposition of the ESSD reconciliation review

An independent review of historical candidate commit
`71ca540185188cbc5b744b676d3c6762a1a603d8` accepted only its bounded
two-grid author-example result. The [exact review result](result.json) also
found that the candidate archive reader could accept unbounded or nonregular
members and that its two-grid parity label did not require the full 9/8 site
identities and passing predicates. These were defects in a historical intake
candidate, not evidence that the pinned 512/562 numerical values differed.

We checked the current
[reconciliation producer](../../../../packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/reconcile.py)
and its [focused tests](../../../../packages/bijux-pollenomics-dev/tests/essd_reproduction/test_reconcile.py).
The producer now limits archive and member bytes, count, expansion and ratio
before reading members, and rejects encrypted or nonregular entries. It
requires exactly two grid objects with the expected IDs, 9/8 named sites,
25 bins, 31 taxa, matching site counts and passing grid, regional and site
checks before emitting the bounded parity status. A separate test rejects an
unknown grouped output header instead of classifying it as a PFT. The three
selected tests passed on the current code. The exact review result above
records the historical defects; the current producer and tests own their
resolution.

The historical `0 / 1,128` statement remains a declared evidence-closure
absence, not a computed exhaustive sample audit. It cannot authenticate the
archive's original pollen, chronology, rights or PFT transformation. The
[publication account](../landclim-metadata-challenge/README.md) and
[open research needs](../../../needed/README.md) retain those gaps.
