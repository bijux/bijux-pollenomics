# Supported facade input contracts

The facade accepts pandas pollen frames whose first column is a **finite numeric
pairing coordinate** and remaining columns are unique pollen taxon names. It is
not a string sample ID and does not by itself imply BP, CE, depth or chronology.
The host retains raw sample/source identities and admits a governed coordinate
axis before calling this engine. Counts are finite, nonnegative and have positive
row totals. Numerical measurement arrays and physical configuration scalars must
be real-valued. Native complex dtypes and object-held complex scalars, including
nested zero-dimensional object arrays, are refused before float conversion.
This includes values with a zero imaginary component; an imaginary component is
never silently discarded. Percentages, concentration and influx are not accepted
as count units by the host admission profile.

Direct GPM distances and parameters, and dispersal-factor basin diameters, also
reject unresolved masks, complex values and booleans before conversion. GPM
parameters remain strictly positive and finite. This tightens the direct
kernel API, which previously accepted boolean values and could discard masks or
imaginary components. Fully unmasked and real numeric inputs retain their
distance or diameter shape; this does not change the scientific domain of a result.
GPM parameters are normalized as scalars: singleton array parameters no longer
produce array-shaped results, and scalar numeric strings may be accepted.

Local and regional LOVE require one row each with identical taxon names/order.
Series require unique finite numeric coordinates and exact counterpart matching;
no implicit time interpolation or nearest-age pairing occurs. Dataframe index
labels do not determine sample pairing.

Parameters normalize unambiguous spellings to `fallspeed`, `ppe`, `ppe.error`,
with an explicit taxon column or taxon index. PPE is relative and strictly positive;
PPE standard error is finite/nonnegative; the current DISQOVER parameter domain
requires fallspeed in [0.01, 0.15] m/s. The host supplies PPE reference, units and
scientific-domain decisions. No taxon grouping or surrogate inference occurs here.

## Expanded LandClim GPM admission

The explicit `fall_speed_profile="landclimii-2016-gpm-neutral-analytical-v1"`
accepts finite fall speeds in **[0.006, 0.15] m/s**, preserving the nominal
Filipendula value of 0.006 without rounding or clamping. Its existing identifier
is retained for both supported operations:

- Regional **REVEALS**, for lake or peatland basins, with
  `distance_weighting="gpm neutral"`.
- **Analytical LOVE**, with the same distance weighting and supplied,
  taxon-aligned `regional_cover_draws` containing closed fractions. Missing or
  invalid draws are refused.

This is an explicit Python admission extension. The default profile remains
[0.01, 0.15] m/s; optimized LOVE and LSM do not gain the expanded range.
Both supported operations require finite, strictly positive deposition factors;
the range alone does not guarantee valid basin, ring or cutoff geometry. Source
GPM diameter/radius conventions are preserved. In particular, the lake LOESS
curve has a finite fitted distance domain: cutoffs above 1,000,000 m produce
undefined source factors and the maintained facade refuses them. The source
peatland path omits its outer-tail term above that cutoff; these are distinct
source behaviors, not extrapolation guarantees.

### Numerical reference and provenance

The exact retained [DISQOVER 0.9.14 archive](../../vendor/disqover_0.9.14.tar.gz)
(SHA-256 `ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c`)
contains a `checkREVEALS` wrapper gate that refuses speeds below 0.01 m/s.
Its GPM and B1 helpers can separately evaluate 0.006 m/s. Expanded-domain
REVEALS therefore records compatibility mode
`landclimii-gpm-neutral-expanded-regional-v1` and a `fall_speed_contract`
parameter dictionary:

| Field | Meaning |
| --- | --- |
| `operation` | `regional-reveals` |
| `domain_m_s` | Admitted finite interval `[0.006, 0.15]`, in m/s |
| `distance_weighting` | Required `gpm neutral` model |
| `source_wrapper_domain_m_s` | Original wrapper interval `[0.01, 0.15]`, in m/s |
| `reference_scope` | `disqover-0.9.14-gpm-kernel-and-b1` |
| `wrapper_admission` | `expanded-python-domain`, distinct from original wrapper admission |

The reference package/version/archive fields identify equation and kernel
ancestry; they do not certify original-wrapper acceptance of the expanded input.
The default regional manifest keeps its existing compatibility identity.

Run manifest input hashes use the existing canonical object representation, not
a byte-for-byte serialization of the original input. DataFrame column and index
labels, Series index labels and names, and mapping keys are converted to strings
for that representation. Consequently, distinct source labels with the same
string form, such as integer `0` and string `"0"` as DataFrame index labels,
can have the same input hash. This does not imply that their source records are
identical. Preserve and authenticate original source bytes separately when label
types matter; do not use the engine input digest alone as evidence of typed label
identity. The current run manifest does not provide a typed-label hash profile.
Introducing one requires an explicitly versioned identity contract and continued
interpretation of historical manifests under their original representation.

The [generated R control](../../tests/reference/regional_profiles/landclim_gpm_neutral.R)
and [retained expectations](../../tests/reference/regional_profiles/landclim_gpm_neutral.json)
identify the exact two upstream source programs, generator hash and native R
4.6.2 runtime. No package dataset or observed pollen counts are used. The control
compares 72 deposition cases: 60 finite results and 12 undefined lake factors.
It also evaluates 48 deterministic two-taxon B1 cases (96 cover cells) and
confirms that the unchanged original wrapper refuses 0.006 m/s. Speeds are
0.006, 0.01, 0.024 and 0.15 m/s; basin diameters are 10, 100 and 2,000 m;
cutoffs are 100,000, 1,000,000 and 1,000,001 m for deposition, with only the
first two used for finite cover comparisons. Fixed prospective tolerances are
`1e-10` relative plus `1e-12` absolute for factors, and `1e-12` percentage points
for source-rounded cover.

