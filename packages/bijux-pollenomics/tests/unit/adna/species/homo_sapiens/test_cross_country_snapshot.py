import hashlib
from pathlib import Path

import pytest

from bijux_pollenomics.adna.species.homo_sapiens import (
    build_homo_sapiens_runtime_manifest_for_version_dir,
)
from bijux_pollenomics.adna.species.homo_sapiens.map_snapshot import (
    capture_aadr_map_snapshot,
)
from tests.support.aadr import write_anno_file


def test_snapshot_retains_per_country_source_after_mutation(tmp_path: Path) -> None:
    path = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        path, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)
    snapshot = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    sweden, _ = snapshot.load_country("Sweden")
    path.write_bytes(path.read_bytes().replace(b"Sweden", b"Norway"))
    norway, _ = snapshot.load_country("Norway")
    assert [x.genetic_id for x in sweden] == ["G1"]
    assert norway == []
    assert snapshot.identity()["runtime_manifest_sha256"]


def test_capture_rejects_changed_or_missing_inventory(tmp_path: Path) -> None:
    path = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        path, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)
    pins = {"ho/witness.anno": hashlib.sha256(path.read_bytes()).hexdigest()}
    with pytest.raises(ValueError):
        capture_aadr_map_snapshot(manifest, {**pins, "ho/extra.anno": "0" * 64})
    path.write_bytes(path.read_bytes().replace(b"Sweden", b"Norway"))
    with pytest.raises(ValueError):
        capture_aadr_map_snapshot(manifest, pins)
    path.unlink()
    with pytest.raises((ValueError, OSError)):
        capture_aadr_map_snapshot(manifest, pins)


def test_snapshot_refuses_fabricated_subsets_and_path_traversal(tmp_path: Path) -> None:
    from dataclasses import replace

    paths = [tmp_path / "v66/ho/first.anno", tmp_path / "v66/1240k/second.anno"]
    for p in paths:
        write_anno_file(
            p, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
        )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(tmp_path / "v66")
    pins = {
        p.relative_to(tmp_path / "v66").as_posix(): hashlib.sha256(
            p.read_bytes()
        ).hexdigest()
        for p in paths
    }
    held = capture_aadr_map_snapshot(manifest, pins)
    with pytest.raises(ValueError):
        replace(
            held, captured=held.captured[:1], expected_sha256=held.expected_sha256[:1]
        )
    with pytest.raises(ValueError):
        replace(
            held,
            captured=tuple(reversed(held.captured)),
            expected_sha256=tuple(reversed(held.expected_sha256)),
        )
    path, body = held.captured[0]
    bad = str(tmp_path / "v66/ho/../ho/first.anno")
    with pytest.raises(ValueError):
        replace(
            held,
            captured=((bad, body), *held.captured[1:]),
            expected_sha256=(
                ("ho/../ho/first.anno", held.expected_sha256[0][1]),
                *held.expected_sha256[1:],
            ),
        )


def test_snapshot_refuses_mutable_nested_pairs(tmp_path: Path) -> None:
    from dataclasses import replace

    path = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        path, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)
    held = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    with pytest.raises(ValueError):
        replace(held, captured=(list(held.captured[0]),))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        replace(held, expected_sha256=(list(held.expected_sha256[0]),))  # type: ignore[arg-type]


