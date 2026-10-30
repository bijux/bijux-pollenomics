"""Admit the executed Linux R source epoch while retaining historical refusal."""

from __future__ import annotations

import ast
from collections.abc import Callable
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError, canonical_json_sha256
from ..ownership import ReportOwnershipError, _regular_confined_file
from ..retained_source.descriptor import normalize_members
from ..retained_source.generated import reconstruct
from ..retained_source.index import SourceCapsule, validated_descriptor
from .source_correspondence import validated_current_scientific_source

OWNER = "method-certification/linux-r-oracle/report-products"
FAMILY = "docs/report/method-certification/linux-r-oracle/"
CAPTURE = "data/method-certification/linux-r-source-capture/capture.json"
CAPTURE_SHA256 = "fa6e9a4fa9c12013a04cc461fef52d0fd54044d517e132e802a9c176def2a913"
SOURCE_CANDIDATE = "6d8f1c5beffc2627b14e3330f8567e60f0fc8c36"
VERSION_SOURCE = (
    "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
)
VERSION_MEMBER = "source/" + VERSION_SOURCE
VERSION_SHA256 = "84040f998392398c91779befcbac6807d107b3d1c62a57e4b440dbf1fcc680c5"
VERSION_BYTES = 539


def _file(repository: Path, name: str, label: str) -> Path:
    try:
        return _regular_confined_file(repository, name, label)
    except (ReportOwnershipError, OSError) as error:
        raise ReportRebuildError(
            "Linux retained file is missing, linked or unconfined"
        ) from error


def _object(value: object, reason: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(k, str) for k in value):
        raise ReportRebuildError(reason)
    return value


def _json(path: Path) -> dict[str, Any]:
    try:
        return _object(json.loads(path.read_bytes()), "Linux capture must be an object")
    except (OSError, ValueError) as error:
        raise ReportRebuildError("Linux capture JSON is invalid") from error


def _zero(value: object) -> bool:
    return type(value) is int and value == 0


def _native_references(
    packet: Path, capture: JsonObject, read_member: Callable[[str], bytes]
) -> None:
    references = capture.get("execution_references")
    expected = {
        "plan": "execution/plan.json",
        "common_terminal": "execution/terminal.json",
        "outer_terminal": "execution/linux-source-terminal.json",
        "independent_numerical_review": "execution/independent-review.json",
        "source_reference": "execution/source-reference.json",
    }
    if references != expected:
        raise ReportRebuildError("Linux execution reference membership differs")
    plan, common, outer, review, source = (
        _json(packet / expected[name]) for name in expected
    )
    if (
        capture.get("schema_version") != "retained-linux-r-source-capture.v1"
        or capture.get("source_candidate") != SOURCE_CANDIDATE
        or any(
            item.get("candidate") != SOURCE_CANDIDATE
            for item in (plan, common, outer, review)
        )
        or source.get("base_candidate") != SOURCE_CANDIDATE
        or common.get("plan_sha256")
        != hashlib.sha256((packet / expected["plan"]).read_bytes()).hexdigest()
        or outer.get("registered_plan_sha256") != common.get("plan_sha256")
        or not all(
            _zero(value)
            for value in (
                common.get("actual_exit"),
                outer.get("actual_exit"),
                outer.get("common_actual_exit"),
            )
        )
        or outer.get("all_protected_inputs_unchanged") is not True
        or outer.get("memory_bound_passed") is not True
        or outer.get("storage_bound_passed") is not True
        or common.get("canonical_before") != common.get("canonical_after")
        or common.get("canonical_before") != plan.get("canonical_identity")
        or common.get("before_pin_mismatches") != []
        or common.get("after_pin_mismatches") != []
        or review.get("core_cases") != 43
        or review.get("source_domain_cases") != 23
        or review.get("all_complete_source_runtime_output_joins_passed") is not True
        or review.get("release_certificate") is not False
    ):
        raise ReportRebuildError("Linux execution epoch or native evidence differs")
    stages, intended = common.get("stages"), plan.get("stages")
    if (
        not isinstance(stages, list)
        or not isinstance(intended, list)
        or len(stages) != len(intended)
        or len(stages) != 2
    ):
        raise ReportRebuildError("Linux execution must retain both native stages")
    for actual_raw, intended_raw in zip(stages, intended, strict=True):
        actual = _object(actual_raw, "Linux native stage malformed")
        declared = _object(intended_raw, "Linux intended stage malformed")
        if (
            not _zero(actual.get("actual_exit"))
            or actual.get("timed_out") is not False
            or actual.get("argv") != declared.get("argv")
        ):
            raise ReportRebuildError("Linux native stage did not pass exactly")
    comparisons = review.get("independent_comparisons")
    source_files = source.get("source_files")
    if (
        not isinstance(comparisons, list)
        or len(comparisons) != 66
        or not isinstance(source_files, dict)
        or len(source_files) != 2148
    ):
        raise ReportRebuildError("Linux independent/source membership differs")
    for name, digest in source_files.items():
        if (
            not isinstance(name, str)
            or PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or not isinstance(digest, str)
            or hashlib.sha256(read_member("source/" + name)).hexdigest() != digest
        ):
            raise ReportRebuildError("Linux executed source bytes differ")


