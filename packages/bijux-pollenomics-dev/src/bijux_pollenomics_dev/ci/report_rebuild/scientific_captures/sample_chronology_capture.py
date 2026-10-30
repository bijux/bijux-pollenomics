"""Authenticate retained source-owned chronology browser observations."""

from __future__ import annotations

import ast
import difflib
import hashlib
from pathlib import Path
from typing import Any

from ..contracts import ReportRebuildError
from ..ownership import _regular_confined_file
from ..retained_source import SourceCapsule
from ..retained_source.descriptor import normalize_members
from ..retained_source.index import validated_descriptor
from .atlas_source_views import (
    CASE_IDS,
    OWNER_IDS,
    ValidatedAtlasCapture,
    _relative,
    _require,
    _sha,
    read_object,
)
from .presentation_source_roles import (
    HISTORICAL_RENDERING_SOURCES,
    atlas_extension_matches,
)
from .source_roles.sead_join_identity import (
    SEAD_JOIN_IDENTITY_SOURCES,
    validated_declared_join_identity_source,
)

CURRENT_CAPTURE_PATH = "data/atlas/sample-chronology-source-view-capture/capture.json"
CURRENT_CAPTURE_SHA256 = (
    "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62"
)
CURRENT_SOURCE_CANDIDATE = "63fe7e57c597d6a0a0b8b80befa8331950b231cd"
CURRENT_CASE_IDS = CASE_IDS | {"sample-owned-chronology-components"}


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
DOCUMENTED_CAPTURE_DEFINITIONS = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/locality.py": (
        "<module>",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/models/localities.py": (
        "AdnaLocalitySummary.latitude",
        "AdnaLocalitySummary.longitude",
        "AdnaLocalitySummary.latitude_text",
        "AdnaLocalitySummary.longitude_text",
        "AdnaLocalitySummary.coordinate_confidence",
        "AdnaLocalitySummary.locality_namespace",
        "AdnaLocalitySummary.locality_token",
        "AdnaLocalitySummary.time_start_bp",
        "AdnaLocalitySummary.time_end_bp",
        "AdnaLocalitySummary.time_mean_bp",
        "AdnaLocalitySummary.time_label",
        "AdnaLocalitySummary.dating_basis",
        "AdnaLocalitySummary.as_dict",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/models/occurrence_support.py": (
        "AdnaSampleChronologySupport.as_dict",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/classification/events/authority.py": (
        "<module>",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/fieldwork/land_use/context.py": (
        "<module>",
        "overlapping_geojson_context",
        "overlapping_human_context",
        "overlapping_animal_context",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py": (
        "PropagationOutputRefusalError.__init__",
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/selection.py": (
        "PropagationSelection.__post_init__",
        "PropagationSelection.as_dict",
    ),
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py": (
        "main",
    ),
}
DOCUMENTED_CAPTURE_STRINGS = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/locality.py": {
        "<module>": "Build locality identities and retain sample chronology support."
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/models/localities.py": {
        "AdnaLocalitySummary.latitude": "Return the locality latitude.",
        "AdnaLocalitySummary.longitude": "Return the locality longitude.",
        "AdnaLocalitySummary.latitude_text": "Return the source latitude text.",
        "AdnaLocalitySummary.longitude_text": "Return the source longitude text.",
        "AdnaLocalitySummary.coordinate_confidence": "Return the coordinate evidence confidence.",
        "AdnaLocalitySummary.locality_namespace": "Return the shared locality identity namespace.",
        "AdnaLocalitySummary.locality_token": "Return the locality's stable identity token.",
        "AdnaLocalitySummary.time_start_bp": "Return the stored locality chronology start bound in BP.",
        "AdnaLocalitySummary.time_end_bp": "Return the stored locality chronology end bound in BP.",
        "AdnaLocalitySummary.time_mean_bp": "Return the stored locality chronology mean in BP.",
        "AdnaLocalitySummary.time_label": "Return the source chronology label.",
        "AdnaLocalitySummary.dating_basis": "Return the source dating basis.",
        "AdnaLocalitySummary.as_dict": "Serialize locality coverage and sample-owned chronology supports.",
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/classification/events/authority.py": {
        "<module>": "Bind classification events to their admitted evidence and release authority."
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/fieldwork/land_use/context.py": {
        "<module>": "Summarize spatial and temporal context for declared fieldwork targets.",
        "overlapping_geojson_context": "Count dated point features and locality references near the target.",
        "overlapping_human_context": "Count localities and samples with overlapping owned intervals.",
        "overlapping_animal_context": "Count animal localities and sample totals within the declared bounds.",
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py": {
        "PropagationOutputRefusalError.__init__": "Retain the stable refusal code alongside its explanatory detail."
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/selection.py": {
        "PropagationSelection.__post_init__": "Require a canonical scenario, country selection and signal set.",
        "PropagationSelection.as_dict": "Expose the selected projection context as JSON-compatible values.",
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/models/occurrence_support.py": {
        "AdnaSampleChronologySupport.as_dict": "Serialize sample chronology with its source and provenance metadata."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py": {
        "main": "Generate the declared sample chronology atlas candidate."
    },
}


