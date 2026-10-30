"""Controls for non-importing delivery history and source identity checks."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.lra_delivery import study
from bijux_pollenomics_dev.source_completion.lra_delivery.archives import ArchiveError

OID = "1" * 40


def _bundle(tmp_path: Path, header: str | None = None) -> Path:
    path = tmp_path / "source.git.bundle"
    path.write_bytes(
        (header if header is not None else f"# v2 git bundle\n{OID} HEAD").encode()
        + b"\n\nPACKsynthetic"
    )
    return path


def _git_success(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    assert args[:3] == ["git", "--no-optional-locks", "bundle"]
    assert args[3] in {"verify", "list-heads"}
    assert kwargs["timeout"] == 10
    return subprocess.CompletedProcess(
        args, 0, f"{OID} HEAD\n" if args[3] == "list-heads" else "", ""
    )


def test_bundle_uses_only_non_importing_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bundle(tmp_path)
    before = path.read_bytes()
    monkeypatch.setattr(subprocess, "run", _git_success)
    result = study.inspect_bundle(tmp_path, path)
    assert result["refs"] == {"HEAD": OID}
    assert result["prerequisites"] == []
    assert path.read_bytes() == before


def test_prerequisites_are_reported_not_called_global_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bundle(tmp_path, f"# v2 git bundle\n-{'2' * 40} prior commit\n{OID} HEAD")
    monkeypatch.setattr(subprocess, "run", _git_success)
    result = study.inspect_bundle(tmp_path, path)
    assert result["prerequisites"] == ["2" * 40]
    assert "not complete prior development" in result["scope"]


@pytest.mark.parametrize(
    "header",
    [
        "# v3 git bundle\n@object-format=sha256",
        f"# v2 git bundle\n{OID} HEAD\n{OID} HEAD",
        "# v2 git bundle\ninvalid",
        "# v2 git bundle",
    ],
)
def test_bad_bundle_header_never_invokes_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, header: str
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("bad header reached Git")

    monkeypatch.setattr(subprocess, "run", forbidden)
    with pytest.raises(ArchiveError):
        study.inspect_bundle(tmp_path, _bundle(tmp_path, header))


def test_ref_disagreement_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(args, 0, "", ""),
    )
    with pytest.raises(ArchiveError, match="listed refs differ"):
        study.inspect_bundle(tmp_path, _bundle(tmp_path))


def test_failed_git_verification_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **kwargs: subprocess.CompletedProcess(
            args, 1, "", "missing prerequisite"
        ),
    )
    with pytest.raises(ArchiveError, match="verify failed"):
        study.inspect_bundle(tmp_path, _bundle(tmp_path))


def test_changed_bundle_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _bundle(tmp_path)

    def mutate(args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        result = _git_success(args, **kwargs)
        if args[3] == "list-heads":
            path.write_bytes(path.read_bytes() + b"changed")
        return result

    monkeypatch.setattr(subprocess, "run", mutate)
    with pytest.raises(ArchiveError, match="changed during"):
        study.inspect_bundle(tmp_path, path)


def test_symlink_original_refuses(tmp_path: Path) -> None:
    original = _bundle(tmp_path)
    link = tmp_path / "linked.git.bundle"
    link.symlink_to(original)
    with pytest.raises(ArchiveError, match="ordinary bounded"):
        study.inspect_bundle(tmp_path, link)


def test_adoption_refusal_retains_missing_member_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    deliveries = tmp_path / "originals"
    deliveries.mkdir()
    (repository / "artifacts").mkdir(parents=True)
    for relative, body in (
        (study.ADOPTION, '{"files": []}'),
        (study.INVENTORY, "prototype_path,sha256\n"),
        (study.FUNCTIONS, "name\n"),
    ):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body)
    original = deliveries / "received.tar"
    original.write_bytes(b"synthetic source identity")
    monkeypatch.setattr(
        study, "SOURCE_IDENTITIES", {original.name: study._identity(original)}
    )
    inventory = {
        "root": "received",
        "members": [{"path": "missing.py", "type": "file", "sha256": "3" * 64}],
    }
    monkeypatch.setattr(study, "archive_inventory", lambda path: inventory)
    with pytest.raises(ArchiveError, match=r'"left_only": \["missing.py"\]'):
        study.build(repository, deliveries, repository / "artifacts/refused.json")
    assert not (repository / "artifacts/refused.json").exists()
