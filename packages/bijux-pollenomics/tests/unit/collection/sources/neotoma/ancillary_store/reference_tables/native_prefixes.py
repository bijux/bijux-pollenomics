"""Native prefix fixtures own source captures and portable reference archives."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.reference_tables import (
    NeotomaReferenceTablePlan,
    capture_neotoma_reference_tables,
)
from bijux_pollenomics.collection.sources.neotoma.capture.transport import (
    NeotomaHttpResponse,
)


@pytest.fixture
def reference_source(tmp_path: Path, request: pytest.FixtureRequest) -> dict[str, Any]:
    posture = getattr(request, "param", "complete")
    bodies = {
        "variableunits": b'{"status":"success","data":[{"variableunitsid":37,"variableunits":"m"}]}',
        "geopoliticalunits": b'{"status":"success","data":[]}',
    }
    if posture == "incomplete":
        bodies["geopoliticalunits"] = b'{"status":"success","data":['

    def fetch(url: str, **_: Any) -> NeotomaHttpResponse:
        table = url.split("/dbtables/", 1)[1].split("?", 1)[0]
        body = bodies[table]
        return NeotomaHttpResponse(
            url,
            404 if posture == "http" and table == "geopoliticalunits" else 200,
            (("Content-Length", str(len(body))),),
            body,
            not (posture == "incomplete" and table == "geopoliticalunits"),
        )

    directory = tmp_path / "original-reference-capture"
    captured = capture_neotoma_reference_tables(
        directory,
        plan=NeotomaReferenceTablePlan(("variableunits", "geopoliticalunits")),
        fetch=fetch,
    )
    return {"directory": directory, "capture": captured, "bodies": bodies}


@pytest.fixture
def reference_archive(
    reference_source: dict[str, Any], tmp_path: Path
) -> dict[str, Any]:
    from hashlib import sha256

    owner = importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.ancillary_store.reference_tables"
    )
    directory = tmp_path / "portable-reference-archive"
    manifest = owner.write_neotoma_reference_archive(
        directory,
        capture_directory=reference_source["directory"],
        expected_capture_manifest_sha256=reference_source["capture"].manifest_sha256,
    )
    return {
        **reference_source,
        "directory": directory,
        "source_directory": reference_source["directory"],
        "manifest": manifest,
        "sha256": sha256((directory / "manifest.json").read_bytes()).hexdigest(),
        "owner": owner,
    }
