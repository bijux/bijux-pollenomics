"""Record the declared legacy optimized-wrapper domain refusal on saved inputs."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import sys
from typing import Any

EXPECTED_CALLS = {
    "LOVE_API_calls": 39,
    "optimizer_attempts": 0,
    "kernel_calls": 0,
    "REVEALS_calls": 0,
    "forward_calls": 0,
    "score_calls": 0,
}
REFUSAL = "unsupported_source_ring_dimensions"


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(detail)


def checked(root: Path, row: dict[str, Any]) -> bytes:
    path: Path = root / row["path"]
    require(
        ".." not in Path(row["path"]).parts
        and path.is_file()
        and path.stat().st_nlink == 1
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Independent declared scientific file required",
    )
    raw = path.read_bytes()
    require(
        type(row["bytes"]) is int
        and len(raw) == row["bytes"]
        and hashlib.sha256(raw).hexdigest() == row["sha256"],
        "Scientific source/input identity changed: " + str(path),
    )
    return raw


def read_inputs(
    repository: Path, prepared: Path, protocol: dict[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reuse admitted input joins, reconstruct nominal hashes, then change profile."""
    from bijux_pollenomics.analysis.lra.inputs.validation import validate_request

    row = protocol["input_reader"]
    checked(repository, row)
    reader = runpy.run_path(str(repository / row["path"]))
    original, authority = reader["load"](repository, prepared, protocol)
    require(len(original) == 39, "Complete original39 request population required")
    pairs = []
    for pair in original:
        nominal = deepcopy(pair["payload"])
        nominal["method_profile"] = "ring-taxon-preserving"
        nominal["configuration"]["love"] = deepcopy(protocol["nominal_love"])
        require(
            validate_request(nominal, input_root=prepared).sha256
            == pair["nominal_request_sha256"],
            "Original nominal payload cannot be reconstructed exactly",
        )
        changed = deepcopy(nominal)
        changed["method_profile"] = "disqover-0.9.14-source-compatible"
        love = changed["configuration"]["love"]
        love["optimized_profile"] = "disqover-0.9.14-source"
        # This backend is required by the legacy profile's public configuration;
        # its source dimension guard must refuse before optimizer construction.
        love["optimizer_backend"] = "scipy.differential_evolution"
        validated = validate_request(changed, input_root=prepared)
        require(
            validated.sha256 != pair["nominal_request_sha256"],
            "Distinct legacy identity required",
        )
        pairs.append(
            {
                "nominal_request_sha256": pair["nominal_request_sha256"],
                "legacy_request_sha256": validated.sha256,
                "payload": validated.payload(),
                "regional_cover": pair["regional_cover"],
            }
        )
    require(
        len({row["legacy_request_sha256"] for row in pairs}) == 39,
        "Unique legacy requests required",
    )
    return pairs, authority


def invoke(pair: dict[str, Any], api: Any, *, binding: Any = None) -> dict[str, Any]:
    """Attempt the native wrapper once; preserve only its exact declared refusal."""
    import numpy as np
    import pandas as pd

    from bijux_pollenomics.analysis.lra.execution.adapter import _configuration
    from bijux_pollenomics_lra.models import configuration
    from bijux_pollenomics_lra.models.errors import ValidationError

    payload = pair["payload"]
    if binding is None:
        from types import SimpleNamespace

        binding = SimpleNamespace(api=configuration)
    _, love, coupled = _configuration(binding, payload)
    _, local_seed = np.random.SeedSequence(coupled.seed).spawn(2)
    love = replace(
        love,
        seed=int(local_seed.generate_state(1, dtype=np.uint32)[0]),
        retain_samples=True,
    )
    taxa, rings_input = payload["taxa"], payload["rings"]
    require(
        len(taxa) == len(set(taxa)) == 30
        and len(rings_input) == 3
        and love.method == "optimized"
        and love.optimized_profile == "disqover-0.9.14-source"
        and love.optimizer_backend == "scipy.differential_evolution"
        and love.max_ring == 2
        and love.repeats == 1
        and love.stochastic is False
        and love.distance_weighting == "gpm neutral"
        and love.fall_speed_profile == "disqover-0.9.14-wrapper-v1",
        "Exact nominal legacy-wrapper profile required",
    )
    require(
        rings_input[0]["ring_area_m2"] > 0
        and rings_input[0]["terrestrial_area_m2"] > 0,
        "Declared nonzero first-local-ring domain required",
    )
    tables = {
        role: pd.DataFrame(
            [[s["coordinate"], *s["counts"]] for s in payload[role]["samples"]],
            columns=["coordinate", *taxa],
        )
        for role in ("local", "regional")
    }
    params = pd.DataFrame(
        [
            {
                "species": r["taxon"],
                "fallspeed": r["fallspeed_m_s"],
                "ppe": r["ppe"],
                "ppe.error": r["ppe_sd"],
            }
            for r in payload["parameters"]
        ]
    )
    rings = pd.DataFrame(
        [
            {
                "inner": r["inner_m"],
                "outer": r["outer_m"],
                "mean": r["mean_m"],
                "ring": r["ring_area_m2"],
                "terrestrial": r["terrestrial_area_m2"],
            }
            for r in rings_input
        ]
    )
    regional = np.asarray([pair["regional_cover"]], dtype=float)
    require(regional.shape == (1, 30), "Exact paired regional fraction axis required")
    record = {
        "nominal_request_sha256": pair["nominal_request_sha256"],
        "legacy_request_sha256": pair["legacy_request_sha256"],
        "taxa": taxa,
        "raw_regional_cover": pair["regional_cover"],
        "local_seed": love.seed,
        "configuration": love.as_dict(),
        "API_calls": 1,
    }
    try:
        api(
            tables["local"],
            tables["regional"],
            params,
            rings,
            love,
            regional_cover_draws=regional,
        )
    except ValidationError as exc:
        if exc.reason_code != REFUSAL:
            raise
        return record | {
            "status": "refused",
            "reason_code": exc.reason_code,
            "detail": str(exc),
            "ring_dispositions": [
                {"ring_index": i, "status": "not_returned_request_refused"}
                for i in range(2)
            ],
        }
    raise RuntimeError(
        "Declared source dimension refusal did not occur; optimizer result is not admitted"
    )