_HISTORICAL_READER_IDENTITIES = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/diagnostics.py": (
        "ca844dca8751054f17055c99c227c8a54084981da745e8c13e3071d2093e911e",
        12514,
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/diagnostics_verification.py": (
        "c8abeb8902e199073e61e9860535605c17c9d882205729562bc058d9a01c51bd",
        15067,
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/finite_covariance_capture.py": (
        "59b4770fbf38efe60633b540edf5925d09be56fe1c1c2795d6cf0af206edefee",
        9194,
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/source_layout_adoption.py": (
        "f0c340faca10b48ec3b9036659ffec26e37bc36719605a98eea7acec2e404272",
        7080,
    ),
}
_DOCUMENTED_NUMERIC_DEFINITIONS = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/two_taxon_counting.py": [
        "main"
    ],
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/two_taxon_counting_verification.py": [
        "binomial_cdf",
        "binomial_probabilities",
        "bounds",
        "main",
        "transform",
    ],
}


def _named_documentation_insertions(
    historical: bytes, current: bytes, names: list[str]
) -> bool:
    """Permit only the declared literal doc insertions, with every other byte exact."""
    try:
        old_text, current_text = historical.decode("utf-8"), current.decode("utf-8")
        old_tree, current_tree = ast.parse(old_text), ast.parse(current_text)
    except (SyntaxError, UnicodeError, RecursionError):
        return False
    removed: set[int] = set()
    for name in names:
        before = [
            node
            for node in old_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        after = [
            node
            for node in current_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ]
        if len(before) != 1 or len(after) != 1:
            return False
        if ast.get_docstring(
            before[0], clean=False
        ) is not None or not ast.get_docstring(after[0], clean=False):
            return False
        statement = after[0].body[0]
        if (
            not isinstance(statement, ast.Expr)
            or not isinstance(statement.value, ast.Constant)
            or type(statement.value.value) is not str
            or statement.end_lineno is None
        ):
            return False
        removed.update(range(statement.lineno - 1, statement.end_lineno))
        after[0].body = after[0].body[1:]
    if ast.dump(old_tree, include_attributes=False) != ast.dump(
        current_tree, include_attributes=False
    ):
        return False
    unchanged = "".join(
        line
        for i, line in enumerate(current_text.splitlines(keepends=True))
        if i not in removed
    )
    return unchanged.encode("utf-8") == historical


_NATIVE_REFERENCE_TRANSPORT_IDENTITIES = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/annulus_capture.py": (
        "47af109200a23537843078d241628273f08270e30150c34e1bbfdf76ffd0603b",
        10937,
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/capture.py": (
        "873b8a968223ca88f8235f999ad803d7f0b66c36dc503850e69478a23506849b",
        6846,
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/count_domain_capture.py": (
        "256ba71ff27976534da4b4c7a5fc496270a4e59c9a2af5100f078cccff8cc761",
        23947,
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/retained_reference/identity.py": (
        "bab7252e9e0b8059a58aa486555163b1cbde321bf1b870da719b23a3253f44bf",
        4875,
    ),
}


