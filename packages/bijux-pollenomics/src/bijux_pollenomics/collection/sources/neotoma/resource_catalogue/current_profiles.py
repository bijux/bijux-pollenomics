"""Explicit derived-current catalogue namespace independent of original v1 results."""

from __future__ import annotations

from typing import Any

from ..capture.resources.current.profiles import (
    CURRENT_SOURCE_TYPES,
    NeotomaCurrentSource,
    _UnavailableCurrentSource,
    parse_neotoma_current_source,
    summarize_current_source,
)
from ..capture.resources.models import DEVELOPMENT_ROLES, NeotomaResourceSpec

CURRENT_SOURCE_PROFILE_SCHEMA = "neotoma-current-source-qualification.v1"


def current_profiles_enabled(catalogue: dict[str, Any]) -> bool:
    if "current_source_profile_schema" not in catalogue:
        return False
    if catalogue["current_source_profile_schema"] != CURRENT_SOURCE_PROFILE_SCHEMA:
        raise ValueError("Catalogue current source profile schema is unsupported")
    return True


def validate_current_source_claims(row: dict[str, Any], enabled: bool) -> None:
    """Refuse contradictory compact claims before an external body can be opened."""
    current = row["versions"]["current"]
    fields = {key for key in current if key.startswith("current_source_")}
    known = row["dataset_type"] in CURRENT_SOURCE_TYPES
    if not enabled or not known:
        if fields:
            raise ValueError("Current source claims lack a declared supported profile")
        return
    status = current.get("current_source_qualification_status")
    allowed = {
        "parsed_current_source",
        "refused_current_source",
        "unavailable_current_api_empty",
        "not_qualified_source_result",
        "not_qualified_exposure_role",
    }
    if (
        not isinstance(status, str)
        or status not in allowed
        or current.get("qualification_status") != "not_qualified"
    ):
        raise ValueError("Current source original or derived qualification differs")
    if current["acquisition_status"] in {"parsed_native", "reused_qualified_native"}:
        raise ValueError("Current source capture-v1 classification was relabelled")
    expected = {"current_source_qualification_status"}
    if status == "parsed_current_source":
        expected.add("current_source_summary")
    elif status in {"refused_current_source", "unavailable_current_api_empty"}:
        expected.add("current_source_qualification_reason")
        if not isinstance(current.get("current_source_qualification_reason"), str):
            raise ValueError("Current source refusal reason is not native text")
    if fields != expected:
        raise ValueError("Current source qualification namespace differs")
    if row["exposure_role"] not in DEVELOPMENT_ROLES:
        if status != "not_qualified_exposure_role":
            raise ValueError("Current source exposure role refuses qualification")
        return
    if status == "not_qualified_exposure_role":
        raise ValueError(
            "Current source exposure posture differs from source inventory"
        )
    qualified_attempt = status in {
        "parsed_current_source",
        "refused_current_source",
        "unavailable_current_api_empty",
    }
    if qualified_attempt != (
        current["acquisition_status"] == "unsupported_dataset_type"
    ):
        raise ValueError(
            "Current source qualification differs from original acquisition"
        )
    if (
        qualified_attempt
        and current.get("source_terminal_status") != "unsupported_dataset_type"
    ):
        raise ValueError("Current source original terminal classification differs")
    if status != "parsed_current_source":
        return
    summary = current["current_source_summary"]
    if (
        not isinstance(summary, dict)
        or summary.get("parser_profile") != "current_native_proxy_hierarchy.v1"
        or summary.get("dataset_type") != row["dataset_type"]
        or summary.get("units_interpreted") is not False
        or summary.get("physical_depth_or_chronology_inferred") is not False
        or summary.get("scientific_admission") != "not_asserted"
        or summary.get("biological_denominator") != "not_established"
        or summary.get("sample_population") != "array"
        or summary.get("native_samples_pointer")
        != "/data/0/site/collectionunit/dataset/samples"
    ):
        raise ValueError("Current source summary profile or interpretation differs")
    for name in (
        "sample_rows",
        "identified_sample_rows",
        "unidentified_sample_rows",
        "datum_rows",
    ):
        if type(summary.get(name)) is not int or summary[name] < 0:
            raise ValueError(
                "Current source summary count is not a native nonnegative integer"
            )
    if (
        summary["sample_rows"]
        != summary["identified_sample_rows"] + summary["unidentified_sample_rows"]
    ):
        raise ValueError("Current source sample count partition differs")
    counts = current.get("native_counts")
    if not isinstance(counts, dict) or any(
        type(counts.get(key)) is not int or counts[key] != summary[value]
        for key, value in (
            ("raw_sample_rows", "sample_rows"),
            ("raw_datum_rows", "datum_rows"),
        )
    ):
        raise ValueError("Current source native and summary counts differ")
    source = current.get("source")
    if (
        not isinstance(source, dict)
        or source.get("source_kind") != "source_http_attempt"
        or source.get("body_complete") is not True
        or source.get("http_status") != 200
        or source.get("requested_url")
        != f"https://api.neotomadb.org/v2.0/data/downloads/{row['dataset_id']}"
    ):
        raise ValueError("Current source summary has no matching current HTTP entity")


def current_source_projection(
    resource: NeotomaResourceSpec,
    status: str,
    body: bytes | None,
    body_sha256: str | None,
) -> tuple[dict[str, Any], NeotomaCurrentSource | None]:
    """Derive format facts only; the owning capture's classification is unchanged."""
    if resource.dataset_type not in CURRENT_SOURCE_TYPES:
        return {}, None
    result: dict[str, Any] = {
        "current_source_qualification_status": "not_qualified_source_result"
    }
    if resource.exposure_role not in DEVELOPMENT_ROLES:
        result["current_source_qualification_status"] = "not_qualified_exposure_role"
        return result, None
    if status != "unsupported_dataset_type":
        return result, None
    if body is None or body_sha256 is None:
        raise ValueError("Derived current source has no authenticated source buffer")
    try:
        parsed = parse_neotoma_current_source(
            resource, body, expected_body_sha256=body_sha256
        )
    except _UnavailableCurrentSource as error:
        result.update(
            current_source_qualification_status="unavailable_current_api_empty",
            current_source_qualification_reason=str(error),
        )
    except ValueError as error:
        result.update(
            current_source_qualification_status="refused_current_source",
            current_source_qualification_reason=str(error),
        )
    else:
        result.update(
            current_source_qualification_status="parsed_current_source",
            current_source_summary=summarize_current_source(parsed),
        )
        return result, parsed
    return result, None
