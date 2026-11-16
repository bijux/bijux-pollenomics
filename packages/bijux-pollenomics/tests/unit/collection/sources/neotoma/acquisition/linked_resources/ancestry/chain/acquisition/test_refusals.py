"""Source and finite-budget refusals precede authorized frontier acquisition."""

from dataclasses import replace
import json
import os
from pathlib import Path
from typing import Any

import pytest

from ..native_products import bindings, current_epoch
from .native_payloads import native_response
from .test_capture import capture_api


def body_opens(monkeypatch: Any) -> list[str]:
    original = os.open
    observed: list[str] = []

    def open_source(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        fd = original(path, flags, *args, **kwargs)
        name = Path(path).name
        if name.startswith(("taxon-", "publication-", "contact-")) and name.endswith(
            ".body"
        ):
            observed.append(name)
        return fd

    monkeypatch.setattr(os, "open", open_source)
    monkeypatch.setattr(os, "supports_dir_fd", os.supports_dir_fd | {open_source})
    return observed


@pytest.mark.parametrize(
    "keys",
    [
        (),
        ["taxon-15"],
        (True,),
        ("taxon-15", "taxon-15"),
        ("taxon-999",),
        ("taxon-015",),
        ("taxon-11",),
        ("contact-900",),
    ],
)
def test_invalid_or_foreign_selection_refuses_before_native_bodies_or_gets(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, keys: Any
) -> None:
    opened = body_opens(monkeypatch)
    calls: list[str] = []
    destination = tmp_path / "refused-selection"
    with pytest.raises(ValueError):
        capture_api()(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=keys,
            fetch=lambda url, **_: calls.append(url),
        )
    assert not calls and not opened and not destination.exists()


def test_stronger_incoming_root_duty_refuses_before_native_replay_or_get(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    context, context_pin, native, native_pin = current_epoch(
        chain_products, tmp_path / "stronger-current-source", "strengthen"
    )
    sources = bindings(
        chain_products,
        current_context_directory=context,
        expected_current_context_sha256=context_pin,
        current_native_archive_directory=native,
        expected_current_native_archive_sha256=native_pin,
    )
    opened = body_opens(monkeypatch)
    calls: list[str] = []
    destination = tmp_path / "protected-target"
    with pytest.raises(ValueError, match="protected"):
        capture_api()(
            destination,
            sources=sources,
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=lambda url, **_: calls.append(url),
        )
    assert not opened and not calls and not destination.exists()


def test_seed_relative_depth_bound_refuses_before_get(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        NeotomaTaxonAncestryChainLimits,
    )

    opened = body_opens(monkeypatch)
    calls: list[str] = []
    with pytest.raises(ValueError, match="bound"):
        capture_api()(
            tmp_path / "depth-refused",
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            limits=NeotomaTaxonAncestryChainLimits(max_additional_parent_hops=0),
            fetch=lambda url, **_: calls.append(url),
        )
    assert not calls and not opened


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("max_requests", True),
        ("max_requests", 17),
        ("max_requests", 0),
        ("max_requests", 1.5),
        ("max_total_response_bytes", 1),
        ("max_total_response_bytes", True),
        ("timeout_seconds", float("nan")),
        ("wall_seconds", float("inf")),
        ("wall_seconds", 0),
    ],
)
def test_operational_budget_refuses_before_source_bodies_or_gets(
    chain_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: Any,
    field: str,
    value: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
        NeotomaTaxonFrontierCaptureLimits,
    )

    opened = body_opens(monkeypatch)
    calls: list[str] = []
    with pytest.raises(ValueError):
        capture_api()(
            tmp_path / "budget-refused",
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            capture_limits=replace(
                NeotomaTaxonFrontierCaptureLimits(), **{field: value}
            ),
            fetch=lambda url, **_: calls.append(url),
        )
    assert not opened and not calls


def test_output_cannot_be_created_inside_consumed_source(
    chain_products: dict[str, Any], monkeypatch: Any
) -> None:
    sources = bindings(chain_products)
    before = sorted(
        path.name for path in sources.baseline_projection_directory.iterdir()
    )
    opened = body_opens(monkeypatch)
    calls: list[str] = []
    with pytest.raises(ValueError, match="overlaps"):
        capture_api()(
            sources.baseline_projection_directory / "capture",
            sources=sources,
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=lambda url, **_: calls.append(url),
        )
    assert not opened and not calls
    assert (
        sorted(path.name for path in sources.baseline_projection_directory.iterdir())
        == before
    )


@pytest.mark.parametrize("change", ["roster", "resolver"])
def test_source_drift_during_get_refuses_before_retaining_body(
    chain_products: dict[str, Any], tmp_path: Path, change: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
        load_neotoma_ancillary_context,
    )

    sources = bindings(chain_products)
    context = load_neotoma_ancillary_context(
        sources.current_context_directory,
        expected_manifest_sha256=sources.expected_current_context_sha256,
        native_archive_directory=sources.current_native_archive_directory,
    )
    roster = next(iter(context.current_scope_inputs.values())).roster_path
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        if change == "roster":
            roster.write_bytes(roster.read_bytes())
        else:
            sources.recorded_baseline_sources.capture_sources.clear()
        return native_response(chain_products, url, **kwargs)

    destination = tmp_path / "drift-refused"
    with pytest.raises(ValueError, match="changed"):
        capture_api()(
            destination,
            sources=sources,
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=fetch,
        )
    assert len(calls) == 1 and not destination.exists()
    refusals = list(tmp_path.glob("*/refusal.json"))
    assert len(refusals) == 1
    assert json.loads(refusals[0].read_text())["request_count"] == 1
    assert not list(refusals[0].parent.glob("*.body"))


