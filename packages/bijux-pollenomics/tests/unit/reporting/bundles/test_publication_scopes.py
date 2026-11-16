"""Callback and attachment authorities survive ordinary thread handoffs."""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Any

import pytest

from bijux_pollenomics.core.filesystem.replacement import publish_owned_replacement
from bijux_pollenomics.reporting.bundles import staging


def test_joined_worker_uses_outer_recovery_without_inherited_context(
    tmp_path: Path,
) -> None:
    standalone = tmp_path / "standalone"
    standalone.mkdir()
    (standalone / ".git").mkdir()
    final = standalone / "report"
    results: list[object] = []

    def outer(candidate: Path) -> str:
        child = candidate / "child"
        child.mkdir()
        (child / "value.txt").write_text("PRIVATE PREDECESSOR")

        def worker() -> None:
            try:
                results.append(
                    staging.publish_into_staging_dir(
                        child,
                        lambda root: (root / "value.txt").write_text("PUBLIC CURRENT"),
                    )
                )
            except BaseException as error:
                results.append(error)

        thread = threading.Thread(target=worker)
        thread.start()
        thread.join(10)
        assert not thread.is_alive() and len(results) == 1
        assert not isinstance(results[0], BaseException)
        return "outer"

    assert staging.publish_into_staging_dir(final, outer) == "outer"
    assert (final / "child/value.txt").read_text() == "PUBLIC CURRENT"
    assert {p.relative_to(final).as_posix() for p in final.rglob("*")} == {
        "child",
        "child/value.txt",
    }


def test_parent_authority_is_checked_inside_replacement_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent, saved = tmp_path / "destination", tmp_path / "saved-parent"
    parent.mkdir()
    final = parent / "report"
    original = publish_owned_replacement
    stages: list[Path] = []

    def substitute(writer: Any, **options: Any) -> Any:
        parent.rename(saved)
        parent.mkdir()
        (parent / "foreign.txt").write_text("FOREIGN OWNER")
        return original(writer, **options)

    def publish(stage: Path) -> str:
        stages.append(stage)
        (stage / "value.txt").write_text("CANDIDATE")
        return "candidate"

    monkeypatch.setattr(staging, "publish_owned_replacement", substitute)
    with pytest.raises((ValueError, OSError)):
        staging.publish_into_staging_dir(final, publish)
    assert (parent / "foreign.txt").read_text() == "FOREIGN OWNER"
    assert not final.exists()
    assert (stages[0] / "value.txt").read_text() == "CANDIDATE"


@pytest.mark.parametrize("prior_present", [False, True])
def test_incomplete_child_publication_refuses_outer_commit(
    tmp_path: Path, prior_present: bool
) -> None:
    standalone = tmp_path / "standalone"
    standalone.mkdir()
    (standalone / ".git").mkdir()
    final = standalone / "report"
    if prior_present:
        final.mkdir()
        (final / "complete.txt").write_text("COMPLETE PRIOR")
    ready, release = threading.Event(), threading.Event()
    threads: list[threading.Thread] = []
    results: list[object] = []

    def outer(candidate: Path) -> None:
        child = candidate / "child"
        child.mkdir()
        (child / "value.txt").write_text("PRIVATE PREDECESSOR")

        def partial(stage: Path) -> str:
            (stage / "value.txt").write_text("INCOMPLETE CHILD")
            ready.set()
            assert release.wait(10)
            return "child"

        def worker() -> None:
            try:
                results.append(staging.publish_into_staging_dir(child, partial))
            except BaseException as error:
                results.append(error)

        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
        assert ready.wait(10)

    try:
        with pytest.raises(ValueError, match="incomplete child"):
            staging.publish_into_staging_dir(final, outer)
    finally:
        release.set()
        for thread in threads:
            thread.join(15)
    assert all(not thread.is_alive() for thread in threads)
    if prior_present:
        assert {p.relative_to(final).as_posix() for p in final.rglob("*")} == {
            "complete.txt"
        }
        assert (final / "complete.txt").read_text() == "COMPLETE PRIOR"
    else:
        assert not final.exists()


def test_moved_active_callback_root_cannot_start_nested_publication(
    tmp_path: Path,
) -> None:
    standalone = tmp_path / "standalone"
    standalone.mkdir()
    (standalone / ".git").mkdir()
    final, saved = standalone / "report", standalone / "displaced-candidate"
    results: list[object] = []

    def outer(candidate: Path) -> None:
        child = candidate / "child"
        child.mkdir()
        (child / "value.txt").write_text("EXISTING CHILD")
        candidate.rename(saved)

        def worker() -> None:
            try:
                results.append(
                    staging.publish_into_staging_dir(
                        saved / "child",
                        lambda root: (root / "value.txt").write_text("CURRENT"),
                    )
                )
            except BaseException as error:
                results.append(error)

        thread = threading.Thread(target=worker)
        try:
            thread.start()
            thread.join(10)
            assert not thread.is_alive() and len(results) == 1
            assert isinstance(results[0], (ValueError, OSError))
        finally:
            saved.rename(candidate)

    staging.publish_into_staging_dir(final, outer)
    assert (final / "child/value.txt").read_text() == "EXISTING CHILD"
    assert {p.relative_to(final).as_posix() for p in final.rglob("*")} == {
        "child",
        "child/value.txt",
    }


def _attempt_joined_worker(destination: Path) -> tuple[object, list[bool]]:
    results: list[object] = []
    called: list[bool] = []

    def publish(candidate: Path) -> str:
        called.append(True)
        (candidate / "value.txt").write_text("LATE WORKER")
        return "published"

    def worker() -> None:
        try:
            results.append(staging.publish_into_staging_dir(destination, publish))
        except BaseException as error:
            results.append(error)

    thread = threading.Thread(target=worker)
    thread.start()
    thread.join(10)
    assert not thread.is_alive() and len(results) == 1
    return results[0], called


def test_closed_child_authority_precedes_active_outer_scope(tmp_path: Path) -> None:
    final = tmp_path / "report"
    probes: list[tuple[object, list[bool]]] = []

    def outer(candidate: Path) -> None:
        child = candidate / "child"

        def validate(root: Path) -> None:
            if root == child:
                result, called = _attempt_joined_worker(root / "late")
                probes.append((result, called))
                assert isinstance(result, (ValueError, OSError)) and called == []

        staging.publish_into_staging_dir(
            child,
            lambda root: (root / "value.txt").write_text("CHILD"),
            validate=validate,
        )

    staging.publish_into_staging_dir(final, outer)
    assert len(probes) == 1
    assert {path.relative_to(final).as_posix() for path in final.rglob("*")} == {
        "child",
        "child/value.txt",
    }


def test_moved_child_identity_precedes_active_outer_scope(tmp_path: Path) -> None:
    final = tmp_path / "report"
    probes: list[tuple[object, list[bool]]] = []

    def outer(stage: Path) -> None:
        def inner(candidate: Path) -> None:
            (candidate / "value.txt").write_text("CHILD")
            moved = stage / "moved-child-root"
            candidate.rename(moved)
            try:
                result, called = _attempt_joined_worker(moved / "late")
                probes.append((result, called))
                assert isinstance(result, (ValueError, OSError)) and called == []
            finally:
                moved.rename(candidate)

        staging.publish_into_staging_dir(stage / "child", inner)

    staging.publish_into_staging_dir(final, outer)
    assert len(probes) == 1
    assert {path.relative_to(final).as_posix() for path in final.rglob("*")} == {
        "child",
        "child/value.txt",
    }