_SourceDefinition = ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef


def _documented_source_matches(name: str, captured: bytes, current: bytes) -> bool:
    """Allow only named literal documentation insertions and their adjacent blank line.

    The archived executable and every noninserted byte stay authoritative. This
    does not add a current authored-text hash or admit another definition's edits.
    """
    definitions = DOCUMENTED_CAPTURE_DEFINITIONS.get(name)
    if definitions is None:
        return False
    try:
        old_text, current_text = captured.decode("utf-8"), current.decode("utf-8")
        old_tree, current_tree = (
            ast.parse(old_text, type_comments=True),
            ast.parse(current_text, type_comments=True),
        )
    except (SyntaxError, UnicodeError, ValueError):
        return False

    def nodes(tree: ast.Module) -> dict[str, list[_SourceDefinition]]:
        found: dict[str, list[_SourceDefinition]] = {"<module>": [tree]}

        def visit(parent: _SourceDefinition, scope: tuple[str, ...]) -> None:
            for child in getattr(parent, "body", []):
                if isinstance(
                    child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    qualified = ".".join((*scope, child.name))
                    found.setdefault(qualified, []).append(child)
                    visit(child, (*scope, child.name))

        visit(tree, ())
        return found

    old_nodes, current_nodes = nodes(old_tree), nodes(current_tree)
    inserted: set[int] = set()
    adjacent: set[int] = set()
    for qualified in definitions:
        if (
            len(old_nodes.get(qualified, [])) != 1
            or len(current_nodes.get(qualified, [])) != 1
        ):
            return False
        old_node, node = old_nodes[qualified][0], current_nodes[qualified][0]
        if (
            ast.get_docstring(old_node, clean=False) is not None
            or ast.get_docstring(node, clean=False)
            != DOCUMENTED_CAPTURE_STRINGS[name][qualified]
            or not (ast.get_docstring(node, clean=False) or "").strip()
        ):
            return False
        statement = node.body[0]
        if (
            not isinstance(statement, ast.Expr)
            or not isinstance(statement.value, ast.Constant)
            or type(statement.value.value) is not str
            or statement.end_lineno is None
        ):
            return False
        if statement.end_col_offset is None:
            return False
        raw_lines = current.splitlines(keepends=True)
        if (
            raw_lines[statement.lineno - 1][: statement.col_offset].strip()
            or raw_lines[statement.end_lineno - 1][statement.end_col_offset :].strip()
        ):
            return False
        inserted.update(range(statement.lineno - 1, statement.end_lineno))
        adjacent.update({statement.lineno - 2, statement.end_lineno})
        node.body = node.body[1:]
    if ast.dump(old_tree, include_attributes=False) != ast.dump(
        current_tree, include_attributes=False
    ):
        return False
    old_lines, current_lines = (
        old_text.splitlines(keepends=True),
        current_text.splitlines(keepends=True),
    )
    for operation, _, _, first, last in difflib.SequenceMatcher(
        a=old_lines, b=current_lines, autojunk=False
    ).get_opcodes():
        if operation == "equal":
            continue
        if operation != "insert":
            return False
        if any(
            line not in inserted
            and (line not in adjacent or current_lines[line].strip())
            for line in range(first, last)
        ):
            return False
    return True


_NEOTOMA_QUALIFIER_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/neotoma/__init__.py"
_NEOTOMA_QUALIFIER_IDENTITY = (
    "cdf755312d22f0b6e1a3edc8f7bd7fac0a8c9bd41b180273d6b22f16c7e47974",
    3711,
)


def _neotoma_qualifier_source_correspondence(
    repository: Path,
    name: str,
    logical: str,
    captured: bytes,
    current: bytes,
    expected: str,
    source_buffer: SourceCapsule | None,
) -> bool:
    """Bind one qualifier annotation extension to the original chronology source."""
    if name != _NEOTOMA_QUALIFIER_SOURCE or source_buffer is None:
        return False
    checksum, size = _NEOTOMA_QUALIFIER_IDENTITY
    identity = {"sha256": checksum, "bytes": size}
    _require(
        repository == repository.resolve()
        and source_buffer.repository == repository
        and source_buffer.prefix == "data/atlas/sample-chronology-source-view-capture"
        and source_buffer.descriptor.capture.get("sha256")
        == "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62"
        and expected == checksum
        and len(captured) == size
        and hashlib.sha256(captured).hexdigest() == checksum
        and logical == "source/" + name
        and logical in source_buffer.detached
        and source_buffer.descriptor.members.get(logical) == identity
        and [
            path
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if member == logical
        ]
        == [name],
        "original chronology qualifier source binding differs",
    )
    source_buffer.fresh()
    source = _regular_confined_file(repository, name, "current qualifier source")
    before = source.stat()
    _require(
        before.st_nlink == 1
        and 0 < before.st_size <= 128 * 1024**2
        and source.read_bytes() == current,
        "current qualifier source must be bounded stable single-link",
    )
    added = b're.compile(r"(?:^|\\s)cf\\.?\\s", re.IGNORECASE)'
    original = b're.compile(r"(?:^|\\s)cf\\.\\s", re.IGNORECASE)'
    if current.count(added) != 1 or current.replace(added, original, 1) != captured:
        return False
    source_buffer.fresh()
    after_source = _regular_confined_file(repository, name, "current qualifier source")
    after = after_source.stat()
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
        all(getattr(before, field) == getattr(after, field) for field in fields)
        and after_source.read_bytes() == current,
        "current qualifier source changed during correspondence",
    )
    return True


