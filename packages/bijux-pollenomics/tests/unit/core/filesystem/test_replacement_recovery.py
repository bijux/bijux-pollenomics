"""Competing destination entries remain in place during publication and recovery."""

from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.core.filesystem import OwnedTreeWriter, replacement
from bijux_pollenomics.core.filesystem.anchors import DirectoryAnchor
from bijux_pollenomics.core.filesystem.regular_inputs import BoundedInputTree


def test_failure_receipt_preserves_primary_validation_error(tmp_path: Path) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    run.mkdir()
    primary = OSError("primary semantic validation failure")

    def validate(root: Path) -> None:
        raise primary

    def record(status: str, fields: dict[str, Any]) -> None:
        raise ValueError("secondary receipt namespace failure")

    with (
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        with pytest.raises(OSError) as caught:
            replacement.publish_owned_replacement(
                writer,
                final=final,
                prior=None,
                recovery=recovery,
                validate=validate,
                record=record,
            )
        assert caught.value is primary
        assert any(
            "secondary receipt namespace failure" in note for note in primary.__notes__
        )
        assert (run / "candidate/value").read_bytes() == b"candidate"
        assert not final.exists()


@pytest.mark.parametrize("existing", [False, True])
def test_foreign_empty_destination_at_publication_is_never_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: bool
) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    run.mkdir()
    if existing:
        final.mkdir()
        (final / "value").write_bytes(b"prior")
    prior = BoundedInputTree(final, max_bytes=100, max_files=2) if existing else None
    primitive = replacement._rename_directory
    inode: list[int] = []

    def competing(parent: int, source: str, target: str, **kwargs: Any) -> None:
        if source == "candidate":
            final.mkdir()
            inode.append(final.stat().st_ino)
        primitive(parent, source, target, **kwargs)

    try:
        with (
            DirectoryAnchor(run) as recovery,
            OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
        ):
            writer.write_bytes("value", b"candidate")
            monkeypatch.setattr(replacement, "_rename_directory", competing)
            with pytest.raises(FileExistsError):
                replacement.publish_owned_replacement(
                    writer,
                    final=final,
                    prior=prior,
                    recovery=recovery,
                    validate=lambda root: None,
                )
            assert final.stat().st_ino == inode[0]
            assert list(final.iterdir()) == []
    finally:
        if prior is not None:
            prior.close()
    if existing:
        assert (run / "prior" / "value").read_bytes() == b"prior"


@pytest.mark.parametrize("existing", [False, True])
def test_foreign_final_substitution_stays_at_user_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, existing: bool
) -> None:
    import os

    final, run = tmp_path / "output", tmp_path / "run"
    run.mkdir()
    if existing:
        final.mkdir()
        (final / "value").write_bytes(b"prior")
    prior = BoundedInputTree(final, max_bytes=100, max_files=2) if existing else None
    primitive = replacement._rename_directory
    observed: list[int] = []

    def substituted(parent: int, source: str, target: str, **kwargs: Any) -> None:
        primitive(parent, source, target, **kwargs)
        if source == "candidate":
            os.rename(final, tmp_path / "authored-displaced")
            final.mkdir()
            (final / "foreign").write_bytes(b"keep user content")
            observed.append(final.stat().st_ino)

    try:
        with (
            DirectoryAnchor(run) as recovery,
            OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
        ):
            writer.write_bytes("value", b"candidate")
            monkeypatch.setattr(replacement, "_rename_directory", substituted)
            with pytest.raises(ValueError, match="identity"):
                replacement.publish_owned_replacement(
                    writer,
                    final=final,
                    prior=prior,
                    recovery=recovery,
                    validate=lambda root: None,
                )
            assert final.stat().st_ino == observed[0]
            assert (final / "foreign").read_bytes() == b"keep user content"
            assert not (run / "refused-publication").exists()
    finally:
        if prior is not None:
            prior.close()
    if existing:
        assert (run / "prior" / "value").read_bytes() == b"prior"


