"""Missing, broken and incompatible engines remain explicit refusals."""

from __future__ import annotations

from collections.abc import Callable
from importlib import metadata
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra.api import LRARefusal
from bijux_pollenomics.analysis.lra.engine import discovery
from bijux_pollenomics.analysis.lra.engine.discovery import load_engine


class StubAPI(ModuleType):
    extension_descriptor: Callable[[], dict[str, str]]


def _installed() -> tuple[SimpleNamespace, StubAPI]:
    distribution = SimpleNamespace(
        version="0.2.0",
        entry_points=[
            metadata.EntryPoint(
                name="lra", group=discovery.GROUP, value=discovery.TARGET
            )
        ],
    )
    api = StubAPI(discovery.API_MODULE)
    descriptor = {
        "schema_version": "1.0.0",
        "distribution": discovery.DISTRIBUTION,
        "version": "0.2.0",
        "python_api": discovery.API_MODULE,
        "extension_group": discovery.GROUP,
        "extension_name": "lra",
        "extension_target": discovery.TARGET,
        "numerical_backend": "python-numpy-scipy",
    }
    api.extension_descriptor = lambda: descriptor
    for name in discovery.OPERATIONS:
        setattr(api, name, lambda *args: None)
    return distribution, api


def test_missing_extension_has_actionable_reason_without_importing_it() -> None:
    with (
        patch.object(
            metadata,
            "distribution",
            side_effect=metadata.PackageNotFoundError,
        ),
        patch.object(discovery, "import_module") as importer,
        pytest.raises(LRARefusal) as raised,
    ):
        load_engine()
    assert raised.value.reason_code == "lra_extension_missing"
    assert "bijux-pollenomics[lra]" in str(raised.value)
    importer.assert_not_called()


def test_binding_records_actual_installed_identity() -> None:
    distribution, api = _installed()
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
    ):
        binding = load_engine()
    assert binding.api is api
    assert binding.as_dict()["numerical_backend"] == "python-numpy-scipy"
    assert binding.version == distribution.version


@pytest.mark.parametrize(
    "failure",
    [
        "duplicate_entry",
        "wrong_target",
        "wrong_version",
        "wrong_backend",
        "missing_operation",
    ],
)
def test_incompatible_installs_do_not_select_a_fallback(failure: str) -> None:
    distribution, api = _installed()
    if failure == "duplicate_entry":
        distribution.entry_points *= 2
    elif failure == "wrong_target":
        distribution.entry_points = [
            metadata.EntryPoint(
                name="lra", group=discovery.GROUP, value="untrusted:entry"
            )
        ]
    elif failure == "wrong_version":
        api.extension_descriptor()["version"] = "0+unknown"
    elif failure == "wrong_backend":
        api.extension_descriptor()["numerical_backend"] = "silently-replaced"
    else:
        delattr(api, "run_lra")
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
        pytest.raises(LRARefusal, match="incompatible"),
    ):
        load_engine()


def test_missing_binary_dependency_is_broken_install_not_absent_extra() -> None:
    distribution, _ = _installed()
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(
            discovery,
            "import_module",
            side_effect=ImportError("native dependency failed"),
        ),
        pytest.raises(LRARefusal) as raised,
    ):
        load_engine()
    assert raised.value.as_dict()["reason_code"] == "lra_extension_broken"
