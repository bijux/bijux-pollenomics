"""Joint local/regional counting sets for eight previously selected LOVE failures."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable
import csv
from dataclasses import asdict
from fractions import Fraction
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

TAXA = ("Betula", "Ulmus")
FIXED_RESULT = "reports/science/pollen-reconstruction/nordic-coupled-workflow/love-counting-uncertainty.json"
FIXED_SHA256 = "dacbf97b1cd1753cc3e1f1ca4846a428ac9a4271ac77ea9d6f22de59953e6cee"
CONTRACT_SHA256 = "beecdd97445f141661c8080c041d81599822066fc2101f44d08ab2a79068afa2"
NATIVE_EPOCH = "964baa9418e0e22a43cdb971fdd67518b000b62f"
PROFILE = "homogeneous-two-taxon-local-regional-counting-set-v1"
Evaluator = Callable[[dict[str, Any]], dict[str, Any]]


def require(condition: object, message: str) -> None:
    if not condition:
        raise ValueError(message)


def asset(archive: Path, digest: str, size: int | None = None) -> bytes:
    """Read one authenticated raw asset directly from the shared preserved store."""
    require(re.fullmatch(r"[0-9a-f]{64}", digest) is not None, "Invalid asset identity")
    objects = archive / "objects"
    path = objects / digest[:2] / digest
    require(
        path.is_file()
        and not path.is_symlink()
        and path.resolve().is_relative_to(objects.resolve()),
        "Missing or unsafe preserved asset",
    )
    require(path.stat().st_size <= 1024**2, "Preserved input exceeds bounded read")
    raw = path.read_bytes()
    require(
        (size is None or len(raw) == size)
        and hashlib.sha256(raw).hexdigest() == digest,
        "Preserved raw asset bytes changed",
    )
    return raw


def table(raw: bytes, columns: list[str]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(raw.decode()))
    require(reader.fieldnames == columns, "Native table axis differs")
    rows = list(reader)
    require(
        rows
        and all(
            set(row) == set(columns)
            and all(isinstance(v, str) and v for v in row.values())
            for row in rows
        ),
        "Incomplete native table",
    )
    return rows


def finite(value: object, *, positive: bool = False) -> float:
    require(type(value) in (int, float, str), "Numeric source cell required")
    number = float(str(value))
    require(
        math.isfinite(number) and (number > 0 if positive else number >= 0),
        "Source response domain differs",
    )
    return number


def counts(sample: dict[str, Any]) -> list[int]:
    values: list[int] = sample["counts"]
    require(
        isinstance(values, list)
        and len(values) == 2
        and all(type(n) is int and n >= 0 for n in values)
        and 1 <= sum(values) <= 10000,
        "Measured two-taxon integer panel required",
    )
    return values


def load_cases(repository: Path, archive: Path) -> list[dict[str, Any]]:
    """Join exact historical members without dereferencing retired run paths."""
    path = repository / FIXED_RESULT
    require(
        path.is_file() and path.resolve().is_relative_to(repository.resolve()),
        "Fixed result unavailable",
    )
    raw = path.read_bytes()
    require(
        len(raw) <= 1024**2 and hashlib.sha256(raw).hexdigest() == FIXED_SHA256,
        "Fixed-background result changed",
    )
    previous = json.loads(raw)
    contract = json.loads(asset(archive, CONTRACT_SHA256))
    require(
        previous["schema_version"] == "nordic-love-conditional-counting-result.v1"
        and previous["original_native_epoch"] == NATIVE_EPOCH
        and previous["confidence_level"] == 0.95
        and previous["original_prediction_native_exit"] == 1
        and previous["original_failed_folds"] == 8
        and previous["original_dependent_method_refusals"] == 24
        and previous["confidence_set_counts"] == {"nonempty": 3, "empty": 5}
        and contract["schema_version"]
        == "nordic-coupled-composition-admissibility-inputs.v1"
        and len(previous["cases"]) == len(contract["cases"]) == 8,
        "Original eight-case population differs",
    )
    identities = [
        json.dumps(row["identity"], sort_keys=True) for row in previous["cases"]
    ]
    require(len(set(identities)) == 8, "Duplicate original case")
    return [
        load_case(archive, old, declared)
        for old, declared in zip(previous["cases"], contract["cases"], strict=True)
    ]


def load_case(
    archive: Path, old: dict[str, Any], declared: dict[str, Any]
) -> dict[str, Any]:
    """Bind one existing request and its actual native response assets."""
    require(
        old["identity"] == declared["identity"]
        and old["cache_manifest"] == declared["manifest"]
        and old["member_pins"] == declared["members"]
        and old["original_refusal_preserved"] is True
        and old["status"] == "computed",
        "Original case/member binding differs",
    )
    pin = declared["manifest"]
    manifest = json.loads(asset(archive, pin["sha256"], pin["bytes"]))
    used: dict[str, str] = {}

    def member(name: str) -> bytes:
        digest = manifest["files"][name]
        if name in declared["members"]:
            require(
                declared["members"][name]["sha256"] == digest,
                "Declared member differs",
            )
        used[name] = digest
        return asset(archive, digest)

    request = json.loads(member("request.json"))
    context = old["fixed_context"]
    require(
        request["taxa"] == manifest["retained_taxa"] == list(TAXA)
        and request["pollen_unit"] == "count"
        and request["operation"] == "lra"
        and request["data_kind"] == "source_observations"
        and request["method_profile"] == manifest["method_profile"]
        and request["configuration"]["love"]["method"] == "analytical"
        and request["configuration"]["love"]["stochastic"] is False
        and request["configuration"]["reveals"]["stochastic"] is False
        and re.fullmatch(
            r"[0-9a-f]{64}", manifest["scientific_identity"]["request_sha256"]
        )
        is not None
        and manifest["units"]["distance"] == "metre"
        and manifest["units"]["local_cover"] == "fraction"
        and manifest["units"]["regional_cover"] == "percent"
        and request["parameters"] == context["parameters"]
        and [row["taxon"] for row in request["parameters"]] == list(TAXA)
        and request["rings"][-1] == context["selected_ring"]
        and finite(context["selected_ring"]["mean_m"]) == 750,
        "Source axes, units, parameters or ring differ",
    )
    for role in ("local", "regional"):
        require(
            request[role]["samples"] == [context[role + "_sample"]]
            and request[role]["basin"] == context[role + "_basin"],
            "Original sample/core context differs",
        )
    run = json.loads(member("numerical/regional_reveals/run_manifest.json"))
    units = json.loads(member("numerical/regional_reveals/result_contract.json"))
    require(
        run["algorithm"] == "REVEALS"
        and run["parameters"]["stochastic"] is False
        and run["parameters"]["basin_diameter_m"]
        == context["regional_basin"]["diameter_m"]
        and run["parameters"]["distance_weighting"] == context["distance_weighting"]
        and units["units"] == {"cover": "percent", "distance": "metre"},
        "Regional response convention differs",
    )
    kernels = []
    for filename in ("aux_Kloc.csv", "aux_Kreg.csv", "cover_mean.csv"):
        rows = table(member("numerical/local_love/" + filename), ["index", *TAXA])
        require(
            len(rows) == 2 and finite(rows[-1]["index"]) == 750,
            "Selected native ring differs",
        )
        if filename == "cover_mean.csv":
            require(
                {t: rows[-1][t] for t in TAXA} == old["identity"]["fractions"],
                "Signed historical estimate differs",
            )
        else:
            kernels.append(
                [finite(rows[-1][t], positive=filename == "aux_Kloc.csv") for t in TAXA]
            )
    response = table(
        member("numerical/regional_reveals/deposition_factors.csv"), ["index", "K"]
    )
    require(
        [row["index"] for row in response] == list(TAXA),
        "Regional response taxon axis differs",
    )
    return {
        "identity": old["identity"],
        "local_sample": context["local_sample"],
        "regional_sample": context["regional_sample"],
        "local_counts": counts(context["local_sample"]),
        "regional_counts": counts(context["regional_sample"]),
        "local_kernel": kernels[0],
        "regional_kernel": kernels[1],
        "regional_deposition": [finite(row["K"], positive=True) for row in response],
        "ppe": [finite(row["ppe"], positive=True) for row in request["parameters"]],
        "signed_historical_cover": old["identity"]["fractions"],
        "previous_fixed_background_classification": old["confidence_set"]["status"],
        "native_manifest_sha256": pin["sha256"],
        "original_scientific_request_sha256": manifest["scientific_identity"][
            "request_sha256"
        ],
        "original_member_sha256": used,
    }


def maintained(case: dict[str, Any]) -> dict[str, Any]:
    from bijux_pollenomics_lra.reconstruction.uncertainty.regional_counting import (
        regional_two_taxon_counting_set,
    )

    return asdict(
        regional_two_taxon_counting_set(
            *(
                case[key]
                for key in (
                    "local_counts",
                    "regional_counts",
                    "local_kernel",
                    "regional_kernel",
                    "regional_deposition",
                    "ppe",
                )
            ),
            local_taxon_measured=[True, True],
            regional_taxon_measured=[True, True],
            confidence_level=0.95,
        )
    )


def evaluate(
    cases: list[dict[str, Any]], evaluator: Evaluator = maintained
) -> list[dict[str, Any]]:
    """Keep numerical refusals and the complete terminal population visible."""
    from bijux_pollenomics_lra.models.errors import ValidationError

    require(len(cases) == 8, "Eight original cases required")
    result = []
    fatal = False
    for case in cases:
        row = {**case, "status": "not_run", "confidence_set": None, "reason": None}
        if not fatal:
            try:
                value = evaluator(case)
                require(
                    value["profile"] == PROFILE
                    and value["confidence_level"] == 0.95
                    and tuple(value["local_counting"]["counts"])
                    == tuple(case["local_counts"])
                    and tuple(value["regional_counting"]["counts"])
                    == tuple(case["regional_counts"])
                    and all(
                        tuple(value[key]) == tuple(case[key])
                        for key in (
                            "local_kernel",
                            "regional_kernel",
                            "regional_deposition",
                            "ppe",
                        )
                    )
                    and value["local_counting"]["confidence_level"]
                    == value["regional_counting"]["confidence_level"]
                    == value["marginal_confidence_level"]
                    and Fraction(value["guaranteed_joint_confidence_lower_bound"])
                    >= Fraction.from_float(0.95)
                    and value["fixed_regional_control"]["local_confidence_level"]
                    == value["marginal_confidence_level"]
                    and value["fixed_regional_control"]["regional_cover_exact"]
                    == value["regional_point_cover_exact"],
                    "Counting API inputs or confidence contract differ",
                )
                for image in (value["image"], value["fixed_regional_control"]["image"]):
                    require(
                        image["status"] in {"empty", "nonempty"},
                        "Unexpected set classification",
                    )
                    require(
                        (image["cover_lower"] is None and image["cover_upper"] is None)
                        if image["status"] == "empty"
                        else (
                            image["cover_lower"] is not None
                            and image["cover_upper"] is not None
                        ),
                        "Set/null classification differs",
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
        result.append(row)
    return result


def _revision(repository: Path) -> str:
    from bijux_pollenomics_lra.reconstruction.uncertainty import (
        homogeneous_counting,
        regional_counting,
        two_taxon_counting,
    )

    package = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/uncertainty"
    modules = [
        (regional_counting, f"{package}/regional_counting.py"),
        (homogeneous_counting, f"{package}/homogeneous_counting.py"),
        (two_taxon_counting, f"{package}/two_taxon_counting.py"),
        (
            sys.modules[__name__],
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/nordic_coupled/regional_counting_uncertainty.py",
        ),
    ]
    for module, relative in modules:
        path = Path(module.__file__ or "")
        require(
            path.resolve(strict=True) == path == repository / relative,
            "Scientific module imported outside canonical source",
        )
    paths = [relative for _, relative in modules]
    command = ["git", "-C", str(repository)]
    revision = subprocess.check_output(
        [*command, "rev-parse", "HEAD"], text=True, timeout=30
    ).strip()
    subprocess.run(
        [*command, "ls-files", "--error-unmatch", "--", *paths],
        check=True,
        capture_output=True,
        timeout=30,
    )
    subprocess.run(
        [*command, "diff", "--exit-code", revision, "--", *paths],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return revision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.absolute()
    require(
        repository.resolve(strict=True) == repository,
        "Physical canonical repository required",
    )
    output = require_absent_artifact_output(repository, args.output)
    revision = _revision(repository)
    rows = evaluate(load_cases(repository, args.archive))
    require(
        _revision(repository) == revision, "Scientific source changed during execution"
    )
    result = {
        "schema_version": "nordic-love-regional-counting-result.v1",
        "source_commit": revision,
        "command": sys.orig_argv,
        "original_native_epoch": NATIVE_EPOCH,
        "scientific_inputs": {
            "fixed_background_result": {"path": FIXED_RESULT, "sha256": FIXED_SHA256},
            "original_cache_contract_sha256": CONTRACT_SHA256,
        },
        "taxa": list(TAXA),
        "confidence_level": 0.95,
        "cases": rows,
        "status_counts": dict(Counter(row["status"] for row in rows)),
        "confidence_set_counts": dict(
            Counter(
                row["confidence_set"]["image"]["status"]
                for row in rows
                if row["status"] == "computed"
            )
        ),
        "matched_fixed_regional_control_counts": dict(
            Counter(
                row["confidence_set"]["fixed_regional_control"]["image"]["status"]
                for row in rows
                if row["status"] == "computed"
            )
        ),
        "previous_fixed_background_counts": {"nonempty": 3, "empty": 5},
        "original_failed_folds": 8,
        "original_dependent_method_refusals": 24,
        "original_estimator_or_refusal_changed": False,
        "original_source_acceptance_discharged": False,
        "limits": [
            "Eight requests were selected after signed LOVE failures. Per-prespecified-request guarantees do not establish postselection or simultaneous eight-case coverage.",
            "Each pooled local/regional panel is assumed marginally binomial with fixed effort and homogeneous taxon probability. These sampling assumptions are not established by the source; Bonferroni does not require independence between panels.",
            "PPE, deposition responses, geometry, chronology, support and model remain fixed. No empirical field coverage, vegetation accuracy, source permission, qualified human approval or release qualification follows.",
            "New rational plug-in estimates use source regional counts/responses and supplied binary64 coefficients. They are new conditional arithmetic, distinct from rounded historical regional means and signed historical LOVE values retained verbatim.",
            "The matched fixed-regional control uses the same local marginal confidence and exact new regional plug-in composition, isolating the added regional interval within this conditional arithmetic. Comparison with previous 95% fixed-background sets also changes local marginal confidence and rounded historical arithmetic.",
            "No kernel evaluations, refits, forwarding or scores were repeated. Original signed estimates and eight/24 prediction refusals remain unchanged.",
        ],
    }
    raw = (json.dumps(result, indent=2, allow_nan=False) + "\n").encode()
    require(len(raw) <= 1024**2, "Output exceeds one MiB")
    with output.open("xb") as handle:
        handle.write(raw)
    raise SystemExit(
        1 if any(row["status"] in {"fatal", "not_run"} for row in rows) else 0
    )


if __name__ == "__main__":
    main()
