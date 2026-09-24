from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

from bijux_pollenomics.collection.contracts.capabilities import (
    build_source_capability_contract_payload,
)
from bijux_pollenomics.collection.contracts.families import (
    build_source_family_contracts,
    build_source_family_state_rows,
)
from bijux_pollenomics.collection.contracts.families.reference_sources.metrics import (
    reference_source_metrics,
)

_EMPD2_SOURCE_SHA256 = (
    "5634e85d922ee0741c41a77d081010c9cc1c113966b283bc52e2051a9d3722e2"
)
_SOURCE_SHA256 = {
    "empd2": dict.fromkeys(("SE", "DK", "NO", "FI"), _EMPD2_SOURCE_SHA256),
    "nfi": {
        "SE": "a0632bbff92e79c490a6bceb4fa21d69133d7fee7221c93e5b340de6c0b0b375",
        "DK": "ab0a563eafe4755414b44d43b0262322a645983996c873777ff830fb937b9f5f",
        "NO": "3ae1e97f5dec256f2a324832131b40063b4f5a8769c538366a329fffca425ec0",
        "FI": "f789c22acaa5c5ca4a3095479c6084bb87ceadbf7f1372305955a12ee1f2a1d1",
    },
}
_EVIDENCE_PATHS = {
    "empd2": [
        {
            "path": "artifacts/v3/reference/empd2-intake001/EMPD2.sqlite3",
            "sha256": "5634e85d922ee0741c41a77d081010c9cc1c113966b283bc52e2051a9d3722e2",
        },
        {
            "path": "artifacts/v3/reference/empd2-product-screen001/report003.json",
            "sha256": "6ca256d6e74d6129ee058bea36e8d28c1199bb276d68c0548e0b998853773aaa",
        },
    ],
    "nfi": [
        {
            "path": "artifacts/v3/reference/nordic-nfi-access-20260922/receipt.json",
            "sha256": "b0ab87f8016b561d84cdff16e74500df1b2f1e4013f4600a3d7e0ec0942d6825",
        },
        {
            "path": "artifacts/v3/reference/swedish-nfi-eligibility002/report.json",
            "sha256": "a38cba2995ec1c71f7276a4798f2ea79778f4cbbbb587bc507f902b71abc33fd",
        },
        {
            "path": "artifacts/v3/reference/empd2-nfi-feasibility001/report004.json",
            "sha256": "5d35aed59cb5e3b49582976264837fab1c8d4ffa3dc1937e73bf2f04f32e2c66",
        },
        {
            "path": "artifacts/v3/reference/swedish-nfi-plot001/swe_nfi_plotdata2.xlsx",
            "sha256": "862d13f26b868e3b32504f0f714f369018e700e54b245fcd2e16c80640316294",
        },
    ],
}


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode()


