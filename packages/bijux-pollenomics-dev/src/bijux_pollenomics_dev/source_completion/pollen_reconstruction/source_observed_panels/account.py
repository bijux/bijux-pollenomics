"""Replay admitted result/source accounts without rerunning physical transport."""

from __future__ import annotations

from collections import Counter
from collections.abc import Hashable, Mapping
import csv
import hashlib
import json
from pathlib import Path
import re
from typing import TypedDict

from .covariance import ConditionalCovariance, finite, verify_result


class ScopePopulation(TypedDict):
    """Bind the native result and source populations for one publication scope."""

    results: int
    profiles: int
    datasets: int
    units: int
    tuples: int
    uses: int
    receipt_key: str


def _record(value: object) -> dict[str, object]:
    """Require literal object keys before accessing retained capture fields."""
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("scientific account capture must be a JSON object")
    return value


def _array(value: object) -> list[object]:
    """Require a retained JSON array without replacing its members."""
    if not isinstance(value, list):
        raise ValueError("scientific account capture array differs")
    return value


def _records(value: object) -> list[dict[str, object]]:
    """Admit each consumed source, profile or authority record independently."""
    return [_record(row) for row in _array(value)]


def _module_origin_count(value: object) -> int:
    """Count a retained module-to-origin object without treating its keys as rows."""
    origins = _record(value)
    if not origins or any(
        not name or not isinstance(origin, str) or not origin
        for name, origin in origins.items()
    ):
        raise ValueError("scientific account module-origin mapping differs")
    return len(origins)


def _integer(value: object) -> int:
    """Keep native integer identities distinct from booleans and fractions."""
    if type(value) is not int:
        raise ValueError("scientific account integer differs")
    return value


def _tokens(value: object) -> list[str]:
    """Require the literal ordered panel labels or limitations."""
    result = []
    for token in _array(value):
        if not isinstance(token, str):
            raise ValueError("scientific account literal token differs")
        result.append(token)
    return result


def _number_rows(value: object) -> list[list[float]]:
    """Admit each finite numerical covariance or deposition row."""
    return [[finite(cell) for cell in _array(row)] for row in _array(value)]


def _covariance(row: Mapping[str, object]) -> ConditionalCovariance:
    """Describe exactly the saved cells consumed by scalar covariance replay."""
    return {
        "deposition": _number_rows(row["deposition"]),
        "conditional_panel_cover": [
            finite(v) for v in _array(row["conditional_panel_cover"])
        ],
        "conditional_standard_error": [
            finite(v) for v in _array(row["conditional_standard_error"])
        ],
        "counting_covariance": _number_rows(row["counting_covariance"]),
        "shared_ppe_covariance": _number_rows(row["shared_ppe_covariance"]),
        "total_conditional_covariance": _number_rows(
            row["total_conditional_covariance"]
        ),
        "direct_observed_panel_pollen_fraction": [
            finite(v) for v in _array(row["direct_observed_panel_pollen_fraction"])
        ],
    }


SCOPES: dict[str, ScopePopulation] = {
    "common-panel": {
        "results": 2685,
        "profiles": 24,
        "datasets": 19,
        "units": 18,
        "tuples": 150,
        "uses": 5890,
        "receipt_key": "physical-results.json",
    },
    "lake-panels": {
        "results": 5040,
        "profiles": 49,
        "datasets": 30,
        "units": 29,
        "tuples": 284,
        "uses": 10600,
        "receipt_key": "physical-extension-results.json",
    },
}


