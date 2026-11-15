"""Archive selectors preserve lower source roles before any body buffer opens."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import archive


def selected_api(mode: str) -> Callable[..., dict[str, Any]]:
    name = "read_neotoma_source_archive_" + mode
    owner: Any = getattr(archive, name, None)
    assert callable(owner), f"Selected archive API {name} is unavailable"
    return cast(Callable[..., dict[str, Any]], owner)


def make_archive(
    make: Callable[..., dict[str, Any]],
    publish: Callable[..., Any],
    root: Path,
    **options: Any,
) -> tuple[Path, str, dict[str, Any]]:
    inputs = make(**options)
    catalogue, pin, sources = publish(inputs)
    output = root / "archive"
    archive.write_neotoma_source_archive(
        output,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=pin,
        capture_sources=sources,
    )
    return output, sha256((output / "manifest.json").read_bytes()).hexdigest(), inputs


def forbid_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    native = Path.open

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body":
            pytest.fail("body buffer opened before selected archive refusal")
        return native(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)


@pytest.mark.parametrize("mode", ["resource", "entity"])
@pytest.mark.parametrize("dataset_id", [203, 204, 999])
@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_protected_and_unknown_archive_selections_open_no_bodies(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
    dataset_id: int,
    version: str,
) -> None:
    read = selected_api(mode)
    root, pin, _ = make_archive(catalogue_sources, publish_catalogue, tmp_path)
    forbid_bodies(monkeypatch)
    with pytest.raises(ValueError, match="exposure role|outside"):
        read(root, expected_manifest_sha256=pin, dataset_id=dataset_id, version=version)


@pytest.mark.parametrize("mode", ["resource", "entity"])
@pytest.mark.parametrize("dataset_id", [True, 0, -1, 201.0, "201"])
def test_invalid_native_selector_refuses_before_archive_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, dataset_id: object
) -> None:
    read = selected_api(mode)
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("archive opened"))
    with pytest.raises(ValueError, match="positive integer"):
        read(
            tmp_path / "absent",
            expected_manifest_sha256="0" * 64,
            dataset_id=dataset_id,
            version="current",
        )


@pytest.mark.parametrize("mode", ["resource", "entity"])
@pytest.mark.parametrize("version", [True, None, "original", [], {}])
def test_invalid_version_refuses_before_archive_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str, version: object
) -> None:
    read = selected_api(mode)
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("archive opened"))
    with pytest.raises(ValueError, match="version"):
        read(
            tmp_path / "absent",
            expected_manifest_sha256="0" * 64,
            dataset_id=201,
            version=version,
        )


@pytest.mark.parametrize("flag", [1, None, "yes"])
def test_native_body_flag_is_literal_before_archive_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, flag: object
) -> None:
    read = selected_api("resource")
    monkeypatch.setattr(Path, "open", lambda *a, **k: pytest.fail("archive opened"))
    with pytest.raises(ValueError, match="literal boolean"):
        read(
            tmp_path / "absent",
            expected_manifest_sha256="0" * 64,
            dataset_id=201,
            version="current",
            include_native_body=flag,
        )


@pytest.mark.parametrize("mode", ["resource", "entity"])
def test_pending_archive_selection_refuses_without_any_body(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    read = selected_api(mode)
    root, pin, _ = make_archive(
        catalogue_sources, publish_catalogue, tmp_path, capture_resources=False
    )
    forbid_bodies(monkeypatch)
    with pytest.raises(ValueError, match="not qualified|complete successful"):
        read(root, expected_manifest_sha256=pin, dataset_id=201, version="current")


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_typed_archive_reader_uses_only_selected_numerical_body_after_sources_removed(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    version: str,
) -> None:
    read = selected_api("resource")
    root, pin, inputs = make_archive(catalogue_sources, publish_catalogue, tmp_path)
    capture = next(iter(inputs["resource_captures"].values()))
    expected = (capture / f"dataset-201-{version}-attempt-1.body").read_bytes()
    for index, path in enumerate(
        [*inputs["metadata_captures"].values(), *inputs["resource_captures"].values()]
    ):
        path.rename(tmp_path / f"detached-source-{index}")
    opened: list[str] = []
    native = Path.open

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.name.startswith("dataset-") and path.suffix == ".body":
            opened.append(path.name)
        return native(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    result = read(
        root,
        expected_manifest_sha256=pin,
        dataset_id=201,
        version=version,
        include_native_body=True,
    )
    assert opened == [f"dataset-201-{version}-attempt-1.body"]
    assert result["native_body"] == expected
    assert result["scientific_admission"] == "not_asserted"
    assert result["archive"]["manifest_sha256"] == pin
    assert (
        result["archive"]["integrity_scope"]
        == "archive_metadata_and_selected_source_entity"
    )
    assert result["archive"]["unselected_source_bodies_verified"] is False


@pytest.mark.parametrize("version", ["current", "doi_frozen"])
def test_forensic_archive_reader_keeps_unsupported_source_bytes_unadmitted(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    version: str,
) -> None:
    read = selected_api("entity")
    root, pin, _ = make_archive(
        catalogue_sources,
        publish_catalogue,
        tmp_path,
        auxiliary_type="unregistered native proxy",
    )
    result = read(root, expected_manifest_sha256=pin, dataset_id=202, version=version)
    assert result["acquisition_status"] in {
        "unsupported_dataset_type",
        "unresolved_frozen_schema",
    }
    assert result["native_body"] and "native_payload" not in result
    assert result["use_scope"] == "source_entity_download_only"
    assert result["scientific_admission"] == "not_asserted"
    if version == "current":
        with pytest.raises(ValueError, match="not qualified"):
            selected_api("resource")(
                root, expected_manifest_sha256=pin, dataset_id=202, version=version
            )
    else:
        snapshot = selected_api("resource")(
            root, expected_manifest_sha256=pin, dataset_id=202, version=version
        )
        assert snapshot["qualification_status"] == "parsed_frozen_snapshot"
        assert snapshot["scientific_admission"] == "not_asserted"


def test_current_derived_profile_and_json_default_preserve_original_ledger(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
) -> None:
    inputs = catalogue_sources(
        auxiliary_type="pollen surface sample",
        source_database="Native database",
        sample_metadata=[
            {
                "sampleid": 2011,
                "depth": None,
                "datum": [
                    {
                        "variablename": "Native datum",
                        "taxonid": None,
                        "element": None,
                        "elementtype": None,
                        "units": None,
                        "taxongroup": None,
                        "ecologicalgroup": None,
                        "context": None,
                        "symmetry": None,
                        "value": None,
                    }
                ],
            }
        ],
    )
    inputs["qualify_current_source_profiles"] = True
    root, pin, _ = make_archive(lambda **_: inputs, publish_catalogue, tmp_path)
    result = selected_api("resource")(
        root, expected_manifest_sha256=pin, dataset_id=202, version="current"
    )
    assert result["qualification_status"] == "parsed_current_source"
    assert result["source_terminal_status"] == "unsupported_dataset_type"
    assert result["scientific_admission"] == "not_asserted"
    assert "native_body" not in result
    json.dumps(result, allow_nan=False)
