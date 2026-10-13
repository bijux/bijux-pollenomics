# Conditional botanical composition of the Pyrenees surveys

The recovered botanical workbook supports a conditional 17-axis botanical
composition under declared taxonomy, parent-row and blank scenarios. An
analyst must assume that blank and unlisted survey entries represent zero
recorded cover to obtain complete vectors. Keeping those entries unknown
instead refuses every complete vector. The result is a source transformation,
with no paired pollen or vegetation accuracy score.

## Sources and scientific scope

The source is Florence Mazier, Clara Plancher, Sébastien Haunold, Colline Bonnet,
Hugo Belly and Thomas Houet's [Vegetation surveys in mountainous area
(Pyrenees, France)](https://doi.org/10.48579/PRO/9SI1PN), published through
data.InDoRES. The retained publisher export identifies version 1.4 and CC BY
4.0. The recovered ODS file contains 125 plots and 208 taxon rows, with 1,757
positive cover entries. These differ from the paper's 116-plot selection;
that selection and its historical source version have not been recovered.

Native BDTFX 3.01 is the declared conditional taxonomy, with 3.00 retained as
a sensitivity. Both archives attribute Benoît Bock and Tela Botanica
contributors and declare CC BY-SA 2.0 France. Neither is authenticated as the
paper's original taxonomy. The [source account](source-account.json) records
separate terms and exact hashes. Detailed taxonomy extracts, original plots
and individual vectors remain local artifacts; this account does not resolve
their public redistribution or derived-taxonomy license compatibility.

## Botanical associations and assumptions

The panel comprises Abies, Betula, Corylus, Fagus, Fraxinus, Picea, Pinus,
Quercus, Salix, Tilia, Calluna vulgaris, Ericaceae excluding Calluna vulgaris,
Juniperus, Cyperaceae, Plantago lanceolata, Poaceae and a botanical Potentilla
genus proxy. No native Cichorioideae anchor or authenticated author crosswalk
is available, so the paper's complete 18-axis denominator is unavailable.
Calluna is counted separately from Ericaceae. Source codes, literal names,
broader labels and alternative accepted identifiers remain distinct.

The 25 original zero-code labels comprise six families and 19 source
`genus sp.` labels. Analyst associations require a unique literal native name,
the declared family or genus rank and a valid retained-name/parent chain.
The genus interpretation means an undetermined species of that genus, with
no invented species identity. Original codes remain zero, and associated
native identifiers remain separately recorded assumptions.

## Complete source accounting

All combinations of two taxonomy versions, two source-name/code association
modes, two parent-row interpretations and two blank interpretations executed:
16 scenarios, 2,000 plot contexts and 34,000 raw axis cells. Each original
positive entry has an included, omitted, outside-panel or unresolved account
in every scenario, totaling 28,112 repeated accounts. These counts do not
create additional independent observations.

All eight strict-unknown scenarios refuse their 125 vectors, producing 1,000
refusals. All eight exhaustive-survey alternatives produce 125 conditional
vectors each. In particular, the unrepresented Salix axis becomes zero only
under that explicit assumption. Source cover sums can exceed 100 because
generic observations and vegetation strata have not been established as
exclusive area components. Closing selected cover to one does not establish
whole-landscape vegetation fractions or actual species absence.

Parent observations either represent declared disjoint residual cover or are
omitted when a descendant occurs in the fixed source inventory. Three literal
names have different accepted identifiers under the code and name alternatives
in each taxonomy; that disagreement is preserved rather than declared a
synonym correction. Both equal-plot mean composition and closure of mean
cover remain in the private class tables. They are different operators.

The original plots span 102 surveys in 2015 and 23 in 2020, with 33 areas of
25 m², 62 of 100 m² and 30 of 400 m². Eight map classes and nine field classes
remain separate. Year, area, class and campaign confounding and spatial
dependence prevent treating these repeated contexts as independent cohorts.

## Numerical verification

The actual native consumer passed 54 guards and its separate native-name and
Decimal50 audit. That audit checked 34,000 raw cells, 17,000 closed cells,
11,424 class-operator cells and all 28,112 positive-observation accounts.
Across 64,424 decimal comparisons, maximum absolute difference was 1e-14
under the unchanged 2e-13 tolerance. The implementations share an interpreter;
their agreement supplies numerical verification, not independent ecological
measurements or qualified external review. The [result receipt](report.json)
binds candidate, exact command, source custody, native exit and audit.

## Reproduction

The maintained [replay producer](../../../../reports/science/vegetation-reference/pyrenees-botanical-projection/replay.py)
requires the exact retained 16-file source packet. From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  reports/science/vegetation-reference/pyrenees-botanical-projection/replay.py \
  --source-root /path/to/private/pyrenees-botanical-projection/inputs \
  --output artifacts/science/pyrenees-botanical-replay
```

The output must be absent. The producer checks managed input pins and original
lineage/census terminal bindings, copies private inputs into its owned output,
executes the projection and guards, and independently audits its saved outputs.
It acquires no data, refits no model and reuses the admitted 183 saved native
identifier chains per taxonomy. No historical reproduction, untouched test,
calibrated uncertainty, matched-pollen prediction or independent vegetation
accuracy is established. Those channels remain unadmitted and unscored.
