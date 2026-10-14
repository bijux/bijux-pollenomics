# LandClim II author and published parameter correspondence

The [31-row comparison](report.json) pairs the exact
[author REVEALS profile](../author-parameter-binding/README.md) with the
[PANGAEA LandClim II PPE/FSP source table](../parameter-candidates/README.md).
Each author target has exactly one published row with the same numerical fall
speed and an RPP mean within **0.00050001** of the displayed mean. This
pairing also resolves display-name differences such as author `Picea` versus
published `Picea abies`, and author `Quercus deciduous` versus published
`Quercus deciduous t.`. It compares source versions; it does not silently
rename native pollen observations.

The published RPP standard deviations agree with the square roots of the
author covariance diagonal to within 0.00050001 for **28 of 31** targets.
The other three exceed what three-decimal display rounding alone explains:

| Target | Author SD from variance | Published SD | Author minus published |
| --- | ---: | ---: | ---: |
| Cerealia-t | 0.380949 | 0.380 | +0.000949 |
| Cyperaceae | 0.050621 | 0.050 | +0.000621 |
| Phillyrea | 0.075000 | 0.076 | −0.001000 |

These small differences may reflect source revisions or another display rule;
the retained sources do not establish which. The author covariance values
remain unchanged for reproducibility, and the published SD values remain
unchanged as comparison targets. The report retains every exact source string,
all 31 differences, footnoted published fall-speed markers and input hashes.
It admits **zero** Swedish LRA samples: source parameter correspondence does
not resolve the native denominator or historical basin geometry.

Replay from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.landclim_parameter_correspondence \
  --repository . \
  --output artifacts/jobs/landclim-parameter-correspondence/replay
```

Compare the replayed `report.json` byte-for-byte with this directory.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** All 31 author mean/fall-speed rows pair uniquely to published rows under the frozen numerical display rule.

**Unsupported claim.** Mean/fall-speed correspondence does not make source SDs identical or authorize silently swapping parameter revisions.

**Actual verification performed.** Read every retained parameter pair and all three SD exceptions under the 0.00050001 display tolerance; no reconstruction or parameter change.

**Remaining input or review.** Source-holder explanation for the SD version/display differences and remaining Swedish input qualifications are needed.

**Cause category.** Parameter revisions retain small but real covariance discrepancies.

**Consequence.** Author covariance and published SD values remain distinct reproducibility targets.

**Precise next acceptance route.** Resolve source version/display authority before selecting a common uncertainty profile, then qualify actual pollen/site inputs.

**Negative or refused result.** Cerealia-t, Cyperaceae and Phillyrea SD differences exceed the declared three-decimal display bound; 0 LRA samples admitted.

**Matched denominator.** 31 exact fall-speed/within-bound mean pairs; 28 SDs within bound and 3 explicit exceptions.

Qualified authored reader SHA-256: `a25dcb75e22963efb35b7bce682090a7decf5767861e8fdc950b5c655d539103`.

- [Retained qualification evidence: docs/report/source-relations/neotoma/parameter-correspondence/report.json](report.json) (SHA-256 `0b869d584239390967c226a82ced03acb1e2419a8fa66b4226ff36b586147f16`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/author-parameter-binding/report.json](../author-parameter-binding/report.json) (SHA-256 `94ae944d1bb1f09fd0234f879915ce32c3d58e1587ad04165ef545f8d13ed202`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md) (source SHA-256 `f171557d0f98cd312aca71fdce6ffcd9d82ef4ef4e1ca328e5fa0dc4762210e5`).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
