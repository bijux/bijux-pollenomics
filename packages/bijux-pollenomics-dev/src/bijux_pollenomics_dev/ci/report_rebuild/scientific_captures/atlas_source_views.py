"""Authenticate actual source-view browser observations before retained transport."""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from ..contracts import ReportRebuildError
from ..ownership import _regular_confined_file
from ..retained_source.index import validated_descriptor
from .presentation_source_roles import (
    HISTORICAL_RENDERING_SOURCES,
    atlas_extension_matches,
)

CAPTURE_PATH = "data/atlas/source-view-capture/capture.json"
CAPTURE_SHA256 = "bf5a62652a8b22734f15ac60584e2ab0f8ab8870d96a632307cfd40211daeddd"
SOURCE_CANDIDATE = "fa79ae6eff0f344b5a2dbff2cc858f92746c1f67"
HISTORICAL_PORTAL_READER_SOURCES = frozenset(
    (
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/markdown.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/narrative_quality.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/publication.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_accounts.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/scientific_qualifications.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/surfaces.py",
    )
)
API_PATH = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py"
API_ADOPTION_PATH = "configs/ci/report-capture-projections/atlas-source-view-api.json"
API_ADOPTION_SHA256 = "65ecb927d8d8220c76830d091a9d953dba5909e532535caed308ee74881c1c4e"
ROOT_API_PATH = "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py"
ROOT_API_ADOPTION_PATH = (
    "configs/ci/report-capture-projections/atlas-source-view-root-api.json"
)
ROOT_API_ADOPTION_SHA256 = (
    "ff0d3d8b14b522313aae5fb49d8a117950f8d8217fa4c0171686ad4d76c24c18"
)
OWNER_IDS = frozenset(
    {
        "atlas/frame-url-replay/browser-verification",
        "atlas/keyless-cache-matrix/candidate-identity",
        "atlas/keyless-cache-matrix/browser-receipt",
        "atlas/modeled-panel-browser/candidate-generation",
        "atlas/modeled-panel-browser/browser-evidence",
        "atlas/nordic-source/browser-evidence",
        "atlas/provider-accessibility/candidate-generation",
        "atlas/provider-accessibility/browser-evidence",
        "atlas/source-detail/browser-evidence",
        "atlas/source-export/browser-verification",
        "atlas/source-export/browser-downloads",
        "atlas/source-url-replay/browser-evidence",
    }
)
CASE_IDS = frozenset(
    {
        "frame-url-replay",
        "keyless-cache-matrix",
        "modeled-panel-browser",
        "nordic-source",
        "provider-accessibility",
        "source-detail",
        "source-export",
        "source-url-replay",
    }
)


def _require(condition: object, message: str) -> None:
    if not condition:
        raise ReportRebuildError("Atlas source capture: " + message)


def _relative(value: object) -> str:
    _require(isinstance(value, str) and value, "path is not text")
    if not isinstance(value, str):
        raise ReportRebuildError("Atlas source capture: path is not text")
    path = PurePosixPath(value)
    _require(
        bool(path.parts)
        and not path.is_absolute()
        and path.as_posix() == value
        and "\\" not in value
        and "\x00" not in value
        and all(part not in {".", ".."} for part in path.parts),
        "path is not confined",
    )
    return value


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for key, value in pairs:
        if key in values:
            raise ReportRebuildError("Atlas source capture: duplicate JSON key")
        values[key] = value
    return values


def _constant(value: str) -> None:
    raise ReportRebuildError("Atlas source capture: nonfinite JSON " + value)


