"""Run an unchanged canonical Rootsi CLI with its real __file__ and isolated xlrd."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import runpy
import sys
import traceback
from typing import Any

# Authenticate the physical helper namespace before Python can select local imports.
_entrypoint_path = Path(__file__).absolute()
_source_directory = _entrypoint_path.parent
if _entrypoint_path != _entrypoint_path.resolve() or any(
    _ancestor.is_symlink()
    for _ancestor in (_entrypoint_path, *_entrypoint_path.parents)
):
    raise ValueError("Controller entrypoint or ancestor is an alias")
_source_modules = {
    "observe.py",
    "common_runner.py",
    "prepare.py",
    "cache_contract.py",
    "runtime.py",
    "contracts.py",
    "run.py",
    "execute_source.py",
    "independent.py",
    "check_contracts.py",
}
for _entry in _source_directory.iterdir():
    if _entry.is_symlink() or (not _entry.is_file() and not _entry.is_dir()):
        raise ValueError("Controller namespace contains an alias/special entry")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller import directory")
    if _entry.suffix in {".py", ".pyc", ".so"} and _entry.name not in _source_modules:
        raise ValueError("Unexpected controller import member")
sys.path.insert(0, str(_source_directory))
from contracts import (  # noqa: E402 — authenticate local imports first.
    LANES,
    SOURCE,
    confined_output,
    dump,
    exact,
    load,
    pin,
    require,
    source_namespace,
    verify_frozen_pins,
)
from runtime import (  # noqa: E402 — authenticate local imports first.
    enable_xlrd,
    profile_guard,
    qualify_process_snapshot,
    raw_process_snapshot,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--lane", choices=LANES, required=True)
    args = parser.parse_args()
    source_namespace()
    profile_guard()
    plan = load(args.plan)
    output = confined_output(Path(plan["output"]))
    lane = plan["lanes"][args.lane]
    argv = lane["source_argv"]
    verify_frozen_pins(plan["input_pins"])
    require(exact(pin(Path(argv[0])), lane["source"]), "Canonical source differs")
    require(
        confined_output(Path(argv[-1]), absent=True).is_relative_to(output),
        "Fresh owned report target required",
    )
    enable_xlrd()
    record: dict[str, Any] = {
        "candidate": plan["candidate"],
        "plan": pin(args.plan),
        "lane": args.lane,
        "source": lane["source"],
        "actual_launcher_argv": [sys.executable, *sys.argv],
        "interpreter_flags": ["-I", "-S", "-B"],
        "executed_source_argv": argv,
        "xlrd_cache_contract": pin(SOURCE / "xlrd-cache-contract.json"),
        "before": None,
        "after": None,
        "source_exit": None,
        "metadata_exit": None,
        "metadata_error": None,
    }
    target = output / (args.lane + "-source-runtime.json")
    try:
        record["before"] = raw_process_snapshot()
        dump(target, record)
        qualify_process_snapshot(record["before"], plan["input_pins"], SOURCE)
        sys.argv = list(argv)
        try:
            runpy.run_path(argv[0], run_name="__main__")
            record["source_exit"] = 0
        except SystemExit as error:
            record["source_exit"] = (
                error.code
                if type(error.code) is int
                else (0 if error.code is None else 1)
            )
        except Exception:
            record["source_exit"] = 1
            traceback.print_exc()
        finally:
            dump(target, record)
        record["after"] = raw_process_snapshot()
        dump(target, record)
        qualify_process_snapshot(record["after"], plan["input_pins"], SOURCE)
        verify_frozen_pins(plan["input_pins"])
        record["metadata_exit"] = 0
    except Exception as error:
        record["metadata_exit"] = 1
        record["metadata_error"] = str(error)
        traceback.print_exc()
    finally:
        dump(target, record)
    print(
        json.dumps(
            {
                "source_runtime": pin(target),
                "generated_report": pin(Path(argv[-1]))
                if Path(argv[-1]).is_file()
                else None,
                "source_exit": record["source_exit"],
                "metadata_exit": record["metadata_exit"],
            }
        ),
        flush=True,
    )
    raise SystemExit(
        0
        if type(record["source_exit"]) is int
        and record["source_exit"] == 0
        and type(record["metadata_exit"]) is int
        and record["metadata_exit"] == 0
        else 1
    )


if __name__ == "__main__":
    main()
