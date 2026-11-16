"""Public validation binds generated draw-source receipt parsing to its hash."""

from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics.analysis.lra.inputs import regional_draw_love
from bijux_pollenomics.analysis.lra.inputs.validation import _evidence
from tests.unit.analysis.lra.support import regional_draw_love_fixture
from tests.unit.analysis.lra.test_publication_draws import _bundle


@pytest.fixture
def request_inputs(tmp_path: Path) -> tuple[dict[str, Any], Path, Path]:
    bundle, _ = _bundle(tmp_path)
    payload = regional_draw_love_fixture(
        tmp_path,
        bundle=bundle,
        checksums_sha256=sha256((bundle / "checksums.json").read_bytes()).hexdigest(),
    )
    return payload, tmp_path, tmp_path / "draw-draw_source_receipt.txt"


def receipt_item(payload: dict[str, Any]) -> dict[str, Any]:
    return next(
        item for item in payload["evidence"] if item["role"] == "draw_source_receipt"
    )


def validate(payload: dict[str, Any], root: Path) -> Any:
    return regional_draw_love.validate_regional_draw_love_request(
        payload, input_root=root
    )


def test_rejected_receipt_A_cannot_become_valid_B_after_authentication(
    request_inputs: tuple[dict[str, Any], Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    payload, root, receipt = request_inputs
    valid = receipt.read_bytes()
    invalid = json.loads(valid)
    invalid["bundle_directory"] = "different-source"
    invalid_bytes = json.dumps(invalid).encode()
    receipt.write_bytes(invalid_bytes)
    receipt_item(payload)["sha256"] = sha256(invalid_bytes).hexdigest()
    with pytest.raises(LRARefusal) as control:
        validate(payload, root)
    assert control.value.reason_code == "invalid_regional_draw_source_receipt"
    authenticate = _evidence
    events = []

    def authenticated_then_substituted(*args: Any, **kwargs: Any) -> Any:
        roles = authenticate(*args, **kwargs)
        receipt.write_bytes(valid)
        events.append("authenticated_A_then_substituted_B")
        return roles

    monkeypatch.setattr(regional_draw_love, "_evidence", authenticated_then_substituted)
    with pytest.raises(LRARefusal) as refused:
        validate(payload, root)
    assert refused.value.reason_code == "invalid_regional_draw_source_receipt"
    assert events == ["authenticated_A_then_substituted_B"]
    assert receipt.read_bytes() == valid


def test_valid_captured_receipt_survives_later_path_mutation(
    request_inputs: tuple[dict[str, Any], Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    payload, root, receipt = request_inputs
    expected = receipt_item(payload)["sha256"]
    authenticate = _evidence
    events = []

    def authenticated_then_changed(*args: Any, **kwargs: Any) -> Any:
        roles = authenticate(*args, **kwargs)
        receipt.write_bytes(b"not the captured receipt")
        events.append("after_authentication")
        return roles

    monkeypatch.setattr(regional_draw_love, "_evidence", authenticated_then_changed)
    accepted = validate(payload, root)
    assert events == ["after_authentication"]
    assert receipt_item(accepted.payload())["sha256"] == expected
    assert sha256(receipt.read_bytes()).hexdigest() != expected


def test_positive_real_generated_bundle_and_receipt_still_match(
    request_inputs: tuple[dict[str, Any], Path, Path],
) -> None:
    payload, root, _ = request_inputs
    accepted = validate(payload, root)
    assert accepted.payload()["regional_draw_source"] == payload["regional_draw_source"]
    assert accepted.payload()["taxa"] == ["A", "B", "C"]


@pytest.mark.parametrize("kind", ["parent_alias", "hardlink"])
def test_selected_receipt_requires_literal_ordinary_custody(
    request_inputs: tuple[dict[str, Any], Path, Path], kind: str
) -> None:
    payload, root, receipt = request_inputs
    if kind == "parent_alias":
        directory = root / "receipt-owner"
        directory.mkdir()
        moved = directory / receipt.name
        receipt.rename(moved)
        alias = root / "receipt-alias"
        alias.symlink_to(directory, target_is_directory=True)
        receipt_item(payload)["path"] = f"receipt-alias/{receipt.name}"
    else:
        os.link(receipt, root / "receipt-hardlink.txt")
    with pytest.raises(LRARefusal) as refused:
        validate(payload, root)
    assert refused.value.reason_code == "evidence_unavailable"


@pytest.mark.parametrize("kind", ["fifo", "oversized"])
def test_invalid_receipt_namespace_refuses_before_body_open(
    request_inputs: tuple[dict[str, Any], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    payload, root, receipt = request_inputs
    if kind == "fifo":
        receipt.unlink()
        os.mkfifo(receipt)
    else:
        content = receipt.read_bytes() + b" " * (1024 * 1024 + 1)
        receipt.write_bytes(content)
        receipt_item(payload)["sha256"] = sha256(content).hexdigest()
    real_open = Path.open
    forbidden = []

    def opened(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == receipt:
            forbidden.append(path)
            raise AssertionError("invalid receipt reached an ordinary body open")
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", opened)
    with pytest.raises(LRARefusal) as refused:
        validate(payload, root)
    assert refused.value.reason_code == "evidence_unavailable"
    assert forbidden == []


@pytest.mark.parametrize("change", ["growth", "early_eof"])
def test_actual_receipt_fd_refuses_growth_or_truncation_and_closes(
    request_inputs: tuple[dict[str, Any], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    payload, root, receipt = request_inputs
    original_size = receipt.stat().st_size
    original_open, original_read = os.open, os.read
    descriptors: list[int] = []
    reads: list[int] = []
    events: list[str] = []

    def opened(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original_open(path, flags, *args, **kwargs)
        if Path(path).name == receipt.name and not flags & os.O_DIRECTORY:
            descriptors.append(descriptor)
        return descriptor

    def read(descriptor: int, size: int) -> bytes:
        if descriptor in descriptors:
            if not events:
                with receipt.open("r+b") as stream:
                    stream.truncate(
                        original_size + 1024 * 1024
                        if change == "growth"
                        else original_size - 5
                    )
                events.append(change)
            raw = original_read(descriptor, size)
            reads.append(len(raw))
            return raw
        return original_read(descriptor, size)

    monkeypatch.setattr(os, "open", opened)
    monkeypatch.setattr(os, "read", read)
    with pytest.raises(LRARefusal) as refused:
        validate(payload, root)
    assert refused.value.reason_code == "evidence_unavailable"
    assert events == [change] and len(descriptors) == 1
    assert sum(reads) <= original_size + 1
    with pytest.raises(OSError):
        os.fstat(descriptors[0])
