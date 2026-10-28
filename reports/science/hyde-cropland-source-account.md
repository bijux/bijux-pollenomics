# What we established from Nordic HYDE cropland sources

We asked what the HYDE release itself reports for Nordic country cropland
before using it as model context. We retained 84 modeled totals for Denmark,
Finland, Norway and Sweden at seven native CE year labels and three source
scenarios in our [country-year table](../../docs/report/regions/nordic/hyde-country-cropland/country-years.csv).
Our [report](../../docs/report/regions/nordic/hyde-country-cropland/report.json)
pins four consumed source files by SHA-256. We read country codes from
`HYDE_country_codes.xlsx` and source totals from the scenario-specific
`cropland_c.txt` tables. We reported those totals in km² without assigning
grid cells to countries.

| Country | Base 500 CE, km² | Base 2000 CE, km² | Base 2025 CE, km² |
| --- | ---: | ---: | ---: |
| Denmark | 4,036.0 | 22,884.9 | 23,553.7 |
| Finland | 411.2 | 21,920.0 | 22,443.0 |
| Norway | 811.7 | 8,840.0 | 8,082.6 |
| Sweden | 3,082.2 | 26,022.0 | 25,235.1 |

We keep the lower and upper **scenario** columns as modeled alternatives, not
confidence limits. At 2000 CE, their four-country source totals bracket the
corresponding base totals; we do not infer that ordering for every native grid
cell or year. The release's README describes `cropland_c.txt` as country total
cropland area in km² and identifies `cropland<yr>.asc` as area in km² per cell.
The [provider's HYDE dataset page](https://landuse.sites.uu.nl/datasets/)
identifies HYDE 3.5 as its 2025 release and reports 5 arc minute resolution.
The release attributes HYDE 3.5 to Klein Goldewijk, Beusen, Vander Linden and
Doelman (2025, manuscript in preparation).

## Our source-authority decision

We compared the public release description with the declarations in the
retained local files before treating any native grid as an admitted Nordic
covariate. The [Utrecht catalog](https://landuse.sites.uu.nl/datasets/) names
HYDE 3.5 for the 2025 Global Carbon Budget at five arc minutes, but does not
publish a file manifest or checksums binding our local bytes to that release.
The local README calls itself `hyde35_c9_base_mrt2025`; all 48 inspected
NetCDF headers instead say `HYDE3.4 test netCDF`. We kept both declarations.
For a concrete byte anchor, our retained base 2000 CE cropland ZIP has SHA-256
`d0a762ccce3256d25c36e1c58894c6a6b05f93075006366854cc7e6176c7d09f`;
its ordinal-zero `cropland2000AD.asc` member has SHA-256
`31a74f63973886edbd2303737df2684c799caaea83af27561755e1d5da67b0c7`.
These identify our local source, not the provider's current distribution.

We retained the three distinct rights statements. The local Yoda metadata and
`License.txt` say CC BY-NC 4.0, while its README and NetCDF attributes say
CC BY 3.0. The [provider DOI record](../../docs/report/source-relations/hyde/provider-record/README.md)
now says CC BY 4.0 after its September 2026 update; it has no exact-member
binding to the local release. We have not selected whichever statement is
most convenient as permission to redistribute native cells.

The local ASCII grid header fixes a 4320-by-2160 source axis beginning at
longitude-like `-180`, latitude-like `-90`, with literal step `0.0833333`;
NetCDF coordinates carry degree units. Neither declaration gives a formal
datum or EPSG identity for country overlay. The ASCII `0AD` label and NetCDF
`365_day` calendar also lack a provider-specific conversion to historical
BP windows. Local headers name area in `km**2` and population in `capita`,
but do not establish which land-use categories overlap. The base, lower and
upper names are source scenarios, not probability intervals or pointwise
bounds. Our [source review](../../docs/public/pollenomics-data/sources/hyde.md)
retains the detailed axis and scenario observations.

We independently checked that one pinned 2000 CE base-cropland ZIP member
reproduces the selected 72,576 source tokens, missing mask, numeric-zero
count and literal-axis edges. The check read all 9,331,200 source cells and
matched the retained geometry result. The [source review](../../docs/public/pollenomics-data/sources/hyde.md)
records this bounded geometry finding.
This confirms a narrow source-index calculation. It supplies no formal CRS,
country membership, cell area or historical date conversion.

We therefore admit the bounded source-reported country totals and internal
grid conservation below as **modeled-source accounting only**. We do not yet
admit a release-wide native-grid product, public cell redistribution or a
matched pollen-model HYDE comparison. The open evidence request
asks for provider binding of file identity, rights, CRS, dates, units and
scenario meaning. This report owns our current decision.

We use these modeled totals as external land-use context. They do not measure
pollen or vegetation at our study sites. We kept the source years as CE labels
and retained the 2025 column while flagging release prose that states a 2023
endpoint. We apply the more restrictive local rights declaration to these
derived summaries. Our [native grid-to-country check](../../docs/report/regions/nordic/hyde-country-cropland/grid-conservation/README.md)
verified 21 cropland grids at the seven selected CE labels against their
source country tables. We still need other variables and years, rights
reconciliation, chronology alignment and a matched no-HYDE/HYDE model
comparison.

To reproduce our result, run from the repository root into a new artifacts
directory:

```sh
source_store="/path/to/qualified/bijux-pollenomics-data"
PYTHONPATH=packages/bijux-pollenomics/src:packages/bijux-pollenomics-dev/src \
  .venv/bin/python -m bijux_pollenomics_dev.source_completion.hyde_country_cropland \
  --source-root "$source_store/HYDE-3.5" \
  --output artifacts/jobs/hyde-nordic-country-cropland-replay
```

We can relocate the external source root without changing its relative input
paths. Our [HYDE source review](../../docs/public/pollenomics-data/sources/hyde.md)
records the remaining release and admission conflicts.

## Local cropland context for archived LandClim agricultural cover

We subsequently completed a bounded local modeled-context calculation for
LandClim II grids 779, 830 and 880. It reused retained source bytes for five
positive CE points (500, 1000, 1500, 1700 and 1900), three HYDE source scenarios,
and the archived LandClim agricultural-land category. This establishes a
conditional arithmetic result, not admission of a comparable pollen-model
HYDE covariate or independent vegetation accuracy. We publish execution scope
and refusal counts here; the cell results remain local.

| Observed outcome | Count | Scope |
| --- | ---: | --- |
| Contexts evaluated | 45 | Three grids, five source points, three scenarios |
| Conditional contrast variants | 180 | Two spatial supports and two area denominators per context |
| Local values retained | 90 | Source ISO 752 subset; comparable estimand remains unestablished |
| Missing-quantity refusals | 90 | Every complete-cell contrast retained missing quantities as unknown |
| Future-point refusals | 18 | CE 2000 and 2025, across three grids and three scenarios |

The complete one-degree cell was partitioned into source ISO 752, other-country
and unassigned positions. The retained ISO 752 subset excludes other-country and source-ISO no-data
positions under an explicit source-country-mask assumption. A no-data value
does not establish zero cropland, sea, lake or another physical class. Known
area terms were conserved across the partitions; partial sums did not become
complete quantities. Source ISO assignment does not establish a reviewed
national boundary, and the narrower subset does not reproduce whole-cell
spatial support.

Two denominators remain distinct: source maximum available land area and source
total spherical cell area. Neither is established as equivalent to LandClim's
closed modeled vegetation denominator. Half-degree LandClim II coordinates
were treated as centers of one-degree boxes by a declared spatial scenario;
the documented northwest-corner convention for LandClim I was not transferred.
Native degree-like axes were interpreted as geographic degrees, without
admitting a formal CRS or datum. Spherical clipping retained boundary slivers
and assumed uniform allocation of source quantities within native cells.
Missing, nonpositive-denominator and impossible-capacity cases remained
refusals rather than clipped or imputed values.

For this finite scenario, documented AD 1950 BP conventions allow the five
positive CE labels to be associated with archived BP interval labels. The
point-to-window rule treats a source instant as contextual to an interval,
not its observed or time-averaged cropland. The youngest archive label does
not recover the contributing cores' actual surface dates. CE 2000 and 2025
imply negative BP and were refused rather than coerced into the youngest
interval. No year-zero or NetCDF calendar convention was inferred.

Archived AL means and marginal standard errors are stored in percentage-cover
units. The calculation checked 31-taxon closure and the AL addends, then
explicitly divided percentage values by 100. AL is the source cereal-associated
agricultural category, comprising Cerealia-type and Secale; HYDE total cropland
is broader. Our [LandClim account](landclim-paper.md) describes the archived
composition and distinguishes it from new pollen reconstructions. Category
equivalence, spatial representativeness and instant-versus-interval equivalence
remain unestablished here. HYDE lower, base and upper are scenarios, not
calibrated confidence bounds. LandClim marginal standard errors do not supply
cross-source covariance or standard errors for these contrasts. We claim no
calibrated difference interval, predictive improvement, physical pollen-model
validation or historical 1,128-record reproduction.

The native calculation exited zero. Twenty-four focused source-fixture cases
and four real command-line refusal cases reached their expected outcomes.
A separate independent consumer also exited zero: it checked all 45 contexts,
540 area-account values, 360 ratio accounts, 90 finite contrasts and 90 null
contrasts. It used a distinct spherical rectangle formula and 50-digit decimal
arithmetic for retained-token sums and ratios, with absolute tolerance
`2e-9` in each checked quantity's units plus relative tolerance `2e-10`.
Country partitions and observed-zero versus missing populations matched.
This qualifies saved conditional arithmetic, not ecological comparability or
uncertainty coverage. Both terminal receipts recorded unchanged input custody
and no surviving owned processes.

Nineteen native ASCII members were read through only the required prefixes.
Their receipts bind actual prefix hashes, literal variable-specific headers,
quantity roles, source positions and compressed archive identities. They do
not claim full-member hashes, end-of-file checks or full-member CRC verification.
The independent consumer reused the saved capture and did not read native ZIP
members again. We did not repeat the whole-country conservation calculation,
certify the complete HYDE collection or perform a new physical reconstruction.

This calculation remains local noncommercial exploratory analysis under the
more restrictive retained CC BY-NC 4.0 declaration described above. Permission
to redistribute native cells or derived cell results is not established. No
cell values, fractions, differences, area totals, maps or numerical data exports
are published by this section. LandClim output licensing does not upgrade HYDE
rights. The [provider record](../../docs/report/source-relations/hyde/provider-record/README.md)
and [maintained source review](../../docs/public/pollenomics-data/sources/hyde.md)
retain the conflicting declarations. Provider-version authority, formal
geography, category and temporal comparability, qualified source review and
public redistribution permission remain open. The finite arithmetic success
does not establish release readiness.


<!-- scientific-verification-and-limits:begin -->
## Scientific verification and limits

**Supported claim.** Selected Nordic source totals and grid conservation; independently checked local cropland/archived-AL contextual arithmetic with explicit support and refusal scopes.

**Unsupported claim.** A licensed native-grid product or HYDE-assisted pollen-model effect.

**Actual verification performed.** Original 84 totals/21 grids/one whole-member token check reused; actual new 45-context native consumer and independent Decimal/spherical account both exited zero. 24 source guards and four CLI refusals passed. Numerical cell outputs remain local.

**Remaining input or review.** Country totals and selected grids conserve modeled source values, but retained file/version declarations and licences conflict; formal CRS, CE/0AD calendar, category overlap and scenario estimand are unbound. Resolver: HYDE release/licence provider and qualified geospatial/temporal reviewer Reopen when: Provider binds exact retained members to version, rights, CRS, time conversion, units and scenario meanings before matched ablation.

**Cause category.** data|assumption|comparability|access/rights

**Consequence.** Keep source scenarios as modeled alternatives, not confidence limits or measured land use.

**Precise next acceptance route.** Provider binds exact retained members to version, rights, CRS, time conversion, units and scenario meanings before matched ablation. Then update reports/science/model-use.md.

**Negative or refused result.** 90 complete-cell variants refused missing source quantities; 18 future CE-point cases refused. No matched no-HYDE/HYDE pollen ablation, ecological accuracy or common estimand admitted.

**Matched denominator.** 84 country totals and 21 source grids; new three grids × five CE points × three scenarios = 45 contexts, two supports × two denominators = 180 variants: 90 ISO752 local finite contrasts, 90 complete-cell nulls, plus 18 future-point refusals.

Retained evidence: [docs/report/regions/nordic/hyde-country-cropland/report.json](../../docs/report/regions/nordic/hyde-country-cropland/report.json), [docs/report/source-relations/hyde/provider-record/README.md](../../docs/report/source-relations/hyde/provider-record/README.md).

This account preserves the verification scope and source limitations; rendering these statements does not rerun or qualify the underlying science.

<!-- scientific-verification-and-limits:end -->
