"""Execute one maintained cohort CLI with closed reads and sealed-target denial."""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import runpy
import sys
import traceback
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

from contracts import (  # noqa: E402
    FAMILIES,
    PACKAGE_ROOTS,
    PREDICTED,
    PREPARED,
    ROOT,
    SCORED,
    dump,
    load,
    pin,
    producer,
    report,
    require,
    verify_inputs,
)


def allowed_open(
    path: Path,
    mode: str,
    flags: int,
    plan: dict[str, Any],
    family: str,
    stage: str,
    pins: set[str],
) -> bool:
    output = Path(plan["output"])
    path = path.absolute()
    writing = any(x in mode for x in "wax+") or bool(
        flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
    )
    aliases = [p for p in (path, *path.parents) if p.is_symlink()]
    declared_aliases = {row["path"]: row for row in plan.get("runtime_aliases", [])}
    for alias in aliases:
        require(
            not writing and str(alias) in declared_aliases,
            "Undeclared source/read alias",
        )
        expected = declared_aliases[str(alias)]
        require(
            os.readlink(alias) == expected["raw_link"]
            and str(alias.resolve()) == expected["resolved_target"],
            "Exact qualified runtime alias differs",
        )
    require(
        (path == path.resolve() or bool(aliases))
        and ".." not in path.parts
        and (not aliases or str(path.resolve()) in pins),
        "Read/write alias outside runtime authority",
    )
    if writing:
        require(path.is_relative_to(output), "Write outside owned output")
    else:
        if str(path) not in pins and not path.is_relative_to(output):
            return absent_source_cache(path, mode, flags, plan, pins)
        require(
            str(path) in pins or path.is_relative_to(output),
            "Unprotected file read: " + str(path),
        )
        if stage == "predict":
            require(
                "sealed-outcomes" not in path.parts
                and not any(path.is_relative_to(ROOT / report(f)) for f in FAMILIES),
                "Prediction read sealed/canonical target evidence",
            )
            if path.is_relative_to(output):
                prepared = output / family / "prepared"
                require(
                    path
                    in {
                        prepared / "input-manifest.json",
                        prepared / "inputs/metadata-SE.json.gz",
                        prepared / "inputs/training-SE.json.gz",
                    },
                    "Prediction read beyond exact three prepared inputs",
                )
    return False


def absent_source_cache(
    path: Path, mode: str, flags: int, plan: dict[str, Any], pins: set[str]
) -> bool:
    """Permit an importer's failed readonly cache probe, never the cache as data."""
    require(
        not any(c in mode for c in "wax+")
        and not flags
        & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND),
        "Absent cache is readonly only",
    )
    require(
        path.is_absolute()
        and path == path.resolve()
        and ".." not in path.parts
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Absent cache lexical/alias boundary",
    )
    require(
        not path.exists() and not path.is_symlink(),
        "Cache candidate must genuinely be absent",
    )
    candidates = plan.get("absent_source_cache_candidates", {})
    require(str(path) in candidates, "Absent cache not frozen in exact plan")
    item = candidates[str(path)]
    source = Path(importlib.util.source_from_cache(str(path)))
    require(
        item["cache_tag"] == sys.implementation.cache_tag
        and item["source_path"] == str(source)
        and str(path) in plan["absent_input_paths"],
        "Cache tag/source/absence declaration differs",
    )
    require(
        Path(importlib.util.cache_from_source(str(source), optimization="")) == path,
        "Noncurrent cache-tag candidate",
    )
    require(
        str(source) in pins
        and source.suffix == ".py"
        and source.is_file()
        and not source.is_symlink()
        and not any(p.is_symlink() for p in source.parents),
        "Cache source is not an exact protected regular .py",
    )
    require(
        any(
            source.is_relative_to(Path(tree["root"]))
            and tree["entries"]
            .get(source.relative_to(Path(tree["root"])).as_posix(), {})
            .get("kind")
            == "file"
            for tree in plan["cache_source_namespaces"]
        ),
        "Cache source outside complete guarded source/runtime namespaces",
    )
    return True


