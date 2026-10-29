"""Retain completed measurements and first-party source without running models."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from contracts import (
    CAPTURE,
    EXECUTION_CANDIDATE,
    REPORT_ROOT,
    measurement_projection,
    pin,
    qualified_execution,
    require,
    write_json,
)

A = Path(__file__).absolute().parent
PACKAGES = (
    "bijux-pollenomics",
    "bijux-pollenomics-dev",
    "bijux-pollenomics-lra",
    "pollenomics",
)


def retained_source_bytes(repository: Path, row: dict) -> tuple[bytes, str]:
    """Authenticate current exact bytes or the original committed source blob."""
    path = Path(row["path"])
    relative = path.relative_to(repository)
    require(
        any(
            relative.is_relative_to(Path("packages") / name / "src")
            for name in PACKAGES
        ),
        "source is outside the four first-party roots",
    )
    if path.is_file() and not path.is_symlink() and path.resolve() == path:
        raw = path.read_bytes()
        if (
            len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"]
        ):
            return raw, "original_pin_equal_current_bytes"
    raw = subprocess.check_output(
        ["git", "show", EXECUTION_CANDIDATE + ":" + relative.as_posix()],
        cwd=repository,
        timeout=30,
    )
    require(
        len(raw) == row["bytes"] and hashlib.sha256(raw).hexdigest() == row["sha256"],
        "historical committed source is not the actual original input",
    )
    return raw, "original_pin_equal_historical_git_blob"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    root, output = Path(plan["execution_root"]), Path(plan["output"])
    repository = Path(plan["repository"])
    original, review = qualified_execution(root)
    destination = output / "source-products"
    packet = destination / Path(CAPTURE).parent
    require(
        not destination.exists() and destination.resolve() == destination,
        "assembly destination already exists or is linked",
    )
    packet.mkdir(parents=True)
    members: list[dict] = []

    def retain(relative: str, raw: bytes, origin: dict, role: str) -> None:
        target = packet / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
        row = pin(target)
        members.append(
            {
                "path": relative,
                "sha256": row["sha256"],
                "bytes": row["bytes"],
                "original": origin,
                "role": role,
            }
        )

    for path in sorted(root.rglob("*")):
        if path.is_file():
            retain(
                "execution/" + path.relative_to(root).as_posix(),
                path.read_bytes(),
                pin(path),
                "complete_actual_measurement_output_or_log",
            )
    custody = []
    for row in original["input_pins"]:
        path = Path(row["path"])
        if path.is_relative_to(repository) and any(
            path.is_relative_to(repository / "packages" / name / "src")
            for name in PACKAGES
        ):
            raw, admission = retained_source_bytes(repository, row)
            name = "source-code/" + path.relative_to(repository).as_posix()
            retain(name, raw, row, "original_first_party_source_or_resource")
            custody.append(
                {
                    "original": row,
                    "disposition": "retained_first_party",
                    "member": name,
                    "admission": admission,
                }
            )
        elif path.is_relative_to(Path(original["stages"][0]["argv"][2]).parent):
            require(pin(path) == row, "original performance controller differs")
            name = (
                "controls/"
                + path.relative_to(
                    Path(original["stages"][0]["argv"][2]).parent
                ).as_posix()
            )
            retain(name, path.read_bytes(), row, "original_measurement_control")
            custody.append(
                {"original": row, "disposition": "retained_first_party", "member": name}
            )
        elif path == Path(original["common_runner"]):
            require(pin(path) == row, "original common runner differs")
            name = "controls/shared/" + path.name
            retain(name, path.read_bytes(), row, "original_common_execution_control")
            custody.append(
                {"original": row, "disposition": "retained_first_party", "member": name}
            )
        elif path.is_relative_to(repository / "docs/report"):
            require(pin(path) == row, "original public reference input differs")
            name = "reference-inputs/" + path.relative_to(repository).as_posix()
            retain(name, path.read_bytes(), row, "original_public_scientific_reference")
            custody.append(
                {"original": row, "disposition": "retained_first_party", "member": name}
            )
        else:
            custody.append(
                {
                    "original": row,
                    "disposition": "hash_reference_only_not_redistributed",
                }
            )
    metadata_sources = []
    for row in plan["metadata_source_pins"]:
        path = Path(row["path"])
        require(pin(path) == row, "metadata assembly source changed")
        name = "publication-controls/" + path.relative_to(A).as_posix()
        retain(name, path.read_bytes(), row, "metadata_only_publication_control")
        metadata_sources.append({"original": row, "member": name})
    report = measurement_projection(root, original, review)
    write_json(destination / REPORT_ROOT / "report.json", report)
    reader = (A / "report-template.md").read_text()
    rows = []
    for item in report["observations"]:
        rows.append(
            f"| {item['workload']} | {item['worker']} | {item['first_seconds']:.9f} | {item['warm_median_seconds']:.9f} | {item['warm_min_seconds']:.9f}–{item['warm_max_seconds']:.9f} | {item['construction_loading_conversion_seconds']:.6f} | {item['whole_worker_peak_RSS_bytes']} |"
        )
    reader = reader.replace("{{OBSERVATION_ROWS}}", "\n".join(rows))
    require("{{" not in reader, "unresolved reader placeholder")
    reader_path = destination / REPORT_ROOT / "README.md"
    with reader_path.open("x", encoding="utf-8") as stream:
        stream.write(reader)
    for path in (destination / REPORT_ROOT / "report.json", reader_path):
        retain(
            "publication/" + path.name,
            path.read_bytes(),
            pin(path),
            "retained_publication_projection",
        )
    capsule = {
        "schema_version": "representative-performance-source-capture.v1",
        "execution_candidate": EXECUTION_CANDIDATE,
        "assembly_candidate": plan["candidate"],
        "members": sorted(members, key=lambda row: row["path"]),
        "original_input_custody": custody,
        "metadata_source_custody": metadata_sources,
        "input_count": len(custody),
        "first_party_source_scope": "Complete four package src roots and original measurement controls from original plan pins; exact historical Git blobs are used only when current public metadata differs. No current whole-tree or new benchmark identity is asserted.",
        "private_and_runtime_scope": "Original private snapshot and runtime inputs remain hash-only references. Neither their source bytes nor binaries are redistributed. Original zero native terminal and exact before/after pin checks remain retained execution evidence, not a new model run or rights grant.",
        "public_products": [REPORT_ROOT + "/report.json", REPORT_ROOT + "/README.md"],
        "scope": report["scope"],
    }
    write_json(packet / "capture.json", capsule)
    write_json(
        output / "assembly-receipt.json",
        {
            "source_only_metadata_assembly": True,
            "candidate": plan["candidate"],
            "execution_candidate": EXECUTION_CANDIDATE,
            "capture": pin(packet / "capture.json"),
            "members": len(members),
            "original_input_references": len(custody),
            "new_model_timing_profile_compiler_R_calls": 0,
        },
    )


if __name__ == "__main__":
    main()
