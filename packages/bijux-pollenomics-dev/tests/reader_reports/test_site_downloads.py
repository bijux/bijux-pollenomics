from collections.abc import Callable
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import NotRequired, Protocol, TypedDict, cast

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


class _GitSourceReader(Protocol):
    """Bind the dynamically loaded Git reader, including its request keyword."""

    def __call__(
        self, root: Path, *arguments: str, request: bytes | None = None
    ) -> bytes:
        """Read exact original Git bytes with an optional request body."""
        ...


@pytest.fixture
def synthetic_pdf_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep PDF boundary fixtures strict; historical authority uses real Git tests."""

    def current_sources(root: Path) -> dict[str, object]:
        lock = json.loads(HOOK._read(root, "presentation/source-lock.json"))
        for relative, expected in lock["sources"].items():
            if hashlib.sha256(HOOK._read(root, relative)).hexdigest() != expected:
                raise ValueError(f"Scientific download deck source changed: {relative}")
        return {}

    monkeypatch.setattr(HOOK, "retained_deck_sources", current_sources)


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


def test_retained_deck_context_admits_original_history_and_exact_current_inputs() -> (
    None
):
    retained = HOOK.retained_deck_sources(ROOT)
    assert retained["context"] == HOOK.RETAINED_CONTEXT
    assert len(retained["historical_inputs"]) == len(retained["current_inputs"]) == 98
    historical = {row["path"]: row["sha256"] for row in retained["historical_inputs"]}
    current = {row["path"]: row["sha256"] for row in retained["current_inputs"]}
    assert set(historical) == set(current)
    assert [name for name in current if current[name] != historical[name]] == [
        "pyproject.toml"
    ]
    before = (ROOT / "presentation/source-lock.json").read_bytes()
    frozen = HOOK.download_bytes(ROOT)
    assert len(frozen) == 12
    manifest = json.loads((ROOT / HOOK.MANIFEST).read_bytes())
    for row in manifest["files"]:
        assert frozen[row["site_uri"]] == (ROOT / row["path"]).read_bytes()
    assert before == (ROOT / "presentation/source-lock.json").read_bytes()


@pytest.mark.parametrize("mutation", ["missing", "unknown", "revision", "metadata"])
def test_retained_deck_context_substitution_refuses(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    read = cast(Callable[[Path, str], bytes], HOOK._read)
    context = json.loads(read(ROOT, HOOK.RETAINED_CONTEXT_PATH))
    if mutation == "unknown":
        context["unreviewed"] = True
    elif mutation == "revision":
        context["source_revision"] = "0" * 40
    elif mutation == "metadata":
        context["security_metadata"]["current_value"] = ["B404"]

    def changed(root: Path, relative: str) -> bytes:
        if relative == HOOK.RETAINED_CONTEXT_PATH:
            if mutation == "missing":
                raise ValueError("Scientific download source unavailable")
            return json.dumps(context).encode()
        return read(root, relative)

    monkeypatch.setattr(HOOK, "_read", changed)
    with pytest.raises(ValueError):
        HOOK.retained_deck_sources(ROOT)


@pytest.mark.parametrize(
    "relative",
    ["presentation/source-lock.json", "pyproject.toml", "presentation/developer.tex"],
)
def test_retained_deck_current_source_drift_refuses(
    monkeypatch: pytest.MonkeyPatch, relative: str
) -> None:
    read = cast(Callable[[Path, str], bytes], HOOK._read)

    def changed(root: Path, name: str) -> bytes:
        value = read(root, name)
        return value + b"\n# changed owning input\n" if name == relative else value

    monkeypatch.setattr(HOOK, "_read", changed)
    with pytest.raises(ValueError, match="changed|differs"):
        HOOK.retained_deck_sources(ROOT)


def test_retained_deck_missing_original_history_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = cast(_GitSourceReader, HOOK._git)

    def missing(root: Path, *arguments: str, request: bytes | None = None) -> bytes:
        if arguments[0] == "merge-base":
            raise subprocess.CalledProcessError(1, ["git", *arguments])
        return command(root, *arguments, request=request)

    monkeypatch.setattr(HOOK, "_git", missing)
    with pytest.raises(subprocess.CalledProcessError):
        HOOK.retained_deck_sources(ROOT)


def test_retained_deck_historical_source_blob_substitution_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    committed = cast(
        Callable[[Path, str, list[str]], dict[str, bytes]], HOOK._committed_inputs
    )

    def changed(root: Path, revision: str, paths: list[str]) -> dict[str, bytes]:
        values = committed(root, revision, paths)
        if revision == HOOK.RETAINED_CONTEXT["source_revision"]:
            values["presentation/source-lock.json"] += b"\n"
        return values

    monkeypatch.setattr(HOOK, "_committed_inputs", changed)
    with pytest.raises(ValueError, match="source lock differs"):
        HOOK.retained_deck_sources(ROOT)


def test_retained_deck_nonregular_git_source_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = cast(_GitSourceReader, HOOK._git)

    def nonregular(root: Path, *arguments: str, request: bytes | None = None) -> bytes:
        value = command(root, *arguments, request=request)
        return (
            value.replace(b"100644 blob", b"120000 blob", 1)
            if arguments[0] == "ls-tree"
            else value
        )

    monkeypatch.setattr(HOOK, "_git", nonregular)
    with pytest.raises(ValueError, match="regular source blobs"):
        HOOK.retained_deck_sources(ROOT)


def test_retained_context_duplicate_json_keys_refuse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read = cast(Callable[[Path, str], bytes], HOOK._read)

    def duplicate(root: Path, relative: str) -> bytes:
        value = read(root, relative)
        if relative == HOOK.RETAINED_CONTEXT_PATH:
            return value.replace(
                b"{", b'{"schema":"retained-deck-source-context.v1",', 1
            )
        return value

    monkeypatch.setattr(HOOK, "_read", duplicate)
    with pytest.raises(ValueError, match="duplicate source keys"):
        HOOK.retained_deck_sources(ROOT)


@pytest.mark.parametrize("alias", ["pyproject.toml", "./pyproject.toml"])
def test_retained_source_duplicate_or_aliased_paths_refuse(alias: str) -> None:
    with pytest.raises(ValueError, match="population|canonical source paths"):
        HOOK._committed_inputs(
            ROOT, HOOK.RETAINED_CONTEXT["source_revision"], ["pyproject.toml", alias]
        )


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


def test_retained_source_physical_executable_mode_substitution_refuses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    command = cast(_GitSourceReader, HOOK._git)

    def changed(root: Path, *arguments: str, request: bytes | None = None) -> bytes:
        value = command(root, *arguments, request=request)
        if arguments[0] == "ls-tree":
            return value.replace(b"100644 blob", b"100755 blob", 1)
        return value

    monkeypatch.setattr(HOOK, "_git", changed)
    with pytest.raises(ValueError, match="physical mode"):
        HOOK.retained_deck_sources(ROOT)


def test_retained_git_reads_disable_replace_objects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def observe(arguments: list[str], **kwargs: object) -> SimpleNamespace:
        assert arguments[:4] == ["git", "--no-replace-objects", "-C", str(ROOT)]
        assert kwargs["check"] is True and kwargs["timeout"] == 30
        return SimpleNamespace(stdout=b"exact committed source")

    monkeypatch.setattr(HOOK.subprocess, "run", observe)
    assert HOOK._git(ROOT, "rev-parse", "HEAD") == b"exact committed source"