def _coverage_evidence(source_key: str) -> dict[str, object]:
    is_empd2 = source_key == "empd2"
    record_counts = (
        (132, 20, 622, 141, None, None)
        if is_empd2
        else (43_892, None, None, None, None, None)
    )
    site_counts = (None,) * 6 if is_empd2 else (6_018, None, None, None, None, None)
    observation_counts = (
        (3_379, 968, 19_774, 3_040, None, None) if is_empd2 else (None,) * 6
    )
    candidate_counts = (
        (131, 20, 622, 141, None, None)
        if is_empd2
        else (16, None, None, None, None, None)
    )
    unresolved_counts = (
        (21, 0, 66, 25, None, None) if is_empd2 else (16, None, None, None, None, None)
    )
    postures = {
        "empd2": (
            (
                "source_reported_candidate",
                [
                    "candidate_screen_only",
                    "cross_source_identity_unresolved",
                    "scientific_admission_not_established",
                ],
            ),
            (
                "source_reported_candidate",
                ["candidate_screen_only", "scientific_admission_not_established"],
            ),
            (
                "source_reported_candidate",
                [
                    "candidate_screen_only",
                    "cross_source_identity_unresolved",
                    "scientific_admission_not_established",
                ],
            ),
            (
                "source_reported_candidate",
                [
                    "candidate_screen_only",
                    "cross_source_identity_unresolved",
                    "scientific_admission_not_established",
                ],
            ),
            ("not_materialized", ["source_partition_not_materialized"]),
            ("not_materialized", ["source_partition_not_materialized"]),
        ),
        "nfi": (
            (
                "source_reported_candidate",
                [
                    "candidate_point_plot_geometry_only",
                    "regional_area_cover_truth_not_admitted",
                    "scientific_admission_not_established",
                ],
            ),
            (
                "nonpublic_agreement_required",
                ["individual_plot_data_nonpublic", "research_agreement_required"],
            ),
            (
                "plot_data_unavailable",
                ["plot_download_license_and_site_data_unavailable"],
            ),
            (
                "access_review_required",
                [
                    "authoritative_release_access_review_required",
                    "scientific_admission_not_established",
                ],
            ),
            ("not_applicable", ["partition_not_applicable"]),
            ("not_applicable", ["partition_not_applicable"]),
        ),
    }
    countries = []
    for index, country_code in enumerate(
        ("SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE")
    ):
        countries.append(
            {
                "country_code": country_code,
                "source_status": postures[source_key][index][0],
                "source_reported_record_count": record_counts[index],
                "source_reported_site_count": site_counts[index],
                "source_reported_observation_count": observation_counts[index],
                "candidate_record_count": candidate_counts[index],
                "unresolved_record_count": unresolved_counts[index],
                "scientifically_admitted_record_count": 0 if index < 4 else None,
                "source_artifact_sha256": (
                    _SOURCE_SHA256[source_key][country_code] if index < 4 else None
                ),
                "reason_codes": postures[source_key][index][1],
            }
        )
    return {
        "schema_version": "source-country-coverage-evidence.v1",
        "source_key": source_key,
        "reviewed_record_count": 915 if is_empd2 else 43_892,
        "scientifically_admitted_record_count": 0,
        "review_status": "candidate_only",
        "countries": countries,
        "evidence_paths": deepcopy(_EVIDENCE_PATHS[source_key]),
    }


def test_reference_sources_append_after_existing_family_order() -> None:
    contracts = build_source_family_contracts()

    assert tuple(contract.source_key for contract in contracts) == (
        "landclim",
        "neotoma",
        "sead",
        "raa",
        "boundaries",
        "svar",
        "aadr",
        "animal_adna",
        "hyde",
        "empd2",
        "nfi",
    )


def test_reference_source_lifecycle_is_review_only(tmp_path: Path) -> None:
    output_root = tmp_path / "data"
    for source_key in ("empd2", "nfi"):
        path = output_root / source_key / "review/country_coverage_evidence.json"
        path.parent.mkdir(parents=True)
        path.write_bytes(_canonical_bytes(_coverage_evidence(source_key)))

    rows = {
        row.source_key: row
        for row in build_source_family_state_rows(output_root, counts={})
    }

    for source_key in ("empd2", "nfi"):
        row = rows[source_key]
        assert row.raw_status == "missing"
        assert row.normalized_status == "missing"
        assert row.reviewed_status == "present"
        assert row.published_status == "missing"
        assert row.authority_status == "review_required"
        assert row.publication_posture == "review_required_not_publication_ready"
        assert "source_authority_review_required" in row.blocking_reasons
    assert rows["empd2"].coverage_metrics == {
        "empd2_source_reported_sample_count": 915,
        "empd2_source_reported_observation_count": 27_161,
        "empd2_mechanical_candidate_count": 914,
        "empd2_unresolved_overlap_lead_count": 112,
        "empd2_scientifically_admitted_record_count": 0,
    }
    assert rows["nfi"].coverage_metrics == {
        "nfi_plot_year_record_count": 43_892,
        "nfi_tract_plot_site_count": 6_018,
        "nfi_proximity_lead_count": 16,
        "nfi_scientifically_admitted_record_count": 0,
    }


