"""Execute an unchanged maintained publication CLI and retain truthful exits/origins."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
import runpy
import sys
import traceback
from typing import Any

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve(strict=True) or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical absolute controller entry and ancestors required")
_entry_directory = _entry_path.parent
_expected_python = {
    "common_runner.py",
    "prepare.py",
    "run.py",
    "runtime_contracts.py",
    "check_contracts.py",
    "runtime_guarded_runner.py",
    "source_runtime.py",
    "observe.py",
    "execute_source.py",
    "contracts.py",
    "metadata.py",
}
_present_python = set()
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry before helper import")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory before helper import")
    if _entry.suffix in {".py", ".pyc", ".so", ".dylib", ".pyd"}:
        if _entry.name not in _expected_python:
            raise ValueError("Unexpected controller import before helper import")
        _present_python.add(_entry.name)
if _present_python != _expected_python:
    raise ValueError("Incomplete exact controller import namespace")
sys.path.insert(0, str(_entry_directory))
import contracts as c  # noqa: E402


def source_origins(plan: dict[str, Any]) -> list[dict[str, Any]]:
    expected = {row["path"]: row for row in plan["input_pins"]}
    records = []
    for name, module in sorted(sys.modules.items()):
        if not (
            name.startswith(("bijux_pollenomics", "pollenomics", "lra."))
            or name == "lra"
        ):
            continue
        value = getattr(module, "__file__", None)
        c.require(isinstance(value, str), "First-party module has no source origin")
        assert isinstance(value, str)
        path = Path(value).resolve(strict=True)
        c.require(
            any(path.is_relative_to(root) for root in c.PACKAGE_ROOTS),
            "First-party import escaped all four owned source trees",
        )
        row = c.pin(path)
        c.require(expected.get(row["path"]) == row, "Unprotected first-party origin")
        records.append({"module": name, **row})
    return records


def call_watcher(
    prefix: str, counters: dict[str, int]
) -> Callable[[Any, str, Any], None]:
    def watch(frame: Any, event: str, arg: Any) -> None:
        if (
            event == "call"
            and frame.f_code.co_filename.startswith(prefix)
            and frame.f_code.co_name != "<module>"
        ):
            counters["LRA_implementation_function_calls"] += 1
            raise ValueError(
                "LRA implementation calls are outside publication metadata scope"
            )

    return watch


def deny_network(counters: dict[str, int]) -> Callable[[str, tuple[Any, ...]], None]:
    def audit(event: str, args: tuple[Any, ...]) -> None:
        if event in {
            "socket.connect",
            "socket.connect_ex",
            "socket.bind",
            "socket.getaddrinfo",
        }:
            counters["network_attempts"] += 1
            raise ValueError("Publication replay has no network permission")

    return audit


def guard_destination(output: Path, destination: Path) -> None:
    c.output_root(output)
    c.require(
        destination.is_relative_to(output) and destination == destination.resolve(),
        "Output destination escaped the artifact root",
    )
    c.require(
        not destination.exists() and not destination.is_symlink(),
        "Absent producer destination required",
    )
    c.require(
        not any(path.is_symlink() for path in (destination, *destination.parents)),
        "Producer destination has an alias ancestor",
    )
    c.require(
        all(not path.exists() or path.is_dir() for path in destination.parents),
        "Producer destination ancestor is not a directory",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--kind", choices=("publication", "doi"), required=True)
    args = parser.parse_args()
    plan = c.load(args.plan)
    c.verify_inputs(plan)
    output = Path(plan["output"])
    source = c.ROOT / c.PRODUCERS[args.kind]
    c.require(
        c.exact(c.pin(source), plan["maintained_sources"][args.kind]),
        "Maintained source differs",
    )
    sys.path[:0] = [str(root) for root in c.PACKAGE_ROOTS]
    repository = (
        c.ROOT if args.kind == "publication" else Path(plan["stage2_repository_view"])
    )
    destination = (
        output
        / "producer"
        / c.REPORT
        / ("report.json" if args.kind == "publication" else "doi-review.json")
    )
    guard_destination(output, destination)
    argv = [
        str(source),
        "--repository",
        str(repository),
        "--capture-root",
        plan["capture_sets"][args.kind]["root"],
        "--output",
        str(destination),
    ]
    input_record = None
    if args.kind == "doi":
        input_record = c.pin(Path(plan["stage2_input_roles"]["generated_attribution"]))
    counters = {"LRA_implementation_function_calls": 0, "network_attempts": 0}
    record: dict[str, Any] = {
        "candidate": plan["candidate"],
        "kind": args.kind,
        "plan": c.pin(args.plan),
        "source": c.pin(source),
        "executed_source_argv": argv,
        "actual_launcher_argv": [sys.executable, *sys.argv],
        "stage2_generated_input": input_record,
        "source_exit": None,
        "metadata_exit": None,
        "metadata_error": None,
        "counters": counters,
    }
    sys.addaudithook(deny_network(counters))
    try:
        sys.argv = argv
        sys.setprofile(
            call_watcher(
                str(c.ROOT / "packages/bijux-pollenomics-lra/src") + "/", counters
            )
        )
        try:
            runpy.run_path(str(source), run_name="__main__")
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
        record["first_party_origins"] = source_origins(plan)
        c.require(
            counters == {"LRA_implementation_function_calls": 0, "network_attempts": 0},
            "Publication metadata boundary was crossed",
        )
        record["produced"] = c.pin(destination) if destination.is_file() else None
        c.verify_inputs(plan)
        record["metadata_exit"] = 0
    except Exception as error:
        sys.setprofile(None)
        record["metadata_exit"] = 1
        record["metadata_error"] = str(error)
        traceback.print_exc()
    c.dump(output / (args.kind + "-source-execution.json"), record)
    raise SystemExit(
        0 if record["source_exit"] == 0 and record["metadata_exit"] == 0 else 1
    )


if __name__ == "__main__":
    main()