def test_wall_expiry_during_get_retains_refusal_instead_of_closed_capture(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:

    clock = [0.0]
    import time

    monkeypatch.setattr(time, "monotonic", lambda: clock[0])
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        clock[0] = 901
        return native_response(chain_products, url, **kwargs)

    destination = tmp_path / "expired-capture"
    with pytest.raises(TimeoutError, match="wall budget"):
        capture_api()(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=fetch,
        )
    assert len(calls) == 1 and not destination.exists()


def test_caller_budget_validator_cannot_disable_finite_profile(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
        NeotomaTaxonFrontierCaptureLimits,
    )

    class UnboundedCallerLimits(NeotomaTaxonFrontierCaptureLimits):
        def validate(self, target_count: int) -> None:
            pass

    calls: list[float] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(kwargs["timeout"])
        return native_response(chain_products, url)

    with pytest.raises(ValueError, match="limit type"):
        capture_api()(
            tmp_path / "caller-limits",
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            capture_limits=UnboundedCallerLimits(
                timeout_seconds=600, wall_seconds=10000
            ),
            fetch=fetch,
        )
    assert not calls


def test_caller_graph_limits_cannot_raise_frozen_seed_depth_bound(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain import (
        NeotomaTaxonAncestryChainLimits,
    )

    class UnboundedGraphLimits(NeotomaTaxonAncestryChainLimits):
        def validate(self) -> None:
            pass

    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return native_response(chain_products, url)

    with pytest.raises(ValueError, match="limit type"):
        capture_api()(
            tmp_path / "caller-graph-limits",
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            limits=UnboundedGraphLimits(max_additional_parent_hops=999),
            fetch=fetch,
        )
    assert not calls


def test_manifest_budget_is_proved_before_any_get_or_output(
    chain_products: dict[str, Any], tmp_path: Path, monkeypatch: Any
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
        workflow,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition.planning import (
        prepare_targets,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.authority import (
        ChainOperation,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.models import (
        DEFAULT_LIMITS,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    sources = bindings(chain_products)
    with ChainOperation(sources) as operation:
        _, plan = prepare_targets(
            operation, None, ("taxon-15",), DEFAULT_LIMITS, native_replay=False
        )
    monkeypatch.setattr(workflow, "MAX_CONTROL_BYTES", len(encoded_json(plan)) + 32)
    calls: list[str] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append(url)
        return native_response(chain_products, url, **kwargs)

    destination = tmp_path / "manifest-budget"
    with pytest.raises(ValueError, match="metadata bound"):
        capture_api()(
            destination,
            sources=sources,
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=fetch,
        )
    assert not calls and not destination.exists()
    assert not (tmp_path / ".manifest-budget.staging").exists()


def test_declared_oversized_source_mapping_refuses_without_iteration(
    chain_products: dict[str, Any], tmp_path: Path
) -> None:
    from collections.abc import Iterator, Mapping

    class OversizedSources(Mapping[str, Path]):
        def __len__(self) -> int:
            return 10001

        def __iter__(self) -> Iterator[str]:
            raise AssertionError("Oversized source mapping was iterated")

        def __getitem__(self, key: str) -> Path:
            raise AssertionError("Oversized source mapping was resolved")

    sources = bindings(chain_products)
    recorded = replace(
        sources.recorded_baseline_sources, capture_sources=OversizedSources()
    )
    sources = replace(sources, recorded_baseline_sources=recorded)
    with pytest.raises(ValueError, match="source resolver"):
        capture_api()(
            tmp_path / "oversized-sources",
            sources=sources,
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=lambda url, **_: pytest.fail("No GET permitted"),
        )


@pytest.mark.parametrize("destination_kind", ["source", "outside", "alias"])
def test_noncanonical_output_refuses_before_native_replay_or_creation(
    chain_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: Any,
    destination_kind: str,
) -> None:
    sources = bindings(chain_products)
    outside = tmp_path / "outside"
    outside.mkdir()
    if destination_kind == "source":
        destination = (
            outside / ".." / sources.baseline_projection_directory.name / "capture"
        )
    elif destination_kind == "outside":
        destination = outside / ".." / "new-capture"
    else:
        alias = tmp_path / "aliased-parent"
        alias.symlink_to(outside, target_is_directory=True)
        destination = alias / "capture"
    before = {path.relative_to(tmp_path) for path in tmp_path.rglob("*")}
    opened = body_opens(monkeypatch)
    calls: list[str] = []
    with pytest.raises(ValueError):
        capture_api()(
            destination,
            sources=sources,
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=lambda url, **_: calls.append(url),
        )
    assert not opened and not calls
    assert {path.relative_to(tmp_path) for path in tmp_path.rglob("*")} == before
