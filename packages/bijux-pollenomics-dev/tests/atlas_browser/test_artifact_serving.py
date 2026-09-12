"""Exercise the actual JavaScript verifier against Python-pinned inventories."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from bijux_pollenomics_dev.ci.atlas_browser import artifact_candidate as audit

from .artifact_fixtures import artifact_plan


def test_javascript_audit_parity_and_served_mutation_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = artifact_plan(tmp_path, monkeypatch)
    expected = audit.audit_artifact_candidate(plan)
    source = tmp_path / "artifacts/source"
    listing = []
    for member in sorted(path for path in source.rglob("*") if path.is_file()):
        payload = member.read_bytes()
        digest = hashlib.sha1(
            b"blob " + str(len(payload)).encode() + b"\0" + payload
        ).hexdigest()
        listing.append(
            f"100644 blob {digest}\t{member.relative_to(source).as_posix()}\0"
        )
    # Replace the bounded Git executable with a read-only object-store double.
    # No test initializes, writes, checks out, or mutates a real Git repository.
    binary = tmp_path / "bin"
    binary.mkdir()
    git = binary / "git"
    git.write_text(
        f"#!{sys.executable}\nimport sys\nsys.stdout.write({('b' * 40)!r} if sys.argv[1]=='rev-parse' else {''.join(listing)!r})\n"
    )
    git.chmod(0o755)
    module = Path(audit.__file__).with_name("artifact-candidate.mjs").as_uri()
    script = r"""
import {writeFile,symlink,unlink} from 'node:fs/promises';
import {join} from 'node:path';
const {assertArtifactCandidate,readArtifactMember} = await import(process.argv[1]);
const plan = JSON.parse(process.argv[2]);
const audit = await assertArtifactCandidate(plan);
const target = join(plan.repository_root,plan.scopes[0].document);
const original = await readArtifactMember(plan,audit,target);
if ((await readArtifactMember(plan,audit,join(plan.repository_root,'not-listed'))) !== null) throw new Error('unlisted member served');
await writeFile(target,'mutated while serving');
let rejected = false;
try {await readArtifactMember(plan,audit,target);} catch {rejected = true;}
if (!rejected) throw new Error('altered member served');
await writeFile(target,original.payload);
await unlink(target);
await symlink(join(plan.repository_root,plan.scopes[0].manifest),target);
rejected = false;
try {await readArtifactMember(plan,audit,target);} catch {rejected = true;}
if (!rejected) throw new Error('symbolic member served');
await unlink(target);
await writeFile(target,original.payload);
console.log(JSON.stringify(audit));
"""
    completed = subprocess.run(
        [
            "node",
            "--input-type=module",
            "-e",
            script,
            module,
            json.dumps(plan.as_json()),
        ],
        env={**os.environ, "PATH": str(binary) + os.pathsep + os.environ["PATH"]},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == expected
    assert audit.audit_artifact_candidate(plan) == expected
