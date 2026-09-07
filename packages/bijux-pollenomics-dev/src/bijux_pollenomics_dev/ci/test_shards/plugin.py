"""Partition the already selected pytest universe without changing markers."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
import json
import os
from pathlib import Path

import pytest

from . import shard_for


@dataclass
class ShardState:
    """Retain collection and execution identities for the final receipt."""

    universe: list[str]
    selected: list[str]
    completed: set[str] = field(default_factory=set)


_STATE = pytest.StashKey[ShardState]()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Expose explicit partition and artifact options."""
    group = parser.getgroup("bijux test partitions")
    group.addoption("--bijux-shard-index", type=int, default=0)
    group.addoption("--bijux-shard-count", type=int, default=1)
    group.addoption("--bijux-shard-receipt", type=Path, default=None)


@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Shard only after pytest has applied the existing selection contract."""
    count = config.getoption("bijux_shard_count")
    index = config.getoption("bijux_shard_index")
    if count < 1 or not 0 <= index < count:
        raise pytest.UsageError("shard index must be within the positive shard count")
    universe = sorted(item.nodeid for item in items)
    if len(universe) != len(set(universe)):
        raise pytest.UsageError("test collection contains duplicate node IDs")
    selected = [item for item in items if shard_for(item.nodeid, count) == index]
    deselected = [item for item in items if shard_for(item.nodeid, count) != index]
    config.stash[_STATE] = ShardState(
        universe, sorted(item.nodeid for item in selected)
    )
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    items[:] = selected


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(
    item: pytest.Item, nextitem: pytest.Item | None
) -> Iterator[None]:
    """Mark a test complete only after its entire pytest protocol returns."""
    yield
    item.config.stash[_STATE].completed.add(item.nodeid)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Write a compact receipt; do not upload temporary fixture trees."""
    config = session.config
    destination = config.getoption("bijux_shard_receipt")
    if destination is None:
        return
    destination = Path(destination).resolve()
    try:
        destination.relative_to(Path(config.rootpath).resolve() / "artifacts")
    except ValueError as error:
        raise pytest.UsageError(
            "shard receipts must be beneath repository artifacts"
        ) from error
    state = config.stash.get(_STATE, ShardState([], []))
    payload = {
        "schema_version": "pytest-shard-receipt.v1",
        "revision": os.environ.get("GITHUB_SHA", "local-unattested"),
        "index": config.getoption("bijux_shard_index"),
        "count": config.getoption("bijux_shard_count"),
        "exit_code": int(exitstatus),
        "collection_only": bool(config.option.collectonly),
        "universe": state.universe,
        "selected": state.selected,
        "completed": sorted(state.completed),
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
