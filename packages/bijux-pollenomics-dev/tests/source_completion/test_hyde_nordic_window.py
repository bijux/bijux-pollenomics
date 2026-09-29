"""Keep the HYDE Nordic-intent bundle source-index-only and refusal-bounded."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, cast

import pytest

from bijux_pollenomics.collection.sources.hyde.ascii import (
    AsciiWindowSelection,
    NativeAsciiHeader,
    NativeAsciiWindow,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics_dev.source_completion import hyde_nordic_window
from bijux_pollenomics_dev.source_completion.hyde_nordic_window import (
    HydeDeclarationParentInput,
    HydeNativeWindowInput,
    publish_hyde_nordic_window_bundle,
    read_hyde_nordic_window_bundle,
)

Scenario = Literal["base", "lower", "upper"]
SCENARIOS: tuple[Scenario, ...] = ("base", "lower", "upper")
ARCHIVES = {
    "base": (
        "original/gbc2025_7apr_base/zip/2000AD_lu.zip",
        "d0a762ccce3256d25c36e1c58894c6a6b05f93075006366854cc7e6176c7d09f",
        "31a74f63973886edbd2303737df2684c799caaea83af27561755e1d5da67b0c7",
    ),
    "lower": (
        "original/gbc2025_7apr_lower/zip/2000AD_lu.zip",
        "e763c82b62e7fd6c19d68113bcff23bfebaf5e71732f39824762a951e738480b",
        "af2ec9495411a2651a17d7e992213c28ca13e6afde8662eed12ffc267edecf70",
    ),
    "upper": (
        "original/gbc2025_7apr_upper/zip/2000AD_lu.zip",
        "8a3a518655e16e7a49c72c6463ef4a377588c271d0a381f32c60dd8a801f7ea9",
        "9e8dbff9b25e24227f4f8fcdf1abb41911f62873e1a23e61b37327105b57aabe",
    ),
}
HEADER_TOKENS = (
    ("ncols", "4320"),
    ("nrows", "2160"),
    ("xllcorner", "-180"),
    ("yllcorner", "-90"),
    ("cellsize", "0.0833333"),
    ("NODATA_value", "-9999"),
)
OUTPUT_NAMES = {
    "manifest.json",
    "scenarios/base/manifest.json",
    "scenarios/base/window.json",
    "scenarios/lower/manifest.json",
    "scenarios/lower/window.json",
    "scenarios/upper/manifest.json",
    "scenarios/upper/window.json",
}

JsonObject = dict[str, Any]


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _json(path: Path) -> JsonObject:
    value = json.loads(path.read_bytes())
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def _write_canonical(path: Path, value: object) -> str:
    content = (
        json.dumps(
            value,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    path.write_bytes(content)
    return _sha256(content)


def _tree_files(root: Path) -> set[str]:
    return {
        path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()
    }


def _replace_first_key(value: object, key: str, replacement: object) -> bool:
    if isinstance(value, dict):
        if key in value:
            value[key] = replacement
            return True
        return any(
            _replace_first_key(child, key, replacement) for child in value.values()
        )
    if isinstance(value, list):
        return any(_replace_first_key(child, key, replacement) for child in value)
    return False


def _window(
    directory: Path,
    scenario: str,
    *,
    first_nonmissing: str,
) -> NativeAsciiWindow:
    archive_path, _, member_sha256 = ARCHIVES[scenario]
    selection = AsciiWindowSelection(
        archive_path=archive_path,
        member_index=0,
        expected_member_name="cropland2000AD.asc",
        row_start=216,
        row_stop=432,
        column_start=2208,
        column_stop=2544,
        native_labels=(
            ("scenario", scenario),
            ("time", "2000AD"),
            ("variable", "cropland"),
        ),
    )
    header = NativeAsciiHeader(
        bytes_base64="",
        tokens=HEADER_TOKENS,
        rows=2160,
        columns=4320,
    )
    missing_count = 29_217
    nonmissing_count = 43_359
    zero_count = {"base": 15_307, "lower": 15_158, "upper": 15_332}[scenario]
    tokens = (
        ("-9999",) * missing_count
        + ("0.000",)
        + ("0",) * (zero_count - 1)
        + (first_nonmissing,)
        + ("1",) * (nonmissing_count - zero_count - 1)
    )
    missing = (True,) * missing_count + (False,) * nonmissing_count
    return NativeAsciiWindow(
        directory=directory,
        manifest_sha256=_sha256((directory / "manifest.json").read_bytes()),
        custody_manifest_sha256=hyde_nordic_window.CUSTODY_MANIFEST_SHA256,
        member_sha256=member_sha256,
        selection=selection,
        header=header,
        source_tokens=tokens,
        missing_mask=missing,
    )


def _geometry(window: NativeAsciiWindow, *, archive_sha256: str) -> JsonObject:
    scenario_source = ARCHIVES[dict(window.selection.native_labels)["scenario"]]
    assert archive_sha256 == scenario_source[1]
    nonmissing = [
        token
        for token, missing in zip(
            window.source_tokens, window.missing_mask, strict=True
        )
        if not missing
    ]
    missing_count = sum(window.missing_mask)
    nonmissing_count = len(nonmissing)
    zero_count = sum(float(value) == 0 for value in nonmissing)
    return {
        "schema_version": "hyde-native-axis-geometry.v1",
        "window_manifest_sha256": window.manifest_sha256,
        "custody_manifest_sha256": window.custody_manifest_sha256,
        "archive_path": window.selection.archive_path,
        "archive_sha256": archive_sha256,
        "archive_member_index": 0,
        "archive_member_name": "cropland2000AD.asc",
        "member_sha256": window.member_sha256,
        "native_labels": dict(window.selection.native_labels),
        "source_header_tokens": dict(window.header.tokens),
        "source_rows": window.header.rows,
        "source_columns": window.header.columns,
        "selected_source_indices": {
            "row_start": 216,
            "row_stop": 432,
            "column_start": 2208,
            "column_stop": 2544,
        },
        "source_axis_edges": dict(hyde_nordic_window._SOURCE_AXIS_EDGES),
        "selected_cells": 72_576,
        "selected_missing": missing_count,
        "selected_nonmissing": nonmissing_count,
        "selected_zero": zero_count,
        "coordinate_reference_system": None,
        "variable_units": None,
        "calendar_support": None,
        "country_projection": "not_performed",
        "scientific_acceptance": "not_evaluated",
        "public_release_allowed": False,
    }


def _declaration_inventory() -> SimpleNamespace:
    global_attributes = cast(
        dict[str, list[str]],
        hyde_nordic_window._NETCDF_RAW_DECLARATIONS["global_attributes"],
    )
    return SimpleNamespace(
        input_sha256=tuple(hyde_nordic_window._DECLARATION_HASHES.items()),
        custody_manifest_sha256=hyde_nordic_window.CUSTODY_MANIFEST_SHA256,
        dataset_inventory_sha256=hyde_nordic_window.DATASET_INVENTORY_SHA256,
        scenario_counts=(("base", 16), ("lower", 16), ("upper", 16)),
        conflicts=hyde_nordic_window._CONFLICTS,
        scenario_role="provider_estimate_scenarios",
        pointwise_ordering_contract="none",
        scenario_confidence_bounds=False,
        native_release_admitted=False,
        rights_cleared=False,
        crs_assigned=False,
        canonical_bp_conversion_allowed=False,
        publication_allowed=False,
        independent_measured_vegetation_truth=False,
        scientific_acceptance="not_evaluated",
        files=tuple(
            SimpleNamespace(
                variable="cropland",
                units="km**2",
                global_attributes=tuple(
                    (key, values[0]) for key, values in global_attributes.items()
                ),
            )
            for _scenario in SCENARIOS
        ),
        axes=(
            SimpleNamespace(
                name="time",
                units="days since 1-5-1 00:00:00",
                calendar="365_day",
            ),
        ),
        schema_version="hyde-netcdf-declaration-inventory.v1",
        sha256="f" * 64,
    )


@pytest.fixture
def configured_inputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> tuple[
    tuple[HydeNativeWindowInput, ...],
    HydeDeclarationParentInput,
    dict[Path, NativeAsciiWindow],
]:
    retained: dict[Path, NativeAsciiWindow] = {}
    inputs = []
    for scenario, first_nonmissing in zip(
        SCENARIOS, ("1.5000", "2.7500", "3.1250"), strict=True
    ):
        directory = tmp_path / "retained" / scenario
        directory.mkdir(parents=True)
        (directory / "manifest.json").write_bytes(
            f'{{"scenario":"{scenario}"}}\n'.encode()
        )
        _write_canonical(
            directory / "window.json",
            {
                "source_tokens": ["-9999", "0.000", first_nonmissing],
                "missing_mask": [True, False, False],
            },
        )
        retained[directory.resolve()] = _window(
            directory.resolve(), scenario, first_nonmissing=first_nonmissing
        )
        inputs.append(
            HydeNativeWindowInput(
                scenario,
                directory,
                _sha256((directory / "manifest.json").read_bytes()),
            )
        )

    parents = tmp_path / "declarations"
    parents.mkdir()
    parent_paths = []
    for name in ("files.jsonl", "report.json", "metadata.json", "conflicts.json"):
        path = parents / name
        path.write_text(name, encoding="utf-8")
        parent_paths.append(path)
    declarations = HydeDeclarationParentInput(
        file_inventory_path=parent_paths[0],
        expected_file_inventory_sha256=hyde_nordic_window._FILE_INVENTORY_SHA256,
        inventory_report_path=parent_paths[1],
        expected_inventory_report_sha256=(hyde_nordic_window._INVENTORY_REPORT_SHA256),
        header_inventory_path=parent_paths[2],
        expected_header_inventory_sha256=hyde_nordic_window._HEADER_INVENTORY_SHA256,
        conflict_report_path=parent_paths[3],
        expected_conflict_report_sha256=hyde_nordic_window._CONFLICT_REPORT_SHA256,
    )

    def read_ascii(
        directory: Path, *, expected_manifest_sha256: str
    ) -> NativeAsciiWindow:
        resolved = Path(directory).resolve()
        window = retained.get(resolved)
        if window is None and resolved.name in SCENARIOS:
            original = next(
                candidate
                for path, candidate in retained.items()
                if path.name == resolved.name
            )
            window = replace(original, directory=resolved)
        assert window is not None
        assert expected_manifest_sha256 == window.manifest_sha256
        return window

    monkeypatch.setattr(hyde_nordic_window, "_read_ascii_window", read_ascii)
    monkeypatch.setattr(
        hyde_nordic_window,
        "_read_declarations",
        lambda **_kwargs: _declaration_inventory(),
    )
    monkeypatch.setattr(hyde_nordic_window, "_native_axis_geometry", _geometry)
    monkeypatch.setattr(
        hyde_nordic_window,
        "_child_source_identity",
        lambda content: (
            hyde_nordic_window.CUSTODY_MANIFEST_SHA256,
            hyde_nordic_window.DATASET_INVENTORY_SHA256,
            (
                source := hyde_nordic_window.SCENARIO_SOURCES[
                    cast(Scenario, json.loads(content)["scenario"])
                ]
            ).archive_sha256,
            source.archive_bytes,
            source.member_bytes,
            source.member_crc32,
        ),
    )
    monkeypatch.setattr(
        hyde_nordic_window,
        "_declaration_parents_unchanged",
        lambda _parents: None,
    )
    monkeypatch.setattr(
        hyde_nordic_window,
        "_producer_identity",
        lambda: {"source_completion/hyde_nordic_window.py": "e" * 64},
    )
    return tuple(inputs), declarations, retained


@pytest.fixture
def bundle(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    tmp_path: Path,
) -> Path:
    windows, declarations, _ = configured_inputs
    destination = tmp_path / "bundle"
    publish_hyde_nordic_window_bundle(
        windows=windows,
        declarations=declarations,
        destination=destination,
    )
    return destination


def test_bundle_is_byte_deterministic_with_exact_inventory_and_child_bytes(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    tmp_path: Path,
) -> None:
    windows, declarations, _ = configured_inputs
    first = tmp_path / "bundle-first"
    second = tmp_path / "bundle-second"
    first_product = publish_hyde_nordic_window_bundle(
        windows=windows, declarations=declarations, destination=first
    )
    second_product = publish_hyde_nordic_window_bundle(
        windows=windows, declarations=declarations, destination=second
    )
    assert _tree_files(first) == OUTPUT_NAMES
    assert _tree_files(second) == OUTPUT_NAMES
    assert first_product.manifest_sha256 == second_product.manifest_sha256
    assert first_product.selected_index_positions == 72_576
    assert first_product.scenario_token_instances == 217_728
    for name in OUTPUT_NAMES:
        assert (first / name).read_bytes() == (second / name).read_bytes()
    for source in windows:
        for name in ("manifest.json", "window.json"):
            assert (first / "scenarios" / source.scenario / name).read_bytes() == (
                source.directory / name
            ).read_bytes()


def test_manifest_retains_raw_profiles_without_semantic_promotion(bundle: Path) -> None:
    manifest = _json(bundle / "manifest.json")
    encoded = json.dumps(manifest, sort_keys=True)
    assert manifest["schema_version"] == ("hyde-nordic-intent-native-window-bundle.v1")
    assert manifest["status"] == "private_source_index_only"
    assert manifest["counts"] == {
        "scenario_count": 3,
        "unique_selected_index_positions": 72_576,
        "scenario_token_instances": 217_728,
    }
    assert "2000AD" in encoded
    assert "cropland" in encoded
    assert "0.0833333" in encoded
    assert "-9999" in encoded
    assert "km**2" in encoded
    assert "365_day" in encoded
    assert "days since 1-5-1 00:00:00" in encoded
    declarations = cast(JsonObject, manifest["declarations"])
    assert declarations["input_sha256"] == hyde_nordic_window._DECLARATION_HASHES
    assert declarations["conflicts"] == list(hyde_nordic_window._CONFLICTS)
    assert declarations["netcdf_raw_declarations"] == (
        hyde_nordic_window._NETCDF_RAW_DECLARATIONS
    )
    assert declarations["netcdf_cropland_unit_candidates"] == ["km**2"]
    assert declarations["netcdf_unit_transfer_to_ascii"] == "not_performed"
    assert "CC BY-NC" not in encoded
    assert '"3.3"' not in encoded
    assert '"3.5"' not in encoded

    semantics = cast(JsonObject, manifest["effective_semantics"])
    assert semantics == {
        "calendar_support": None,
        "cell_area": None,
        "coordinate_reference_system": None,
        "country_assignment_method": None,
        "independent_measured_vegetation_truth": False,
        "pointwise_ordering_contract": "none",
        "public_release_allowed": False,
        "rights_cleared": False,
        "scenario_confidence_bounds": False,
        "scientific_acceptance": "not_evaluated",
        "variable_units": None,
    }
    forbidden = (
        "value_total",
        "value_mean",
        "value_minimum",
        "value_maximum",
        "cell_fraction",
        "cross_scenario_arithmetic",
    )
    assert all(name not in manifest for name in forbidden)


def test_raw_numeric_spelling_missingness_zero_headers_and_labels_survive(
    bundle: Path,
) -> None:
    for scenario, raw in zip(SCENARIOS, ("1.5000", "2.7500", "3.1250"), strict=True):
        content = (bundle / "scenarios" / scenario / "window.json").read_text()
        assert '"-9999"' in content
        assert '"0.000"' in content
        assert f'"{raw}"' in content
    manifest = _json(bundle / "manifest.json")
    scenarios = cast(list[JsonObject], manifest["scenarios"])
    assert [row["scenario"] for row in scenarios] == list(SCENARIOS)
    assert all(
        row["source_header_tokens"] == [list(pair) for pair in HEADER_TOKENS]
        for row in scenarios
    )
    assert all(
        row["native_labels"]
        == [
            ["scenario", row["scenario"]],
            ["time", "2000AD"],
            ["variable", "cropland"],
        ]
        for row in scenarios
    )
    assert all(
        row["source_axis_edges"]
        == {
            "authority": "undeclared_native_axis_values",
            **hyde_nordic_window._SOURCE_AXIS_EDGES,
        }
        for row in scenarios
    )
    assert [row["counts"] for row in scenarios] == [
        {
            "selected_cells": 72_576,
            "selected_missing": 29_217,
            "selected_nonmissing": 43_359,
            "selected_zero": zero_count,
        }
        for zero_count in (15_307, 15_158, 15_332)
    ]
    # The synthetic lower token exceeds base and remains valid source text; no
    # confidence-bound or pointwise-ordering contract is inferred.
    assert float("2.7500") > float("1.5000")


def test_four_country_intents_remain_ordered_null_and_refused(bundle: Path) -> None:
    manifest = _json(bundle / "manifest.json")
    intent = cast(JsonObject, manifest["country_intent"])
    assert intent["requested_country_codes"] == ["SE", "DK", "NO", "FI"]
    assert intent["partition_status"] == "not_materialized"
    rows = cast(list[JsonObject], intent["rows"])
    assert [row["country_code"] for row in rows] == ["SE", "DK", "NO", "FI"]
    assert "UNASSIGNED" not in json.dumps(intent)
    for row in rows:
        assert row["assignment_status"] == "refused"
        assert row["selected_cells"] is None
        assert row["nonmissing_cells"] is None
        assert row["cell_area"] is None
        assert row["value_total"] is None
        assert row["reason_codes"] == [
            "hyde_native_country_projection_unverified",
            "candidate_source_axis_window_is_not_country_partition",
        ]


@pytest.mark.parametrize(
    "indices",
    ((0, 2, 1), (0, 0, 2), (0, 1)),
)
def test_exact_three_scenario_order_and_denominator_are_required(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    tmp_path: Path,
    indices: tuple[int, ...],
) -> None:
    windows, declarations, _ = configured_inputs
    with pytest.raises(IntakeRefusal):
        publish_hyde_nordic_window_bundle(
            windows=tuple(windows[index] for index in indices),
            declarations=declarations,
            destination=tmp_path / f"bad-order-{''.join(map(str, indices))}",
        )


@pytest.mark.parametrize(
    ("mutation", "value"),
    (
        ("scenario", "upper"),
        ("time", "1999AD"),
        ("variable", "pasture"),
        ("row_start", 215),
        ("row_stop", 431),
        ("column_start", 2207),
        ("column_stop", 2543),
        ("expected_member_name", "pasture2000AD.asc"),
    ),
)
def test_coordinated_source_profile_relabeling_is_refused(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    tmp_path: Path,
    mutation: str,
    value: object,
) -> None:
    windows, declarations, retained = configured_inputs
    base_path = windows[0].directory.resolve()
    base = retained[base_path]
    selection = base.selection
    with pytest.raises(IntakeRefusal):
        if mutation in {"scenario", "time", "variable"}:
            labels = dict(selection.native_labels)
            labels[mutation] = cast(str, value)
            changed_selection = replace(selection, native_labels=tuple(labels.items()))
        else:
            if mutation == "expected_member_name":
                assert isinstance(value, str)
                changed_selection = replace(selection, expected_member_name=value)
            else:
                assert isinstance(value, int)
                if mutation == "row_start":
                    changed_selection = replace(selection, row_start=value)
                elif mutation == "row_stop":
                    changed_selection = replace(selection, row_stop=value)
                elif mutation == "column_start":
                    changed_selection = replace(selection, column_start=value)
                else:
                    assert mutation == "column_stop"
                    changed_selection = replace(selection, column_stop=value)
        retained[base_path] = replace(base, selection=changed_selection)
        publish_hyde_nordic_window_bundle(
            windows=windows,
            declarations=declarations,
            destination=tmp_path / f"bad-profile-{mutation}",
        )


@pytest.mark.parametrize("mutation", ("archive", "member", "header"))
def test_archive_member_and_header_identity_changes_are_refused(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    tmp_path: Path,
    mutation: str,
) -> None:
    windows, declarations, retained = configured_inputs
    base_path = windows[0].directory.resolve()
    base = retained[base_path]
    if mutation == "archive":
        selection = replace(
            base.selection,
            archive_path=("original/gbc2025_7apr_base/renamed/zip/2000AD_lu.zip"),
        )
        changed = replace(base, selection=selection)
    elif mutation == "member":
        changed = replace(base, member_sha256="0" * 64)
    else:
        header = replace(
            base.header,
            tokens=tuple(
                (key, "0.1" if key == "cellsize" else value)
                for key, value in base.header.tokens
            ),
        )
        changed = replace(base, header=header)
    retained[base_path] = changed
    with pytest.raises(IntakeRefusal, match="hyde_nordic_window_profile_invalid"):
        publish_hyde_nordic_window_bundle(
            windows=windows,
            declarations=declarations,
            destination=tmp_path / f"bad-{mutation}",
        )


@pytest.mark.parametrize(
    ("key", "replacement"),
    (
        ("coordinate_reference_system", "EPSG:4326"),
        ("variable_units", "km**2"),
        ("calendar_support", "2000 CE"),
        ("cell_area", "1 km2"),
        ("country_assignment_method", "rectangle-is-Nordic"),
        ("selected_cells", 1),
        ("nonmissing_cells", 1),
        ("value_total", "1"),
        ("public_release_allowed", True),
        ("rights_cleared", True),
        ("scientific_acceptance", "accepted"),
        ("independent_measured_vegetation_truth", True),
        ("scenario_confidence_bounds", True),
        ("pointwise_ordering_contract", "lower_le_base_le_upper"),
        ("time_axis_units", ["days since 2000-1-1"]),
        ("time_axis_calendars", ["gregorian"]),
    ),
)
def test_coordinated_outer_rehash_cannot_promote_a_refused_claim(
    bundle: Path,
    key: str,
    replacement: object,
) -> None:
    manifest_path = bundle / "manifest.json"
    manifest = _json(manifest_path)
    assert _replace_first_key(manifest, key, replacement), key
    changed_sha256 = _write_canonical(manifest_path, manifest)
    with pytest.raises(IntakeRefusal, match="hyde_nordic"):
        read_hyde_nordic_window_bundle(bundle, expected_manifest_sha256=changed_sha256)


def test_wrong_outer_digest_refuses_before_any_child_read(
    bundle: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def forbidden_child_read(*_args: object, **_kwargs: object) -> None:
        nonlocal calls
        calls += 1
        raise AssertionError("child reader must not run before outer identity passes")

    monkeypatch.setattr(hyde_nordic_window, "_read_ascii_window", forbidden_child_read)
    with pytest.raises(IntakeRefusal, match="digest"):
        read_hyde_nordic_window_bundle(bundle, expected_manifest_sha256="0" * 64)
    assert calls == 0


@pytest.mark.parametrize(
    "relative", ("scenarios/base/manifest.json", "scenarios/base/window.json")
)
def test_child_mutation_is_refused(bundle: Path, relative: str) -> None:
    manifest_sha256 = _sha256((bundle / "manifest.json").read_bytes())
    path = bundle / relative
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(IntakeRefusal, match="hyde_nordic"):
        read_hyde_nordic_window_bundle(bundle, expected_manifest_sha256=manifest_sha256)


def test_extra_files_and_symlinked_children_are_refused(bundle: Path) -> None:
    manifest_sha256 = _sha256((bundle / "manifest.json").read_bytes())
    (bundle / "unexpected.txt").write_text("not contracted", encoding="utf-8")
    with pytest.raises(IntakeRefusal, match="hyde_nordic"):
        read_hyde_nordic_window_bundle(bundle, expected_manifest_sha256=manifest_sha256)
    (bundle / "unexpected.txt").unlink()
    child = bundle / "scenarios/base/window.json"
    child.unlink()
    child.symlink_to(bundle / "scenarios/lower/window.json")
    with pytest.raises(IntakeRefusal):
        read_hyde_nordic_window_bundle(bundle, expected_manifest_sha256=manifest_sha256)


def test_input_window_mutation_during_validation_is_refused(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    windows, declarations, _ = configured_inputs
    original = hyde_nordic_window._native_axis_geometry
    changed = False

    def mutate_after_capture(
        window: NativeAsciiWindow, *, archive_sha256: str
    ) -> JsonObject:
        nonlocal changed
        result = original(window, archive_sha256=archive_sha256)
        if not changed:
            changed = True
            source = windows[0].directory / "window.json"
            source.write_bytes(source.read_bytes() + b" ")
        return result

    monkeypatch.setattr(
        hyde_nordic_window, "_native_axis_geometry", mutate_after_capture
    )
    with pytest.raises(IntakeRefusal, match="changed"):
        publish_hyde_nordic_window_bundle(
            windows=windows,
            declarations=declarations,
            destination=tmp_path / "source-race",
        )


def test_output_path_refusals_cover_existing_dangling_parent_and_overlap(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    tmp_path: Path,
) -> None:
    windows, declarations, _ = configured_inputs
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises((FileExistsError, IntakeRefusal)):
        publish_hyde_nordic_window_bundle(
            windows=windows, declarations=declarations, destination=existing
        )

    dangling = tmp_path / "dangling"
    dangling.symlink_to(tmp_path / "absent", target_is_directory=True)
    with pytest.raises((FileExistsError, IntakeRefusal)):
        publish_hyde_nordic_window_bundle(
            windows=windows, declarations=declarations, destination=dangling
        )

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(IntakeRefusal):
        publish_hyde_nordic_window_bundle(
            windows=windows,
            declarations=declarations,
            destination=linked_parent / "bundle",
        )

    with pytest.raises(IntakeRefusal, match="overlap"):
        publish_hyde_nordic_window_bundle(
            windows=windows,
            declarations=declarations,
            destination=windows[0].directory / "nested-output",
        )

    with pytest.raises(IntakeRefusal, match="overlap"):
        publish_hyde_nordic_window_bundle(
            windows=windows,
            declarations=declarations,
            destination=declarations.file_inventory_path / "nested-output",
        )


def test_declaration_parent_bytes_are_rechecked_after_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths: list[Path] = []
    hashes: list[str] = []
    for name in ("files.jsonl", "report.json", "metadata.json", "conflict.json"):
        path = tmp_path / name
        path.write_bytes(f"governed-{name}".encode())
        paths.append(path)
        hashes.append(_sha256(path.read_bytes()))
    expected = {
        "file_inventory": hashes[0],
        "inventory_report": hashes[1],
        "header_inventory": hashes[2],
        "conflict_report": hashes[3],
    }
    monkeypatch.setattr(hyde_nordic_window, "_DECLARATION_HASHES", expected)
    parents = HydeDeclarationParentInput(
        paths[0],
        hashes[0],
        paths[1],
        hashes[1],
        paths[2],
        hashes[2],
        paths[3],
        hashes[3],
    )
    hyde_nordic_window._declaration_parents_unchanged(parents)
    paths[2].write_bytes(paths[2].read_bytes() + b"changed")
    with pytest.raises(IntakeRefusal, match="hyde_nordic_input_changed"):
        hyde_nordic_window._declaration_parents_unchanged(parents)


def test_injected_target_race_preserves_target_and_pending_stage(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    windows, declarations, _ = configured_inputs
    destination = tmp_path / "raced"
    original = hyde_nordic_window._publish_new_output_tree

    def inject_target(*, final_output_root: Path, staging_output_root: Path) -> None:
        final_output_root.mkdir()
        original(
            final_output_root=final_output_root,
            staging_output_root=staging_output_root,
        )

    monkeypatch.setattr(hyde_nordic_window, "_publish_new_output_tree", inject_target)
    with pytest.raises(IntakeRefusal, match="hyde_nordic_publish_failed"):
        publish_hyde_nordic_window_bundle(
            windows=windows,
            declarations=declarations,
            destination=destination,
        )
    assert destination.is_dir()
    assert any(path.name.startswith(".raced.pending-") for path in tmp_path.iterdir())


def test_producer_change_before_publication_is_refused(
    configured_inputs: tuple[
        tuple[HydeNativeWindowInput, ...],
        HydeDeclarationParentInput,
        dict[Path, NativeAsciiWindow],
    ],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    windows, declarations, _ = configured_inputs
    calls = 0

    def changing_identity() -> dict[str, str]:
        nonlocal calls
        calls += 1
        return {"source_completion/hyde_nordic_window.py": f"{calls:064x}"}

    monkeypatch.setattr(hyde_nordic_window, "_producer_identity", changing_identity)
    with pytest.raises(IntakeRefusal, match="producer.*changed"):
        publish_hyde_nordic_window_bundle(
            windows=windows,
            declarations=declarations,
            destination=tmp_path / "producer-change",
        )


@pytest.mark.skipif(
    os.environ.get("BIJUX_RUN_HYDE_NORDIC_REAL_INTEGRATION") != "1",
    reason="explicit BIJUX_RUN_HYDE_NORDIC_REAL_INTEGRATION=1 opt-in required",
)
def test_real_retained_windows_match_the_pinned_three_scenario_profile(
    tmp_path: Path,
) -> None:
    repository = Path(__file__).resolve().parents[4]
    root = repository / "artifacts/v3/hyde/nordic-intent-window-9180abe1/windows"
    windows = tuple(
        HydeNativeWindowInput(scenario, root / scenario, manifest_sha256)
        for scenario, manifest_sha256 in zip(
            SCENARIOS,
            (
                "915adbbb8f2d47e887c79c0a4cdcb2a6af24e5d352e2ef464c6cdda375496e3f",
                "425c3e85d7ca54d6c5ca6834852ea94f2f474c6fbd28ffc9e48261e00116ef80",
                "70ef0a31e8f2e4e0441236f204d0e14244c414d8406bd5d399d67d0f2c3179da",
            ),
            strict=True,
        )
    )
    declarations = HydeDeclarationParentInput(
        file_inventory_path=repository / "artifacts/v2/hyde-intake/hash002/files.jsonl",
        expected_file_inventory_sha256=(
            "727893bef686146611dcb702e7fab5c497f70c8630b8d2a3fc158b3b5b7d53ef"
        ),
        inventory_report_path=(
            repository / "artifacts/v2/hyde-intake/hash002/report.json"
        ),
        expected_inventory_report_sha256=(
            "3b951d91b064fa6885ec5e3ffaac82217bb7d9058f11e21d9b58216f4d3d1ac9"
        ),
        header_inventory_path=repository
        / "artifacts/v2/hyde-intake/netcdf001/metadata.json",
        expected_header_inventory_sha256=(
            "b1809b9a5f935332c336aa695b9c2614a5c8db4a15ee1b86106fa6a13a622d1f"
        ),
        conflict_report_path=repository
        / "artifacts/v2/hyde-native-metadata/report.json",
        expected_conflict_report_sha256=(
            "1de8918edcb9e27507effc6ab360a7c23a4e06c9bbb369552ea3e4d88589fcbb"
        ),
    )
    product = publish_hyde_nordic_window_bundle(
        windows=windows,
        declarations=declarations,
        destination=tmp_path / "real-bundle",
    )
    assert product.selected_index_positions == 72_576
    assert product.scenario_token_instances == 217_728
