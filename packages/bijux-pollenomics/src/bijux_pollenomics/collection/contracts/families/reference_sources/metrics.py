"""Governed coverage metrics from candidate-only reference reviews."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from .contracts import EMPD2_REVIEW_EVIDENCE, NFI_REVIEW_EVIDENCE

_COVERAGE_KEYS = {
    "schema_version",
    "source_key",
    "reviewed_record_count",
    "scientifically_admitted_record_count",
    "review_status",
    "countries",
    "evidence_paths",
}
_COUNTRY_KEYS = {
    "country_code",
    "source_status",
    "source_reported_record_count",
    "source_reported_site_count",
    "source_reported_observation_count",
    "candidate_record_count",
    "unresolved_record_count",
    "scientifically_admitted_record_count",
    "source_artifact_sha256",
    "reason_codes",
}
_COUNTRY_ORDER = ("SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_COUNT_FIELDS_IN_ORDER = (
    "source_reported_record_count",
    "source_reported_site_count",
    "source_reported_observation_count",
    "candidate_record_count",
    "unresolved_record_count",
    "scientifically_admitted_record_count",
)
_COUNT_FIELDS = set(_COUNT_FIELDS_IN_ORDER)
_EMPD2_SOURCE_SHA256 = (
    "5634e85d922ee0741c41a77d081010c9cc1c113966b283bc52e2051a9d3722e2"
)
_EXPECTED_SOURCE_SHA256 = {
    "empd2": dict.fromkeys(("SE", "DK", "NO", "FI"), _EMPD2_SOURCE_SHA256),
    "nfi": {
        "SE": "a0632bbff92e79c490a6bceb4fa21d69133d7fee7221c93e5b340de6c0b0b375",
        "DK": "ab0a563eafe4755414b44d43b0262322a645983996c873777ff830fb937b9f5f",
        "NO": "3ae1e97f5dec256f2a324832131b40063b4f5a8769c538366a329fffca425ec0",
        "FI": "f789c22acaa5c5ca4a3095479c6084bb87ceadbf7f1372305955a12ee1f2a1d1",
    },
}
_EXPECTED_EVIDENCE_PATHS = {
    "empd2": (
        (
            "reference-sources/empd2-nfi/empd2/source.sqlite3",
            "5634e85d922ee0741c41a77d081010c9cc1c113966b283bc52e2051a9d3722e2",
        ),
        (
            "reference-sources/empd2-nfi/empd2/product-screen.json",
            "6ca256d6e74d6129ee058bea36e8d28c1199bb276d68c0548e0b998853773aaa",
        ),
    ),
    "nfi": (
        (
            "reference-sources/empd2-nfi/nfi/nordic-access.json",
            "b0ab87f8016b561d84cdff16e74500df1b2f1e4013f4600a3d7e0ec0942d6825",
        ),
        (
            "reference-sources/empd2-nfi/nfi/swedish-eligibility.json",
            "a38cba2995ec1c71f7276a4798f2ea79778f4cbbbb587bc507f902b71abc33fd",
        ),
        (
            "reference-sources/empd2-nfi/pairing/spatial-feasibility.json",
            "5d35aed59cb5e3b49582976264837fab1c8d4ffa3dc1937e73bf2f04f32e2c66",
        ),
        (
            "reference-sources/empd2-nfi/nfi/swedish-plot-data.xlsx",
            "862d13f26b868e3b32504f0f714f369018e700e54b245fcd2e16c80640316294",
        ),
    ),
}
_EXPECTED_POSTURE = {
    "empd2": {
        "SE": (
            "source_reported_candidate",
            (
                "candidate_screen_only",
                "cross_source_identity_unresolved",
                "scientific_admission_not_established",
            ),
        ),
        "DK": (
            "source_reported_candidate",
            ("candidate_screen_only", "scientific_admission_not_established"),
        ),
        "NO": (
            "source_reported_candidate",
            (
                "candidate_screen_only",
                "cross_source_identity_unresolved",
                "scientific_admission_not_established",
            ),
        ),
        "FI": (
            "source_reported_candidate",
            (
                "candidate_screen_only",
                "cross_source_identity_unresolved",
                "scientific_admission_not_established",
            ),
        ),
        "UNASSIGNED": ("not_materialized", ("source_partition_not_materialized",)),
        "OUTSIDE": ("not_materialized", ("source_partition_not_materialized",)),
    },
    "nfi": {
        "SE": (
            "source_reported_candidate",
            (
                "candidate_point_plot_geometry_only",
                "regional_area_cover_truth_not_admitted",
                "scientific_admission_not_established",
            ),
        ),
        "DK": (
            "nonpublic_agreement_required",
            ("individual_plot_data_nonpublic", "research_agreement_required"),
        ),
        "NO": (
            "plot_data_unavailable",
            ("plot_download_license_and_site_data_unavailable",),
        ),
        "FI": (
            "access_review_required",
            (
                "authoritative_release_access_review_required",
                "scientific_admission_not_established",
            ),
        ),
        "UNASSIGNED": ("not_applicable", ("partition_not_applicable",)),
        "OUTSIDE": ("not_applicable", ("partition_not_applicable",)),
    },
}


def reference_source_metrics(
    output_root: Path, source_key: str
) -> dict[str, int | None]:
    """Read only counts explicitly governed by candidate review evidence."""
    if source_key == "empd2":
        payload = _load_review(output_root, EMPD2_REVIEW_EVIDENCE)
        valid = _valid_coverage_evidence(payload, source_key)
        countries = payload.get("countries", [])
        return {
            "empd2_source_reported_sample_count": (
                _country_total(countries, "source_reported_record_count")
                if valid
                else None
            ),
            "empd2_source_reported_observation_count": (
                _country_total(countries, "source_reported_observation_count")
                if valid
                else None
            ),
            "empd2_mechanical_candidate_count": (
                _country_total(countries, "candidate_record_count") if valid else None
            ),
            "empd2_unresolved_overlap_lead_count": (
                _country_total(countries, "unresolved_record_count") if valid else None
            ),
            "empd2_scientifically_admitted_record_count": (
                _count(payload.get("scientifically_admitted_record_count"))
                if valid
                else None
            ),
        }
    if source_key == "nfi":
        payload = _load_review(output_root, NFI_REVIEW_EVIDENCE)
        valid = _valid_coverage_evidence(payload, source_key)
        countries = payload.get("countries", [])
        return {
            "nfi_plot_year_record_count": (
                _country_total(countries, "source_reported_record_count")
                if valid
                else None
            ),
            "nfi_tract_plot_site_count": (
                _country_total(countries, "source_reported_site_count")
                if valid
                else None
            ),
            "nfi_proximity_lead_count": (
                _country_total(countries, "candidate_record_count") if valid else None
            ),
            "nfi_scientifically_admitted_record_count": (
                _count(payload.get("scientifically_admitted_record_count"))
                if valid
                else None
            ),
        }
    raise ValueError(f"unsupported reference source: {source_key}")


def valid_reference_review_bytes(content: bytes, source_key: str) -> bool:
    """Require canonical, closed review bytes for the requested source."""
    if source_key not in {"empd2", "nfi"}:
        raise ValueError(f"unsupported reference source: {source_key}")
    return _valid_coverage_evidence(_decode_review(content), source_key)


def _load_review(output_root: Path, repository_path: str) -> dict[str, Any]:
    path = output_root.parent / repository_path
    try:
        return _decode_review(path.read_bytes())
    except OSError:
        return {}


def _decode_review(content: bytes) -> dict[str, Any]:

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate reference-review JSON key")
            value[key] = item
        return value

    try:
        value = json.loads(content, object_pairs_hook=unique_object)
        canonical = (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode()
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {}
    return value if isinstance(value, dict) and content == canonical else {}


def _count(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _valid_coverage_evidence(payload: dict[str, Any], source_key: str) -> bool:
    countries = payload.get("countries")
    evidence_paths = payload.get("evidence_paths")
    return bool(
        set(payload) == _COVERAGE_KEYS
        and payload.get("schema_version") == "source-country-coverage-evidence.v1"
        and payload.get("source_key") == source_key
        and payload.get("review_status") == "candidate_only"
        and _count(payload.get("reviewed_record_count")) is not None
        and _count(payload.get("scientifically_admitted_record_count")) == 0
        and isinstance(countries, list)
        and all(isinstance(country, dict) for country in countries)
        and [country.get("country_code") for country in countries]
        == list(_COUNTRY_ORDER)
        and all(
            set(country) == _COUNTRY_KEYS
            and isinstance(country.get("reason_codes"), list)
            and (
                country.get("source_status"),
                tuple(country["reason_codes"]),
            )
            == _EXPECTED_POSTURE[source_key][country["country_code"]]
            and all(_nullable_count(country.get(field)) for field in _COUNT_FIELDS)
            and country.get("scientifically_admitted_record_count") in {None, 0}
            and all(
                isinstance(reason, str) and bool(reason.strip())
                for reason in country["reason_codes"]
            )
            and (
                country.get("source_artifact_sha256") is None
                if country["country_code"] in {"UNASSIGNED", "OUTSIDE"}
                else country.get("source_artifact_sha256")
                == _EXPECTED_SOURCE_SHA256[source_key][country["country_code"]]
            )
            for country in countries
        )
        and isinstance(evidence_paths, list)
        and bool(evidence_paths)
        and all(isinstance(evidence, dict) for evidence in evidence_paths)
        and all(
            isinstance(evidence, dict)
            and set(evidence) == {"path", "sha256"}
            and isinstance(evidence["path"], str)
            and bool(evidence["path"].strip())
            and isinstance(evidence["sha256"], str)
            and _SHA256.fullmatch(evidence["sha256"]) is not None
            for evidence in evidence_paths
        )
        and len({evidence["path"] for evidence in evidence_paths})
        == len(evidence_paths)
        and tuple((evidence["path"], evidence["sha256"]) for evidence in evidence_paths)
        == _EXPECTED_EVIDENCE_PATHS[source_key]
        and _source_denominator_closes(payload, source_key)
    )


def _nullable_count(value: object) -> bool:
    return value is None or _count(value) is not None


def _country_total(countries: object, field: str) -> int:
    assert isinstance(countries, list)
    return sum(
        value
        for country in countries
        if isinstance(country, dict)
        and isinstance((value := country.get(field)), int)
        and not isinstance(value, bool)
    )


def _source_denominator_closes(payload: dict[str, Any], source_key: str) -> bool:
    countries = payload["countries"]
    records = tuple(country["source_reported_record_count"] for country in countries)
    if source_key == "empd2":
        expected_empd2 = (
            (132, None, 3_379, 131, 21, 0),
            (20, None, 968, 20, 0, 0),
            (622, None, 19_774, 622, 66, 0),
            (141, None, 3_040, 141, 25, 0),
            (None, None, None, None, None, None),
            (None, None, None, None, None, None),
        )
        return bool(
            payload["reviewed_record_count"] == 915
            and records == (132, 20, 622, 141, None, None)
            and tuple(
                tuple(country[field] for field in _COUNT_FIELDS_IN_ORDER)
                for country in countries
            )
            == expected_empd2
            and _country_total(countries, "source_reported_observation_count") == 27_161
            and _country_total(countries, "candidate_record_count") == 914
            and _country_total(countries, "unresolved_record_count") == 112
        )
    expected_nfi = (
        (43_892, 6_018, None, 16, 16, 0),
        (None, None, None, None, None, 0),
        (None, None, None, None, None, 0),
        (None, None, None, None, None, 0),
        (None, None, None, None, None, None),
        (None, None, None, None, None, None),
    )
    return bool(
        payload["reviewed_record_count"] == 43_892
        and records == (43_892, None, None, None, None, None)
        and tuple(country["source_reported_site_count"] for country in countries)
        == (6_018, None, None, None, None, None)
        and all(
            country["source_reported_observation_count"] is None
            for country in countries
        )
        and tuple(
            tuple(country[field] for field in _COUNT_FIELDS_IN_ORDER)
            for country in countries
        )
        == expected_nfi
        and _country_total(countries, "candidate_record_count") == 16
    )
