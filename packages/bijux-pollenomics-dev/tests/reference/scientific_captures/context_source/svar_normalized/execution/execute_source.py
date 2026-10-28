"""Execute the unchanged canonical CLI while preserving source and metadata exits separately."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import runpy
import sys
import traceback
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import dump, exact, load, pin, require
from runtime import profile_guard, qualify_process_snapshot, raw_process_snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = load(args.plan)
    output = Path(plan["output"])
    argv = plan["maintained_source_argv"]
    require(
        exact(pin(Path(argv[0])), plan["maintained_source"]),
        "Canonical maintained source differs",
    )
    profile_guard()
    record: dict[str, Any] = {
        "candidate": plan["candidate"],
        "plan": pin(args.plan),
        "actual_launcher_argv": [sys.executable, *sys.argv],
        "interpreter_flags": ["-I", "-S", "-B"],
        "executed_source_argv": argv,
        "source": plan["maintained_source"],
        "before": None,
        "after": None,
        "source_exit": None,
        "metadata_exit": None,
        "metadata_error": None,
    }
    target = output / "source-runtime-observation.json"
    try:
        record["before"] = raw_process_snapshot()
        dump(target, record)
        qualify_process_snapshot(
            record["before"], plan["input_pins"], Path(__file__).resolve().parent
        )
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
        qualify_process_snapshot(
            record["after"], plan["input_pins"], Path(__file__).resolve().parent
        )
        record["metadata_exit"] = 0
    except Exception as error:
        record["metadata_exit"] = 1
        record["metadata_error"] = str(error)
        traceback.print_exc()
    finally:
        dump(target, record)
    report = output / "producer/report.json"
    print(
        json.dumps(
            {
                "source_runtime": pin(target),
                "generated_report": pin(report) if report.is_file() else None,
                "source_exit": record["source_exit"],
                "metadata_exit": record["metadata_exit"],
            }
        ),
        flush=True,
    )
    raise SystemExit(
        0 if record["source_exit"] == 0 and record["metadata_exit"] == 0 else 1
    )


if __name__ == "__main__":
    main()
