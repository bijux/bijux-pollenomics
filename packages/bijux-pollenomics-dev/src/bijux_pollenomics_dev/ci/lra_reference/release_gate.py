"""Require same-revision actual-R CI evidence before release; never publish or wait."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any
import zipfile

from .contracts import ReferenceRefusal, read_json
from .evidence import EXTENDED_CASE_IDS, validate_bundle
from .remote import EvidenceReader, GitHubReader, collection
from .source_identity import inspect_source_identity
from .sources import SOURCE_STATUS_ARGUMENTS, SOURCE_TREE_ARGUMENTS, source_inventory

LOCK_PATH = "configs/ci/lra-r-source-lock.v1.json"
WORKFLOWS = frozenset(
    {".github/workflows/verify.yml", ".github/workflows/lra-reference.yml"}
)
JOB_NAMES = frozenset(
    {"lra-live-r-certification", "lra-reference / lra-live-r-certification"}
)
PARITY_JOB_NAMES = frozenset(
    {"lra-native-live-r-parity", "lra-reference / lra-native-live-r-parity"}
)


def git_bytes(repository: Path, *arguments: str) -> bytes:
    """Only small source-identity reads; no generic process execution interface."""
    if not arguments or (
        arguments[0] not in {"rev-parse", "show"}
        and arguments not in {SOURCE_STATUS_ARGUMENTS, SOURCE_TREE_ARGUMENTS}
    ):
        raise ReferenceRefusal("Unsupported release source query")
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            process = subprocess.run(
                ["git", *arguments],
                cwd=repository,
                stdout=stdout,
                stderr=stderr,
                timeout=15,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            raise ReferenceRefusal("Release source query failed or timed out") from None
        if process.returncode:
            raise ReferenceRefusal("Release source revision or tag is unavailable")
        stdout.seek(0)
        data = stdout.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise ReferenceRefusal("Release source query exceeded byte limit")
        return data


def require_clean_checkout(repository: Path) -> None:
    """The admitted inventory must belong to the declared committed tree."""
    if git_bytes(repository, *SOURCE_STATUS_ARGUMENTS).strip():
        raise ReferenceRefusal(
            "Relevant source checkout has uncommitted or untracked files"
        )


def _positive_id(value: Any) -> int:
    if type(value) is not int or value < 1:
        raise ReferenceRefusal("GitHub run/job/artifact identity is invalid")
    return value


def select_run(
    rows: list[dict[str, Any]], repository: str, target_sha: str
) -> dict[str, Any]:
    """Select the latest completed successful run for the target revision."""
    matching = [
        row
        for row in rows
        if row.get("head_sha") == target_sha
        and row.get("path", "").split("@", 1)[0] in WORKFLOWS
        and row.get("event") in {"push", "workflow_dispatch"}
        and row.get("head_repository", {}).get("full_name") == repository
    ]
    if not matching:
        raise ReferenceRefusal("No same-revision certification workflow run exists")
    selected = max(matching, key=lambda row: _positive_id(row.get("id")))
    if selected.get("status") != "completed" or selected.get("conclusion") != "success":
        raise ReferenceRefusal(
            "Latest same-revision certification run is pending, skipped or failed"
        )
    _positive_id(selected.get("run_attempt"))
    return selected


def _extract_archive(data: bytes, destination: Path) -> None:
    if destination.exists():
        raise ReferenceRefusal("Retrieved evidence destination already exists")
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        names = [member.filename for member in members]
        if (
            len(names) != len(set(names))
            or len(names) > 2000
            or sum(member.file_size for member in members) > 128 * 1024 * 1024
        ):
            raise ReferenceRefusal(
                "Retrieved evidence archive exceeds bounded inventory or duplicates a path"
            )
        for member in members:
            path = PurePosixPath(member.filename)
            mode = (member.external_attr >> 16) & 0o170000
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in member.filename
                or str(path) != member.filename.rstrip("/")
                or mode not in {0, 0o100000, 0o040000}
            ):
                raise ReferenceRefusal("Unsafe retrieved evidence archive member")
        destination.mkdir(parents=True)
        for member in members:
            output_path = destination / member.filename
            if member.is_dir():
                output_path.mkdir(parents=True, exist_ok=True)
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(archive.read(member))


def _matching_job(
    jobs: list[dict[str, Any]], names: frozenset[str], target_sha: str, run_id: int
) -> int:
    matching = [job for job in jobs if job.get("name") in names]
    if (
        len(matching) != 1
        or matching[0].get("head_sha") != target_sha
        or matching[0].get("status") != "completed"
        or matching[0].get("conclusion") != "success"
        or matching[0].get("run_id") != run_id
    ):
        raise ReferenceRefusal("Completed certification or parity job is missing")
    return _positive_id(matching[0].get("id"))


def _matching_artifact(
    artifacts: list[dict[str, Any]], name: str, run_id: int, target_sha: str
) -> dict[str, Any]:
    matching = [row for row in artifacts if row.get("name") == name]
    if len(matching) != 1:
        raise ReferenceRefusal(
            "Same-attempt certification or parity artifact is missing"
        )
    artifact = matching[0]
    _positive_id(artifact.get("id"))
    if (
        artifact.get("expired") is not False
        or artifact.get("workflow_run", {}).get("id") != run_id
        or artifact.get("workflow_run", {}).get("head_sha") != target_sha
        or not isinstance(artifact.get("digest"), str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", artifact["digest"]) is None
    ):
        raise ReferenceRefusal("Certification or parity artifact identity is invalid")
    return artifact


def _retrieve_artifact(
    reader: EvidenceReader, prefix: str, artifact: dict[str, Any], destination: Path
) -> None:
    data = reader.read(prefix + f"/artifacts/{artifact['id']}/zip")
    if "sha256:" + hashlib.sha256(data).hexdigest() != artifact["digest"]:
        raise ReferenceRefusal("Downloaded archive bytes differ from provider digest")
    _extract_archive(data, destination)


def _verify_parity_receipt(output: Path, target_sha: str, lock_hash: str) -> str:
    receipt = read_json((output / "parity/report.json").read_bytes())
    manifest_bytes = (output / "bundle/oracle/case_manifest.json").read_bytes()
    manifest = read_json(manifest_bytes)
    if not isinstance(receipt, dict) or not isinstance(manifest, list):
        raise ReferenceRefusal("Parity receipt or case inventory is invalid")
    case_ids = [row.get("id") for row in manifest if isinstance(row, dict)]
    if len(manifest) != 43 or len(case_ids) != 43 or set(case_ids) != EXTENDED_CASE_IDS:
        raise ReferenceRefusal("Live-R case inventory is incomplete")
    expected = {
        "schema_version": "lra-native-live-r-parity-gate.v1",
        "status": "passed",
        "target_sha": target_sha,
        "case_count": 43,
        "case_ids": case_ids,
        "case_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "case_input_sha256": {row["id"]: row["input_sha256"] for row in manifest},
        "python_expected_sha256": {
            row["id"]: row["python_expected_sha256"] for row in manifest
        },
        "source_lock_sha256": lock_hash,
        "live_r_certificate_sha256": hashlib.sha256(
            (output / "bundle/certificate.json").read_bytes()
        ).hexdigest(),
        "live_R_executed": True,
    }
    if receipt != expected:
        raise ReferenceRefusal("Parity receipt differs from certified live-R cases")
    return hashlib.sha256((output / "parity/report.json").read_bytes()).hexdigest()


def verify_release(
    *,
    repository_root: Path,
    repository: str,
    target_sha: str,
    release_tag: str,
    output: Path,
    reader: EvidenceReader,
) -> dict[str, Any]:
    """Verify same-revision R evidence and write a local release receipt."""
    if (
        re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository) is None
        or re.fullmatch(r"[0-9a-f]{40}", target_sha) is None
        or re.fullmatch(r"v[0-9A-Za-z][0-9A-Za-z._+-]*", release_tag) is None
    ):
        raise ReferenceRefusal("Invalid release repository, SHA or tag")
    head = git_bytes(repository_root, "rev-parse", "--verify", "HEAD").decode().strip()
    tag = (
        git_bytes(
            repository_root,
            "rev-parse",
            "--verify",
            f"refs/tags/{release_tag}^{{commit}}",
        )
        .decode()
        .strip()
    )
    if head != target_sha or tag != target_sha:
        raise ReferenceRefusal("Release tag, checkout and target SHA differ")
    target_tree = (
        git_bytes(repository_root, "rev-parse", "--verify", target_sha + "^{tree}")
        .decode()
        .strip()
    )
    require_clean_checkout(repository_root)
    source_identity = inspect_source_identity(
        repository_root, git_bytes(repository_root, *SOURCE_TREE_ARGUMENTS)
    )
    executed_sources = source_identity.tracked_files
    lock_bytes = git_bytes(repository_root, "show", f"{target_sha}:{LOCK_PATH}")
    lock_hash = hashlib.sha256(lock_bytes).hexdigest()
    prefix = f"/repos/{repository}/actions"
    runs = collection(reader, prefix + "/runs?head_sha=" + target_sha, "workflow_runs")
    run = select_run(runs, repository, target_sha)
    run_id = _positive_id(run["id"])
    attempt = _positive_id(run["run_attempt"])
    jobs = collection(
        reader, prefix + f"/runs/{run_id}/attempts/{attempt}/jobs", "jobs"
    )
    job_id = _matching_job(jobs, JOB_NAMES, target_sha, run_id)
    parity_job_id = _matching_job(jobs, PARITY_JOB_NAMES, target_sha, run_id)
    artifacts = collection(reader, prefix + f"/runs/{run_id}/artifacts", "artifacts")
    artifact = _matching_artifact(
        artifacts, f"lra-live-r-{target_sha}-attempt-{attempt}", run_id, target_sha
    )
    parity_artifact = _matching_artifact(
        artifacts,
        f"lra-native-live-r-{target_sha}-attempt-{attempt}",
        run_id,
        target_sha,
    )
    artifact_id = artifact["id"]
    parity_artifact_id = parity_artifact["id"]
    digest = artifact["digest"]
    _retrieve_artifact(reader, prefix, artifact, output / "bundle")
    _retrieve_artifact(reader, prefix, parity_artifact, output / "parity")
    certificate = validate_bundle(
        output / "bundle",
        target_sha=target_sha,
        expected_lock_sha256=lock_hash,
        expected_run=(repository, run_id, attempt),
    )
    if (
        certificate.get("source_tree") != target_tree
        or certificate.get("source_files") != executed_sources
    ):
        raise ReferenceRefusal(
            "Certificate executable sources differ from the release checkout"
        )
    parity_receipt_hash = _verify_parity_receipt(output, target_sha, lock_hash)
    latest = select_run(
        collection(reader, prefix + "/runs?head_sha=" + target_sha, "workflow_runs"),
        repository,
        target_sha,
    )
    if latest["id"] != run_id or latest["run_attempt"] != attempt:
        raise ReferenceRefusal(
            "A newer certification run/attempt appeared during retrieval"
        )
    after = read_json(reader.read(prefix + f"/runs/{run_id}"))
    after_artifact = read_json(reader.read(prefix + f"/artifacts/{artifact_id}"))
    after_parity_artifact = read_json(
        reader.read(prefix + f"/artifacts/{parity_artifact_id}")
    )
    for field in ("id", "run_attempt", "head_sha", "status", "conclusion"):
        if after.get(field) != run.get(field):
            raise ReferenceRefusal(
                "Certification workflow changed during evidence retrieval"
            )
    for field in ("id", "name", "digest", "expired", "workflow_run"):
        if after_artifact.get(field) != artifact.get(field):
            raise ReferenceRefusal(
                "Certification artifact changed during evidence retrieval"
            )
        if after_parity_artifact.get(field) != parity_artifact.get(field):
            raise ReferenceRefusal("Parity artifact changed during evidence retrieval")
    if (
        git_bytes(repository_root, "rev-parse", "--verify", "HEAD").decode().strip()
        != target_sha
        or git_bytes(
            repository_root,
            "rev-parse",
            "--verify",
            f"refs/tags/{release_tag}^{{commit}}",
        )
        .decode()
        .strip()
        != target_sha
    ):
        raise ReferenceRefusal("Release checkout/tag changed during evidence retrieval")
    require_clean_checkout(repository_root)
    if source_inventory(repository_root) != source_identity.executed_files:
        raise ReferenceRefusal(
            "Release executable sources changed during evidence retrieval"
        )
    receipt = {
        "schema_version": "lra-release-evidence.v1",
        "status": "passed",
        "repository": repository,
        "target_sha": target_sha,
        "release_tag": release_tag,
        "run_id": run_id,
        "run_attempt": attempt,
        "job_id": job_id,
        "parity_job_id": parity_job_id,
        "artifact_id": artifact_id,
        "artifact_digest": digest,
        "parity_artifact_id": parity_artifact_id,
        "parity_artifact_digest": parity_artifact["digest"],
        "parity_receipt_sha256": parity_receipt_hash,
        "lock_sha256": lock_hash,
        "certificate_sha256": hashlib.sha256(
            (output / "bundle/certificate.json").read_bytes()
        ).hexdigest(),
        "profile_id": certificate["profile_id"],
        "published": False,
    }
    (output / "release-evidence.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main() -> int:
    """Check a release candidate and retain its evidence or refusal receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--release-tag", required=True)
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    base = args.repository_root / "artifacts/bijux-pollenomics-lra/release-evidence"
    base.mkdir(parents=True, exist_ok=True)
    output = args.output or Path(tempfile.mkdtemp(prefix="check-", dir=base))
    if args.output is not None:
        output.mkdir(parents=True, exist_ok=False)
    try:
        verify_release(
            repository_root=args.repository_root,
            repository=args.repository or "",
            target_sha=args.target_sha,
            release_tag=args.release_tag,
            output=output,
            reader=GitHubReader(),
        )
    except (
        ReferenceRefusal,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        zipfile.BadZipFile,
    ) as error:
        (output / "refusal.json").write_text(
            json.dumps(
                {"status": "refused", "error": str(error), "published": False}, indent=2
            )
            + "\n"
        )
        print("Release evidence refused: " + str(error))
        return 2
    print("Same-revision actual-R release evidence passed; no publication performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
