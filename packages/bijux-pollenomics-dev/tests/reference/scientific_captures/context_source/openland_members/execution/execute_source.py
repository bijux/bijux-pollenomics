"""Execute the unchanged OpenLand CLI with bounded member-read and source-origin telemetry."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import json
from pathlib import Path
import runpy
import sys
import traceback
from typing import Any
from zipfile import ZipFile, ZipInfo

_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve() or any(
    p.is_symlink() for p in (_entry_path, *_entry_path.parents)
):
    raise ValueError("Physical entrypoint required before helper imports")
_entry_directory = _entry_path.parent
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


def member_watch(
    zip_read_filename: str,
    lra_prefix: str,
    archive_path: str,
    expected_reads: set[str],
    counters: dict[str, Any],
) -> Callable[[Any, str, Any], None]:
    """Inspect relevant raw filenames before any function-name or local-variable lookup."""
    require(
        lra_prefix.startswith("/") and lra_prefix.endswith("/"),
        "Exact absolute LRA directory prefix required",
    )

    def watch(frame: Any, event: str, arg: Any) -> None:
        if event != "call":
            return
        filename = frame.f_code.co_filename
        if filename == zip_read_filename:
            if frame.f_code.co_name != "read":
                return
            zipped = frame.f_locals.get("self")
            if isinstance(zipped, ZipFile) and zipped.filename == archive_path:
                name = frame.f_locals["name"]
                member = name.filename if isinstance(name, ZipInfo) else name
                require(
                    type(member) is str and member in expected_reads,
                    "Undeclared member payload read",
                )
                counters["member_content_reads"].append(member)
        elif filename.startswith(lra_prefix) and frame.f_code.co_name != "<module>":
            counters["LRA_implementation_function_calls"] += 1
            raise ValueError("LRA implementation execution is outside source scope")

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
        "--archive",
        plan["source_input_records"]["archive"]["path"],
        "--upstream-tree",
        plan["source_input_records"]["upstream_tree"]["path"],
        "--output",
        str(output / "producer"),
    ]
    require(exact(pin(source), plan["maintained_source"]), "Maintained source differs")
    counters: dict[str, Any] = {
        "member_content_reads": [],
        "LRA_implementation_function_calls": 0,
    }
    import metadata

    expected_reads = {
        *metadata.CSV_MEMBERS,
        metadata.PDF_MEMBER,
        metadata.SCRIPT_MEMBER,
    }
    archive_path = plan["source_input_records"]["archive"]["path"]
    zip_read_filename = ZipFile.read.__code__.co_filename
    lra_prefix = str(ROOT / "packages/bijux-pollenomics-lra/src") + "/"
    watch = member_watch(
        zip_read_filename, lra_prefix, archive_path, expected_reads, counters
    )

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
            set(counters["member_content_reads"]) == expected_reads
            and len(counters["member_content_reads"]) == 27
            and counters["LRA_implementation_function_calls"] == 0,
            "Exact27 declared payload reads and no LRA calls required",
        )
        copied = []
        for role in ("upstream_tree", "doi_lineage"):
            record_input = plan["source_input_records"][role]
            source_input = Path(record_input["path"])
            require(
                exact(pin(source_input), record_input),
                "Retained input changed before copy",
            )
            target = output / "retained-inputs" / source_input.name
            with target.open("xb") as stream:
                stream.write(source_input.read_bytes())
            require(
                pin(target)["sha256"] == record_input["sha256"]
                and pin(target)["bytes"] == record_input["bytes"],
                "Retained input copy differs",
            )
            copied.append(
                {
                    "role": "retained_declared_metadata_input_not_new_acquisition",
                    "source": record_input,
                    "copied": pin(target),
                }
            )
        record["retained_input_copy_chain"] = copied
        verify_inputs(plan)
        record["metadata_exit"] = 0
    except Exception as error:
        sys.setprofile(None)
        record["metadata_exit"] = 1
        record["metadata_error"] = str(error)
        traceback.print_exc()
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
