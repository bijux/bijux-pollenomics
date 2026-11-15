"""Literal source replay does not authorize replacing the publisher's inode."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.context_resources import (
    NeotomaContextResourcePlan,
    capture_neotoma_context_resources,
)
from bijux_pollenomics.collection.sources.neotoma.publication import ownership

from .native_products import source_response


def test_equal_byte_capture_root_swap_is_refused(
    context_resource_inputs: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = context_resource_inputs()
    plan = NeotomaContextResourcePlan(
        (12,),
        inputs.pop("context_manifest_sha256"),
        inputs.pop("native_archive_manifest_sha256"),
        ("dataset_depositional_environment",),
    )
    final, saved = tmp_path / "capture", tmp_path / "owned-capture"
    publish = vars(ownership)["publish_new_output_tree"]
    calls = []

    def swapped(**kwargs: Path) -> None:
        publish(**kwargs)
        final.rename(saved)
        shutil.copytree(saved, final)
        calls.append(True)

    monkeypatch.setattr(ownership, "publish_new_output_tree", swapped)
    with pytest.raises(ValueError, match="identity|inode"):
        capture_neotoma_context_resources(
            final, plan=plan, fetch=source_response, **inputs
        )
    assert calls == [True]
    assert saved.stat().st_ino != final.stat().st_ino
    assert (saved / "capture-manifest.json").read_bytes() == (
        final / "capture-manifest.json"
    ).read_bytes()