def _require_scientific_projection(
    repository: Path,
    name: str,
    identity: dict[str, Any],
    historical: bytes,
    *,
    source_buffer: SourceCapsule | None = None,
) -> JsonObject | None:
    """Keep ordinary sources strict and six reviewed reader/documentation roles explicit."""
    expected = identity.get("sha256"), identity.get("bytes")
    if (
        type(expected[1]) is not int
        or len(historical) != expected[1]
        or hashlib.sha256(historical).hexdigest() != expected[0]
    ):
        raise ReportRebuildError("Linux original source projection differs")
    current = _file(repository, name, "Linux current scientific source")
    if current.stat().st_nlink != 1 or current.stat().st_size > max(
        expected[1], 128 * 1024
    ):
        raise ReportRebuildError(
            "Linux current scientific source is linked or unbounded"
        )
    body = current.read_bytes()
    actual = hashlib.sha256(body).hexdigest(), len(body)
    if actual == expected:
        return None
    transport = _NATIVE_REFERENCE_TRANSPORT_IDENTITIES.get(name)
    if transport is not None:
        logical = "source/" + name
        if (
            expected != tuple(transport)
            or source_buffer is None
            or logical not in source_buffer.detached
            or source_buffer.read_source(logical) != historical
        ):
            raise ReportRebuildError(
                "Linux fixed native transport source identity differs"
            )
        role = validated_current_scientific_source(
            repository,
            {"path": name, "sha256": expected[0], "bytes": expected[1]},
            logical,
            source_buffer,
        )
        if (
            role is None
            or role.get("path") != name
            or role.get("classification")
            != "finite_native_reference_transport_extension"
        ):
            raise ReportRebuildError(
                "Linux finite native transport correspondence differs"
            )
        return role
    if name in {
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py",
    }:
        if source_buffer is None:
            raise ReportRebuildError(
                "Linux counting API requires captured source custody"
            )
        role = validated_current_scientific_source(
            repository,
            {"path": name, "sha256": expected[0], "bytes": expected[1]},
            "source/" + name,
            source_buffer,
        )
        if role is None or role.get("classification") != "finite_counting_api_addition":
            raise ReportRebuildError("Linux counting API correspondence differs")
        return role
    correspondence = _HISTORICAL_READER_IDENTITIES.get(name)
    if correspondence is not None:
        logical = "source/" + name
        if (
            expected != tuple(correspondence)
            or source_buffer is None
            or logical not in source_buffer.detached
            or source_buffer.read_source(logical) != historical
        ):
            raise ReportRebuildError(
                "Linux declared reader source correspondence differs"
            )
        role = validated_current_scientific_source(
            repository,
            {"path": name, "sha256": expected[0], "bytes": expected[1]},
            logical,
            source_buffer,
        )
        if (
            role is None
            or role.get("path") != name
            or role.get("classification") != "historical_custody_reader_metadata"
        ):
            raise ReportRebuildError("Linux declared reader custody role differs")
        return role
    definitions = _DOCUMENTED_NUMERIC_DEFINITIONS.get(name)
    if definitions is not None and _named_documentation_insertions(
        historical, body, definitions
    ):
        return None
    raise ReportRebuildError("Linux current scientific implementation changed")


