"""Exercise the independent JavaScript generated-report byte closure."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from bijux_pollenomics_dev.ci.atlas_browser import generated_report_candidate as audit

from .generated_report_fixtures import generated_report_plan


def test_javascript_audit_parity_and_served_mutation_refusal(tmp_path: Path) -> None:
    plan = generated_report_plan(tmp_path)
    expected = audit.audit_generated_report_candidate(plan)
    module = Path(audit.__file__).with_name("generated-report-candidate.mjs").as_uri()
    script = r"""
import {writeFile} from 'node:fs/promises';
import {join} from 'node:path';
const {
  assertGeneratedReportCandidate,
  readGeneratedReportMember,
} = await import(process.argv[1]);
const plan = JSON.parse(process.argv[2]);
const audit = await assertGeneratedReportCandidate(plan);
const target = join(plan.repository_root,plan.scopes[0].document);
const original = await readGeneratedReportMember(plan,audit,target);
const missing = join(plan.repository_root,'not-listed');
if ((await readGeneratedReportMember(plan,audit,missing)) !== null) {
  throw new Error('unlisted member served');
}
await writeFile(target,'mutated while serving');
let rejected = false;
try {await readGeneratedReportMember(plan,audit,target);} catch {rejected = true;}
if (!rejected) throw new Error('altered member served');
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
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == expected
