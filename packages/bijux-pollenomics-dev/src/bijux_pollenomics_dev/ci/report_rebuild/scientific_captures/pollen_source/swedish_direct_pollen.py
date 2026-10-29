"""Bind observed direct-pollen preparation while preserving historical unresolved artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import ReportOwnershipError, _regular_confined_file

CAPTURE: Any = (
    "data/surface-reference/swedish-direct-pollen-source-capture/capture.json"
)
CAPTURE_SHA256: Any = "fed646a3620b7266f8ab87dd44cdbfac72461179d74df29410460deb81672449"
CAPTURE_BYTES: Any = 566411
MEMBER_COUNT: Any = 2276
MEMBERS_SHA256: Any = "6219f0d4b95f44a0d157fa7bd9e11a7549d88fe30beed23a75c0873ee7eda3a2"
ORIGINAL_CANDIDATE: Any = "65d4752111915e1157315004d59603469af2d644"
FAMILIES: Any = ["swedish-lake-transfer", "swedish-neotoma-holdout"]
PREPARED_NAMES: Any = [
    "input-manifest.json",
    "inputs/metadata-SE.json.gz",
    "inputs/training-SE.json.gz",
    "sealed-outcomes/outcomes-SE.json.gz",
]
INPUT_SCOPE_COUNTS: Any = {
    "qualified_runtime_or_dependency_authority_identity_only": 59886,
    "private_source_identity_only": 1,
    "retained_executed_controller_or_declared_metadata": 22,
    "retained_historical_publication_or_owner_metadata_input": 32,
    "public_relational_input_identity_only": 20,
    "retained_public_first_party_source_or_resource": 2164,
    "bytecode_identity_only": 4356,
}
EXPECTED_SCOPE: Any = {
    "new_native_retention_execution_claimed": False,
    "private_runtime_bytecode_or_relational_input_payload_published": False,
    "historical_protocol_freeze_reference_verification_produced_or_certified": False,
    "prepared_product_count": 8,
    "native_total_compared_products": 20,
    "historical_unresolved_count": 9,
    "previously_exposed_development_direct_pollen_only": True,
    "untouched_confirmation_field_accuracy_vegetation_truth_acquisition_rights_human_or_LRA_admission": False,
    "original_whole_failed_predecessors_relabelled": False,
}
CURRENT_SOURCE_SHA256: Any = (
    "de51c55046e74926692d402be58921b496ea52c191194fef6215b8df02b143d9"
)
PREPARED_PUBLICATIONS: Any = {
    "docs/report/regions/nordic/swedish-lake-transfer/input-manifest.json": {
        "member": "native-products/swedish-lake-transfer/prepared/input-manifest.json",
        "sha256": "8c266e2c44fabe0e7c3a31c38fc0058b27b3db08cff670b65ca239ea5eeb7905",
        "bytes": 3279,
        "role": "genuinely_produced_source_preparation",
    },
    "docs/report/regions/nordic/swedish-lake-transfer/inputs/metadata-SE.json.gz": {
        "member": "native-products/swedish-lake-transfer/prepared/inputs/metadata-SE.json.gz",
        "sha256": "83895824a229cad9d974ace2887275e37d174beda2057433fb5bb0c7f692d5b4",
        "bytes": 1016,
        "role": "genuinely_produced_source_preparation",
    },
    "docs/report/regions/nordic/swedish-lake-transfer/inputs/training-SE.json.gz": {
        "member": "native-products/swedish-lake-transfer/prepared/inputs/training-SE.json.gz",
        "sha256": "de2683e4a01ab4d3aa3e8add4891ddbb487f4cc0ee650aada57ed839abecce80",
        "bytes": 99397,
        "role": "genuinely_produced_source_preparation",
    },
    "docs/report/regions/nordic/swedish-lake-transfer/sealed-outcomes/outcomes-SE.json.gz": {
        "member": "native-products/swedish-lake-transfer/prepared/sealed-outcomes/outcomes-SE.json.gz",
        "sha256": "44c4ea3b2c607436b1c882d0881c2a1f8d0fe733a7a95c674b6481db9754473a",
        "bytes": 4718,
        "role": "genuinely_produced_source_preparation",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/input-manifest.json": {
        "member": "native-products/swedish-neotoma-holdout/prepared/input-manifest.json",
        "sha256": "752d43a47cbbc6cdde39b2625595c4bf939047649c09cae239449baf59b1994f",
        "bytes": 3135,
        "role": "genuinely_produced_source_preparation",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/inputs/metadata-SE.json.gz": {
        "member": "native-products/swedish-neotoma-holdout/prepared/inputs/metadata-SE.json.gz",
        "sha256": "061003889b07f4cad3db40484c217a2ef26a418ab92b80570f28e852d67b6913",
        "bytes": 454,
        "role": "genuinely_produced_source_preparation",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/inputs/training-SE.json.gz": {
        "member": "native-products/swedish-neotoma-holdout/prepared/inputs/training-SE.json.gz",
        "sha256": "de2683e4a01ab4d3aa3e8add4891ddbb487f4cc0ee650aada57ed839abecce80",
        "bytes": 99397,
        "role": "genuinely_produced_source_preparation",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/sealed-outcomes/outcomes-SE.json.gz": {
        "member": "native-products/swedish-neotoma-holdout/prepared/sealed-outcomes/outcomes-SE.json.gz",
        "sha256": "6fe46a235568eeba5a8d94849d2b82d3013e4d3d11cee27d02a4ceb731e1a1ab",
        "bytes": 1878,
        "role": "genuinely_produced_source_preparation",
    },
}
HISTORICAL_UNRESOLVED: Any = {
    "docs/report/regions/nordic/swedish-lake-transfer/manifest.json": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-lake-transfer/manifest.json",
        "sha256": "da15dcad06e44e97506157c2110d8af040241c059b8e40be2f484ac967ff54b7",
        "bytes": 2492,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
    "docs/report/regions/nordic/swedish-lake-transfer/prediction-freeze.json": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-lake-transfer/prediction-freeze.json",
        "sha256": "3aa60965e7d79b02674a0a61d8806e267bc04a7e2d37df711feb003ef289f18a",
        "bytes": 1193,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
    "docs/report/regions/nordic/swedish-lake-transfer/protocol.json": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-lake-transfer/protocol.json",
        "sha256": "046be3fa589fde3cba0d67f3d4a46f21f73a81a2dd2e089c454775affebabade",
        "bytes": 3662,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
    "docs/report/regions/nordic/swedish-lake-transfer/reference/prediction-producer.py.txt": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-lake-transfer/reference/prediction-producer.py.txt",
        "sha256": "3c4321f729c5ea4cc53172b3ebf0a22b782f0e873ae88ad67225b43a0ad01b62",
        "bytes": 13425,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/manifest.json": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-neotoma-holdout/manifest.json",
        "sha256": "8076afa47195b7fd613a9ddd3e332835fab05a4128dd645e176670d5dfd0a6a5",
        "bytes": 2822,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/prediction-freeze.json": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-neotoma-holdout/prediction-freeze.json",
        "sha256": "008c83b3b65065e808cd89a98c1b9903cc7b9e8815e698d67c5f2e176476add0",
        "bytes": 1001,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/protocol.json": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-neotoma-holdout/protocol.json",
        "sha256": "d33a453d047e19afd6206c69191ea5f5d4193f5b13d6fcb341d5a071b84e3053",
        "bytes": 2624,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/reference/parallel-dataset-review-producer.py.txt": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-neotoma-holdout/reference/parallel-dataset-review-producer.py.txt",
        "sha256": "3415a3cd6474aaf1fbdc7c260fcf03664b96ee3c1edc4b428dea0b9577d6adc7",
        "bytes": 4553,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
    "docs/report/regions/nordic/swedish-neotoma-holdout/reference/prediction-producer.py.txt": {
        "member": "original-source/source/docs/report/regions/nordic/swedish-neotoma-holdout/reference/prediction-producer.py.txt",
        "sha256": "25cdbebb05f9883fe7d980d21519af7b3ebf38f137f167f556607e6579ad67b7",
        "bytes": 13208,
        "role": "historical_authored_or_verification_or_freeze_reference_unresolved",
    },
}


def _require(value: object, reason: str) -> None:
    if not value:
        raise ReportRebuildError("Swedish direct-pollen source custody: " + reason)


def _exact(left: object, right: object) -> None:
    _require(type(left) is type(right), "metadata type differs")
    if isinstance(left, dict) and isinstance(right, dict):
        _require(left.keys() == right.keys(), "metadata fields differ")
        for key in left:
            _exact(left[key], right[key])
    elif isinstance(left, list) and isinstance(right, list):
        _require(len(left) == len(right), "metadata list membership differs")
        for a, b in zip(left, right, strict=True):
            _exact(a, b)
    else:
        _require(left == right, "metadata value differs")


def _object(value: object) -> dict[str, Any]:
    _require(
        isinstance(value, dict) and all(isinstance(k, str) for k in value),
        "JSON object required",
    )
    assert isinstance(value, dict)
    return value


def _file(root: Path, name: str) -> Path:
    try:
        return _regular_confined_file(
            root, name, "Swedish direct-pollen source custody"
        )
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "Swedish source missing, linked or unconfined"
        ) from error


def _json(path: Path) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in items:
            _require(key not in value, "duplicate JSON key")
            value[key] = item
        return value

    try:
        value = json.loads(path.read_bytes(), object_pairs_hook=pairs)
        json.dumps(value, allow_nan=False)
        return _object(value)
    except (OSError, ValueError) as error:
        raise ReportRebuildError("Swedish JSON is invalid") from error


def _same(left: object, right: object) -> bool:
    _exact(left, right)
    return True


def validate_owner_partition(owners: list[JsonObject]) -> None:
    """Only the four genuinely prepared files per family receive retained source admission."""
    for family in FAMILIES:
        prefix = "docs/report/regions/nordic/" + family + "/"
        generated = sorted(prefix + name for name in PREPARED_NAMES)
        historical = sorted(n for n in HISTORICAL_UNRESOLVED if n.startswith(prefix))
        selected = [
            r
            for r in owners
            if r.get("owner_id")
            == "regions/nordic/" + family + "/source-preparation-products"
        ]
        previous = [
            r
            for r in owners
            if r.get("owner_id") == "regions/nordic/" + family + "/report-products"
        ]
        _exact(len(selected), 1)
        _exact(len(previous), 1)
        for row, role, paths in [
            (selected[0], "retained_source", generated),
            (previous[0], "unresolved", historical),
        ]:
            for key, value in [
                ("role", role),
                ("paths", paths),
                ("producer_paths", []),
                ("producer_inputs", []),
            ]:
                _exact(row[key], value)
        for row in owners:
            other_paths = row.get("paths")
            _require(isinstance(other_paths, list), "Owner path list required")
            assert isinstance(other_paths, list)
            if row is not selected[0]:
                _require(
                    not set(generated).intersection(other_paths),
                    "Prepared owner overlap",
                )
            if row is not previous[0]:
                _require(
                    not set(historical).intersection(other_paths),
                    "Historical owner overlap",
                )


def validate_native_records(
    plan: dict[str, Any],
    common: dict[str, Any],
    inner: dict[str, Any],
    outer: dict[str, Any],
    reviews: list[dict[str, Any]],
    receipts: list[dict[str, Any]],
) -> None:
    """Keep native exits, declarations, historical limits and the actual training source literal."""
    for value in (
        plan["candidate"],
        common["candidate"],
        inner["candidate"],
        outer["source_candidate"],
    ):
        _exact(value, ORIGINAL_CANDIDATE)
    for value in (
        common["actual_exit"],
        inner["actual_exit"],
        outer["actual_exit"],
        outer["delegate_actual_exit"],
    ):
        _exact(value, 0)
    _exact(common["status"], "passed")
    _exact(common["before_pin_mismatches"], [])
    _exact(common["after_pin_mismatches"], [])
    _exact(common["absent_input_paths_unchanged"], True)
    _exact(outer["resource_bounds_met"], True)
    _exact(outer["timed_out"], False)
    _exact(inner["scientific_acceptance_claimed"], False)
    _exact(
        inner["historical_protocol_freeze_reference_or_verification_files_reproduced"],
        False,
    )
    _exact(
        plan["historical_protocol_freeze_reference_or_verification_files_reproduced"],
        False,
    )
    _exact(len(plan["input_pins"]), 66481)
    _exact(len({r["path"] for r in plan["input_pins"]}), 66481)
    _exact(len(plan["stages"]), 8)
    _exact(len(common["stages"]), 8)
    _exact(inner["native_stages"], common["stages"])
    for stage, declared in zip(common["stages"], plan["stages"], strict=True):
        for key in ("id", "argv", "timeout_seconds", "must_succeed"):
            _exact(stage[key], declared[key])
        _exact(stage["actual_exit"], 0)
        _exact(stage["timed_out"], False)
    _exact(len(reviews), 2)
    _exact(len(receipts), 6)
    for family, review, selected, sites, bins in zip(
        FAMILIES, reviews, [268, 77], [3, 1], [63, 22], strict=True
    ):
        for key, value in [
            ("schema_version", "swedish-direct-pollen-source-observation.v1"),
            ("candidate", ORIGINAL_CANDIDATE),
            ("family", family),
            ("actual_exit", 0),
            ("prepared_product_count", 4),
            ("prediction_product_count", 1),
            ("scoring_product_count", 5),
            ("previously_exposed_direct_pollen_development_only", True),
            (
                "historical_protocol_freeze_reference_or_verification_files_reproduced",
                False,
            ),
            (
                "LRA_or_field_accuracy_independent_confirmation_rights_or_human_acceptance",
                False,
            ),
        ]:
            _exact(review[key], value)
        for key, value in [
            ("selected_samples", selected),
            ("selected_sites", sites),
            ("target_bins", bins),
        ]:
            _exact(review["native_source_membership_and_mass"][key], value)
        _exact(len(review["native_source_membership_and_mass"]["axis"]), 31)
        _exact(len(review["this_study_complete_ten_product_comparisons"]), 10)
        for comparison in review["this_study_complete_ten_product_comparisons"]:
            _exact(comparison["checker_actual_exit"], 0)
            for key in ("sha256", "bytes"):
                _exact(comparison["generated"][key], comparison["retained"][key])
        study = plan["studies"][family]
        _exact(
            study["protocol"]["training"]["input_path"],
            "docs/report/regions/nordic/swedish-author-target-pollen/inputs/training-SE.json.gz",
        )
        _exact(
            study["protocol"]["training"]["input_sha256"],
            "de2683e4a01ab4d3aa3e8add4891ddbb487f4cc0ee650aada57ed839abecce80",
        )
    for receipt, family, stage in zip(
        receipts,
        [f for f in FAMILIES for _ in range(3)],
        ["prepare", "predict", "score"] * 2,
        strict=True,
    ):
        for key, value in [
            ("candidate", ORIGINAL_CANDIDATE),
            ("family", family),
            ("stage", stage),
            ("source_exit", 0),
            ("metadata_exit", 0),
            ("absent_cache_probes_are_actual_protected_reads", False),
        ]:
            _exact(receipt[key], value)
        _exact(receipt["counters"]["LRA_numerical_function_calls"], 0)
        _require(
            not set(receipt["attempted_absent_source_cache_paths"]).intersection(
                receipt["actual_read_paths"]
            ),
            "Absent cache probe is not a protected read",
        )
        if stage == "predict":
            _require(
                not any("/sealed-outcomes/" in p for p in receipt["actual_read_paths"]),
                "Prediction read sealed target observations",
            )


def validate_capsule_members(
    repository: Path, prefix: str, members: dict[str, Any]
) -> None:
    """Reject every alias, special or unlisted entry, including empty directories with unsafe aliases."""
    root = _file(repository, prefix + "/capture.json").parent
    actual = []
    for path in root.rglob("*"):
        _require(
            not path.is_symlink() and (path.is_file() or path.is_dir()),
            "Capsule alias/special entry",
        )
        if path.is_file():
            actual.append(path.relative_to(root).as_posix())
    _exact(sorted(actual), sorted([*members, "capture.json"]))
    for name, expected in members.items():
        _require(
            "__pycache__" not in Path(name).parts and Path(name).suffix != ".pyc",
            "Bytecode payload is identity-only",
        )
        path = _file(repository, prefix + "/" + name)
        _exact(
            {
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            },
            expected,
        )


def validated_swedish_direct_pollen_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit eight preparation products and leave all nine historical artifacts unresolved."""
    if (
        not any(
            r.get("owner_id")
            in [
                "regions/nordic/" + family + "/source-preparation-products"
                for family in FAMILIES
            ]
            for r in owners
        )
        and not (repository / CAPTURE).exists()
    ):
        return (), {}
    validate_owner_partition(owners)
    path = _file(repository, CAPTURE)
    _exact(
        {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        },
        {"sha256": CAPTURE_SHA256, "bytes": CAPTURE_BYTES},
    )
    packet = _json(path)
    members = _object(packet["members"])
    prefix = Path(CAPTURE).parent.as_posix()
    for key, value in [
        ("schema_version", "swedish-direct-pollen-source-capture.v1"),
        ("original_execution_candidate", ORIGINAL_CANDIDATE),
        ("original_input_count", 66481),
        ("original_actual_stage_exits", [0] * 8),
        ("original_common_inner_outer_exits", [0] * 3),
        ("member_count", MEMBER_COUNT),
        ("source_retention_role_counts", INPUT_SCOPE_COUNTS),
        ("prepared_publications", PREPARED_PUBLICATIONS),
        ("historical_unresolved_publications", HISTORICAL_UNRESOLVED),
        ("all_twenty_native_product_comparisons_preserved", True),
        ("scope", EXPECTED_SCOPE),
    ]:
        _exact(packet[key], value)
    _exact(len(members), MEMBER_COUNT)
    _exact(
        hashlib.sha256(
            json.dumps(members, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        MEMBERS_SHA256,
    )
    validate_capsule_members(repository, prefix, members)

    def record(name: str) -> dict[str, Any]:
        return _json(_file(repository, prefix + "/" + name))

    plan = record("execution/plan.json")
    common = record("execution/terminal.json")
    inner = record("execution/swedish-direct-pollen-terminal.json")
    outer = record("execution/runtime-custody-terminal.json")
    reviews = [record("execution/" + f + "/independent-review.json") for f in FAMILIES]
    receipts = [
        record("execution/native-receipts/" + f + "-" + s + ".json")
        for f in FAMILIES
        for s in ["prepare", "predict", "score"]
    ]
    validate_native_records(plan, common, inner, outer, reviews, receipts)
    plan_pin = members["execution/plan.json"]
    _exact(plan_pin, members["original-source/execution-plan.json"])
    for key in ("plan_sha256",):
        for value in (common[key], inner[key], outer[key]):
            _exact(value, plan_pin["sha256"])
    for stage in common["stages"]:
        for stream in ("stdout", "stderr"):
            _exact(
                members["execution/" + Path(stage[stream]).name]["sha256"],
                stage[stream + "_sha256"],
            )
    for review in reviews:
        _exact({k: review["plan"][k] for k in ("sha256", "bytes")}, plan_pin)
        for item in review["this_study_complete_ten_product_comparisons"]:
            name = (
                Path(item["generated"]["path"])
                .relative_to(Path(plan["output"]))
                .as_posix()
            )
            _exact(
                members["native-products/" + name],
                {k: item["generated"][k] for k in ("sha256", "bytes")},
            )
    for receipt in receipts:
        _exact({k: receipt["plan"][k] for k in ("sha256", "bytes")}, plan_pin)
        for item in receipt["produced_files"]:
            name = Path(item["path"]).relative_to(Path(plan["output"])).as_posix()
            _exact(
                members["native-products/" + name],
                {k: item[k] for k in ("sha256", "bytes")},
            )
    runtime_names = set()
    runtime = record("runtime-authority/plan.json")
    for label in ("plan", "outer", "common", "independent_review"):
        row = plan["qualified_source_runtime"][label]
        _exact(
            members["runtime-authority/" + label + ".json"],
            {k: row[k] for k in ("sha256", "bytes")},
        )
        runtime_names.add(row["path"])
    runtime_names.update(row["path"] for row in runtime["input_pins"])
    catalog = json.loads(
        _file(
            repository,
            prefix + "/original-source/ordered-original-input-identities.json",
        ).read_bytes()
    )
    _exact(len(catalog), 66481)
    counts: dict[str, int] = {}
    pinned = {r["path"]: r for r in plan["input_pins"]}
    for index, (row, original) in enumerate(
        zip(catalog, plan["input_pins"], strict=True)
    ):
        _exact({k: row[k] for k in ("path", "sha256", "bytes")}, original)
        _exact(row["original_index"], index)
        role = row["retention_role"]
        counts[role] = counts.get(role, 0) + 1
        member = row["retained_member"]
        p = Path(original["path"])
        if member is not None:
            _require(
                role
                in {
                    "retained_public_first_party_source_or_resource",
                    "retained_executed_controller_or_declared_metadata",
                    "retained_historical_publication_or_owner_metadata_input",
                },
                "Unknown copied role",
            )
            _exact(
                members["original-source/" + member],
                {k: original[k] for k in ("sha256", "bytes")},
            )
        elif role == "qualified_runtime_or_dependency_authority_identity_only":
            _require(
                original["path"] in runtime_names, "Undeclared omitted runtime input"
            )
        elif role == "bytecode_identity_only":
            _require(
                p.is_relative_to(Path(plan["repository"]) / "packages")
                and (p.suffix == ".pyc" or "__pycache__" in p.parts),
                "Omitted nonbytecode",
            )
        elif role == "private_source_identity_only":
            _require(
                p.is_relative_to(Path(plan["private_source_store"])),
                "Undeclared omitted private input",
            )
        elif role == "public_relational_input_identity_only":
            _require(
                p.is_relative_to(Path(plan["repository"]) / "data/neotoma/relational"),
                "Undeclared omitted relational input",
            )
        else:
            _require(False, "Unknown omitted original pin")
    _exact(counts, INPUT_SCOPE_COUNTS)
    projected = {}
    for receipt in receipts:
        for origin in receipt["first_party_origins"]:
            _exact(
                {k: origin[k] for k in ("path", "sha256", "bytes")},
                pinned[origin["path"]],
            )
        for name in receipt["actual_read_paths"]:
            p = Path(name)
            if (
                p.is_relative_to(Path(plan["repository"]) / "packages")
                and p.suffix != ".pyc"
                and "__pycache__" not in p.parts
            ):
                projected[p.relative_to(Path(plan["repository"])).as_posix()] = {
                    k: pinned[name][k] for k in ("sha256", "bytes")
                }
    _exact(len(projected), 65)
    _exact(projected, packet["current_observed_first_party_source_projection"])
    _exact(
        hashlib.sha256(
            json.dumps(projected, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        CURRENT_SOURCE_SHA256,
    )
    for name, expected in projected.items():
        current = _file(repository, name)
        _exact(
            {
                "sha256": hashlib.sha256(current.read_bytes()).hexdigest(),
                "bytes": current.stat().st_size,
            },
            expected,
        )
    entries = []
    for name, row in PREPARED_PUBLICATIONS.items():
        _exact(row["role"], "genuinely_produced_source_preparation")
        public = _file(repository, name)
        _exact(
            public.read_bytes(),
            _file(repository, prefix + "/" + row["member"]).read_bytes(),
        )
        entry = tracked_by_path.get(name)
        _require(entry is not None, "Tracked prepared product required")
        assert entry is not None
        for got, want in [
            (entry.path, name.removeprefix("docs/report/")),
            (entry.kind, "file"),
            (entry.sha256, row["sha256"]),
            (entry.size, row["bytes"]),
        ]:
            _exact(got, want)
        entries.append(entry)
    for name, row in HISTORICAL_UNRESOLVED.items():
        _exact(
            row["role"],
            "historical_authored_or_verification_or_freeze_reference_unresolved",
        )
        _exact(
            _file(repository, name).read_bytes(),
            _file(repository, prefix + "/" + row["member"]).read_bytes(),
        )
    return tuple(entries), {
        "capture_sha256": CAPTURE_SHA256,
        "original_execution_candidate": ORIGINAL_CANDIDATE,
        "actual_native_stage_exits": [0] * 8,
        "prepared_products_admitted": 8,
        "historical_unresolved_paths": sorted(HISTORICAL_UNRESOLVED),
        "twenty_native_byte_comparisons_preserved": True,
        "actual_training_source": plan["source_metadata_defect"],
        "observed_current_first_party_source_projection_count": 65,
        "whole_current_source_or_input_tree_equivalence": False,
        "generic_outer_EMPD2_scope_label_defect_preserved": True,
        "new_native_retention_or_untouched_confirmation_LRA_rights_human_acceptance_claimed": False,
    }
