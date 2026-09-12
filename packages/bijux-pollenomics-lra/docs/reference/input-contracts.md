# Supported facade input contracts

The facade accepts pandas pollen frames whose first column is a **finite numeric
pairing coordinate** and remaining columns are unique pollen taxon names. It is
not a string sample ID and does not by itself imply BP, CE, depth or chronology.
The host retains raw sample/source identities and admits a governed coordinate
axis before calling this engine. Counts are finite, nonnegative and have positive
row totals. Percentages, concentration and influx are not accepted as count units
by the host admission profile.

Local and regional LOVE require one row each with identical taxon names/order.
Series require unique finite numeric coordinates and exact counterpart matching;
no implicit time interpolation or nearest-age pairing occurs. Dataframe index
labels do not determine sample pairing.

Parameters normalize unambiguous spellings to `fallspeed`, `ppe`, `ppe.error`,
with an explicit taxon column or taxon index. PPE is relative and strictly positive;
PPE standard error is finite/nonnegative; the current DISQOVER parameter domain
requires fallspeed in [0.01, 0.15] m/s. The host supplies PPE reference, units and
scientific-domain decisions. No taxon grouping or surrogate inference occurs here.

Ring distances (`inner`, `outer`, `mean`) and basin diameters are metres.
Optimized LOVE additionally requires `terrestrial` area and geometric `ring` area
in consistent square-metre units. Source-profile geometry quirks are declared in
compatibility notes; the host must choose this profile explicitly.

| Facade argument | Exact dimensions | Values/units |
| --- | --- | --- |
| REVEALS `ppe_draws` | `(samples, iterations, taxa)` | Relative PPE |
| REVEALS `pollen_draws` | `(samples, iterations, taxa)` | Nonnegative pollen draws under the declared count sampling profile |
| LOVE `regional_cover_draws` | `(repeats, taxa)` | Fractions only; closure tolerance is bounded by source per-taxon .001-percent rounding |
| Analytical LOVE `local_ppe_draws` | `(repeats, max_ring, taxa)` | Relative PPE |
| Analytical LOVE `local_count_draws` | `(repeats, max_ring, taxa)` | Nonnegative counts with positive totals |
| Optimized LOVE `local_count_draws` | `(repeats, taxa)` | Nonnegative counts with positive totals |
| Optimized LOVE `replay_candidates` | `(candidates, taxa)` | Candidate coordinates within the declared [0,1] bounds |

Optimized LOVE refuses supplied local PPE draws because this source profile does
not consume them. Analytical LOVE refuses optimizer candidates. Supplied arrays
are hashed in run provenance; seeds control NumPy streams and do not reproduce R
streams. Direct translated helper functions are private implementation/testing
surfaces and do not broaden these facade contracts.
