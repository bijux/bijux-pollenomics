import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "science_downloads", ROOT / "configs/docs/science_downloads.py"
)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


def _fixture(root: Path) -> dict:
    def write(relative: str, content: bytes) -> str:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    inventory = "paper_id,canonical_report\n"
    rows = []
    sources = {}
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
    manifest = {
        "schema_version": "scientific-reader-downloads.v1",
        "inputs": inputs,
        "files": rows,
    }
    write(HOOK.MANIFEST, json.dumps(manifest).encode())
    return manifest


def test_downloads_freeze_pdf_bytes_without_writing_sources(tmp_path: Path) -> None:
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
def test_changed_pdf_or_deck_source_refuses(tmp_path: Path, relative: str) -> None:
    _fixture(tmp_path)
    (tmp_path / relative).write_bytes(b"unreviewed replacement")
    with pytest.raises(ValueError, match="changed"):
        HOOK.download_bytes(tmp_path)


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "route", "closure"])
def test_missing_population_duplicate_route_and_closure_refuse(
    tmp_path: Path, mutation: str
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


def test_escaping_input_and_symlink_refuse(tmp_path: Path) -> None:
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
