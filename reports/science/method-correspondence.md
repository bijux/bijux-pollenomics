# What we reproduced from the numerical method

We [bound the released author profile](publication-correspondence/author-method-profile.md)
to its 17 example sites, 31-taxon PPE/covariance axis and 25 bins. We
checked bounded numerical contracts against retained author source cases
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

## Optimizer budget accounting

We independently challenged an earlier differential-evolution solver against
its corrected successor on 135 combinations of dimension, fixed bounds,
population size and evaluation budget. In both executed runs, 54 cases changed
the reported completed-generation count; 81 did not. Every case retained the
same objective-evaluation trace, random-generator state and other result fields.
The corrected snapshots in that comparison precede today's
solver, so this is evidence for the historical accounting change, not a fresh
135-case certification of current code. Our [current focused regression](../../packages/bijux-pollenomics-lra/tests/unit/optimization/test_solver.py)
checks completed generations and exact evaluations at four budgets. Generation
accounting alone says nothing about the quality of a vegetation optimum or
agreement with the original R optimizer.

## Optimized LOVE on shared objectives

We compared the installed RcppDE and Python searches on three declared LOVE
objectives with identical pollen, deposition, background, PPE, bounds and
iteration cap. In the [governed solution-quality study](../../docs/report/method-certification/optimizer-solution-quality/README.md),
both achieved objective values within `1e-4` of the independently derived
optima. Evaluating each selected candidate in the other implementation gave
absolute objective gaps below `1e-10`. The [three result rows](../../docs/report/method-certification/optimizer-solution-quality/summary.csv)
include a composition-ambiguous case where different cover vectors are equally
good; we judged objective quality and common-candidate arithmetic, not vector
identity. Python reported success after 29–40 iterations and 600–1,230
evaluations. R used its full 400-iteration cap in all three cases. These
small, declared objectives support bounded numerical solution quality; they
do not establish identical random search paths, global convergence on other
landscapes or ecological accuracy.

We also [replayed analytical LOVE across ten example rings](analytical-love-ring-sensitivity/README.md).
Only three satisfy the source's local-basin boundary; 16 of their 30
taxon/ring estimates are negative and six exceed one. We retained those
unconstrained results to show ring sensitivity rather than presenting an
invented closed vegetation composition or a recommended Nordic radius.

We re-executed the [native R oracle](../../docs/report/method-certification/current-r-oracle/README.md)
against the installed Python source closure. All 43 core and 23 source-domain
cases pass, including 18 prospective optimized LOVE cases. The 97 numeric CSV
files match the earlier retained oracle byte for byte, and 48 original-R
vector comparisons pass. This is numerical method correspondence on declared
inputs. We also ran the [same ten-taxon `LOVEexample` inputs](../../docs/report/numerical-performance/love-source-comparison/README.md)
through native R and Python with binary-identical values and 32 fixed
candidates at each of eight active ring/repeat calls. Cover and pollen agree
exactly; ring factors differ by at most 5.11e-15 and objective values by at
most 4.67e-15. All eight selected candidate indices agree. This checks
fixed-candidate calculation, while optimizer searches and Nordic vegetation
remain outside the comparison.

We checked a separate source behavior in a [controlled optimized LOVE
regression](../../packages/bijux-pollenomics-lra/tests/unit/reconstruction/test_optimized_profile.py):
two distinct sampled local PPE vectors produce identical cover, pollen and
objective values when regional cover, local pollen counts and candidates are
held fixed. The source-compatible optimized objective uses nominal local PPE
despite sampling a local PPE vector. We do not count that sampled vector as
propagated local PPE uncertainty or infer the paper's Figure 2 from this test.

## A real publication difference

We compared the exact shared TW2 interval, 100–350 BP, in our
[paper correspondence account](publication-correspondence.md). The archived PANGAEA
937075 means differ from author-R by up to 9.19787 percentage points in grid
512 and 10.5527 in grid 562; SE gaps reach 3.21615 and 4.25814 points.
Only one of 25 window intervals matches exactly. We retain the differences
without shifting windows or renaming taxon groups because the possible source
revision or transformation explanation remains unverified. Our
[row ledger](../../docs/report/pollen-reconstruction/paper-correspondence.csv)
and [PFT crosswalk](publication-correspondence/pft-crosswalk/README.md)
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
