"""Conditional counting sets for the eight retained signed LOVE requests."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from fractions import Fraction
import json
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.admissibility import (
    TAXA,
    csv_rows,
    load,
    number,
    raw_member,
)
from bijux_pollenomics_dev.essd_reproduction.nordic_coupled.workflow import (
    physical,
    read,
    require,
)

CONTRACT_SHA256 = "beecdd97445f141661c8080c041d81599822066fc2101f44d08ab2a79068afa2"
PRIOR_SHA256 = "92f9c3ea9328b9945a430b5e734350cab2bf2115db1a3854b91bd63f2b8fee99"
NATIVE_EPOCH = "964baa9418e0e22a43cdb971fdd67518b000b62f"
PROFILE = "homogeneous-two-taxon-fixed-background-binomial-set-v1"
MEMBERS = frozenset(
    {
        "request.json",
        "numerical/local_love/aux_Kloc.csv",
        "numerical/local_love/aux_Kreg.csv",
        "numerical/local_love/aux_valid_ring.csv",
        "numerical/local_love/cover_mean.csv",
        "numerical/local_love/run_manifest.json",
        "numerical/regional_reveals/reconstruction.csv",
    }
)
Evaluator = Callable[[list[int], list[float], list[float]], dict[str, Any]]


def saved_cases(
    contract: dict[str, Any], prior: dict[str, Any]
) -> list[dict[str, Any]]:
    """Reopen the exact selected cache members; never replay their producer."""
    require(
        contract["schema_version"]
        == "nordic-coupled-composition-admissibility-inputs.v1",
        "Wrong cache contract",
    )
    require(
        prior["schema_version"] == "nordic-coupled-composition-admissibility.v1"
        and prior["input_contract_sha256"] == CONTRACT_SHA256
        and prior["original_native_epoch"] == NATIVE_EPOCH,
        "Wrong prior diagnostic",
    )
    _, finding = load(contract["original_finding"])
    _, batch = load(contract["original_batch"])
    require(
        finding["candidate"] == NATIVE_EPOCH
        and batch["execution_epoch"] == NATIVE_EPOCH,
        "Original epoch differs",
    )
    require(
        len(contract["cases"]) == len(finding["evidence"]) == len(prior["cases"]) == 8,
        "Complete eight-case population required",
    )
    identities = [
        json.dumps(row["identity"], sort_keys=True) for row in contract["cases"]
    ]
    require(len(set(identities)) == 8, "Duplicate case")
    result: list[dict[str, Any]] = []
    for declared, original, previous in zip(
        contract["cases"], finding["evidence"], prior["cases"], strict=True
    ):
        require(
            declared["identity"] == original == previous["identity"],
            "Original identity differs",
        )
        require(
            previous["diagnostic"]["conditional_nonnegative_cover_exists"] is False,
            "Original refusal differs",
        )
        _, manifest = load(declared["manifest"])
        members = declared["members"]
        require(set(members) == MEMBERS, "Selected member population differs")
        for name, pin in members.items():
            require(
                manifest["files"][name] == pin["sha256"],
                "Native member binding differs",
            )
            raw_member(pin)
        # These are historical equation identities, not a claim that every old
        # workflow source file is unchanged in the current checkout.
        for source in contract["source_pins"]:
            if "engine_member" in source:
                require(
                    manifest["scientific_identity"]["engine_files"][
                        source["engine_member"]
                    ]
                    == source["sha256"],
                    "Saved equation identity differs",
                )
        _, request = load(members["request.json"])
        _, native = load(members["numerical/local_love/run_manifest.json"])
        require(
            request["taxa"] == list(TAXA)
            and [p["taxon"] for p in request["parameters"]] == list(TAXA),
            "Taxon axis differs",
        )
        require(
            request["configuration"]["love"]["stochastic"] is False
            and request["configuration"]["reveals"]["stochastic"] is False
            and native["parameters"]["stochastic"] is False
            and native["parameters"]["paired_regional_cover_draws"] is True
            and native["parameters"]["paired_local_count_draws"] is False
            and native["parameters"]["paired_local_ppe_draws"] is False,
            "Native deterministic handoff differs",
        )
        require(
            len(request["local"]["samples"])
            == len(request["regional"]["samples"])
            == 1,
            "One local/regional sample required",
        )
        context = previous["fixed_context"]
        require(
            all(
                context[key + "_sample"] == request[key]["samples"][0]
                and context[key + "_basin"] == request[key]["basin"]
                for key in ("local", "regional")
            )
            and context["parameters"] == request["parameters"]
            and context["selected_ring"] == request["rings"][-1]
            and context["distance_weighting"]
            == request["configuration"]["love"]["distance_weighting"],
            "Saved context differs",
        )
        require(
            number(request["rings"][-1]["mean_m"]) == 750
            and request["configuration"]["love"]["max_ring"] == 2,
            "Selected ring differs",
        )
        selected = {}
        for name in ("aux_Kloc.csv", "aux_Kreg.csv", "cover_mean.csv"):
            rows = csv_rows(members["numerical/local_love/" + name])
            require(
                len(rows) == 2
                and list(rows[-1]) == ["index", *TAXA]
                and number(rows[-1]["index"]) == 750,
                "Saved CSV axis/ring differs",
            )
            selected[name] = rows[-1]
        valid = csv_rows(members["numerical/local_love/aux_valid_ring.csv"])
        require(
            len(valid) == 2
            and list(valid[-1]) == ["index", "value"]
            and number(valid[-1]["index"]) == 750
            and valid[-1]["value"] == "True",
            "Saved ring invalid",
        )
        regional = csv_rows(members["numerical/regional_reveals/reconstruction.csv"])
        require(len(regional) == 1, "One regional result required")
        reg = regional[0]
        require(
            all(
                number(reg[t + ".sd"]) == 0
                and all(
                    number(reg[t + suffix]) == number(reg[t + ".mean"])
                    for suffix in (".q10", ".q90", ".median")
                )
                and context["regional_cover_percent"][t] == reg[t + ".mean"]
                and selected["cover_mean.csv"][t] == original["fractions"][t]
                for t in TAXA
            ),
            "Saved background/signed result differs",
        )
        result.append(
            {
                "identity": original,
                "local_sample": context["local_sample"],
                "fixed_context": context,
                "ppe": [p["ppe"] for p in request["parameters"]],
                "regional_fraction": [number(reg[t + ".mean"]) / 100 for t in TAXA],
                "kloc": [selected["aux_Kloc.csv"][t] for t in TAXA],
                "kreg": [selected["aux_Kreg.csv"][t] for t in TAXA],
                "previous_diagnostic": previous["diagnostic"],
                "cache_manifest": declared["manifest"],
                "member_pins": members,
            }
        )
    return result


def coefficients(
    case: dict[str, Any],
) -> tuple[list[int], list[float], list[float], dict[str, Any]]:
    """Translate the recorded LOVE law into fixed raw-pollen coefficients.

    q_i=(n_i/PPE_i)/sum(n/PPE), v_i=(D+B)*q_i/D-b_i/D,
    D=sum(c_i*Kloc_i), b_i=c_i*Kreg_i. Thus the raw pollen law is
    p_i(v)=PPE_i*(D*v_i+b_i)/sum_j PPE_j*(D*v_j+b_j).
    This common D is not the taxon-specific Kloc vector.
    """
    counts = case["local_sample"]["counts"]
    require(
        type(counts) is list
        and len(counts) == 2
        and all(type(n) is int and n >= 0 for n in counts)
        and 1 <= sum(counts) <= 10000,
        "Bounded integer two-taxon panel required",
    )
    vectors = [case[key] for key in ("ppe", "regional_fraction", "kloc", "kreg")]
    require(all(len(v) == 2 for v in vectors), "Two coefficient axes required")
    ppe, regional, local, distant = [[number(v) for v in axis] for axis in vectors]
    require(
        all(v > 0 for v in ppe) and all(v >= 0 for v in regional + local + distant),
        "Fixed coefficients outside domain",
    )
    denominator = sum((c * k for c, k in zip(regional, local, strict=True)), Fraction())
    require(denominator > 0, "Positive common denominator required")
    previous = case["previous_diagnostic"]["denominator_D"]
    require(
        denominator
        == Fraction(int(previous["numerator"]), int(previous["denominator"])),
        "Prior denominator differs",
    )
    exact_a = [p * denominator for p in ppe]
    exact_b = [p * c * k for p, c, k in zip(ppe, regional, distant, strict=True)]
    a, b = [float(v) for v in exact_a], [float(v) for v in exact_b]
    require(
        all(math.isfinite(v) and v > 0 for v in a)
        and all(math.isfinite(v) and v >= 0 for v in b),
        "Binary64 coefficient conversion refused",
    )
    return (
        counts,
        a,
        b,
        {
            "denominator_D": str(denominator),
            "local_coefficients_exact_decimal_rationals": list(map(str, exact_a)),
            "regional_deposition_exact_decimal_rationals": list(map(str, exact_b)),
            "conversion": "Each exact saved-decimal coefficient rounded once to binary64; API conditions on those supplied binary64 values. Not native arithmetic replay.",
        },
    )


def maintained(counts: list[int], a: list[float], b: list[float]) -> dict[str, Any]:
    """Load the maintained fixed-background counting-set evaluator."""
    from bijux_pollenomics_lra.reconstruction.uncertainty.homogeneous_counting import (
        homogeneous_two_taxon_counting_set,
    )

    return asdict(
        homogeneous_two_taxon_counting_set(
            counts,
            a,
            b,
            taxon_measured=[True, True],
            confidence_level=0.95,
        )
    )


def evaluate(
    cases: list[dict[str, Any]], evaluator: Evaluator = maintained
) -> list[dict[str, Any]]:
    """Retain every requested case, including numerical refusals and later not-run rows."""
    from bijux_pollenomics_lra.models.errors import ValidationError

    require(len(cases) == 8, "Eight cases required")
    output: list[dict[str, Any]] = []
    fatal = False
    for case in cases:
        row: dict[str, Any] = {
            "identity": case["identity"],
            "original_refusal_preserved": True,
            "fixed_context": case["fixed_context"],
            "cache_manifest": case["cache_manifest"],
            "member_pins": case["member_pins"],
            "previous_diagnostic": case["previous_diagnostic"],
            "status": "not_run",
            "confidence_set": None,
            "reason": None,
        }
        if not fatal:
            try:
                counts, a, b, derivation = coefficients(case)
                row["coefficient_derivation"] = derivation
                row["restricted_panel_N"] = sum(counts)
                row["local_coefficients"] = a
                row["regional_deposition"] = b
                value = evaluator(counts, a, b)
                require(
                    value["profile"] == PROFILE
                    and value["confidence_level"] == 0.95
                    and tuple(value["counts"]) == tuple(counts)
                    and value["total_count"] == sum(counts)
                    and tuple(value["local_coefficients"]) == tuple(a)
                    and tuple(value["regional_deposition"]) == tuple(b)
                    and value["status"] in ("empty", "nonempty"),
                    "Counting API result differs",
                )
                require(
                    (value["cover_lower"] is None and value["cover_upper"] is None)
                    if value["status"] == "empty"
                    else (
                        value["cover_lower"] is not None
                        and value["cover_upper"] is not None
                    ),
                    "Counting set/null classification differs",
                )
                row.update(status="computed", confidence_set=value)
            except ValidationError as error:
                known = type(error) is ValidationError and error.reason_code in {
                    "invalid_input",
                    "counting_interval_certification",
                    "counting_interval_conditioning",
                    "taxon_measurement_unresolved",
                }
                row.update(
                    status="refused" if known else "fatal",
                    reason={
                        "class": type(error).__name__,
                        "reason_code": error.reason_code,
                        "detail": str(error),
                    },
                )
                fatal = not known
            except Exception as error:
                row.update(
                    status="fatal",
                    reason={"class": type(error).__name__, "detail": str(error)},
                )
                fatal = True
        output.append(row)
    return output


def main() -> None:
    """Parse arguments for the declared source-bound conditional calculation."""
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--execution-epoch", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    physical(args.repository)
    _, protocol = read(args.protocol, args.protocol_sha256, 65536)
    require(
        protocol["schema_version"] == "nordic-love-conditional-counting.v1"
        and protocol["profile"] == PROFILE
        and type(protocol["alpha"]) is float
        and protocol["alpha"] == 0.05
        and type(protocol["confidence_level"]) is float
        and protocol["confidence_level"] == 0.95
        and protocol["cases"] == 8
        and protocol["taxa"] == list(TAXA),
        "Protocol differs",
    )
    pins = {}
    for name, row in protocol["input_pins"].items():
        relative = Path(row["path"])
        require(
            not relative.is_absolute() and ".." not in relative.parts,
            "Relative input required",
        )
        pins[name] = {**row, "path": str(args.repository / relative)}
    require(
        set(pins) == {"cache_contract", "prior_admissibility"}
        and pins["cache_contract"]["sha256"] == CONTRACT_SHA256
        and pins["prior_admissibility"]["sha256"] == PRIOR_SHA256,
        "Input authority differs",
    )
    _, contract = load(pins["cache_contract"])
    require(contract["repository"] == str(args.repository), "Repository differs")
    _, prior = load(pins["prior_admissibility"])
    require(
        len(args.execution_epoch) == 40
        and all(c in "0123456789abcdef" for c in args.execution_epoch),
        "Execution epoch required",
    )
    cases = saved_cases(contract, prior)
    rows = evaluate(cases)
    result = {
        "schema_version": "nordic-love-conditional-counting-result.v1",
        "execution_epoch": args.execution_epoch,
        "original_native_epoch": NATIVE_EPOCH,
        "original_prediction_native_exit": 1,
        "original_failed_folds": 8,
        "original_dependent_method_refusals": 24,
        "protocol_sha256": args.protocol_sha256,
        "input_pins": pins,
        "alpha": 0.05,
        "confidence_level": 0.95,
        "cases": rows,
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "confidence_set_counts": dict(
            Counter(
                row["confidence_set"]["status"]
                for row in rows
                if row["status"] == "computed"
            )
        ),
        "conditioning": protocol["conditioning"],
        "interpretation_limits": protocol["interpretation_limits"],
        "original_estimator_or_refusal_changed": False,
        "original_source_acceptance_discharged": False,
    }
    body = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    physical(args.output)
    require(
        args.output.is_relative_to(args.repository / "artifacts")
        and not args.output.exists()
        and len(body) <= 1024**2,
        "Fresh owned bounded output required",
    )
    with args.output.open("xb") as stream:
        stream.write(body)
    raise SystemExit(
        1 if any(row["status"] in ("fatal", "not_run") for row in rows) else 0
    )


if __name__ == "__main__":
    main()
