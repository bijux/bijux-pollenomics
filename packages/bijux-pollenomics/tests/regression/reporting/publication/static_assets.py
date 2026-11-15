from __future__ import annotations

import base64
import gzip
import hashlib
import json
from pathlib import Path
import re

from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)


def read_static_atlas_payload_text(output_dir: Path, slug: str) -> str:
    manifest = json.loads(
        (output_dir / f"{slug}_map_assets.json").read_text(encoding="utf-8")
    )
    payloads: list[str] = []
    for row in normalize_asset_inventory(manifest["assets"]):
        asset_path = row["path"]
        assert isinstance(asset_path, str)
        script = (output_dir / asset_path).read_text(encoding="utf-8")
        envelope = json.loads(script[script.index(".push(") + 6 : -3])
        payloads.append(
            gzip.decompress(base64.b64decode(envelope["payload_gzip_base64"])).decode(
                "utf-8"
            )
            if envelope.get("payload_encoding") == "gzip_base64"
            else envelope["payload_json"]
        )
    return "\n".join(payloads)


def read_static_atlas_runtime(output_dir: Path, slug: str) -> str:
    """Read only the authenticated main code declared by a generated document."""
    document = output_dir / f"{slug}_map.html"
    matches = re.findall(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        document.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert len(matches) == 1
    runtime = json.loads(matches[0])["runtime"]
    name = runtime["path"]
    assert isinstance(name, str)
    assert re.fullmatch(
        re.escape(document.stem) + r"\.atlas-runtime\.[a-f0-9]{16}\.js", name
    )
    path = output_dir / name
    assert path.resolve(strict=True) == path.absolute()
    assert path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1
    body = path.read_bytes()
    digest = hashlib.sha256(body).digest()
    assert type(runtime["byte_count"]) is int
    assert len(body) == runtime["byte_count"]
    assert digest.hex()[:16] == name.rsplit(".", 2)[1]
    assert runtime["integrity"] == "sha256-" + base64.b64encode(digest).decode("ascii")
    return body.decode("utf-8")
