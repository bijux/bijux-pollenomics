"""Exercise the finite public-data policy without scientific producers."""
from __future__ import annotations

import copy
from fnmatch import fnmatchcase
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]


def check_static_sources(configuration, policy: dict, downloads: dict) -> int:
    """Check configured static-source selection against the publication policy."""
    from mkdocs.structure.files import get_files
    exceptions = [row["pattern"] for row in policy.get("public_exceptions", [])]
    exceptions.extend(row["path"] for row in downloads["files"])
    selected = [item for item in get_files(configuration)
                if item.inclusion.is_included() and not item.is_documentation_page()]
    failures = []
    for item in selected:
        path = PurePosixPath(item.dest_uri)
        denied = any(part.startswith(".") or part in policy["forbidden_names"]
                     for part in path.parts)
        exception = any(fnmatchcase(item.dest_uri, pattern) for pattern in exceptions)
        if denied or path.name.startswith(("id_rsa", "id_ed25519")):
            failures.append({"source": item.src_uri, "code": "private-file"})
        elif (path.suffix.lower() not in policy["allowed_extensions"]
              or path.suffix.lower() == ".map") and not exception:
            failures.append({"source": item.src_uri, "code": "unadmitted-extension"})
    if failures:
        raise ValueError("Publication source boundary refused: " + json.dumps(failures, sort_keys=True))
    return len(selected)


