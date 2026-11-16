"""Each report callback publishes its own complete ordinary namespace."""

from __future__ import annotations

from pathlib import Path
import threading

import pytest

from bijux_pollenomics.reporting.bundles.staging import publish_into_staging_dir


@pytest.mark.parametrize("prior_present", [False, True])
def test_concurrent_return_belongs_to_published_writer(
    tmp_path: Path, prior_present: bool
) -> None:
    final = tmp_path / "report"
    if prior_present:
        final.mkdir()
        (final / "value.txt").write_text("PRIOR")
    first_written, second_written, first_finished = (
        threading.Event() for _ in range(3)
    )
    results: dict[str, object] = {}

    def first(stage: Path) -> str:
        (stage / "value.txt").write_text("FIRST")
        first_written.set()
        assert second_written.wait(10)
        return "FIRST"

    def second(stage: Path) -> str:
        (stage / "value.txt").write_text("SECOND")
        second_written.set()
        assert first_finished.wait(10)
        return "SECOND"

    def run(name: str, callback: object) -> None:
        try:
            assert callable(callback)
            results[name] = publish_into_staging_dir(final, callback)
        except BaseException as error:
            results[name] = error
        finally:
            if name == "first":
                first_finished.set()

    left = threading.Thread(target=run, args=("first", first))
    right = threading.Thread(target=run, args=("second", second))
    left.start()
    assert first_written.wait(10)
    right.start()
    left.join(15)
    right.join(15)
    assert not left.is_alive() and not right.is_alive()
    assert results["first"] == "FIRST"
    assert (final / "value.txt").read_text() == results["first"]
    assert isinstance(results["second"], (ValueError, FileExistsError))


def test_failing_callback_preserves_foreign_fixed_stage(tmp_path: Path) -> None:
    final, foreign = tmp_path / "report", tmp_path / ".report.staging"
    foreign.mkdir()
    marker = foreign / "foreign.txt"
    marker.write_text("must survive")

    def refuse(stage: Path) -> None:
        (stage / "partial.txt").write_text("partial")
        raise ValueError("generated callback refusal")

    with pytest.raises(ValueError, match="generated callback refusal"):
        publish_into_staging_dir(final, refuse)
    assert marker.read_text() == "must survive"
    assert not final.exists()


def test_callback_root_substitution_is_refused_without_foreign_deletion(
    tmp_path: Path,
) -> None:
    final, displaced = tmp_path / "report", tmp_path / "displaced-candidate"
    stages: list[Path] = []

    def substitute(stage: Path) -> str:
        stages.append(stage)
        (stage / "value.txt").write_text("FIRST")
        stage.rename(displaced)
        stage.mkdir()
        (stage / "foreign.txt").write_text("foreign")
        return "FIRST"

    with pytest.raises(ValueError):
        publish_into_staging_dir(final, substitute)
    assert (displaced / "value.txt").read_text() == "FIRST"
    assert (stages[0] / "foreign.txt").read_text() == "foreign"
    assert not final.exists()


def test_destination_appearing_during_callback_is_preserved(tmp_path: Path) -> None:
    final = tmp_path / "report"

    def compete(stage: Path) -> str:
        (stage / "value.txt").write_text("candidate")
        final.mkdir()
        (final / "foreign.txt").write_text("competing publication")
        return "candidate"

    with pytest.raises(ValueError):
        publish_into_staging_dir(final, compete)
    assert (final / "foreign.txt").read_text() == "competing publication"
    assert not (final / "value.txt").exists()


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_nonordinary_callback_member_preserves_prior(tmp_path: Path, kind: str) -> None:
    import os

    final = tmp_path / "report"
    final.mkdir()
    (final / "value.txt").write_text("complete prior")
    external = tmp_path / "external.txt"
    external.write_text("generated external")

    def publish(stage: Path) -> None:
        member = stage / "nonordinary"
        if kind == "symlink":
            member.symlink_to(external)
        elif kind == "hardlink":
            os.link(external, member)
        else:
            os.mkfifo(member)

    with pytest.raises(ValueError):
        publish_into_staging_dir(final, publish)
    assert (final / "value.txt").read_text() == "complete prior"
    assert external.read_text() == "generated external"


def test_nested_standalone_reports_keep_recovery_outside_published_namespace(
    tmp_path: Path,
) -> None:
    standalone = tmp_path / "standalone"
    standalone.mkdir()
    (standalone / ".git").mkdir()
    final = standalone / "report"

    def outer(stage: Path) -> str:
        nested = stage / "country"
        nested.mkdir()
        (nested / "value.txt").write_text("nested prior")

        def inner(candidate: Path) -> str:
            (candidate / "value.txt").write_text("nested current")
            return "inner"

        assert publish_into_staging_dir(nested, inner) == "inner"
        return "outer"

    assert publish_into_staging_dir(final, outer) == "outer"
    assert (final / "country/value.txt").read_text() == "nested current"
    assert {path.relative_to(final).as_posix() for path in final.rglob("*")} == {
        "country",
        "country/value.txt",
    }