def _historical_version_metadata(
    source_buffer: SourceCapsule, identity: dict[str, Any], historical: bytes
) -> None:
    """Authenticate the one original generated member without current-file authority."""
    generated = source_buffer.descriptor.generated
    if (
        len(generated) != 1
        or type(generated[0]) is not dict
        or generated[0].get("member") != VERSION_MEMBER
        or type(identity.get("bytes")) is not int
        or identity.get("bytes") != VERSION_BYTES
        or identity.get("sha256") != VERSION_SHA256
        or len(historical) != VERSION_BYTES
        or hashlib.sha256(historical).hexdigest() != VERSION_SHA256
    ):
        raise ReportRebuildError("Linux historical generated metadata identity differs")
    if reconstruct(generated[0], identity) != historical:
        raise ReportRebuildError("Linux historical generated metadata content differs")


def validated_linux_r_reference_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Transport exactly 137 outputs from the captured source-built Linux R run."""
    rows = [r for r in owners if r.get("owner_id") == OWNER]
    active = (
        any(r.get("role") == "retained_source" for r in rows)
        or (repository / CAPTURE).exists()
    )
    if not active:
        return (), {}
    if len(rows) != 1:
        raise ReportRebuildError("Linux capture needs exactly one owner")
    owner = rows[0]
    if (
        owner.get("role") != "retained_source"
        or owner.get("producer_paths") != []
        or owner.get("producer_inputs") != []
    ):
        raise ReportRebuildError("Linux capture owner declaration differs")
    path = _file(repository, CAPTURE, "Linux capture")
    if hashlib.sha256(path.read_bytes()).hexdigest() != CAPTURE_SHA256:
        raise ReportRebuildError("Linux capture authority bytes differ")
    capture = _json(path)
    members = capture.get("members")
    if (
        not isinstance(members, list)
        or type(capture.get("member_count")) is not int
        or capture["member_count"] != len(members)
        or len(members) != 2311
    ):
        raise ReportRebuildError("Linux retained member count differs")
    packet = path.parent
    files: dict[str, dict[str, Any]] = {}
    for raw in members:
        member = _object(raw, "Linux member malformed")
        name, digest, size = (
            member.get("path"),
            member.get("sha256"),
            member.get("bytes"),
        )
        if (
            not isinstance(name, str)
            or not name
            or PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or PurePosixPath(name).as_posix() != name
            or name in files
            or type(size) is not int
            or size < 0
            or not isinstance(digest, str)
        ):
            raise ReportRebuildError("Linux member identity differs")
        files[name] = member
    source_buffer = validated_descriptor(
        repository,
        packet.relative_to(repository).as_posix(),
        normalize_members(members),
    )
    _native_references(packet, capture, source_buffer.read_source)
    projection = _object(
        capture.get("current_scientific_source_projection"),
        "Linux source projection missing",
    )
    scientific = projection.get("members")
    if not isinstance(scientific, list) or len(scientific) != 127:
        raise ReportRebuildError("Linux scientific projection differs")
    historical_generated = 0
    reader_correspondences: list[JsonObject] = []
    transport_correspondences: list[JsonObject] = []
    counting_correspondences: list[JsonObject] = []
    for raw in scientific:
        item = _object(raw, "Linux source projection malformed")
        name = item.get("relative_path")
        if not isinstance(name, str) or not name.startswith(
            (
                "packages/bijux-pollenomics-lra/",
                "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/",
            )
        ):
            raise ReportRebuildError("Linux scientific source owner differs")
        if files.get("source/" + name, {}).get("sha256") != item.get("sha256"):
            raise ReportRebuildError(
                "Linux original source projection membership differs"
            )
        historical = source_buffer.read_source("source/" + name)
        if name == VERSION_SOURCE:
            _historical_version_metadata(source_buffer, item, historical)
            historical_generated += 1
        else:
            role = _require_scientific_projection(
                repository, name, item, historical, source_buffer=source_buffer
            )
            if role is not None:
                if (
                    role.get("classification")
                    == "finite_native_reference_transport_extension"
                ):
                    transport_correspondences.append(role)
                elif role.get("classification") == "finite_counting_api_addition":
                    counting_correspondences.append(role)
                else:
                    reader_correspondences.append(role)
    if historical_generated != 1:
        raise ReportRebuildError("Linux historical generated source membership differs")
    lock_name = "configs/ci/lra-r-source-lock.v1.json"
    current_lock = _file(repository, lock_name, "Linux current R source lock")
    if hashlib.sha256(current_lock.read_bytes()).hexdigest() != files.get(
        "source/" + lock_name, {}
    ).get("sha256"):
        raise ReportRebuildError("Linux current R dependency lock changed")
    authority = _object(
        capture.get("current_report_owner"), "Linux output authority missing"
    )
    outputs = authority.get("outputs")
    if (
        authority.get("owner_id") != OWNER
        or not isinstance(outputs, list)
        or len(outputs) != 137
    ):
        raise ReportRebuildError("Linux output membership differs")
    accepted: list[InventoryEntry] = []
    names: list[str] = []
    for raw in outputs:
        item = _object(raw, "Linux output malformed")
        name = item.get("path")
        if not isinstance(name, str) or not name.startswith(FAMILY) or name in names:
            raise ReportRebuildError("Linux output path differs")
        names.append(name)
        expected = files.get("retained/" + name.removeprefix(FAMILY))
        entry = tracked_by_path.get(name)
        physical = _file(repository, name, "Linux report")
        if (
            expected is None
            or item.get("sha256") != expected["sha256"]
            or item.get("bytes") != expected["bytes"]
            or entry is None
            or entry.kind != "file"
            or entry.sha256 != expected["sha256"]
            or entry.size != expected["bytes"]
            or hashlib.sha256(physical.read_bytes()).hexdigest() != expected["sha256"]
            or physical.stat().st_size != expected["bytes"]
        ):
            raise ReportRebuildError("Linux current report bytes differ")
        accepted.append(entry)
    if owner.get("paths") != sorted(names):
        raise ReportRebuildError("Linux exact137 owner path set differs")
    for other in owners:
        other_paths = other.get("paths")
        if (
            other is not owner
            and other.get("role") == "retained_source"
            and isinstance(other_paths, list)
            and set(names).intersection(other_paths)
        ):
            raise ReportRebuildError("Linux retained output ownership overlaps")
    source_buffer.fresh()
    return tuple(accepted), {
        "owner_id": OWNER,
        "capture_sha256": CAPTURE_SHA256,
        "executed_source_candidate": SOURCE_CANDIDATE,
        "assembly_candidate": capture.get("assembly_candidate"),
        "source_files": 2148,
        "scientific_current_projection": 126,
        "historical_reader_source_correspondences": reader_correspondences,
        "native_reference_transport_correspondences": transport_correspondences,
        "finite_counting_api_correspondences": counting_correspondences,
        "ordinary_current_byte_exact_members": 120
        - len(transport_correspondences)
        - len(counting_correspondences),
        "historical_generated_metadata_members": 1,
        "historical_generated_metadata_sha256": VERSION_SHA256,
        "retained_execution_files": 140,
        "report_outputs": 137,
        "paths_sha256": canonical_json_sha256(sorted(names)),
        "historical_source_gap_retained": True,
        "scope": "Captured local ARM64 R4.6 source oracle,43core+23source-domain cases and independentDecimal50 comparison. Original127source projection binds126current inputs:116 declared ordinary tracked inputs, with separately listed exact counting API additions and all other ordinary bodies byte-exact, four fixed old-identity reader custody roles, four separately bound native-reference transport extensions and two exact named numeric-documentation insertions. Current custody validators require their separate maintained qualification, and their current file hashes are not execution-time source postimages. One separately declared historical539 runtime member is authenticated by its exact descriptor generator, scalars and original body identity; no equality with current ignored version metadata is claimed. The ten declared current reader/documentation/transport bodies are not labelled execution-time source. No claim the entire current executable source tree equals the captured execution. Original1661source missing4 epoch stays separate. Transport executes noR, optimizer, browser, acquisition or ecological/human/rights/hostedx86_64 release acceptance.",
    }