@pytest.mark.parametrize("failure", ["prior_move", "candidate_move", "readback"])
def test_failed_publication_restores_complete_prior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    final.mkdir()
    (final / "value").write_bytes(b"prior")
    run.mkdir()
    primitive = replacement._rename_directory

    def refused(parent: int, source: str, target: str, **kwargs: Any) -> None:
        if (failure == "prior_move" and source == "output") or (
            failure == "candidate_move" and source == "candidate"
        ):
            raise OSError("synthetic rename refusal")
        primitive(parent, source, target, **kwargs)

    def validate(root: Path) -> None:
        if failure == "readback" and root == final:
            raise OSError("synthetic final readback refusal")

    with (
        BoundedInputTree(final, max_bytes=100, max_files=2) as prior,
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        monkeypatch.setattr(replacement, "_rename_directory", refused)
        with pytest.raises(OSError, match="synthetic"):
            replacement.publish_owned_replacement(
                writer, final=final, prior=prior, recovery=recovery, validate=validate
            )
        assert (final / "value").read_bytes() == b"prior"
        assert not (run / "prior").exists()


def test_recovery_collision_preserves_foreign_entry_and_current_prior(
    tmp_path: Path,
) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    final.mkdir()
    (final / "value").write_bytes(b"prior")
    (run / "prior").mkdir(parents=True)
    (run / "prior" / "foreign").write_bytes(b"user")
    with (
        BoundedInputTree(final, max_bytes=100, max_files=2) as prior,
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        with pytest.raises(FileExistsError):
            replacement.publish_owned_replacement(
                writer,
                final=final,
                prior=prior,
                recovery=recovery,
                validate=lambda root: None,
            )
    assert (run / "prior" / "foreign").read_bytes() == b"user"
    assert (final / "value").read_bytes() == b"prior"


@pytest.mark.parametrize("change", ["directory", "leaf"])
def test_receipt_callback_cannot_make_a_foreign_final_successful(
    tmp_path: Path, change: str
) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    final.mkdir()
    (final / "value").write_bytes(b"prior")
    run.mkdir()
    foreign: list[int] = []

    def record(status: str, fields: dict[str, Any]) -> None:
        if status == "published":
            if change == "directory":
                final.rename(tmp_path / "authored-displaced")
                final.mkdir()
            (final / "foreign").write_bytes(b"user content")
            foreign.append(final.stat().st_ino)

    with (
        BoundedInputTree(final, max_bytes=100, max_files=2) as prior,
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        with pytest.raises(ValueError):
            replacement.publish_owned_replacement(
                writer,
                final=final,
                prior=prior,
                recovery=recovery,
                validate=lambda root: None,
                record=record,
            )
    assert final.stat().st_ino == foreign[0]
    assert (final / "foreign").read_bytes() == b"user content"
    assert (run / "prior" / "value").read_bytes() == b"prior"


@pytest.mark.parametrize("fault", ["restore", "refused_candidate", "prior_check"])
@pytest.mark.parametrize("primary_type", [OSError, KeyboardInterrupt])
def test_recovery_fault_preserves_primary_and_all_owned_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fault: str,
    primary_type: type[BaseException],
) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    final.mkdir()
    (final / "value").write_bytes(b"prior")
    run.mkdir()
    primary = primary_type("primary final validation")
    secondary = OSError("secondary recovery fault")
    failed = False
    primitive = replacement._rename_directory

    def rename(parent: int, source: str, target: str, **kwargs: Any) -> None:
        if failed and (
            (fault == "restore" and source == "prior")
            or (fault == "refused_candidate" and target == "refused-publication")
        ):
            raise secondary
        primitive(parent, source, target, **kwargs)

    def validate(root: Path) -> None:
        nonlocal failed
        if root == final:
            failed = True
            raise primary

    with (
        BoundedInputTree(final, max_bytes=100, max_files=2) as prior,
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        original_check = prior.validate

        def check_prior() -> None:
            if failed and fault == "prior_check":
                raise secondary
            original_check()

        monkeypatch.setattr(prior, "validate", check_prior)
        monkeypatch.setattr(replacement, "_rename_directory", rename)
        with pytest.raises(primary_type) as caught:
            replacement.publish_owned_replacement(
                writer, final=final, prior=prior, recovery=recovery, validate=validate
            )
        assert caught.value is primary
        assert any("secondary recovery fault" in note for note in primary.__notes__)
        assert (run / "prior/value").read_bytes() == b"prior"
        candidate = (
            final if fault == "refused_candidate" else run / "refused-publication"
        )
        assert (candidate / "value").read_bytes() == b"candidate"


def test_displaced_recovery_keeps_primary_without_claiming_foreign_ownership(
    tmp_path: Path,
) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    run.mkdir()
    primary = OSError("primary final validation")
    displaced = tmp_path / "displaced-owned-recovery"

    def validate(root: Path) -> None:
        if root == final:
            run.rename(displaced)
            run.mkdir()
            (run / "foreign").write_bytes(b"user work")
            raise primary

    with (
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        with pytest.raises(OSError) as caught:
            replacement.publish_owned_replacement(
                writer, final=final, prior=None, recovery=recovery, validate=validate
            )
        assert caught.value is primary
        assert (final / "value").read_bytes() == b"candidate"
        assert (run / "foreign").read_bytes() == b"user work"
        assert displaced.is_dir()
        assert any(
            "recovery originally allocated" in note for note in primary.__notes__
        )
        assert any("expected directory identity" in note for note in primary.__notes__)


def test_failed_receipt_does_not_claim_its_replaced_recovery_path(
    tmp_path: Path,
) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    run.mkdir()
    primary = OSError("primary validation")
    displaced = tmp_path / "displaced-owned-recovery"

    def validate(root: Path) -> None:
        raise primary

    def record(status: str, fields: dict[str, Any]) -> None:
        run.rename(displaced)
        run.mkdir()
        (run / "foreign").write_bytes(b"user work")
        raise PermissionError("receipt cannot be written")

    with (
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        with pytest.raises(OSError) as caught:
            replacement.publish_owned_replacement(
                writer,
                final=final,
                prior=None,
                recovery=recovery,
                validate=validate,
                record=record,
            )
        assert caught.value is primary
        assert (displaced / "candidate/value").read_bytes() == b"candidate"
        assert (run / "foreign").read_bytes() == b"user work"
        assert any("expected directory identity" in note for note in primary.__notes__)
        assert not any(
            f"retained recovery: {run}" in note for note in primary.__notes__
        )
