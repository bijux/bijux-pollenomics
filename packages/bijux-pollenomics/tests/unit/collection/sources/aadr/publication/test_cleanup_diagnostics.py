"""Release recovery notes cannot replace an annotation builder failure."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.aadr import publication
from bijux_pollenomics.core.filesystem import OwnedTreeWriter


@pytest.mark.parametrize("site", ["receipt", "displaced", "retained"])
@pytest.mark.parametrize("diagnostics", ["ordinary", "annotation"])
def test_release_diagnostic_preserves_primary_and_owned_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, site: str, diagnostics: str
) -> None:
    """Each note boundary preserves the original candidate and foreign bytes."""
    prefix = {
        "receipt": "AADR refusal receipt failed:",
        "displaced": "AADR recovery originally allocated",
        "retained": "AADR recovery state retained",
    }[site]

    class Primary(OSError):
        def add_note(self, note: str) -> None:
            if diagnostics == "annotation" and note.startswith(prefix):
                raise RuntimeError("generated annotation failure")
            super().add_note(note)

    primary = Primary("generated release builder failure")
    real_write = OwnedTreeWriter.write_bytes

    def write(writer: OwnedTreeWriter, name: str, raw: bytes) -> None:
        if site == "receipt" and name == "failed-operation.json":
            raise OSError("generated receipt failure")
        real_write(writer, name, raw)

    monkeypatch.setattr(OwnedTreeWriter, "write_bytes", write)
    candidates: list[Path] = []
    foreign: list[Path] = []

    def build(writer: OwnedTreeWriter, manifest: publication.ManifestOutput) -> None:
        writer.write_bytes("panel/generated.anno", b"owned annotation fixture")
        if site == "displaced":
            run = writer.root.parent
            detached = run.with_name("detached-owned-release")
            run.rename(detached)
            run.mkdir()
            (run / "foreign").write_bytes(b"foreign owner")
            foreign.append(run)
            candidates.append(detached / "candidate")
        else:
            candidates.append(writer.root)
        raise primary

    output = tmp_path / "collection"
    with pytest.raises(Primary) as caught:
        publication.publish_release(
            output,
            "generated-release",
            names={"panel/generated.anno"},
            max_asset_bytes=1024,
            build=build,
            validate=lambda _: pytest.fail("Failed build cannot validate"),
        )
    assert caught.value is primary
    assert not (output / "generated-release").exists()
    assert (
        candidates[0] / "panel/generated.anno"
    ).read_bytes() == b"owned annotation fixture"
    if foreign:
        assert (foreign[0] / "foreign").read_bytes() == b"foreign owner"
    if diagnostics == "ordinary":
        assert any(note.startswith(prefix) for note in primary.__notes__)
    elif site == "receipt":
        assert any("recovery state retained" in note for note in primary.__notes__)
