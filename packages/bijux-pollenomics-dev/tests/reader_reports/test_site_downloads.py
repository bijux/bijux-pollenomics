import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from typing import NotRequired, TypedDict

import pytest

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "science_downloads", ROOT / "configs/docs/science_downloads.py"
)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


class _DownloadFile(TypedDict):
    """Bind one fixture download to its owned source and exact PDF bytes."""

    path: str
    site_uri: str
    canonical_source: str
    source_sha256: str
    sha256: NotRequired[str]
    bytes: NotRequired[int]


class _DownloadManifest(TypedDict):
    """Retain the complete fixture source and downloadable-file population."""

    schema_version: str
    inputs: dict[str, str]
    files: list[_DownloadFile]


@pytest.fixture
def synthetic_pdf_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep PDF boundary fixtures strict; paper/deck authority is substituted only with this fixture's own bytes."""

    def current_sources(root: Path) -> dict[str, object]:
        lock = json.loads(HOOK._read(root, "presentation/source-lock.json"))
        for relative, expected in lock["sources"].items():
            if hashlib.sha256(HOOK._read(root, relative)).hexdigest() != expected:
                raise ValueError(f"Scientific download deck source changed: {relative}")
        return {}

    monkeypatch.setattr(HOOK, "retained_deck_sources", current_sources)

    def paper_sources(root: Path) -> dict[str, dict[str, object]]:
        manifest = json.loads(HOOK._read(root, HOOK.MANIFEST))
        return {
            row["path"]: {
                "canonical_source": row["canonical_source"],
                "source_sha256": hashlib.sha256(
                    HOOK._read(root, row["canonical_source"])
                ).hexdigest(),
                "sha256": hashlib.sha256(HOOK._read(root, row["path"])).hexdigest(),
                "bytes": len(HOOK._read(root, row["path"])),
            }
            for row in manifest["files"]
            if row["path"].startswith("reports/exports/papers/")
        }

    monkeypatch.setattr(HOOK, "_paper_sources", paper_sources)


def _fixture(root: Path) -> _DownloadManifest:
    def write(relative: str, content: bytes) -> str:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    inventory = "paper_id,canonical_report\n"
    rows: list[_DownloadFile] = []
    sources: dict[str, str] = {}
    for number in range(9):
        identity = f"paper-{number}"
        source = f"reports/science/{identity}.md"
        inventory += f"{identity},{source}\n"
        rows.append(
            {
                "path": f"reports/exports/papers/{identity}.pdf",
                "site_uri": f"assets/science/papers/{identity}.pdf",
                "canonical_source": source,
                "source_sha256": write(source, b"canonical text"),
            }
        )
    for name in HOOK.DECKS:
        source = f"presentation/{name}.tex"
        digest = write(source, b"reviewed deck")
        sources[source] = digest
        rows.append(
            {
                "path": f"presentation/{name}.pdf",
                "site_uri": f"assets/science/presentations/{name}.pdf",
                "canonical_source": source,
                "source_sha256": digest,
            }
        )
    for row in rows:
        content = b"%PDF-1.4\nfixture PDF boundary"
        row["sha256"] = write(row["path"], content)
        row["bytes"] = len(content)
    inputs = {
        "reports/science/paper-accounts.csv": write(
            "reports/science/paper-accounts.csv", inventory.encode()
        ),
        "reports/exports/papers/manifest.json": write(
            "reports/exports/papers/manifest.json", b"{}"
        ),
        "reports/exports/papers/visual-review.json": write(
            "reports/exports/papers/visual-review.json", b"{}"
        ),
        "presentation/source-lock.json": write(
            "presentation/source-lock.json",
            json.dumps({"decks": list(HOOK.DECKS), "sources": sources}).encode(),
        ),
    }
    manifest: _DownloadManifest = {
        "schema_version": "scientific-reader-downloads.v1",
        "inputs": inputs,
        "files": rows,
    }
    write(HOOK.MANIFEST, json.dumps(manifest).encode())
    return manifest


def test_downloads_freeze_pdf_bytes_without_writing_sources(
    tmp_path: Path, synthetic_pdf_sources: None
) -> None:
    _fixture(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = HOOK.download_bytes(tmp_path)
    assert len(result) == 12
    assert all(content.startswith(b"%PDF-") for content in result.values())
    assert before == {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    (tmp_path / "presentation/developer.pdf").write_bytes(b"changed after snapshot")
    assert result["assets/science/presentations/developer.pdf"].startswith(b"%PDF-")


@pytest.mark.parametrize(
    "relative", ["presentation/developer.pdf", "presentation/developer.tex"]
)
def test_changed_pdf_or_deck_source_refuses(
    tmp_path: Path, relative: str, synthetic_pdf_sources: None
) -> None:
    _fixture(tmp_path)
    (tmp_path / relative).write_bytes(b"unreviewed replacement")
    with pytest.raises(ValueError, match="changed"):
        HOOK.download_bytes(tmp_path)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "route", "closure"])