def read_object(path: Path) -> dict[str, Any]:
    """Read original JSON without accepting duplicate keys or nonfinite constants."""
    try:
        value = json.loads(
            path.read_bytes(), object_pairs_hook=_pairs, parse_constant=_constant
        )
    except (ValueError, UnicodeError) as error:
        raise ReportRebuildError("Atlas source capture: malformed JSON") from error
    _require(isinstance(value, dict), "JSON root is not an object")
    if not isinstance(value, dict):
        raise ReportRebuildError("Atlas source capture: JSON root is not an object")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _api_without_adoptions(raw: bytes, proof: dict[str, Any]) -> str:
    """Remove only the reviewed added imports/exports/descriptor capabilities."""
    tree = ast.parse(raw)
    imports = proof["additional_imports"]
    exports = set(proof["additional_exports"])
    capabilities = set(proof["additional_capabilities"])
    removed_imports: set[str] = set()
    removed_exports: set[str] = set()
    removed_capabilities: set[str] = set()
    body = []
    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and node.module in imports
        ):
            _require(
                node.level == 0
                and [a.name for a in node.names] == imports[node.module]
                and all(a.asname is None for a in node.names)
                and node.module not in removed_imports,
                "added API import differs",
            )
            removed_imports.add(node.module)
            continue
        node = copy.deepcopy(node)
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
            and isinstance(node.value, ast.List)
        ):
            remaining = []
            for element in node.value.elts:
                if (
                    isinstance(element, ast.Constant)
                    and isinstance(element.value, str)
                    and element.value in exports
                ):
                    _require(
                        element.value not in removed_exports,
                        "duplicate added API export",
                    )
                    removed_exports.add(element.value)
                else:
                    remaining.append(element)
            node.value.elts = remaining
        if isinstance(node, ast.FunctionDef) and node.name == "extension_descriptor":
            for child in ast.walk(node):
                if not isinstance(child, ast.Dict):
                    continue
                for key, value in zip(child.keys, child.values, strict=True):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "capabilities"
                        and isinstance(value, ast.List)
                    ):
                        remaining = []
                        for element in value.elts:
                            if (
                                isinstance(element, ast.Constant)
                                and isinstance(element.value, str)
                                and element.value in capabilities
                            ):
                                _require(
                                    element.value not in removed_capabilities,
                                    "duplicate added API capability",
                                )
                                removed_capabilities.add(element.value)
                            else:
                                remaining.append(element)
                        value.elts = remaining
        body.append(node)
    _require(
        removed_imports == set(imports)
        and removed_exports == exports
        and removed_capabilities == capabilities,
        "named API additions are incomplete",
    )
    tree.body = body
    return ast.dump(tree, include_attributes=False)


def _validate_api_adoption(repository: Path, captured: bytes, current: Path) -> None:
    from bijux_pollenomics_dev.lra_validation.native_reference.source_layout_adoption import (
        api_adoption_preimage,
    )

    adopted = api_adoption_preimage(repository, current)
    proof_path = _regular_confined_file(
        repository, API_ADOPTION_PATH, "atlas source API adoption"
    )
    _require(
        _sha(proof_path) == API_ADOPTION_SHA256, "API adoption certificate differs"
    )
    proof = read_object(proof_path)
    _require(
        proof["schema_version"] == "atlas-captured-api-additive-adoption.v1"
        and proof["captured_source_candidate"] == SOURCE_CANDIDATE
        and proof["path"] == API_PATH
        and proof["captured_sha256"] == hashlib.sha256(captured).hexdigest()
        and proof["adopted_sha256"] == hashlib.sha256(adopted).hexdigest(),
        "API adoption source identity differs",
    )
    _require(
        _api_without_adoptions(adopted, proof)
        == ast.dump(ast.parse(captured), include_attributes=False),
        "original API semantics changed",
    )


def _root_api_without_adoptions(raw: bytes, proof: dict[str, Any]) -> str:
    """Remove only two reviewed interval aliases from the existing package API."""
    tree = ast.parse(raw)
    names = set(proof["additional_import_names"])
    exports = set(proof["additional_exports"])
    _require(
        names
        == exports
        == {"TwoTaxonCountingInterval", "fixed_two_taxon_counting_interval"},
        "root API named additions differ",
    )
    imported: set[str] = set()
    exported: set[str] = set()
    body = []
    for original in tree.body:
        node = copy.deepcopy(original)
        if isinstance(node, ast.ImportFrom) and node.module == "api":
            _require(node.level == 1, "root API import level differs")
            remaining = []
            for alias in node.names:
                if alias.name in names:
                    _require(
                        alias.asname is None and alias.name not in imported,
                        "root API added alias differs",
                    )
                    imported.add(alias.name)
                else:
                    remaining.append(alias)
            node.names = remaining
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "__all__"
            and isinstance(node.value, ast.List)
        ):
            remaining_exports = []
            for item in node.value.elts:
                if (
                    isinstance(item, ast.Constant)
                    and isinstance(item.value, str)
                    and item.value in exports
                ):
                    _require(item.value not in exported, "duplicate root API addition")
                    exported.add(item.value)
                else:
                    remaining_exports.append(item)
            node.value.elts = remaining_exports
        body.append(node)
    _require(
        imported == names and exported == exports, "root API additions are incomplete"
    )
    tree.body = body
    return ast.dump(tree, include_attributes=False)