def _counting_api_source_extension(
    repository: Path,
    name: str,
    logical: str,
    captured: bytes,
    expected: str,
    source_buffer: SourceCapsule | None,
) -> bool:
    """Apply the exact counting addition only to the original chronology API pair."""
    if name not in {
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/api.py",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/__init__.py",
    }:
        return False
    from .source_correspondence import validated_current_scientific_source

    _require(
        source_buffer is not None, "chronology counting API requires source custody"
    )
    assert source_buffer is not None
    role = validated_current_scientific_source(
        repository,
        {"path": name, "sha256": expected, "bytes": len(captured)},
        logical,
        source_buffer,
    )
    return (
        role is not None
        and role.get("classification") == "finite_counting_api_addition"
    )


def _validate_current_source(
    repository: Path,
    name: str,
    logical: str,
    captured: bytes,
    expected: str,
    detached: frozenset[str],
    *,
    source_buffer: SourceCapsule | None = None,
) -> None:
    """Keep raw capture bytes exact and current presentation roles explicit."""
    _require(
        hashlib.sha256(captured).hexdigest() == expected,
        "captured source bytes differ: " + name,
    )
    source = _regular_confined_file(
        repository, _relative(name), "current captured source"
    )
    if name in HISTORICAL_PORTAL_READER_SOURCES | HISTORICAL_RENDERING_SOURCES:
        _require(
            logical == "source/" + name
            and logical in detached
            and source.stat().st_nlink == 1,
            "historical presentation storage role differs: " + name,
        )
        return
    current = source.read_bytes()
    if hashlib.sha256(current).hexdigest() != expected:
        _require(
            logical == "source/" + name
            and logical in detached
            and source.stat().st_nlink == 1
            and (
                (
                    name in DOCUMENTED_CAPTURE_DEFINITIONS
                    and _documented_source_matches(name, captured, current)
                )
                or atlas_extension_matches(name, captured, current)
                or (
                    source_buffer is not None
                    and name in SEAD_JOIN_IDENTITY_SOURCES
                    and validated_declared_join_identity_source(
                        repository,
                        {"path": name, "sha256": expected, "bytes": len(captured)},
                        logical,
                        source_buffer,
                    ).get("classification")
                    == "declared_child_key_refusal_identity"
                )
                or _counting_api_source_extension(
                    repository, name, logical, captured, expected, source_buffer
                )
                or _neotoma_qualifier_source_correspondence(
                    repository,
                    name,
                    logical,
                    captured,
                    current,
                    expected,
                    source_buffer,
                )
            ),
            "current source footprint differs: " + name,
        )


