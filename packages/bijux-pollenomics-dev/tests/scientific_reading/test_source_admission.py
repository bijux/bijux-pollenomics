"""Exercise source/checkpoint/publication byte binding through the actual preparer."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.ci.scientific_reading.contracts import (
    DATA,
    ENTRY,
    ROUTES,
    SITE,
    SITE_URL,
    identity,
)
from bijux_pollenomics_dev.ci.scientific_reading.runner import prepare


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


@pytest.fixture
def candidate(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "source"
    root.mkdir()
    pin = root / ".github/standards/bijux-docs.sha"
    pin.parent.mkdir(parents=True)
    pin.write_text("f" * 40 + "\n")
    rows, public = [], {}
    for index in range(12):
        kind = "papers" if index < 9 else "presentations"
        path = f"reports/exports/{index}.pdf"
        uri = f"assets/science/{kind}/{index}.pdf"
        raw = f"%PDF-1.4\nsynthetic {index}\n".encode()
        source = root / path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(raw)
        rows.append({"path": path, "site_uri": uri, **identity(raw)})
        public[uri] = raw
    write_json(
        root / "reports/exports/site-downloads.json",
        {
            "schema_version": "scientific-reader-downloads.v1",
            "files": rows,
        },
    )
    for path in DATA:
        raw = b"opaque controlled source bytes\n"
        source = root / "docs" / path
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(raw)
        public[path] = raw
    subprocess.run(("git", "init", "--quiet", str(root)), check=True)
    subprocess.run(
        ("git", "-C", str(root), "add", "--", ".github", "reports", "docs"), check=True
    )
    subprocess.run(
        (
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Bijux test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--quiet",
            "-m",
            "test(site): bind synthetic source",
        ),
        check=True,
    )
    accepted = subprocess.check_output(
        ("git", "-C", str(root), "rev-parse", "HEAD"), text=True
    ).strip()
    tree = subprocess.check_output(
        ("git", "-C", str(root), "rev-parse", "HEAD^{tree}"), text=True
    ).strip()
    checkpoint = {
        "repository_source": {"sha": accepted, "tree": tree},
        "site_url": SITE_URL,
        "site_dir": SITE,
        "standard": {"sha": "f" * 40},
    }
    checkpoint_path = root / "artifacts/website-security/source-identity.json"
    write_json(checkpoint_path, checkpoint)
    for path in [ENTRY + "index.html", *(route + "index.html" for route in ROUTES)]:
        public[path] = b"<main><h1>Controlled reader page</h1></main>"
    for path, raw in public.items():
        output = root / SITE / path
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(raw)
    write_json(
        root / "artifacts/website-security/publication.json",
        {
            "schema": 2,
            "repository_source_sha": accepted,
            "standard_sha": "f" * 40,
            "site_url": SITE_URL,
            "site_dir": SITE,
            "qualification": {
                "source": {
                    "receipt": checkpoint,
                    "sha256": identity(checkpoint_path.read_bytes())["sha256"],
                }
            },
            "files": [{"path": path, **identity(raw)} for path, raw in public.items()],
        },
    )
    return root, accepted


def test_preparer_binds_actual_git_source_and_existing_publication(
    candidate: tuple[Path, str],
) -> None:
    root, accepted = candidate
    result = prepare(root, accepted, Path("/controlled-browser"))
    assert result["candidate"]["sha"] == accepted
    assert len(result["downloads"]) == 15
    assert len(result["selected_site"]) == 23


@pytest.mark.parametrize(
    "change",
    [
        "commit",
        "dirty",
        "source_checkpoint",
        "standard",
        "publication",
        "pdf",
        "data",
        "html",
    ],
)
def test_changed_source_or_admitted_bytes_are_refused(
    candidate: tuple[Path, str], change: str
) -> None:
    root, accepted = candidate
    if change == "commit":
        accepted = "0" * 40
    elif change == "dirty":
        (root / "reports/exports/0.pdf").write_bytes(b"%PDF-altered")
    elif change in {"source_checkpoint", "standard"}:
        path = root / "artifacts/website-security/source-identity.json"
        checkpoint = json.loads(path.read_text())
        if change == "standard":
            checkpoint["standard"]["sha"] = "0" * 40
        else:
            checkpoint["repository_source"]["sha"] = "0" * 40
        write_json(path, checkpoint)
    elif change == "publication":
        path = root / "artifacts/website-security/publication.json"
        publication = json.loads(path.read_text())
        publication["repository_source_sha"] = "0" * 40
        write_json(path, publication)
    else:
        path = {
            "pdf": "assets/science/papers/0.pdf",
            "data": DATA[0],
            "html": ENTRY + "index.html",
        }[change]
        (root / SITE / path).write_bytes(b"changed public bytes")
    with pytest.raises(ValueError):
        prepare(root, accepted, Path("/controlled-browser"))
