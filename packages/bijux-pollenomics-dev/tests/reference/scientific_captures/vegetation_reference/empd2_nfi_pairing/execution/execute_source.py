"""Execute the unchanged pairing CLI with outcome-selection and source-origin telemetry."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import runpy
import sys
import traceback
from typing import Any, cast

_entry_directory = Path(__file__).resolve().parent
_expected_python = {
    "contracts.py",
    "metadata.py",
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
from contracts import (  # noqa: E402 - authenticate the local import namespace first.
    PACKAGE_ROOTS,
    PRODUCER,
    ROOT,
    dump,
    exact,
    load,
    pin,
    require,
    verify_inputs,
)

PROJ_USER_DATA_GETTER = "get_user_data_dir"
PROJ_NETWORK_GETTER = "is_network_enabled"


def project_runtime(plan: dict[str, Any]) -> dict[str, Any]:
    import pyproj
    from pyproj import datadir, network

    expected = Path(plan["PROJ_data_directory"])
    require(Path(datadir.get_data_dir()) == expected, "Unowned PROJ data path")
    require(
        Path(
            cast(Callable[[bool], str], getattr(datadir, PROJ_USER_DATA_GETTER))(False)
        )
        == Path(plan["PROJ_user_directory"]),
        "PROJ user directory differs from private artifact path",
    )
    require(
        cast(Callable[[], bool], getattr(network, PROJ_NETWORK_GETTER))() is False,
        "PROJ network access enabled",
    )
    rows = {r["path"]: r for r in plan["input_pins"]}
    origins = []
    for name, module in sorted(sys.modules.items()):
        if name == "pyproj" or name.startswith("pyproj."):
            path = getattr(module, "__file__", None)
            if path:
                record = pin(Path(path).resolve(strict=True))
                require(
                    rows.get(record["path"]) == record, "Unprotected PROJ module origin"
                )
                origins.append({"module": name, **record})
    return {
        "pyproj_version": pyproj.__version__,
        "PROJ_version": pyproj.proj_version_str,
        "data_directory": str(expected),
        "proj_db": pin(expected / "proj.db"),
        "private_user_directory": plan["PROJ_user_directory"],
        "network_enabled": False,
        "module_origins": origins,
        "same_input_R_or_LRA_estimator_called": False,
        "OS_network_firewall_or_complete_mapped_image_census_claimed": False,
    }


def source_origins(plan: dict[str, Any]) -> list[dict[str, Any]]:
    rows = {r["path"]: r for r in plan["input_pins"]}
    records = []
    for name, module in sorted(sys.modules.items()):
        if not name.startswith(("bijux_pollenomics", "pollenomics")):
            continue
        value = getattr(module, "__file__", None)
        require(
            isinstance(value, str), "First-party module lacks physical source origin"
        )
        assert isinstance(value, str)
        path = Path(value).resolve(strict=True)
        require(
            any(path.is_relative_to(root) for root in PACKAGE_ROOTS),
            "First-party source escaped owned source trees",
        )
        item = pin(path)
        require(rows.get(item["path"]) == item, "Unprotected first-party source origin")
        records.append({"module": name, **item})
    return records


def source_call_watcher(
    nfi_filename: str, lra_prefix: str, counters: dict[str, int]
) -> Callable[[Any, str, Any], None]:
    """Inspect only owned source calls without allocating paths for unrelated frames."""

    def watch(frame: Any, event: str, arg: Any) -> None:
        if event != "call":
            return
        filename = frame.f_code.co_filename
        if filename == nfi_filename:
            name = frame.f_code.co_name
            if name == "_cell":
                cell = frame.f_locals["cell"]
                column = cell.get("r", "").rstrip("0123456789")
                if column not in {"A", "B", "C", "D", "E", "F"}:
                    counters["outcome_cell_decode_attempts"] += 1
                    raise ValueError("Tree outcome cell decoder reached")
                counters["selected_NFI_cells"] += 1
            if name == "_selected":
                counters["selected_NFI_rows"] += 1
        if filename.startswith(lra_prefix) and frame.f_code.co_name != "<module>":
            counters["LRA_implementation_function_calls"] += 1
            raise ValueError("LRA implementation execution is outside metadata scope")

    return watch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = load(args.plan)
    verify_inputs(plan)
    output = Path(plan["output"])
    sys.path[:0] = [str(p) for p in PACKAGE_ROOTS]
    source = ROOT / PRODUCER
    argv = [
        str(source),
        "--repository",
        str(ROOT),
        "--private-source-store",
        plan["private_source_store"],
        "--output",
        str(output / "producer"),
    ]
    require(exact(pin(source), plan["maintained_source"]), "Maintained source changed")
    counters = {
        "selected_NFI_cells": 0,
        "selected_NFI_rows": 0,
        "outcome_cell_decode_attempts": 0,
        "LRA_implementation_function_calls": 0,
    }
    nfi_source = (
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/empd2_nfi.py"
    ).resolve()
    lra_root = ROOT / "packages/bijux-pollenomics-lra/src"

    watch = source_call_watcher(str(nfi_source), str(lra_root) + "/", counters)

    record: dict[str, Any] = {
        "candidate": plan["candidate"],
        "plan": pin(args.plan),
        "source": pin(source),
        "executed_source_argv": argv,
        "actual_launcher_argv": [sys.executable, *sys.argv],
        "source_exit": None,
        "metadata_exit": None,
        "metadata_error": None,
        "counters": counters,
    }
    try:
        record["PROJ"] = project_runtime(plan)
        sys.argv = argv
        sys.setprofile(watch)
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
        require(
            counters
            == {
                "selected_NFI_cells": (43892 + 1) * 6,
                "selected_NFI_rows": 43892 + 1,
                "outcome_cell_decode_attempts": 0,
                "LRA_implementation_function_calls": 0,
            },
            "Maintained six-column metadata access changed",
        )
        verify_inputs(plan)
        record["metadata_exit"] = 0
    except Exception as error:
        sys.setprofile(None)
        record["metadata_exit"] = 1
        record["metadata_error"] = str(error)
        traceback.print_exc()
    record["raw_XML_and_shared_strings_physically_read"] = (
        counters["selected_NFI_rows"] > 0
    )
    record["raw_outcome_bytes_unread_claimed"] = False
    dump(output / "source-execution.json", record)
    print(
        json.dumps(
            {
                "source_exit": record["source_exit"],
                "metadata_exit": record["metadata_exit"],
                "source_execution": pin(output / "source-execution.json"),
            }
        )
    )
    raise SystemExit(
        0 if record["source_exit"] == 0 and record["metadata_exit"] == 0 else 1
    )


if __name__ == "__main__":
    main()
