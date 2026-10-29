"""Retain source-bound fixture construction and experiment read-order evidence."""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterator
from contextlib import contextmanager
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
from typing import Any, cast

Json = dict[str, Any]


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def write(path: Path, value: object) -> None:
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def pin(path: Path) -> Json:
    value = path.read_bytes()
    return {
        "path": str(path),
        "sha256": hashlib.sha256(value).hexdigest(),
        "bytes": len(value),
    }


def checked(root: Path, row: Json) -> Path:
    path = root / str(row["path"])
    if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
        raise ValueError("Source must be a regular single-link file")
    value = path.read_bytes()
    if len(value) != row["bytes"] or hashlib.sha256(value).hexdigest() != row["sha256"]:
        raise ValueError("Source bytes differ from frozen protocol")
    return path


def fixture(root: Path, source: Path) -> Json:
    """Execute the two exact maintained fixture functions without importing pytest."""
    tree = ast.parse(source.read_text())
    selected = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"store", "fixture_inputs"}
    ]
    if {node.name for node in selected} != {"store", "fixture_inputs"} or len(
        selected
    ) != 2:
        raise ValueError("Exact maintained fixture functions required")
    namespace: Json = {
        "hashlib": hashlib,
        "json": json,
        "math": math,
        "Path": Path,
        "Any": Any,
    }
    exec(
        compile(
            ast.Module(list[ast.stmt](selected), type_ignores=[]), str(source), "exec"
        ),
        namespace,
    )
    return cast(Json, namespace["fixture_inputs"](root))


class Journal:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.rows: list[Json] = []
        self.lane = "unassigned"
        self.variant = "unassigned"

    def record(self, kind: str, **values: Any) -> None:
        row = {
            "index": len(self.rows),
            "lane": self.lane,
            "variant": self.variant,
            "kind": kind,
            **values,
        }
        with self.path.open("a") as stream:
            stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.rows.append(row)


@contextmanager
def instrument(journal: Journal) -> Iterator[None]:
    """Observe unchanged call results and restore every binding even on failure."""
    base = "bijux_pollenomics.analysis.lra_validation.experiments."
    persistence = importlib.import_module(base + "split_authority.persistence")
    reconstruction = importlib.import_module(base + "reconstruction")
    model = importlib.import_module(base + "fitted.model")
    scoring = importlib.import_module(base + "scoring")
    paired = importlib.import_module("bijux_pollenomics_lra.workflows.paired")
    originals: list[tuple[Any, str, Callable[..., Any]]] = []

    def attach(module: Any, name: str, builder: Callable[..., Any]) -> None:
        original = getattr(module, name)
        originals.append((module, name, original))
        setattr(module, name, builder(original))

    def verified(original: Callable[..., Any]) -> Callable[..., Any]:
        def call(authority: Any) -> Any:
            result = original(authority)
            journal.record(
                "split_verified",
                directory=str(authority.directory),
                folds_sha256=authority.folds_sha256,
            )
            return result

        return call

    def batch(original: Callable[..., Any]) -> Callable[..., Any]:
        def call(items: Any, **kwargs: Any) -> Any:
            requests = [
                {
                    "item_id": item.item_id,
                    "request_sha256": item.request_sha256,
                    "payload": item.payload(),
                }
                for item in items
            ]
            journal.record("batch_before", requests=requests)
            result = original(items, **kwargs)
            journal.record("batch_completed", result=result.as_dict())
            return result

        return call

    def reconstructed(original: Callable[..., Any]) -> Callable[..., Any]:
        def call(spec: Any, fold: Any, groups: Any, **kwargs: Any) -> Any:
            journal.record("reconstruction_before", fold=fold.as_dict())
            result = original(spec, fold, groups, **kwargs)
            journal.record(
                "reconstruction_completed",
                fold=fold.as_dict(),
                compositions=result.compositions,
                regional_cover=result.regional_cover,
                fit_identities=result.fit_identities,
            )
            return result

        return call

    def fit(original: Callable[..., Any]) -> Callable[..., Any]:
        def call(*args: Any, **kwargs: Any) -> Any:
            journal.record(
                "spatial_fit_before",
                fold=args[0].as_dict(),
                compositions=args[1],
                coordinates={k: v.as_dict() for k, v in args[2].items()},
            )
            result = original(*args, **kwargs)
            journal.record(
                "spatial_fit_completed",
                model_sha256=result.model_sha256,
                fit_manifest=json.loads(result.fit_manifest_json),
            )
            return result

        return call

    def read(original: Callable[..., Any]) -> Callable[..., Any]:
        def call(root: Path, reference: Any) -> Any:
            journal.record(
                "outcome_open",
                reference={"path": reference.path, "sha256": reference.sha256},
            )
            return original(root, reference)

        return call

    def engine(name: str) -> Callable[..., Any]:
        def builder(original: Callable[..., Any]) -> Callable[..., Any]:
            def call(*args: Any, **kwargs: Any) -> Any:
                journal.record("engine_before", operation=name)
                result = original(*args, **kwargs)
                journal.record("engine_completed", operation=name)
                return result

            return call

        return builder

    try:
        attach(persistence.PrefitSplitAuthority, "verify", verified)
        attach(reconstruction, "run_lra_batch", batch)
        attach(
            importlib.import_module(base + "workflow"),
            "reconstruct_fold",
            reconstructed,
        )
        attach(
            importlib.import_module(base + "fitted.workflow"),
            "reconstruct_fold",
            reconstructed,
        )
        attach(model, "fit_spatial_model", fit)
        attach(scoring, "read_reference", read)
        attach(paired, "run_reveals", engine("REVEALS"))
        attach(paired, "run_love", engine("LOVE-analytical"))
        yield
    finally:
        for module, name, original in reversed(originals):
            setattr(module, name, original)


