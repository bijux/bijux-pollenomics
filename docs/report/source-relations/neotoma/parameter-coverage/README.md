# Native pollen mass with literal LandClim parameter names

The [39-bin screen](bins.csv) consumes the same three Swedish Neotoma/EPD
datasets and 13 common age bins as the [held-out direct-pollen study](../../../pollen-reconstruction/swedish-direct-pollen/REPORT.md).
It reconstructs each full native `NISP` bin from the 16-taxon study matrix and
its enumerated excluded counts. Each denominator closes exactly. The parameter
names come from the [source-bound LandClim PPE/FSP candidate ledger](../parameter-candidates/README.md);
only literal names with a distinct native `NISP` concept are counted. Digitized
`NISP` concepts are not merged into the count denominator.

| Site | Native NISP | Literal-name NISP | Fraction | Direct-pollen 16-taxon fraction |
| --- | ---: | ---: | ---: | ---: |
| Abborrtjärnen | 88,004 | 81,970 | 93.1435% | 41.4958% |
| Bussjösjön | 56,450 | 10,752 | 19.0469% | 43.2223% |
| Bökesjön | 42,548 | 14,512 | 34.1074% | 57.1519% |

These fractions measure *text correspondence*, not LRA-ready pollen mass.
For example, `Alnus` is the largest unmatched native name at Abborrtjärnen
and Bussjösjön, while the parameter table names `Alnus glutinosa`. Bökesjön's
leading unmatched names are `Corylus`, `Alnus` and `Quercus`. Relabeling them
from genus to species or another parameter taxon would require a qualified
source decision. Even Abborrtjärnen's high literal fraction does not establish
its historical basin geometry, appropriate PPE/FSP profile, complete counting
denominator or LRA eligibility. All 39 bins remain **unadmitted for LRA**.
The [Bussjösjön basin review](../bussjosjon-basin/README.md) also records a
2.5264 km mismatch between a published lake-inventory point and the Neotoma
site point; its 3 ha inventory area cannot be assigned to these pollen bins.
The [author taxonomy and parameter review](../author-parameter-binding/README.md)
uses the authors' explicit synonym table and model inputs to resolve name and
parameter leads while retaining excluded and unmapped source mass.

The [report](report.json) pins every consumed path, byte count and SHA-256, the
separate direct-pollen response fraction, and the largest unmatched native
labels per site. Reproduce the output from the repository root with:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m \
  bijux_pollenomics_dev.source_completion.neotoma_parameter_mass \
  --repository . --output artifacts/jobs/neotoma-parameter-mass/replay
```

Compare `bins.csv` and `report.json` byte-for-byte with this directory. The
[producer](https://github.com/bijux/bijux-pollenomics/blob/828081f963fa574cd217c8f9c4c2cfcdb9397d52/packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma_parameter_mass.py)
refuses a changed source population, incomplete count denominator, changed
parameter review state or a nonzero LRA admission claim.


<!-- scientific-account-route:begin -->
## Scientific verification and limits

Native source hierarchy, chronology, units, taxon/count/parameter correspondence and unresolved physical/historical/review acceptance.

**Supported claim.** The 39-bin literal-name screen closes each native NISP pollen bin and records how much mass has a parameter-name lead.

**Unsupported claim.** A high spelling-match fraction is not an accepted taxon/PPE mapping, whole-pollen denominator or historical basin qualification.

**Actual verification performed.** Read the source-bound report/CSV and per-site native/literal fractions, retaining the separate 16-label direct-pollen response; no mapping or reconstruction.

**Remaining input or review.** Biological concept decisions, complete count support, parameter profile, core/chronology/basin identity and rights remain.

**Cause category.** Literal-name coverage addresses text correspondence only.

**Consequence.** Unmatched genus/species names cannot be relabeled silently to improve coverage.

**Precise next acceptance route.** Resolve source-specific concept-to-parameter mappings and complete scientific inputs before any numerical LRA request.

**Negative or refused result.** All 39 bins remain LRA-unadmitted; BUS retains the 2.5264 km coordinate conflict.

**Matched denominator.** 3 sites×13 bins=39; native NISP 88,004/56,450/42,548, of which literal 81,970/10,752/14,512; digitized units excluded.

- [Retained qualification evidence: docs/report/source-relations/neotoma/parameter-coverage/report.json](report.json) (SHA-256 `2e03bd0f134647c3549fd67be43d7dfa05589edf6bae67c701f3eaca861a9c55`).

- [Retained qualification evidence: docs/report/source-relations/neotoma/parameter-coverage/bins.csv](bins.csv) (SHA-256 `e4530cc679662aeaac9496451aa5a7164097ee625a7c28482c67dbfcc69d8bf6`).

- [Canonical scientific account: reports/science/source-cohorts.md](https://github.com/bijux/bijux-pollenomics/blob/main/reports/science/source-cohorts.md).

JSON and CSV retain their domain source and numerical manifests; a reading route does not rerun those producers. PDF exports retain their export inventory and source pins and must be regenerated when their canonical account changes.
<!-- scientific-account-route:end -->
