# What we reproduced from the numerical method

We checked bounded numerical contracts against retained author source cases
in our [original-R certification](../../docs/report/method-certification/original-r-reference/README.md).
We then compared the installed Python publication profile with an
independently executed author-R example in the
[author-example correspondence](../../docs/report/publication-replay/landclim-author-example-correspondence/README.md).
All 14,074 supported fractional cover and standard-error values meet the
declared tolerances. Maximum absolute mean and SE residuals are 1.83881e-13
and 7.15331e-14. We claim calculation correspondence for these two grids,
not full historical input closure or ecological accuracy.

We reproduced 17 prepared author-example files byte for byte from 871 raw
sample rows and 15,028 matching prepared cells in the
[raw-to-prepared replay](../../docs/report/source-relations/landclim/author-example-taxon-support/README.md).
We have not authenticated the historical Nordic publication revisions.

## A real publication difference

We compared the exact shared TW2 interval, 100–350 BP, in our
[paper correspondence account](publication-correspondence.md). The archived PANGAEA
937075 means differ from author-R by up to 9.19787 percentage points in grid
512 and 10.5527 in grid 562; SE gaps reach 3.21615 and 4.25814 points.
Only one of 25 window intervals matches exactly. We retain the differences
without shifting windows or renaming taxon groups because the possible source
revision or transformation explanation remains unverified. Our
[row ledger](../../docs/report/pollen-reconstruction/paper-correspondence.csv)
and [PFT crosswalk](../../docs/report/publication-replay/landclim-pft-crosswalk/README.md)
give the exact cells and arithmetic.

We closed archived ISTS/TBS **mean arithmetic** on the source taxon groups
over 10,500 grid/window rows. We did not identify the archive's biological
ISTS definition or SE covariance transformation. The paper, deposit prose
and archive expose different PFT counts or positions. We still need a
provider-bound historical input and transformation packet to reproduce the
full paper.

## How to use this result

We use the selected author profile to test numerical fidelity to the
retained R example. We use the separate archive comparison to investigate
historical source identity. We do not treat either as measured vegetation
validation. Our [English LRA development study](english-lra-pollen-prediction.md)
provides a distinct real reconstruction and withheld forward-pollen test;
we summarize its matched direct-pollen scores and model conditions in the
[prediction report](pollen-prediction.md).