def _validate_root_api_adoption(
    repository: Path, captured: bytes, current: Path
) -> None:
    from bijux_pollenomics_dev.lra_validation.native_reference.source_layout_adoption import (
        fixed_background_counting_api_basis,
    )

    checked = _regular_confined_file(repository, ROOT_API_PATH, "current root API")
    _require(current == checked, "root API path differs")
    initial = checked.stat()
    _require(
        initial.st_nlink == 1 and 0 < initial.st_size <= 32768,
        "root API must be bounded single-link",
    )
    current_body = checked.read_bytes()
    adopted = fixed_background_counting_api_basis(ROOT_API_PATH, current_body)
    if adopted is None:
        adopted = current_body
    proof_path = _regular_confined_file(
        repository, ROOT_API_ADOPTION_PATH, "atlas source root API adoption"
    )
    _require(
        _sha(proof_path) == ROOT_API_ADOPTION_SHA256,
        "root API adoption certificate differs",
    )
    proof = read_object(proof_path)
    _require(
        proof["schema_version"] == "atlas-captured-root-api-additive-adoption.v1"
        and proof["captured_source_candidate"] == SOURCE_CANDIDATE
        and proof["path"] == ROOT_API_PATH
        and proof["captured_sha256"] == hashlib.sha256(captured).hexdigest()
        and proof["adopted_sha256"] == hashlib.sha256(adopted).hexdigest(),
        "root API adoption source identity differs",
    )
    _require(
        _root_api_without_adoptions(adopted, proof)
        == ast.dump(ast.parse(captured), include_attributes=False),
        "original root API semantics changed",
    )
    again = _regular_confined_file(repository, ROOT_API_PATH, "current root API")
    final = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    _require(
        all(getattr(initial, field) == getattr(final, field) for field in fields)
        and again.read_bytes() == current_body,
        "root API changed during correspondence",
    )


@dataclass(frozen=True)
class ValidatedAtlasCapture:
    """An immutable packet with independently checked native execution lineage."""

    directory: Path
    document: dict[str, Any]
    members: dict[str, Path]


