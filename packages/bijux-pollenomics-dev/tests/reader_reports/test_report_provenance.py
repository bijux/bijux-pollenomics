"""Portable display mappings preserve exact scientific receipt bytes and scope."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "report_provenance", ROOT / "configs/docs/report_provenance.py"
)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def row_for(raw: bytes, path: str) -> dict[str, Any]:
    return {
        "path": path,
        "source_sha256": digest(raw),
        "fields": [
            {
                "pointer": "/command/0",
                "value_sha256": digest(b"/Users/example/environment/bin/python"),
                "kind": "interpreter-display",
                "display": "python",
            }
        ],
    }


@pytest.fixture
def projection(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    raw = b'{"command":["/Users/example/environment/bin/python"],"values":[1.2300e-7,-0.000,10000000000000001],"whole_exit":1,"current_execution_qualified":false}'
    inputs = {"docs/" + name: raw for name in HOOK.REPORT_PATHS}
    rows = []
    for name in HOOK.REPORT_PATHS:
        row = row_for(raw, name)
        row["public_sha256"] = digest(HOOK._project_report(raw, row))
        rows.append(row)
    manifest = {"schema": 1, "owner": "bijux-pollenomics", "reports": rows}
    inputs[HOOK.MANIFEST] = json.dumps(manifest).encode()
    monkeypatch.setattr(HOOK, "_read", lambda root, name: inputs[name])
    return inputs, manifest


def test_actual_thirteen_current_projections_preserve_receipt_scope() -> None:
    outputs = HOOK.projected_reports(ROOT)
    assert tuple(outputs) == HOOK.REPORT_PATHS
    manifest = json.loads((ROOT / HOOK.MANIFEST).read_bytes())
    for row in manifest["reports"]:
        raw = (ROOT / "docs" / row["path"]).read_bytes()
        public = outputs[row["path"]]
        assert digest(raw) == row["source_sha256"]
        assert digest(public) == row["public_sha256"]
        original = json.loads(raw)
        projected = json.loads(public)
        projected.pop(HOOK.NOTE_KEY)
        for field in row["fields"]:
            parts = field["pointer"].split("/")[1:]
            source, target = original, projected
            for part in parts[:-1]:
                key = (
                    int(part)
                    if isinstance(source, list)
                    else part.replace("~1", "/").replace("~0", "~")
                )
                source, target = source[key], target[key]
            key = int(parts[-1]) if isinstance(source, list) else parts[-1]
            assert target[key] == field["display"]
            target[key] = source[key]
        assert projected == original


def test_configuration_formatting_has_no_content_fingerprint_trigger(
    projection: tuple[dict[str, bytes], dict[str, Any]],
) -> None:
    inputs, manifest = projection
    first = HOOK.projected_reports(ROOT)
    inputs[HOOK.MANIFEST] = json.dumps(manifest, indent=4).encode() + b"\n"
    assert HOOK.projected_reports(ROOT) == first


def test_exact_numeric_lexemes_and_failed_execution_remain_unchanged(
    projection: tuple[dict[str, bytes], dict[str, Any]],
) -> None:
    inputs, _ = projection
    name = HOOK.REPORT_PATHS[0]
    raw = inputs["docs/" + name].decode()
    public = HOOK.projected_reports(ROOT)[name].decode()
    token = re.compile(
        r'"(?:[^"\\]|\\.)*"|(-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)'
    )

    def numbers(text: str) -> list[str]:
        return [match[1] for match in token.finditer(text) if match[1]]

    assert numbers(raw) == numbers(public.split('"_public_provenance"')[0])
    result = json.loads(public)
    assert result["whole_exit"] == 1
    assert result["current_execution_qualified"] is False


@pytest.mark.parametrize(
    "change",
    [
        "raw",
        "value",
        "public",
        "missing",
        "duplicate",
        "foreign",
        "escape",
        "unmapped",
        "schema",
        "nonfinite",
    ],
)
def test_meaningful_source_public_and_privacy_guards_refuse(
    projection: tuple[dict[str, bytes], dict[str, Any]], change: str
) -> None:
    inputs, original = projection
    manifest = copy.deepcopy(original)
    row = manifest["reports"][0]
    name = "docs/" + row["path"]
    if change == "raw":
        inputs[name] = inputs[name].replace(b"1.2300e-7", b"1.2301e-7")
    elif change == "value":
        row["fields"][0]["value_sha256"] = "0" * 64
    elif change == "public":
        row["public_sha256"] = "0" * 64
    elif change == "missing":
        manifest["reports"].pop()
    elif change == "duplicate":
        manifest["reports"][-1] = copy.deepcopy(row)
    elif change == "foreign":
        row["path"] = "report/foreign/report.json"
    elif change == "escape":
        row["fields"][0]["display"] = "../private"
    elif change == "unmapped":
        row["fields"][0]["pointer"] = "/other"
        raw = inputs[name].replace(
            b'{"command"', b'{"other":"/Users/example/environment/bin/python","command"'
        )
        inputs[name] = raw
        row["source_sha256"] = digest(raw)
    elif change == "schema":
        row["extra"] = "unreviewed"
    elif change == "nonfinite":
        inputs[HOOK.MANIFEST] = (
            json.dumps(manifest).replace('"schema": 1', '"schema": NaN').encode()
        )
    if change != "nonfinite":
        inputs[HOOK.MANIFEST] = json.dumps(manifest).encode()
    with pytest.raises(ValueError):
        HOOK.projected_reports(ROOT)


def test_duplicate_manifest_key_refused(
    projection: tuple[dict[str, bytes], dict[str, Any]],
) -> None:
    inputs, _ = projection
    inputs[HOOK.MANIFEST] = inputs[HOOK.MANIFEST].replace(
        b'{"schema": 1', b'{"schema": 1,"schema": 1'
    )
    with pytest.raises(ValueError, match="duplicate JSON key"):
        HOOK.projected_reports(ROOT)


@pytest.mark.parametrize(
    "relative",
    [
        "../private.json",
        "/private/report.json",
        "report/../private.json",
        "report\\private.json",
    ],
)
def test_source_path_escape_refused(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError, match="canonical relative input required"):
        HOOK._read(tmp_path, relative)
