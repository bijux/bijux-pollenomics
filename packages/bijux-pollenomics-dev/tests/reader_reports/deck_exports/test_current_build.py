"""Compiled Git inputs stay separate from scientific references and old inventories."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import runpy
import subprocess
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.reader_reports.source import MAINTAINED_PRESENTATION_INPUTS

ROOT = Path(__file__).resolve().parents[5]
BUILD = runpy.run_path(str(ROOT / "configs/docs/publication/deck_build.py"))
SPEC = importlib.util.spec_from_file_location(
    "deck_build_downloads", ROOT / "configs/docs/science_downloads.py"
)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)
REVISION = "a" * 40
CURRENT = "b" * 40


@pytest.fixture
def current_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    root = tmp_path / "repository"
    root.mkdir()

    def write(name: str, raw: bytes) -> str:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    rows = []
    inventory = "paper_id,canonical_report\n"
    for index in range(9):
        name = f"paper-{index}"
        source = f"reports/science/{name}.md"
        inventory += f"{name},{source}\n"
        pdf = f"reports/exports/papers/{name}.pdf"
        raw = b"%PDF-explicit synthetic portable boundary\n"
        rows.append(
            {
                "path": pdf,
                "site_uri": f"assets/science/papers/{name}.pdf",
                "canonical_source": source,
                "source_sha256": write(source, b"Synthetic scientific account"),
                "sha256": write(pdf, raw),
                "bytes": len(raw),
            }
        )
    compiled = {}
    for path in BUILD["COMPILED_INPUTS"]:
        write(path, b"Synthetic compiled input, not a real deck\n")
        compiled[path] = (root / path).read_bytes()
    compilers = []
    for name in BUILD["DECKS"]:
        pdf = f"presentation/{name}.pdf"
        raw = b"%PDF-explicit synthetic deck\n"
        rows.append(
            {
                "path": pdf,
                "site_uri": f"assets/science/presentations/{name}.pdf",
                "canonical_source": f"presentation/{name}.tex",
                "sha256": write(pdf, raw),
                "bytes": len(raw),
            }
        )
        compilers.append(
            {
                "deck": name,
                "argv": [
                    "latexmk",
                    *BUILD["FLAGS"],
                    f"-outdir=artifacts/jobs/presentation/{name}",
                    f"presentation/{name}.tex",
                ],
                "actual_exit": 0,
            }
        )
    manifest: dict[str, Any] = {
        "schema_version": "scientific-reader-downloads.v1",
        "files": rows,
        "inputs": {
            "reports/science/paper-accounts.csv": write(
                "reports/science/paper-accounts.csv", inventory.encode()
            ),
            "reports/exports/papers/manifest.json": write(
                "reports/exports/papers/manifest.json", b"{}"
            ),
            "reports/exports/papers/visual-review.json": write(
                "reports/exports/papers/visual-review.json", b"{}"
            ),
        },
        "deck_build": {
            "schema_version": "git-compiled-deck-inputs.v1",
            "source_revision": REVISION,
            "source_date_epoch": 123,
            "inputs": list(BUILD["COMPILED_INPUTS"]),
            "compilers": compilers,
        },
    }
    current = dict(compiled)
    head = [CURRENT]

    def committed(
        repository: Path, revision: str, paths: list[str]
    ) -> dict[str, bytes]:
        assert repository == root and paths == list(BUILD["COMPILED_INPUTS"])
        assert revision in {REVISION, CURRENT, "c" * 40}
        source = compiled if revision == REVISION else current
        return {path: source[path] for path in paths}

    def git(repository: Path, *args: str) -> bytes:
        assert repository == root
        if args[0] == "merge-base":
            assert args == ("merge-base", "--is-ancestor", REVISION, "HEAD")
            return b""
        if args[0] == "show":
            assert args == ("show", "-s", "--format=%ct", REVISION)
            return b"123\n"
        if args[0] == "rev-parse":
            return (head[0] + "\n").encode()
        assert (
            args[:3] == ("ls-tree", "-r", "-z")
            and args[3] in {CURRENT, "c" * 40}
            and args[4] == "--"
        )
        return (
            b"\0".join(
                b"100644 blob " + b"c" * 40 + b"\t" + name.encode() for name in args[5:]
            )
            + b"\0"
        )

    monkeypatch.setattr(HOOK, "_git", git)
    monkeypatch.setattr(HOOK, "_committed_inputs", committed)
    original_read = HOOK._read

    def read(repository: Path, relative: str) -> bytes:
        if relative == "configs/docs/publication/deck_build.py":
            return (ROOT / relative).read_bytes()
        return bytes(original_read(repository, relative))

    monkeypatch.setattr(HOOK, "_read", read)

    def paper_sources(repository: Path) -> dict[str, dict[str, object]]:
        return {
            row["path"]: {
                "canonical_source": row["canonical_source"],
                "source_sha256": hashlib.sha256(
                    read(repository, row["canonical_source"])
                ).hexdigest(),
                "sha256": hashlib.sha256(read(repository, row["path"])).hexdigest(),
                "bytes": len(read(repository, row["path"])),
            }
            for row in manifest["files"]
            if row["path"].startswith("reports/exports/papers/")
        }

    monkeypatch.setattr(HOOK, "_paper_sources", paper_sources)

    def save() -> None:
        write(HOOK.MANIFEST, json.dumps(manifest).encode())

    save()
    return SimpleNamespace(
        root=root,
        manifest=manifest,
        save=save,
        compiled=compiled,
        current=current,
        head=head,
    )


def test_current_build_freezes_twelve_pdfs_without_historical_hash_inventory(
    current_fixture: SimpleNamespace,
) -> None:
    fixture = current_fixture
    result = HOOK.retained_deck_sources(fixture.root)
    assert result["context"]["source_revision"] == REVISION
    assert len(result["current_inputs"]) == 5
    before = {
        path: path.read_bytes() for path in fixture.root.rglob("*") if path.is_file()
    }
    frozen = HOOK.download_bytes(fixture.root)
    assert len(frozen) == 12
    assert before == {path: path.read_bytes() for path in before}
    # Unrelated committed work can move HEAD; the admitted original input blobs stay the same.
    assert REVISION != CURRENT
    (fixture.root / "reports/unrelated.md").write_text("Unrelated new prose")
    assert HOOK.download_bytes(fixture.root) == frozen


def test_compiled_input_set_matches_builder_and_maintained_ownership() -> None:
    builder = runpy.run_path(str(ROOT / "presentation/build.py"))
    assert BUILD["COMPILED_INPUTS"] == builder["COMPILED_INPUTS"]
    assert set(BUILD["COMPILED_INPUTS"]) == set(MAINTAINED_PRESENTATION_INPUTS)


def test_unrelated_head_movement_during_validation_is_allowed(
    current_fixture: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    committed = HOOK._committed_inputs

    def moving(root: Path, revision: str, paths: list[str]) -> dict[str, bytes]:
        result = dict(committed(root, revision, paths))
        if revision == CURRENT:
            current_fixture.head[0] = "c" * 40
        return result

    monkeypatch.setattr(HOOK, "_committed_inputs", moving)
    assert len(HOOK.download_bytes(current_fixture.root)) == 12


@pytest.mark.parametrize("kind", ["dirty", "committed"])
def test_changed_actual_compiled_input_refuses(
    current_fixture: SimpleNamespace, kind: str
) -> None:
    path = "presentation/shared.tex"
    raw = b"Changed compiled TeX input"
    (current_fixture.root / path).write_bytes(raw)
    if kind == "committed":
        current_fixture.current[path] = raw
    with pytest.raises(ValueError, match="Compiled deck input changed"):
        HOOK.download_bytes(current_fixture.root)


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_revision",
        "wrong_revision",
        "missing_input",
        "extra_reference",
        "duplicate_input",
        "epoch",
        "nonzero",
        "incomplete",
        "boolean_exit",
        "missing_compiler",
        "wrong_flags",
        "legacy_inventory",
        "legacy_source_hash",
    ],
)
def test_incomplete_or_mixed_build_contract_refuses(
    current_fixture: SimpleNamespace, mutation: str
) -> None:
    manifest = current_fixture.manifest
    build = manifest["deck_build"]
    if mutation == "missing_revision":
        del build["source_revision"]
    elif mutation == "wrong_revision":
        build["source_revision"] = "not-a-revision"
    elif mutation == "missing_input":
        build["inputs"].pop()
    elif mutation == "extra_reference":
        build["inputs"].append("reports/science/new-study.md")
    elif mutation == "duplicate_input":
        build["inputs"][-1] = build["inputs"][0]
    elif mutation == "epoch":
        build["source_date_epoch"] += 1
    elif mutation == "nonzero":
        build["compilers"][0]["actual_exit"] = 1
    elif mutation == "incomplete":
        build["compilers"][0]["actual_exit"] = None
    elif mutation == "boolean_exit":
        build["compilers"][0]["actual_exit"] = False
    elif mutation == "missing_compiler":
        build["compilers"].pop()
    elif mutation == "wrong_flags":
        build["compilers"][0]["argv"][1] = "-draftmode"
    elif mutation == "legacy_inventory":
        manifest["inputs"]["presentation/source-lock.json"] = hashlib.sha256(
            b"historical"
        ).hexdigest()
        (current_fixture.root / "presentation/source-lock.json").write_bytes(
            b"historical"
        )
    else:
        manifest["files"][-1]["source_sha256"] = "0" * 64
    current_fixture.save()
    with pytest.raises(ValueError):
        HOOK.download_bytes(current_fixture.root)


@pytest.mark.parametrize("cause", ["nonancestor", "missing_blob"])
def test_unavailable_build_history_refuses(
    current_fixture: SimpleNamespace, monkeypatch: pytest.MonkeyPatch, cause: str
) -> None:
    if cause == "missing_blob":

        def missing(*args: Any) -> Any:
            raise ValueError("Retained deck history is missing an exact source")

        monkeypatch.setattr(HOOK, "_committed_inputs", missing)
    else:
        git = HOOK._git

        def nonancestor(root: Path, *args: str) -> bytes:
            if args[0] == "merge-base":
                raise subprocess.CalledProcessError(1, ["git", *args])
            return bytes(git(root, *args))

        monkeypatch.setattr(HOOK, "_git", nonancestor)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        HOOK.download_bytes(current_fixture.root)


@pytest.mark.parametrize(
    "path",
    [
        "presentation/big-picture.pdf",
        "reports/exports/papers/paper-0.pdf",
        "reports/exports/papers/manifest.json",
        "reports/science/paper-0.md",
    ],
)
def test_distributed_pdf_raw_and_scientific_source_integrity_remain(
    current_fixture: SimpleNamespace, path: str
) -> None:
    target = current_fixture.root / path
    target.write_bytes(target.read_bytes() + b"unreviewed changes")
    with pytest.raises(ValueError):
        HOOK.download_bytes(current_fixture.root)


def test_compiled_physical_source_mode_remains_owned(
    current_fixture: SimpleNamespace,
) -> None:
    path = current_fixture.root / "presentation/shared.tex"
    path.chmod(path.stat().st_mode | 0o100)
    with pytest.raises(ValueError, match="physical source mode"):
        HOOK.download_bytes(current_fixture.root)


def test_compiled_input_late_physical_mutation_refuses(
    current_fixture: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    committed = HOOK._committed_inputs
    reads = 0

    def changed(root: Path, revision: str, paths: list[str]) -> dict[str, bytes]:
        nonlocal reads
        result = dict(committed(root, revision, paths))
        if revision == CURRENT:
            reads += 1
            if reads == 2:
                (root / "presentation/shared.tex").write_bytes(b"late input mutation")
        return result

    monkeypatch.setattr(HOOK, "_committed_inputs", changed)
    with pytest.raises(ValueError, match="input changed during validation"):
        HOOK.download_bytes(current_fixture.root)
