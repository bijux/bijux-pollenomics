"""Authenticate the complete source-bound constrained run and its eleven produced results."""

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

JsonObject = dict[str, Any]

R = Path(__file__).absolute().parents[3]
AUTHORITY = "configs/ci/qualified-report-sources/landclim-author-snapshot.json"
PRIVATE = R.parent / "-bijux-pollenomics-data/landclim/author-reference"
PACKET = "data/method-certification/constrained-author-source-capture"
ACCOUNTS = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.json"
LANES: dict[str, JsonObject] = {
    "complete-constrained": {
        "root": "current-constrained-author-complete-source",
        "candidate": "22c6e480ba4690cc508202925a8773afe95ab36e",
        "plan_sha256": "7a75256e79a577280d8bd828380ebb8438b80914e3aa8c5ddc390fa428e6428c",
        "outer_sha256": "c4ab7b6a50c989cd646454ae2b52020df2bbdc749a4806077a45917117fc1539",
        "observer": "independent-constrained-author-review.json",
        "observer_sha256": "93f0c05d69b2bd9a59a9b05759e757f8815a48390c0208c72d86c85e0b04cb9f",
    }
}
FAMILY = "docs/report/pollen-reconstruction/author-lra-constrained/"
PRODUCT_NAMES = (
    "folds.csv",
    "predictions.csv",
    "scores.csv",
    "report.json",
    "direct-pollen/manifest.json",
    "direct-pollen/predictions.json",
    "direct-pollen/comparison.json",
    "direct-pollen/matched-scores.csv",
    "direct-pollen/site-sensitivity.json",
    "direct-pollen/paired-hellinger.json",
    "direct-pollen/paired-hellinger-sensitivity.json",
)
PRODUCTS = {
    name: (
        "pollen-reconstruction/author-lra-constrained/report-products",
        FAMILY + name,
    )
    for name in PRODUCT_NAMES
}

READER_METADATA = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.json"
NONMATH_GUARD = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/maintained_sources.py"


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def regular(path: Path) -> JsonObject:
    assert path.is_absolute() and ".." not in path.parts
    assert path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def safe_member(name: str) -> Path:
    path = Path(name)
    assert name and not path.is_absolute() and ".." not in path.parts
    assert path.as_posix() == name and name not in {".", "capture.json"}
    return path


def git_blob(candidate: str, name: str) -> bytes:
    safe_member(name)
    return subprocess.check_output(
        ["git", "show", f"{candidate}:{name}"], cwd=R, timeout=60
    )


def matches(raw: bytes, item: JsonObject) -> bool:
    return bool(
        len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"]
    )


def validate_terminal(
    plan: JsonObject, terminal: JsonObject, outer: JsonObject
) -> None:
    assert terminal["candidate"] == outer["candidate"] == plan["candidate"]
    assert type(terminal["actual_exit"]) is int and terminal["actual_exit"] == 0
    assert type(outer["actual_exit"]) is int and outer["actual_exit"] == 0
    assert terminal["status"] == "passed" and outer["common_actual_exit"] == 0
    assert outer["memory_bound_pass"] is True and outer["storage_bound_pass"] is True
    assert terminal["before_pin_mismatches"] == terminal["after_pin_mismatches"] == []
    assert terminal["absent_input_paths_unchanged"] is True
    assert (
        terminal["canonical_before"]
        == terminal["canonical_after"]
        == plan["canonical_identity"]
    )
    assert terminal["canonical_before"]["status"] == ""
    assert len(terminal["stages"]) == len(plan["stages"]) == 2
    for actual, expected in zip(terminal["stages"], plan["stages"], strict=True):
        assert actual["id"] == expected["id"] and actual["argv"] == expected["argv"]
        assert type(actual["actual_exit"]) is int and actual["actual_exit"] == 0
        assert actual["timed_out"] is False
    expected_launch = [
        plan["qualified_python"],
        plan["common_runner"],
        "--plan",
        str(Path(plan["output"]) / "plan.json"),
        "--registered-plan-sha256",
        terminal["plan_sha256"],
    ]
    assert terminal["actual_launch_argv"] == expected_launch


