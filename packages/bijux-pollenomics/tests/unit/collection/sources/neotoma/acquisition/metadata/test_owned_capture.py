from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataPlan,
    NeotomaMetadataResponse,
    capture_neotoma_metadata,
)
from bijux_pollenomics.core.owned_tree import build_staging_output_dir

from .native_responses import response


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
@pytest.mark.parametrize("transport_failure", [False, True])
def test_metadata_attempt_never_writes_into_a_replaced_staging_root(
    tmp_path: Path, replacement: str, transport_failure: bool
) -> None:
    output = tmp_path / "capture"
    staging = build_staging_output_dir(output)
    original = tmp_path / "original-owned-stage"
    foreign = tmp_path / "another-writer"
    foreign.mkdir()
    marker = foreign / "preserve"
    marker.write_bytes(b"another writer owns this entry")

    def fetch(url: str, **_: object) -> NeotomaMetadataResponse:
        assert (staging / "request-plan.json").is_file()
        staging.rename(original)
        if replacement == "symlink":
            staging.symlink_to(foreign, target_is_directory=True)
        else:
            foreign.rename(staging)
        if transport_failure:
            raise TimeoutError("provider request failed after staging replacement")
        return response(url)

    with pytest.raises((ValueError, OSError)):
        capture_neotoma_metadata(
            output, plan=NeotomaMetadataPlan(site_ids=(12,)), fetch=fetch
        )

    foreign_root = foreign if replacement == "symlink" else staging
    assert sorted(path.name for path in foreign_root.iterdir()) == ["preserve"]
    assert (foreign_root / "preserve").read_bytes() == b"another writer owns this entry"
    assert sorted(path.name for path in original.iterdir()) == ["request-plan.json"]
    assert not output.exists()


def test_owned_json_receipts_preserve_existing_serialization(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import (
        _write_json,
    )
    from bijux_pollenomics.core.filesystem import OwnedTreeWriter

    payload = {"source": "native–entity", "nested": [None, 12, 0.25, False]}
    legacy = tmp_path / "existing-wire.json"
    expected_digest = _write_json(legacy, payload)
    root = tmp_path / "owned"
    with OwnedTreeWriter(root, max_bytes=4096, max_files=2) as writer:
        digest = _write_json(root / "receipt.json", payload, writer=writer)
        assert digest == expected_digest
        assert (root / "receipt.json").read_bytes() == legacy.read_bytes()
        foreign = tmp_path / "unowned.json"
        with pytest.raises(ValueError):
            _write_json(foreign, payload, writer=writer)
        assert not foreign.exists()
