"""Capture the exact historical LandClim receipt against its current successor."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics.core.filesystem import BoundedInputTree, read_regular_file

_PREDECESSOR = "eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677"
_SUCCESSOR = "c2a34ecfc5fc83a811b9a7d84eb3ff4d44edce403f1c06d3de9cc43048ddf80e"
_RECEIPT = "landclim_sources.json"
_CONTRIBUTOR = "landclim_ii_contributors.xlsx"


def capture_predecessor_assets(
    raw_dir: Path, predecessor_receipt: Path
) -> dict[str, bytes]:
    """Capture the known eight-file successor and its exact seven-file predecessor.

    This only establishes byte correspondence for these two named receipt epochs;
    it does not establish rights or scientific admission.
    """
    predecessor = read_regular_file(predecessor_receipt, max_bytes=65536)
    if hashlib.sha256(predecessor).hexdigest() != _PREDECESSOR:
        raise ValueError("LandClim predecessor receipt digest differs")
    old = json.loads(predecessor)
    with BoundedInputTree(raw_dir, max_bytes=16_000_000, max_files=9) as tree:
        receipt = tree.read(tree.root / _RECEIPT, max_bytes=65536)
        if hashlib.sha256(receipt).hexdigest() != _SUCCESSOR:
            raise ValueError("LandClim current receipt digest differs")
        current = json.loads(receipt)
        old_assets = {row["filename"]: row for row in old["assets"]}
        current_assets = {row["filename"]: row for row in current["assets"]}
        if (
            len(old_assets) != 7
            or len(current_assets) != 8
            or set(current_assets) != set(old_assets) | {_CONTRIBUTOR}
            or any(current_assets[name] != row for name, row in old_assets.items())
            or set(tree.files) != set(current_assets) | {_RECEIPT}
        ):
            raise ValueError(
                "LandClim predecessor and current asset inventories differ"
            )
        captured = {}
        for name, row in current_assets.items():
            raw = tree.read(tree.root / name, max_bytes=row["size_bytes"])
            if (
                len(raw) != row["size_bytes"]
                or hashlib.sha256(raw).hexdigest() != row["sha256"]
            ):
                raise ValueError(f"LandClim current asset digest differs: {name}")
            captured[name] = raw
        tree.check()
    return captured
