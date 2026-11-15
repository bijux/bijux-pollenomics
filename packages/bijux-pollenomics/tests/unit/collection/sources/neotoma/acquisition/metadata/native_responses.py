from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma.capture import (
    NeotomaMetadataResponse,
)

SITE_BODY = b'{"status":"success","data":[{"site":{"siteid":12,"collectionunitid":100,"unittype":"Core","datasets":[{"datasetid":201,"datasettype":"pollen"}]}}]}'


def response(url: str, body: bytes = SITE_BODY) -> NeotomaMetadataResponse:
    return NeotomaMetadataResponse(
        final_url=url,
        http_status=200,
        headers=(
            ("Content-Length", str(len(body))),
            ("X-Source", "a"),
            ("X-Source", "b"),
        ),
        body=body,
    )


def rewrite_json(path: Path, payload: object) -> str:
    content = json.dumps(payload).encode()
    path.write_bytes(content)
    return sha256(content).hexdigest()