def digest(path: Path) -> str:
    """Bind retained bytes to their SHA-256 capture identity."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(directory: Path, name: str) -> dict[str, object]:
    """Read one retained capture with literal object keys."""
    value: object = json.loads((directory / name).read_bytes())
    return _record(value)


def retained(
    directory: Path, name: str, terminal: str, receipt_key: str
) -> dict[str, object]:
    """Authenticate native success, custody and the exact captured product bytes."""
    receipt = read(directory, terminal)
    if (
        receipt.get("status") != "PASS"
        or type(receipt.get("native_exit_code")) is not int
        or receipt["native_exit_code"] != 0
    ):
        raise ValueError("scientific capture must retain actual native success")
    if (
        receipt.get("custody_after_unchanged") is not True
        or receipt.get("custody_errors")
        or receipt.get("owned_survivors")
    ):
        raise ValueError("scientific capture custody/process closure differs")
    if _record(_record(receipt["product_files"])[receipt_key])["sha256"] != digest(
        directory / name
    ):
        raise ValueError("scientific result differs from its native capture authority")
    return read(directory, name)


def parameters(
    directory: Path, axis: list[str]
) -> tuple[list[float], list[float], list[float]]:
    """Admit the literal two-token axis and its public parameter domains."""
    with (directory / "parameters.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if (
        len(rows) != 31
        or len({r["Plant taxa/Pollen-morphological types"] for r in rows}) != 31
    ):
        raise ValueError("public parameter source population differs")
    byname = {r["Plant taxa/Pollen-morphological types"]: r for r in rows}
    parsed = []
    for name in axis:
        row = byname[name]
        pair = re.fullmatch(r"([0-9.]+) \(([0-9.]+)\)", row["PPE (SD)"])
        if pair is None or re.fullmatch(r"[0-9.]+", row["FSP (m/s)"]) is None:
            raise ValueError(
                "annotated public parameters need separately admitted interpretation"
            )
        p, sd, fall = float(pair[1]), float(pair[2]), float(row["FSP (m/s)"])
        if finite(p) <= 0 or finite(sd) < 0 or finite(fall) <= 0:
            raise ValueError("public parameter domain differs")
        parsed.append((p, sd, fall))
    if len(parsed) != 2 or len(set(axis)) != 2:
        raise ValueError("literal observed panel must contain two distinct tokens")
    ppe, standard_deviations, fall_speeds = zip(*parsed, strict=True)
    return list(ppe), list(standard_deviations), list(fall_speeds)


def support(value: Mapping[str, object]) -> list[int]:
    """Verify observed counts, denominators and native sample membership."""
    raw_counts = _array(value["counts"])
    counts = [_integer(v) for v in raw_counts]
    if (
        len(counts) != 2
        or any(type(v) is not int or v < 0 for v in counts)
        or sum(counts) == 0
    ):
        raise ValueError("retained observed counts differ")
    total = value["reported_source_pollen_NISP_sum"]
    if (
        type(total) is not int
        or total < sum(counts)
        or value["selected_panel_count_denominator"] != sum(counts)
        or value["unparameterized_reported_source_NISP_sum"] != total - sum(counts)
    ):
        raise ValueError("retained selected/full pollen denominators differ")
    ids = [_integer(v) for v in _array(value["native_sample_ids"])]
    if (
        len(ids) != value["native_sample_count"]
        or len(set(ids)) != len(ids)
        or any(type(s) is not int or s <= 0 for s in ids)
    ):
        raise ValueError("retained native sample identities differ")
    if len(_array(value["native_analysis_unit_ids"])) != len(ids):
        raise ValueError("retained native analysis-unit population differs")
    if (
        abs(finite(value["reported_source_panel_mass_fraction"]) - sum(counts) / total)
        > 1e-12
    ):
        raise ValueError("retained panel mass fraction differs")
    return counts


def profile_key(profile: Mapping[str, object], scope: str) -> Hashable:
    """Keep common-panel identities distinct from source-qualified lake keys."""
    if scope != "common-panel":
        key = profile["source_profile_key"]
        if not isinstance(key, Hashable):
            raise ValueError("scientific profile key is not hashable")
        return key
    return (
        _integer(profile["native_dataset_id"]),
        _integer(profile["native_chronology_id"]),
        tuple(_tokens(profile["literal_panel"])),
    )


def products(directory: Path, scope: str) -> dict[str, dict[str, object]]:
    """Replay authenticated source accounts and scalar checks without transport fits."""
    if scope not in SCOPES:
        raise ValueError("unknown scientific publication scope")
    expected = SCOPES[scope]
    source = retained(
        directory,
        "native-results.json",
        "native-terminal.json",
        expected["receipt_key"],
    )
    native = read(directory, "native-terminal.json")
    plan = read(directory, "native-plan.json")
    if digest(directory / "native-plan.json") != native["plan_sha256"]:
        raise ValueError("native plan differs from actual terminal authority")
    for name, filename in [
        ("consume.py", "native-consumer.py"),
        ("runner.py", "native-supervisor.py"),
        ("engine-source-reuse.json", "engine-source-identities.json"),
    ]:
        if _record(plan["controls_sha256"])[name] != digest(directory / filename):
            raise ValueError("native producer/source control identity differs")
    if source["frozen_protocol_sha256"] != digest(directory / "protocol.json"):
        raise ValueError("native numerical protocol differs")
    protocol = read(directory, "protocol.json")
    eligibility = retained(
        directory,
        "source-eligibility.json",
        "source-terminal.json",
        "eligibility-report.json",
    )
    if protocol["source_eligibility_report_sha256"] != digest(
        directory / "source-eligibility.json"
    ):
        raise ValueError("source-account dependency differs")
    cores = {c["native_dataset_id"]: c for c in _records(eligibility["cores"])}
    if len(cores) != 59 or eligibility["native_samples"] != 4548:
        raise ValueError("retained source-account population differs")
    review = retained(
        directory,
        "independent-factors.json",
        "independent-terminal.json",
        "independent-integration-review.json",
    )
    if review["source_actual_result_sha256"] != digest(
        directory / "native-results.json"
    ) or review["source_actual_terminal_sha256"] != digest(
        directory / "native-terminal.json"
    ):
        raise ValueError("physical qualification belongs to another scientific capture")
    tuple_rows = {
        (
            finite(r["receiver_radius_m"]),
            finite(r["fall_speed_m_s"]),
            finite(r["wind_speed_m_s"]),
        ): r
        for r in _records(source["actual_physical_quadratures"])
    }
    review_rows = {
        (
            finite(_record(r["parameters"])["receiver_radius_m"]),
            finite(_record(r["parameters"])["fall_speed_m_s"]),
            finite(_record(r["parameters"])["wind_speed_m_s"]),
        ): r
        for r in _records(review["results"])
    }
    if (
        len(tuple_rows) != expected["tuples"]
        or len(review_rows) != expected["tuples"]
        or set(tuple_rows) != set(review_rows)
    ):
        raise ValueError("current physical tuple qualification population differs")
    for key, row in tuple_rows.items():
        q = review_rows[key]
        if (
            finite(row["factor"]) <= 0
            or row["factor"] != q["actual_factor"]
            or abs(finite(row["factor"]) - finite(q["independent_scalar_factor"]))
            > 2e-8 + 2e-8 * abs(finite(q["independent_scalar_factor"]))
        ):
            raise ValueError("current physical factor qualification differs")
    physical = {p["id"]: p for p in _records(protocol["profiles"])}
    individual = _records(source["single_dataset_profiles"])
    if len(individual) != expected["profiles"]:
        raise ValueError("native scientific profile population differs")
    source_profiles = [_record(p["selected_source_profile"]) for p in individual]
    if (
        len({p["native_dataset_id"] for p in source_profiles}) != expected["datasets"]
        or len({p["native_collection_unit_id"] for p in source_profiles})
        != expected["units"]
    ):
        raise ValueError("native dataset/distinct-unit population differs")
    lookup = {
        profile_key(_record(p["selected_source_profile"]), scope): p for p in individual
    }
    if len(lookup) != len(individual):
        raise ValueError("scientific profile identity repeats")
    uses: Counter[tuple[float, float, float]] = Counter()
    errors: dict[str, float] = {}
    result_count = 0
    baseline = []
    for profile in individual + _records(source["shared_PPE_multisite_grid_profiles"]):
        members = (
            [_record(profile["selected_source_profile"])]
            if "selected_source_profile" in profile
            else _records(profile["prespecified_source_members"])
        )
        units = [m["native_collection_unit_id"] for m in members]
        if len(units) != len(set(units)):
            raise ValueError("pooled profile repeats a native unit")
        axis = _tokens(members[0]["literal_panel"])
        if any(m["literal_panel"] != axis for m in members):
            raise ValueError("pooled literal taxon panels differ")
        ppe, sd, fall = parameters(directory, axis)
        for member in members:
            if (
                member["native_collection_unit_id"]
                != cores[member["native_dataset_id"]]["native_collection_unit_id"]
            ):
                raise ValueError("native collection-unit source identity differs")
        for row in _records(profile["conditional_results"]):
            result_count += 1
            source_rows = (
                [_record(row["source_support"])]
                if "source_support" in row
                else [
                    _record(
                        _record(row["source_support_by_native_dataset"])[
                            str(m["native_dataset_id"])
                        ]
                    )
                    for m in members
                ]
            )
            counts = [support(r) for r in source_rows]
            sample_ids = [
                s for r in source_rows for s in _array(r["native_sample_ids"])
            ]
            if len(set(sample_ids)) != len(sample_ids):
                raise ValueError("pooled source observations repeat native sample IDs")
            if len(_array(row["deposition"])) != len(members):
                raise ValueError("physical deposition site population differs")
            for member, source_row, factors in zip(
                members, source_rows, _number_rows(row["deposition"]), strict=True
            ):
                account = next(
                    p
                    for p in _records(
                        cores[member["native_dataset_id"]][
                            "fixed_common_panel_candidates"
                        ]
                    )
                    if p["literal_panel"] == axis
                    and p["native_chronology_id"] == member["native_chronology_id"]
                )
                window = next(
                    p
                    for p in _records(account["window_pooled_observed_counts"])
                    if p["window_index"] == row["window_index"]
                )
                if source_row["counts"] != [_record(window["counts"])[n] for n in axis]:
                    raise ValueError(
                        "captured source-window counts differ from retained source account"
                    )
                radius = (
                    member["static_radius_m"]
                    if scope == "lake-panels"
                    else _records(member["static_workbook_radius_candidates"])[0][
                        "metadata_radius_m"
                    ]
                )
                radius = finite(radius) * finite(
                    physical[row["physical_profile"]]["radius_multiplier"]
                )
                for speed, factor in zip(fall, factors, strict=True):
                    key = (
                        radius,
                        speed,
                        finite(physical[row["physical_profile"]]["wind_speed_m_s"]),
                    )
                    if key not in tuple_rows or tuple_rows[key]["factor"] != factor:
                        raise ValueError(
                            "retained result uses an unqualified physical tuple"
                        )
                    uses[key] += 1
            for name, value in verify_result(_covariance(row), counts, ppe, sd).items():
                errors[name] = max(errors.get(name, 0), value)
            if (
                "declared_workbook_grid_id" in profile
                and row["physical_profile"] == "metadata_radius_wind_3"
            ):
                baseline.append(
                    {
                        "grid_id": profile["declared_workbook_grid_id"],
                        "window_index": row["window_index"],
                        "younger_cal_bp": row["younger_cal_bp"],
                        "older_cal_bp_exclusive": row["older_cal_bp_exclusive"],
                        "conditional_panel_cover": row["conditional_panel_cover"],
                        "conditional_standard_error": row["conditional_standard_error"],
                        "distinct_native_units": len(members),
                        "selected_panel_counts_by_dataset": {
                            str(m["native_dataset_id"]): r["counts"]
                            for m, r in zip(members, source_rows, strict=True)
                        },
                    }
                )
    if (
        result_count != expected["results"]
        or sum(uses.values()) != expected["uses"]
        or set(uses) != set(tuple_rows)
    ):
        raise ValueError("native numerical/factor-use population differs")
    if (
        review["actual_conditional_results"] != result_count
        or review["actual_result_factor_uses"] != sum(uses.values())
        or any(
            review_rows[k]["actual_result_factor_uses"] != v for k, v in uses.items()
        )
    ):
        raise ValueError(
            "independent factor-use consumer belongs to another result population"
        )
    domain = (
        retained(
            directory,
            "qualified-window-domain.json",
            "domain-terminal.json",
            "qualified-window-domain.json",
        )["complete_declared_grid_window_domain"]
        if scope == "common-panel"
        else source["full75_multisite_window_domain"]
    )
    classified = {}
    for pool in _records(source["shared_PPE_multisite_grid_profiles"]):
        members = _records(pool["prespecified_source_members"])
        windows = {
            m["native_dataset_id"]: {
                r["window_index"]
                for r in _records(lookup[profile_key(m, scope)]["conditional_results"])
            }
            for m in members
        }
        for index in range(25):
            missing = [
                m["native_dataset_id"]
                for m in members
                if index not in windows[m["native_dataset_id"]]
            ]
            classification = (
                "all_members_absent"
                if len(missing) == len(members)
                else "partial_membership"
                if missing
                else "complete_membership"
            )
            classified[(pool["declared_workbook_grid_id"], index)] = {
                "grid_id": pool["declared_workbook_grid_id"],
                "window_index": index,
                "classification": classification,
                "missing_native_dataset_ids": missing,
                "missing_units_filled_as_zero": False,
            }
    if len(_array(domain)) != 75 or len(classified) != 75:
        raise ValueError("complete declared grid-window domain differs")
    for row in _records(domain):
        original = (
            row["classification"]
            if scope == "common-panel"
            else row["source_membership_scope"]
        )
        if not isinstance(original, str):
            raise ValueError("full-domain captured missingness classification differs")
        mapped = {
            "complete_prespecified_membership": "complete_membership",
            "partial_prespecified_membership": "partial_membership",
            "all_prespecified_members_absent": "all_members_absent",
            "partially_observed": "partial_membership",
        }.get(original, original)
        actual = classified[(row["grid_id"], _integer(row["window_index"]))]
        if (
            mapped != actual["classification"]
            or row["missing_native_dataset_ids"] != actual["missing_native_dataset_ids"]
        ):
            raise ValueError("full-domain captured missingness classification differs")
    comparison = retained(
        directory,
        "published-comparison.json",
        "comparison-terminal.json",
        "published-grid-comparison.json",
    )
    if (
        comparison["actual_new_physical_result_sha256"]
        != digest(directory / "native-results.json")
        or len(_array(comparison["actual_model_ratio_comparisons"])) != 225
        or len(_array(comparison["scoped_refusals"])) != 30
    ):
        raise ValueError("published model comparator scientific population differs")
    citations = retained(
        directory,
        "publication-attribution.json",
        "publication-terminal.json",
        "publication-attribution.json",
    )
    if {
        r["native_dataset_id"]
        for r in _records(citations["dataset_attribution_accounts"])
    } != {m["native_dataset_id"] for m in source_profiles}:
        raise ValueError(
            "current citation scope differs from actually used source datasets"
        )
    policy = retained(
        directory,
        "policy-acquisition.json",
        "policy-terminal.json",
        "consumer-result.json",
    )
    for row in _records(policy["records"]):
        file = directory / f"policy-{row['policy_id']}.response"
        if row["http_status"] != 200 or row["response_sha256"] != digest(file):
            raise ValueError("current primary policy source/capture differs")
    origins = read(directory, "observed-import-origins.json")
    authority = {
        "scientific_scope": scope,
        "native_candidate": native["candidate"],
        "native_plan_sha256": native["plan_sha256"],
        "native_terminal_sha256": digest(directory / "native-terminal.json"),
        "native_result_sha256": digest(directory / "native-results.json"),
        "native_exit_code": native["native_exit_code"],
        "native_wall_seconds": native["wall_seconds"],
        "observed_import_capture_sha256": digest(
            directory / "observed-import-origins.json"
        ),
        "observed_module_origin_count": _module_origin_count(
            origins["actual_loaded_module_origins"]
        ),
        "scope": "Actual immutable native result custody; maintained publisher replays accounts and scalar covariance, not physical fits, integrations or raw-source acquisition",
    }
    return {
        "report.json": {
            "schema_version": "source-observed-pollen-panel-publication.v1",
            "scientific_scope": scope,
            "retained_numerical_results": result_count,
            "native_datasets": expected["datasets"],
            "distinct_native_collection_units": expected["units"],
            "named_profiles": expected["profiles"],
            "actual_physical_tuples": expected["tuples"],
            "actual_factor_uses": expected["uses"],
            "current_scalar_covariance_replay_maximum_errors": dict(errors),
            "multisite_baseline_windows": baseline,
            "native_producer_authority": authority,
            "scientific_assumptions": protocol,
            "current_writer_scope": "Retained native source/account replay and all-cell scalar covariance verification; no fresh physical transport or native R execution",
            "limits": _tokens(source.get("limitations", []))
            + [
                "Distinct native unit IDs establish deduplication, not empirical statistical independence",
                "Within-result covariance only; shared PPE implies possible cross-result dependence, no joint time-series covariance exported",
                "No historical1128source replay, total vegetation, independent vegetation accuracy, untouched confirmation, qualified external review, reader/application exercise or release completion",
            ],
        },
        "source-coverage.json": {
            "schema_version": "retained-source-observed-panel-coverage.v1",
            "qualified_native_datasets": 59,
            "native_samples": 4548,
            "workbook_rows": eligibility["workbook_rows"],
            "source_account_sha256": digest(directory / "source-eligibility.json"),
            "source_terminal_sha256": digest(directory / "source-terminal.json"),
            "used_dataset_ids": sorted(
                {_integer(m["native_dataset_id"]) for m in source_profiles}
            ),
            "raw_source_reacquisition_or_raw_scan_claim": False,
        },
        "physical-factor-qualification.json": {
            k: v for k, v in review.items() if k != "results"
        },
        "window-domain.json": {
            "declared_grid_windows": 75,
            "classification_counts": dict(
                Counter(r["classification"] for r in classified.values())
            ),
            "windows": [classified[k] for k in sorted(classified)],
            "conditional_independence_assumption": "Separate source-unit identity deduplication from assumed independent multinomial counts",
        },
        "published-model-comparison.json": {
            "schema_version": "retained-published-model-panel-comparison.v1",
            "actual_comparisons": 225,
            "source_cohort_refusals": comparison["scoped_refusals"],
            "baseline_model_comparator_summary": comparison[
                "baseline_model_comparator_summary"
            ],
            "original_comparison_sha256": digest(
                directory / "published-comparison.json"
            ),
            "units": comparison["units"],
            "limits": comparison["limits"],
        },
        "attribution.json": {
            "used_native_datasets": expected["datasets"],
            "distinct_native_collection_units": expected["units"],
            "current_primary_publication_scope_counts": citations[
                "current_primary_publication_scope_counts"
            ],
            "dataset_attribution_accounts": [
                {
                    k: v
                    for k, v in row.items()
                    if k
                    in {
                        "native_dataset_id",
                        "native_collection_unit_id",
                        "native_site_name",
                        "native_constituent_database",
                        "native_dataset_DOI_strings",
                        "original_native_investigator_records",
                        "native_primary_citation_strings",
                        "native_primary_designated_publication_ids",
                        "current_primary_publication_scope",
                        "actual_publication_source_URL",
                        "remaining_attribution_followthrough",
                    }
                }
                for row in _records(citations["dataset_attribution_accounts"])
            ],
            "primary_policy_sources": [
                {
                    "url": p["url"],
                    "http_status": p["http_status"],
                    "sha256": p["response_sha256"],
                }
                for p in _records(policy["records"])
            ],
            "scope": "Current public Neotoma/EPD analytical-use component with source-qualified attribution; historical workbook restrictions/private author material rights and historical source selection remain separate",
        },
    }
