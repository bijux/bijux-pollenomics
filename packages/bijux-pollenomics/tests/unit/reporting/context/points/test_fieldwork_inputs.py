"""Fieldwork media are selected from pinned bytes, independent of output path."""

from hashlib import sha256
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.context.points import fieldwork_inputs
from bijux_pollenomics.reporting.context.points.fieldwork import (
    build_fieldwork_point_layer,
)

PHOTO = "2026-02-26-data-collection.JPG"
VIDEO = "2026-02-26-data-collection.mp4"


def test_held_fieldwork_media_is_staged_after_source_replacement(
    tmp_path: Path,
) -> None:
    gallery = tmp_path / "gallery"
    gallery.mkdir()
    (gallery / PHOTO).write_bytes(b"photo")
    held = fieldwork_inputs.capture_fieldwork_media(
        gallery, {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
    )
    (gallery / PHOTO).write_bytes(b"other")
    (gallery / VIDEO).write_bytes(b"not selected")
    output = tmp_path / "map"
    output.mkdir()
    layer = build_fieldwork_point_layer(output, fieldwork_inputs=held)
    assert layer is not None
    features = cast(list[dict[str, object]], layer["features"])
    assert features[0]["media_links"] == [
        {"kind": "photo", "label": "Field photo", "url": f"fieldwork-media/{PHOTO}"}
    ]
    assert (output / "fieldwork-media" / PHOTO).read_bytes() == b"photo"
    assert not (output / "fieldwork-media" / VIDEO).exists()
    held.validate_staged(output)


def test_capture_refuses_unexpected_presence(tmp_path: Path) -> None:
    (tmp_path / PHOTO).write_bytes(b"photo")
    with pytest.raises(ValueError, match="presence"):
        fieldwork_inputs.capture_fieldwork_media(tmp_path, {PHOTO: None, VIDEO: None})


@pytest.mark.parametrize(
    "mutation", ["wrong_digest", "missing", "symlink", "extra_pin"]
)
def test_capture_rejects_mismatched_inputs(tmp_path: Path, mutation: str) -> None:
    path = tmp_path / PHOTO
    path.write_bytes(b"photo")
    pins = {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
    if mutation == "wrong_digest":
        path.write_bytes(b"changed")
    elif mutation == "missing":
        path.unlink()
    elif mutation == "symlink":
        path.unlink()
        path.symlink_to(tmp_path / "target")
    else:
        pins["other"] = None
    with pytest.raises(ValueError):
        fieldwork_inputs.capture_fieldwork_media(tmp_path, pins)


def test_absent_capture_refuses_later_staged_media(tmp_path: Path) -> None:
    gallery = tmp_path / "gallery"
    gallery.mkdir()
    held = fieldwork_inputs.capture_fieldwork_media(gallery, {PHOTO: None, VIDEO: None})
    out = tmp_path / "map"
    out.mkdir()
    assert build_fieldwork_point_layer(out, fieldwork_inputs=held) is None
    (out / "fieldwork-media").mkdir()
    with pytest.raises(ValueError, match="unselected"):
        held.validate_staged(out)


def test_staged_media_tamper_is_refused(tmp_path: Path) -> None:
    gallery = tmp_path / "gallery"
    gallery.mkdir()
    (gallery / PHOTO).write_bytes(b"photo")
    held = fieldwork_inputs.capture_fieldwork_media(
        gallery, {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
    )
    out = tmp_path / "map"
    out.mkdir()
    assert build_fieldwork_point_layer(out, fieldwork_inputs=held) is not None
    (out / "fieldwork-media" / PHOTO).write_bytes(b"changed")
    with pytest.raises(ValueError, match="differs"):
        held.validate_staged(out)


def test_direct_constructor_cannot_claim_source_absent_when_present(
    tmp_path: Path,
) -> None:
    (tmp_path / PHOTO).write_bytes(b"photo")
    with pytest.raises(ValueError, match="absence"):
        fieldwork_inputs.FieldworkMediaInputs(
            tmp_path, {PHOTO: None, VIDEO: None}, {PHOTO: None, VIDEO: None}
        )


def test_public_map_stages_held_media_and_decoded_relative_links(
    tmp_path: Path,
) -> None:
    import json
    import re
    from typing import Any, cast
    from urllib.parse import urljoin

    from bijux_pollenomics.adna.species.homo_sapiens import (
        build_homo_sapiens_runtime_manifest_for_version_dir,
    )
    from bijux_pollenomics.adna.species.homo_sapiens.map_snapshot import (
        capture_aadr_map_snapshot,
    )
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs
    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        normalize_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        decode_chunk_script,
    )
    from bijux_pollenomics.reporting.service import generate_multi_country_map
    from tests.support.aadr import write_anno_file

    gallery = tmp_path / "gallery"
    gallery.mkdir()
    (gallery / PHOTO).write_bytes(b"photo")
    (gallery / VIDEO).write_bytes(b"video")
    held = fieldwork_inputs.capture_fieldwork_media(
        gallery,
        {PHOTO: sha256(b"photo").hexdigest(), VIDEO: sha256(b"video").hexdigest()},
    )
    (gallery / PHOTO).write_bytes(b"replacement")
    anno = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        anno, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(anno.parent.parent)
    aadr = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": sha256(anno.read_bytes()).hexdigest()}
    )
    output = tmp_path / "nested/report/nordic"
    generate_multi_country_map(
        anno.parent.parent,
        ("Sweden", "Norway"),
        output,
        "Nordic",
        "nordic",
        lake_inputs=SwedenLakeInputs(),
        aadr_map_snapshot=aadr,
        fieldwork_inputs=held,
        published_output_dir=tmp_path / "logical/docs/report/nordic",
    )
    html = (output / "nordic_map.html").read_text()
    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    assert match is not None
    inventory = cast(
        list[dict[str, Any]],
        normalize_asset_inventory(json.loads(match.group(1))["assets"]),
    )
    row = next(
        row
        for row in inventory
        if row["domain"] == "nodes"
        and row.get("layer_key") == "fieldwork-documentation"
    )
    chunk = decode_chunk_script(
        (output / row["path"]).read_bytes(),
        expected_asset_key=row["asset_key"],
        expected_payload_sha256=row["payload_sha256"],
        expected_payload_encoding=row["payload_encoding"],
        expected_decoded_byte_count=row.get("decoded_byte_count"),
    )
    feature = cast(list[dict[str, Any]], chunk["features"])[0]
    assert feature["record_id"] == "bijux:fieldwork:lyngsjon-lake:2026-02-26"
    assert [x["url"] for x in feature["media_links"]] == [
        f"fieldwork-media/{PHOTO}",
        f"fieldwork-media/{VIDEO}",
    ]
    for link, body in zip(feature["media_links"], (b"photo", b"video"), strict=True):
        assert (
            urljoin(
                "https://example.invalid/nested/report/nordic/nordic_map.html",
                link["url"],
            )
            == f"https://example.invalid/nested/report/nordic/{link['url']}"
        )
        assert (output / link["url"]).read_bytes() == body
    contract = json.loads(
        (output / "nordic_map_publication_contract.json").read_bytes()
    )
    assert contract["fieldwork_media_inputs"] == held.identity()
    summary = json.loads((output / "nordic_summary.json").read_bytes())
    recorded = {row["filename"] for row in summary["artifacts"]["extra_files"]}
    assert {f"fieldwork-media/{PHOTO}", f"fieldwork-media/{VIDEO}"} <= recorded


def test_held_media_urls_use_existing_escaped_html_renderer(tmp_path: Path) -> None:
    import json
    from typing import Any

    from tests.unit.reporting.map_document.browser_semantics.support import (
        run_node_json,
        template_block,
    )

    gallery = tmp_path / "gallery"
    gallery.mkdir()
    (gallery / PHOTO).write_bytes(b"photo")
    held = fieldwork_inputs.capture_fieldwork_media(
        gallery, {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
    )
    output = tmp_path / "nested/map"
    output.mkdir(parents=True)
    layer = build_fieldwork_point_layer(output, fieldwork_inputs=held)
    assert layer is not None
    feature = cast(list[dict[str, Any]], layer["features"])[0]
    source = template_block("function escapeHtml", "function titleCaseWords")
    payload = [{**feature["media_links"][0], "label": '<photo & "label">'}]
    html = run_node_json(
        source
        + "\nconsole.log(JSON.stringify(mediaLinksHtml("
        + json.dumps(payload)
        + ")));\n"
    )
    assert f'href="fieldwork-media/{PHOTO}"' in html
    assert "&lt;photo &amp; &quot;label&quot;&gt;" in html


def test_media_presence_change_during_capture_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / PHOTO).write_bytes(b"photo")
    from bijux_pollenomics.core.filesystem import read_regular_file

    original = read_regular_file

    def replace(path: Path, *, max_bytes: int) -> bytes:
        data = original(path, max_bytes=max_bytes)
        (tmp_path / VIDEO).write_bytes(b"appeared")
        return data

    monkeypatch.setattr(fieldwork_inputs, "read_regular_file", replace)
    with pytest.raises(ValueError, match="presence"):
        fieldwork_inputs.capture_fieldwork_media(
            tmp_path, {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
        )


def test_fieldwork_capture_refuses_oversize_media(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / PHOTO).write_bytes(b"photo")
    monkeypatch.setattr(fieldwork_inputs, "_MAX_FILE", 4)
    with pytest.raises(ValueError, match="byte bound"):
        fieldwork_inputs.capture_fieldwork_media(
            tmp_path, {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
        )


def test_missing_gallery_is_not_reported_as_observed_empty(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="absent or uses a symlink"):
        fieldwork_inputs.capture_fieldwork_media(
            tmp_path / "missing", {PHOTO: None, VIDEO: None}
        )


def test_fieldwork_capture_rejects_substituted_builders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.reporting.context import layers

    held = fieldwork_inputs.capture_fieldwork_media(
        tmp_path, {PHOTO: None, VIDEO: None}
    )
    fieldwork_inputs.require_fieldwork_capture_owner(held, layers.build_context_layers)
    with pytest.raises(ValueError, match="maintained"):
        fieldwork_inputs.require_fieldwork_capture_owner(held, lambda: None)
    monkeypatch.setattr(
        layers, "build_fieldwork_point_layer", lambda *_args, **_kwargs: None
    )
    with pytest.raises(ValueError, match="maintained"):
        fieldwork_inputs.require_fieldwork_capture_owner(
            held, layers.build_context_layers
        )


def test_staged_extra_media_is_refused(tmp_path: Path) -> None:
    gallery = tmp_path / "gallery"
    gallery.mkdir()
    (gallery / PHOTO).write_bytes(b"photo")
    held = fieldwork_inputs.capture_fieldwork_media(
        gallery, {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
    )
    out = tmp_path / "map"
    out.mkdir()
    assert build_fieldwork_point_layer(out, fieldwork_inputs=held) is not None
    (out / "fieldwork-media" / VIDEO).write_bytes(b"not selected")
    with pytest.raises(ValueError, match="inventory"):
        held.validate_staged(out)


def test_direct_constructor_refuses_bytes_not_in_gallery(tmp_path: Path) -> None:
    (tmp_path / PHOTO).write_bytes(b"original")
    with pytest.raises(ValueError, match="source bytes"):
        fieldwork_inputs.FieldworkMediaInputs(
            tmp_path,
            {PHOTO: b"replacement", VIDEO: None},
            {PHOTO: sha256(b"replacement").hexdigest(), VIDEO: None},
        )


@pytest.mark.parametrize("tamper", [False, True])
def test_publication_owner_attaches_nested_media_or_preserves_prior_output(
    tmp_path: Path, tamper: bool
) -> None:
    from bijux_pollenomics.reporting.bundles.staging import publish_into_staging_dir

    gallery = tmp_path / "gallery"
    gallery.mkdir()
    (gallery / PHOTO).write_bytes(b"photo")
    held = fieldwork_inputs.capture_fieldwork_media(
        gallery, {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
    )
    output = tmp_path / "nested/report"
    output.mkdir(parents=True)
    (output / "prior.txt").write_bytes(b"prior")

    def publish(staging: Path) -> None:
        assert build_fieldwork_point_layer(staging, fieldwork_inputs=held) is not None
        if tamper:
            (staging / "fieldwork-media" / PHOTO).write_bytes(b"changed")

    if tamper:
        with pytest.raises(ValueError, match="differs"):
            publish_into_staging_dir(output, publish, validate=held.validate_staged)
        assert (output / "prior.txt").read_bytes() == b"prior"
    else:
        publish_into_staging_dir(output, publish, validate=held.validate_staged)
        assert (output / "fieldwork-media" / PHOTO).read_bytes() == b"photo"
        held.validate_staged(output)


@pytest.mark.parametrize("attack", ["context_owner", "fieldwork_owner", "staged_media"])
def test_public_map_refuses_bypass_or_tamper_and_preserves_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    from bijux_pollenomics.adna.species.homo_sapiens import (
        build_homo_sapiens_runtime_manifest_for_version_dir,
    )
    from bijux_pollenomics.adna.species.homo_sapiens.map_snapshot import (
        capture_aadr_map_snapshot,
    )
    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.bundles.atlas_bundle import (
        publish_multi_country_map_bundle,
    )
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs
    from bijux_pollenomics.reporting.context import layers
    from tests.support.aadr import write_anno_file

    gallery = tmp_path / "gallery"
    gallery.mkdir()
    (gallery / PHOTO).write_bytes(b"photo")
    held = fieldwork_inputs.capture_fieldwork_media(
        gallery, {PHOTO: sha256(b"photo").hexdigest(), VIDEO: None}
    )
    anno = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        anno, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(anno.parent.parent)
    aadr = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": sha256(anno.read_bytes()).hexdigest()}
    )
    if attack == "context_owner":
        monkeypatch.setattr(service, "build_context_layers", lambda **_kwargs: None)
    elif attack == "fieldwork_owner":
        monkeypatch.setattr(
            layers, "build_fieldwork_point_layer", lambda *_args, **_kwargs: None
        )
    else:
        real_publish: Any = publish_multi_country_map_bundle

        def publish_and_tamper(staging: Path, **kwargs: Any) -> None:
            real_publish(staging, **kwargs)
            (staging / "fieldwork-media" / PHOTO).write_bytes(b"tampered")

        monkeypatch.setattr(
            service, "publish_multi_country_map_bundle", publish_and_tamper
        )
    output = tmp_path / "map"
    output.mkdir()
    (output / "prior.txt").write_bytes(b"preserve")
    with pytest.raises(ValueError, match="maintained|differs"):
        service.generate_multi_country_map(
            anno.parent.parent,
            ("Sweden", "Norway"),
            output,
            "Nordic",
            "nordic",
            lake_inputs=SwedenLakeInputs(),
            aadr_map_snapshot=aadr,
            fieldwork_inputs=held,
        )
    assert (output / "prior.txt").read_bytes() == b"preserve"


def test_public_map_respects_held_absence_when_gallery_later_appears(
    tmp_path: Path,
) -> None:
    import json

    from bijux_pollenomics.adna.species.homo_sapiens import (
        build_homo_sapiens_runtime_manifest_for_version_dir,
    )
    from bijux_pollenomics.adna.species.homo_sapiens.map_snapshot import (
        capture_aadr_map_snapshot,
    )
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs
    from bijux_pollenomics.reporting.service import generate_multi_country_map
    from tests.support.aadr import write_anno_file

    gallery = tmp_path / "gallery"
    gallery.mkdir()
    held = fieldwork_inputs.capture_fieldwork_media(gallery, {PHOTO: None, VIDEO: None})
    (gallery / PHOTO).write_bytes(b"appeared")
    anno = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        anno, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(anno.parent.parent)
    aadr = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": sha256(anno.read_bytes()).hexdigest()}
    )
    output = tmp_path / "map"
    generate_multi_country_map(
        anno.parent.parent,
        ("Sweden", "Norway"),
        output,
        "Nordic",
        "nordic",
        lake_inputs=SwedenLakeInputs(),
        aadr_map_snapshot=aadr,
        fieldwork_inputs=held,
    )
    contract = json.loads(
        (output / "nordic_map_publication_contract.json").read_bytes()
    )
    assert contract["fieldwork_media_inputs"] == held.identity()
    assert not (output / "fieldwork-media").exists()
    assert all(
        layer["key"] != "fieldwork-documentation" for layer in contract["layer_rows"]
    )


def test_selected_fieldwork_refuses_excluded_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.reporting.context import layers

    held = fieldwork_inputs.capture_fieldwork_media(
        tmp_path, {PHOTO: None, VIDEO: None}
    )
    monkeypatch.setattr(layers, "map_allows_fieldwork_layer", lambda **_kwargs: False)
    with pytest.raises(ValueError, match="unavailable for this map scope"):
        layers.build_context_layers(
            samples=(),
            version="v66",
            output_dir=tmp_path,
            context_root=None,
            fieldwork_inputs=held,
        )
