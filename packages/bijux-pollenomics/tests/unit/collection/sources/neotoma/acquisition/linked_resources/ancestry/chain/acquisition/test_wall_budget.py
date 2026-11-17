"""Keep explicit wall extensions finite without bypassing native preparation."""

from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, NoReturn

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition import (
    NeotomaTaxonFrontierCaptureLimits,
    workflow,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.ancestry.chain.acquisition.planning import (
    prepare_targets,
)

from ..native_products import bindings
from .native_payloads import native_response
from .test_refusals import body_opens


def _consume_preparation_time(
    monkeypatch: pytest.MonkeyPatch, elapsed: float
) -> list[bool]:
    """Advance only the workflow clock after real generated native preparation."""
    clock = [0.0]
    phases: list[bool] = []
    original = prepare_targets

    def prepare(*args: Any, **kwargs: Any) -> Any:
        result = original(*args, **kwargs)
        phases.append(kwargs["native_replay"])
        if kwargs["native_replay"]:
            clock[0] = elapsed
        return result

    monkeypatch.setattr(workflow, "time", SimpleNamespace(monotonic=lambda: clock[0]))
    monkeypatch.setattr(workflow, "prepare_targets", prepare)
    return phases


@pytest.mark.parametrize(
    ("wall_seconds", "preparation_seconds", "request_timeout"),
    [(900.5, 900.25, 0.25), (3600.0, 901.0, 60.0)],
)
def test_explicit_wall_budget_survives_native_preparation_above_default(
    chain_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    wall_seconds: float,
    preparation_seconds: float,
    request_timeout: float,
) -> None:
    phases = _consume_preparation_time(monkeypatch, preparation_seconds)
    calls: list[tuple[str, dict[str, Any]]] = []

    def fetch(url: str, **kwargs: Any) -> Any:
        calls.append((url, kwargs))
        return native_response(chain_products, url)

    limits = NeotomaTaxonFrontierCaptureLimits(wall_seconds=wall_seconds)
    assert limits.max_requests == 16
    assert limits.max_total_response_bytes == 16 * (2 * 1024 * 1024 + 1)
    assert limits.timeout_seconds == 60
    destination = tmp_path / "explicit-wall-capture"
    result = workflow.capture_neotoma_taxon_ancestry_frontier(
        destination,
        sources=bindings(chain_products),
        parent_chain_sha256=None,
        target_keys=("taxon-15",),
        capture_limits=limits,
        fetch=fetch,
    )
    assert phases == [False, True]
    assert calls == [
        (
            "https://api.neotomadb.org/v2.0/data/taxa/15",
            {"max_bytes": 2 * 1024 * 1024, "timeout": request_timeout},
        )
    ]
    assert result.directory == destination and result.request_count == 1
    manifest = json.loads((destination / "capture-manifest.json").read_bytes())
    assert manifest["scientific_admission"] == "not_asserted"
    assert manifest["request_count"] == 1


@pytest.mark.parametrize("preparation_seconds", [900.0, 901.0])
def test_default_wall_budget_still_refuses_after_native_preparation(
    chain_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    preparation_seconds: float,
) -> None:
    assert NeotomaTaxonFrontierCaptureLimits().wall_seconds == 900
    phases = _consume_preparation_time(monkeypatch, preparation_seconds)
    calls: list[str] = []

    def unexpected_fetch(url: str, **_: Any) -> NoReturn:
        calls.append(url)
        raise AssertionError("Exhausted default wall budget reached transport")

    destination = tmp_path / "default-wall-refusal"
    with pytest.raises(TimeoutError, match="wall budget exhausted"):
        workflow.capture_neotoma_taxon_ancestry_frontier(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            fetch=unexpected_fetch,
        )
    assert phases == [False, True]
    assert not calls and not destination.exists()


@pytest.mark.parametrize(
    "wall_seconds",
    [
        True,
        False,
        float("nan"),
        float("inf"),
        -float("inf"),
        0,
        -1,
        3600.1,
        3601,
        10**400,
    ],
    ids=[
        "true",
        "false",
        "nan",
        "infinite",
        "negative-infinite",
        "exhausted",
        "expired",
        "above-ceiling",
        "above-integer-ceiling",
        "oversized-integer",
    ],
)
def test_invalid_or_exhausted_wall_budget_refuses_before_native_io(
    chain_products: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    wall_seconds: Any,
) -> None:
    opened = body_opens(monkeypatch)
    calls: list[str] = []

    def unexpected_fetch(url: str, **_: Any) -> NoReturn:
        calls.append(url)
        raise AssertionError("Invalid wall budget reached transport")

    destination = tmp_path / "invalid-wall-refusal"
    with pytest.raises(ValueError, match="finite positive time limits"):
        workflow.capture_neotoma_taxon_ancestry_frontier(
            destination,
            sources=bindings(chain_products),
            parent_chain_sha256=None,
            target_keys=("taxon-15",),
            capture_limits=replace(
                NeotomaTaxonFrontierCaptureLimits(), wall_seconds=wall_seconds
            ),
            fetch=unexpected_fetch,
        )
    assert not opened and not calls and not destination.exists()
