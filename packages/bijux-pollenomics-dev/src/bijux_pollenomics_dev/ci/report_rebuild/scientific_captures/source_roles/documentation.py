"""Preserve exact named documentation insertions beside immutable source bodies."""

from __future__ import annotations

import ast
import difflib
from typing import Any

DOCUMENTED_SOURCE_STRINGS: dict[str, dict[str, str]] = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/sample_chronology/candidate.py": {
        "main": "Generate the declared sample chronology atlas candidate."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/source_contracts/raa_native_geopackage.py": {
        "check_capture": "Require the original national byte identity and nonadmission flags."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/two_taxon_counting.py": {
        "main": "Write the declared two-taxon counting comparison and its source context."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/two_taxon_counting_verification.py": {
        "binomial_cdf": "Accumulate the independent binomial lower-tail probability.",
        "binomial_probabilities": "Evaluate the independent binomial mass probabilities.",
        "bounds": "Bracket the binomial probability interval under the declared confidence.",
        "main": "Verify the retained counting intervals against independent arithmetic.",
        "transform": "Map a pollen probability through the fixed response factors.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/cli.py": {
        "main": "Verify a private native witness before publishing aggregate support."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/geometry.py": {
        "envelope_distances": "Bound projected distance from a point to a finite envelope.",
        "support_class": "Classify circle support from point distance or envelope bounds.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/independent.py": {
        "records": "Read byte-pinned witness rows with bounded lines and exact final counts.",
        "verify": "Verify saved geometry, owner and support identities and counts.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/native.py": {
        "candidates": "Yield bounded geometry candidates through the declared RTree index.",
        "indexed_rows": "Read bounded UUID-owned rows only through an indexed lookup.",
        "inspect_local_schema": "Validate the native GeoPackage tables, geometry profile and CRS.",
        "native": "Preserve bounded native values with their SQLite storage types.",
        "require": "Refuse a violated native-source invariant.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/report.py": {
        "aggregate": "Build public support counts without admitting dates or events."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/streams.py": {
        "NativeWitness": "Write deterministic gzip witness rows under shared byte limits.",
        "NativeWitness.__init__": "Open an absent witness file with a shared decoded-byte budget.",
        "NativeWitness.close": "Close the witness and return its byte and row identities.",
        "NativeWitness.write": "Append one JSON row after checking row and cumulative byte ceilings.",
        "WitnessBudget": "Share a decoded-byte ceiling across native witness streams.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/landscape_context/geodesic.py": {
        "point": "Validate finite WGS84 latitude and longitude coordinates."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/landscape_context/membership.py": {
        "evaluate": "Compare source memberships and counts under both distance methods."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/landscape_context/publication.py": {
        "main": "Publish geographic sensitivity without private feature rows."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/landscape_context/report.py": {
        "csv_file": "Write ordered tabular rows with declared empty-output columns.",
        "main": "Write source-bound distance and membership comparison artifacts.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/landscape_context/source.py": {
        "age": "Preserve nullable finite native ages and refuse other types.",
        "load": "Load pinned trajectory features, centres and shared-grid lineage.",
        "text_list": "Require textual native identities and preserve their order.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_reconstruction/swedish_conditional_love/identifiability/algebra.py": {
        "require": "Refuse an input outside the declared affine-mixture domain."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_reconstruction/swedish_conditional_love/identifiability/independent.py": {
        "rational": "Represent a declared scalar with exact rational arithmetic.",
        "require": "Refuse an invalid independent identifiability comparison.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/pollen_reconstruction/swedish_conditional_love/identifiability/producer.py": {
        "main": "Write the conditional identifiability comparison and its source context.",
        "pin": "Describe the bytes and digest of a declared source input.",
        "qualify": "Keep one input inside its declared conditional identifiability scope.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/scientific_readers/source_files.py": {
        "main": "Export the finite first-party attachment set without scientific admission."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead/chronology_annotations/cli.py": {
        "main": "Write annotation aggregates and a separately owned native witness."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead/chronology_annotations/comparison.py": {
        "compare_field": "Classify native-field changes without approving equivalence.",
        "json_type": "Name JSON storage kinds without collapsing booleans into integers.",
        "same": "Require exact canonical JSON equality for the named native field.",
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead/chronology_annotations/custody.py": {
        "lookup": "Resolve a typed native parent while preserving allowed nulls."
    },
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/sead/chronology_annotations/source.py": {
        "index_rows": "Index native rows by unique nonnegative integer identifiers."
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/locality.py": {
        "<module>": "Build locality identities and retain sample chronology support."
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/models/localities.py": {
        "AdnaLocalitySummary.as_dict": "Serialize locality coverage and sample-owned chronology supports.",
        "AdnaLocalitySummary.coordinate_confidence": "Return the coordinate evidence confidence.",
        "AdnaLocalitySummary.dating_basis": "Return the source dating basis.",
        "AdnaLocalitySummary.latitude": "Return the locality latitude.",
        "AdnaLocalitySummary.latitude_text": "Return the source latitude text.",
        "AdnaLocalitySummary.locality_namespace": "Return the shared locality identity namespace.",
        "AdnaLocalitySummary.locality_token": "Return the locality's stable identity token.",
        "AdnaLocalitySummary.longitude": "Return the locality longitude.",
        "AdnaLocalitySummary.longitude_text": "Return the source longitude text.",
        "AdnaLocalitySummary.time_end_bp": "Return the stored locality chronology end bound in BP.",
        "AdnaLocalitySummary.time_label": "Return the source chronology label.",
        "AdnaLocalitySummary.time_mean_bp": "Return the stored locality chronology mean in BP.",
        "AdnaLocalitySummary.time_start_bp": "Return the stored locality chronology start bound in BP.",
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/models/occurrence_support.py": {
        "AdnaSampleChronologySupport.as_dict": "Serialize sample chronology with its source and provenance metadata."
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/classification/events/authority.py": {
        "<module>": "Bind classification events to their admitted evidence and release authority."
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/fieldwork/land_use/context.py": {
        "<module>": "Summarize spatial and temporal context for declared fieldwork targets.",
        "overlapping_animal_context": "Count animal localities and sample totals within the declared bounds.",
        "overlapping_geojson_context": "Count dated point features and locality references near the target.",
        "overlapping_human_context": "Count localities and samples with overlapping owned intervals.",
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py": {
        "PropagationOutputRefusalError.__init__": "Retain the stable refusal code alongside its explanatory detail."
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/selection.py": {
        "PropagationSelection.__post_init__": "Require a canonical scenario, country selection and signal set.",
        "PropagationSelection.as_dict": "Expose the selected projection context as JSON-compatible values.",
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/rootsi/cells/biff.py": {
        "CompoundBook.dirlist": "Expose physical directory entries for stream ownership checks.",
        "CompoundBook.get_named_stream": "Return the named raw stream without interpreting cell formulas.",
        "CompoundDecoder.__call__": "Decode one bounded container while retaining diagnostics.",
    },
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/presentation/report_portal/publication.py": {
        "<module>": "Publish report portal navigation and structural reader accounts."
    },
}


def _documented_source_matches(name: str, captured: bytes, current: bytes) -> bool:
    """Recognize only named literal docs, adjacent blank lines and three typed stubs."""
    expected = DOCUMENTED_SOURCE_STRINGS.get(name)
    if expected is None:
        return False
    try:
        old = ast.parse(captured.decode("utf-8"), type_comments=True)
        new = ast.parse(current.decode("utf-8"), type_comments=True)
    except (SyntaxError, UnicodeError, ValueError):
        return False

    def definitions(tree: ast.Module) -> dict[str, list[Any]]:
        result: dict[str, list[Any]] = {"<module>": [tree]}

        def walk(node: Any, parents: tuple[str, ...] = ()) -> None:
            for child in getattr(node, "body", []):
                if isinstance(
                    child, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    key = ".".join((*parents, child.name))
                    result.setdefault(key, []).append(child)
                    walk(child, (*parents, child.name))

        walk(tree)
        return result

    before, after = definitions(old), definitions(new)
    lines = current.decode("utf-8").splitlines(keepends=True)
    removed: set[int] = set()
    adjacent: set[int] = set()
    for key, literal in expected.items():
        if len(before.get(key, [])) != 1 or len(after.get(key, [])) != 1:
            return False
        first, last = before[key][0], after[key][0]
        if (
            ast.get_docstring(first, clean=False) is not None
            or ast.get_docstring(last, clean=False) != literal
        ):
            return False
        statement = last.body[0]
        if (
            not isinstance(statement, ast.Expr)
            or not isinstance(statement.value, ast.Constant)
            or type(statement.value.value) is not str
            or statement.end_lineno is None
            or statement.end_col_offset is None
        ):
            return False
        if (
            lines[statement.lineno - 1][: statement.col_offset].strip()
            or lines[statement.end_lineno - 1][statement.end_col_offset :].strip()
        ):
            return False
        removed.update(range(statement.lineno - 1, statement.end_lineno))
        adjacent.update((statement.lineno - 2, statement.end_lineno))
        last.body = last.body[1:]
    if ast.dump(old, include_attributes=False) != ast.dump(
        new, include_attributes=False
    ):
        return False
    remaining = [(i, line) for i, line in enumerate(lines) if i not in removed]
    if name.endswith("/collection/sources/rootsi/cells/biff.py"):
        # The three named Protocol methods expand only their literal ellipsis stubs.
        signatures = (
            "    def dirlist(self) -> Sequence[DirectoryEntry]:",
            "    def get_named_stream(self, name: str) -> bytes | None:",
            "    def __call__(self, payload: bytes, *, logfile: TextIO) -> CompoundBook:",
        )
        for signature in signatures:
            found = [
                i for i, (_, line) in enumerate(remaining) if line == signature + "\n"
            ]
            if len(found) != 1:
                return False
            index = found[0]
            if (
                index + 1 >= len(remaining)
                or remaining[index + 1][1] != "        ...\n"
            ):
                return False
            original_index = remaining[index][0]
            remaining[index : index + 2] = [(original_index, signature + " ...\n")]
    old_lines = captured.decode("utf-8").splitlines(keepends=True)
    new_lines = [line for _, line in remaining]
    for operation, _, _, start, stop in difflib.SequenceMatcher(
        a=old_lines, b=new_lines, autojunk=False
    ).get_opcodes():
        if operation == "equal":
            continue
        if operation != "insert" or any(
            remaining[i][0] not in adjacent or new_lines[i].strip()
            for i in range(start, stop)
        ):
            return False
    return True
