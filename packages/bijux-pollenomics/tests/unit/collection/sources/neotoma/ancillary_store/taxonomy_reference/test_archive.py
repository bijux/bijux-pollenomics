"""Exercise literal reference custody and reusable dated lookup."""

from dataclasses import replace
from hashlib import sha1, sha256
import importlib
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

Retained = tuple[Path, dict[str, dict[str, Any]], dict[str, Path], dict[str, Path], str]


def api() -> ModuleType:
    """Require the source-specific owner rather than the API-prefix protocol."""
    name = "bijux_pollenomics.collection.sources.neotoma.ancillary_store.taxonomy_reference"
    assert importlib.util.find_spec(name) is not None, (
        "Dated Git reference owner is missing"
    )
    return importlib.import_module(name)


def encoded(value: Any) -> bytes:
    """Keep generated source bytes deterministic."""
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def git_tree(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Generate real Git tree identities for independently pinned metadata."""
    raw = b"".join(
        (row["mode"].lstrip("0") + " " + row["path"]).encode()
        + b"\0"
        + bytes.fromhex(row["sha"])
        for row in sorted(
            rows, key=lambda row: row["path"] + ("/" if row["type"] == "tree" else "")
        )
    )
    digest = sha1(b"tree " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    return {
        "sha": digest,
        "url": f"https://api.github.com/repos/NeotomaDB/Taxonomy-Viewer/git/trees/{digest}",
        "tree": rows,
        "truncated": False,
    }


@pytest.fixture
def retained(tmp_path: Path) -> Retained:
    """Build three real projections and their distinct retained transport evidence."""
    directory = tmp_path / "retained"
    directory.mkdir()
    taxa = {
        str(i): {
            "taxonid": i,
            "taxonname": name,
            "highertaxonid": parent,
            "taxagroupid": group,
            "recdatecreated": "2001-01-01",
            "recdatemodified": None,
        }
        for i, name, parent, group in [
            (1, "native name", None, "VPL"),
            (2, "unknown measure", 2, "UPA"),
            (3, "source synonym", 1, "VPL"),
        ]
    }
    metadata = {
        str(i): {
            "taxonid": i,
            "author": None,
            "publicationid": 99 if i == 1 else None,
            "publication": "fallback reference" if i == 1 else None,
            "citation": None,
            "publicationYear": None,
            "validatorid": None,
            "validatorName": None,
            "validatedate": "2010-02-03",
        }
        for i in range(1, 4)
    }
    synonyms = [
        {
            "valid_id": 1,
            "valid_name": "native name",
            "taxagroupid": "VPL",
            "synonyms": [
                {
                    "invalid_id": 3,
                    "invalid_name": "source synonym",
                    "synonymtypeid": 4,
                    "synonymtype": "native assertion",
                    "recdatecreated": created,
                    "recdatemodified": None,
                }
                for created in ["2005-01-01T00:00:00", "2005-01-01T00:00:51"]
            ],
        }
    ]
    documents = {
        "taxa_snapshot.json": {
            "generated_at": "2026-11-02T08:54:54+00:00",
            "taxa": taxa,
        },
        "taxon_metadata.json": metadata,
        "all_synonyms.json": synonyms,
    }
    files = {}
    for name, value in documents.items():
        raw = encoded(value)
        (directory / name).write_bytes(raw)
        files[name] = {
            "bytes": len(raw),
            "sha256": sha256(raw).hexdigest(),
            "git_blob": sha1(
                b"blob " + str(len(raw)).encode() + b"\0" + raw
            ).hexdigest(),
        }
    data = git_tree(
        [
            {
                "path": name,
                "mode": "100644",
                "type": "blob",
                "sha": row["git_blob"],
                "size": row["bytes"],
            }
            for name, row in files.items()
        ]
    )
    root = git_tree(
        [{"path": "data", "mode": "040000", "type": "tree", "sha": data["sha"]}]
    )
    revision = "a" * 40
    commit = {
        "sha": revision,
        "url": f"https://api.github.com/repos/NeotomaDB/Taxonomy-Viewer/git/commits/{revision}",
        "tree": {"sha": root["sha"], "url": root["url"]},
        "committer": {"date": "2026-11-02T08:54:59Z"},
    }
    evidence = {}
    for name, value in [("commit", commit), ("root_tree", root), ("data_tree", data)]:
        path = directory / (name + ".json")
        path.write_bytes(encoded(value))
        evidence[name] = path
    transport = {}
    for name in files:
        path = directory / (name + ".transport.json")
        url = f"https://raw.githubusercontent.com/NeotomaDB/Taxonomy-Viewer/{revision}/data/{name}"
        path.write_bytes(
            encoded(
                {
                    "url": url,
                    "url_effective": url,
                    "http_code": 200,
                    "ssl_verify_result": 0,
                    "num_redirects": 0,
                    "size_download": files[name]["bytes"],
                    "time_total": 0.1,
                    "filename_effective": "/Users/generated/artifacts/private-file",
                    "local_ip": "192.0.2.1",
                    "local_port": 1234,
                }
            )
        )
        transport[name] = path
    return directory, files, evidence, transport, revision


def source(api_module: ModuleType, retained: Retained) -> Any:
    """Bind explicit independent local pins without granting current API authority."""
    directory, files, evidence, transport, revision = retained

    def pinned(path: Path) -> Any:
        raw = path.read_bytes()
        return api_module.NeotomaTaxonomyReferenceFile(
            path, len(raw), sha256(raw).hexdigest()
        )

    return api_module.NeotomaTaxonomyReferenceSource(
        revision=revision,
        files={name: pinned(directory / name) for name in files},
        git_metadata={name: pinned(path) for name, path in evidence.items()},
        transport={name: pinned(path) for name, path in transport.items()},
        intake_intervals=dict.fromkeys(
            files, ("2026-11-17T18:54:03+00:00", "2026-11-17T18:54:07+00:00")
        ),
        attribution="Neotoma Paleoecology Database and source classification contributors; see native reference fields.",
    )


def publish(retained: Retained, tmp_path: Path) -> tuple[ModuleType, Path, Any, str]:
    """Exercise the actual maintained publisher, not a prebuilt accepted flag."""
    owner = api()
    provenance = source(owner, retained)
    directory = tmp_path / "archive"
    manifest = owner.write_neotoma_taxonomy_reference_archive(
        directory, source_provenance=provenance
    )
    pin = sha256((directory / "manifest.json").read_bytes()).hexdigest()
    return owner, directory, manifest, pin


def test_literal_lookup_preserves_dates_fallback_and_positional_assertions(
    retained: Retained, tmp_path: Path
) -> None:
    owner, directory, manifest, pin = publish(retained, tmp_path)
    rows = owner.read_neotoma_taxonomy_reference_taxa(
        directory, expected_manifest_sha256=pin, taxon_ids=(2, 1)
    )
    assert [row.native_id for row in rows] == [2, 1]
    assert rows[0].taxon["highertaxonid"] == 2
    assert rows[1].taxon["highertaxonid"] is None
    assert rows[1].metadata["publication"] == "fallback reference"
    assert rows[1].metadata["citation"] is None
    assert rows[1].metadata["validatedate"] == "2010-02-03"
    assert [
        (row.group_position, row.assertion_position) for row in rows[1].synonyms
    ] == [(0, 0), (0, 1)]
    assert [row.fields["recdatecreated"] for row in rows[1].synonyms] == [
        "2005-01-01T00:00:00",
        "2005-01-01T00:00:51",
    ]
    assert manifest.scientific_admission == "not_asserted"
    assert rows[1].source_generated_at == "2026-11-02T08:54:54+00:00"
    with pytest.raises(TypeError):
        rows[1].taxon["taxonname"] = "changed"
    for name in retained[1]:
        assert (directory / "originals" / name).read_bytes() == (
            retained[0] / name
        ).read_bytes()


def test_public_transport_is_labeled_portable_projection(
    retained: Retained, tmp_path: Path
) -> None:
    _, directory, _, _ = publish(retained, tmp_path)
    raw = (directory / "provenance.json").read_bytes()
    assert (
        b"/Users/" not in raw and b"artifacts/" not in raw and b"192.0.2.1" not in raw
    )
    provenance = json.loads(raw)
    assert (
        provenance["transport_scope"]
        == "portable_projection_of_retained_github_transport"
    )
    assert provenance["current_roles_revalidated"] is False
    assert provenance["source_status_available"] is False
    assert provenance["database_dates_are_sample_ages"] is False
    assert all(row["source_record_sha256"] for row in provenance["transport"].values())


@pytest.mark.parametrize("ids", [(True,), (1, 1), (999,), (-1,)])
def test_selected_ids_require_unique_native_identity(
    retained: Retained, tmp_path: Path, ids: tuple[object, ...]
) -> None:
    owner, directory, _, pin = publish(retained, tmp_path)
    with pytest.raises(ValueError):
        owner.read_neotoma_taxonomy_reference_taxa(
            directory, expected_manifest_sha256=pin, taxon_ids=ids
        )


def test_independently_pinned_tree_membership_is_required(
    retained: Retained, tmp_path: Path
) -> None:
    owner = api()
    provenance = source(owner, retained)
    path = retained[2]["data_tree"]
    value = json.loads(path.read_bytes())
    value["tree"][0]["sha"] = "b" * 40
    path.write_bytes(encoded(value))
    with pytest.raises(ValueError):
        owner.write_neotoma_taxonomy_reference_archive(
            tmp_path / "archive", source_provenance=provenance
        )
    assert not (tmp_path / "archive").exists()


def test_existing_destination_is_preserved(retained: Retained, tmp_path: Path) -> None:
    owner = api()
    provenance = source(owner, retained)
    directory = tmp_path / "archive"
    directory.mkdir()
    (directory / "foreign").write_text("preserve")
    with pytest.raises(FileExistsError):
        owner.write_neotoma_taxonomy_reference_archive(
            directory, source_provenance=provenance
        )
    assert (directory / "foreign").read_text() == "preserve"


def test_inventory_leaves_originals_unread_and_batch_opens_each_once(
    retained: Retained, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, directory, _, pin = publish(retained, tmp_path)
    real_open = os.open
    original_opens = []

    def observed(path: Any, *args: Any, **kwargs: Any) -> int:
        if not isinstance(path, int) and Path(path).name in retained[1]:
            original_opens.append(Path(path).name)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", observed)
    inventory = owner.read_neotoma_taxonomy_reference_inventory(
        directory, expected_manifest_sha256=pin
    )
    assert inventory.source_entity_bodies_verified is False
    assert not original_opens
    owner.read_neotoma_taxonomy_reference_taxa(
        directory, expected_manifest_sha256=pin, taxon_ids=(1, 2)
    )
    assert sorted(original_opens) == sorted(retained[1])


def test_changed_original_is_refused_before_its_semantic_decode(
    retained: Retained, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner, directory, _, pin = publish(retained, tmp_path)
    original = directory / "originals/taxa_snapshot.json"
    changed = original.read_bytes().replace(b"native name", b"other label")
    original.write_bytes(changed)
    reading = importlib.import_module(owner.__name__ + ".reading")
    decode = reading.decode
    decoded = []

    def observed(raw: bytes) -> Any:
        decoded.append(raw)
        return decode(raw)

    monkeypatch.setattr(reading, "decode", observed)
    with pytest.raises(ValueError, match="hash differs"):
        owner.read_neotoma_taxonomy_reference_taxa(
            directory, expected_manifest_sha256=pin, taxon_ids=(1,)
        )
    assert changed not in decoded


def test_rehashed_foreign_git_tree_still_needs_commit_membership(
    retained: Retained, tmp_path: Path
) -> None:
    owner = api()
    directory, files, evidence, transport, revision = retained
    original = json.loads(evidence["root_tree"].read_bytes())
    original["tree"][0]["sha"] = "b" * 40
    evidence["root_tree"].write_bytes(encoded(git_tree(original["tree"])))
    provenance = source(owner, (directory, files, evidence, transport, revision))
    with pytest.raises(ValueError, match="commit membership"):
        owner.write_neotoma_taxonomy_reference_archive(
            tmp_path / "archive", source_provenance=provenance
        )
    assert not (tmp_path / "archive").exists()


def test_source_binding_copies_borrowed_file_map(retained: Retained) -> None:
    owner = api()
    original = source(owner, retained)

    borrowed = dict(original.files)
    bound = replace(original, files=borrowed)
    borrowed.clear()
    assert set(bound.files) == set(retained[1])
    with pytest.raises(TypeError):
        bound.files["taxa_snapshot.json"] = original.files["taxa_snapshot.json"]


def test_parent_substitution_cannot_publish_into_replacement(
    retained: Retained, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = api()
    provenance = source(owner, retained)
    parent = tmp_path / "output-parent"
    parent.mkdir()
    original_parent = tmp_path / "original-parent"
    publication = importlib.import_module(owner.__name__ + ".publication")
    real_publish = publication.publish_owned_source_tree
    fired = []

    def substitute(*args: Any, **kwargs: Any) -> Any:
        fired.append(True)
        parent.rename(original_parent)
        parent.mkdir()
        return real_publish(*args, **kwargs)

    monkeypatch.setattr(publication, "publish_owned_source_tree", substitute)
    with pytest.raises(FileNotFoundError, match=r"\.archive\.staging"):
        owner.write_neotoma_taxonomy_reference_archive(
            parent / "archive", source_provenance=provenance
        )
    assert fired == [True]
    assert not list(parent.iterdir())
    assert list(original_parent.iterdir())
