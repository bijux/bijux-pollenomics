"""Exercise pure source, count, leakage and actual-score boundaries without data replay."""

from __future__ import annotations

import ast
from copy import deepcopy
import csv
import gzip
import importlib.machinery
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve() or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical controller entrypoint before helper imports")
_entry_directory = _entry_path.parent
_expected_python = {
    "contracts.py",
    "independent.py",
    "execute_source.py",
    "observe.py",
    "prepare.py",
    "run.py",
    "check_contracts.py",
    "source_runtime.py",
    "runtime_contracts.py",
    "runtime_guarded_runner.py",
    "common_runner.py",
}
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _expected_python:
        raise ValueError("Unexpected controller import")
sys.path.insert(0, str(_entry_directory))

from contracts import SOURCE, exact, pin, require, union, verify_inputs  # noqa: E402
from execute_source import absent_source_cache, allowed_open, engine_watch  # noqa: E402
from independent import (  # noqa: E402
    METHODS,
    allocate,
    direct_count,
    selected_claims,
    source_coordinate,
    taxonomy,
    verify_scores,
)
from observe import validate_stage  # noqa: E402
from run import accounted_receipt  # noqa: E402


def refused(function: Any, *args: Any) -> None:
    try:
        function(*args)
    except (ValueError, KeyError, TypeError):
        return
    raise AssertionError("Unsafe synthetic input accepted")


def write_json(path: Path, value: Any, *, compressed: bool = False) -> None:
    raw = json.dumps(value).encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(raw, mtime=0) if compressed else raw)