def test_missing_population_duplicate_route_and_closure_refuse(
    tmp_path: Path, mutation: str, synthetic_pdf_sources: None
) -> None:
    manifest = _fixture(tmp_path)
    if mutation == "missing":
        manifest["files"].pop()
    elif mutation == "duplicate":
        manifest["files"][0] = manifest["files"][1]
    elif mutation == "route":
        manifest["files"][0]["site_uri"] = "assets/private.pdf"
    else:
        manifest["inputs"].pop("reports/exports/papers/visual-review.json")
    (tmp_path / HOOK.MANIFEST).write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        HOOK.download_bytes(tmp_path)


def test_escaping_input_and_symlink_refuse(
    tmp_path: Path, synthetic_pdf_sources: None
) -> None:
    root = tmp_path / "repository"
    manifest = _fixture(root)
    outside = tmp_path / "private-source"
    outside.write_bytes(b"private")
    manifest["inputs"]["../private-source"] = hashlib.sha256(b"private").hexdigest()
    (root / HOOK.MANIFEST).write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Unsafe"):
        HOOK.download_bytes(root)
    pdf = root / "presentation/developer.pdf"
    pdf.unlink()
    pdf.symlink_to(outside)
    with pytest.raises(ValueError, match="unavailable"):
        HOOK._read(root, "presentation/developer.pdf")


def test_collision_refuses_before_inserting_any_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(HOOK.runpy, "run_path", lambda *args, **kwargs: None)
    monkeypatch.setattr(HOOK, "download_bytes", lambda _: {"assets/file.pdf": b"%PDF-"})
    files = [SimpleNamespace(src_uri="assets/file.pdf")]
    with pytest.raises(ValueError, match="collides"):
        HOOK.on_files(files, None)
    assert len(files) == 1


@pytest.mark.parametrize("alias", ["pyproject.toml", "./pyproject.toml"])
def test_retained_source_duplicate_or_aliased_paths_refuse(
    tmp_path: Path, alias: str
) -> None:
    with pytest.raises(ValueError, match="population|canonical source paths"):
        HOOK._committed_inputs(tmp_path, "a" * 40, ["pyproject.toml", alias])


@pytest.mark.parametrize("kind", ["hardlink", "symlink", "directory"])
def test_retained_source_nonregular_or_linked_paths_refuse(
    tmp_path: Path, kind: str
) -> None:
    source = tmp_path / "source"
    source.write_bytes(b"retained source")
    alias = tmp_path / "alias"
    if kind == "hardlink":
        alias.hardlink_to(source)
    elif kind == "symlink":
        alias.symlink_to(source)
    else:
        alias.mkdir()
    with pytest.raises(ValueError, match="unavailable"):
        HOOK._read(tmp_path, "alias")


def test_retained_git_reads_disable_replace_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def observe(arguments: list[str], **kwargs: object) -> SimpleNamespace:
        assert arguments[:4] == ["git", "--no-replace-objects", "-C", str(ROOT)]
        assert kwargs["check"] is True and kwargs["timeout"] == 30
        return SimpleNamespace(stdout=b"exact committed source")

    monkeypatch.setattr(HOOK.subprocess, "run", observe)
    assert HOOK._git(ROOT, "rev-parse", "HEAD") == b"exact committed source"


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "missing_tree",
        "symlink",
        "directory",
        "missing_blob",
        "terminator",
        "extra_blob",
    ],
)
def test_committed_source_reader_requires_exact_regular_git_population(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str | None
) -> None:
    sources = {"code/input.py": b"synthetic = True\n", "source.json": b"{}\n"}
    revision = "a" * 40
    paths = list(sources)

    def git(root: Path, *args: str, request: bytes | None = None) -> bytes:
        assert root == tmp_path
        if args[0] == "ls-tree":
            rows = [
                b"100644 blob " + b"b" * 40 + b"\t" + name.encode() for name in paths
            ]
            if mutation == "missing_tree":
                rows.pop()
            elif mutation == "symlink":
                rows[0] = rows[0].replace(b"100644", b"120000")
            elif mutation == "directory":
                rows[0] = rows[0].replace(b"100644 blob", b"040000 tree")
            return b"\0".join(rows) + b"\0"
        assert args == ("cat-file", "--batch")
        assert request == "".join(f"{revision}:{name}\n" for name in paths).encode()
        stream = b"".join(
            b"b" * 40 + b" blob " + str(len(raw)).encode() + b"\n" + raw + b"\n"
            for raw in sources.values()
        )
        if mutation == "missing_blob":
            return b"missing source\n"
        if mutation == "terminator":
            return stream[:-1]
        if mutation == "extra_blob":
            return stream + b"unrequested record\n"
        return stream

    monkeypatch.setattr(HOOK, "_git", git)
    if mutation is None:
        assert HOOK._committed_inputs(tmp_path, revision, paths) == sources
    else:
        with pytest.raises(ValueError):
            HOOK._committed_inputs(tmp_path, revision, paths)


@pytest.mark.parametrize(
    "relative", ["../outside", "/absolute", "./source", "source\\alias", "source\nname"]
)
def test_noncanonical_scientific_source_paths_refuse_before_io(
    tmp_path: Path, relative: str
) -> None:
    with pytest.raises(ValueError, match="Unsafe"):
        HOOK._read(tmp_path, relative)


def test_context_json_duplicate_keys_refuse_without_a_dispatch_assumption() -> None:
    with pytest.raises(ValueError, match="duplicate source keys"):
        HOOK._json_object([("schema", "first"), ("schema", "second")])