def recover_original_pin(
    item: JsonObject, candidate: str, aliases: dict[str, str]
) -> tuple[JsonObject, bytes | None]:
    """Retain an original Git blob while authenticating its changed current counterpart."""
    path = Path(item["path"])
    if path.is_symlink():
        assert str(path) in aliases and path.resolve() == Path(aliases[str(path)])
        target = regular(path.resolve())
        assert target["sha256"] == item["sha256"] and target["bytes"] == item["bytes"]
        return {"original": item, "current": target, "runtime_entry": str(path)}, None
    current = regular(path)
    if current == item:
        return {"original": item, "current": current}, None
    assert path.is_relative_to(R) and not path.is_relative_to(R / "artifacts")
    name = path.relative_to(R).as_posix()
    original = git_blob(candidate, name)
    assert matches(original, item), (
        f"Original registered source does not match Git {candidate}:{name}"
    )
    current_git = git_blob("HEAD", name)
    assert matches(current_git, current), (
        f"Changed current source is not its clean Git blob: {name}"
    )
    return {
        "original": item,
        "current": current,
        "recovered_git_blob": {"candidate": candidate, "path": name},
    }, original


def validate_product_scope(
    products: list[JsonObject], references: list[JsonObject]
) -> None:
    assert len(products) == 11 and {p["path"] for p in products} == {
        p[1] for p in PRODUCTS.values()
    }
    assert references == []


def validate_native_population(receipts: list[JsonObject], report: JsonObject) -> None:
    assert len(receipts) == 195
    completed = [r for r in receipts if r["item_status"] == "completed"]
    refused = [r for r in receipts if r["item_status"] == "refused"]
    assert len(completed) == 192 and len(refused) == 3
    assert sorted(r["item_id"] for r in refused) == [
        "author:CUTHILL2",
        "author:HANGINGS",
        "author:LONGBREACH",
    ]
    assert all("product" not in r and isinstance(r["error"], dict) for r in refused)
    assert all(isinstance(r["product"], dict) for r in completed)
    assert all(r["scientific_acceptance"] == "not_evaluated" for r in receipts)
    for key, expected in (
        ("requested_folds", 15),
        ("predicted_folds", 14),
        ("refused_folds", 1),
        ("training_items_completed", 192),
        ("training_items_refused", 3),
    ):
        assert type(report[key]) is int and report[key] == expected
    assert (
        report["refused_site"] == "author:BECKHAM"
        and report["measured_vegetation_accuracy"] is None
    )


def validate_original_pin_population(original_pins: list[JsonObject]) -> None:
    assert len(original_pins) == len({row["path"] for row in original_pins}) == 33336


