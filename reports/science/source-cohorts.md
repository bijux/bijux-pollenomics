# Source cohorts and admissible comparisons

The four-country [31-target observed-pollen study](../../docs/report/regions/nordic/author-target-pollen/README.md)
uses selected Neotoma/EPD counts and the authors' exact taxonomy lookup.
Country exclusion is applied to the training input before prediction. This
supports a bounded test of pollen composition transfer, with one Danish site,
28 Finnish sites, 52 Norwegian sites and three Swedish sites. The study retains
all native count mass, assignments, excluded names, refused site-bins and
frozen prediction identities. Its 31-target closed denominator differs from
the earlier 16-label result. Neither result admits these samples to LRA.

| Country | Physical sites | Selected samples | Assigned/native pollen NISP | Scored/attempted 500 BP bins | Source account |
| --- | ---: | ---: | ---: | ---: | --- |
| Denmark | 1 | 91 | 122,998/129,768 | 24/24 | [Country study](../../docs/report/regions/nordic/author-target-pollen/README.md), [Solsø lineage](../../docs/report/countries/denmark/solsoe-source-lineage/README.md) |
| Finland | 28 | 1,797 | 1,229,019/1,260,281 | 435/435 | [Country study](../../docs/report/regions/nordic/author-target-pollen/README.md) |
| Norway | 52 | 3,544 | 2,018,295/2,286,020 | 1,084/1,178 | [Country study](../../docs/report/regions/nordic/author-target-pollen/README.md) |
| Sweden | 3 | 228 | 221,800/240,966 | 51/54 | [Swedish account](nordic-pollen-study.md), [ABB method](../../docs/report/source-relations/neotoma/abbo-published-method/README.md) |

The country study's [input manifest](../../docs/report/regions/nordic/author-target-pollen/input-manifest.json),
[coverage ledger](../../docs/report/regions/nordic/author-target-pollen/coverage.csv)
and [score table](../../docs/report/regions/nordic/author-target-pollen/scores.csv)
give the exact prediction and denominator trail. Ninety-four Norwegian bins
and three Swedish bins lack eligible training support; they are refusals, not
zero-valued predictions. Denmark's single site cannot estimate within-country
between-site variation. Prior exposure to Nordic outcomes makes all four
country results development evidence.

## LRA source gate

Real LRA needs a physical core and selected chronology, time-matched basin
geometry, eligible count/taxon denominator, fall speeds and PPE use that the
source permits. The [ABB source correspondence](../../docs/report/source-relations/neotoma/abbo-native-correspondence/README.md)
matches many depth/count cells, while the [published-method review](../../docs/report/source-relations/neotoma/abbo-published-method/README.md)
still cannot bind the LandClim-selected age model and historical basin series.
Solsø likewise has a source-lineage question despite a reported site area and
matched age controls. These gaps are recorded in [research needs](../needed/README.md),
not replaced by generic study-wide assumptions.

## Context and validation sources

The [HYDE country cropland report](../../docs/report/regions/nordic/hyde-country-cropland/README.md)
checks modeled-source quantities and native grid reconciliation at seven CE
labels. It supplies context, not a vegetation observation or a measured pollen
model benefit. The [independent vegetation screen](../../docs/report/validation/empd2-nfi-pairing/README.md)
retains zero admitted source-measurement pairs. Any vegetation accuracy claim
must wait for matched measured targets and their sampling design.
