"""Final session checks retain live permissions without a redundant first scan."""

from collections.abc import Callable, Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context.seals import (
    _CurrentContextSeals,
)
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.session import (
    _LinkedEvidenceSession,
)
from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read
from bijux_pollenomics.core.filesystem import BoundedInputTree

from .native_products import observe_work, session_arguments
from .test_scope import inputs


class DriftingResolver(Mapping[str, Path]):
    """Keep exact source paths while changing permission metadata during comparison."""

    def __init__(self, values: Mapping[str, Path], mutate: Callable[[], None]) -> None:
        self._values = values
        self.mutate = mutate
        self.changed = False

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterator[str]:
        if not self.changed:
            self.changed = True
            self.mutate()
        return iter(self._values)

    def __getitem__(self, key: str) -> Path:
        return self._values[key]


@pytest.mark.parametrize("full", [False, True])
def test_one_final_tree_check_preserves_outer_current_guard(
    session_products: dict[str, Any], monkeypatch: Any, full: bool
) -> None:
    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    current_calls: list[bool] = []
    with _CurrentContextSeals(
        context_directory=owner.context_directory,
        expected_context_sha256=owner.expected_context_sha256,
        native_archive_directory=owner.native_archive_directory,
        expected_native_archive_sha256=owner.expected_native_archive_sha256,
    ) as current:

        def before_body() -> None:
            current.check()
            current_calls.append(True)

        arguments["_before_body_read"] = before_body
        with _LinkedEvidenceSession(**arguments) as session:
            current_calls.clear()
            observed: list[int] = []
            original = BoundedInputTree.check
            owned = {id(tree) for tree in session._trees.values()}
            expected = {
                id(tree)
                for tree in (session._trees.values() if full else session._permissions)
            }

            def check(tree: BoundedInputTree) -> None:
                if id(tree) in owned:
                    observed.append(id(tree))
                original(tree)

            with monkeypatch.context() as capture:
                capture.setattr(BoundedInputTree, "check", check)
                session.check(**inputs(arguments), full=full)
            assert current_calls == [True]
            assert set(observed) == expected
            assert len(observed) == len(expected)


@pytest.mark.parametrize("replacement", [False, True])
def test_resolver_comparison_drift_refuses_before_next_real_body(
    session_products: dict[str, Any], monkeypatch: Any, replacement: bool
) -> None:
    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    scope = next(iter(arguments["scope_inputs"].values()))
    permission = scope.roster_path
    body = next(
        path
        for root in owner.capture_sources.values()
        for path in root.glob("taxon-*.body")
    )
    work = observe_work(monkeypatch)
    mutated: list[bool] = []

    def change() -> None:
        raw = permission.read_bytes()
        if replacement:
            other = permission.with_suffix(".replacement")
            other.write_bytes(raw)
            other.replace(permission)
        else:
            permission.write_bytes(raw)
        mutated.append(True)

    supplied = {
        **inputs(arguments),
        "source_facets": DriftingResolver(owner.source_facets, change),
    }
    with (
        pytest.raises(ValueError, match="changed"),
        _LinkedEvidenceSession(**arguments) as session,
    ):
        before = work["native_detail_opens"]
        session.check(**supplied)
        _read(body, body.stat().st_size)
    assert mutated == [True]
    assert work["native_detail_opens"] == before
