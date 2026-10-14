"""Exact named uncertainty ownership; original native execution stays immutable."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file

PROOF_PATH = "configs/ci/report-capture-projections/lra-uncertainty-source-layout.json"
PROOF_SHA256 = "8f6d5e31f612b140b8bebec47419fb529f2aebc7bacddbe034845fd9cd0a54ef"
API_PATH = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py"
ROOT_API_PATH = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py"
PREIMAGE_PATH = "data/source-custody/lra-uncertainty-layout/api-before-relocation.py"
PREIMAGE_SHA256 = "6c3359cba2d080f0e5f97dd231f5732389cca1adbfec3cc303b38e90cbec0e3b"
SOURCE_PREFIX = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/"
)
MODULE_PREFIX = "bijux_pollenomics_lra.reconstruction."
NAMES = ("joint_aliquot_covariance", "two_taxon_counting", "joint_site_draws")
RELOCATIONS = {
    SOURCE_PREFIX + name + ".py": SOURCE_PREFIX + "uncertainty/" + name + ".py"
    for name in NAMES
}
MODULES = {
    MODULE_PREFIX + name: MODULE_PREFIX + "uncertainty." + name for name in NAMES
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ReportRebuildError("Uncertainty source layout: " + message)


def _imports_and_remaining(raw: bytes, *, moved: bool) -> tuple[dict[str, str], str]:
    """Compare only three exact renamed imports; retain all other ordered AST."""
    tree = ast.parse(raw)
    expected = (
        {target: original for original, target in MODULES.items()}
        if moved
        else {name: name for name in MODULES}
    )
    imports = {}
    remaining = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in expected:
            original = expected[node.module]
            _require(
                node.level == 0 and original not in imports,
                "duplicate or relative relocated import",
            )
            _require(
                all(alias.asname is None for alias in node.names),
                "relocated import alias differs",
            )
            node.module = original
            imports[original] = ast.dump(node, include_attributes=False)
        else:
            remaining.append(node)
    _require(set(imports) == set(MODULES), "named API relocation is incomplete")
    tree.body = remaining
    return imports, ast.dump(tree, include_attributes=False)


def validated_source_layout(repository: Path) -> dict[str, Any]:
    """Require the fixed proof and every physical byte before path projection."""
    path = _regular_confined_file(repository, PROOF_PATH, "uncertainty source proof")
    _require(
        path.stat().st_nlink == 1 and _sha(path) == PROOF_SHA256,
        "certificate digest or physical alias differs",
    )
    proof: dict[str, Any] = json.loads(path.read_bytes())
    _require(
        proof["schema_version"] == "lra-uncertainty-source-layout.v1"
        and proof["native_R_executed"] is False
        and proof["browser_executed"] is False
        and proof["scientific_admission"] is False,
        "admission identity differs",
    )
    _require(
        proof["preimage_api"] == {"path": PREIMAGE_PATH, "sha256": PREIMAGE_SHA256}
        and proof["module_names"] == MODULES,
        "named source mapping differs",
    )
    rows = proof["module_relocations"]
    _require(
        len(rows) == 3 and {row["before"]: row["after"] for row in rows} == RELOCATIONS,
        "three source relocations required",
    )
    for row in rows:
        _require(
            not (repository / row["before"]).exists()
            and not (repository / row["before"]).is_symlink(),
            "old operation path remains",
        )
        current = _regular_confined_file(
            repository, row["after"], "uncertainty operation source"
        )
        _require(
            current.stat().st_nlink == 1 and _sha(current) == row["sha256"],
            "operation source bytes or physical alias differ",
        )
    preimage = _regular_confined_file(
        repository, PREIMAGE_PATH, "uncertainty API preimage"
    )
    current_api = _regular_confined_file(
        repository, API_PATH, "uncertainty current API"
    )
    _require(
        preimage.stat().st_nlink == 1
        and current_api.stat().st_nlink == 1
        and _sha(preimage) == PREIMAGE_SHA256
        and _sha(current_api) == proof["adopted_api_sha256"],
        "API physical identity differs",
    )
    _require(
        _imports_and_remaining(preimage.read_bytes(), moved=False)
        == _imports_and_remaining(current_api.read_bytes(), moved=True),
        "original API AST differs beyond named import ownership",
    )
    return proof


def api_adoption_preimage(repository: Path, current: Path) -> Path:
    """Return reviewed preimage bytes only after proving current import ownership."""
    if _sha(current) == PREIMAGE_SHA256:
        return current
    validated_source_layout(repository)
    return _regular_confined_file(repository, PREIMAGE_PATH, "uncertainty API preimage")


def captured_source_path(repository: Path, name: str) -> Path:
    """Map the one captured operation path after complete three-module custody."""
    if name in RELOCATIONS:
        validated_source_layout(repository)
        return _regular_confined_file(
            repository, RELOCATIONS[name], "uncertainty captured source"
        )
    return _regular_confined_file(repository, name, "unchanged captured source")


def validate_current_native_source(repository: Path, name: str, digest: str) -> None:
    """Admit exact bytes or named API/path custody; never claim fresh native R."""
    from .annulus_capture import _file

    current = captured_source_path(repository, name)
    current_bytes = _file(repository, current.relative_to(repository).as_posix())
    if hashlib.sha256(current_bytes).hexdigest() == digest:
        return
    _require(name in {API_PATH, ROOT_API_PATH}, "current protected source differs")
    from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
        atlas_source_views,
    )

    captured = _regular_confined_file(
        repository,
        "data/atlas/source-view-capture/source/" + name,
        "original native API bytes",
    )
    _require(
        hashlib.sha256(
            _file(repository, captured.relative_to(repository).as_posix())
        ).hexdigest()
        == digest,
        "original protected API bytes differ",
    )
    if name == API_PATH:
        atlas_source_views._validate_api_adoption(repository, captured, current)
    elif name == ROOT_API_PATH:
        atlas_source_views._validate_root_api_adoption(repository, captured, current)
    else:
        _require(False, "current protected source differs")
