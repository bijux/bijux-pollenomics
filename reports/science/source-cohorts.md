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

We use the [governed source-capability report](../../docs/report/regions/nordic/source-capability/README.md)
to distinguish source-reported, governed-assignment and publication
availability across 11 families and six country partitions. We do not select
an analytical cohort from those family-level cells. Our selected
**observed-pollen** cohorts have these source denominators and scored bins:

| Country | Physical sites | Selected samples | Assigned/native pollen NISP | Scored/attempted 500 BP bins | Governed result |
| --- | ---: | ---: | ---: | ---: | --- |
| Denmark | 1 | 91 | 122,998/129,768 | 24/24 | [DK/FI/NO result](../../docs/report/regions/nordic/author-target-pollen/report.json) |
| Finland | 28 | 1,797 | 1,229,019/1,260,281 | 435/435 | [DK/FI/NO result](../../docs/report/regions/nordic/author-target-pollen/report.json) |
| Norway | 52 | 3,544 | 2,018,295/2,286,020 | 1,084/1,178 | [DK/FI/NO result](../../docs/report/regions/nordic/author-target-pollen/report.json) |
| Sweden | 3 | 228 | 221,800/240,966 | 51/54 | [Swedish result](../../docs/report/regions/nordic/swedish-author-target-pollen/report.json) |

The governed results own the site, sample and count-mass values. Their
[DK/FI/NO coverage](../../docs/report/regions/nordic/author-target-pollen/coverage.csv)
and [Swedish coverage](../../docs/report/regions/nordic/swedish-author-target-pollen/coverage.csv)
retain every attempted and scored bin. The [DK/FI/NO input manifest](../../docs/report/regions/nordic/author-target-pollen/input-manifest.json),
[Swedish input manifest](../../docs/report/regions/nordic/swedish-author-target-pollen/input-manifest.json),
[DK/FI/NO scores](../../docs/report/regions/nordic/author-target-pollen/scores.csv)
and [Swedish scores](../../docs/report/regions/nordic/swedish-author-target-pollen/scores.csv)
retain prediction identities and results. We refused 94 Norwegian bins and
three Swedish bins without eligible training support instead of recording
zero-valued predictions. Denmark's single site cannot estimate within-country
between-site variation. We treat all four country results as development
evidence because the Nordic outcomes were previously exposed.

## LRA source gate

We require one identified physical core with selected chronology,
time-matched basin geometry, an eligible count and taxon denominator, fall
speeds and permitted PPE use before LRA admission. Our
[ABB source correspondence](../../docs/report/source-relations/neotoma/abbo-native-correspondence/README.md)
matches many depth and count cells, but the
[published-method review](abborrtjarnen-source-method.md)
still cannot bind the LandClim-selected age model and historical basin series.
For Solsø, our [source decision](solsoe-lra-input.md) still lacks the actual
79 LandClim II input rows, selected authors chronology and historical basin
series despite a reported area and matched age controls. For Norwegian
Dalmutladdo, our [source control comparison](dalmutladdo-lra-input/README.md)
matches 72 samples and all 11 radiocarbon source controls, while conflicting
reported areas and missing time-matched basin and analytical-use fields still
prevent LRA admission. Finnish Laihalampi has an exact 150-sample, single-core
lead and consistent modern area claims, but its [source decision](laihalampi-lra-input/README.md)
still needs the selected age vector and dated basin. We recorded these exact gaps in
[research needs](../needed/README.md); we have not substituted study-wide
assumptions for a named core's missing evidence.

The existing [site-level author-taxonomy mass ledger](../../docs/report/regions/nordic/author-taxonomy-mass/sites.csv)
accounts for 84,078 assigned, 916 excluded and 309 unmapped native counts at
Laihalampi, and 46,477 assigned, 600 excluded and eight unmapped at
Dalmutladdo. Both sums close on their respective 150 and 72 selected
Neotoma samples. This reuses the prior observed-pollen study; neither
31-target subcomposition is an admitted LRA denominator.

## Context and validation sources

We also joined every reviewed SEAD chronology claim to its governed country and
site decision in the [country claim account](../../docs/report/source-relations/sead/chronology-country-accounting/README.md).
The 25,109 claims belong to 853 distinct sites among 2,069 assigned sites:
Sweden 22,643 claims at 741 sites, Denmark 1,939 at 56, Norway 468 at 27,
and Finland 59 at 29. Another 126 site decisions remain outside that assigned
population. These are chronology source rows, not pollen samples or admitted
ecological events. We retained all 25,109 propagation refusals, including the
13,170 claims eligible only for chronology display.

We decided that the present four-country scientific comparison tests
**observed-pollen prediction**, not national archaeology density or candidate
rankings. No archaeology count enters its training inputs, outcomes, scores or
country denominators. We therefore do not acquire Danish, Finnish and
Norwegian heritage registries for this comparison. This is a scope decision,
not evidence that archaeology is absent or comparable across countries.
Sweden-only RAÄ cannot stand in for the other national registries; its current
source authority is refused even for Swedish analytical density. SEAD is
environmental-archaeology context with its own site and record units, not a
replacement national inventory. The
[country capability table](../../docs/public/pollenomics-data/sources/country-source-limitations.md)
records this asymmetry. If we later compare archaeological density or use
heritage context to rank candidates across all four countries, that analysis
must first identify appropriate national sources and review each source's
licence, observation unit, classification, coverage, update method and time
support. Missing capture must remain unknown rather than a zero.

We checked modeled HYDE quantities and native grid reconciliation at seven
CE labels in the [country cropland report](hyde-cropland-source-account.md).
We use that result as modeled context, not as observed vegetation or measured
pollen-model benefit. Our [independent vegetation screen](../../docs/report/validation/empd2-nfi-pairing/README.md)
admits zero source-measurement pairs. We will score vegetation accuracy only
after matching measured targets and their sampling design.
