"""Keep original scoring-source identities separate from declared reader changes."""

from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    scoring_protocols as subject,
)

_PREFIX = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
_CHALLENGE = _PREFIX + "lra_validation/site_leakage_challenge.py"
_RECEIVER = (
    _PREFIX + "source_completion/pollen_reconstruction/english_receiver_annulus.py"
)
_SCORING = _PREFIX + "source_completion/lilla_gloppsjon_direct_pollen_scoring.py"
_PATHS = (_CHALLENGE, _RECEIVER, _SCORING)
_HISTORICAL = "2a1cba9420a815ec019776c2155ab53f1a3a84d2"


def _case(name: str) -> tuple[bytes, bytes]:
    repository = Path(
        subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(__file__).resolve().parent,
            text=True,
        ).strip()
    )
    entry = subprocess.check_output(
        ["git", "--no-replace-objects", "ls-tree", _HISTORICAL, "--", name],
        cwd=repository,
    )
    assert entry.startswith(b"100644 blob ") and entry.count(b"\n") == 1
    captured = subprocess.check_output(
        ["git", "--no-replace-objects", "show", _HISTORICAL + ":" + name],
        cwd=repository,
    )
    current = (repository / name).read_bytes()
    assert subject.scoring_protocol_extension_matches(name, captured, current)
    return captured, current


@pytest.mark.parametrize("name", _PATHS)
def test_exact_three_original_source_readers_have_a_positive_baseline(
    name: str,
) -> None:
    expected_sources = frozenset(_PATHS)
    assert expected_sources == subject.SCORING_PROTOCOL_SOURCES
    captured, current = _case(name)
    assert subject.scoring_protocol_extension_matches(name, captured, current)
    assert not subject.scoring_protocol_extension_matches(
        name + ".unknown", captured, current
    )


@pytest.mark.parametrize("name", _PATHS)
def test_original_source_bytes_and_bounded_current_body_are_required(name: str) -> None:
    captured, current = _case(name)
    assert not subject.scoring_protocol_extension_matches(
        name, captured + b"\n", current
    )
    assert not subject.scoring_protocol_extension_matches(
        name, b"!" + captured[1:], current
    )
    assert not subject.scoring_protocol_extension_matches(name, captured, b"")
    assert not subject.scoring_protocol_extension_matches(
        name, captured, b"x" * (64 * 1024 + 1)
    )


@pytest.mark.parametrize("name", _PATHS)
@pytest.mark.parametrize(
    "extra",
    (
        b"\n# Unreviewed source bytes.\n",
        b"\nUNEXPECTED = 1\n",
        b"\nimport os as unexpected\n",
    ),
)
def test_every_other_old_source_byte_remains_required(name: str, extra: bytes) -> None:
    captured, current = _case(name)
    assert not subject.scoring_protocol_extension_matches(
        name, captured, current + extra
    )


@pytest.mark.parametrize("name", (_CHALLENGE, _SCORING))
@pytest.mark.parametrize(
    "replacement", (b'arithmetic_profile="stable"', b'arithmetic_profile="unknown"')
)
def test_historical_profile_cannot_silently_select_another_arithmetic(
    name: str, replacement: bytes
) -> None:
    captured, current = _case(name)
    selected = b'arithmetic_profile="source-compatible-22c6e480"'
    assert current.count(selected) == 1
    assert not subject.scoring_protocol_extension_matches(
        name, captured, current.replace(selected, replacement, 1)
    )


@pytest.mark.parametrize(
    "original,changed",
    (
        (
            b"if type(value) not in {int, float}:",
            b"if not isinstance(value, (int, float)):",
        ),
        (
            b'if relative == "models/validation.py":',
            b'if relative in ("models/validation.py", "dispersal/kernels.py"):',
        ),
        (b"if result != value:", b"if False:"),
        (b"        validate_blobs(\n", b"        unverified_blobs(\n"),
    ),
)
def test_receiver_native_admission_and_equation_identity_guards_remain_required(
    original: bytes, changed: bytes
) -> None:
    captured, current = _case(_RECEIVER)
    assert current.count(original) == 1
    assert not subject.scoring_protocol_extension_matches(
        _RECEIVER, captured, current.replace(original, changed, 1)
    )
