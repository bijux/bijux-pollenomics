# R parity harness

This directory separates four claims that must not be conflated:

1. **Python deterministic tests** check Python equations, shapes, validation,
   output contracts, and workflows.
2. **Stored-model parity** evaluates and independently refits all 45 LSM
   curves serialized by R in the supplied DISQOVER archive.
3. **Live R parity** executes the exact installed DISQOVER 0.9.14 package and
   compares its outputs with independently computed Python expectations.
4. **Scientific validation** compares reconstructed vegetation with external
   observations. It is outside translation parity and is not claimed here.

Prepare the live suite without executing R:

```bash
python tests/reference/lra_oracle/run_live_r.py --prepare-only
```

Install and execute the actual reference:

```bash
python tests/reference/lra_oracle/install_reference.py
python tests/reference/lra_oracle/run_live_r.py
```

Exit code `2` means blocked, not passed. The runner verifies package version and
the exact bundled archive SHA-256 before executing cases.

The suite uses supplied Monte Carlo draws and fixed-candidate optimizer replay
where needed. Equal integer seeds across R and NumPy are not treated as paired
RNG evidence. Candidate replay validates the objective and wrapper around a
common candidate set; it does not assert identical convergence trajectories for
SciPy differential evolution and RcppDE/DEoptim.
