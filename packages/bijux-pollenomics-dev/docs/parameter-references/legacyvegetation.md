# LegacyVegetation 2025 in BOKE parameter coverage

The maintained BOKE source-audit consumer can include the attributed 2025
LegacyVegetation parameter reference alongside its original LandClim and 2020
inventories. This optional metadata extension does not replace either inventory,
change an existing parameter profile or rerun the Swedish transfer study.

```sh
python -B -m bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot \
  --repository . --output artifacts/bokesjon-parameter-reference \
  --legacyvegetation-2025
```

The ordinary source-audit command still requires its declared native inputs and
committed producer source. The new flag additionally reads only the independently
pinned `source.json`, `original-study-estimates.csv` and
`synthesized-estimates.csv` under
`data/validation/pollen-productivity/legacyvegetation-2025`. It does not acquire
workbooks or read vegetation outcomes. Without the flag, the original coverage
output and input population remain unchanged. Previously published 110-row
European coverage describes the 2020 reference; it did not consume this packet.

## Source rows and model axes are different

Each 2025 reference record retains its workbook, sheet, row, region or continent,
source cell references and literal values. Source-row identities distinguish the
two Sapindales rows (123 and 127); a `(region, taxon)` lookup is insufficient.
The original-study DOI/reference remains attached to original rows. Linking an
original row by literal taxon label is a candidate comparison, not proof that it
contributed to a particular synthesized value.

The synthesis contains 131 source rows in each of four regions. Europe has 61
reported positive nominal RPP rows, including overlapping genus/family levels
such as Betula and Betulaceae. That count does not describe 61 disjoint plant
axes, independent estimates or a validated model panel. The coverage product
selects no model axes and grants no scientific admission. It preserves literal
label matches only; no species, cereal/rye or aquatic/terrestrial mapping follows.

Original `rpp_se` values retain the source SE label; synthesis `rpp_sd` values
retain the source SD label. Neither becomes a local-model uncertainty law or
cross-taxon covariance. Blank and en-dash values remain distinct and never
become zero. Native `fall_speed`/`vg` strings retain their unqualified unit status;
no `fall_speed_m_s` value is inferred from their magnitudes.

European Ulmus RPP/SD/n remain missing even though its native `vg` is `0.032`.
Northern Hemisphere Ulmus is a different regional record, not an automatic
European replacement. `nominal_rpp_available` records only whether a literal
positive number is present. `nominal_rpp_fsp_available` remains false for these
unqualified reference rows, and `uncertainty_model_admitted` remains false.

## A bounded scientific use

A separately declared nominal Betula sensitivity can compare LandClim 5.106
with the European synthesis value 4.94 while holding the existing Ulmus value,
physical kernels, counts, chronology and geometry fixed. It is a mixed-source,
Betula-only model sensitivity, not a complete 2025 European profile or measured
vegetation accuracy. The synthesis SD and unqualified `vg` are unnecessary for
that nominal experiment and must not be silently substituted.

The existing Swedish parameter-transfer study already evaluates four explicit
mapping hypotheses across four cores. Its sparse-zero, partition and physical
assumptions retain their own scope; this new reference does not rerun that study
or inherit its numerical qualifications. A new sensitivity must first reproduce
its selected unchanged baseline, retain raw and adjusted LOVE output, and report
any refused case rather than silently dropping it.
