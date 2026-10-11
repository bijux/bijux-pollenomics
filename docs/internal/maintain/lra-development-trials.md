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
frozen development-design and input hashes, canonical cohort-admission receipt,
scope and split, experiment, target, fold, enumerated candidate, configuration,
hyperparameters, seed, backend and budget. It records elapsed time, metrics or a
refusal/failure reason afterward.
A process killed before termination leaves an unfinished row visible to
`read_development_attempts`.

The ledger serializes only the short budget-check and start-record reservation.
Concurrent starters never wait or poll: one reserves atomically and another
receives `ledger_reservation_busy`, retaining the outer managed-job receipt for
an explicitly scheduled retry. This prevents parallel trials from jointly
exceeding the predeclared trial or declared compute-allocation budget. A killed
starter leaves an active-reservation marker or incomplete start as hidden
evidence. Readers ignore valid dead-owner evidence while continuing to expose
every complete row; the next starter archives that evidence before reserving.
Malformed reservation evidence refuses with
`ledger_reservation_recovery_required` for explicit inspection.

The outer managed job plan must name the trial plan, input files, exclusive score
output and ledger root in its read and output sets. Set the outer timeout above
the trial's own `timeout_seconds`. Give each run a unique `run_id`, score path
and managed-job ID. Keep credentials out of the explicit environment, arguments
and result file. The plan timeout must equal the attempt's declared seconds, and
the explicit environment must set `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
`MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS` and `VECLIB_MAXIMUM_THREADS` to the
declared thread count. These variables are reproducibility declarations, not an
operating-system CPU quota; candidate executables must be reviewed for
conformance. The runner enforces the wall timeout on the whole child process
group and terminates descendants when the direct child exits. No shell is used.

A trial plan has this shape; supply real absolute paths and SHA-256 values from
the frozen development input and design. The canonical design must enumerate
every permitted experiment/target, fold, candidate configuration, seed, metric,
selection rule and resource limit. Each candidate also binds the exact absolute
argument vector, working directory, explicit environment and executable-byte
SHA-256. The runner hashes an open executable descriptor, copies those descriptor
bytes to a private read-only file inside the trial directory, verifies the copy
digest and launches through that frozen file. Path replacement, symlink
retargeting or an in-place source write cannot select different launch bytes.
SIGTERM and SIGINT terminate the entire child process group before a terminal
interruption row is written. Its
cohort/scope/split hashes must match the attempt. The embedded cohort receipt is
canonical JSON produced by the evaluation cohort factory. Its current
`reviewer_authority` remains `declared_not_authenticated`, so recording it does
not authenticate a scientist or admit a real benchmark cohort:

```json
{
  "schema_version": "lra-development-trial.v2",
  "ledger_root": "/absolute/private/development-ledger",
  "timeout_seconds": 300,
  "spec": {
    "schema_version": "lra-development-attempt.v3",
    "run_id": "development-fold-01-setting-001",
    "development_design": {
      "canonical_design_json": "<canonical lra-development-design.v1 JSON>",
      "design_sha256": "<SHA-256 of those exact UTF-8 bytes>"
    },
    "input_hashes": {
      "split_manifest": "<64 lowercase hexadecimal digits>",
      "pollen": "<64 lowercase hexadecimal digits>"
    },
    "evaluation_binding": {
      "canonical_cohort_admission_json": "<canonical JSON string>",
      "cohort_admission_sha256": "<64 lowercase hexadecimal digits>",
      "scope_sha256": "<64 lowercase hexadecimal digits>",
      "split_manifest_sha256": "<same digest as input_hashes.split_manifest>",
      "split_kind": "predefined_block",
      "experiment": "all_target_pollen_withheld",
      "target": "pollen_composition"
    },
    "fold_id": "development-fold-01",
    "candidate_id": "declared-model-setting-001",
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
      "environment": {
        "MKL_NUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1"
      },
      "result_path": "/absolute/private/output/trial-result.json"
    }
  }
}
```

The child command writes a **separate** JSON result at `result_path` with exactly
`status`, `metrics` and `reason_code`. A completed result needs nonempty metrics
whose exact predeclared keys contain only finite numeric values, plus
`reason_code: null`; a refusal or failure needs a nonempty reason code. The ledger
supplies `elapsed_seconds` itself. The result path must be new and outside
the ledger root. Missing, invalid or misleading results, a nonzero command
claiming completion, startup failure and timeout produce terminal failure rows.
The start and result records are content-hashed and cannot be replaced by a
second invocation with the same run ID.

New starts accept only the v2 outer plan and v3 attempt schema. Existing v1/v2
ledger records remain readable as historical attempts, but they cannot be used
to start a new command. A new attempt must match one exact candidate in the
frozen design; undeclared folds, seeds, metrics or excessive per-trial budgets
refuse before the child starts. Valid experiment/target pairs are local-pollen-available
vegetation, all-target-pollen-withheld vegetation and all-target-pollen-withheld
pollen. Local pollen cannot be scored as a held-out pollen target.

Invoke the plan with `python -m bijux_pollenomics_dev.lra_validation.trial_runner
PLAN.json` **as the command of a managed job**. The direct behavioral fixture is
[`test_trial_runner.py`](../../../packages/bijux-pollenomics-dev/tests/lra_validation/test_trial_runner.py).
Do not score final-test observations through this development runner. This
mechanism records attempts; it does not admit source rows, certify a split,
select parameters, establish ecological accuracy or replace qualified review.
The canonical receipt explicitly retains
`scientific_acceptance=not_evaluated`; qualified returned review remains a
separate prerequisite for scientific use.