def authenticate() -> JsonObject:
    """Authenticate original inputs, retaining original Git bytes without changing the epoch."""
    import sys

    sys.path[:0] = [
        str(R / f"packages/{name}/src")
        for name in (
            "bijux-pollenomics-dev",
            "bijux-pollenomics",
            "bijux-pollenomics-lra",
            "pollenomics",
        )
    ]
    from bijux_pollenomics_dev.ci.report_rebuild.author_snapshot import (
        validated_author_snapshot,
    )

    qualified = validated_author_snapshot(R, PRIVATE.parents[1], Path(AUTHORITY))
    assert qualified.directory == PRIVATE and len(qualified.inputs) == 195
    spec = LANES["complete-constrained"]
    lane = "complete-constrained"
    root = R / "artifacts/science" / spec["root"]
    pp, tp, op = (
        root / "plan.json",
        root / "terminal.json",
        root / "constrained-author-terminal.json",
    )
    assert sha(pp) == spec["plan_sha256"] and sha(op) == spec["outer_sha256"]
    plan, terminal, outer = [json.loads(p.read_bytes()) for p in (pp, tp, op)]
    assert plan["candidate"] == spec["candidate"] and plan["repository"] == str(R)
    assert terminal["plan_sha256"] == outer["plan_sha256"] == sha(pp)
    assert outer["common_terminal"] == {"path": str(tp), "sha256": sha(tp)}
    validate_terminal(plan, terminal, outer)
    witness = root / spec["observer"]
    assert sha(witness) == spec["observer_sha256"]
    review = json.loads(witness.read_bytes())
    assert review["candidate"] == spec["candidate"]
    assert review["all_eleven_products_scientific_values_equal"] is True
    assert (
        review["native_training_items"],
        review["native_completed"],
        review["native_refused"],
    ) == (195, 192, 3)
    assert review["refused_training_sites"] == [
        "author:CUTHILL2",
        "author:HANGINGS",
        "author:LONGBREACH",
    ]
    assert review["historical_3d6_terminal_available"] is False
    entries: list[JsonObject] = []
    pins: dict[str, JsonObject] = {}
    recovered: dict[str, bytes] = {}
    history: list[JsonObject] = []
    recoveries: list[JsonObject] = []
    public: list[JsonObject] = []
    projection: list[JsonObject] = []

    def retain(path: Path, target: str) -> None:
        safe_member(target)
        row = regular(path)
        pins[row["path"]] = row
        entries.append({**row, "target": target})

    def blob(raw: bytes, target: str, key: str) -> None:
        safe_member(target)
        recovered[key] = raw
        entries.append(
            {
                "recovery_key": key,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
                "target": target,
            }
        )

    original_pins = plan["input_pins"]
    validate_original_pin_population(original_pins)
    by_path = {r["path"]: r for r in original_pins}
    for item in original_pins:
        record, raw = recover_original_pin(
            item, spec["candidate"], plan["runtime_entry_targets"]
        )
        history.append(record)
        pins[record["current"]["path"]] = record["current"]
        path = Path(item["path"])
        if raw is not None:
            key = f"{lane}/{len(recoveries)}"
            recoveries.append({"key": key, **record})
            blob(
                raw,
                f"executions/{lane}/original-inputs/{path.relative_to(R).as_posix()}",
                key,
            )
        if path.is_relative_to(R) and path.relative_to(R).parts[0] in {
            "packages",
            "docs",
            "configs",
        }:
            name = path.relative_to(R).as_posix()
            target = f"executions/{lane}/first-party-inputs/{name}"
            if raw is None:
                retain(path, target)
            else:
                blob(raw, target, f"source/{name}")
            public.append(
                {
                    "path": name,
                    "sha256": item["sha256"],
                    "bytes": item["bytes"],
                    "captured_path": target,
                }
            )
            # Authenticate original package inputs and producer code available to this execution; new unrelated modules are not inferred into it.
            if (
                name.startswith("packages/")
                and "/src/" in name
                and name not in {NONMATH_GUARD, READER_METADATA}
            ) or (name.startswith("docs/") and path.suffix == ".py"):
                assert regular(path)["sha256"] == item["sha256"]
                projection.append(
                    {"path": name, "sha256": item["sha256"], "bytes": item["bytes"]}
                )
        elif path.is_relative_to(R / "artifacts") and not path.is_relative_to(
            R / "artifacts/science/runtime"
        ):
            retain(
                path,
                f"executions/{lane}/controlled-inputs/{path.relative_to(R).as_posix()}",
            )
    for entry, target in plan["runtime_entry_targets"].items():
        assert (
            Path(entry).is_symlink()
            and Path(entry).resolve() == Path(target)
            and target in by_path
        )
    assert all(not Path(p).exists() for p in plan["absent_input_paths"])
    for path in (pp, tp, op, witness):
        retain(path, f"executions/{lane}/{path.name}")
    for stage in terminal["stages"]:
        for kind in ("stdout", "stderr"):
            path = Path(stage[kind])
            assert sha(path) == stage[kind + "_sha256"]
            retain(path, f"executions/{lane}/logs/{path.name}")
    for name in (
        "LICENSE",
        "NOTICE",
        "packages/bijux-pollenomics-lra/LICENSE",
        "packages/bijux-pollenomics-lra/NOTICE",
    ):
        blob(
            git_blob(spec["candidate"], name),
            f"executions/{lane}/legal/{name}",
            f"legal/{name}",
        )
    original_controls = (
        R
        / "artifacts/science/constrained-author-provenance-custody/prepared-source-manifest.json"
    )
    assert (
        sha(original_controls)
        == "b991de9d6c60745b5c8299b7319ac43b17ee24f82f17e95652e70e5b03bba4e1"
    )
    original_manifest = json.loads(original_controls.read_bytes())
    assert len(original_manifest["files"]) == 9
    for row in original_manifest["files"]:
        path = original_controls.parent / safe_member(row["path"])
        assert by_path[str(path)] == regular(path) == {**row, "path": str(path)}
    # Retain the complete produced work tree, authenticated by the original common terminal.
    work = Path(plan["retained_work"])
    declared_work = {
        r["path"]: r
        for r in terminal["products"]
        if Path(r["path"]).is_relative_to(work)
    }
    physical_work = {
        str(path): regular(path) for path in work.rglob("*") if path.is_file()
    }
    assert physical_work == declared_work and len(physical_work) == 900
    assert not any(path.is_symlink() for path in work.rglob("*"))
    for row in physical_work.values():
        path = Path(row["path"])
        retain(
            path, f"executions/{lane}/complete-work/{path.relative_to(work).as_posix()}"
        )
    product_proofs = {r["path"]: r for r in terminal["products"]}
    products = []
    for label, (existing_owner, name) in PRODUCTS.items():
        path = Path(plan["source_products"]) / label
        canonical = R / name
        assert regular(path) == product_proofs[str(path)]
        assert sha(canonical) == product_proofs[str(path)]["sha256"]
        assert path.read_bytes() == canonical.read_bytes()
        retain(path, f"executions/{lane}/products/{label}")
        retain(canonical, f"published/{name}")
        products.append(
            {
                "owner_id": existing_owner,
                "previous_owner_id": existing_owner,
                "path": name,
                "raw": regular(path),
                "native_terminal_product_proof": product_proofs[str(path)],
                "published": regular(canonical),
                "retained_path": f"published/{name}",
                "execution_lane": lane,
                "raw_name": label,
            }
        )
    reference_inputs: list[JsonObject] = []
    retain(R / AUTHORITY, "authority/landclim-author-snapshot.json")
    retain(PRIVATE / "snapshot-manifest.json", "authority/private-source-manifest.json")
    validate_product_scope(products, reference_inputs)
    targets = [r["target"] for r in entries]
    assert len(targets) == len(set(targets))
    assert all(
        not Path(r.get("path", "/")).is_relative_to(PRIVATE)
        or r["target"] == "authority/private-source-manifest.json"
        for r in entries
    )
    return {
        "entries": sorted(entries, key=lambda r: r["target"]),
        "pins": list(pins.values()),
        "recoveries": recovered,
        "execution_custody": {
            lane: {
                "candidate": spec["candidate"],
                "original_plan_sha256": sha(pp),
                "original_input_count": len(history),
                "input_custody": history,
                "git_recoveries": recoveries,
                "public_first_party_inputs": public,
                "runtime_entry_targets": plan["runtime_entry_targets"],
                "original_controller_members": 9,
                "retained_complete_work_files": 900,
                "complete_work_proofs": list(physical_work.values()),
            }
        },
        "report_outputs": products,
        "reference_inputs": reference_inputs,
        "current_scientific_source_projection": sorted(
            projection, key=lambda r: r["path"]
        ),
    }
