"""Frozen dependency audit admission controls."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest

from bijux_pollenomics_dev.security.locked_dependencies import (
    registry_batches,
    validate_report,
)
from bijux_pollenomics_dev.trusted_process import run_text


def test_developer_security_reenters_owned_profile(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    make = shutil.which("make")
    assert make is not None
    arguments = tmp_path / "audit-arguments.json"
    interpreter = tmp_path / "audit-interpreter"
    interpreter.write_text(
        f"#!{sys.executable}\n"
        "import json, sys\n"
        "from pathlib import Path\n"
        f"Path({str(arguments)!r}).write_text(json.dumps(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    interpreter.chmod(0o755)
    result = run_text(
        [
            Path(make),
            "-C",
            root / "packages" / "bijux-pollenomics-dev",
            "-f",
            root / "makes" / "packages" / "bijux-pollenomics-dev.mk",
            "security-deps",
            "SELF_MAKE=make",
            f"VENV_PYTHON={interpreter}",
        ],
        cwd=root,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(arguments.read_text(encoding="utf-8")) == [
        "-m",
        "bijux_pollenomics_dev.security.locked_dependencies",
    ]


def test_optional_and_platform_versions_are_all_audited(tmp_path: Path) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text(
        '[[package]]\nname = "workspace"\nsource = {editable = "."}\n'
        '[[package]]\nname = "AnyIO"\nversion = "4.14.2"\nsource = {registry = "https://pypi.org/simple"}\n'
        '[[package]]\nname = "anyio"\nversion = "4.15.1"\nsource = {registry = "https://pypi.org/simple"}\n'
        '[[package]]\nname = "fsspec"\nversion = "2026.6.0"\nsource = {registry = "https://pypi.org/simple"}\n',
        encoding="utf-8",
    )
    batches = registry_batches(lock)
    assert {pair for batch in batches for pair in batch} == {
        ("anyio", "4.14.2"),
        ("anyio", "4.15.1"),
        ("fsspec", "2026.6.0"),
    }
    assert all(len({name for name, _ in batch}) == len(batch) for batch in batches)


@pytest.mark.parametrize(
    "source",
    [
        '{git = "https://example.org/project"}',
        "{}",
        '{registry = "https://example.org/simple"}',
    ],
)
def test_unsupported_source_is_not_silently_omitted(
    tmp_path: Path, source: str
) -> None:
    lock = tmp_path / "uv.lock"
    lock.write_text(
        f'[[package]]\nname = "distribution"\nversion = "1"\nsource = {source}\n',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unsupported .*source"):
        registry_batches(lock)


@pytest.mark.parametrize(
    "dependencies",
    [
        [],
        [{"name": "fsspec", "version": "2026.6.0", "skip_reason": "unsupported"}],
        [{"name": "fsspec", "version": "2026.6.0", "vulns": [{"id": "GHSA-example"}]}],
        [{"name": "fsspec", "version": "2026.3.0", "vulns": []}],
    ],
)
def test_incomplete_or_vulnerable_report_fails(
    dependencies: list[dict[str, object]],
) -> None:
    assert not validate_report({"dependencies": dependencies}, [("fsspec", "2026.6.0")])


def test_every_exact_locked_version_must_be_present() -> None:
    assert validate_report(
        {"dependencies": [{"name": "fsspec", "version": "2026.6.0", "vulns": []}]},
        [("fsspec", "2026.6.0")],
    )
