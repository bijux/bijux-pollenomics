"""Confine documentation correspondence to three authenticated ADNA source names."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as policy,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.adna import (
    current_domain as module,
)

NAMES = tuple(module._DOCUMENTED_CURRENT_SOURCE_IDENTITIES)
OLD = b"from __future__ import annotations\n\ndef own(value: int = 3) -> int:\n    return value + 1\n"
DOC = "Retain this own literal document."
CURRENT = OLD.replace(
    b"    return value + 1", b'    """' + DOC.encode() + b'"""\n    return value + 1'
)


def _world(
    root: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> tuple[Path, dict[str, Any]]:
    """Install only own strings and explicit literal fixture authorities."""
    checksum = hashlib.sha256(OLD).hexdigest()
    monkeypatch.setattr(
        module, "_DOCUMENTED_CURRENT_SOURCE_IDENTITIES", {name: (checksum, len(OLD))}
    )
    monkeypatch.setattr(policy, "DOCUMENTED_CAPTURE_DEFINITIONS", {name: ("own",)})
    monkeypatch.setattr(policy, "DOCUMENTED_CAPTURE_STRINGS", {name: {"own": DOC}})
    path = root / name
    path.parent.mkdir(parents=True)
    path.write_bytes(CURRENT)
    return path, {"sha256": checksum, "bytes": len(OLD)}


@pytest.mark.parametrize("name", NAMES)
def test_each_named_source_keeps_old_bytes_and_exact_documentary_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """A changed source needs full old-byte reconstruction, not a current hash pin."""
    _, expected = _world(tmp_path, monkeypatch, name)
    facts = module._documented_current_source_correspondence(
        tmp_path, name, expected, OLD
    )
    assert facts is not None
    assert facts["path"] == name
    assert facts["classification"] == "exact_named_documentation_source_correspondence"
    assert facts["original_sha256"] == expected["sha256"]
    assert facts["original_bytes"] == expected["bytes"]
    assert (
        facts["whole_original_executable_ast_and_noninserted_bytes_preserved"] is True
    )
    assert facts["current_source_byteequal"] is False
    assert facts["new_native_or_mathematical_qualification_claimed"] is False


@pytest.mark.parametrize("name", NAMES)
def test_unchanged_source_keeps_the_byte_equal_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """The original source body requires no documentary correspondence."""
    path, expected = _world(tmp_path, monkeypatch, name)
    path.write_bytes(OLD)
    assert (
        module._documented_current_source_correspondence(tmp_path, name, expected, OLD)
        is None
    )


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize(
    "damage",
    [
        "unknown_name",
        "path_alias",
        "expected_hash",
        "expected_size",
        "bool_size",
        "extra_identity_field",
        "old_bytes",
        "bytearray",
        "missing_current",
        "symlink",
        "hardlink",
        "parent_symlink",
        "outside_comment",
        "outside_whitespace",
        "import",
        "number",
        "default",
        "annotation",
        "changed_doc",
        "empty_doc",
        "whitespace_doc",
        "fstring_doc",
        "wrong_scope",
        "new_definition",
        "oversize",
        "changed_during_law",
    ],
)
def test_source_identity_alias_and_noninserted_byte_changes_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, damage: str
) -> None:
    """Reject every departure from old identity, confinement or named doc content."""
    path, expected = _world(tmp_path, monkeypatch, name)
    captured: Any = OLD
    assert (
        module._documented_current_source_correspondence(tmp_path, name, expected, OLD)
        is not None
    )
    if damage == "unknown_name":
        name = "packages/own/development.py"
    elif damage == "path_alias":
        name = name.replace("/adna/", "/adna/../adna/")
    elif damage == "expected_hash":
        expected["sha256"] = "0" * 64
    elif damage == "expected_size":
        expected["bytes"] += 1
    elif damage == "bool_size":
        expected["bytes"] = True
    elif damage == "extra_identity_field":
        expected["extra"] = "unreviewed"
    elif damage == "old_bytes":
        captured += b"\n# altered original\n"
    elif damage == "bytearray":
        captured = bytearray(OLD)
    elif damage == "missing_current":
        path.unlink()
    elif damage in {"symlink", "hardlink"}:
        target = tmp_path / "own-target"
        target.write_bytes(path.read_bytes())
        path.unlink()
        if damage == "symlink":
            path.symlink_to(target)
        else:
            path.hardlink_to(target)
    elif damage == "parent_symlink":
        parent = path.parent
        target = tmp_path / "own-parent"
        parent.rename(target)
        parent.symlink_to(target, target_is_directory=True)
    elif damage == "outside_comment":
        path.write_bytes(CURRENT + b"\n# changed outside literal\n")
    elif damage == "outside_whitespace":
        path.write_bytes(CURRENT.replace(b"return value + 1", b"return  value + 1"))
    elif damage == "import":
        path.write_bytes(CURRENT + b"\nimport math\n")
    elif damage == "number":
        path.write_bytes(CURRENT.replace(b"value + 1", b"value + 2"))
    elif damage == "default":
        path.write_bytes(CURRENT.replace(b"value: int = 3", b"value: int = 4"))
    elif damage == "annotation":
        path.write_bytes(CURRENT.replace(b"value: int", b"value: float"))
    elif damage == "changed_doc":
        path.write_bytes(CURRENT.replace(DOC.encode(), (DOC + " changed").encode()))
    elif damage == "empty_doc":
        path.write_bytes(CURRENT.replace(DOC.encode(), b""))
    elif damage == "whitespace_doc":
        path.write_bytes(CURRENT.replace(DOC.encode(), b"   "))
    elif damage == "fstring_doc":
        path.write_bytes(CURRENT.replace(b'    """', b'    f"""', 1))
    elif damage == "wrong_scope":
        monkeypatch.setattr(
            policy, "DOCUMENTED_CAPTURE_DEFINITIONS", {name: ("other",)}
        )
        monkeypatch.setattr(
            policy, "DOCUMENTED_CAPTURE_STRINGS", {name: {"other": DOC}}
        )
    elif damage == "new_definition":
        path.write_bytes(CURRENT + b"\ndef extra() -> int:\n    return 1\n")
    elif damage == "oversize":
        path.write_bytes(b"#" + b" " * 32768)
    elif damage == "changed_during_law":
        actual_law = policy._documented_source_matches

        def changed_law(
            source_name: str, captured_source: bytes, current_source: bytes
        ) -> bool:
            result = actual_law(source_name, captured_source, current_source)
            path.write_bytes(current_source.replace(b"value + 1", b"value + 2"))
            return result

        monkeypatch.setattr(module, "_documented_source_matches", changed_law)
    else:
        raise AssertionError(damage)
    with pytest.raises((ReportRebuildError, OSError)):
        module._documented_current_source_correspondence(
            tmp_path, name, expected, captured
        )
