"""Diagnose the fixed-input LOVE admissibility boundary from saved intermediates."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import csv
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import stat
from typing import Any, NotRequired, TypedDict, cast

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.workflow import (
    read,
    require,
)

TAXA = ("Betula", "Ulmus")


class TaxonAdmissibility(TypedDict):
    """Exact interval quantities for one ordered taxon in the saved equation."""

    taxon: str
    ppe_adjusted_local_fraction: Fraction
    lower_admissible_bound: Fraction
    upper_admissible_bound: Fraction
    lower_margin: Fraction
    upper_margin: Fraction
    implied_cover: Fraction
    below_lower: bool
    above_upper: bool
    saved_native_cover: NotRequired[str]
    saved_minus_rational_cover: NotRequired[Fraction]
    native_range_refusal: NotRequired[bool]


class CompositionAdmissibility(TypedDict):
    """Fixed correction scale and its complete two-taxon feasibility result."""

    denominator_D: Fraction
    scale_T: Fraction
    taxa: list[TaxonAdmissibility]
    conditional_nonnegative_cover_exists: bool


def number(value: object) -> Fraction:
    if isinstance(value, Fraction):
        return value
    require(type(value) in (int, float, str), "Expected a finite numeric cell")
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("Expected a finite numeric cell") from exc


def algebra(
    counts: Sequence[object],
    ppe: Sequence[object],
    regional: Sequence[object],
    kloc: Sequence[object],
    kreg: Sequence[object],
) -> CompositionAdmissibility:
    """Return the exact affine preimage of a nonnegative unit-sum cover vector.

    Arithmetic interprets saved decimal cells as rationals. It is an independent
    algebraic diagnostic, not a replay of native floating-point evaluation.
    """
    require(
        all(len(values) == 2 for values in (counts, ppe, regional, kloc, kreg)),
        "Two-taxon axes required",
    )
    n, a, c, local, distant = (
        [number(value) for value in values]
        for values in (counts, ppe, regional, kloc, kreg)
    )
    require(
        all(value >= 0 for value in n + c),
        "Counts and regional cover must be nonnegative",
    )
    require(all(value > 0 for value in a), "PPE must be positive")
    require(
        all(value >= 0 for value in local + distant),
        "Saved deposition factors must be nonnegative",
    )
    weights = [count / alpha for count, alpha in zip(n, a, strict=True)]
    total_weight = cast(Fraction, sum(weights))
    require(total_weight > 0, "Local count/PPE total must be positive")
    q = [value / total_weight for value in weights]
    denominator = cast(Fraction, sum(x * y for x, y in zip(c, local, strict=True)))
    require(denominator > 0, "Fixed regional correction denominator must be positive")
    background = [x * y for x, y in zip(c, distant, strict=True)]
    scale = denominator + sum(background)
    require(scale > 0, "Fixed affine scale must be positive")
    result: list[TaxonAdmissibility] = []
    for taxon, fraction, correction in zip(TAXA, q, background, strict=True):
        lower = correction / scale
        upper = (denominator + correction) / scale
        result.append(
            {
                "taxon": taxon,
                "ppe_adjusted_local_fraction": fraction,
                "lower_admissible_bound": lower,
                "upper_admissible_bound": upper,
                "lower_margin": fraction - lower,
                "upper_margin": upper - fraction,
                "implied_cover": (scale * fraction - correction) / denominator,
                "below_lower": fraction < lower,
                "above_upper": fraction > upper,
            }
        )
    require(
        sum(row["implied_cover"] for row in result) == 1,
        "Affine closure identity failed",
    )
    return {
        "denominator_D": denominator,
        "scale_T": scale,
        "taxa": result,
        "conditional_nonnegative_cover_exists": all(
            not row["below_lower"] and not row["above_upper"] for row in result
        ),
    }


def load(pin: Mapping[str, Any]) -> tuple[bytes, Any]:
    raw, value = read(Path(pin["path"]), pin["sha256"], 8 * 1024**2)
    require(len(raw) == pin["bytes"], "Input size differs")
    return raw, value


def raw_member(pin: Mapping[str, Any]) -> bytes:
    path = Path(pin["path"])
    require(
        path.is_absolute()
        and ".." not in path.parts
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical source required",
    )
    before = path.stat()
    require(
        stat.S_ISREG(before.st_mode)
        and before.st_nlink == 1
        and before.st_size <= 8 * 1024**2,
        "Bounded regular member required",
    )
    raw = path.read_bytes()
    after = path.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    require(
        all(getattr(before, k) == getattr(after, k) for k in fields)
        and len(raw) == before.st_size == pin["bytes"]
        and hashlib.sha256(raw).hexdigest() == pin["sha256"],
        "Raw member identity differs",
    )
    return raw


def csv_rows(pin: Mapping[str, Any]) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(raw_member(pin).decode())))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    _, contract = read(args.contract, args.contract_sha256, 131072)
    require(
        contract["schema_version"]
        == "nordic-coupled-composition-admissibility-inputs.v1",
        "Wrong diagnostic contract",
    )
    _, finding = load(contract["original_finding"])
    require(
        len(finding["evidence"]) == len(contract["cases"]) == 8,
        "Complete eight-fold population required",
    )
    load(contract["original_batch"])
    for source in contract["source_pins"]:
        raw_member(source)
    outputs: list[dict[str, Any]] = []
    for declared, original in zip(contract["cases"], finding["evidence"], strict=True):
        require(declared["identity"] == original, "Original fold identity differs")
        _, manifest = load(declared["manifest"])
        members = declared["members"]
        require(
            all(
                manifest["scientific_identity"]["engine_files"][row["engine_member"]]
                == row["sha256"]
                for row in contract["source_pins"]
                if "engine_member" in row
            ),
            "Saved equation source identity differs",
        )
        for name, pin in members.items():
            require(
                manifest["files"][name] == pin["sha256"],
                "Native member identity differs",
            )
        _, request = load(members["request.json"])
        _, native_run = load(members["numerical/local_love/run_manifest.json"])
        require(
            request["taxa"] == list(TAXA)
            and [row["taxon"] for row in request["parameters"]] == list(TAXA),
            "Native taxon axis differs",
        )
        require(
            request["configuration"]["love"]["stochastic"] is False
            and request["configuration"]["reveals"]["stochastic"] is False,
            "Diagnostic requires deterministic native inputs",
        )
        require(
            native_run["parameters"]["paired_regional_cover_draws"] is True
            and native_run["parameters"]["stochastic"] is False,
            "Native regional handoff differs",
        )
        require(
            native_run["parameters"]["paired_local_count_draws"] is False
            and native_run["parameters"]["paired_local_ppe_draws"] is False,
            "Local draws are outside this diagnostic",
        )
        require(
            len(request["local"]["samples"])
            == len(request["regional"]["samples"])
            == 1,
            "One native local/regional sample required",
        )
        ring = request["rings"][-1]
        require(
            number(ring["mean_m"]) == 750
            and request["configuration"]["love"]["max_ring"] == 2,
            "Original selected ring differs",
        )
        selected: dict[str, dict[str, str]] = {}
        for name in ("aux_Kloc.csv", "aux_Kreg.csv", "cover_mean.csv"):
            rows = csv_rows(members["numerical/local_love/" + name])
            require(
                len(rows) == 2
                and list(rows[-1]) == ["index", *TAXA]
                and number(rows[-1]["index"]) == 750,
                "Native ring/axis differs",
            )
            selected[name] = rows[-1]
        valid = csv_rows(members["numerical/local_love/aux_valid_ring.csv"])
        require(
            len(valid) == 2
            and number(valid[-1]["index"]) == 750
            and valid[-1]["value"] == "True",
            "Native selected ring is not valid",
        )
        regional = csv_rows(members["numerical/regional_reveals/reconstruction.csv"])
        require(len(regional) == 1, "One deterministic regional row required")
        reg = regional[0]
        require(
            all(
                number(reg[taxon + ".sd"]) == 0
                and all(
                    number(reg[taxon + suffix]) == number(reg[taxon + ".mean"])
                    for suffix in (".q10", ".q90", ".median")
                )
                for taxon in TAXA
            ),
            "Regional native repetitions differ",
        )
        diagnostic = algebra(
            request["local"]["samples"][0]["counts"],
            [row["ppe"] for row in request["parameters"]],
            [number(reg[taxon + ".mean"]) / 100 for taxon in TAXA],
            [selected["aux_Kloc.csv"][taxon] for taxon in TAXA],
            [selected["aux_Kreg.csv"][taxon] for taxon in TAXA],
        )
        for row in diagnostic["taxa"]:
            saved = selected["cover_mean.csv"][row["taxon"]]
            require(
                saved == original["fractions"][row["taxon"]],
                "Saved original signed result differs",
            )
            value = number(saved)
            row["saved_native_cover"] = saved
            row["saved_minus_rational_cover"] = value - row["implied_cover"]
            row["native_range_refusal"] = value < 0 or value > 1
            require(
                row["native_range_refusal"]
                == (row["below_lower"] or row["above_upper"]),
                "Native and algebraic range classifications disagree",
            )
        outputs.append(
            {
                "identity": original,
                "fixed_context": {
                    "local_sample": request["local"]["samples"][0],
                    "regional_sample": request["regional"]["samples"][0],
                    "local_basin": request["local"]["basin"],
                    "regional_basin": request["regional"]["basin"],
                    "parameters": request["parameters"],
                    "selected_ring": ring,
                    "distance_weighting": request["configuration"]["love"][
                        "distance_weighting"
                    ],
                    "regional_cover_percent": {
                        taxon: reg[taxon + ".mean"] for taxon in TAXA
                    },
                },
                "diagnostic": diagnostic,
            }
        )
    result: dict[str, Any] = {
        "schema_version": "nordic-coupled-composition-admissibility.v1",
        "input_contract_sha256": args.contract_sha256,
        "original_native_epoch": finding["candidate"],
        "cases": outputs,
        "arithmetic": "Exact rational interpretation of saved decimal cells; every rational serialized numerator/denominator. Native residuals retained, no tolerance/equality permission introduced.",
        "scope": "Conditional algebraic incompatibility of this fixed count/PPE/background/K packet with a nonnegative local cover. No field cause, faulty source, wrong geometry/PPE/kernel, universal model failure or corrected prediction inferred. No refit, K evaluation, score, clipping or source guard change.",
    }

    def serial(value: object) -> dict[str, str]:
        if isinstance(value, Fraction):
            return {
                "numerator": str(value.numerator),
                "denominator": str(value.denominator),
            }
        raise TypeError(type(value).__name__)

    body = (
        json.dumps(result, indent=2, allow_nan=False, default=serial) + "\n"
    ).encode()
    require(
        len(body) <= 1024**2 and not args.output.exists(),
        "Fresh bounded output required",
    )
    require(
        args.output.is_absolute()
        and args.output.is_relative_to(Path(contract["repository"]) / "artifacts")
        and ".." not in args.output.parts
        and not any(p.is_symlink() for p in (args.output, *args.output.parents)),
        "Owned output required",
    )
    args.output.write_bytes(body)


if __name__ == "__main__":
    main()
