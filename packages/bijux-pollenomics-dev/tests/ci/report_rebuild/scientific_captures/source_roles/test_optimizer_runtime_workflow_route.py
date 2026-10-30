"""Keep the optimizer's one inherited workflow route on exact runtime custody."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    author_optimizer_diagnostics as optimizer,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    atlas_runtime_transport as transport,
)

from .test_atlas_runtime_transport_custody import (
    _CONTEXTS,
    _CURRENT,
    _OLD,
    _WORKFLOW,
    TransportCase,
    _case,
)

_PAYLOAD = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py"
)


def _outer_case(
    root: Path, monkeypatch: pytest.MonkeyPatch, source: str = _WORKFLOW
) -> TransportCase:
    """Repin only invented fixture identities while retaining every other adapter role."""
    case = _case(root, monkeypatch, _CONTEXTS[0], source)
    authority = dict(optimizer._OPTIMIZER_ATLAS_SOURCES)
    authority[source] = (
        hashlib.sha256(_OLD).hexdigest(),
        len(_OLD),
        "finite_atlas_extension",
    )
    monkeypatch.setattr(optimizer, "_OPTIMIZER_ATLAS_SOURCES", authority)
    capture_sha = case.buffer.descriptor.capture["sha256"]
    assert isinstance(capture_sha, str)
    monkeypatch.setattr(optimizer, "CAPTURE_SHA256", capture_sha)
    return case


def _invoke(case: TransportCase) -> dict[str, Any] | None:
    """Call the actual outer adapter that previously bypassed the central route."""
    return optimizer._optimizer_source_input_correspondence(
        case.consumer.repository, case.row, case.logical, case.buffer
    )


def _observe_runtime_route(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Observe actual maintained helper calls without replacing acceptance results."""
    calls: list[str] = []
    original = transport.validated_atlas_runtime_transport_source

    def observed(
        repository: Path, row: dict[str, Any], logical: str, resolver: SourceCapsule
    ) -> dict[str, Any]:
        calls.append(row["path"])
        return original(repository, row, logical, resolver)

    monkeypatch.setattr(optimizer, "validated_atlas_runtime_transport_source", observed)
    return calls


def test_outer_workflow_delegates_after_real_positive_old_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Preserve fixed original custody and explicitly changed runtime/native scope."""
    case = _outer_case(tmp_path / "repository", monkeypatch)
    calls = _observe_runtime_route(monkeypatch)
    result = _invoke(case)
    assert isinstance(result, dict)
    assert calls == [_WORKFLOW]
    assert result["path"] == _WORKFLOW
    assert result["original_member"] == case.logical
    assert result["original_bytes"] == len(_OLD)
    assert result["original_sha256"] == hashlib.sha256(_OLD).hexdigest()
    assert result["classification"] == "runtime_transport_extension"
    assert result["whole_old_module_reconstructed"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert result["historical_native_equal_current_output_claimed"] is False
    assert result["historical_browser_equal_current_browser_claimed"] is False
    assert result["old_native_equal_current_admission_claimed"] is False


@pytest.mark.parametrize(
    "damage", ("unknown_current", "wrong_group", "wrong_old_hash", "wrong_context")
)
def test_outer_workflow_refuses_after_positive_actual_route(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Keep outer member guards and the inner unknown-byte refusal observable."""
    case = _outer_case(tmp_path / "repository", monkeypatch)
    calls = _observe_runtime_route(monkeypatch)
    baseline = _invoke(case)
    assert isinstance(baseline, dict)
    assert baseline["classification"] == "runtime_transport_extension"
    assert calls == [_WORKFLOW]
    calls.clear()
    if damage == "unknown_current":
        case.target.write_bytes(case.target.read_bytes() + b"# unknown current code\n")
    elif damage == "wrong_group":
        case.buffer.descriptor.groups[0]["resolved_paths"] = [(case.logical, _PAYLOAD)]
    elif damage == "wrong_old_hash":
        case.row["sha256"] = "0" * 64
    else:
        case.buffer.prefix = _CONTEXTS[1]
    with pytest.raises(ReportRebuildError):
        _invoke(case)
    assert calls == ([_WORKFLOW] if damage == "unknown_current" else [])


def test_other_finite_atlas_role_keeps_old_exact_or_named_predicate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not send a different existing finite presentation role to the new helper."""
    case = _outer_case(tmp_path / "repository", monkeypatch, _PAYLOAD)
    calls = _observe_runtime_route(monkeypatch)
    case.target.write_bytes(_OLD)
    assert _invoke(case) is None
    assert calls == []
    case.target.write_bytes(_CURRENT)
    with pytest.raises(
        ReportRebuildError,
        match="Optimizer Atlas source differs beyond named asset or provider additions",
    ):
        _invoke(case)
    assert calls == []
