from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path


def read_static_asset_payload(path: Path) -> dict[str, object]:
    script = path.read_text(encoding="utf-8")
    marker = "globalThis.__BIJUX_ATLAS_RAW_CHUNKS__.push("
    start = script.index(marker) + len(marker)
    assert script.endswith(");\n")
    envelope = json.loads(script[start:-3])
    payload_json = (
        gzip.decompress(base64.b64decode(envelope["payload_gzip_base64"])).decode(
            "utf-8"
        )
        if envelope.get("payload_encoding") == "gzip_base64"
        else envelope["payload_json"]
    )
    assert isinstance(payload_json, str)
    assert (
        envelope["payload_sha256"]
        == hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    )
    payload = json.loads(payload_json)
    assert isinstance(payload, dict)
    return payload


__all__ = ["read_static_asset_payload"]
