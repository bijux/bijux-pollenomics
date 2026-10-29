"""Evaluate thirty-taxon analytical LOVE against authenticated saved regional fractions."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import math
import os
from pathlib import Path
import re
import runpy
import sys
from typing import Any


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def number(value: Any) -> float | str:
    finite = float(value)
    if math.isnan(finite):
        return "NaN"
    if math.isinf(finite):
        return "Infinity" if finite > 0 else "-Infinity"
    return finite


def invoke(pair: dict[str, Any], api: Any, *, binding: Any = None) -> dict[str, Any]:
    """Call exactly one analytical workflow; dependency injection is for source controls."""
    import numpy as np
    import pandas as pd

    from bijux_pollenomics.analysis.lra.execution.adapter import _configuration
    from bijux_pollenomics_lra.models import configuration
    from bijux_pollenomics_lra.models.errors import ValidationError

    payload = pair["payload"]
    if binding is None:
        from types import SimpleNamespace

        binding = SimpleNamespace(api=configuration)
    reveals, love, coupled = _configuration(binding, payload)
    _, local_seed = np.random.SeedSequence(coupled.seed).spawn(2)
    love = replace(
        love,
        seed=int(local_seed.generate_state(1, dtype=np.uint32)[0]),
        retain_samples=True,
    )
    require(
        love.method == "analytical"
        and love.repeats == 1
        and love.max_ring == 2
        and love.stochastic is False,
        "Exact single deterministic analytical call required",
    )
    taxa = payload["taxa"]
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
            for r in payload["rings"]
        ]
    )
    regional = np.asarray([pair["regional_cover"]], dtype=float)
    require(
        regional.shape == (1, 30) and len(taxa) == 30 and len(rings) == 3,
        "Exact caller input dimensions required",
    )
    record = {
        "nominal_request_sha256": pair["nominal_request_sha256"],
        "analytical_request_sha256": pair["analytical_request_sha256"],
        "taxa": taxa,
        "raw_regional_cover": pair["regional_cover"],
        "regional_fraction_sum": float(regional.sum()),
        "local_seed": love.seed,
        "method": love.method,
        "API_calls": 1,
    }
    try:
        result = api(
            tables["local"],
            tables["regional"],
            params,
            rings,
            love,
            regional_cover_draws=regional,
        )
    except ValidationError as error:
        return record | {
            "status": "refused",
            "reason": str(error),
            "reason_code": getattr(error, "reason_code", None),
            "ring_dispositions": [
                {"ring_index": i, "status": "not_returned_request_refused"}
                for i in range(2)
            ],
        }
    require(result.method == "analytical", "Foreign workflow result refused")
    raw = result.samples["cover"]
    require(
        isinstance(raw, np.ndarray) and raw.shape == (1, 2, 30),
        "Complete native analytical sample array required",
    )
    require(
        list(result.cover["mean"].columns) == taxa
        and result.cover["mean"].shape == (2, 30),
        "Native analytical result taxon labels differ",
    )
    means = result.cover["mean"].to_numpy(dtype=float)
    require(
        np.array_equal(raw[0], means, equal_nan=True),
        "Single deterministic raw/mean output differs",
    )
    valid = result.auxiliary["valid_ring"]
    kreg, kloc = result.auxiliary["Kreg"], result.auxiliary["Kloc"]
    require(
        isinstance(valid, pd.Series)
        and valid.dtype.kind == "b"
        and valid.shape == (2,)
        and isinstance(kreg, pd.DataFrame)
        and isinstance(kloc, pd.DataFrame)
        and kreg.shape == kloc.shape == (2, 30)
        and list(kreg.columns) == list(kloc.columns) == taxa
        and valid.index.equals(result.cover["mean"].index)
        and kreg.index.equals(valid.index)
        and kloc.index.equals(valid.index),
        "Native labelled kernel/ring schema differs",
    )
    valid = valid.to_numpy()
    kreg, kloc = kreg.to_numpy(dtype=float), kloc.to_numpy(dtype=float)
    outcomes = []
    for i in range(2):
        values = raw[0, i]
        finite = bool(np.isfinite(values).all())
        closed = (
            finite
            and bool((values >= 0).all())
            and bool((values <= 1).all())
            and abs(float(values.sum()) - 1) <= 1e-9
        )
        outcomes.append(
            {
                "ring_index": i,
                "valid_ring": bool(valid[i]),
                "status": "unsupported_geometry"
                if not valid[i]
                else "closed_composition"
                if closed
                else "nonfinite_composition"
                if not finite
                else "invalid_composition",
                "raw_cover": [number(v) for v in values],
                "raw_sum": number(values.sum()),
                "negative_taxa": [taxa[j] for j, v in enumerate(values) if v < 0],
                "above_one_taxa": [taxa[j] for j, v in enumerate(values) if v > 1],
                "Kreg": [number(v) for v in kreg[i]],
                "Kloc": [number(v) for v in kloc[i]],
            }
        )
    return record | {"status": "returned", "ring_dispositions": outcomes}


def source_guard(protocol: dict[str, Any]) -> dict[str, Any]:
    directory = Path(__file__).absolute().parent
    names = {"replay.py", "inputs.py"}
    require(
        {p.name for p in directory.iterdir()} == names
        and len(protocol["execution_sources"]) == 2
        and {r["path"] for r in protocol["execution_sources"]} == names,
        "Exact two-source namespace required",
    )
    for row in protocol["execution_sources"]:
        path = directory / row["path"]
        require(
            path.is_file()
            and path.stat().st_nlink == 1
            and not any(p.is_symlink() for p in (path, *path.parents)),
            "Independent scientific source required",
        )
        raw = path.read_bytes()
        require(
            len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "Source changed before helper import",
        )
    return runpy.run_path(str(directory / "inputs.py"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("repository", "prepared", "protocol", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
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
    require(
        args.protocol.is_file()
        and args.protocol.stat().st_size <= 1024**2
        and args.protocol.stat().st_nlink == 1,
        "Bounded physical protocol required",
    )
    raw = args.protocol.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == args.protocol_sha256
        and re.fullmatch("[a-f0-9]{40}", args.candidate) is not None,
        "Exact protocol/current candidate required",
    )
    protocol = json.loads(raw)
    require(
        protocol["schema_version"] == "author-love-analytical-cohort-protocol.v1"
        and protocol["expected_new_scientific_calls"]
        == {
            "analytical_LOVE_calls": 39,
            "REVEALS_calls": 0,
            "optimizer_attempts": 0,
            "forward_calls": 0,
            "score_calls": 0,
        },
        "Finite analytical protocol required",
    )
    helper = source_guard(protocol)
    protocol = helper["decode"](raw)
    plan_raw = Path(os.environ["BIJUX_ATLAS_REGISTERED_PLAN"]).read_bytes()
    require(
        hashlib.sha256(plan_raw).hexdigest()
        == os.environ["BIJUX_ATLAS_REGISTERED_SHA256"],
        "Same registered plan buffer required",
    )
    plan = helper["decode"](plan_raw)
    source = next(r for r in protocol["execution_sources"] if r["path"] == "replay.py")
    require(
        plan["candidate"] == args.candidate
        and plan["repository"] == str(args.repository)
        and plan["scientific_mode"] == "analytical_saved_regional_cohort"
        and plan["scientific_arguments"] == sys.argv[1:]
        and plan["scientific_producer"]
        == {**source, "path": str(Path(__file__).absolute())}
        and plan["scientific_protocol"]
        == {
            "path": str(args.protocol),
            "sha256": args.protocol_sha256,
            "bytes": len(raw),
        }
        and plan["expected_new_scientific_calls"]
        == protocol["expected_new_scientific_calls"]
        and plan["maximum_new_attempts"] == 0
        and args.output == Path(plan["output"]) / "products"
        and args.output.is_relative_to(args.repository / "artifacts")
        and not args.output.exists(),
        "Exact registered analytical route/output required",
    )
    pairs, authority = helper["load"](args.repository, args.prepared, protocol)
    from bijux_pollenomics.analysis.lra.engine.discovery import (
        load_engine,
        required_capability_for_profile,
    )
    from bijux_pollenomics_lra.workflows.local import run_love

    binding = load_engine(
        required_capability=required_capability_for_profile(
            "disqover-0.9.14-source-compatible"
        )
    )
    records = [invoke(pair, run_love, binding=binding) for pair in pairs]
    require(
        len(records) == len({r["nominal_request_sha256"] for r in records}) == 39
        and sum(r["API_calls"] for r in records) == 39
        and sum(len(r["ring_dispositions"]) for r in records) == 78,
        "Complete39call/78ring disposition population required",
    )
    helper["load"](args.repository, args.prepared, protocol)
    args.output.mkdir(parents=True)

    def write(name: str, value: Any) -> dict[str, Any]:
        body = (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
        with (args.output / name).open("xb") as stream:
            stream.write(body)
        return {
            "path": name,
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
        }

    diagnostics = write(
        "analytical-diagnostics.json",
        {
            "schema_version": "author-love-analytical-diagnostics.v1",
            "candidate": args.candidate,
            "protocol_sha256": args.protocol_sha256,
            "records": records,
            "nominal_saved_authority": authority,
        },
    )
    write(
        "report.json",
        {
            "schema_version": "author-love-analytical-cohort.v1",
            "candidate": args.candidate,
            "protocol_sha256": args.protocol_sha256,
            "diagnostics": diagnostics,
            "unique_pairs": 39,
            "logical_ancestry": 2715,
            "contexts": 225,
            "sites": 15,
            "taxa": 30,
            "temporal_support": protocol["temporal_matching"],
            "calls": protocol["expected_new_scientific_calls"],
            "request_returns": sum(r["status"] == "returned" for r in records),
            "request_refusals": sum(r["status"] == "refused" for r in records),
            "scope": "Previously exposed TW5 development input diagnostic. No scoring, method choice, normalization/clipping, old31taxon outcome reuse, ecological accuracy, uncertainty interval or whole sweep admission.",
        },
    )