def score_fixture(root: Path) -> tuple[Path, Path, Path]:
    prepared, predicted, scored = (
        root / n for n in ("prepared", "predicted", "scored")
    )
    axis = ["A", "B"]
    write_json(prepared / "input-manifest.json", {"axis": axis})
    write_json(
        prepared / "inputs/metadata-SE.json.gz",
        {
            "sites": [
                {
                    "site_id": "target",
                    "candidate_bin_ids": ["0"],
                    "candidate_sample_ids": ["sample1"],
                }
            ]
        },
        compressed=True,
    )
    training = {
        name: {"group_id": name, "site_id": name, "bins": {"0": {"closed_nisp": 2}}}
        for name in ("train1", "train2")
    }
    write_json(prepared / "inputs/training-SE.json.gz", training, compressed=True)
    write_json(
        prepared / "sealed-outcomes/outcomes-SE.json.gz",
        {
            "SE:target": {
                "0": {
                    "counts": {"A": 1, "B": 1},
                    "closed_nisp": 2,
                    "all_pollen_nisp": 3,
                    "author_excluded_nisp": 0,
                    "unmapped_nisp": 1,
                    "sample_count": 1,
                }
            }
        },
        compressed=True,
    )
    rows = [
        {
            "country": "SE",
            "site_id": "target",
            "bin_id": 0,
            "method": method,
            "fractions": {"A": 0.25, "B": 0.75},
            "training_site_ids": ["train1", "train2"],
            "target_pollen_counts_read": False,
        }
        for method in METHODS
    ]
    write_json(
        predicted / "predictions-SE.json.gz",
        {"axis": axis, "country": "SE", "predictions": rows, "refusals": []},
        compressed=True,
    )
    hellinger = math.sqrt(
        0.5 * sum((math.sqrt(x) - math.sqrt(0.5)) ** 2 for x in (0.25, 0.75))
    )
    scores = [
        {
            "country": "SE",
            "site_id": "target",
            "bin_id": 0,
            "method": row["method"],
            "status": "scored",
            "mae_fraction": 0.25,
            "hellinger_distance": hellinger,
            "target_sample_count": 1,
            "target_assigned_nisp": 2,
            "target_native_nisp": 3,
            "prediction_sha256": pin(predicted / "predictions-SE.json.gz")["sha256"],
        }
        for row in rows
    ]
    scored.mkdir()
    text = io.StringIO(newline="")
    writer = csv.DictWriter(text, fieldnames=list(scores[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(scores)
    (scored / "scores.csv").write_text(text.getvalue())
    write_json(
        scored / "report.json",
        {
            "axis": axis,
            "methods": list(METHODS),
            "score_rows": 3,
            "site_macro_mae_fraction": {"SE": dict.fromkeys(METHODS, 0.25)},
            "site_macro_hellinger_distance": {"SE": dict.fromkeys(METHODS, hellinger)},
            "country_source_denominators": {
                "SE": {
                    "sites": 1,
                    "selected_samples": 1,
                    "native_nisp": 3,
                    "assigned_nisp": 2,
                    "author_excluded_nisp": 0,
                    "unmapped_nisp": 1,
                }
            },
        },
    )
    return prepared, predicted, scored


def mutate_prediction(path: Path, operation: Any) -> None:
    value = json.loads(gzip.decompress(path.read_bytes()))
    operation(value)
    write_json(path, value, compressed=True)


def launcher_prefix(raw: bytes, directory: Path) -> None:
    """Execute the real import guard up to, but never including, helper imports."""
    tree = ast.parse(raw)
    boundary = next(
        index
        for index, node in enumerate(tree.body)
        if isinstance(node, ast.ImportFrom) and node.module == "source_runtime"
    )
    prefix = ast.Module(body=tree.body[:boundary], type_ignores=[])
    saved = list(sys.path)
    try:
        exec(
            compile(prefix, str(directory / "runtime_guarded_runner.py"), "exec"),
            {
                "__file__": str(directory / "runtime_guarded_runner.py"),
                "__name__": "source_import_boundary_control",
            },
        )
    finally:
        sys.path[:] = saved


def check_launcher_namespace() -> list[str]:
    expected = {path.name for path in SOURCE.glob("*.py")}
    require(len(expected) == 11, "Exactly eleven held Python controllers")
    checked = []
    for filename in (
        "prepare.py",
        "execute_source.py",
        "observe.py",
        "run.py",
        "check_contracts.py",
        "runtime_guarded_runner.py",
        "contracts.py",
    ):
        tree = ast.parse((SOURCE / filename).read_bytes())
        bindings = [
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id in {"_expected_python", "MODULES"}
                for t in node.targets
            )
        ]
        require(
            len(bindings) == 1 and ast.literal_eval(bindings[0].value) == expected,
            "Complete actual module allowlist differs: " + filename,
        )
        checked.append(filename)
    raw = (SOURCE / "runtime_guarded_runner.py").read_bytes()
    original = (
        SOURCE.parent / "swedish-direct-pollen-source-custody/runtime_guarded_runner.py"
    ).read_bytes()
    require(
        original.replace(b'"metadata.py"', b'"independent.py"') == raw,
        "Only exact runtime launcher import-set correction allowed",
    )
    with tempfile.TemporaryDirectory(
        dir=SOURCE / "preflight", prefix="launcher-boundary-"
    ) as folder:
        root = Path(folder)

        def complete(name: str) -> Path:
            directory = root / name
            directory.mkdir()
            for item in expected:
                shutil.copyfile(SOURCE / item, directory / item)
            return directory

        positive = complete("complete-controller-copy")
        launcher_prefix(raw, positive)
        refused(launcher_prefix, original, positive)
        for suffix in (".py", ".pyc", ".so"):
            directory = complete("unexpected" + suffix)
            (directory / ("unexpected" + suffix)).write_text("not admitted")
            refused(launcher_prefix, raw, directory)
        directory = complete("unexpected-obsolete-helper")
        (directory / "metadata.py").write_text("obsolete helper is not a dependency")
        refused(launcher_prefix, raw, directory)
        directory = complete("unexpected-special")
        os.mkfifo(directory / "unexpected-fifo")
        refused(launcher_prefix, raw, directory)
        directory = complete("unexpected-alias")
        (directory / "alias.json").symlink_to(directory / "contracts.py")
        refused(launcher_prefix, raw, directory)
        directory = complete("unexpected-directory")
        (directory / "unexpected-import-directory").mkdir()
        refused(launcher_prefix, raw, directory)
    return checked


def check_absent_import_cache() -> None:
    """Exercise Python's actual cache miss and source fallback on harmless owned code."""
    with tempfile.TemporaryDirectory(
        dir=SOURCE / "preflight", prefix="source-cache-"
    ) as directory:
        root = Path(directory)
        source = root / "harmless_import.py"
        source.write_text("VALUE = 7\n")
        cache = Path(importlib.util.cache_from_source(str(source), optimization=""))
        binding = {
            "source_path": str(source),
            "cache_tag": sys.implementation.cache_tag,
        }
        plan = {
            "output": str(root / "outputs"),
            "input_pins": [pin(source)],
            "first_party_namespaces": [],
            "cache_source_namespaces": [
                {"root": str(root), "entries": {source.name: {"kind": "file"}}}
            ],
            "absent_input_paths": [str(cache)],
            "absent_source_cache_candidates": {str(cache): binding},
        }
        pins = {str(source)}
        require(
            absent_source_cache(cache, "r", 0, plan, pins),
            "Exact declared absent cache positive",
        )
        require(
            sys.dont_write_bytecode,
            "Actual source-control interpreter must not write bytecode",
        )
        active = True
        misses: set[str] = set()
        reads: set[str] = set()

        def audit(event: str, values: tuple[Any, ...]) -> None:
            if active and event == "open" and isinstance(values[0], (str, bytes)):
                raw = os.fsdecode(values[0])
                if raw.startswith(str(root) + "/"):
                    path = Path(raw)
                    missed = allowed_open(
                        path,
                        values[1] or "",
                        values[2],
                        plan,
                        "swedish-lake-transfer",
                        "prepare",
                        pins,
                    )
                    (misses if missed else reads).add(str(path))

        sys.addaudithook(audit)
        try:
            spec = importlib.util.spec_from_file_location(
                "harmless_source_cache_control", source
            )
            assert spec is not None and isinstance(
                spec.loader, importlib.machinery.SourceFileLoader
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            require(
                module.VALUE == 7,
                "Actual SourceFileLoader fallback did not execute source",
            )
        finally:
            active = False
        require(
            misses == {str(cache)}
            and reads == {str(source)}
            and not cache.exists()
            and not cache.parent.exists(),
            "Absent probe and actual source read must remain separate without cache writes",
        )
        verify_inputs(plan)
        require(
            not allowed_open(
                source, "r", 0, plan, "swedish-lake-transfer", "prepare", pins
            ),
            "Ordinary protected source read is not a missing cache",
        )
        refused(absent_source_cache, cache, "r", 0, plan, set())
        refused(absent_source_cache, cache, "wb", os.O_CREAT | os.O_WRONLY, plan, pins)
        refused(
            absent_source_cache,
            cache,
            "r",
            0,
            {**plan, "cache_source_namespaces": []},
            pins,
        )
        refused(
            absent_source_cache, cache, "r", 0, {**plan, "absent_input_paths": []}, pins
        )
        refused(
            absent_source_cache,
            cache,
            "r",
            0,
            {
                **plan,
                "absent_source_cache_candidates": {
                    str(cache): {**binding, "source_path": str(root / "other.py")}
                },
            },
            pins,
        )
        wrong = Path(
            str(cache).replace(str(sys.implementation.cache_tag), "unqualified-tag")
        )
        refused(
            absent_source_cache,
            wrong,
            "r",
            0,
            {
                **plan,
                "absent_input_paths": [str(wrong)],
                "absent_source_cache_candidates": {str(wrong): binding},
            },
            pins,
        )
        cache.parent.mkdir()
        cache.write_bytes(b"unqualified cache bytes")
        refused(absent_source_cache, cache, "r", 0, plan, pins)
        refused(
            allowed_open, cache, "r", 0, plan, "swedish-lake-transfer", "prepare", pins
        )
        refused(verify_inputs, plan)
        cache.unlink()
        cache.parent.rmdir()
        alias_target = root / "other-cache"
        alias_target.mkdir()
        cache.parent.symlink_to(alias_target, target_is_directory=True)
        refused(absent_source_cache, cache, "r", 0, plan, pins)
        cache.parent.unlink()


def main() -> None:
    checks = []
    raw = b"oldvar,RPP.LANDCLIMII\nx,A\ny,zz.do not use\nz,aage.cal.BP\n"
    require(
        taxonomy(raw) == ({"x": "A", "y": "zz.do not use", "z": "aage.cal.BP"}, ["A"]),
        "Lookup positive",
    )
    checks.append("literal taxonomy target/excluded axis")
    refused(taxonomy, raw + b"x,B\n")
    checks.append("ambiguous native lookup refusal")
    require(
        allocate(
            {"x": 4, "y": 2, "missing": 3}, {"x": "A", "y": "zz.do not use"}, ["A"]
        )
        == {
            "counts": {"A": 4},
            "closed_nisp": 4,
            "all_pollen_nisp": 9,
            "author_excluded_nisp": 2,
            "unmapped_nisp": 3,
        },
        "Mass closure positive",
    )
    for bad in (-1, True, 0.5):
        refused(allocate, {"x": bad}, {"x": "A"}, ["A"])
    checks.append("integer native mass and explicit excluded/unmapped accounting")
    direct = {
        "source_element": "pollen",
        "source_element_type": "pollen",
        "source_unit": "NISP",
        "unit_family": "count",
        "detection_status": "reported_value",
        "source_value": 0,
        "source_reported_name": "x",
    }
    require(direct_count(direct), "Reported zero must remain count")
    for field, value in [
        ("source_value", True),
        ("source_value", -1),
        ("source_unit", "percent"),
        ("detection_status", "missing"),
        ("source_reported_name", ""),
    ]:
        require(
            not direct_count({**direct, field: value}), "Malformed/noncount admitted"
        )
    checks.append("reported zero versus bool/missing/noncount")
    age = {
        "subject_type": "sample",
        "country_code": "SE",
        "source_age_type": "Calibrated radiocarbon years BP",
        "is_default_chronology": True,
        "comparability_status": "comparable",
        "calibration_status": "calibrated",
        "source_age_value": 0,
        "subject_id": "sample",
    }
    require(set(selected_claims([age])) == {"sample"}, "Zero BP central claim")
    refused(selected_claims, [age, deepcopy(age)])
    for value in (True, -1, float("nan")):
        refused(selected_claims, [{**age, "source_age_value": value}])
    require(
        selected_claims([{**age, "is_default_chronology": False}]) == {},
        "Nondefault age admitted",
    )
    checks.append("source age uniqueness/type/default/calibration boundaries")
    require(
        source_coordinate({"type": "Point", "coordinates": [12, 55]})
        == {"latitude": 55.0, "longitude": 12.0},
        "Point orientation",
    )
    require(
        source_coordinate(
            {
                "type": "Polygon",
                "coordinates": [[[0, 0], [2, 0], [2, 2], [0, 2], [0, 0]]],
            }
        )
        == {"latitude": 1.0, "longitude": 1.0},
        "Source polygon centroid",
    )
    refused(source_coordinate, {"type": "Point", "coordinates": [181, 55]})
    refused(source_coordinate, {"type": "LineString", "coordinates": [[0, 0], [1, 1]]})
    checks.append("declared source geometry orientation and invalid shape refusal")
    with tempfile.TemporaryDirectory(
        dir=SOURCE / "preflight", prefix="guard-"
    ) as directory:
        root = Path(directory)
        prepared, predicted, scored = score_fixture(root / "positive")
        require(
            verify_scores(prepared, predicted, scored)["score_rows"] == 3,
            "Whole synthetic score positive",
        )
        checks.append("full synthetic score/count/site macro positive")
        operations = [
            lambda x: x["predictions"].append(deepcopy(x["predictions"][0])),
            lambda x: x["predictions"][0].update(target_pollen_counts_read=True),
            lambda x: x["predictions"][0].update(
                training_site_ids=["target", "train1"]
            ),
            lambda x: x["predictions"][0]["fractions"].update(A=0.5),
            lambda x: x["predictions"].pop(),
            lambda x: x.update(axis=["A", "C"]),
            lambda x: x["refusals"].append({"site_id": "target", "bin_id": 0}),
        ]
        for index, operation in enumerate(operations):
            parts = score_fixture(root / ("bad-score-" + str(index)))
            mutate_prediction(parts[1] / "predictions-SE.json.gz", operation)
            refused(verify_scores, *parts)
        checks.append(
            "duplicate/leakage/training/axis/count/method/refusal score negatives"
        )
        bad_mass = score_fixture(root / "bad-mass")
        target = bad_mass[0] / "sealed-outcomes/outcomes-SE.json.gz"
        value = json.loads(gzip.decompress(target.read_bytes()))
        value["SE:target"]["0"]["sample_count"] = 2
        write_json(target, value, compressed=True)
        refused(verify_scores, *bad_mass)
        checks.append("self-consistent serialized source-count mismatch refusal")
        fake = {"output": str(root)}
        target = root / "cohort/prepared/sealed-outcomes/outcomes-SE.json.gz"
        allowed_open(target, "w", 0, fake, "swedish-lake-transfer", "prepare", set())
        refused(
            allowed_open,
            target,
            "r",
            0,
            fake,
            "swedish-lake-transfer",
            "predict",
            set(),
        )
        refused(
            allowed_open,
            root.parent / "outside",
            "w",
            0,
            fake,
            "swedish-lake-transfer",
            "prepare",
            set(),
        )
        link = root / "alias"
        link.symlink_to(prepared / "input-manifest.json")
        refused(
            allowed_open,
            link,
            "r",
            0,
            fake,
            "swedish-lake-transfer",
            "prepare",
            {str(link)},
        )
        checks.append("sealed target/output containment/alias refusal")
        expected_alias = {
            "path": str(link),
            "raw_link": os.readlink(link),
            "resolved_target": str(link.resolve()),
        }
        permitted_alias_plan = {**fake, "runtime_aliases": [expected_alias]}
        allowed_open(
            link,
            "r",
            0,
            permitted_alias_plan,
            "swedish-lake-transfer",
            "prepare",
            {str(link), str(link.resolve())},
        )
        refused(
            allowed_open,
            link,
            "w",
            0,
            permitted_alias_plan,
            "swedish-lake-transfer",
            "prepare",
            {str(link), str(link.resolve())},
        )
        refused(
            allowed_open,
            link,
            "r",
            0,
            {**fake, "runtime_aliases": [{**expected_alias, "raw_link": "different"}]},
            "swedish-lake-transfer",
            "prepare",
            {str(link), str(link.resolve())},
        )
        checks.append(
            "qualified runtime raw-link positive and changed-link/write refusals"
        )
        frozen = root / "expected-source.txt"
        frozen.write_text("held source")
        fixed = pin(frozen)
        fake_plan = {
            "input_pins": [fixed],
            "first_party_namespaces": [],
            "absent_input_paths": [],
        }
        verify_inputs(fake_plan)
        frozen.write_text("changed during census")
        refused(verify_inputs, fake_plan)
        checks.append(
            "original expected source mutation during census refuses before writing plan"
        )
        stdout, stderr = root / "native.stdout", root / "native.stderr"
        stdout.write_text("source result\n")
        stderr.write_text("")
        stage = {
            "id": "actual",
            "argv": ["qualified", "-I"],
            "actual_exit": 0,
            "timed_out": False,
            "stdout": str(stdout),
            "stderr": str(stderr),
            "stdout_sha256": pin(stdout)["sha256"],
            "stderr_sha256": pin(stderr)["sha256"],
        }
        validate_stage(stage, stage)
        for field, changed in [
            ("actual_exit", 1),
            ("actual_exit", False),
            ("timed_out", True),
            ("argv", ["wrong"]),
        ]:
            refused(validate_stage, {**stage, field: changed}, stage)
        stdout.write_text("tampered result\n")
        refused(validate_stage, stage, stage)
        checks.append("actual stage/log/argv/native-zero type and timeout custody")
        special_root = root / "special-output"
        special_root.mkdir()
        (special_root / "regular").write_text("a")
        receipt = accounted_receipt(special_root, {"actual_exit": 0}, 4096)
        require(
            json.loads(receipt)["completed_output_bytes_including_receipt"]
            == 1 + len(receipt),
            "Receipt-inclusive storage positive",
        )
        os.mkfifo(special_root / "unexpected-fifo")
        refused(accounted_receipt, special_root, {"actual_exit": 0}, 4096)
        checks.append("inclusive output bytes and FIFO refusal")
    row = {"path": "/ordinary/source", "sha256": "a" * 64, "bytes": 1}
    require(union([row], [deepcopy(row)]) == [row], "Equal expected union")
    refused(union, [row], [{**row, "sha256": "b" * 64}])
    require(not exact({"count": 1}, {"count": True}), "Typed expected count")
    checks.append("frozen expected-pin conflicts and bool count refusal")

    class Code:
        co_filename = "/unrelated/source.py"

        @property
        def co_name(self) -> str:
            raise AssertionError("Unrelated call name inspected")

    class Frame:
        f_code = Code()

    counter = {"LRA_numerical_function_calls": 0}
    watch = engine_watch(("/owned/lra/reconstruction/",), counter)
    for _ in range(1_000_000):
        watch(Frame(), "call", None)
    require(
        counter["LRA_numerical_function_calls"] == 0, "Unrelated numerical callback"
    )
    checks.append("million unrelated profile calls avoid name/Path processing")
    native = type(
        "Frame",
        (),
        {
            "f_code": type(
                "Code",
                (),
                {
                    "co_filename": "/owned/lra/reconstruction/analytical.py",
                    "co_name": "run",
                },
            )()
        },
    )()
    refused(watch, native, "call", None)
    require(
        counter["LRA_numerical_function_calls"] == 1, "Numerical denial not observed"
    )
    checks.append("actual attempted numerical call counter and refusal")
    declared = json.loads((SOURCE / "declared-inputs.json").read_text())
    for study in declared["studies"].values():
        require(
            study["protocol"]["training"]["input_path"]
            not in study["original_owner_row"]["producer_inputs"]
            and study["wrong_owner_training_path"]
            in study["original_owner_row"]["producer_inputs"],
            "Training declaration defect lost",
        )
        require(
            study["actual_protocol_training"]["path"].endswith(
                study["protocol"]["training"]["input_path"]
            )
            and study["actual_protocol_training"]["sha256"]
            == study["protocol"]["training"]["input_sha256"],
            "Actual declared protocol-training binding",
        )
    checks.append(
        "actual two protocol/owner training mismatch and truthful selected-input binding"
    )
    require(
        len(check_launcher_namespace()) == 7,
        "Every actual preimport map and contracts binding checked",
    )
    checks.extend(
        [
            "all seven actual helper/entrypoint module maps equal the complete eleven Python source members",
            "actual corrected launcher prefix accepts complete physical copy while literal registered predecessor refuses",
            "actual launcher prefix refuses unknown py/pyc/so additions and obsolete metadata helper",
            "actual launcher prefix refuses FIFO, alias and unexpected import directory without runtime/helper execution",
        ]
    )
    check_absent_import_cache()
    checks.extend(
        [
            "actual SourceFileLoader cache miss falls back to exact pinned source without cache file or directory creation",
            "absent cache attempts and actual protected source reads are distinct identities",
            "existing/unpinned/wrong-tag/write/namespace-escape/changed-source/undeclared-absence cache refusals",
            "cache ancestor alias and before-after absence mutation refusal",
        ]
    )
    print(
        json.dumps(
            {
                "actual_exit": 0,
                "guard_groups": len(checks),
                "checks": checks,
                "no_actual_source_data_or_predictor_execution": True,
            }
        )
    )


if __name__ == "__main__":
    main()