def seed_buffers(repository: Path, declaration: Json) -> dict[str, bytes]:
    """Authenticate the exact finite scientific seed before any new API invocation."""
    source = repository / declaration["cache_root"]
    if (
        source.is_symlink()
        or not source.is_dir()
        or any(p.is_symlink() for p in source.parents)
    ):
        raise ValueError("Regular original scientific cache required")
    rows = declaration["files"]
    if len(rows) != 115 or len({row["relative"] for row in rows}) != 115:
        raise ValueError("Exact115 seed members required")
    expected = {row["relative"] for row in rows}
    expected_dirs = {
        str(parent)
        for name in expected
        for parent in Path(name).parents
        if str(parent) != "."
    }
    entries = list(source.rglob("*"))
    if (
        len(entries) > 256
        or {p.relative_to(source).as_posix() for p in entries}
        != expected | expected_dirs
    ):
        raise ValueError("Exact saved cache namespace required")
    for entry in entries:
        if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
            raise ValueError("Linked or special seed member")
    buffers: dict[str, bytes] = {}
    for row in rows:
        name = row["relative"]
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Scoped seed member required")
        path = source / name
        if path.stat().st_nlink != 1:
            raise ValueError("Single-link seed member required")
        body = path.read_bytes()
        if (
            len(body) != row["bytes"]
            or hashlib.sha256(body).hexdigest() != row["sha256"]
        ):
            raise ValueError("Saved seed bytes differ")
        buffers[name] = body
    if sum(map(len, buffers.values())) != 195665:
        raise ValueError("Saved seed byte denominator differs")
    products = declaration["products"]
    if len(products) != 5 or {name.split("/")[0] for name in expected} != {
        row["cache_key"] for row in products
    }:
        raise ValueError("Five original cache products required")
    for row in products:
        request = json.loads(buffers[row["cache_key"] + "/request.json"])
        manifest = json.loads(buffers[row["cache_key"] + "/manifest.json"])
        if (
            digest(request) != row["request_sha256"]
            or manifest["request_sha256"] != row["request_sha256"]
        ):
            raise ValueError("Saved request identity differs")
        if (
            hashlib.sha256(buffers[row["cache_key"] + "/manifest.json"]).hexdigest()
            != row["manifest_sha256"]
        ):
            raise ValueError("Saved product manifest differs")
    return buffers


def seed_cache(repository: Path, destination: Path, declaration: Json) -> Json:
    """Copy authenticated scientific outputs only, preserving original failure."""
    from bijux_pollenomics.analysis.lra.outputs.reading import read_lra_product

    for row in declaration["authority"].values():
        checked(repository, row)
    terminal = json.loads(
        (repository / declaration["authority"]["terminal"]["path"]).read_bytes()
    )
    if (
        terminal["actual_exit"] != 1
        or terminal["plan_sha256"] != declaration["authority"]["plan"]["sha256"]
        or terminal["candidate"] != declaration["candidate"]
        or terminal["source_pins_before_mismatches"]
        or terminal["source_pins_after_mismatches"]
    ):
        raise ValueError("Original failed native/source authority differs")
    buffers = seed_buffers(repository, declaration)
    source = repository / declaration["cache_root"]
    for row in declaration["products"]:
        verified = read_lra_product(
            source / row["cache_key"], expected_manifest_sha256=row["manifest_sha256"]
        )
        if verified.manifest()["request_sha256"] != row["request_sha256"]:
            raise ValueError("Verified seed request differs")
    if seed_buffers(repository, declaration) != buffers or destination.exists():
        raise ValueError("Changed source seed or existing destination")
    destination.mkdir()
    for name, body in buffers.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(body)
    return {
        "original_native_exit": 1,
        "original_candidate": declaration["candidate"],
        "original_plan": declaration["authority"]["plan"],
        "original_terminal": declaration["authority"]["terminal"],
        "seeded_products": 5,
        "seeded_files": 115,
        "seeded_bytes": 195665,
        "new_model_calls_during_seed": 0,
        "request_sha256s": sorted(
            row["request_sha256"] for row in declaration["products"]
        ),
    }
