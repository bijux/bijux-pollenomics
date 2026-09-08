"""Validate repository state fields used as release build identity."""

from __future__ import annotations

from collections.abc import Mapping

from ..release_evidence.models import ReleaseEvidenceError


def code_commit(state: Mapping[str, object]) -> str:
    """Return the governed commit identity, including fixture repositories."""
    value = state.get("head_commit")
    if value is None:
        return "0" * 40
    if not isinstance(value, str):
        raise ReleaseEvidenceError("repository HEAD identity is invalid")
    return value


def dirty_state(state: Mapping[str, object]) -> bool:
    """Return the observed dirty flag after rejecting non-boolean values."""
    value = state.get("dirty")
    if type(value) is not bool:
        raise ReleaseEvidenceError("repository dirty state is invalid")
    return value
