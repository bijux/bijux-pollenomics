# LandClim II author parameter binding for Swedish pollen

The [author taxonomy screen](../author-taxonomy-mass/README.md) maps native
Swedish source names into the LandClim II authors' 31 RPP target names. Their
[REVEALS driver](https://github.com/rmfyfe/landclimII/blob/57ead2e2fcc493d099be4e5a3092fc396e1c3d3a/Kunes_REVEALS_iterate_across_sitelists.R)
reads `av-RPP.all.landclimII.csv` as the mean RPP (`alpha`) and pollen fall
speed (`vg`) input, and `avar-RPP.all.landclimII.csv` as the RPP covariance
input. The source files are retained in the external author-reference bundle.
The [bound report](report.json) verifies that all 31 lookup targets occur
exactly once, in the same order, in both parameter inputs; covariance is
symmetric, nonnegative on the diagonal and has zero nonzero off-diagonal
cells in this source version. The three Swedish sites have **169,013 of
187,002** native `NISP` counts (90.3803%) assigned to **24** of those targets.

| Author target | RPP `alpha` | Fall speed `vg` (m/s) | RPP variance | Assigned Swedish NISP |
| --- | ---: | ---: | ---: | ---: |
| Alnus glutinosa | 13.562 | 0.021 | 0.085936336 | 22,341 |
| Corylus avellana | 1.71 | 0.025 | 0.009995081 | 18,275 |
| Picea | 5.4375 | 0.056 | 0.009440571 | 6,705 |
| Poaceae | 1 | 0.035 | 0 | 3,166 |
| Quercus deciduous | 4.53667 | 0.035 | 0.007427785 | 9,500 |

These are source values from one coherent author computation profile, not
interchangeable values from an unrelated PPE table. The lookup deliberately
excludes some source names and leaves others unmapped; the 90.3803% fraction
is **not** a complete all-pollen LRA denominator. The 31-target binding
resolves parameter-name matching for assigned counts but does not prove that
Neotoma's BUS/ABB/BOKE core ages, radii or basin boundaries match those in the
authors' original run. The [Bussjösjön coordinate conflict](../bussjosjon-basin/README.md)
remains open. **Zero Swedish LRA samples are admitted.**

The source identities in the report pin the author driver
(`bc20b58bc1dc5933eb046233d44739d7da006624031aa4863e9a2731b077e341`),
mean/fall-speed file
(`066ebadbe6ab10aead80c74a184284e05b9db3cd1f5daff04249596170a663e2`),
covariance file
(`8821de94682c454e3a751897b487c8bf1612cf60994dc6246fb33284a73e9918`)
and governed taxonomy-mass input. Replay with:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.landclim_parameter_binding \
  --repository . \
  --author-source-root ../bijux-pollenomics-data/landclim/author-reference \
  --output artifacts/jobs/landclim-parameter-binding/replay
```

Compare the replayed `report.json` byte-for-byte with this directory.