def test_reference_metrics_reject_corrupt_identity_and_denominators(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "data"
    path = output_root / "empd2/review/country_coverage_evidence.json"
    path.parent.mkdir(parents=True)
    baseline = _coverage_evidence("empd2")
    attacks = []
    bad_digest = deepcopy(baseline)
    bad_digest["countries"][0]["source_artifact_sha256"] = "z" * 64
    attacks.append(bad_digest)
    substituted_digest = deepcopy(baseline)
    substituted_digest["countries"][0]["source_artifact_sha256"] = "3" * 64
    attacks.append(substituted_digest)
    substituted_evidence = deepcopy(baseline)
    substituted_evidence["evidence_paths"][0]["sha256"] = "4" * 64
    attacks.append(substituted_evidence)
    reordered_evidence = deepcopy(baseline)
    reordered_evidence["evidence_paths"].reverse()
    attacks.append(reordered_evidence)
    malformed_evidence = deepcopy(baseline)
    malformed_evidence["evidence_paths"] = ["not-an-object"]
    attacks.append(malformed_evidence)
    changed_posture = deepcopy(baseline)
    changed_posture["countries"][0]["source_status"] = "available"
    attacks.append(changed_posture)
    boolean_count = deepcopy(baseline)
    boolean_count["countries"][0]["candidate_record_count"] = True
    attacks.append(boolean_count)
    bad_order = deepcopy(baseline)
    bad_order["countries"][0], bad_order["countries"][1] = (
        bad_order["countries"][1],
        bad_order["countries"][0],
    )
    attacks.append(bad_order)
    bad_denominator = deepcopy(baseline)
    bad_denominator["reviewed_record_count"] = 914
    attacks.append(bad_denominator)

    for attack in attacks:
        path.write_bytes(_canonical_bytes(attack))
        metrics = reference_source_metrics(output_root, "empd2")
        assert metrics and set(metrics.values()) == {None}
        row = next(
            row
            for row in build_source_family_state_rows(output_root, counts={})
            if row.source_key == "empd2"
        )
        assert row.reviewed_status == "missing"


def test_reference_review_requires_canonical_unique_json_keys(tmp_path: Path) -> None:
    output_root = tmp_path / "data"
    for source_key in ("empd2", "nfi"):
        path = output_root / source_key / "review/country_coverage_evidence.json"
        path.parent.mkdir(parents=True)
        baseline = _coverage_evidence(source_key)
        canonical = _canonical_bytes(baseline)
        duplicate = canonical.replace(
            b'      "country_code": "SE",',
            b'      "country_code": "SE",\n      "country_code": "SE",',
            1,
        )

        for refused in (b"{}\n", json.dumps(baseline).encode(), duplicate):
            path.write_bytes(refused)
            row = next(
                row
                for row in build_source_family_state_rows(output_root, counts={})
                if row.source_key == source_key
            )
            assert row.reviewed_status == "missing"
            assert set(row.coverage_metrics.values()) == {None}


def test_reference_review_hook_does_not_change_existing_family_layers(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "data"
    review = output_root / "landclim/review/spatiotemporal_review.json"
    review.parent.mkdir(parents=True)
    review.write_bytes(b"not canonical governed reference JSON")

    row = next(
        row
        for row in build_source_family_state_rows(output_root, counts={})
        if row.source_key == "landclim"
    )

    assert row.reviewed_status == "present"


def test_reference_sources_extend_capabilities_without_normative_promotion() -> None:
    payload = build_source_capability_contract_payload()
    sources = payload["sources"]
    assert isinstance(sources, list)

    assert payload["source_count"] == 11
    assert payload["dimension_count"] == 17
    assert payload["normative_contract"]["source_count"] == 7
    assert payload["extension_sources"] == ["aadr", "empd2", "hyde", "nfi"]
    assert len(sources) * payload["dimension_count"] == 187
    by_key = {source["source_key"]: source for source in sources}
    assert by_key["empd2"]["human_review_required"] is True
    assert by_key["nfi"]["human_review_required"] is True