def main() -> None:
    spec = importlib.util.spec_from_file_location("bijux_download_admission", Path(__file__).with_name("admission.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = json.loads(Path(__file__).with_name("downloads.json").read_text())
    base = json.loads((ROOT / ".bijux/shared/bijux-docs/security/policy.json").read_text())
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    committed = module.committed_hashes(ROOT, head, [r["source"] for r in manifest["files"]])
    destination = ROOT / "artifacts/docs-publication/download-controls"
    destination.mkdir(parents=True, exist_ok=True)
    from mkdocs.config import load_config
    configuration = load_config(config_file=str(ROOT / "mkdocs.yml"))
    metadata = configuration.extra["bijux"]
    module.owner_records(ROOT, metadata)
    selected_static_files = check_static_sources(configuration, base, manifest)
    cases = ["actual_configuration_binds_owned_adapter_and_manifest",
             "actual_selected_static_sources_match_publication_policy"]
    excluded = configuration.exclude_docs
    restored = "/report/method-certification/current-r-oracle/retained-vector-historical-uv.lock"
    patterns = [item for item in excluded.patterns if item.pattern != restored]
    assert len(patterns) == len(excluded.patterns) - 1
    configuration.exclude_docs = type(excluded)(patterns)
    try:
        check_static_sources(configuration, base, manifest)
    except ValueError as error:
        assert restored.lstrip("/") in str(error) and "unadmitted-extension" in str(error)
        cases.append("restored_retained_source_exclusion_refused")
    else:
        raise AssertionError("Restored retained source unexpectedly admitted")
    finally:
        configuration.exclude_docs = excluded
    for name, key, field, value in (
        ("changed_adapter_hash", "publication_adapter", "sha256", "0" * 64),
        ("changed_manifest_hash", "publication_downloads", "sha256", "0" * 64),
        ("foreign_adapter_owner", "publication_adapter", "path", "configs/foreign.py"),
        ("foreign_manifest_owner", "publication_downloads", "path", "configs/foreign.json"),
    ):
        candidate = copy.deepcopy(metadata)
        candidate[key][field] = value
        try:
            module.owner_records(ROOT, candidate)
        except ValueError as error:
            assert "differs from checkpoint-bound owner" in str(error)
            cases.append(name)
        else:
            raise AssertionError(name + " unexpectedly admitted")
    with tempfile.TemporaryDirectory(prefix="download-boundary-", dir=destination) as folder:
        root = Path(folder)
        site = root / "artifacts/site"
        for row in manifest["files"]:
            for relative in (row["source"], "artifacts/site/" + row["path"]):
                p = root / relative
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / row["source"], p)
        policy = module.download_policy(root, site, head, base, manifest, committed)
        assert policy["public_exceptions"][:len(base["public_exceptions"])] == base["public_exceptions"]
        assert {k: v for k, v in policy.items() if k != "public_exceptions"} == {
            k: v for k, v in base.items() if k != "public_exceptions"}
        assert len(policy["public_exceptions"]) - len(base["public_exceptions"]) == 50
        cases.append("exact50_committed_geojson_baseline")

        reasons = {
            "missing_manifest_member": "exact reviewed finite population",
            "extra_manifest_member": "exact reviewed finite population",
            "duplicate_manifest_member": "unique owned GeoJSON source paths",
            "foreign_source_owner": "unique owned GeoJSON source paths",
            "unsupported_declared_hash": "exact source policy fields",
            "unsupported_declared_bytes": "exact source policy fields",
            "wrong_native_resource_kind": "reviewed data purpose and identity",
            "missing_public_purpose": "reviewed data purpose and identity",
            "wildcard_path": "exact confined public path",
            "path_escape": "exact confined public path",
            "private_path": "exact confined public path",
            "changed_public_download": "differs from its committed owning source",
            "missing_public_download": "file is missing",
            "changed_authored_download": "differs from its committed owning source",
            "coordinated_download_changes": "differs from its committed owning source",
            "extra_public_download": "population differs",
            "extra_authored_download": "population differs",
            "missing_committed_source": "differs from its committed owning source",
            "changed_committed_source": "differs from its committed owning source",
            "symlink_public_download": "symlink paths",
            "non_geojson_data": "not a GeoJSON feature surface",
        }

        def refuse(name, changed=None, hashes=None):
            try:
                module.download_policy(root, site, head, base, changed or manifest, hashes or committed)
            except (ValueError, OSError, KeyError, TypeError) as error:
                assert reasons[name] in str(error), (name, str(error))
                if name in {"changed_public_download", "changed_authored_download",
                            "coordinated_download_changes",
                            "missing_committed_source", "changed_committed_source"}:
                    assert manifest["files"][0]["source"] in str(error), (name, str(error))
                    assert manifest["files"][0]["path"] in str(error), (name, str(error))
                cases.append(name)
            else:
                raise AssertionError(name + " unexpectedly admitted")

        for name, mutation in (
            ("missing_manifest_member", lambda d: d["files"].pop()),
            ("extra_manifest_member", lambda d: d["files"].append(copy.deepcopy(d["files"][0]))),
            ("duplicate_manifest_member", lambda d: d["files"].__setitem__(1, copy.deepcopy(d["files"][0]))),
            ("foreign_source_owner", lambda d: d["files"][0].__setitem__("source", "configs/foreign.geojson")),
            ("unsupported_declared_hash", lambda d: d["files"][0].__setitem__("sha256", "0" * 64)),
            ("unsupported_declared_bytes", lambda d: d["files"][0].__setitem__("bytes", 1)),
            ("wrong_native_resource_kind", lambda d: next(r for r in d["files"] if r["kind"] == "native-sequence-data").__setitem__("kind", "geojson-download")),
            ("missing_public_purpose", lambda d: d["files"][0].__setitem__("purpose", "")),
        ):
            candidate = copy.deepcopy(manifest)
            mutation(candidate)
            refuse(name, candidate)
        for name, value in (("wildcard_path", "report/*.geojson"),
                            ("path_escape", "report/../private.geojson"),
                            ("private_path", "report/.git/private.geojson")):
            candidate = copy.deepcopy(manifest)
            candidate["files"][0].update(path=value, source="docs/" + value)
            refuse(name, candidate)
        first = manifest["files"][0]
        path = site / first["path"]
        original = path.read_bytes()
        path.write_bytes(original + b"\n")
        refuse("changed_public_download")
        path.write_bytes(original)
        path.unlink()
        refuse("missing_public_download")
        path.write_bytes(original)
        authored = root / first["source"]
        authored.write_bytes(original + b"\n")
        refuse("changed_authored_download")
        authored.write_bytes(original + b"\n")
        path.write_bytes(original + b"\n")
        refuse("coordinated_download_changes")
        authored.write_bytes(original)
        path.write_bytes(original)
        extra = site / "report/unreviewed.geojson"
        extra.write_text('{"type":"FeatureCollection","features":[]}')
        refuse("extra_public_download")
        extra.unlink()
        extra = root / "docs/report/unreviewed.geojson"
        extra.write_text('{"type":"FeatureCollection","features":[]}')
        refuse("extra_authored_download")
        extra.unlink()
        missing_commit = dict(committed)
        missing_commit.pop(first["source"])
        refuse("missing_committed_source", hashes=missing_commit)
        altered_commit = dict(committed)
        altered_commit[first["source"]] = "0" * 64
        refuse("changed_committed_source", hashes=altered_commit)
        path.unlink()
        path.symlink_to(authored)
        refuse("symlink_public_download")
        path.unlink()
        path.write_bytes(original)
        candidate = copy.deepcopy(manifest)
        invalid = b'{"type":"UnreviewedData"}'
        path.write_bytes(invalid)
        authored.write_bytes(invalid)
        forged = dict(committed)
        forged[first["source"]] = module.digest(invalid)
        refuse("non_geojson_data", candidate, forged)
    result = {"status": "passed", "scope": "finite retained download policy controls; no science or site qualification",
              "cases": cases, "source_sha": head, "selected_static_files": selected_static_files,
              "adapter_sha256": module.digest(Path(module.__file__).read_bytes()),
              "manifest_sha256": module.digest(Path(__file__).with_name("downloads.json").read_bytes()),
              "control_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (destination / "controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": "passed", "cases": len(cases)}))


if __name__ == "__main__":
    main()