def _validate_current_reader_custody(
    packet: dict[str, Any],
    members: dict[str, Path],
    review: dict[str, Any],
    generation_inputs: dict[str, str],
) -> None:
    """Join readers to exact successful source production or retained partial custody."""
    current = packet.get("current_reader_reference")
    reused = packet.get("reused_source_producer_reference")
    _require(
        isinstance(current, dict)
        and set(current)
        == {"plan", "terminal", "locality-producer", "reader", "observer"}
        and isinstance(reused, dict)
        and set(reused) == {"plan", "terminal", "producer-import-origins"},
        "current reader and reused producer reference coverage differs",
    )
    assert isinstance(current, dict) and isinstance(reused, dict)
    objects: dict[str, dict[str, Any]] = {}
    for group, references in (("current", current), ("reused", reused)):
        observed = review.get(
            "current_reader_reference"
            if group == "current"
            else "reused_source_producer_reference"
        )
        _require(
            isinstance(observed, dict) and set(observed) == set(references),
            "independent reader reference coverage differs",
        )
        assert isinstance(observed, dict)
        for role, name in references.items():
            member = members[_relative(name)]
            _require(
                observed[role]["sha256"] == _sha(member),
                "independent reader reference digest differs",
            )
            objects[f"{group}/{role}"] = read_object(member)
    plan = objects["current/plan"]
    terminal = objects["current/terminal"]
    producer = objects["current/locality-producer"]
    reader = objects["current/reader"]
    observer = objects["current/observer"]
    old_plan = objects["reused/plan"]
    old_terminal = objects["reused/terminal"]
    origins = objects["reused/producer-import-origins"]
    stages = terminal["stages"]
    mode = plan.get("reader_custody_mode", "reused-partial-source-producer")
    _require(
        mode in {"reused-partial-source-producer", "same-run-source-producer"},
        "current reader custody mode differs",
    )
    direct = mode == "same-run-source-producer"
    _require(
        plan["candidate"] == terminal["candidate"] == CURRENT_SOURCE_CANDIDATE
        and terminal["plan_sha256"] == _sha(members[current["plan"]])
        and type(terminal["native_exit_code"]) is int
        and terminal["native_exit_code"] == 0
        and terminal["status"] == "passed"
        and terminal["protected_inputs_unchanged"] is True
        and len(stages) == len(plan["stages"]) == (3 if direct else 2)
        and [stage["name"] for stage in stages]
        == [stage["name"] for stage in plan["stages"]]
        and all(
            type(stage["native_exit_code"]) is int
            and stage["native_exit_code"] == 0
            and stage["timed_out"] is False
            and stage["actual_argv"] == declared["argv"]
            for stage, declared in zip(stages, plan["stages"], strict=True)
        ),
        "current reader native execution differs",
    )
    if direct:
        _require(
            [stage["name"] for stage in stages]
            == [
                "maintained-source-owned-locality-wire-products",
                "actual-declared-public-reader-transport",
                "independent-original-membership-reader-observer",
            ]
            and _sha(members[reused["plan"]]) == _sha(members[current["plan"]])
            and _sha(members[reused["terminal"]]) == _sha(members[current["terminal"]])
            and old_plan == plan
            and old_terminal == terminal
            and plan["source_directory"] == origins["source_root"]
            and set(plan["reader_products"])
            == {"locality_producer", "reader", "observer"}
            and plan["reader_products"]["locality_producer"]
            == str(
                Path(origins["source_root"])
                / "artifacts/public-chronology-readers/localities/producer-proof.json"
            )
            and "reused_source_producer" not in plan,
            "same-run producer native result differs",
        )
        source_pins = {row["path"]: row["sha256"] for row in plan["protected_inputs"]}
        _require(
            len(source_pins) == len(plan["protected_inputs"])
            and all(
                source_pins.get(origin["path"]) == origin["sha256"]
                for origin in origins["actual_origins"]
            ),
            "same-run producer protected source differs",
        )
    else:
        reused_producer = plan["reused_source_producer"]
        _require(
            reused_producer["original_plan_sha256"] == _sha(members[reused["plan"]])
            and reused_producer["original_terminal_sha256"]
            == _sha(members[reused["terminal"]])
            and reused_producer["reused_source_producer_proof_sha256"]
            == _sha(members[current["locality-producer"]])
            and old_plan["candidate"]
            == old_terminal["candidate"]
            == CURRENT_SOURCE_CANDIDATE
            and old_terminal["plan_sha256"] == _sha(members[reused["plan"]])
            and type(old_terminal["native_exit_code"]) is int
            and old_terminal["native_exit_code"] == 1
            and old_terminal["status"] == "failed"
            and old_terminal["protected_inputs_unchanged"] is True
            and old_terminal["stages"][0]
            == reused_producer["reused_source_producer_stage"]
            and type(old_terminal["stages"][0]["native_exit_code"]) is int
            and old_terminal["stages"][0]["native_exit_code"] == 0
            and old_terminal["stages"][0]["timed_out"] is False
            and old_terminal["stages"][0]["actual_argv"]
            == old_plan["stages"][0]["argv"]
            and plan["source_directory"]
            == old_plan["source_directory"]
            == reused_producer["source_directory"]
            == origins["source_root"],
            "reused producer partial native result differs",
        )
    _require(
        all(
            type(result["native_exit"]) is int and result["native_exit"] == 0
            for result in (producer, reader, observer, origins)
        )
        and producer["animal_localities"] == 547
        and producer["human_selected_localities"] == 2
        and producer["animal_source_samples"] == 1468
        and producer["human_source_samples"] == 55
        and reader["actual_sample_records"]
        == observer["actual_original_samples"]
        == 2699
        and reader["new_locality_records"] == 549
        and reader["new_locality_producer_proof_sha256"]
        == observer["locality_producer_sha256"]
        == _sha(members[current["locality-producer"]])
        and observer["reader_proof_sha256"] == _sha(members[current["reader"]])
        and observer["original_sample_producer_sha256"]
        == _sha(members[packet["source_normalization_reference"]["producer"]])
        and observer["all_reader_cases_joined_to_exact_source_membership"] is True,
        "current reader source membership differs",
    )
    source = Path(origins["source_root"])
    observed_modules: set[str] = set()
    _require(bool(origins["actual_origins"]), "reused producer origins are absent")
    for origin in origins["actual_origins"]:
        path = Path(origin["path"])
        _require(path.is_relative_to(source), "reused producer origin escapes source")
        relative = _relative(path.relative_to(source).as_posix())
        _require(
            isinstance(origin["module"], str)
            and origin["module"] not in observed_modules
            and generation_inputs.get(relative) == origin["sha256"],
            "reused producer captured source differs",
        )
        observed_modules.add(origin["module"])


