"""Exact named uncertainty ownership; original native execution stays immutable."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.index import (
    read_source_path,
    source_revision,
)
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
    read_blob,
)

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


_FIXED_BACKGROUND_COUNTING_SPANS: dict[str, tuple[bytes, ...]] = {
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py": (
        b"from bijux_pollenomics_lra.reconstruction.uncertainty.homogeneous_counting import (\n    HomogeneousCountingSet,\n    homogeneous_two_taxon_counting_set,\n)\n",
        b'            "lra.love.two-taxon.fixed-background-binomial-set",\n',
        b'    "HomogeneousCountingSet",\n    "homogeneous_two_taxon_counting_set",\n',
    ),
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py": (
        b"    HomogeneousCountingSet,\n",
        b"    homogeneous_two_taxon_counting_set,\n",
        b'    "HomogeneousCountingSet",\n    "homogeneous_two_taxon_counting_set",\n',
    ),
}


def fixed_background_counting_api_basis(name: str, current: bytes) -> bytes | None:
    """Invert only four counting bindings and their one advertised capability."""
    if name not in _FIXED_BACKGROUND_COUNTING_SPANS:
        return None
    body = current
    for inserted in _FIXED_BACKGROUND_COUNTING_SPANS[name]:
        if body.count(inserted) != 1:
            return None
        body = body.replace(inserted, b"", 1)
    return body


def counting_api_extension_matches(name: str, captured: bytes, current: bytes) -> bool:
    """Require every historical API byte after the exact named counting insertion."""
    basis = fixed_background_counting_api_basis(name, current)
    return basis is not None and basis == captured


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


def _api_preimage_bytes(repository: Path) -> bytes:
    """Read the exact original API without restoring an executable snapshot."""
    return read_blob(
        repository,
        GitSourceMember(
            PREIMAGE_PATH,
            API_PATH,
            source_revision(repository, "1d14065e277e0be39c4cafe6f163ad6f411f36f0"),
            "476bdee064d6f38f6920f338af721529254bf501",
            PREIMAGE_SHA256,
            6049,
        ),
    )


def validated_source_layout(repository: Path) -> dict[str, Any]:
    """Authenticate relocation and its exact bounded counting API addition."""
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
    preimage = _api_preimage_bytes(repository)
    current_api = _regular_confined_file(
        repository, API_PATH, "uncertainty current API"
    )
    api_before = current_api.stat()
    _require(0 < api_before.st_size <= 32768, "current API must be bounded")
    current_body = current_api.read_bytes()
    adopted_basis = fixed_background_counting_api_basis(API_PATH, current_body)
    if adopted_basis is None:
        adopted_basis = current_body
    _require(
        current_api.stat().st_nlink == 1
        and hashlib.sha256(preimage).hexdigest() == PREIMAGE_SHA256
        and hashlib.sha256(adopted_basis).hexdigest() == proof["adopted_api_sha256"],
        "API historical basis or physical identity differs",
    )
    _require(
        _imports_and_remaining(preimage, moved=False)
        == _imports_and_remaining(adopted_basis, moved=True),
        "original API AST differs beyond named ownership and counting exports",
    )
    stable_api = _regular_confined_file(repository, API_PATH, "uncertainty current API")
    api_after = stable_api.stat()
    stat_fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    _require(
        all(
            getattr(api_before, field) == getattr(api_after, field)
            for field in stat_fields
        )
        and api_after.st_nlink == 1
        and stable_api.read_bytes() == current_body,
        "current API changed during source correspondence",
    )
    return proof


def read_historical_api_preimage(repository: Path) -> bytes:
    """Read the fixed archived API for raw inventory, without current qualification."""
    path = _regular_confined_file(repository, PROOF_PATH, "historical API proof")
    before = path.stat()
    _require(
        before.st_nlink == 1 and 0 < before.st_size <= 32768,
        "historical API proof must be bounded and unaliased",
    )
    raw = path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == PROOF_SHA256, "proof digest differs")
    proof = json.loads(raw)
    _require(
        proof["schema_version"] == "lra-uncertainty-source-layout.v1"
        and proof["preimage_api"] == {"path": PREIMAGE_PATH, "sha256": PREIMAGE_SHA256}
        and proof["native_R_executed"] is False
        and proof["browser_executed"] is False
        and proof["scientific_admission"] is False,
        "historical API identity or admission scope differs",
    )
    physical = repository / PREIMAGE_PATH
    _require(
        not physical.exists() and not physical.is_symlink(),
        "historical API must remain in Git storage",
    )
    body = _api_preimage_bytes(repository)
    _require(
        len(body) == 6049 and hashlib.sha256(body).hexdigest() == PREIMAGE_SHA256,
        "historical API bytes differ",
    )
    stable = _regular_confined_file(repository, PROOF_PATH, "historical API proof")
    after = stable.stat()
    _require(
        all(
            getattr(before, field) == getattr(after, field)
            for field in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        )
        and after.st_nlink == 1
        and stable.read_bytes() == raw
        and not physical.exists()
        and not physical.is_symlink(),
        "historical API proof or storage changed during read",
    )
    return body


def api_adoption_preimage(repository: Path, current: Path) -> bytes:
    """Return original API bytes after proving exact named import ownership."""
    body = current.read_bytes()
    if hashlib.sha256(body).hexdigest() == PREIMAGE_SHA256:
        return body
    validated_source_layout(repository)
    return _api_preimage_bytes(repository)


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

    captured = read_source_path(
        repository, "data/atlas/source-view-capture/source/" + name
    )
    _require(
        hashlib.sha256(captured).hexdigest() == digest,
        "original protected API bytes differ",
    )
    if name == API_PATH:
        atlas_source_views._validate_api_adoption(repository, captured, current)
    elif name == ROOT_API_PATH:
        atlas_source_views._validate_root_api_adoption(repository, captured, current)
    else:
        _require(False, "current protected source differs")
