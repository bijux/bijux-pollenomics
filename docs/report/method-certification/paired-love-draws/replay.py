"""Pair explicit local LOVE draws between source R and the native engine."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import warnings

import numpy as np

from bijux_pollenomics_lra.reconstruction.analytical import LOVEr
from bijux_pollenomics_lra.reconstruction.regional import REVEALSinR
from bijux_pollenomics_lra.resources.examples import load_love_example


REFERENCE_SHA256 = "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"
TOLERANCE = 3e-10


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--rscript", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve()
    library = args.library.resolve()
    rscript = args.rscript.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    here = Path(__file__).resolve().parent
    source = repository / "packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz"
    marker = library / "disqover/SOURCE_SHA256"
    assert (
        _sha(source) == marker.read_text(encoding="utf-8").strip() == REFERENCE_SHA256
    )

    local, regional, parameters, rings = load_love_example()
    taxa = list(local.columns[1:])
    ppe_table = parameters["ppes"]
    assert taxa == ppe_table["Taxon"].tolist()
    deterministic = REVEALSinR(
        regional,
        ppe_table,
        parameters["tBasinRegional"][0],
        parameters["dBasinRegional"][0],
        dwm=parameters["dwm"][0],
        n=1,
        stochastic=False,
        verbose=False,
    )
    regional_cover = (
        deterministic.filter(regex=r"\.mean$").iloc[0].to_numpy(dtype=float) / 100
    )
    valid_positions = [8, 9, 10]
    base_counts = local.iloc[0, 1:].to_numpy(dtype=int)
    total = int(base_counts.sum())
    base_ppe = ppe_table["ppe"].to_numpy(dtype=float)
    generator = np.random.default_rng(1729)
    ppe_draws = np.zeros((2, 10, 10), dtype=float)
    count_draws = np.zeros((2, 10, 10), dtype=int)
    for repetition in range(2):
        for ring in range(10):
            ppe_draws[repetition, ring] = base_ppe * (
                1 + 0.01 * (repetition + 1) * (ring + 1)
            )
            count_draws[repetition, ring] = generator.multinomial(
                total, base_counts / total
            )
    draws = {
        "schema_version": "paired-love-draws.1",
        "taxa": taxa,
        "valid_ring_positions": valid_positions,
        "regional_cover": regional_cover.tolist(),
        "local_ppe": ppe_draws.tolist(),
        "local_counts": count_draws.tolist(),
    }
    (output / "draws.json").write_text(
        json.dumps(draws, indent=2) + "\n", encoding="utf-8"
    )
    setup = {
        "pollen_columns": list(local.columns),
        "local": [float(x) for x in local.iloc[0]],
        "regional": [float(x) for x in regional.iloc[0]],
        "ppes": ppe_table.to_dict(orient="records"),
        "fallspeed": parameters["fallspeed"].to_dict(orient="records"),
        "rings": rings.to_dict(orient="records"),
        "params": {
            "dBasinRegional": float(parameters["dBasinRegional"][0]),
            "dBasinLocal": float(parameters["dBasinLocal"][0]),
            "tBasinRegional": parameters["tBasinRegional"][0],
            "dwm": parameters["dwm"][0],
        },
    }
    (output / "setup.json").write_text(
        json.dumps(setup, indent=2) + "\n", encoding="utf-8"
    )
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice encountered")
        native = LOVEr(
            local,
            regional,
            parameters,
            rings,
            10,
            repeats=2,
            stochastic=True,
            regional_cover_draws=np.broadcast_to(regional_cover, (2, 10)).copy(),
            local_ppe_draws=ppe_draws,
            local_count_draws=count_draws,
        )
    python_rows: list[dict[str, object]] = []
    for field, frame in (
        ("Mean", native["Mean"]),
        ("Q10", native["Q10"]),
        ("Q90", native["Q90"]),
        ("SD", native["SD"]),
    ):
        values = frame.to_numpy(dtype=float)
        for ring in range(10):
            for index, taxon in enumerate(taxa):
                value = values[ring, index]
                python_rows.append(
                    {
                        "field": field,
                        "ring": ring + 1,
                        "taxon": taxon,
                        "value": "" if np.isnan(value) else format(value, ".17g"),
                    }
                )
    with (output / "python-values.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=list(python_rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(python_rows)

    r_path = output / "r-values.csv"
    environment = dict(
        os.environ, R_LIBS_USER=str(library), TZ="UTC", LANG="C", LC_ALL="C"
    )
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        environment[key] = "1"
    completed = subprocess.run(
        [
            str(rscript),
            "--vanilla",
            str(here / "replay.R"),
            str(output / "draws.json"),
            str(output / "setup.json"),
            str(
                repository
                / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/r_support.R"
            ),
            str(r_path),
            str(output / "r-session.txt"),
        ],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    (output / "r-stdout.log").write_text(completed.stdout, encoding="utf-8")
    (output / "r-stderr.log").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode:
        raise RuntimeError(
            f"Source R LOVEr exited {completed.returncode}; see retained logs"
        )
    r_rows = list(csv.DictReader(r_path.open(encoding="utf-8")))
    assert len(r_rows) == len(python_rows) == 400
    passed = 0
    maximum = 0.0
    for r_row, py_row in zip(r_rows, python_rows, strict=True):
        assert all(r_row[key] == str(py_row[key]) for key in ("field", "ring", "taxon"))
        r_value = r_row["value"]
        py_value = str(py_row["value"])
        if r_value == "" or py_value == "":
            assert r_value == py_value == ""
            continue
        error = abs(float(r_value) - float(py_value))
        maximum = max(maximum, error)
        assert error <= TOLERANCE
        passed += 1
    assert passed == 120
    input_names = [
        "packages/bijux-pollenomics-lra/vendor/disqover_0.9.14.tar.gz",
        "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/r_support.R",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/analytical.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/regional.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexamplePollen.json",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexampleParams.json",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/resources/data/LOVEexampleRings.json",
        str((here / "replay.R").relative_to(repository)),
        str((here / "replay.py").relative_to(repository)),
    ]
    report = {
        "schema_version": "paired-love-draws-result.1",
        "status": "passed",
        "source_package": "disqover 0.9.14",
        "rscript_sha256": _sha(rscript),
        "input_sha256": {name: _sha(repository / name) for name in input_names},
        "paired_finite_values": passed,
        "paired_missing_values": 400 - passed,
        "maximum_absolute_difference": maximum,
        "tolerance_absolute": TOLERANCE,
        "output_sha256": {
            name: _sha(output / name)
            for name in (
                "draws.json",
                "setup.json",
                "python-values.csv",
                "r-values.csv",
                "r-session.txt",
            )
        },
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
