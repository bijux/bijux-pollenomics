---
title: Recorded LRA Development Trials
audience: maintainer
type: how-to
status: canonical
owner: bijux-pollenomics-dev-docs
last_reviewed: 2026-09-22
---

# Record an LRA development trial

Use `bijux_pollenomics_dev.lra_validation.trial_runner` inside the repository's
managed background-job runner for each **development-fold** attempt. The trial
runner reserves an append-only ledger row before starting its child command.
It records the exact argument vector, working directory, explicit environment,
policy hash, input hashes, target, fold, model, configuration, hyperparameters,
seed, backend and budget. It records elapsed time, metrics or a refusal/failure
reason afterward. A process killed before termination leaves an unfinished row
visible to `read_development_attempts`.

The outer managed job plan must name the trial plan, input files, exclusive score
output and ledger root in its read and output sets. Set the outer timeout above
the trial's own `timeout_seconds`. Give each run a unique `run_id`, score path
and managed-job ID. Keep credentials out of the explicit environment, arguments
and result file. No shell is used for the child command.

A trial plan has this shape; supply real absolute paths and SHA-256 values from
the frozen development input and reviewed policy:

```json
{
  "schema_version": "lra-development-trial.v1",
  "ledger_root": "/absolute/private/development-ledger",
  "timeout_seconds": 300,
  "spec": {
    "run_id": "development-fold-01-setting-001",
    "policy_sha256": "<64 lowercase hexadecimal digits>",
    "input_hashes": {
      "folds": "<64 lowercase hexadecimal digits>",
      "pollen": "<64 lowercase hexadecimal digits>"
    },
    "target": "withheld_pollen_prediction",
    "fold_id": "development-fold-01",
    "model": "declared-model-id",
    "configuration": {
      "method": "declared-method",
      "transport": "declared-transport",
      "taxon_profile": "reviewed-taxon-profile",
      "ppe_profile": "reviewed-ppe-profile",
      "basin_scenario": "declared-basin-scenario",
      "spatial_support": "declared-spatial-support",
      "temporal_support": "declared-temporal-support",
      "uncertainty": "declared-uncertainty"
    },
    "hyperparameters": {"radius_m": 5000},
    "seed": 7,
    "backend": "installed-backend-and-version",
    "budget": {"seconds": 300, "threads": 1},
    "invocation": {
      "argv": ["/absolute/path/to/executable", "argument"],
      "cwd": "/absolute/private/frozen-candidate",
      "environment": {"OMP_NUM_THREADS": "1"},
      "result_path": "/absolute/private/output/trial-result.json"
    }
  }
}
```

The child command writes a **separate** JSON result at `result_path` with exactly
`status`, `metrics` and `reason_code`. A completed result needs nonempty metrics
and `reason_code: null`; a refusal or failure needs a nonempty reason code. The
ledger supplies `elapsed_seconds` itself. The result path must be new and outside
the ledger root. Missing, invalid or misleading results, a nonzero command
claiming completion, startup failure and timeout produce terminal failure rows.
The start and result records are content-hashed and cannot be replaced by a
second invocation with the same run ID.

Invoke the plan with `python -m bijux_pollenomics_dev.lra_validation.trial_runner
PLAN.json` **as the command of a managed job**. The direct behavioral fixture is
[`test_trial_runner.py`](../../../packages/bijux-pollenomics-dev/tests/lra_validation/test_trial_runner.py).
Do not score final-test observations through this development runner. This
mechanism records attempts; it does not admit source rows, certify a split,
select parameters, establish ecological accuracy or replace qualified review.
