# Numerical method and publication correspondence

The [original-R certification](../../docs/report/method-certification/original-r-reference/README.md)
checks bounded numerical contracts against retained author source cases. The
[author-example correspondence](../../docs/report/publication-replay/landclim-author-example-correspondence/README.md)
then compares the installed Python publication profile with an independently
executed author-R example: all 14,074 supported fractional cover and standard
error values meet the declared tolerances. Maximum absolute mean and SE
residuals are 1.83881e-13 and 7.15331e-14. This is selected two-grid
calculation correspondence, not full historical input or ecological accuracy.

The [raw-to-prepared replay](../../docs/report/source-relations/landclim/author-example-taxon-support/README.md)
reproduces 17 example prepared files byte for byte from 871 raw sample rows
and 15,028 matching prepared cells. It does not authenticate the historical
Nordic publication revisions.

## A real publication difference

The [paper correspondence account](publication-correspondence.md)
compares the exact shared TW2 interval, 100–350 BP. The archived PANGAEA
937075 means differ from author-R by up to 9.19787 percentage points in grid
512 and 10.5527 in grid 562; SE gaps reach 3.21615 and 4.25814 points.
Only one of 25 window intervals matches exactly. A plausible source-revision
or transformation explanation remains unverified, so the differences are
retained as differences, without shifting windows or renaming taxon groups.
The [row ledger](../../docs/report/pollen-reconstruction/paper-correspondence.csv)
and [PFT crosswalk](../../docs/report/publication-replay/landclim-pft-crosswalk/README.md)
give the exact cells and arithmetic.

Archived ISTS/TBS **mean arithmetic** closes on the source taxon groups over
10,500 grid/window rows. It does not identify the archive's biological ISTS
definition or SE covariance transformation. The paper, deposit prose and
archive expose different PFT counts or positions. A provider-bound historical
input and transformation packet is still needed for full-paper reproduction.

## How to use this result

Use the selected author profile to test numerical fidelity to the retained R
example. Use the separate archive comparison to investigate historical source
identity. Do not treat either result as measured vegetation validation. The
[English LRA development study](../../docs/report/pollen-reconstruction/author-lra-constrained/README.md)
provides a distinct real reconstruction and withheld forward-pollen test;
its matched direct-pollen scores and model conditions are summarized in the
[prediction report](pollen-prediction.md).
