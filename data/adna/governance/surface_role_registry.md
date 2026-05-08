# Animal ancient-DNA governance roles

The governance tree carries three distinct responsibilities so recovery plumbing, cross-species review, and publication accounting do not blur into one vague bucket.

| Role | Path pattern | Responsibility |
| --- | --- | --- |
| Source recovery | `data/adna/governance/source_library/**` | capture archive metadata, project dossiers, paper manifests, and per-project recovery evidence before species normalization |
| Cross-species review | `data/adna/governance/*.json` | publish truth, caveats, coverage posture, and evidence-honesty surfaces that compare projects across species |
| Publication accounting | `data/adna/governance/*product*.json` | state what the repository is allowed to ship and how publication surfaces are audited against foundation truth |

## Examples

- Source recovery: `data/adna/governance/source_library/project_registry.json`
- Cross-species review: `data/adna/governance/animal_sample_foundation_truth.json`
- Publication accounting: `data/adna/governance/shipped_product_audit.json`
