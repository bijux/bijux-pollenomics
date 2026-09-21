"""Missing, broken and incompatible engines remain explicit refusals."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib import metadata
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

import pytest

from bijux_pollenomics.analysis.lra.api import LRARefusal
from bijux_pollenomics.analysis.lra.engine import discovery
from bijux_pollenomics.analysis.lra.engine.discovery import (
    LANDCLIM_ANALYTICAL_LOVE_CAPABILITY,
    MULTISITE_DRAW_LOVE_CAPABILITY,
    MULTISITE_PUBLICATION_CAPABILITY,
    load_engine,
)


class StubAPI(ModuleType):
    extension_descriptor: Callable[[], dict[str, object]]


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


def _selected(distribution: SimpleNamespace, api: StubAPI, capability: str) -> None:
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
    ):
        assert load_engine(required_capability=capability).api is api


@pytest.mark.parametrize(
    "capability",
    [
        MULTISITE_PUBLICATION_CAPABILITY,
        LANDCLIM_ANALYTICAL_LOVE_CAPABILITY,
        MULTISITE_DRAW_LOVE_CAPABILITY,
    ],
)
def test_old_descriptor_retains_default_contract_but_refuses_selected_feature(
    capability: str,
) -> None:
    distribution, api = _installed()
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
    ):
        assert load_engine().api is api
        with pytest.raises(LRARefusal) as raised:
            load_engine(required_capability=capability)
    assert raised.value.reason_code == "lra_extension_capability_unavailable"
    assert capability in str(raised.value)


def test_multisite_capability_requires_actual_callable_and_typed_facade() -> None:
    distribution, api = _installed()
    api.extension_descriptor()["capabilities"] = [MULTISITE_PUBLICATION_CAPABILITY]
    api.run_reveals_multisite = lambda *args: None
    api.MultisiteRevealsInput = type("MultisiteRevealsInput", (), {})
    api.PublicationRevealsConfig = type("PublicationRevealsConfig", (), {})
    api.MultisiteRevealsResult = type(
        "MultisiteRevealsResult", (), {"write": lambda self, path: path}
    )
    _selected(distribution, api, MULTISITE_PUBLICATION_CAPABILITY)
    delattr(api, "MultisiteRevealsInput")
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
        pytest.raises(LRARefusal) as raised,
    ):
        load_engine(required_capability=MULTISITE_PUBLICATION_CAPABILITY)
    assert raised.value.reason_code == "lra_extension_capability_invalid"


def test_draw_capability_requires_typed_source_and_bounds_identity() -> None:
    distribution, api = _installed()
    api.extension_descriptor()["capabilities"] = [MULTISITE_DRAW_LOVE_CAPABILITY]
    api.RegionalCoverDrawSource = type(
        "RegionalCoverDrawSource",
        (),
        {"from_verified_member": classmethod(lambda cls, **kwargs: cls())},
    )
    api.run_love_from_regional_draws = lambda *args: None
    api.publication_bin_bounds_sha256 = lambda bounds: "0" * 64
    _selected(distribution, api, MULTISITE_DRAW_LOVE_CAPABILITY)
    delattr(api, "publication_bin_bounds_sha256")
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
        pytest.raises(LRARefusal) as raised,
    ):
        load_engine(required_capability=MULTISITE_DRAW_LOVE_CAPABILITY)
    assert raised.value.reason_code == "lra_extension_capability_invalid"


@dataclass
class _NamedLoveConfig:
    method: str
    regional_basin_type: str
    regional_basin_diameter_m: float
    local_basin_diameter_m: float
    max_ring: int
    distance_weighting: str
    fall_speed_profile: str
    repeats: int
    stochastic: bool

    def as_dict(self) -> dict[str, object]:
        return {"fall_speed_profile": self.fall_speed_profile}


def _draw_aware_love(*args: object, regional_cover_draws: object) -> None:
    del args, regional_cover_draws


def test_named_love_capability_requires_profile_aware_configuration() -> None:
    distribution, api = _installed()
    api.extension_descriptor()["capabilities"] = [LANDCLIM_ANALYTICAL_LOVE_CAPABILITY]
    api.LoveConfig = _NamedLoveConfig
    api.run_love = _draw_aware_love
    _selected(distribution, api, LANDCLIM_ANALYTICAL_LOVE_CAPABILITY)
    api.LoveConfig = type("OldLoveConfig", (), {})
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
        pytest.raises(LRARefusal) as raised,
    ):
        load_engine(required_capability=LANDCLIM_ANALYTICAL_LOVE_CAPABILITY)
    assert raised.value.reason_code == "lra_extension_capability_invalid"


def test_broken_advertised_named_profile_is_structured_refusal() -> None:
    distribution, api = _installed()
    api.extension_descriptor()["capabilities"] = [LANDCLIM_ANALYTICAL_LOVE_CAPABILITY]
    api.run_love = _draw_aware_love

    @dataclass
    class BrokenConfig(_NamedLoveConfig):
        def as_dict(self) -> dict[str, object]:
            raise RuntimeError("broken optional configuration")

    api.LoveConfig = BrokenConfig
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
        pytest.raises(LRARefusal) as raised,
    ):
        load_engine(required_capability=LANDCLIM_ANALYTICAL_LOVE_CAPABILITY)
    assert raised.value.reason_code == "lra_extension_capability_invalid"


def test_named_love_capability_refuses_missing_regional_draw_keyword() -> None:
    distribution, api = _installed()
    api.extension_descriptor()["capabilities"] = [LANDCLIM_ANALYTICAL_LOVE_CAPABILITY]
    api.LoveConfig = _NamedLoveConfig
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
        pytest.raises(LRARefusal) as raised,
    ):
        load_engine(required_capability=LANDCLIM_ANALYTICAL_LOVE_CAPABILITY)
    assert raised.value.reason_code == "lra_extension_capability_invalid"


def test_unhashable_requested_capability_is_structured_refusal() -> None:
    distribution, api = _installed()
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
        pytest.raises(LRARefusal) as raised,
    ):
        load_engine(required_capability=[])  # type: ignore[arg-type]
    assert raised.value.reason_code == "lra_extension_capability_unknown"


def test_optional_capability_inventory_is_strict_only_on_selected_path() -> None:
    distribution, api = _installed()
    api.extension_descriptor()["capabilities"] = [
        MULTISITE_PUBLICATION_CAPABILITY,
        MULTISITE_PUBLICATION_CAPABILITY,
    ]
    with (
        patch.object(metadata, "distribution", return_value=distribution),
        patch.object(discovery, "import_module", return_value=api),
    ):
        assert load_engine().api is api
        with pytest.raises(LRARefusal) as raised:
            load_engine(required_capability=MULTISITE_PUBLICATION_CAPABILITY)
    assert raised.value.reason_code == "lra_extension_capability_invalid"
