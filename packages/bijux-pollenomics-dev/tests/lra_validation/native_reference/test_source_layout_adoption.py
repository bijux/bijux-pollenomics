"""Named operation/path custody never accepts unrelated source or API changes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
)
from bijux_pollenomics_dev.lra_validation.native_reference import (
    source_layout_adoption as layout,
)


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    prefix = "\n".join("from " + name + " import X" for name in layout.MODULES)
    original = (prefix + "\ndef retained():\n    return 17\n").encode()
    original += b"#" + b" synthetic metadata padding" * (
        (6049 - len(original)) // 27 + 1
    )
    original = original[:6048] + b"\n"
    assert len(original) == 6049
    current = original
    for old, new in layout.MODULES.items():
        current = current.replace(old.encode(), new.encode())
    rows = []
    for index, (old, new) in enumerate(layout.RELOCATIONS.items()):
        raw = f"def own_operation_{index}():\n    return {index}\n".encode()
        path = root / new
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        rows.append(
            {"before": old, "after": new, "sha256": hashlib.sha256(raw).hexdigest()}
        )
    path = root / layout.API_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(current)
    root_api = root / layout.ROOT_API_PATH
    root_api.write_bytes(b"def own_root():\n    return 3\n")
    original_sha = hashlib.sha256(original).hexdigest()
    monkeypatch.setattr(layout, "PREIMAGE_SHA256", original_sha)
    proof = {
        "schema_version": "lra-uncertainty-source-layout.v1",
        "source_candidate": "a" * 40,
        "preimage_api": {"path": layout.PREIMAGE_PATH, "sha256": original_sha},
        "adopted_api_sha256": hashlib.sha256(current).hexdigest(),
        "module_relocations": rows,
        "module_names": layout.MODULES,
        "native_R_executed": False,
        "browser_executed": False,
        "scientific_admission": False,
    }
    proof_path = root / layout.PROOF_PATH
    proof_path.parent.mkdir(parents=True, exist_ok=True)
    proof_path.write_text(json.dumps(proof))
    monkeypatch.setattr(
        layout, "PROOF_SHA256", hashlib.sha256(proof_path.read_bytes()).hexdigest()
    )

    def revision(repository: Path, historical: str) -> str:
        assert (
            repository == root
            and historical == "1d14065e277e0be39c4cafe6f163ad6f411f36f0"
        )
        return historical

    def blob(repository: Path, member: GitSourceMember) -> bytes:
        assert repository == root
        assert member.repository_path == layout.API_PATH
        assert member.member == layout.PREIMAGE_PATH
        assert member.bytes == 6049
        assert member.sha256 == original_sha
        assert member.source_revision == "1d14065e277e0be39c4cafe6f163ad6f411f36f0"
        assert member.git_blob == "476bdee064d6f38f6920f338af721529254bf501"
        return original

    monkeypatch.setattr(layout, "source_revision", revision)
    monkeypatch.setattr(layout, "read_blob", blob)
    return root


def test_exact_named_layout_retains_original_api_preimage(repository: Path) -> None:
    proof = layout.validated_source_layout(repository)
    assert proof["native_R_executed"] is False
    assert proof["scientific_admission"] is False
    assert (
        hashlib.sha256(
            layout.api_adoption_preimage(repository, repository / layout.API_PATH)
        ).hexdigest()
        == layout.PREIMAGE_SHA256
    )


@pytest.mark.parametrize("name", list(layout.RELOCATIONS))
def test_changed_operation_bytes_refuse(repository: Path, name: str) -> None:
    target = repository / layout.RELOCATIONS[name]
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ReportRebuildError, match="operation source bytes"):
        layout.validated_source_layout(repository)


def test_duplicate_old_operation_owner_refuses(repository: Path) -> None:
    before, after = next(iter(layout.RELOCATIONS.items()))
    target = repository / before
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((repository / after).read_bytes())
    with pytest.raises(ReportRebuildError, match="old operation path"):
        layout.validated_source_layout(repository)


@pytest.mark.parametrize("name", [layout.PROOF_PATH, layout.API_PATH])
def test_changed_api_or_certificate_bytes_refuse(repository: Path, name: str) -> None:
    path = repository / name
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ReportRebuildError):
        layout.validated_source_layout(repository)


def test_current_native_identity_does_not_open_a_historical_source(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: object) -> bytes:
        raise AssertionError("exact current source opened a historical buffer")

    monkeypatch.setattr(layout, "read_source_path", forbidden)
    for name in (layout.API_PATH, layout.ROOT_API_PATH):
        layout.validate_current_native_source(
            repository,
            name,
            hashlib.sha256((repository / name).read_bytes()).hexdigest(),
        )


def test_unchanged_import_ast_outside_named_moves_is_required() -> None:
    prefix = "\n".join("from " + name + " import X" for name in layout.MODULES)
    original = (prefix + "\ndef retained():\n return 1\n").encode()
    current = original
    for old, new in layout.MODULES.items():
        current = current.replace(old.encode(), new.encode())
    assert layout._imports_and_remaining(
        original, moved=False
    ) == layout._imports_and_remaining(current, moved=True)
    assert layout._imports_and_remaining(
        original, moved=False
    ) != layout._imports_and_remaining(
        current.replace(b"return 1", b"return 2"), moved=True
    )


def test_renamed_api_import_alias_is_not_accepted() -> None:
    current = "\n".join(
        "from " + name + " import X as Renamed" for name in layout.MODULES.values()
    )
    with pytest.raises(ReportRebuildError, match="alias differs"):
        layout._imports_and_remaining(current.encode(), moved=True)


@pytest.mark.parametrize("alias", ["symlink", "hardlink"])
def test_current_operation_file_alias_refuses(repository: Path, alias: str) -> None:
    import os

    target = repository / next(iter(layout.RELOCATIONS.values()))
    backing = repository / "backing.py"
    target.rename(backing)
    if alias == "symlink":
        target.symlink_to(backing)
    else:
        os.link(backing, target)
    expected_error = ReportOwnershipError if alias == "symlink" else ReportRebuildError
    with pytest.raises(expected_error):
        layout.validated_source_layout(repository)


@pytest.mark.parametrize("moved", [False, True])
def test_duplicate_named_import_is_refused(moved: bool) -> None:
    names = layout.MODULES.values() if moved else layout.MODULES
    statements = ["from " + name + " import X" for name in names]
    current = "\n".join([*statements, statements[0]])
    with pytest.raises(ReportRebuildError, match="duplicate"):
        layout._imports_and_remaining(current.encode(), moved=moved)


@pytest.mark.parametrize("fault", ["missing_ancestor", "wrong_body"])
def test_api_preimage_transport_must_remain_authenticated(
    repository: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    def unavailable(*args: object) -> bytes:
        if fault == "missing_ancestor":
            raise ReportRebuildError("synthetic original API ancestor absent")
        return b"wrong historical API"

    monkeypatch.setattr(layout, "read_blob", unavailable)
    with pytest.raises(ReportRebuildError):
        layout.validated_source_layout(repository)
    assert not (repository / layout.PREIMAGE_PATH).exists()


def test_rebound_current_api_cannot_hide_other_ast_changes(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api = repository / layout.API_PATH
    api.write_bytes(api.read_bytes().replace(b"return 17", b"return 18"))
    proof_path = repository / layout.PROOF_PATH
    proof = json.loads(proof_path.read_bytes())
    proof["adopted_api_sha256"] = hashlib.sha256(api.read_bytes()).hexdigest()
    proof_path.write_text(json.dumps(proof))
    monkeypatch.setattr(
        layout, "PROOF_SHA256", hashlib.sha256(proof_path.read_bytes()).hexdigest()
    )
    with pytest.raises(ReportRebuildError, match="API AST differs"):
        layout.validated_source_layout(repository)


def test_captured_native_hash_mismatch_refuses_before_adoption(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        layout, "read_source_path", lambda *args: b"wrong captured source"
    )
    with pytest.raises(ReportRebuildError, match="original protected API bytes differ"):
        layout.validate_current_native_source(repository, layout.API_PATH, "0" * 64)
