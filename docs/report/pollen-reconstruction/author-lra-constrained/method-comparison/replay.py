"""Compare two authenticated saved LOVE methods without refitting or rescoring."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import runpy
from typing import Any


def authenticate_sources(
    protocol_path: Path, expected: str
) -> tuple[bytes, dict[str, Any]]:
    """Authenticate the entire three-file private namespace before any helper executes."""
    if (
        not protocol_path.is_absolute()
        or ".." in protocol_path.parts
        or any(p.is_symlink() for p in (protocol_path, *protocol_path.parents))
        or not protocol_path.is_file()
        or protocol_path.stat().st_nlink != 1
    ):
        raise ValueError("Physical absolute protocol required")
    raw = protocol_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("Registered comparison protocol changed")
    protocol = json.loads(raw)
    rows = protocol["source_files"]
    names = [row["name"] for row in rows]
    if names != ["comparison.py", "replay.py", "sources.py"] or any(
        set(row) != {"name", "sha256", "bytes"} for row in rows
    ):
        raise ValueError("Exact three reviewed comparison sources required")
    owned = Path(__file__).absolute().parent
    companions = {
        "protocol.json",
        "README.md",
        "report.json",
        "paired-scores.csv",
        "fold-dispositions.csv",
    }
    actual = {p.name for p in owned.iterdir()}
    if not set(names) <= actual <= set(names) | companions:
        raise ValueError("Complete comparison code/publication namespace differs")
    for entry in owned.iterdir():
        if entry.name in companions and (
            entry.is_symlink()
            or not entry.is_file()
            or entry.stat().st_nlink != 1
            or entry.stat().st_size > 8 * 1024**2
        ):
            raise ValueError(
                "Published comparison companion must be bounded and physical"
            )
    local_protocol = owned / "protocol.json"
    if (
        local_protocol.exists()
        and hashlib.sha256(local_protocol.read_bytes()).hexdigest() != expected
    ):
        raise ValueError(
            "Published scientific protocol differs from the registered input"
        )
    for row in rows:
        path = owned / row["name"]
        if (
            any(p.is_symlink() for p in (path, *path.parents))
            or not path.is_file()
            or path.stat().st_nlink != 1
            or path.stat().st_size != row["bytes"]
        ):
            raise ValueError("Physical comparison source identity differs")
        body = path.read_bytes()
        if (
            len(body) != row["bytes"]
            or hashlib.sha256(body).hexdigest() != row["sha256"]
        ):
            raise ValueError("Comparison helper changed before execution")
    replay = next(row for row in rows if row["name"] == "replay.py")
    if any(protocol["producer"][key] != replay[key] for key in ("sha256", "bytes")):
        raise ValueError("Comparison entry differs from the scientific protocol")
    return raw, protocol


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.absolute()
    raw, initial = authenticate_sources(args.protocol, args.protocol_sha256)
    source_functions = runpy.run_path(
        str(Path(__file__).absolute().parent / "sources.py")
    )
    arithmetic = runpy.run_path(
        str(Path(__file__).absolute().parent / "comparison.py"),
        init_globals={"sources": source_functions},
    )
    require, decode, digest, read = (
        source_functions[name] for name in ("require", "decode", "digest", "read")
    )
    compare = arithmetic["compare"]
    protocol = decode(raw)
    require(protocol == initial, "same registered protocol buffer differs")
    require(
        protocol["schema_version"] == "author-love-matched-method-protocol.v1",
        "protocol schema differs",
    )
    producer = Path(__file__).absolute()
    require(
        digest(producer.read_bytes()) == protocol["producer"]["sha256"]
        and producer.stat().st_size == protocol["producer"]["bytes"],
        "reviewed comparison producer changed",
    )
    rows = {
        **protocol["inputs"],
        **{
            "prepared:" + name: row for name, row in protocol["prepared_inputs"].items()
        },
    }
    require(
        len(rows) == 51 and len({row["path"] for row in rows.values()}) == 51,
        "exact51 independent logical inputs required",
    )
    bodies = {role: read(repository, row) for role, row in rows.items()}
    report = compare(bodies, protocol)
    output = args.output.absolute()
    require(
        not output.exists()
        and not output.is_symlink()
        and output.is_relative_to(repository / "artifacts")
        and ".." not in output.parts
        and not any(p.is_symlink() for p in output.parents),
        "fresh physical artifact output required",
    )
    for role, row in rows.items():
        require(
            read(repository, row) == bodies[role], "input changed during comparison"
        )
    output.mkdir(parents=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    flat = []
    for row in report["paired_scores"]:
        for metric, values in row["metrics"].items():
            flat.append(
                {
                    "fold_id": row["fold_id"],
                    "record_id": row["record_id"],
                    "baseline": row["baseline"],
                    "metric": metric,
                    **values,
                }
            )
    for name, items, fields in [
        (
            "paired-scores.csv",
            flat,
            (
                "fold_id",
                "record_id",
                "baseline",
                "metric",
                "original",
                "cohort",
                "delta",
                "category",
            ),
        ),
        (
            "fold-dispositions.csv",
            report["fold_dispositions"],
            (
                "fold_id",
                "record_id",
                "original_status",
                "original_reason",
                "cohort_status",
                "paired_baseline_rows",
            ),
        ),
    ]:
        with (output / name).open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(items)
    print(
        json.dumps(
            {
                "saved_result_comparison": True,
                "models_or_rescoring_executed": False,
                "counts": report["counts"],
                "output": str(output),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