def validated_sample_chronology_capture(repository: Path) -> ValidatedAtlasCapture:
    """Admit a fixed native packet, never an arbitrary ownership role or receipt.

    Captured source and verifier bytes must still match the candidate whose
    displays are described. Retained transport does not execute a browser and
    does not extend the scientific admission of the displayed records.
    """
    repository = repository.absolute()
    path = _regular_confined_file(repository, CURRENT_CAPTURE_PATH, "atlas capture")
    _require(_sha(path) == CURRENT_CAPTURE_SHA256, "certificate digest differs")
    packet = read_object(path)
    _require(
        packet["schema_version"] == "atlas-sample-chronology-source-capture.v2"
        and packet["source_candidate"] == CURRENT_SOURCE_CANDIDATE
        and packet["scientific_admission"] is False
        and packet["numerical_execution"] is False
        and packet["browser"] == "Chrome/155.0.8059.40",
        "capture identity or admission differs",
    )
    directory = path.parent
    catalogue = normalize_members(packet["files"])
    _require(len(catalogue) == 1472, "original logical member population differs")
    source_buffer = validated_descriptor(
        repository, directory.relative_to(repository).as_posix(), catalogue
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
    _require(
        len(packet["source_footprint"]) == 1226, "original source population differs"
    )
    for name, expected in packet["source_footprint"].items():
        logical = _relative(packet["source_members"][name])
        captured = source_buffer.read_source(logical)
        _validate_current_source(
            repository,
            name,
            logical,
            captured,
            expected,
            source_buffer.detached,
            source_buffer=source_buffer,
        )
    runtime_resources = packet.get("runtime_resources", {})
    _require(isinstance(runtime_resources, dict), "runtime resource inventory differs")
    generated_version = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/_build_version.py"
    )
    _require(
        set(runtime_resources) <= {generated_version},
        "unrecognized generated runtime resource",
    )
    _require(
        not set(runtime_resources) & set(packet["source_footprint"]),
        "runtime resource overlaps maintained source",
    )
    resource_digests: dict[str, str] = {}
    for name, resource in runtime_resources.items():
        _require(
            resource["generated_by"] == "vcs-versioning",
            "generated runtime producer differs",
        )
        logical = _relative(resource["member"])
        _require(
            logical in source_buffer.detached
            and {row["member"] for row in source_buffer.descriptor.generated}
            == {logical},
            "named retained runtime resource differs",
        )
        _require(
            hashlib.sha256(source_buffer.read_source(logical)).hexdigest()
            == resource["sha256"],
            "retained generated runtime bytes differ",
        )
        resource_digests[name] = resource["sha256"]
    generation_inputs = {**packet["source_footprint"], **resource_digests}
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
            "generate-sample-chronology",
        }
        and len(packet["generator_executions"]) == 5,
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
    _require(len(generations) == 5, "candidate generation coverage differs")
    for member in generations.values():
        generation = read_object(members[_relative(member)])
        _require(
            all(
                generation_inputs.get(name) == digest
                for name, digest in generation["inputs_sha256"].items()
            ),
            "generation source footprint differs",
        )
    review = read_object(members[packet["independent_review"]["member"]])
    _require(
        review["candidate"] == CURRENT_SOURCE_CANDIDATE
        and review["counts"]["successful_probes"] == 9
        and review["counts"]["visually_inspected_PNGs"] == 12
        and review["counts"]["authentic_component_source_sample_rows"] == 55
        and review["counts"]["normalized_sample_chronologies_checked"] == 55
        and review["counts"]["authentic_disjoint_components"] == 3
        and review["counts"]["native_browser_viewports"] == 2
        and review["served_and_output_hashes_all_match"] is True
        and review["all_selected_source_tables_exact"] is True,
        "independent current source/browser review differs",
    )
    references = packet["source_normalization_reference"]
    _require(
        set(references)
        == {
            "plan",
            "terminal",
            "producer",
            "observer",
            "human-sweden",
            "human-denmark",
        },
        "source normalization reference coverage differs",
    )
    source_execution = read_object(members[_relative(references["terminal"])])
    source_proof = read_object(members[_relative(references["producer"])])
    source_review = read_object(members[_relative(references["observer"])])
    _require(
        type(source_execution["native_exit_code"]) is int
        and source_execution["native_exit_code"] == 0
        and source_execution["status"] == "passed"
        and source_execution["protected_inputs_unchanged"] is True
        and source_execution["plan_sha256"]
        == _sha(members[_relative(references["plan"])])
        and type(source_proof["human_records"]) is int
        and source_proof["human_records"] == 1231
        and type(source_proof["animal_records"]) is int
        and source_proof["animal_records"] == 1468
        and type(source_review["native_exit"]) is int
        and source_review["native_exit"] == 0
        and type(source_review["counts"]["samples"]) is int
        and source_review["counts"]["samples"] == 2699
        and source_review[
            "exact_cross_format_chronology_native_identity_and_provenance"
        ]
        is True,
        "source normalization native proof differs",
    )
    _validate_current_reader_custody(packet, members, review, generation_inputs)
    for case in packet["cases"]:
        case_id = case["case_id"]
        _require(
            case_id in CURRENT_CASE_IDS and case_id not in cases,
            "case coverage differs",
        )
        cases.add(case_id)
        receipt = read_object(members[_relative(case["receipt"])])
        _require(case["generation"] in generations.values(), "case generation differs")
        execution = case["native_execution"]
        _require(
            case["source_candidate"] == CURRENT_SOURCE_CANDIDATE
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
        verifier = (
            "sample_chronology/components.mjs"
            if case_id == "sample-owned-chronology-components"
            else Path(execution["actual_argv"][1]).name
        )
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
    _require(cases == CURRENT_CASE_IDS, "browser observations are incomplete")
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
    expected_stage_ids = {
        "generate-source-details",
        "generate-Nordic-source-contexts",
        "generate-modeled-panels",
        "generate-context-frames",
        "generate-sample-chronology",
        *("capture-" + name for name in CURRENT_CASE_IDS),
    }
    execution = read_object(members[_relative(packet["native_terminal"])])
    stages = {stage["id"]: stage for stage in execution["stages"]}
    _require(
        execution["candidate"] == CURRENT_SOURCE_CANDIDATE
        and type(execution["native_exit"]) is int
        and execution["native_exit"] == 0
        and execution["status"] == "passed"
        and execution["resource_bounds_met"] is True
        and len(stages) == len(execution["stages"]) == 14
        and set(stages) == expected_stage_ids
        and all(
            stage["passed"] is True
            and type(stage["native_exit"]) is int
            and stage["native_exit"] == 0
            and stage["timeout"] is False
            for stage in stages.values()
        ),
        "complete current native generator/browser scope did not pass",
    )
    _require(
        review["qualified_current_plan_sha256"]
        == _sha(members[_relative(packet["native_plan"])])
        and review["qualified_current_terminal_sha256"]
        == _sha(members[_relative(packet["native_terminal"])]),
        "independent review native execution binding differs",
    )
    for case in packet["cases"]:
        stage = stages["capture-" + case["case_id"]]
        _require(
            all(
                case["native_execution"][key] == stage[key]
                for key in (
                    "id",
                    "actual_argv",
                    "native_exit",
                    "timeout",
                    "stdout_sha256",
                    "stderr_sha256",
                )
            )
            and stage["browser_receipt"]["sha256"] == _sha(members[case["receipt"]]),
            "browser case native lineage differs",
        )
    for generation in packet["generator_executions"]:
        stage = stages[generation["id"]]
        _require(
            all(
                generation[key] == stage[key]
                for key in (
                    "id",
                    "actual_argv",
                    "native_exit",
                    "timeout",
                    "stdout_sha256",
                    "stderr_sha256",
                )
            ),
            "candidate generator native lineage differs",
        )
    _require(
        packet["scientific_admission"] is False
        and packet["sample_chronology_admission"] is False
        and packet["source_context"].get("not_a_clean_git_tree") is True,
        "selected-source/browser scope differs",
    )
    source_buffer.fresh()
    return ValidatedAtlasCapture(directory, packet, members)