def test_callback_cancellation_preserves_primary_and_prior(tmp_path: Path) -> None:
    class Cancelled(BaseException):
        pass

    final = tmp_path / "report"
    final.mkdir()
    (final / "value.txt").write_text("prior")
    primary = Cancelled("cancelled callback")
    stages: list[Path] = []

    def cancel(stage: Path) -> None:
        stages.append(stage)
        (stage / "partial.txt").write_text("partial")
        raise primary

    with pytest.raises(Cancelled) as error:
        publish_into_staging_dir(final, cancel)
    assert error.value is primary
    assert (final / "value.txt").read_text() == "prior"
    assert (stages[0] / "partial.txt").read_text() == "partial"


@pytest.mark.parametrize(
    "mutation", ["growth", "equal_inode", "child_inode", "empty_directory"]
)
def test_completed_candidate_seal_refuses_validation_mutation(
    tmp_path: Path, mutation: str
) -> None:
    final = tmp_path / "report"
    final.mkdir()
    (final / "value.txt").write_text("prior")

    def publish(stage: Path) -> None:
        (stage / "nested").mkdir()
        (stage / "nested/value.txt").write_text("candidate")

    def validate(root: Path) -> None:
        target = root / "nested/value.txt"
        assert target.read_text() == "candidate"
        if mutation == "growth":
            target.write_text("candidate grew")
        elif mutation == "equal_inode":
            replacement = root / "replacement"
            replacement.write_bytes(target.read_bytes())
            replacement.replace(target)
        elif mutation == "child_inode":
            saved = root.parent / "saved-child"
            target.parent.rename(saved)
            target.parent.mkdir()
            target.write_bytes((saved / "value.txt").read_bytes())
        else:
            (root / "foreign-empty-directory").mkdir()

    with pytest.raises(ValueError):
        publish_into_staging_dir(final, publish, validate=validate)
    assert (final / "value.txt").read_text() == "prior"


def test_noncanonical_member_name_is_refused_before_attachment(tmp_path: Path) -> None:
    final = tmp_path / "report"

    def publish(stage: Path) -> None:
        (stage / "not\\canonical").write_text("candidate")

    with pytest.raises(ValueError, match="canonical"):
        publish_into_staging_dir(final, publish)
    assert not final.exists()


def test_final_readback_failure_restores_prior_and_preserves_primary(
    tmp_path: Path,
) -> None:
    final = tmp_path / "report"
    final.mkdir()
    (final / "value.txt").write_text("prior")
    primary = ValueError("published readback refused")
    stages: list[Path] = []

    def publish(stage: Path) -> str:
        stages.append(stage)
        (stage / "value.txt").write_text("candidate")
        return "candidate"

    def validate(root: Path) -> None:
        assert (root / "value.txt").read_text() == "candidate"
        if root == final:
            raise primary

    with pytest.raises(ValueError) as error:
        publish_into_staging_dir(final, publish, validate=validate)
    assert error.value is primary
    assert (final / "value.txt").read_text() == "prior"
    assert (
        stages[0].parent / "refused-publication/value.txt"
    ).read_text() == "candidate"


def test_foreign_final_after_attachment_retains_predecessor_recovery(
    tmp_path: Path,
) -> None:
    final, saved = tmp_path / "report", tmp_path / "saved-candidate"
    final.mkdir()
    (final / "value.txt").write_text("prior")
    stages: list[Path] = []

    def publish(stage: Path) -> None:
        stages.append(stage)
        (stage / "value.txt").write_text("candidate")

    def validate(root: Path) -> None:
        assert (root / "value.txt").read_text() == "candidate"
        if root == final:
            final.rename(saved)
            final.mkdir()
            (final / "foreign.txt").write_text("foreign final")

    with pytest.raises(ValueError):
        publish_into_staging_dir(final, publish, validate=validate)
    assert (final / "foreign.txt").read_text() == "foreign final"
    assert (saved / "value.txt").read_text() == "candidate"
    assert (stages[0].parent / "prior/value.txt").read_text() == "prior"


def test_attachment_competitor_is_not_replaced_or_cleaned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.core.filesystem import replacement

    final = tmp_path / "report"
    final.mkdir()
    (final / "value.txt").write_text("prior")
    stages: list[Path] = []
    original = replacement._rename_directory

    def competing(
        descriptor: int,
        source: str,
        target: str,
        *,
        destination_descriptor: int | None = None,
    ) -> None:
        if source == "candidate" and target == final.name:
            final.mkdir()
            (final / "foreign.txt").write_text("foreign final")
        original(
            descriptor, source, target, destination_descriptor=destination_descriptor
        )

    def publish(stage: Path) -> None:
        stages.append(stage)
        (stage / "value.txt").write_text("candidate")

    monkeypatch.setattr(replacement, "_rename_directory", competing)
    with pytest.raises(FileExistsError):
        publish_into_staging_dir(final, publish)
    assert (final / "foreign.txt").read_text() == "foreign final"
    assert (stages[0] / "value.txt").read_text() == "candidate"
    assert (stages[0].parent / "prior/value.txt").read_text() == "prior"