To rerun the generated control from the repository root, verify the archive
hash above, extract only the two named source programs and choose fresh output
paths under `artifacts/`:

```sh
mkdir -p artifacts/landclim-gpm-reference/code artifacts/landclim-gpm-reference/output
tar -xzf packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz \
  -C artifacts/landclim-gpm-reference/code --strip-components=2 \
  disqover/R/REVEALS.R disqover/R/dispersal_models.R
R_DEFAULT_PACKAGES=stats,utils Rscript --vanilla \
  packages/bijux-pollenomics-lra/tests/reference/regional_profiles/landclim_gpm_neutral.R \
  artifacts/landclim-gpm-reference/code artifacts/landclim-gpm-reference/output
```

The retained expectations record both source-program hashes. The generator
sources those programs directly and supplies fixed PPE/count callbacks;
installation of DISQOVER or loading its example datasets is unnecessary.

These are selected kernel/B1 numerical comparisons, not verification of every
geometry, stochastic R-stream identity, analytical LOVE at every ring,
historical LandClim software identity or ecological applicability. The named
analytical LOVE contract still requires authenticated external regional draws
and valid positive deposition geometry.

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
streams. The four seeded configuration types preserve accepted integer seeds
exactly, including values above the binary64 exact-integer range. Existing
singleton seed sequences accepted by NumPy retain their representation and
provenance. A mutable sequence remains caller-owned; changing it after config
construction changes the later entropy and can make it invalid. Previously
accepted integral float, numeric-string, or singleton values that NumPy could not use are normalized to their exact nonnegative
integer value at construction; a string whose exact value is fractional is
refused even if binary64 rounding would hide the fraction. This normalization
changes the recorded representation for those formerly non-executable inputs.
Direct translated helper functions are private implementation/testing surfaces
and do not broaden these facade contracts.

## Owned REVEALS inputs

`run_reveals(..., input_ownership="snapshot")` captures a bounded set of inputs
before reconstruction. It copies ordinary DataFrames with plain or range axes,
immutable scalar labels and cells, ordinary numeric arrays or scalar sequences
of draws, and the configuration seed. Python-backed pandas string columns are
supported. Unsupported objects, masked arrays and other pandas extension or
index types are refused in this opt-in profile. The
calculation and run manifest use the captured values; the manifest records the
snapshot choice. Capture is sequential, not an atomic snapshot of concurrently
changing inputs. Callers must prevent mutation during capture if a coherent
multi-input instant matters. The returned manifest and results are not an
external execution attestation. The legacy canonical hashes still stringify
labels and do not attest original source bytes or typed label identity. The
default `input_ownership="borrowed"` retains the existing behavior.

## Multisite input capture

The historical multisite REVEALS workflow revalidates and copies its standard
`MultisiteRevealsInput` at operation entry, then uses the captured values for
calculation and its run manifest. Bootstrap site indices are validated after
copying. Capture is sequential and does not establish an atomic instant across
caller-owned inputs; callers must keep them stable during capture and keep
the configuration stable throughout the run. The workflow requires the standard
input class and ordinary Python or NumPy string values for site, bin, taxon and
basin identities. Subclasses and custom string-like objects
previously accepted by construction are refused at operation entry. These checks
do not establish source-byte custody or scientific accuracy.

## Paired regional extent

`LRAConfig` requires `reveals.region_cutoff_m=100000` for analytical LOVE,
whether regional draws are coupled or independently recomputed. Historical
analytical `Kreg` integrates to 100 km even when regional cover is supplied.
Uncoupled optimized LOVE also requires this cutoff because its internal
REVEALS estimate uses 100 km. Incompatible paired configurations are refused
before either numerical stage runs; the equations and source geometry are
unchanged. Standalone REVEALS retains its configurable cutoff.

Coupled optimized LOVE accepts other REVEALS cutoffs: it consumes the supplied
regional draws and derives deposition from the explicitly supplied ring
geometry and terrestrial fractions. Its regional background estimation domain
and ring deposition domain have different roles and need not be identical.
This support does not establish that regional vegetation is representative of
the local site's background; that scientific assumption still needs admission.

Paired and local child manifests record `effective_regional_extent`: the
REVEALS cutoff, LOVE background source and cutoff, and either the historical
analytical deposition cutoff or the optimized ring boundaries and local ring
count. The latter identifies the changing local/regional ring partition for
each evaluated local extent; it does not invent a common fixed ring cutoff.

## Conditional observation interval verification

`PollenObservationDraws` checks its canonical identity and structural constraints
when read. Those checks alone do not establish that saved predictive interval
bounds match the declared equal-tail binomial profile. Call
`validate_predictive_intervals()` to check that relationship before interpreting
the intervals. Small supports use exact binary64 probability arithmetic; larger
nondegenerate supports require the recorded SciPy version to match the installed
version and refuse unresolved numerical boundaries. Matching version strings do
not authenticate a provider build. Degenerate zero/one probabilities are checked
exactly without SciPy. The host coverage readers require this verification; an
older engine without the method cannot qualify their intervals. Verification does
not authenticate the result, replay random draws, or establish empirical coverage.
