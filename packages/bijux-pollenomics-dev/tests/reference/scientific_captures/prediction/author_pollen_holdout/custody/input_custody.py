"""Reconcile the complete named source inputs of the observed-pollen holdout."""

import csv
import hashlib
import json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def row(path):
    assert path.is_absolute() and path.resolve() == path and ".." not in path.parts
    assert path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def qualify(repository, private):
    root = (
        repository / "docs/report/publication-replay/landclim-method-profile/reference"
    )
    receipt_path = private / "reference/receipt.json"
    receipt = json.loads(receipt_path.read_bytes())
    assert type(receipt["exit_code"]) is int and receipt["exit_code"] == 0
    assert receipt["input_files_unchanged"] is True
    parity = json.loads((root / "report.json").read_bytes())
    assert sha(receipt_path) == parity["reference_receipt_sha256"]
    crosswalk = private / "reference/taxon-name-crosswalk.csv"
    assert sha(crosswalk) == parity["grids"][0]["crosswalk_sha256"]
    with crosswalk.open(newline="") as f:
        taxa = list(csv.DictReader(f))
    assert (
        len(taxa)
        == len({r["source"] for r in taxa})
        == len({r["prepared"] for r in taxa})
        == 31
    )
    paths = {root / "report.json", receipt_path, crosswalk}
    sites = []
    for grid in ("512", "562"):
        manifest_path = root / grid / "run-manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        current = next(r for r in parity["grids"] if r["grid_id"] == grid)
        assert current["passed"] is True
        assert (
            manifest["parameters"]["source_revision"]
            == "57ead2e2fcc493d099be4e5a3092fc396e1c3d3a"
        )
        assert manifest["parameters"]["profile"] == parity["profile"]
        paths.add(manifest_path)
        list_name = f"run.REVEALS.files/site.list.{grid}.csv"
        site_list = private / "author" / list_name
        assert sha(site_list) == receipt["input_files"][list_name]
        paths.add(site_list)
        names = site_list.read_text().splitlines()
        assert names and len(names) == len(set(names)) == current["sites"]
        for name in names:
            path = private / "author/run.REVEALS.files" / name
            assert sha(path) == receipt["input_files"][f"run.REVEALS.files/{name}"]
            with path.open(newline="") as f:
                raw = list(csv.reader(f))
            assert len(raw) == 34 and len(raw[0]) == 26
            assert raw[0][0] == "TW" and len(set(raw[0][1:])) == 25
            assert [r[0] for r in raw[3:]] == [r["prepared"] for r in taxa]
            paths.add(path)
            sites.append(
                {
                    "grid": grid,
                    "site_id": path.stem.removeprefix("LRAready_"),
                    **row(path),
                }
            )
    assert len(sites) == len({r["site_id"] for r in sites}) == 17
    producer = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/observed_pollen_baseline.py"
    manifest_path = repository / "docs/report/pollen-reconstruction/manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    declared = [r for r in manifest["files"] if r["path"] == producer]
    assert len(declared) == 1 and declared[0]["sha256"] == sha(repository / producer)
    buffered_path = (
        repository
        / "docs/report/pollen-reconstruction/author-buffered-pollen/manifest.json"
    )
    buffered = json.loads(buffered_path.read_bytes())
    assert (
        sha(private / "snapshot-manifest.json")
        == buffered["private_source_manifest_sha256"]
    )
    paths.update({repository / producer, manifest_path, buffered_path})
    return {
        "inputs": [row(p) for p in sorted(paths)],
        "sites": sites,
        "source_grids": ["512", "562"],
        "taxa": 31,
        "original_reference_execution_is_reused": True,
        "source_snapshot_sha256": sha(private / "snapshot-manifest.json"),
    }
