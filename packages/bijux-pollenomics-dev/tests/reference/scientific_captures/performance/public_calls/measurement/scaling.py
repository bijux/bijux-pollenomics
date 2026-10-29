"""Compare equal two-worker batches sequentially and concurrently."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import BinaryIO

from storage import destination, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    output = Path(plan["output"])
    script = Path(__file__).absolute().with_name("measure.py")
    rows = []
    for workload in plan["workloads"]:
        for label, ids in (("sequential", (100, 101)), ("parallel", (102, 103))):
            began = time.perf_counter()
            children = []
            streams: list[BinaryIO] = []
            try:
                for worker in ids:
                    stdout = destination(
                        output, output / f"scaling-{workload}-{worker}.stdout"
                    ).open("xb")
                    stderr = destination(
                        output, output / f"scaling-{workload}-{worker}.stderr"
                    ).open("xb")
                    streams.extend((stdout, stderr))
                    child = subprocess.Popen(
                        [
                            sys.executable,
                            "-B",
                            str(script),
                            "--plan",
                            str(args.plan),
                            "--worker",
                            str(worker),
                            "--workload",
                            workload,
                            "--samples",
                            "1",
                        ],
                        stdout=stdout,
                        stderr=stderr,
                    )
                    children.append(child)
                    if label == "sequential":
                        assert child.wait(timeout=60) == 0
                for child in children:
                    assert child.wait(timeout=60) == 0
            finally:
                for child in children:
                    if child.poll() is None:
                        child.kill()
                    child.wait(timeout=10)
                for stream in streams:
                    stream.close()
            rows.append(
                {
                    "mode": label,
                    "workload": workload,
                    "workers": list(ids),
                    "wall_seconds": time.perf_counter() - began,
                    "total_work": "2identical public workload calls; one numerical thread per worker",
                }
            )
    path = output / "scaling.json"
    assert not path.exists()
    write_json(
        output,
        path,
        {
            "rows": rows,
            "scope": "Independent fresh-process equal-total-work1vs2worker throughput diagnostic; startup/load costs included; no machine/platform extrapolation.",
        },
    )


if __name__ == "__main__":
    main()
