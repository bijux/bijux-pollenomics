"""Replacement retains exact predecessors while publishing only owned candidates."""

from pathlib import Path

from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from bijux_pollenomics.core.filesystem.anchors import DirectoryAnchor
from bijux_pollenomics.core.filesystem.regular_inputs import BoundedInputTree
from bijux_pollenomics.core.filesystem.replacement import publish_owned_replacement


def test_valid_replacement_retains_prior_and_final_readback(tmp_path: Path) -> None:
    final, run = tmp_path / "output", tmp_path / "run"
    final.mkdir()
    (final / "value").write_bytes(b"prior")
    run.mkdir()
    with (
        BoundedInputTree(final, max_bytes=100, max_files=2) as prior,
        DirectoryAnchor(run) as recovery,
        OwnedTreeWriter(run / "candidate", max_bytes=100, max_files=2) as writer,
    ):
        writer.write_bytes("value", b"candidate")
        seen: list[Path] = []

        def validate(root: Path) -> bytes:
            seen.append(root)
            return (root / "value").read_bytes()

        assert (
            publish_owned_replacement(
                writer, final=final, prior=prior, recovery=recovery, validate=validate
            )
            == b"candidate"
        )
        assert seen == [run / "candidate", final]
    assert (run / "prior" / "value").read_bytes() == b"prior"
    assert (final / "value").read_bytes() == b"candidate"
