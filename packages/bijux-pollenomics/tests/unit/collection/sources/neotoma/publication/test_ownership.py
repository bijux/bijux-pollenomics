"""Equal content cannot substitute for an open publisher's directory ownership."""

from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from bijux_pollenomics.collection.sources.neotoma.publication import ownership
from bijux_pollenomics.core.filesystem import OwnedTreeWriter


def replace_equal(root: Path) -> Path:
    detached = root.with_name(root.name + "-detached")
    root.rename(detached)
    shutil.copytree(detached, root)
    assert (root / "source").read_bytes() == (detached / "source").read_bytes()
    return detached


def test_publishes_owned_inode_and_returns_final_validation(tmp_path: Path) -> None:
    staging, final = tmp_path / "staging", tmp_path / "final"
    calls = []
    with OwnedTreeWriter(staging, max_bytes=100, max_files=1) as writer:
        writer.write_bytes("source", b"retained source")
        inode = staging.stat().st_ino

        def validate(root: Path) -> Path:
            assert (root / "source").read_bytes() == b"retained source"
            calls.append(root)
            return root

        result = ownership.publish_owned_source_tree(
            writer, staging=staging, final=final, validate=validate
        )
        assert writer._root_fd >= 0
    assert result == final
    assert calls == [staging, final]
    assert final.stat().st_ino == inode
    assert not staging.exists()


@pytest.mark.parametrize(
    "moment", ["stage_validation", "attachment", "rename", "final_validation"]
)
def test_rejects_equal_byte_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, moment: str
) -> None:
    staging, final = tmp_path / "staging", tmp_path / "final"
    detached = []
    publish = vars(ownership)["publish_new_output_tree"]
    publications = []
    with OwnedTreeWriter(staging, max_bytes=100, max_files=1) as writer:
        writer.write_bytes("source", b"retained source")
        attachment = writer.validate_attachment
        attachment_calls = 0

        def check_attachment() -> None:
            nonlocal attachment_calls
            attachment()
            attachment_calls += 1
            if moment == "attachment" and attachment_calls == 1:
                detached.append(replace_equal(staging))

        monkeypatch.setattr(writer, "validate_attachment", check_attachment)

        def validate(root: Path) -> bytes:
            raw = (root / "source").read_bytes()
            assert raw == b"retained source"
            if (root == staging and moment == "stage_validation") or (
                root == final and moment == "final_validation"
            ):
                detached.append(replace_equal(root))
            return raw

        def swap_publish(**kwargs: Path) -> None:
            if moment == "rename":
                detached.append(replace_equal(staging))
            publications.append(kwargs)
            publish(**kwargs)

        monkeypatch.setattr(ownership, "publish_new_output_tree", swap_publish)
        with pytest.raises(ValueError, match="identity|inode"):
            ownership.publish_owned_source_tree(
                writer, staging=staging, final=final, validate=validate
            )
    assert len(detached) == 1
    assert (detached[0] / "source").read_bytes() == b"retained source"
    survivor = final if final.exists() else staging
    assert (survivor / "source").read_bytes() == b"retained source"
    assert bool(publications) == (moment in {"rename", "final_validation"})


def test_refuses_wrong_or_closed_writer(tmp_path: Path) -> None:
    staging, final = tmp_path / "staging", tmp_path / "final"
    with OwnedTreeWriter(staging, max_bytes=100, max_files=1) as writer:
        writer.write_bytes("source", b"retained source")
        with pytest.raises(ValueError):
            ownership.publish_owned_source_tree(
                writer,
                staging=tmp_path / "foreign",
                final=final,
                validate=lambda _: None,
            )
    with pytest.raises(ValueError, match="closed"):
        ownership.publish_owned_source_tree(
            writer, staging=staging, final=final, validate=lambda _: None
        )
    assert staging.exists() and not final.exists()


def test_existing_destination_and_validation_failure_preserve_evidence(
    tmp_path: Path,
) -> None:
    staging, final = tmp_path / "staging", tmp_path / "final"
    final.mkdir()
    (final / "foreign").write_bytes(b"another owner")
    with OwnedTreeWriter(staging, max_bytes=100, max_files=1) as writer:
        writer.write_bytes("source", b"retained source")
        with pytest.raises(FileExistsError):
            ownership.publish_owned_source_tree(
                writer, staging=staging, final=final, validate=lambda _: None
            )
        assert (staging / "source").read_bytes() == b"retained source"
        assert (final / "foreign").read_bytes() == b"another owner"

        def refuse(_: Path) -> None:
            raise ValueError("invalid source")

        with pytest.raises(ValueError, match="invalid source"):
            ownership.publish_owned_source_tree(
                writer, staging=staging, final=tmp_path / "absent", validate=refuse
            )
    assert staging.exists()