def engine_watch(prefixes: tuple[str, ...], counter: dict[str, int]) -> Any:
    def watch(frame: Any, event: str, arg: Any) -> None:
        if event != "call":
            return
        filename = frame.f_code.co_filename
        if filename.startswith(prefixes) and frame.f_code.co_name != "<module>":
            counter["LRA_numerical_function_calls"] += 1
            raise ValueError(
                "LRA numerical execution outside direct-pollen baseline scope"
            )

    return watch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--family", choices=FAMILIES, required=True)
    parser.add_argument(
        "--stage", choices=("prepare", "predict", "score"), required=True
    )
    args = parser.parse_args()
    plan = load(args.plan)
    verify_inputs(plan)
    family, stage = args.family, args.stage
    output = Path(plan["output"])
    base = output / family
    target = (
        base
        / {"prepare": "prepared", "predict": "predictions", "score": "scores"}[stage]
    )
    require(
        not target.exists() and not target.is_symlink(), "Stage output already exists"
    )
    argv = [
        "bijux_pollenomics_dev.source_completion." + family.replace("-", "_"),
        stage,
    ]
    if stage == "prepare":
        argv += [
            "--repository",
            str(ROOT),
            "--author-source-root",
            plan["private_source_store"],
        ]
    else:
        argv += ["--prepared", str(base / "prepared")]
    if stage == "score":
        argv += ["--predictions", str(base / "predictions")]
    argv += ["--output", str(target)]
    sys.path[:0] = [str(p) for p in PACKAGE_ROOTS]
    reads: set[str] = set()
    absent_cache_attempts: set[str] = set()
    pinned = {row["path"]: row for row in plan["input_pins"]}
    # Reads through the explicitly declared runtime lexical aliases are already
    # guarded by the qualified outer runtime; Python open sees resolved files.
    permitted = {*pinned, *(str(Path(x).resolve()) for x in pinned), str(args.plan)}
    active = True

    def audit(event: str, values: tuple[Any, ...]) -> None:
        if not active:
            return
        if event == "open" and isinstance(values[0], (str, bytes)):
            path = Path(os.fsdecode(values[0]))
            mode = values[1] if type(values[1]) is str else ""
            absent_cache = allowed_open(
                path, mode, values[2], plan, family, stage, permitted
            )
            if absent_cache:
                absent_cache_attempts.add(str(path.absolute()))
                return
            if not any(x in mode for x in "wax+") and not values[2] & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT
            ):
                reads.add(str(path.absolute()))
        elif event in (
            "socket.connect",
            "socket.bind",
            "subprocess.Popen",
            "os.system",
        ):
            raise ValueError("Network/subprocess outside fixed host baseline")

    counters = {"LRA_numerical_function_calls": 0}
    lra = ROOT / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra"
    prefixes = tuple(
        str(lra / part) + "/"
        for part in ("reconstruction", "optimization", "dispersal", "workflows")
    )
    record: dict[str, Any] = {
        "candidate": plan["candidate"],
        "plan": pin(args.plan),
        "family": family,
        "stage": stage,
        "maintained_source": pin(ROOT / producer(family)),
        "actual_source_module_argv": argv,
        "actual_launcher_argv": [sys.executable, *sys.argv],
        "source_exit": None,
        "metadata_exit": None,
        "counters": counters,
    }
    try:
        sys.argv = argv
        sys.addaudithook(audit)
        sys.setprofile(engine_watch(prefixes, counters))
        try:
            runpy.run_module(argv[0], run_name="__main__")
            record["source_exit"] = 0
        except SystemExit as error:
            record["source_exit"] = (
                error.code
                if type(error.code) is int
                else 0
                if error.code is None
                else 1
            )
        except Exception:
            record["source_exit"] = 1
            traceback.print_exc()
        finally:
            sys.setprofile(None)
            active = False
        require(
            record["source_exit"] == 0
            and counters["LRA_numerical_function_calls"] == 0,
            "Maintained source failed or invoked numerical LRA",
        )
        expected_names = {"prepare": PREPARED, "predict": PREDICTED, "score": SCORED}[
            stage
        ]
        for item in target.rglob("*"):
            require(
                not item.is_symlink() and (item.is_file() or item.is_dir()),
                "Generated special/alias",
            )
        actual_names = sorted(
            p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()
        )
        require(
            actual_names == sorted(expected_names),
            "Actual generated membership differs",
        )
        record["produced_files"] = [
            pin(target / name) for name in sorted(expected_names)
        ]
        origins = []
        for name, module in sorted(sys.modules.items()):
            if not name.startswith(("bijux_pollenomics", "pollenomics")):
                continue
            path = getattr(module, "__file__", None)
            require(type(path) is str, "First-party module missing physical origin")
            assert isinstance(path, str)
            item = pin(Path(path))
            require(
                pinned.get(item["path"]) == item
                and any(Path(item["path"]).is_relative_to(p) for p in PACKAGE_ROOTS),
                "First-party origin escaped frozen complete roots",
            )
            origins.append({"module": name, **item})
        record["first_party_origins"] = origins
        record["actual_read_paths"] = sorted(reads)
        record["attempted_absent_source_cache_paths"] = sorted(absent_cache_attempts)
        record["absent_cache_probes_are_actual_protected_reads"] = False
        if stage == "prepare":
            study = plan["studies"][family]
            needed = {
                study["actual_protocol_training"]["path"],
                study["taxonomy_lookup"]["path"],
                *(
                    str(ROOT / p)
                    for p in study["retained_input_manifest"]["source_surface_sha256"]
                ),
            }
            require(
                needed <= reads, "Declared scientific source was not actually consumed"
            )
        verify_inputs(plan)
        record["metadata_exit"] = 0
    except Exception as error:
        active = False
        sys.setprofile(None)
        record.update(metadata_exit=1, metadata_error=str(error))
        traceback.print_exc()
    receipt = output / "native-receipts" / (family + "-" + stage + ".json")
    dump(receipt, record)
    print(
        __import__("json").dumps(
            {
                "source_exit": record["source_exit"],
                "metadata_exit": record["metadata_exit"],
                "source_execution": pin(receipt),
            }
        )
    )
    raise SystemExit(
        0 if record["source_exit"] == 0 and record["metadata_exit"] == 0 else 1
    )


if __name__ == "__main__":
    main()