def test_public_nordic_map_uses_snapshot_and_records_identity(tmp_path: Path) -> None:
    import json

    from bijux_pollenomics.reporting.service import generate_multi_country_map

    path = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        path, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    release_manifest = path.parent.parent / "release_manifest.json"
    release_manifest.write_text(
        json.dumps(
            {
                "source": "AADR",
                "requested_version": "v66",
                "anno_files": [
                    {
                        "dataset_name": "ho",
                        "filename": "witness.anno",
                        "filesize": path.stat().st_size,
                        "md5": hashlib.md5(
                            path.read_bytes(), usedforsecurity=False
                        ).hexdigest(),
                    }
                ],
            }
        )
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)
    held = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    path.write_bytes(path.read_bytes().replace(b"Sweden", b"Norway"))
    out = tmp_path / "map"
    report = generate_multi_country_map(
        path.parent.parent,
        ("Sweden", "Norway"),
        out,
        "Nordic",
        "nordic",
        aadr_map_snapshot=held,
    )
    assert report.country_sample_counts == {"Sweden": 1, "Norway": 0}
    contract = json.loads((out / "nordic_map_publication_contract.json").read_bytes())
    assert contract["aadr_map_annotation_inputs"] == held.identity()
    import re
    from typing import Any, cast

    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        normalize_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        decode_chunk_script,
    )

    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        (out / "nordic_map.html").read_text(),
        re.S,
    )
    assert match is not None
    inventory = cast(
        list[dict[str, Any]],
        normalize_asset_inventory(json.loads(match.group(1))["assets"]),
    )
    asset = next(
        x for x in inventory if x["domain"] == "nodes" and x.get("layer_key") == "aadr"
    )
    node = cast(
        dict[str, Any],
        decode_chunk_script(
            (out / asset["path"]).read_bytes(),
            expected_asset_key=asset["asset_key"],
            expected_payload_sha256=asset["payload_sha256"],
            expected_payload_encoding=asset["payload_encoding"],
            expected_decoded_byte_count=asset.get("decoded_byte_count"),
        ),
    )
    assert len(node["features"]) == 1
    feature = node["features"][0]
    assert (feature["country"], feature["latitude"], feature["longitude"]) == (
        "Sweden",
        58.5,
        15.1,
    )
    assert {row["label"]: row["value"] for row in feature["popup_rows"]}[
        "Genetic ID"
    ] == "G1"


def test_snapshot_matches_country_dedup_and_rejects_extra_file(tmp_path: Path) -> None:
    from bijux_pollenomics.adna import AdnaSampleQuery, load_species_samples

    path = tmp_path / "v66/ho/first.anno"
    row = "G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"
    write_anno_file(path, [row, row])
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)
    pins = {"ho/first.anno": hashlib.sha256(path.read_bytes()).hexdigest()}
    held = capture_aadr_map_snapshot(manifest, pins)
    samples, counts = held.load_country("Sweden")
    expected, expected_counts = load_species_samples(
        manifest, query=AdnaSampleQuery(political_entity="Sweden")
    )
    assert samples == expected and counts == expected_counts and len(samples) == 1
    write_anno_file(path.parent / "extra.anno", [row])
    with pytest.raises(ValueError, match="inventory"):
        capture_aadr_map_snapshot(manifest, pins)
    assert held.load_country("Sweden") == (samples, counts)


def test_public_map_refuses_fabricated_snapshot_and_wrong_release(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.service import generate_multi_country_map

    path = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        path, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)
    held = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    out = tmp_path / "map"
    out.mkdir()
    (out / "prior").write_text("preserved")
    with pytest.raises(ValueError, match="snapshot"):
        generate_multi_country_map(
            path.parent.parent,
            ("Sweden",),
            out,
            "Nordic",
            "nordic",
            aadr_map_snapshot=object(),  # type: ignore[arg-type]
        )
    from bijux_pollenomics.adna.species.homo_sapiens.map_snapshot import AadrMapSnapshot

    class Fabricated(AadrMapSnapshot):
        pass

    fake = Fabricated(
        held.manifest, held.runtime_manifest_sha256, held.captured, held.expected_sha256
    )
    with pytest.raises(ValueError, match="snapshot"):
        generate_multi_country_map(
            path.parent.parent,
            ("Sweden",),
            out,
            "Nordic",
            "nordic",
            aadr_map_snapshot=fake,
        )
    with pytest.raises(ValueError, match="bound release"):
        generate_multi_country_map(
            tmp_path / "other",
            ("Sweden",),
            out,
            "Nordic",
            "nordic",
            aadr_map_snapshot=held,
        )
    assert (out / "prior").read_text() == "preserved"


def test_snapshot_map_input_guard_refuses_fabricated_samples(tmp_path: Path) -> None:
    from bijux_pollenomics.adna.species.homo_sapiens.map_snapshot import (
        validate_aadr_map_inputs,
    )

    path = tmp_path / "v66/ho/witness.anno"
    write_anno_file(
        path, ["G1\tM1\tX\tKanaljorden\tSweden\t58.5\t15.1\tPaper\t2020\t\t500\tAG\tM"]
    )
    manifest = build_homo_sapiens_runtime_manifest_for_version_dir(path.parent.parent)
    held = capture_aadr_map_snapshot(
        manifest, {"ho/witness.anno": hashlib.sha256(path.read_bytes()).hexdigest()}
    )
    with pytest.raises(ValueError, match="samples differ"):
        validate_aadr_map_inputs(held, "v66", ("Sweden",), (), {"Sweden": 0})
