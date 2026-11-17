"""Collection and report callbacks share one physical publication scope."""

from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Any

import pytest

from bijux_pollenomics.collection.workflow.materialization import staging
from bijux_pollenomics.reporting.bundles import staging as reports


@pytest.mark.parametrize("outer_collection", [False, True])
def test_joined_mixed_callbacks_keep_child_recovery_outside_output(
    tmp_path: Path, outer_collection: bool
) -> None:
    standalone = tmp_path / "standalone"
    standalone.mkdir()
    (standalone / ".git").mkdir()
    final = standalone / "collected"
    outer_publish = (
        staging.collect_into_staging_dir
        if outer_collection
        else reports.publish_into_staging_dir
    )
    child_publish = (
        reports.publish_into_staging_dir
        if outer_collection
        else staging.collect_into_staging_dir
    )
    results: list[Any] = []

    def outer(root: Path) -> str:
        child = root / "child"
        child.mkdir()
        (child / "value.txt").write_text("PRIVATE PREDECESSOR")

        def collect(candidate: Path) -> str:
            (candidate / "value.txt").write_text("PUBLIC CURRENT")
            return "child"

        def worker() -> None:
            try:
                results.append(child_publish(child, collect))
            except BaseException as error:
                results.append(error)

        thread = Thread(target=worker)
        thread.start()
        thread.join(10)
        assert not thread.is_alive()
        assert results == ["child"]
        return "outer"

    assert outer_publish(final, outer) == "outer"
    assert (final / "child/value.txt").read_text() == "PUBLIC CURRENT"
    assert {path.relative_to(final).as_posix() for path in final.rglob("*")} == {
        "child",
        "child/value.txt",
    }


def test_closed_report_child_cannot_borrow_outer_collection_lease(
    tmp_path: Path,
) -> None:
    final = tmp_path / "collected"
    attempts: list[BaseException] = []
    calls: list[Path] = []

    def outer(candidate: Path) -> None:
        child = candidate / "child"

        def late(root: Path) -> None:
            calls.append(root)
            (root / "unexpected.txt").write_text("MUST NOT RUN")

        def validate(root: Path) -> None:
            if root != child:
                return

            def worker() -> None:
                try:
                    staging.collect_into_staging_dir(child / "late", late)
                except BaseException as error:
                    attempts.append(error)

            thread = Thread(target=worker)
            thread.start()
            thread.join(10)
            assert not thread.is_alive()

        reports.publish_into_staging_dir(
            child,
            lambda root: (root / "current.txt").write_text("CURRENT"),
            validate=validate,
        )

    staging.collect_into_staging_dir(final, outer)
    assert calls == []
    assert len(attempts) == 1 and isinstance(attempts[0], ValueError)
    assert (final / "child/current.txt").read_text() == "CURRENT"
    assert not (final / "child/late").exists()


@pytest.mark.parametrize("kind", ["directory", "file", "symlink", "dangling"])
def test_legacy_recovery_refuses_before_callback(tmp_path: Path, kind: str) -> None:
    final = tmp_path / "collected"
    recovery = tmp_path / ".collected.recovery"
    if kind == "directory":
        recovery.mkdir()
    elif kind == "file":
        recovery.write_text("RECOVERY")
    else:
        target = tmp_path / "target"
        if kind == "symlink":
            target.mkdir()
        recovery.symlink_to(target, target_is_directory=True)
    calls: list[Path] = []
    with pytest.raises(FileExistsError, match="recovery requires review"):
        staging.collect_into_staging_dir(final, lambda root: calls.append(root))
    assert calls == []


def test_recovery_appearing_during_callback_blocks_attachment(tmp_path: Path) -> None:
    final = tmp_path / "collected"
    final.mkdir()
    (final / "complete.txt").write_text("COMPLETE PRIOR")
    recovery = tmp_path / ".collected.recovery"

    def collect(root: Path) -> str:
        (root / "new.txt").write_text("CANDIDATE")
        recovery.mkdir()
        (recovery / "retained.txt").write_text("EXTERNAL RECOVERY")
        return "candidate"

    with pytest.raises(FileExistsError, match="recovery requires review"):
        staging.collect_into_staging_dir(final, collect)
    assert (final / "complete.txt").read_text() == "COMPLETE PRIOR"
    assert (recovery / "retained.txt").read_text() == "EXTERNAL RECOVERY"
