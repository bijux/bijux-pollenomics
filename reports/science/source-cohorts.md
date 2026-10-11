# How we selected source cohorts and comparisons

We selected Neotoma/EPD counts and the authors' exact taxonomy lookup for the
[Denmark/Finland/Norway](denmark-finland-norway-author-pollen.md) and
[Swedish](sweden-author-pollen.md) 31-target observed-pollen studies. We
excluded each target country from training before prediction. This tests
pollen composition transfer on one Danish, 28 Finnish, 52 Norwegian and
three Swedish physical sites. We retained native count mass, assignments,
excluded names, refused site-bins and frozen prediction identities. We keep
the 31-target closed denominator separate from the earlier 16-label result.
Neither study admits its samples to LRA.

| Country | Physical sites | Selected samples | Assigned/native pollen NISP | Scored/attempted 500 BP bins | Source account |
| --- | ---: | ---: | ---: | ---: | --- |
| Denmark | 1 | 91 | 122,998/129,768 | 24/24 | [Country study](denmark-finland-norway-author-pollen.md), [Solsø lineage](../../docs/report/countries/denmark/solsoe-source-lineage/README.md) |
| Finland | 28 | 1,797 | 1,229,019/1,260,281 | 435/435 | [Country study](denmark-finland-norway-author-pollen.md) |
| Norway | 52 | 3,544 | 2,018,295/2,286,020 | 1,084/1,178 | [Country study](denmark-finland-norway-author-pollen.md) |
| Sweden | 3 | 228 | 221,800/240,966 | 51/54 | [Swedish study](sweden-author-pollen.md), [ABB method](abborrtjarnen-source-method.md) |

We retained the country study's [input manifest](../../docs/report/regions/nordic/author-target-pollen/input-manifest.json),
[coverage ledger](../../docs/report/regions/nordic/author-target-pollen/coverage.csv)
and [score table](../../docs/report/regions/nordic/author-target-pollen/scores.csv)
as the exact prediction and denominator trail. We refused 94 Norwegian bins
and three Swedish bins that lacked eligible training support; we did not
record them as zero-valued predictions. Denmark's single site cannot estimate
within-country between-site variation. We treat all four country results as
development evidence because the Nordic outcomes were previously exposed.

## LRA source gate

We require one identified physical core with selected chronology,
time-matched basin geometry, an eligible count and taxon denominator, fall
speeds and permitted PPE use before LRA admission. Our
[ABB source correspondence](../../docs/report/source-relations/neotoma/abbo-native-correspondence/README.md)
matches many depth and count cells, but the
[published-method review](abborrtjarnen-source-method.md)
still cannot bind the LandClim-selected age model and historical basin series.
For Solsø, we also lack complete source lineage despite a reported area and
matched age controls. We recorded these exact gaps in
[research needs](../needed/README.md); we have not substituted study-wide
assumptions for a named core's missing evidence.

## Context and validation sources

We checked modeled HYDE quantities and native grid reconciliation at seven
CE labels in the [country cropland report](hyde-cropland-source-account.md).
We use that result as modeled context, not as observed vegetation or measured
pollen-model benefit. Our [independent vegetation screen](../../docs/report/validation/empd2-nfi-pairing/README.md)
admits zero source-measurement pairs. We will score vegetation accuracy only
after matching measured targets and their sampling design.
