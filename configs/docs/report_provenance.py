"""Project finite public path metadata while retaining immutable execution receipts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import File, Files

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "configs/docs/publication/report-provenance.json"
MANIFEST_SHA256 = "cbe708fc7b95f330d555dd4071e3caaf83fca720fca494fb6db4a51130aad91b"
REPORT_PATHS = (
    "report/publication-replay/landclim-example-reexecution/report.json",
    "report/method-certification/linux-r-oracle/report.json",
    "report/pollen-reconstruction/tibetanus-point-age-sensitivity/execution/native-capture.json",
    "report/pollen-reconstruction/tibetanus-point-age-sensitivity/execution/source-cell-encoding-refusal.json",
    "report/pollen-reconstruction/tibetanus-point-age-sensitivity/execution/source-census-status-refusal.json",
    "report/pollen-reconstruction/nordic-static-basin-scenarios/verification/source-census-terminal.json",
    "report/pollen-reconstruction/nordic-static-basin-scenarios/verification/independent-physical-terminal.json",
    "report/pollen-reconstruction/nordic-static-basin-scenarios/verification/independent-scalar-terminal.json",
    "report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/acquisition-terminal.json",
    "report/pollen-reconstruction/nordic-static-basin-scenarios/verification/publication-metadata/qualification-terminal.json",
    "report/pollen-reconstruction/nordic-static-basin-scenarios/verification/native-terminal.json",
    "report/pollen-reconstruction/nordic-static-basin-scenarios/verification/source-census.json",
    "report/pollen-reconstruction/nordic-static-basin-scenarios/verification/primary-policy-native-terminal.json",
)
NOTE_KEY = "_public_provenance"
INTERNAL_PREFIXES = ("/Users/", "/home/", "/private/", "/tmp/")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("Public report provenance: " + message)


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read(root: Path, relative: str) -> bytes:
    path = PurePosixPath(relative)
    _require(
        bool(relative)
        and not path.is_absolute()
        and "\\" not in relative
        and all(part not in {"", ".", ".."} for part in relative.split("/")),
        "canonical relative input required",
    )
    source = root / relative
    _require(source.is_file(), "source input missing")
    for parent in (source, *source.parents):
        _require(not parent.is_symlink(), "source symlink forbidden")
        if parent == root:
            break
    return source.read_bytes()


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in items:
        _require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(value: str) -> None:
    raise ValueError("Public report provenance: nonfinite JSON token forbidden")


def _string_fields(text: str) -> dict[str, tuple[str, int, int]]:
    """Locate semantic string pointers without rewriting any numerical token."""
    decoder = json.JSONDecoder(object_pairs_hook=_pairs, parse_constant=_nonfinite)
    value, end = decoder.raw_decode(text, len(text) - len(text.lstrip()))
    _require(
        isinstance(value, dict) and not text[end:].strip(), "one report object required"
    )
    _require(NOTE_KEY not in value, "source already contains public projection note")
    fields = {}

    def whitespace(index: int) -> int:
        while index < len(text) and text[index] in " \t\r\n":
            index += 1
        return index

    def walk(index: int, pointer: str) -> int:
        index = whitespace(index)
        if text[index] == "{":
            index = whitespace(index + 1)
            if text[index] == "}":
                return index + 1
            while True:
                key, index = decoder.raw_decode(text, index)
                _require(isinstance(key, str), "object key required")
                index = whitespace(index)
                _require(text[index] == ":", "object separator required")
                index = whitespace(
                    walk(
                        index + 1,
                        pointer + "/" + key.replace("~", "~0").replace("/", "~1"),
                    )
                )
                if text[index] == "}":
                    return index + 1
                _require(text[index] == ",", "object member separator required")
                index = whitespace(index + 1)
        if text[index] == "[":
            index = whitespace(index + 1)
            if text[index] == "]":
                return index + 1
            position = 0
            while True:
                index = whitespace(walk(index, pointer + "/" + str(position)))
                if text[index] == "]":
                    return index + 1
                _require(text[index] == ",", "array member separator required")
                index = whitespace(index + 1)
                position += 1
        value, finish = decoder.raw_decode(text, index)
        if isinstance(value, str):
            fields[pointer] = (value, index, finish)
        return finish

    _require(walk(0, "") == end, "JSON pointer scan differs")
    return fields


def _note(row: dict) -> dict:
    return {
        "schema": 1,
        "source_receipt_sha256": row["source_sha256"],
        "display_fields": row["fields"],
        "display_semantics": "Only the declared path strings are portable display values. They are not executed argv or physical acquisition authority. The immutable source receipt owns those original facts.",
    }


def _project_report(raw: bytes, row: dict) -> bytes:
    _require(_digest(raw) == row["source_sha256"], "raw source digest differs")
    text = raw.decode("utf-8")
    positions = _string_fields(text)
    fields = row["fields"]
    pointers = [field["pointer"] for field in fields]
    _require(
        bool(fields) and len(set(pointers)) == len(pointers),
        "unique declared fields required",
    )
    edits = []
    for field in fields:
        _require(
            set(field) == {"pointer", "value_sha256", "kind", "display"},
            "field schema differs",
        )
        _require(field["pointer"] in positions, "declared pointer is not a string")
        value, begin, end = positions[field["pointer"]]
        _require(
            _digest(value.encode()) == field["value_sha256"],
            "declared value digest differs",
        )
        display = field["display"]
        _require(
            isinstance(display, str)
            and bool(display)
            and not display.startswith("/")
            and "\\" not in display
            and ":" not in display
            and all(ord(character) >= 32 for character in display)
            and all(part not in {"", ".", ".."} for part in display.split("/")),
            "portable display value required",
        )
        _require(
            field["kind"]
            in {
                "interpreter-display",
                "repository-path-display",
                "artifact-path-display",
                "retained-source-path-display",
            },
            "unknown display semantics",
        )
        edits.append((begin, end, json.dumps(display, ensure_ascii=False)))
    for begin, end, replacement in sorted(edits, reverse=True):
        text = text[:begin] + replacement + text[end:]
    _require(
        not any(
            prefix in value
            for value, _, _ in _string_fields(text).values()
            for prefix in INTERNAL_PREFIXES
        ),
        "unmapped internal path remains",
    )
    closing = len(text.rstrip()) - 1
    _require(text[closing] == "}", "report object closure required")
    note = json.dumps(_note(row), ensure_ascii=False, sort_keys=True, allow_nan=False)
    return (
        text[:closing].rstrip()
        + ",\n  "
        + json.dumps(NOTE_KEY)
        + ": "
        + note
        + "\n}"
        + text[closing + 1 :]
    ).encode("utf-8")


def projected_reports(root: Path) -> dict[str, bytes]:
    """Re-read every finite source input; previous projections never grant authority."""
    raw = _read(root, MANIFEST)
    _require(
        _digest(raw) == MANIFEST_SHA256, "manifest differs from reviewed projection"
    )
    manifest = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_nonfinite)
    _require(
        set(manifest) == {"schema", "owner", "reports"}
        and manifest["schema"] == 1
        and manifest["owner"] == "bijux-pollenomics",
        "manifest owner/schema differs",
    )
    rows = manifest["reports"]
    _require(
        tuple(row["path"] for row in rows) == REPORT_PATHS and len(rows) == 13,
        "report population differs",
    )
    _require(
        sum(len(row["fields"]) for row in rows) == 32,
        "display field population differs",
    )
    result = {}
    for row in rows:
        _require(
            set(row) == {"path", "source_sha256", "fields", "public_sha256"},
            "report schema differs",
        )
        value = _project_report(_read(root, "docs/" + row["path"]), row)
        _require(
            _digest(value) == row["public_sha256"], "public projection digest differs"
        )
        result[row["path"]] = value
    return result


def on_files(files: Files, config: MkDocsConfig) -> Files:
    _require(
        Path(config.docs_dir).absolute() == ROOT / "docs",
        "native document owner differs",
    )
    projected = projected_reports(ROOT)
    selected = {file.src_uri: file for file in files if file.src_uri in projected}
    _require(
        tuple(sorted(selected)) == tuple(sorted(REPORT_PATHS)),
        "native static input population differs",
    )
    generated = {}
    for relative, content in projected.items():
        original = selected[relative]
        _require(
            isinstance(original, File)
            and original.abs_src_path == str(ROOT / "docs" / relative)
            and original.dest_uri == relative
            and not original.is_documentation_page(),
            "native static input owner or route differs",
        )
        _require(
            original.content_bytes == _read(ROOT, "docs/" + relative),
            "native selected source content differs",
        )
        generated[relative] = File.generated(
            config, relative, content=content, inclusion=original.inclusion
        )
    for relative, original in selected.items():
        files.remove(original)
        files.append(generated[relative])
    return files