def test_copied_callback_context_cannot_extend_nested_storage_lease(
    tmp_path: Path,
) -> None:
    from contextvars import copy_context

    contexts = []
    stages: list[Path] = []
    called: list[bool] = []

    def publish(stage: Path) -> None:
        stages.append(stage)
        contexts.append(copy_context())
        (stage / "value.txt").write_text("candidate")

    final = tmp_path / "report"
    publish_into_staging_dir(final, publish)

    def late(candidate: Path) -> None:
        called.append(True)
        (candidate / "late.txt").write_text("late")

    with pytest.raises(ValueError, match="workspace is unavailable"):
        contexts[0].run(publish_into_staging_dir, stages[0] / "late", late)
    assert called == []
    assert not stages[0].exists()
    assert (final / "value.txt").read_text() == "candidate"


def test_empty_directories_and_return_value_are_preserved(tmp_path: Path) -> None:
    final = tmp_path / "report"
    result = object()

    def publish(stage: Path) -> object:
        (stage / "empty/nested").mkdir(parents=True)
        (stage / "ordinary Ω.txt").write_text("candidate")
        return result

    assert publish_into_staging_dir(final, publish) is result
    assert (final / "empty/nested").is_dir()
    assert (final / "ordinary Ω.txt").read_text() == "candidate"


def test_destination_parent_replacement_is_refused(tmp_path: Path) -> None:
    parent, saved = tmp_path / "destination", tmp_path / "saved-parent"
    parent.mkdir()
    final = parent / "report"

    def publish(stage: Path) -> None:
        (stage / "value.txt").write_text("candidate")
        parent.rename(saved)
        parent.mkdir()
        (parent / "foreign.txt").write_text("foreign parent")

    with pytest.raises(ValueError, match="identity changed"):
        publish_into_staging_dir(final, publish)
    assert (parent / "foreign.txt").read_text() == "foreign parent"
    assert not final.exists()


def test_candidate_completion_is_metadata_only_and_input_seals_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.core.filesystem.regular_inputs import BoundedInputTree
    from bijux_pollenomics.reporting.bundles import staging

    final = tmp_path / "report"
    final.mkdir()
    (final / "value.txt").write_text("prior")
    trees: list[BoundedInputTree] = []
    reads: list[tuple[Path, str]] = []
    original_tree = staging._completed_report_tree
    original_read = BoundedInputTree._read

    def completed(root: Path) -> BoundedInputTree:
        tree = original_tree(root)
        trees.append(tree)
        return tree

    def read(
        self: BoundedInputTree, name: str, *, retain: bool, max_bytes: int | None = None
    ) -> bytes:
        reads.append((self.root, name))
        return original_read(self, name, retain=retain, max_bytes=max_bytes)

    def publish(stage: Path) -> None:
        (stage / "value.txt").write_text("candidate")

    monkeypatch.setattr(staging, "_completed_report_tree", completed)
    monkeypatch.setattr(BoundedInputTree, "_read", read)
    publish_into_staging_dir(final, publish)
    assert len(trees) == 2 and all(tree.anchor.fd == -1 for tree in trees)
    assert reads == [(final, "value.txt"), (trees[0].root, "value.txt")]
    assert trees[0].root.name == "prior"
    assert (final / "value.txt").read_text() == "candidate"


def test_new_public_parent_keeps_ordinary_creation_permissions(tmp_path: Path) -> None:
    import stat

    control = tmp_path / "ordinary"
    control.mkdir()
    final = tmp_path / "new-parent/report"

    def publish(stage: Path) -> None:
        assert stage.parent.stat().st_mode & 0o077 == 0
        (stage / "value.txt").write_text("candidate")

    publish_into_staging_dir(final, publish)
    assert stat.S_IMODE(final.parent.stat().st_mode) == stat.S_IMODE(
        control.stat().st_mode
    )
    assert stat.S_IMODE(final.stat().st_mode) == stat.S_IMODE(control.stat().st_mode)


def test_false_valued_validator_still_runs_before_attachment(tmp_path: Path) -> None:
    final = tmp_path / "report"

    class RefusingValidator:
        def __bool__(self) -> bool:
            return False

        def __call__(self, root: Path) -> None:
            assert (root / "value.txt").read_text() == "candidate"
            raise ValueError("semantic validation refused")

    def publish(stage: Path) -> None:
        (stage / "value.txt").write_text("candidate")

    with pytest.raises(ValueError, match="semantic validation refused"):
        publish_into_staging_dir(final, publish, validate=RefusingValidator())
    assert not final.exists()
