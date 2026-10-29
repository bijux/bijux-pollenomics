"""Authenticate the real metadata-only prerequisite and all its original registered inputs."""

from __future__ import annotations
from pathlib import Path
from typing import Any
from contracts import pin, read, require, sha
from runtime_custody import aliases_unchanged
from observe_runtime_probe import validate_metadata

IDENTITIES = {
    "plan.json": "195696988e1ed51109895514fa04c729b74cf64da00414fc4893a017efb3edf9",
    "terminal.json": "65b3b3dd699559e5d7e663fbabab59364b59d3a19a88863ac9180a6779ea98bb",
    "controlled-runtime-terminal.json": "a66268f607f6a38be8a3745184bfe9b14072f41233c560936fd5a6071a903e19",
    "independent-runtime-review.json": "6a3d32fe1ace7c9b6d687bc32679cb0826425efea7c4e888ba012cba761f8696",
}


def qualify_probe_status(
    plan: dict[str, Any],
    terminal: dict[str, Any],
    outer: dict[str, Any],
    observer: dict[str, Any],
) -> None:
    require(
        plan["candidate"] == "60bf419979bdc682ef227fb01e42a4f5ed6e2722"
        and terminal["candidate"]
        == outer["candidate"]
        == observer["candidate"]
        == plan["candidate"],
        "Qualified runtime source epoch differs",
    )
    require(
        terminal["plan_sha256"]
        == outer["plan_sha256"]
        == observer["plan_sha256"]
        == IDENTITIES["plan.json"],
        "Qualified prerequisite plan joins differ",
    )
    require(
        type(terminal["actual_exit"]) is int
        and terminal["actual_exit"] == 0
        and type(outer["actual_exit"]) is int
        and outer["actual_exit"] == 0
        and type(outer["common_actual_exit"]) is int
        and outer["common_actual_exit"] == 0
        and type(observer["actual_exit"]) is int
        and observer["actual_exit"] == 0,
        "Runtime prerequisite did not pass",
    )
    require(
        outer["common_terminal"]["sha256"] == IDENTITIES["terminal.json"]
        and outer["memory_bound_pass"] is True
        and outer["storage_bound_pass"] is True,
        "Actual resource/common terminal custody differs",
    )
    require(
        len(plan["stages"]) == len(terminal["stages"]) == 2,
        "Both actual runtime stages required",
    )
    for expected, actual in zip(plan["stages"], terminal["stages"], strict=True):
        require(
            actual["argv"] == expected["argv"]
            and actual["id"] == expected["id"]
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Actual runtime prerequisite argv/status differs",
        )
    require(
        not terminal["before_pin_mismatches"]
        and not terminal["after_pin_mismatches"]
        and terminal["canonical_before"]
        == terminal["canonical_after"]
        == plan["canonical_identity"],
        "Qualified runtime before/after custody differs",
    )


def qualify_runtime_probe(root: Path) -> tuple[dict[str, Any], set[Path]]:
    files = set()
    for name, digest in IDENTITIES.items():
        path = root / name
        require(
            sha(path) == digest,
            f"Actual qualified runtime prerequisite changed: {path}",
        )
        files.add(path)
    plan = read(root / "plan.json")
    terminal = read(root / "terminal.json")
    outer = read(root / "controlled-runtime-terminal.json")
    observer = read(root / "independent-runtime-review.json")
    qualify_probe_status(plan, terminal, outer, observer)
    require(
        aliases_unchanged(
            plan["runtime_aliases"], link_text=plan["runtime_alias_links"]
        ),
        "Original runtime prerequisite aliases changed",
    )
    for row in plan["input_pins"]:
        path = Path(row["path"])
        require(
            pin(path) == row, f"Original runtime prerequisite input changed: {path}"
        )
        files.add(path)
    for row in terminal["products"]:
        path = Path(row["path"])
        require(
            pin(path) == row, f"Original runtime prerequisite product changed: {path}"
        )
        files.add(path)
    observation = Path(observer["metadata"]["path"])
    require(
        pin(observation) == observer["metadata"],
        "Actual raw runtime observation changed",
    )
    counts = validate_metadata(read(observation), plan)
    require(
        counts
        == observer["counts"]
        == dict(
            before_namespaces=40, before_DLLs=29, after_namespaces=40, after_DLLs=29
        ),
        "Actual qualified namespace/DLL population differs",
    )
    return {
        "candidate": plan["candidate"],
        "receipts": {name: pin(root / name) for name in IDENTITIES},
        "raw_observation": pin(observation),
        "observed_counts": counts,
        "input_pin_count": len(plan["input_pins"]),
        "source_and_runtime_all_original_pins_revalidated": True,
        "qualification": "Metadata-only original124 prerequisite; not numerical execution or ecological/historical/release acceptance.",
    }, files
