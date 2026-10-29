"""Import source-custody consumers without launching tools or copying source trees."""

from __future__ import annotations

import importlib
import shutil
import subprocess

import pytest


@pytest.mark.parametrize(
    ("module", "entrypoint"),
    [
        ("controlled_numerical.love_objective", "validated_love_objective_capture"),
        ("lake_registry.neotoma_lake", "validated_neotoma_lake_capture"),
        ("lake_registry.svar_census", "validated_svar_feature_census_capture"),
        ("land_use.hyde_grid", "validated_hyde_grid_source_captures"),
        ("land_use.openland_members", "validated_openland_member_capture"),
        ("pollen_source.amsoldingersee", "validated_amsoldingersee_capture"),
        ("pollen_source.neotoma_publication", "validated_neotoma_publication_capture"),
        (
            "pollen_source.swedish_direct_pollen",
            "validated_swedish_direct_pollen_capture",
        ),
        (
            "vegetation_reference.empd2_nfi_pairing",
            "validated_empd2_nfi_pairing_capture",
        ),
    ],
)
def test_source_consumer_import_does_not_launch_tools_or_copy_inputs(
    monkeypatch: pytest.MonkeyPatch, module: str, entrypoint: str
) -> None:
    def forbidden(*args: object, **kwargs: object) -> object:
        raise AssertionError("Import attempted a tool launch or source-copy operation")

    for attribute in ("run", "check_output", "Popen"):
        monkeypatch.setattr(subprocess, attribute, forbidden)
    monkeypatch.setattr(shutil, "copytree", forbidden)
    monkeypatch.setattr(shutil, "copyfile", forbidden)
    imported = importlib.import_module(
        "bijux_pollenomics_dev.ci.report_rebuild.scientific_captures." + module
    )
    assert callable(getattr(imported, entrypoint))
