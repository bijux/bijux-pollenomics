"""Generated callbacks challenge the collection publication ownership contract."""

from __future__ import annotations

from pathlib import Path
import shutil
from threading import Event, Thread
from typing import Any

import pytest

from bijux_pollenomics.collection.workflow.materialization import staging
from bijux_pollenomics.core.filesystem.replacement import publish_owned_replacement


def test_foreign_fixed_stage_is_preserved(tmp_path: Path) -> None:
    final = tmp_path / "collected"
    foreign = staging.build_staging_output_dir(final)
    foreign.mkdir()
    sentinel = foreign / "foreign-sentinel.txt"
    sentinel.write_text("PRESERVE FOREIGN STAGE")

    def collect(root: Path) -> str:
        (root / "value.txt").write_text("owned candidate")
        return "owned candidate"

    staging.collect_into_staging_dir(final, collect)
    assert sentinel.exists(), "Collector deleted a preexisting stage it did not own"
    assert sentinel.read_text() == "PRESERVE FOREIGN STAGE"


def test_success_result_belongs_to_its_published_callback(tmp_path: Path) -> None:
    final = tmp_path / "collected"
    first_ready, second_ready, release_second = Event(), Event(), Event()
    first_done = Event()
    results: dict[str, tuple[str, str]] = {}
    errors: dict[str, BaseException] = {}

    def first_callback(root: Path) -> str:
        (root / "value.txt").write_text("FIRST")
        first_ready.set()
        assert second_ready.wait(5), "second callback did not reach schedule"
        return "FIRST"

    def second_callback(root: Path) -> str:
        (root / "value.txt").write_text("SECOND")
        second_ready.set()
        assert release_second.wait(5), "first publisher did not complete"
        return "SECOND"

    def run(name: str, callback: Any) -> None:
        try:
            result = staging.collect_into_staging_dir(final, callback)
            results[name] = (result, (final / "value.txt").read_text())
        except BaseException as error:
            errors[name] = error
        finally:
            if name == "first":
                first_done.set()

    first = Thread(target=run, args=("first", first_callback))
    second = Thread(target=run, args=("second", second_callback))
    first.start()
    assert first_ready.wait(5)
    second.start()
    try:
        assert first_done.wait(5), "first publisher stalled"
    finally:
        release_second.set()
        first.join(5)
        second.join(5)
    assert not first.is_alive() and not second.is_alive()
    assert results.get("first") == ("FIRST", "FIRST"), (
        "A success returned FIRST while publishing SECOND",
        results,
        errors,
    )


def test_destination_parent_replacement_cannot_authorize_foreign_namespace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path / "owner"
    parent.mkdir()
    final = parent / "collected"
    retained = tmp_path / "original-parent"
    real_replace = publish_owned_replacement
    stages: list[Path] = []

    def replace_after_parent_swap(*args: Any, **kwargs: Any) -> Any:
        parent.rename(retained)
        parent.mkdir()
        final.mkdir()
        (final / "foreign-sentinel.txt").write_text("PRESERVE FOREIGN FINAL")
        foreign_stage = staging.build_staging_output_dir(final)
        foreign_stage.mkdir()
        (foreign_stage / "value.txt").write_text("FOREIGN STAGE")
        return real_replace(*args, **kwargs)

    monkeypatch.setattr(staging, "publish_owned_replacement", replace_after_parent_swap)

    def collect(root: Path) -> str:
        stages.append(root)
        (root / "value.txt").write_text("OWNED CANDIDATE")
        return "OWNED CANDIDATE"

    with pytest.raises((ValueError, OSError)):
        staging.collect_into_staging_dir(final, collect)
    owned = stages[0]
    if owned.is_relative_to(parent):
        owned = retained / owned.relative_to(parent)
    assert (owned / "value.txt").read_text() == "OWNED CANDIDATE"
    assert (final / "foreign-sentinel.txt").exists(), (
        "Publication entered a replacement parent and deleted its foreign final"
    )
    assert (final / "foreign-sentinel.txt").read_text() == "PRESERVE FOREIGN FINAL"


def test_cleanup_alias_refusal_preserves_primary_callback_error(tmp_path: Path) -> None:
    final = tmp_path / "collected"
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    sentinel = foreign / "sentinel.txt"
    sentinel.write_text("PRESERVE")
    primary = RuntimeError("original callback failure")

    def collect(root: Path) -> None:
        (root / "partial.txt").write_text("owned partial")
        shutil.rmtree(root)
        root.symlink_to(foreign, target_is_directory=True)
        raise primary

    caught = None
    try:
        staging.collect_into_staging_dir(final, collect)
    except BaseException as error:
        caught = error
    assert sentinel.read_text() == "PRESERVE"
    assert caught is primary, f"Cleanup masked the primary callback failure: {caught!r}"
