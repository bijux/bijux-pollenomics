"""Confine exact OpenLand member source replay and retained metadata input roles."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
PRIVATE = Path("/Users/bijan/bijux/-bijux-pollenomics-data")
OWNER = "source-relations/openland-intake/report-products"
PRODUCER = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/openland_intake.py"
REPORT = "docs/report/source-relations/openland-intake"
POLICY = "configs/ci/report-ownership.json"
MODULES = {
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
INPUTS = {
    "archive": (
        Path(
            "/Users/bijan/bijux/-bijux-pollenomics-data/openland/original/LandCover_OpenLand.zip"
        ),
        "7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b",
        204058381,
    ),
    "failed_intake": (
        Path(
            "/Users/bijan/bijux/-bijux-pollenomics-data/source-intakes/receipts/EXT-2026-09-04-OPENLAND-001.json"
        ),
        "da69bd9ecf4a07fa05cee7466adb8fb4ee9e7e338d30fa83c225bd1225dfd5c0",
        8580,
    ),
    "received_intake": (
        Path(
            "/Users/bijan/bijux/-bijux-pollenomics-data/source-intakes/receipts/EXT-2026-09-04-OPENLAND-002.json"
        ),
        "e5d3aa9016ba548e31abd69d3f5bf18d26a365bdd0ecc6e5d5070239e7dbda0a",
        15978,
    ),
    "doi_lineage": (
        Path(
            "/Users/bijan/bijux/bijux-pollenomics/docs/report/source-relations/openland-intake/doi-lineage.json"
        ),
        "52421cacb6bf4f0ec580e7f2d0f2665ab0e87a1184efff6b887247513e3afa27",
        1868,
    ),
    "members_csv": (
        Path(
            "/Users/bijan/bijux/bijux-pollenomics/docs/report/source-relations/openland-intake/members.csv"
        ),
        "9bd4f430895d3b0c76522e2f44e7e9d5a4613ece4cafbf5d632c3feafc42c9df",
        17044,
    ),
    "report": (
        Path(
            "/Users/bijan/bijux/bijux-pollenomics/docs/report/source-relations/openland-intake/report.json"
        ),
        "6ede25d42a64a041139aab7a32ed6abfb3e2fb19ec0caf932647b7377455e52b",
        3831,
    ),
    "upstream_tree": (
        Path(
            "/Users/bijan/bijux/bijux-pollenomics/docs/report/source-relations/openland-intake/upstream-tree.json"
        ),
        "4bbd8f7a11b6fc01083dab358143f01b8f06192c8562592758e451436f75eae1",
        9513,
    ),
}
PACKAGE_ROOTS = [
    ROOT / "packages" / name / "src"
    for name in (
        "bijux-pollenomics",
        "bijux-pollenomics-dev",
        "bijux-pollenomics-lra",
        "pollenomics",
    )
]


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_file()
        and path.is_absolute()
        and path == path.resolve()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical regular input required: " + str(path),
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def exact(a: Any, b: Any) -> bool:
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(
            (exact(x, y) for x, y in zip(a, b, strict=True))
        )
    return bool(a == b)


def load(path: Path) -> Any:

    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        require(len(rows) == len({k for k, _ in rows}), "Duplicate JSON key")
        return dict(rows)

    def constant(value: str) -> None:
        raise ValueError("Nonfinite JSON constant: " + value)

    return json.loads(
        path.read_bytes(), object_pairs_hook=pairs, parse_constant=constant
    )


def dump(path: Path, value: Any) -> None:
    require(
        not path.exists() and (not path.is_symlink()),
        "No receipt replacement: " + str(path),
    )
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False) + "\n")


def output_root(path: Path, *, absent: bool = False) -> Path:
    require(
        path.is_absolute()
        and path == path.resolve()
        and path.is_relative_to(ROOT / "artifacts")
        and (not any(p.is_symlink() for p in (path, *path.parents))),
        "Physical normalized artifact output required",
    )
    if absent:
        require(not path.exists() and (not path.is_symlink()), "Absent output required")
    return path


def namespace() -> None:
    for p in SOURCE.iterdir():
        require(
            not p.is_symlink() and (p.is_dir() or p.is_file()),
            "Alias/special controller entry",
        )
        require(
            not p.is_dir() or p.name == "preflight", "Unexpected controller directory"
        )
        if p.suffix in {".py", ".pyc", ".so"}:
            require(p.name in MODULES, "Unexpected importable controller")


def identity() -> dict[str, str]:

    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=ROOT)

    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def union(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for group in groups:
        for row in group:
            require(
                set(row) == {"path", "sha256", "bytes"} and type(row["bytes"]) is int,
                "Malformed expected pin",
            )
            name = row["path"]
            require(
                name not in rows or exact(rows[name], row),
                "Conflicting original input pin: " + name,
            )
            rows[name] = dict(row)
    return [rows[k] for k in sorted(rows)]


def first_party_snapshot() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from runtime_contracts import namespace_snapshot

    trees = []
    files: list[dict[str, Any]] = []
    for root in PACKAGE_ROOTS:
        tree = namespace_snapshot(root, [])
        require(
            all(v["kind"] != "symlink" for v in tree["entries"].values()),
            "First-party source alias is not declared",
        )
        trees.append(tree)
        files.extend(
            (
                pin(root / name)
                for name, v in tree["entries"].items()
                if v["kind"] == "file"
            )
        )
    return (trees, files)


def verify_inputs(plan: dict[str, Any]) -> None:
    from runtime_contracts import verify_absences, verify_base_namespaces, verify_pin

    namespace()
    for row in plan["input_pins"]:
        verify_pin(row)
    verify_base_namespaces(plan["first_party_namespaces"])
    verify_absences(plan["absent_input_paths"])


def csv_wire(rows: list[dict[str, object]], fields: tuple[str, ...]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def read_csv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == list(fields), "CSV field order changed")
        result = list(reader)
    require(
        all(set(x) == set(fields) and None not in x.values() for x in result),
        "Ragged CSV",
    )
    return result


def bridge_pair(
    old: bytes, current: bytes, producer: bytes, bridge: dict[str, Any]
) -> None:
    """Accept only the reviewed source attribution binding change and literal digests."""
    import ast

    require(
        hashlib.sha256(old).hexdigest() == bridge["recorded"]["sha256"]
        and len(old) == bridge["recorded"]["bytes"],
        "Recorded authority differs",
    )
    require(
        hashlib.sha256(current).hexdigest() == bridge["current"]["sha256"]
        and len(current) == bridge["current"]["bytes"],
        "Current authority differs",
    )
    trees = [ast.parse(raw) for raw in (old, current)]
    values = []
    for tree in trees:
        matches = [
            node
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(t, ast.Name) and t.id == "SOURCE_ATTRIBUTION"
                for t in node.targets
            )
        ]
        require(len(matches) == 1, "One literal attribution binding required")
        value = ast.literal_eval(matches[0].value)
        require(type(value) is str, "Literal source attribution required")
        values.append(value)
        tree.body.remove(matches[0])
    require(
        values
        == [
            "Behnaz Pirzamanbein; Pirzamanbein et al. (2022), doi:10.3389/fevo.2022.795794",
            "Behnaz Pirzamanbein (upstream data creator); Githumbi et al. (2022), doi:10.3389/fevo.2022.795794",
        ],
        "Reviewed attribution pair differs",
    )
    require(
        ast.dump(trees[0], include_attributes=False)
        == ast.dump(trees[1], include_attributes=False),
        "Authority executable/data change outside attribution",
    )
    require(
        not any(
            isinstance(node, ast.ImportFrom)
            and any(item.name == "SOURCE_ATTRIBUTION" for item in node.names)
            for node in ast.walk(ast.parse(producer))
        ),
        "Attribution binding unexpectedly consumed",
    )


def validate_source_bridge(bridge: dict[str, Any]) -> None:
    name = bridge["path"]
    require(
        name
        == "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/open_land/authority.py",
        "Closed authority path required",
    )
    old = subprocess.check_output(
        ["git", "show", bridge["historical_parent_expression"] + ":" + name],
        cwd=ROOT,
        timeout=30,
    )
    current = (ROOT / name).read_bytes()
    committed = subprocess.check_output(
        ["git", "show", "HEAD:" + name], cwd=ROOT, timeout=30
    )
    require(current == committed, "Current authority not current Git blob")
    bridge_pair(old, current, (ROOT / PRODUCER).read_bytes(), bridge)
