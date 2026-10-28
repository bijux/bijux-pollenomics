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

The linked canonical accounts state the supported and unsupported claim, actual verification performed, remaining input or review, cause category, consequence, precise next acceptance route, negative or refused result and matched denominator. Read those limits alongside this page's own source population; an account link does not substitute another study's denominator or establish scientific validity.

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
