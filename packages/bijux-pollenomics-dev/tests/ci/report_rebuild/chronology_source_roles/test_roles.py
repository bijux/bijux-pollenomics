"""Keep historical portal roles and named documentation confined to exact source identities."""

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as capture,
)

from .fixtures import (
    DOCS,
    PORTAL,
    ROOT_SOURCE,
    current_file,
    sha,
    source_pair,
)
from .fixtures import (
    literal_authority as literal_authority,
)
from .fixtures import (
    repository as repository,
)


def test_finite_approved_role_names_remain_closed() -> None:
    assert capture.HISTORICAL_PORTAL_READER_SOURCES == PORTAL
    assert capture.DOCUMENTED_CAPTURE_DEFINITIONS == DOCS
    assert len(PORTAL) == 6 and len(DOCS) == 7
    assert sum(map(len, DOCS.values())) == 23
    assert not set(DOCS) & PORTAL


@pytest.mark.parametrize("name", sorted(PORTAL))
def test_portal_current_semantics_are_not_relabelled_as_archived_source(
    repository: Path, name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = b"VALUE = 7\n"
    current_file(repository, name, b"DIFFERENT_CURRENT_VALUE = 19\n")

    def no_documentation_comparison(*args: object) -> bool:
        raise AssertionError(
            "A retained portal role is not an executable-AST equivalence claim"
        )

    monkeypatch.setattr(
        capture, "_documented_source_matches", no_documentation_comparison
    )
    logical = "source/" + name
    capture._validate_current_source(
        repository, name, logical, captured, sha(captured), frozenset({logical})
    )


@pytest.mark.parametrize("name", sorted(DOCS))
def test_documented_roles_preserve_the_own_archived_program(
    repository: Path, name: str
) -> None:
    captured, current = source_pair(name)
    current_file(repository, name, current)
    logical = "source/" + name
    assert capture._documented_source_matches(name, captured, current)
    capture._validate_current_source(
        repository, name, logical, captured, sha(captured), frozenset({logical})
    )


@pytest.mark.parametrize("name", [next(iter(sorted(PORTAL))), next(iter(sorted(DOCS)))])
@pytest.mark.parametrize(
    "damage",
    [
        "wrong_logical",
        "runtime_logical",
        "missing_detached",
        "only_extra_detached",
        "captured_hash",
        "missing_current",
        "directory",
        "symlink",
        "hardlink",
    ],
)
def test_role_and_custody_refusals(repository: Path, name: str, damage: str) -> None:
    captured, current = (
        source_pair(name) if name in DOCS else (b"VALUE = 7\n", b"VALUE = 9\n")
    )
    path = current_file(repository, name, current)
    logical = "source/" + name
    detached = frozenset({logical})
    expected = sha(captured)
    if damage == "wrong_logical":
        logical = "source/packages/own/other.py"
        detached = frozenset({logical})
    elif damage == "runtime_logical":
        logical = "runtime/" + name
        detached = frozenset({logical})
    elif damage == "missing_detached":
        detached = frozenset()
    elif damage == "only_extra_detached":
        detached = frozenset({logical + ".other"})
    elif damage == "captured_hash":
        expected = "0" * 64
    elif damage == "missing_current":
        path.unlink()
    elif damage == "directory":
        path.unlink()
        path.mkdir()
    else:
        reference = repository / "own-current.py"
        reference.write_bytes(current)
        path.unlink()
        if damage == "symlink":
            path.symlink_to(reference)
        else:
            path.hardlink_to(reference)
    with pytest.raises((ReportRebuildError, ValueError)):
        capture._validate_current_source(
            repository, name, logical, captured, expected, detached
        )


@pytest.mark.parametrize(
    "name",
    [
        ROOT_SOURCE + "reporting/presentation/report_portal/unlisted.py",
        ROOT_SOURCE + "adna/domain/unlisted.py",
    ],
)
def test_unlisted_program_cannot_borrow_an_exception(
    repository: Path, name: str
) -> None:
    captured = b"VALUE = 7\n"
    current_file(repository, name, b'"""Own new prose."""\nVALUE = 7\n')
    logical = "source/" + name
    with pytest.raises(ReportRebuildError, match="source footprint differs"):
        capture._validate_current_source(
            repository, name, logical, captured, sha(captured), frozenset({logical})
        )


def test_unlisted_program_still_requires_exact_current_bytes(repository: Path) -> None:
    name = ROOT_SOURCE + "own_exact.py"
    raw = b"VALUE = 7\n"
    current_file(repository, name, raw)
    capture._validate_current_source(
        repository, name, "source/" + name, raw, sha(raw), frozenset()
    )


@pytest.mark.parametrize(
    "name", ["../escape.py", "/absolute.py", "packages/own/../escape.py"]
)
def test_source_name_cannot_escape_repository(repository: Path, name: str) -> None:
    raw = b"VALUE = 7\n"
    with pytest.raises((ReportRebuildError, ValueError)):
        capture._validate_current_source(
            repository,
            name,
            "source/" + name,
            raw,
            sha(raw),
            frozenset({"source/" + name}),
        )