def validated_atlas_source_views(repository: Path) -> ValidatedAtlasCapture:
    """Admit a fixed native packet, never an arbitrary ownership role or receipt.

    Every captured source and verifier body authenticates the historical display.
    Six portal readers and six display sources remain historical Git witnesses;
    current presentation software is separately checked and is not asserted equal
    to those browser-epoch bodies.
    Retained transport admits no fresh source reproduction, browser execution,
    generator execution or extension of displayed scientific admission.
    """
    repository = repository.absolute()
    path = _regular_confined_file(repository, CAPTURE_PATH, "atlas capture")
    _require(_sha(path) == CAPTURE_SHA256, "certificate digest differs")
    packet = read_object(path)
    _require(
        packet["schema_version"] == "atlas-source-view-native-capture.v1"
        and packet["source_candidate"] == SOURCE_CANDIDATE
        and packet["scientific_admission"] is False
        and packet["numerical_execution"] is False
        and packet["browser"] == "Chrome/155.0.8059.40",
        "capture identity or admission differs",
    )
    directory = path.parent
    catalogue = {
        _relative(row["path"]): {"sha256": row["sha256"], "bytes": row["bytes"]}
        for row in packet["files"]
    }
    _require(len(catalogue) == len(packet["files"]), "duplicate logical member")
    source_buffer = validated_descriptor(
        repository, directory.relative_to(repository).as_posix(), catalogue
    )
    source_buffer.validate()
    generated_member = (
        "source/packages/bijux-pollenomics-lra/src/"
        "bijux_pollenomics_lra/_build_version.py"
    )
    _require(
        {row["member"] for row in source_buffer.descriptor.generated}
        == {generated_member},
        "named generated source metadata differs",
    )
    members = {
        name: directory / name
        for name in catalogue
        if name not in source_buffer.detached
    }
    _require(
        set(packet["source_members"]) == set(packet["source_footprint"]),
        "captured source coverage differs",
    )
    for name, expected in packet["source_footprint"].items():
        logical_member = _relative(packet["source_members"][name])
        captured = source_buffer.read_source(logical_member)
        _require(
            hashlib.sha256(captured).hexdigest() == expected,
            "captured source bytes differ: " + name,
        )
        if logical_member == generated_member:
            # This authenticates recorded metadata, not the current version generator.
            continue
        from bijux_pollenomics_dev.lra_validation.native_reference.source_layout_adoption import (
            captured_source_path,
        )

        source = captured_source_path(repository, _relative(name))
        if name in HISTORICAL_PORTAL_READER_SOURCES | HISTORICAL_RENDERING_SOURCES:
            _require(
                logical_member == "source/" + name
                and logical_member in source_buffer.detached
                and source.stat().st_nlink == 1,
                "historical presentation storage role differs: " + name,
            )
            continue
        if _sha(source) != expected:
            if (
                logical_member == "source/" + name
                and logical_member in source_buffer.detached
                and source.stat().st_nlink == 1
                and atlas_extension_matches(name, captured, source.read_bytes())
            ):
                continue
            if name == API_PATH:
                _validate_api_adoption(repository, captured, source)
            elif name == ROOT_API_PATH:
                _validate_root_api_adoption(repository, captured, source)
            else:
                _require(False, "source footprint differs: " + name)
    for name, expected in packet["verifier_sources"].items():
        source = _regular_confined_file(
            repository, _relative(name), "atlas verifier source"
        )
        _require(_sha(source) == expected, "verifier source footprint differs: " + name)
    _require(
        {row["id"] for row in packet["generator_executions"]}
        == {
            "generate-source-details",
            "generate-Nordic-source-contexts",
            "generate-modeled-panels",
            "generate-context-frames",
        }
        and len(packet["generator_executions"]) == 4,
        "generator coverage differs",
    )
    for execution in packet["generator_executions"]:
        _require(
            type(execution["native_exit"]) is int
            and execution["native_exit"] == 0
            and execution["timeout"] is False,
            "candidate generator did not pass",
        )
    cases: set[str] = set()
    generations = packet["generations"]
    _require(len(generations) == 4, "candidate generation coverage differs")
    for member in generations.values():
        generation = read_object(members[_relative(member)])
        _require(
            all(
                packet["source_footprint"].get(name) == digest
                for name, digest in generation["inputs_sha256"].items()
            ),
            "generation source footprint differs",
        )
    review = read_object(members[packet["independent_review"]["member"]])
    _require(
        review["candidate"] == SOURCE_CANDIDATE
        and review["counts"]["successful_probes"] == 8
        and review["counts"]["served_file_digests_checked"] == 134
        and review["counts"]["download_or_screenshot_hashes_checked"] == 88
        and review["counts"]["source_table_full_equalities"] == 90
        and review["counts"]["live_DOM_negative_refusals"] == 4
        and review["counts"]["visually_inspected_PNGs"] == 8,
        "independent native source review differs",
    )
    for case in packet["cases"]:
        case_id = case["case_id"]
        _require(case_id in CASE_IDS and case_id not in cases, "case coverage differs")
        cases.add(case_id)
        receipt = read_object(members[_relative(case["receipt"])])
        _require(case["generation"] in generations.values(), "case generation differs")
        execution = case["native_execution"]
        _require(
            case["source_candidate"] == SOURCE_CANDIDATE
            and type(execution["native_exit"]) is int
            and execution["native_exit"] == 0
            and execution["timeout"] is False
            and receipt["status"] == "PASS"
            and receipt["runtime_errors"] == []
            and receipt["browser"]["product"] == packet["browser"],
            "native browser execution did not pass",
        )
        for key in ("candidate_generation_sha256", "generation_sha256"):
            if key in receipt:
                _require(
                    receipt[key] == _sha(members[case["generation"]]),
                    "browser generation digest differs",
                )
        if "scientific_admission" in receipt:
            _require(
                receipt["scientific_admission"] is False,
                "browser scientific admission differs",
            )
        verifier = Path(execution["actual_argv"][1]).name
        verifier_path = (
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/"
            "atlas_browser/" + verifier
        )
        _require(
            packet["verifier_sources"].get(verifier_path) == receipt["verifier_sha256"],
            "native verifier identity differs",
        )
        served = receipt.get("served_files_sha256", receipt.get("served_files"))
        if not isinstance(served, dict):
            raise ReportRebuildError(
                "Atlas source capture: served inventory is not an object"
            )
        _require(set(served) == set(case["served_files"]), "served coverage differs")
        for name, digest in served.items():
            _relative(name)
            digest = digest["sha256"] if isinstance(digest, dict) else digest
            member = members[_relative(case["served_files"][name])]
            _require(_sha(member) == digest, "actual served bytes differ")
    _require(cases == CASE_IDS, "browser observations are incomplete")
    products: set[str] = set()
    owners: set[str] = set()
    for product in packet["products"]:
        _require(product["owner_id"] in OWNER_IDS, "unknown governed owner")
        owners.add(product["owner_id"])
        name = _relative(product["output_path"])
        _require(name not in products and name.startswith("atlas/"), "product overlaps")
        products.add(name)
        operation = product["operation"]
        _require(
            operation
            in {"copy", "keyless-identity", "provider-review", "modeled-review"},
            "unknown retained projection",
        )
        if operation == "copy":
            _require(
                _relative(product["source"]) in members, "product source is absent"
            )
    _require(
        frozenset(owners) == OWNER_IDS and len(products) == 43,
        "product coverage differs",
    )
    _require(
        packet["preceding_failures"]["original_aggregate_native_exit"] == 1
        and packet["preceding_failures"]["successful_original_observations"] == 6
        and packet["preceding_failures"]["successful_successor_observations"] == 2,
        "native failure history differs",
    )
    source_buffer.fresh()
    return ValidatedAtlasCapture(directory, packet, members)
