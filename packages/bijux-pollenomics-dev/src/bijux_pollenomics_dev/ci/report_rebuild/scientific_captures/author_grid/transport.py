"""Authenticate the retained original-R/source-Python two-grid execution boundary."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any

JsonObject = dict[str, Any]
CAPTURE = "data/publication-replay/landclim-author-example-capture/capture.json"
CAPTURE_SHA256 = "9d6c4821ea1ba2a1216272d9691017e88ad96a66cf5820271b76442e617e3eec"
CAPTURE_BYTES = 7871526
MEMBER_COUNT = 4237
SOURCE_COUNT = 15759
ASSEMBLY_PLAN_SHA256 = (
    "e39d4cbe0c7067b27f0db894ba3e25be64ca925e4b40f6e9f0dd046cfe356d59"
)
ASSEMBLY_TERMINAL_SHA256 = (
    "8e6388063405beba2f9b2d04a4dfb73adad503914cf72eb24ee25483d67a8ec8"
)
ASSEMBLY_REVIEW_SHA256 = (
    "550701277e3e1b6a5146751cab32a731b98f31d54cd6666a762c83310f592919"
)
EPOCHS = {
    "numerical-execution": (
        "e282e08d796528488b438edd3ea661fb94b97b5d",
        "430e168b9a1a5d6c739b2be21f93bf9c9c7b8899fce10ddc55d8db1a4ae5d408",
        "1842fe6e1d68f36d427aaa3ec8742b038407968cb188bfc8eff6daf32ad0bb8d",
        "author-grid-terminal.json",
        "706d3009a9831521f97e049faef4cb6626188cb25e7b28f037be70c1327cd72b",
        [0, 0, 1],
        54092,
    ),
    "numerical-source-review": (
        "2784d4eae839e4a4e43f80ec77fd26bd0172aff0",
        "a17d914be6bbc138b0b5e95b9328375ba4776f1e5eaebd5bd04f81184d16ad40",
        "4378d571805bc3e0abf0a076a5a3dede625a85faf63d9b3ad344c77be8c29a4d",
        "author-grid-review-terminal.json",
        "42e4a37997ff8f5d24fe9352cf9afd9282d65dda30f85cc818c22f231caa593c",
        [0],
        54542,
    ),
    "correspondence-writer": (
        "e1ca9def55e7cd3e68ac6f20270059e743373251",
        "c4a5e9d93a3ef87df11489be2c52d2b5ccda41a2c2c369c6cd1fd44432578a8b",
        "3da64778a02ae8bd18c5c6826fd17c6e25434137a684eeec2401b511bad1b932",
        "correspondence-terminal.json",
        "fbd5922e4d91204aaebd61a01d73469dd912db8e2cfd5d23cf2df29ed51d477e",
        [0, 1],
        54759,
    ),
    "saved-ledger-review": (
        "aed78f8befdf0449789249e780ad80f13f44e086",
        "f831349bc34f0519e2d28c9b80dd01d5f933a3cdc7e9583f3be47ab20e0f4e08",
        "87e1dd4c763306afbbb74132da3b47123f1e9fc794fe25ab2263e5617def02c0",
        "ledger-observer-terminal.json",
        "71d5f761f80e074d30fb1b13c4c0d53a3d34c86f9d5fa3dfa9e045bfb1ffbf45",
        [0],
        57025,
    ),
}


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def object_value(value: object) -> JsonObject:
    require(
        isinstance(value, dict) and all(isinstance(k, str) for k in value),
        "Author-grid object required",
    )
    assert isinstance(value, dict)
    return value


def member(value: object) -> str:
    require(isinstance(value, str) and bool(value), "Author-grid member path required")
    assert isinstance(value, str)
    path = PurePosixPath(value)
    require(
        not path.is_absolute()
        and ".." not in path.parts
        and path.as_posix() == value
        and "\\" not in value
        and value != ".",
        "Author-grid member unconfined",
    )
    return value


def file(root: Path, name: str) -> Path:
    path = root / member(name)
    require(
        root.resolve() == root
        and path.is_file()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Author-grid physical file required",
    )
    return path


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_object(path: Path) -> JsonObject:
    def pairs(rows: list[tuple[str, Any]]) -> JsonObject:
        result: JsonObject = {}
        for key, value in rows:
            require(key not in result, "Author-grid duplicate JSON key")
            result[key] = value
        return result

    result = json.loads(
        path.read_bytes(),
        object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError("Nonfinite author-grid JSON")
        ),
    )
    return object_value(result)


def typed(value: object, wanted: object) -> None:
    require(
        type(value) is type(wanted) and value == wanted,
        "Author-grid typed value differs",
    )


def native_history(
    plan: JsonObject, terminal: JsonObject, outer: JsonObject, lane: str
) -> None:
    candidate, plan_sha, _, _, _, exits, pins = EPOCHS[lane]
    require(
        plan["candidate"] == terminal["candidate"] == outer["candidate"] == candidate,
        "Author-grid native epoch differs",
    )
    require(
        terminal["plan_sha256"] == outer["plan_sha256"] == plan_sha,
        "Author-grid native plan binding differs",
    )
    whole = max(exits)
    for value in [
        terminal["actual_exit"],
        outer["actual_exit"],
        outer["common_actual_exit"],
    ]:
        typed(value, whole)
    require(
        terminal["canonical_before"]
        == terminal["canonical_after"]
        == plan["canonical_identity"]
        and plan["canonical_identity"]["status"] == "",
        "Author-grid original source changed",
    )
    require(
        terminal["before_pin_mismatches"] == terminal["after_pin_mismatches"] == []
        and terminal["absent_input_paths_unchanged"] is True,
        "Author-grid original input custody differs",
    )
    require(
        outer["memory_bound_pass"] is True and outer["storage_bound_pass"] is True,
        "Author-grid original resource refusal",
    )
    require(
        len(plan["stages"]) == len(terminal["stages"]) == len(exits),
        "Author-grid native stage membership differs",
    )
    for intended, actual, exit_code in zip(
        plan["stages"], terminal["stages"], exits, strict=True
    ):
        require(
            actual["id"] == intended["id"]
            and actual["argv"] == intended["argv"]
            and actual["timed_out"] is False,
            "Author-grid native command differs",
        )
        typed(actual["actual_exit"], exit_code)
    require(
        len(plan["input_pins"]) == len({r["path"] for r in plan["input_pins"]}) == pins,
        "Author-grid original pin membership differs",
    )


def validate_retained_ledger(path: Path) -> None:
    """Check exact supported rows under the original prospective cell tolerances."""
    from bijux_pollenomics_dev.essd_reproduction.example_reexecution import TOLERANCES

    expected = [
        "source",
        "grid_id",
        "scope",
        "site_id",
        "bin_id_bp",
        "taxon",
        "metric",
        "unit",
        "author_reference",
        "installed_lra",
        "signed_residual",
        "within_declared_tolerance",
    ]
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == expected, "Author-grid ledger header differs")
        keys = set()
        for row in reader:
            require(
                None not in row and all(value is not None for value in row.values()),
                "Author-grid ledger cell missing",
            )
            key = tuple(
                row[name]
                for name in [
                    "grid_id",
                    "scope",
                    "site_id",
                    "bin_id_bp",
                    "taxon",
                    "metric",
                ]
            )
            require(
                key not in keys
                and row["grid_id"] in {"512", "562"}
                and row["scope"] in {"site", "regional"}
                and bool(row["site_id"]) == (row["scope"] == "site"),
                "Author-grid ledger source key differs",
            )
            require(
                row["metric"] in {"mean", "standard_error"}
                and row["unit"] == "fraction"
                and row["source"] == "ESSD_LandClim_author_R_example",
                "Author-grid ledger metric/source scope differs",
            )
            keys.add(key)
            reference, python, residual = [
                float(row[name])
                for name in ["author_reference", "installed_lra", "signed_residual"]
            ]
            require(
                all(math.isfinite(v) for v in [reference, python, residual])
                and residual == python - reference,
                "Author-grid ledger raw arithmetic differs",
            )
            tolerance = TOLERANCES["cover" if row["metric"] == "mean" else "se"]
            require(
                row["within_declared_tolerance"] == "True"
                and abs(residual)
                <= tolerance["atol"] + tolerance["rtol"] * abs(reference),
                "Author-grid original prospective numerical tolerance failed",
            )
        require(len(keys) == 14074, "Author-grid supported cell denominator differs")


def validated_retained_author_grid(
    repository: Path,
) -> tuple[JsonObject, dict[str, JsonObject]]:
    capture_path = file(repository, CAPTURE)
    require(
        capture_path.stat().st_size == CAPTURE_BYTES
        and sha(capture_path) == CAPTURE_SHA256,
        "Author-grid sealed capture identity differs",
    )
    capture = json_object(capture_path)
    root = capture_path.parent
    require(
        capture["schema_version"] == "retained-author-grid-source-capture.v1"
        and capture["private_source_redistributed"] is False
        and capture["historical_9dd1_raw_receipt_available"] is False,
        "Author-grid capture scope differs",
    )
    rows = capture["members"]
    require(
        isinstance(rows, list) and len(rows) == MEMBER_COUNT,
        "Author-grid member denominator differs",
    )
    members = {}
    for raw in rows:
        row = object_value(raw)
        name = member(row.get("path"))
        require(
            set(row) == {"path", "sha256", "bytes"}
            and type(row["bytes"]) is int
            and row["bytes"] >= 0
            and name not in members,
            "Author-grid member record differs",
        )
        path = file(root, name)
        require(
            path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
            "Author-grid retained member bytes differ",
        )
        members[name] = row
    physical = set()
    for path in root.rglob("*"):
        require(not path.is_symlink(), "Author-grid packet contains link")
        if path.is_file():
            physical.add(path.relative_to(root).as_posix())
    require(
        physical == set(members) | {"capture.json"},
        "Author-grid physical packet membership differs",
    )
    sources = capture["retained_first_party_source_inputs"]
    require(
        isinstance(sources, list) and len(sources) == SOURCE_COUNT,
        "Author-grid original source denominator differs",
    )
    by_lane: dict[str, dict[str, JsonObject]] = {lane: {} for lane in EPOCHS}
    for raw in sources:
        row = object_value(raw)
        lane = row["execution_lane"]
        require(
            lane in by_lane and row["path"] not in by_lane[lane],
            "Author-grid source attribution duplicates",
        )
        by_lane[lane][row["path"]] = row
        retained = members.get(member(row["captured_path"]))
        require(
            retained is not None
            and (retained["sha256"], retained["bytes"])
            == (row["sha256"], row["bytes"]),
            "Author-grid original source bytes unbound",
        )
    histories = object_value(capture["original_execution_custody"])
    require(set(histories) == set(EPOCHS), "Author-grid execution membership differs")
    for lane, spec in EPOCHS.items():
        prefix = "executions/" + lane + "/"
        for name, digest in [
            ("plan.json", spec[1]),
            ("terminal.json", spec[2]),
            (spec[3], spec[4]),
        ]:
            require(
                members[prefix + name]["sha256"] == digest,
                "Author-grid original receipt identity differs",
            )
        plan = json_object(file(root, prefix + "plan.json"))
        terminal = json_object(file(root, prefix + "terminal.json"))
        outer = json_object(file(root, prefix + spec[3]))
        native_history(plan, terminal, outer, lane)
        require(
            outer["common_terminal"]["sha256"] == spec[2],
            "Author-grid resource terminal differs",
        )
        history = object_value(histories[lane])
        require(
            history["candidate"] == spec[0]
            and history["original_plan_sha256"] == spec[1]
            and history["original_terminal_sha256"] == spec[2]
            and history["original_outer_sha256"] == spec[4],
            "Author-grid history bindings differ",
        )
        typed(history["original_input_count"], spec[6])
        typed(history["original_whole_actual_exit"], max(spec[5]))
        require(
            history["original_stage_exits"] == spec[5],
            "Author-grid historical refusal changed",
        )
        expected = {}
        old_root = PurePosixPath(plan["repository"])
        originals = {row["path"]: row for row in plan["input_pins"]}
        for original in originals.values():
            original_path = PurePosixPath(original["path"])
            if original_path.is_relative_to(old_root) and original_path.relative_to(
                old_root
            ).parts[0] in {"packages", "configs", "makes", "apis"}:
                expected[original["path"]] = original
        require(
            set(expected) == set(by_lane[lane]),
            "Author-grid complete first-party source set differs",
        )
        for name, row in by_lane[lane].items():
            require(
                (row["sha256"], row["bytes"])
                == (expected[name]["sha256"], expected[name]["bytes"]),
                "Author-grid original source declaration differs",
            )
        for recovery in history["git_recoveries"]:
            old = object_value(recovery["original"])
            require(
                old == originals[old["path"]]
                and recovery["original_candidate"] == spec[0]
                and recovery["current_candidate"] == capture["assembly_candidate"],
                "Author-grid source recovery epoch differs",
            )
            retained = members[member(recovery["retained_original"])]
            require(
                (retained["sha256"], retained["bytes"])
                == (old["sha256"], old["bytes"]),
                "Author-grid recovered original source differs",
            )
    return capture, members
