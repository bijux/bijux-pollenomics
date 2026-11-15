"""Real source capsules and federation fixtures for selected reader contracts."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
    write_neotoma_ancillary_capsule,
)
from bijux_pollenomics.collection.sources.neotoma.ancillary_store.federation import (
    load_neotoma_ancillary_federation,
    write_neotoma_ancillary_federation,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
    encoded_json,
)
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


def pin(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def selected_products(capsule_inputs: dict[str, Any], tmp_path: Path) -> dict[str, Any]:
    capsule = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(capsule, **capsule_inputs)
    sources = {pin(capsule / "manifest.json"): capsule}
    inputs = {
        key: capsule_inputs[key]
        for key in (
            "context_directory",
            "expected_context_sha256",
            "native_archive_directory",
        )
    }
    inputs["capsule_sources"] = sources
    output = tmp_path / "federation"
    write_neotoma_ancillary_federation(output, **inputs)
    view = load_neotoma_ancillary_federation(
        output,
        expected_manifest_sha256=pin(output / "manifest.json"),
        **{
            key: value
            for key, value in inputs.items()
            if key != "expected_context_sha256"
        },
    )
    return {
        "directory": output,
        "kwargs": {
            **inputs,
            "expected_manifest_sha256": pin(output / "manifest.json"),
            "expected_native_archive_sha256": pin(
                inputs["native_archive_directory"] / "manifest.json"
            ),
        },
        "view": view,
        "capsule": capsule,
    }


def facet_row(
    products: dict[str, Any], *, dataset: int = 201, legacy: bool = False
) -> dict[str, Any]:
    return next(
        row
        for row in products["view"].observations
        if row["kind"] == "facet"
        and row["root_identity"]["dataset_id"] == dataset
        and row["facet"] == "taxa"
        and (row["capture_parent_scope_verification"] == "not_recorded_legacy_capture")
        == legacy
    )


def entity_paths(products: dict[str, Any]) -> set[Path]:
    return set(products["capsule"].rglob("*.body"))


def observe_entities(
    monkeypatch: pytest.MonkeyPatch, products: dict[str, Any], allowed: set[Path]
) -> list[Path]:
    paths = entity_paths(products)
    opened = []
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path in paths:
            assert path in allowed, f"Unselected entity opened: {path}"
            opened.append(path)
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    return opened


def rewrite_federation_member(
    products: dict[str, Any], relative: str, document: dict[str, Any]
) -> None:
    directory = products["directory"]
    content = encoded_json(document)
    (directory / relative).write_bytes(content)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    manifest["files"][relative] = {
        "bytes": len(content),
        "sha256": sha256(content).hexdigest(),
    }
    if relative == "scope/current-parent-proof.json":
        manifest["current_use_parent_obligations_sha256"] = sha256(content).hexdigest()
        manifest["current_use_parent_obligations"].update(manifest["files"][relative])
    manifest["source_bytes"] = sum(
        member["bytes"] for member in manifest["files"].values()
    )
    (directory / "manifest.json").write_bytes(encoded_json(manifest))
    products["kwargs"]["expected_manifest_sha256"] = pin(directory / "manifest.json")


def rewrite_index_row(
    products: dict[str, Any], population: str, key: str, mutate: Any
) -> None:
    directory = products["directory"]
    index = json.loads((directory / "index.json").read_bytes())
    field = {
        "slots": "slot_key",
        "observations": "observation_id",
        "linked_occurrences": "occurrence_id",
    }[population]
    for part in index["parts"]:
        if (
            part["population"] == population
            and part["first_key"] <= key <= part["last_key"]
        ):
            content = json.loads((directory / part["path"]).read_bytes())
            rows = [row for row in content["rows"] if row[field] == key]
            if not rows:
                continue
            mutate(rows[0])
            raw = encoded_json(content)
            part.update(bytes=len(raw), sha256=sha256(raw).hexdigest())
            rewrite_federation_member(products, part["path"], content)
            rewrite_federation_member(products, "index.json", index)
            return
    raise AssertionError("Fixture index row not found")


def rewrite_capture(products: dict[str, Any], digest: str, mutate: Any) -> str:
    """Rehash literal selected capture, capsule and federation metadata after mutation."""
    root = products["capsule"]
    directory = root / "captures" / digest
    document = json.loads((directory / "capture-manifest.json").read_bytes())
    control = json.loads((directory / "request-plan.json").read_bytes())
    mutate(document, control, directory)
    (directory / "request-plan.json").write_bytes(encoded_json(control))
    document["plan_sha256"] = pin(directory / "request-plan.json")
    (directory / "capture-manifest.json").write_bytes(encoded_json(document))
    capture_pin = pin(directory / "capture-manifest.json")
    directory.rename(root / "captures" / capture_pin)
    old_capsule = next(iter(products["kwargs"]["capsule_sources"]))

    def replace(value: Any, replacements: dict[str, str]) -> Any:
        if isinstance(value, str):
            for old, new in replacements.items():
                value = value.replace(old, new)
            return value
        if isinstance(value, list):
            return [replace(item, replacements) for item in value]
        if isinstance(value, dict):
            return {
                replace(key, replacements): replace(item, replacements)
                for key, item in value.items()
            }
        return value

    capsule = replace(
        json.loads((root / "manifest.json").read_bytes()), {digest: capture_pin}
    )
    for name in list(capsule["files"]):
        if name.endswith(".json") and not name.startswith("captures/"):
            path = root / name
            path.write_bytes(
                encoded_json(
                    replace(json.loads(path.read_bytes()), {digest: capture_pin})
                )
            )
    files = {
        path.relative_to(root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": pin(path),
        }
        for path in root.rglob("*")
        if path.is_file() and path != root / "manifest.json"
    }
    capsule["files"], capsule["source_bytes"] = (
        files,
        sum(row["bytes"] for row in files.values()),
    )
    capsule["captures"][capture_pin]["files"] = {
        path.name: files[path.relative_to(root).as_posix()]
        for path in (root / "captures" / capture_pin).iterdir()
    }
    (root / "manifest.json").write_bytes(encoded_json(capsule))
    capsule_pin = pin(root / "manifest.json")
    products["kwargs"]["capsule_sources"] = {capsule_pin: root}
    federation = products["directory"]
    replacements = {digest: capture_pin, old_capsule: capsule_pin}
    header = replace(
        json.loads((federation / "manifest.json").read_bytes()), replacements
    )
    header["capsule_manifest_sha256s"] = sorted(header["capsule_captures"])
    header["capsule_captures"] = {
        owner: sorted(captures)
        for owner, captures in header["capsule_captures"].items()
    }
    index = replace(json.loads((federation / "index.json").read_bytes()), replacements)
    for part in index["parts"]:
        old_path = part["path"].replace(capture_pin, digest)
        path = federation / old_path
        content = replace(json.loads(path.read_bytes()), replacements)
        raw = encoded_json(content)
        destination = federation / part["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        if destination != path:
            path.unlink()
        part.update(bytes=len(raw), sha256=sha256(raw).hexdigest())
        header["files"][part["path"]] = {key: part[key] for key in ("bytes", "sha256")}
    raw = encoded_json(index)
    (federation / "index.json").write_bytes(raw)
    header["files"]["index.json"] = {
        "bytes": len(raw),
        "sha256": sha256(raw).hexdigest(),
    }
    header["source_bytes"] = sum(row["bytes"] for row in header["files"].values())
    (federation / "manifest.json").write_bytes(encoded_json(header))
    products["kwargs"]["expected_manifest_sha256"] = pin(federation / "manifest.json")
    return capture_pin


def sync_observation(
    products: dict[str, Any], capture_pin: str, kind: str, offset: int = 0
) -> dict[str, Any]:
    directory = products["capsule"] / "captures" / capture_pin
    document = json.loads((directory / "capture-manifest.json").read_bytes())
    population = "resources" if kind == "linked" else "facets"
    entry = document[population][offset]
    identity = f"{capture_pin}:/{population}/{offset}"
    attempts = []
    for reference in entry["attempts"]:
        record = json.loads((directory / reference["receipt_file"]).read_bytes())
        attempts.append(
            {
                **reference,
                **(
                    {
                        "body_sha256": pin(directory / reference["body_file"]),
                        "body_bytes": (directory / reference["body_file"])
                        .stat()
                        .st_size,
                    }
                    if "body_file" in reference
                    else {}
                ),
                **{
                    key: record[key]
                    for key in (
                        "http_status",
                        "body_complete",
                        "terminal_status",
                        "utc_start",
                        "utc_end",
                        "tls_mode",
                        "requested_url",
                    )
                    if key in record
                },
            }
        )

    previous = []

    def mutate(row: dict[str, Any]) -> None:
        previous.append(row["terminal_status"])
        row["attempts"] = attempts
        row["terminal_status"] = entry["terminal_status"]

    rewrite_index_row(products, "observations", identity, mutate)
    if kind == "facet" and previous[0] != entry["terminal_status"]:

        def slot_status(slot: dict[str, Any]) -> None:
            counts = slot["source_terminal_counts"]
            counts[previous[0]] -= 1
            if counts[previous[0]] == 0:
                del counts[previous[0]]
            counts[entry["terminal_status"]] = (
                counts.get(entry["terminal_status"], 0) + 1
            )
            slot["coverage_status"] = (
                "complete_source_entity"
                if counts.get("received_complete_unqualified_facet", 0)
                else "recorded_without_complete_source_entity"
            )

        rewrite_index_row(products, "slots", entry["facet_key"], slot_status)
    return {"observation_id": identity, "entry": entry, "directory": directory}
