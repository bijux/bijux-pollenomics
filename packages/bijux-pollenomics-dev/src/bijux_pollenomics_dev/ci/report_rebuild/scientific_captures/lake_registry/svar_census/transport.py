"""Admit bounded normalized-source aggregate observations without provider geometry payloads."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ....contracts import JsonObject, ReportRebuildError
from ..svar import _exact, _file, _json, _object, _require
from .projection import public_census, validate_public_joins

CAPTURE = "data/surface-reference/svar-feature-census-capture/capture.json"
CAPTURE_SHA256 = "d121668fe9abb7123d73593fce0c13f098e25ce04a074f8b210e21ccf91df0db"
OWNER = "source-relations/svar/normalized-export/feature-census"
REPORT = "docs/report/source-relations/svar/normalized-export/feature-census.json"
PRODUCT_SHA256 = "5ce50017af55e496ca391d34997ce5f182296f8e9db82ea20c118016d30ff0db"
PRODUCT_BYTES = 4689
MEMBER_COUNT = 102
ORIGINAL_CANDIDATE = "5c120dcb67d31b50d9da6d7bf5efb41dcb0ddf87"
RECEIPTS = {
    "plan.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-svar-normalized-feature-census/plan.json",
        "sha256": "6d3399fd228f43ea97a5fefb07084a688252ff67b6ed75838de0f3aed7ab3633",
        "bytes": 1459087,
    },
    "terminal.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-svar-normalized-feature-census/terminal.json",
        "sha256": "9d5036b1b005143de1f09db1248e977271bbf879ce5b9eb838260c726e6f1d8f",
        "bytes": 8113,
    },
    "svar-feature-census-terminal.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-svar-normalized-feature-census/svar-feature-census-terminal.json",
        "sha256": "10bd94f8a880b6f3f81cab8265d0ed979bc10f4ff6e1ba0adc28ced2dea0b03c",
        "bytes": 1625,
    },
    "census.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-svar-normalized-feature-census/census.json",
        "sha256": "e32469bf881194419b26136f24814a989c3b0980f274a33a2b252ff390611230",
        "bytes": 3800,
    },
    "census-runtime.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-svar-normalized-feature-census/census-runtime.json",
        "sha256": "08d40b95ed0f1ab44a10f3148c7484465b01414e9d3fc7f046238d1ad06fc46e",
        "bytes": 89628,
    },
    "independent-source-review.json": {
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-svar-normalized-feature-census/independent-source-review.json",
        "sha256": "f8e024f70f71c0d9471da5c3ec12ce40073e22b112dbb7262d2b51b10b7c4f0d",
        "bytes": 93780,
    },
}
SCOPE_COUNTS = {
    "runtime_identity_only": 3482,
    "private_normalized_source_identity_only": 3,
    "retained_execution_source": 86,
    "private_bounded_inspection_metadata_identity_only": 1,
    "existing_public_input_identity_only": 6,
}


def _pin(path: Path) -> dict[str, Any]:
    return {
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


def _member(value: object) -> str:
    _require(type(value) is str and bool(value), "Census member name missing")
    assert isinstance(value, str)
    name = PurePosixPath(value)
    _require(
        not name.is_absolute()
        and ".." not in name.parts
        and name.as_posix() == value
        and "\\" not in value,
        "Census member escapes capsule",
    )
    return value


def _array(path: Path) -> list[Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            _require(key not in result, "Duplicate census array JSON key")
            result[key] = value
        return result

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        _require(type(value) is list, "Census array required")
        assert isinstance(value, list)
        return value
    except (OSError, ValueError) as error:
        raise ReportRebuildError("Invalid census array metadata") from error


def _claims(capture: dict[str, Any]) -> None:
    expected = {
        "schema_version": "svar-feature-census-source-capture.v1",
        "owner_id": "source-relations/svar/normalized-export/feature-census",
        "original_execution_candidate": "5c120dcb67d31b50d9da6d7bf5efb41dcb0ddf87",
        "retention_mode": "authored_aggregate_and_execution_source_custody",
        "new_metadata_native_job_claimed": False,
        "publication_path": "docs/report/source-relations/svar/normalized-export/feature-census.json",
        "publication_member": "publication/feature-census.json",
        "member_count": 102,
        "original_input_count": 3578,
        "private_full_registry_identity": {
            "path": "/Users/bijan/bijux/-bijux-pollenomics-data/svar/normalized-export-2026-09-08/sweden_lake_registry.geojson",
            "sha256": "d9a1943d1a35e7ab6d48e06156fef625e7c62c8bc410cecf9d8f592ccb07dfd8",
            "bytes": 261041034,
        },
        "private_feature_ledger_identity": {
            "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-svar-normalized-feature-census/feature-ledger.jsonl",
            "sha256": "4b8a210b427bd248e933d4f86c101b2855d8c2706634cfd175e3fb096b184132",
            "bytes": 57098367,
        },
        "private_original_join_metadata_identity": {
            "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/current-svar-normalized-feature-census/subset-native-joins.json",
            "sha256": "d065f3b8ae95a34b04b5cfba2817e735f933e49a665ac57730cff904169f7643",
            "bytes": 135987,
        },
        "raw_properties_geometry_or_native_ID_values_published": False,
        "private_first_feature_inspection_values_published": False,
        "runtime_payloads_published": False,
        "source_payload_published": False,
        "public_join_projection_rows": 99,
        "public_join_projection_rule": "Only subset_index,match_count and seven-field presence/typed-equality flags retained; record_id/full_source_index and raw native properties/geometry remain private.",
        "scope": "Actual normalized file measurements only. Original WFS acquisition/version/rights, CRS/units/effective basin area, old40523fullpopulation identities, chronology, human review and governing registry/ranking remain unqualified.",
    }
    expected.update(
        original_execution_receipts=RECEIPTS, original_input_scope_counts=SCOPE_COUNTS
    )
    _require(
        set(capture) == set(expected) | {"members"},
        "Census capsule claim fields differ",
    )
    _exact({key: capture[key] for key in expected}, expected)


def _native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    outer: dict[str, Any],
    census: dict[str, Any],
    runtime: dict[str, Any],
    review: dict[str, Any],
) -> None:
    _require(
        all(
            row.get("candidate") == ORIGINAL_CANDIDATE
            for row in (plan, common, outer, census, runtime, review)
        ),
        "Census native epoch differs",
    )
    checksum = RECEIPTS["plan.json"]["sha256"]
    _require(
        common.get("plan_sha256") == outer.get("plan_sha256") == checksum
        and all(
            _object(row.get("plan")).get("sha256") == checksum
            for row in (census, runtime, review)
        ),
        "Census native plan binding differs",
    )
    for value in (
        common.get("actual_exit"),
        outer.get("actual_exit"),
        outer.get("common_actual_exit"),
        runtime.get("source_exit"),
        runtime.get("metadata_exit"),
        review.get("actual_exit"),
    ):
        _exact(value, 0)
    _require(
        common.get("canonical_before")
        == common.get("canonical_after")
        == plan.get("canonical_identity")
        and common.get("before_pin_mismatches")
        == common.get("after_pin_mismatches")
        == []
        and common.get("absent_input_paths_unchanged") is True,
        "Census original source/runtime/candidate custody differs",
    )
    _require(
        outer.get("outer_timed_out") is False
        and all(
            outer.get(key) is True
            for key in (
                "completed_whole_wall_bound_pass",
                "framework_membership_unchanged",
                "absent_paths_unchanged",
                "memory_bound_pass",
                "storage_bound_pass",
            )
        ),
        "Census native resource/namespace bound differs",
    )
    _require(
        _object(outer.get("common_terminal")).get("sha256")
        == RECEIPTS["terminal.json"]["sha256"]
        and _object(outer.get("independent_review")).get("sha256")
        == RECEIPTS["independent-source-review.json"]["sha256"],
        "Census terminal/review hash joins differ",
    )
    _exact(outer.get("actual_native_stage_exits"), [0, 0])
    _exact(len(plan["stages"]), 2)
    _exact(len(common["stages"]), 2)
    for intended, actual in zip(plan["stages"], common["stages"], strict=True):
        _require(
            all(actual.get(key) == value for key, value in intended.items())
            and actual.get("timed_out") is False,
            "Census actual argv or stage timeout differs",
        )
        _exact(actual.get("actual_exit"), 0)
    _require(
        _object(review.get("census")).get("sha256")
        == RECEIPTS["census.json"]["sha256"],
        "Census independent product hash differs",
    )
    _exact(census.get("source"), plan.get("full_registry"))
    _exact(census.get("feature_ledger"), review.get("feature_ledger"))
    products = {row["path"]: row for row in common["products"]}
    for identity in (review["feature_ledger"], review["subset_joins"]):
        _exact(products.get(identity["path"]), identity)
    _require(
        review.get("complete_independent_source_and_typed_ledger_equal") is True,
        "Census independent complete comparison missing",
    )


def validated_svar_feature_census_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    rows = [row for row in owners if row.get("owner_id") == OWNER]
    if (
        not any(row.get("role") == "retained_source" for row in rows)
        and not (repository / CAPTURE).exists()
    ):
        return (), {}
    _require(
        len(rows) == 1
        and rows[0].get("role") == "retained_source"
        and rows[0].get("paths") == [REPORT]
        and rows[0].get("producer_paths") == rows[0].get("producer_inputs") == [],
        "Census exact retained owner differs",
    )
    path = _file(repository, CAPTURE)
    _require(_pin(path)["sha256"] == CAPTURE_SHA256, "Sealed census capsule differs")
    capture = _json(path)
    _claims(capture)
    prefix = path.parent.relative_to(repository).as_posix()
    members = _object(capture.get("members"))
    _exact(len(members), MEMBER_COUNT)
    for name, record in members.items():
        _exact(_pin(_file(repository, prefix + "/" + _member(name))), record)
    physical = set()
    for item in path.parent.rglob("*"):
        _require(
            not item.is_symlink() and (item.is_file() or item.is_dir()),
            "Census capsule alias/special entry",
        )
        if item.is_file():
            physical.add(item.relative_to(path.parent).as_posix())
    _require(
        physical == set(members) | {"capture.json"},
        "Census physical member inventory differs",
    )
    records = []
    for name, identity in RECEIPTS.items():
        file = _file(repository, prefix + "/execution/" + name)
        _exact(_pin(file), {key: identity[key] for key in ("sha256", "bytes")})
        records.append(_json(file))
    plan, common, outer, census, runtime, review = records
    _native_records(plan, common, outer, census, runtime, review)
    for stage in common["stages"]:
        for kind in ("stdout", "stderr"):
            name = stage["id"] + "." + kind
            _require(
                Path(stage[kind]).name == name
                and _pin(_file(repository, prefix + "/execution/" + name))["sha256"]
                == stage[kind + "_sha256"],
                "Census native output log differs",
            )
    custody = _array(_file(repository, prefix + "/original-input-custody.json"))
    _exact([_object(row).get("original") for row in custody], plan["input_pins"])
    _exact(len(custody), 3578)
    counts: dict[str, int] = {}
    source_root = Path(plan["stages"][0]["argv"][4]).parent
    for raw in custody:
        row = _object(raw)
        original = _object(row["original"])
        scope = row["scope"]
        member = row["member"]
        counts[scope] = counts.get(scope, 0) + 1
        if member is not None:
            _exact(
                members.get(_member(member)),
                {key: original[key] for key in ("sha256", "bytes")},
            )
        origin = Path(original["path"])
        if origin.is_relative_to(source_root):
            if origin.name == "first-feature-forensics.json":
                _require(
                    scope == "private_bounded_inspection_metadata_identity_only"
                    and member is None,
                    "Private bounded inspection values leaked",
                )
            else:
                _require(
                    scope == "retained_execution_source"
                    and member
                    == "source-control/" + origin.relative_to(source_root).as_posix(),
                    "Actual census source control missing",
                )
        else:
            _require(
                member is None
                and scope
                in {
                    "runtime_identity_only",
                    "private_normalized_source_identity_only",
                    "existing_public_input_identity_only",
                },
                "Census source omission undeclared",
            )
    _exact(counts, SCOPE_COUNTS)
    joins = _array(_file(repository, prefix + "/public-subset-joins.json"))
    validate_public_joins(joins)
    expected = public_census(census, review, joins)
    product = _file(repository, REPORT)
    retained = _file(repository, prefix + "/publication/feature-census.json")
    _exact(_json(retained), expected)
    _require(
        product.read_bytes() == retained.read_bytes()
        and _pin(product) == {"sha256": PRODUCT_SHA256, "bytes": PRODUCT_BYTES},
        "Census current public aggregate differs",
    )
    projection = _json(
        _file(repository, prefix + "/projection/public-projection-qualification.json")
    )
    _require(
        projection.get("all99redacted_rows_equal_named_original_projection") is True
        and projection.get("private_registry_or_feature_ledger_read") is False
        and projection.get("native_or_model_or_actual_preparer_executed") is False
        and projection.get("metadata_retention_job_claimed") is False,
        "Census public projection scope differs",
    )
    _exact(
        projection.get("original_raw_join_metadata_sha256"),
        review["subset_joins"]["sha256"],
    )
    _exact(projection.get("public_witness_sha256"), PRODUCT_SHA256)
    entry = tracked_by_path.get(REPORT)
    _require(
        entry is not None
        and entry.kind == "file"
        and entry.sha256 == PRODUCT_SHA256
        and entry.size == PRODUCT_BYTES,
        "Census tracked aggregate inventory differs",
    )
    assert entry is not None
    return (entry,), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "original_native_stages": [0, 0],
        "paths": [entry.path],
        "measured_features": 40565,
        "subset_unique_matches": 99,
        "source_population_difference": 42,
        "identities_of_42_difference_established": False,
        "source_WFS_rights_CRS_units_human_or_ranking_admitted": False,
        "raw_property_geometry_ID_or_runtime_payloads_published": False,
        "new_metadata_native_execution_claimed": False,
    }
