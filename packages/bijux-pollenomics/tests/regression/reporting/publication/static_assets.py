from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)


def read_static_atlas_payload_text(output_dir: Path, slug: str) -> str:
    manifest = json.loads(
        (output_dir / f"{slug}_map_assets.json").read_text(encoding="utf-8")
    )
    payloads: list[str] = []
    for row in normalize_asset_inventory(manifest["assets"]):
        script = (output_dir / row["path"]).read_text(encoding="utf-8")
        envelope = json.loads(script[script.index(".push(") + 6 : -3])
        payloads.append(
            gzip.decompress(base64.b64decode(envelope["payload_gzip_base64"])).decode(
                "utf-8"
            )
            if envelope.get("payload_encoding") == "gzip_base64"
            else envelope["payload_json"]
        )
    return "\n".join(payloads)
