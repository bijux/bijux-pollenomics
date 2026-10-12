"""Bind finite retained GeoJSON downloads to the canonical Pages admission."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SHARED = ROOT / ".bijux/shared/bijux-docs"
EVIDENCE = "artifacts/website-security"
OWNED_ADAPTER = "configs/docs/publication/admission.py"
OWNED_MANIFEST = "configs/docs/publication/downloads.json"
POLICY = EVIDENCE + "/download-policy.json"
SOURCE = EVIDENCE + "/source-identity.json"
SITE = "artifacts/docs/site"
URL = "https://bijux.io/bijux-pollenomics/"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def regular(root: Path, relative: str) -> Path:
    require(isinstance(relative, str), "Download authority requires a text path")
    parts = PurePosixPath(relative)
    require(relative == parts.as_posix()
            and not parts.is_absolute() and bool(parts.parts)
            and not any(p in {".", ".."} or p.startswith(".") for p in parts.parts)
            and not any(c in relative for c in "\\*?[]\n\r\x00"),
            "Download authority requires an exact confined public path")
    current = root
    for part in parts.parts:
        current /= part
        require(not current.is_symlink(), "Download authority refuses symlink paths")
    require(current.is_file(), "Download authority file is missing")
    return current


def committed_hashes(root: Path, source_sha: str, paths: list[str]) -> dict[str, str]:
    # One Git request preserves exact committed authority without spawning a
    # process for each potentially large retained scientific data download.
    request = "".join(f"{source_sha}:{p}\n" for p in paths).encode()
    run = subprocess.run(["git", "-C", str(root), "cat-file", "--batch"],
                         input=request, capture_output=True, check=True)
    stream = io.BytesIO(run.stdout)
    result = {}
    for path in paths:
        header = stream.readline().split()
        require(len(header) == 3 and header[1] == b"blob",
                "Download authority requires an existing committed file")
        content = stream.read(int(header[2]))
        require(stream.read(1) == b"\n", "Committed download stream is incomplete")
        result[path] = digest(content)
    require(not stream.read(), "Committed download stream contains extra records")
    return result


def download_policy(root: Path, site: Path, source_sha: str,
                    base_policy: dict, manifest: dict, committed: dict[str, str]) -> dict:
    require(set(manifest) == {"schema", "scope", "files"} and manifest["schema"] == 1
            and manifest["scope"] == "retained-public-geojson-downloads"
            and isinstance(manifest["files"], list) and len(manifest["files"]) == 50,
            "Download manifest requires the exact reviewed finite population")
    result = json.loads(json.dumps(base_policy))
    seen = set()
    for record in manifest["files"]:
        require(set(record) == {"path", "source", "sha256", "bytes", "kind", "purpose"},
                "Download manifest requires exact source identity fields")
        path, source = record["path"], record["source"]
        require(isinstance(path, str) and path.startswith("report/") and path.endswith(".geojson")
                and source == "docs/" + path and path not in seen,
                "Download manifest requires unique owned GeoJSON source paths")
        seen.add(path)
        expected_kind = ("native-sequence-data" if path ==
                         "report/pollen-reconstruction/swedish-native-sequences/map-summary.geojson"
                         else "geojson-download")
        require(record["kind"] == expected_kind and isinstance(record["purpose"], str)
                and record["purpose"].strip() and isinstance(record["bytes"], int)
                and not isinstance(record["bytes"], bool) and record["bytes"] > 0
                and isinstance(record["sha256"], str) and bool(SHA256.fullmatch(record["sha256"])),
                "Download manifest requires reviewed data purpose and identity")
        authored = regular(root, source).read_bytes()
        public = regular(site, path).read_bytes()
        require(digest(authored) == record["sha256"] == committed.get(source)
                and authored == public and len(public) == record["bytes"],
                "Retained public download differs from its committed owning source")
        body = json.loads(public)
        require(isinstance(body, dict) and body.get("type") in {"Feature", "FeatureCollection"},
                "Retained public download is not a GeoJSON feature surface")
        require(body["type"] != "FeatureCollection" or isinstance(body.get("features"), list),
                "Retained public GeoJSON feature collection is malformed")
        result.setdefault("public_exceptions", []).append(
            {"pattern": path, "purpose": record["purpose"]})
    source_roster = {p.relative_to(root / "docs").as_posix()
                     for p in (root / "docs").rglob("*.geojson") if p.is_file()}
    public_roster = {p.relative_to(site).as_posix() for p in site.rglob("*.geojson") if p.is_file()}
    require(source_roster == public_roster == seen,
            "Retained GeoJSON source/public population differs from reviewed downloads")
    return result


def shared_module(name: str):
    spec = importlib.util.spec_from_file_location("bijux_" + name, SHARED / "security" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def owner_records(root: Path, metadata: dict) -> dict:
    records = {}
    for key, path in (("publication_adapter", OWNED_ADAPTER),
                      ("publication_downloads", OWNED_MANIFEST)):
        record = metadata.get(key)
        require(isinstance(record, dict) and set(record) == {"path", "sha256"}
                and record["path"] == path and record["sha256"] == digest(regular(root, path).read_bytes()),
                "Download authority adapter/manifest differs from checkpoint-bound owner")
        records[key] = record
    return records


def effective_policy() -> tuple[Path, dict]:
    identity = shared_module("build_identity")
    source = json.loads((ROOT / SOURCE).read_text())
    identity.verify_source(ROOT, source)
    expected_sha = os.environ.get("GITHUB_SHA")
    require(not expected_sha or expected_sha == source["repository_source"]["sha"],
            "Download publication checkout differs from dispatched source")
    require(source["site_url"] == URL and source["site_dir"] == SITE
            and source["config"]["path"] == "mkdocs.yml",
            "Download authority requires the exact publication source checkpoint")
    from mkdocs.config import load_config
    configuration = load_config(config_file=str(ROOT / "mkdocs.yml"))
    require(digest((ROOT / "mkdocs.yml").read_bytes()) == source["config"]["sha256"],
            "Download authority owning configuration changed")
    metadata = configuration.extra["bijux"]
    require(configuration.site_url == URL, "Download authority resolved URL differs")
    owner_records(ROOT, metadata)
    manifest = json.loads((ROOT / OWNED_MANIFEST).read_text())
    require(isinstance(manifest, dict) and isinstance(manifest.get("files"), list),
            "Download authority requires a typed manifest")
    paths = [OWNED_ADAPTER, OWNED_MANIFEST]
    for record in manifest["files"]:
        require(isinstance(record, dict) and isinstance(record.get("source"), str),
                "Download authority requires exact source paths")
        regular(ROOT, record["source"])
        paths.append(record["source"])
    committed = committed_hashes(ROOT, source["repository_source"]["sha"], paths)
    require(all(committed[p] == digest(regular(ROOT, p).read_bytes()) for p in paths[:2]),
            "Download authority adapter/manifest differs from committed source")
    base = json.loads((SHARED / "security/policy.json").read_text())
    policy = download_policy(ROOT, ROOT / SITE, source["repository_source"]["sha"], base, manifest, committed)
    selected = ROOT / POLICY
    selected.write_text(json.dumps(policy, indent=2) + "\n")
    record = {"scope": "source-bound finite retained public download policy",
              "source_sha": source["repository_source"]["sha"], "standard_sha": source["standard"]["sha"],
              "configuration": source["config"], "adapter": metadata["publication_adapter"],
              "manifest": metadata["publication_downloads"],
              "base_policy_sha256": digest((SHARED / "security/policy.json").read_bytes()),
              "effective_policy_sha256": digest(selected.read_bytes()), "download_count": len(manifest["files"])}
    (ROOT / EVIDENCE / "download-policy-authority.json").write_text(json.dumps(record, indent=2) + "\n")
    return selected, source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("admit", "verify"))
    options = parser.parse_args()
    try:
        policy, source = effective_policy()
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")
        if options.operation == "admit":
            environment.update(DOCS_PYTHON=sys.executable, DOCS_SITE_DIR=SITE, DOCS_BUILD_SITE_URL=URL,
                               DOCS_SOURCE_IDENTITY=SOURCE, BIJUX_DOCS_SITE_REPORT=EVIDENCE + "/site-verification.json",
                               BIJUX_DOCS_INTERACTIVE_REPORT_OWNER="configs/docs/maps/report-owner.json",
                               BIJUX_DOCS_READER_SOURCE_SHA=source["repository_source"]["sha"])
            environment.pop("BIJUX_DOCS_READER_OWNER", None)
            subprocess.run(["bash", str(SHARED / "tooling/scripts/verify_bijux_docs_site.sh")],
                           cwd=ROOT, env=environment, check=True)
            arguments = ["admit", "--site-dir", SITE, "--site-url", URL,
                         "--source-sha", source["repository_source"]["sha"], "--source-identity", SOURCE,
                         "--build-identity", EVIDENCE + "/build-identity.json",
                         "--verification-report", EVIDENCE + "/site-verification.json",
                         "--csp-report", EVIDENCE + "/csp.json", "--output", EVIDENCE + "/publication.json"]
        else:
            arguments = ["verify", "--manifest", EVIDENCE + "/publication.json", "--require-qualified"]
        subprocess.run([sys.executable, str(SHARED / "security/publication.py"), *arguments,
                        "--policy", str(policy)], cwd=ROOT, env=environment, check=True)
        return 0
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print("Retained download publication refused: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