def run(
    pairs: list[dict[str, Any]], api: Any, *, binding: Any = None
) -> list[dict[str, Any]]:
    require(
        len(pairs)
        == len({p["nominal_request_sha256"] for p in pairs})
        == len({p["legacy_request_sha256"] for p in pairs})
        == 39,
        "Complete distinct39 request population required",
    )
    return [invoke(pair, api, binding=binding) for pair in pairs]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "prepared", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    require(
        all(
            p.is_absolute()
            and ".." not in p.parts
            and not any(q.is_symlink() for q in (p, *p.parents))
            for p in (args.repository, args.prepared, args.protocol, args.output)
        ),
        "Absolute independent scientific paths required",
    )
    protocol_raw = checked(
        Path("/"),
        {
            "path": str(args.protocol),
            "sha256": args.protocol_sha256,
            "bytes": args.protocol.stat().st_size,
        },
    )
    require(
        len(protocol_raw) <= 1024**2
        and re.fullmatch("[a-f0-9]{40}", args.candidate) is not None,
        "Bounded protocol/current candidate required",
    )
    protocol = json.loads(protocol_raw)
    require(
        protocol["schema_version"] == "legacy-optimized-wrapper-protocol.v1"
        and protocol["expected_new_scientific_calls"] == EXPECTED_CALLS,
        "Finite legacy diagnostic protocol required",
    )
    source = next(r for r in protocol["execution_sources"] if r["path"] == "replay.py")
    directory = Path(__file__).absolute().parent
    require(
        {p.name for p in directory.iterdir() if p.name != "__pycache__"}
        == {"replay.py"}
        and len(protocol["execution_sources"]) == 1,
        "Exact scientific source namespace required",
    )
    checked(directory, source)
    plan_raw = Path(os.environ["BIJUX_ATLAS_REGISTERED_PLAN"]).read_bytes()
    require(
        hashlib.sha256(plan_raw).hexdigest()
        == os.environ["BIJUX_ATLAS_REGISTERED_SHA256"],
        "Same registered plan buffer required",
    )
    plan = json.loads(plan_raw)
    require(
        plan["candidate"] == args.candidate
        and plan["repository"] == str(args.repository)
        and plan["scientific_mode"] == "legacy_optimized_wrapper_diagnostic"
        and plan["scientific_arguments"] == sys.argv[1:]
        and plan["scientific_producer"]
        == {**source, "path": str(Path(__file__).absolute())}
        and plan["scientific_protocol"]
        == {
            "path": str(args.protocol),
            "sha256": args.protocol_sha256,
            "bytes": len(protocol_raw),
        }
        and plan["expected_new_scientific_calls"] == EXPECTED_CALLS
        and plan["maximum_new_attempts"] == 0
        and args.output == Path(plan["output"]) / "products"
        and args.output.is_relative_to(args.repository / "artifacts")
        and not args.output.exists(),
        "Exact registered diagnostic route/output required",
    )
    pairs, authority = read_inputs(args.repository, args.prepared, protocol)
    from bijux_pollenomics.analysis.lra.engine.discovery import load_engine
    from bijux_pollenomics_lra.workflows.local import run_love

    binding = load_engine()
    records = run(pairs, run_love, binding=binding)
    read_inputs(args.repository, args.prepared, protocol)
    args.output.mkdir(parents=True)
    diagnostics = {
        "schema_version": "legacy-optimized-wrapper-dispositions.v1",
        "candidate": args.candidate,
        "protocol_sha256": args.protocol_sha256,
        "records": records,
        "nominal_saved_authority": authority,
    }
    raw = (
        json.dumps(diagnostics, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode()
    (args.output / "dispositions.json").write_bytes(raw)
    report = {
        "schema_version": "legacy-optimized-wrapper-diagnostic.v1",
        "candidate": args.candidate,
        "protocol_sha256": args.protocol_sha256,
        "dispositions": {
            "path": "dispositions.json",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
        },
        "unique_requests": 39,
        "request_refusals": 39,
        "ring_dispositions": 78,
        "logical_ancestry": 2715,
        "contexts": 225,
        "sites": 15,
        "taxa": 30,
        "calls": EXPECTED_CALLS,
        "temporal_support": protocol["temporal_matching"],
        "selection_stratum": "not_ranked",
        "scope": "Previously exposed development input diagnostic of the named legacy source domain. No optimizer success, reconstruction, prediction, scoring, method selection, ecological accuracy, calibrated uncertainty or whole model-development acceptance.",
    }
    (args.output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


if __name__ == "__main__":
    main()
