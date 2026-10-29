"""Read only tracked source and root-authenticated input identities; do not open responses."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

A=Path(__file__).resolve().parent.parent; R=A.parents[2]
BASE="/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
EXECUTE=R/"artifacts/science/cached-source-validation-custody/execute.py"
PREFIX=[BASE,"-I","-S","-B",str(EXECUTE),"--profile",str(EXECUTE.parent/"profile.json"),"--profile-sha256","3331ec5104b2d083c886dcb10ad62551c2f69ff7d00d604aba60b10023e9e08b","--mode","python","--"]
def pin(path):
    raw=path.read_bytes(); return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
authority_path=R/"artifacts/science/neotoma-publication-capture-input-custody/physical-capture-custody.json"
authority_pin=pin(authority_path); assert authority_pin["sha256"]=="bf1ff4e05cb656f96bf3f06d7f3c0dcc40f3b8d910a3c9829705eaa4ec2d7e92"
authority=json.loads(authority_path.read_bytes())
rows=[row for capture in authority["capture_sets"] for row in capture["members"]]
assert len(rows)==len({row["path"] for row in rows})==256 and sum(row["bytes"] for row in rows)==640035
owner_id="regions/nordic/source-capability/neotoma-attribution/report-products"
policy=json.loads((R/"configs/ci/report-ownership.json").read_bytes()); owner=next(row for row in policy["owners"] if row["owner_id"]==owner_id)
expected={"packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma_publication_readiness.py","packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma_doi_review.py","packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra/materialization/neotoma/publication_intake.py"}
assert set(owner["producer_paths"])==expected and all((R/name).is_file() for name in expected)
sources=[]
for name in sorted(expected):
    path=R/name; tree=ast.parse(path.read_bytes()); functions={node.name:ast.unparse(node.args) for node in tree.body if isinstance(node,ast.FunctionDef)}
    flags=[node.args[0].value for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=="add_argument" and node.args and isinstance(node.args[0],ast.Constant)]
    if name.endswith(("neotoma_publication_readiness.py","neotoma_doi_review.py")):
        assert functions["build"]=="repository: Path, capture_root: Path" and flags==["--repository","--capture-root","--output"]
    else: assert functions["parse_dataset_publications"]=="dataset_id: int, content: bytes"
    sources.append({**pin(path),"functions":functions,"CLI_flags":flags})
reports={name:pin(R/name) for name in owner["paths"]}; raw_report=json.loads((R/"docs/report/regions/nordic/source-capability/neotoma-attribution/report.json").read_bytes()); raw_doi=json.loads((R/"docs/report/regions/nordic/source-capability/neotoma-attribution/doi-review.json").read_bytes())
assert raw_report["provider_capture_manifest_sha256"]=="d6dee3065e6fcfae8a7e484406cf37e2b5aa0424bee66d3a6922bbbdc1e867da" and raw_doi["registry_capture_manifest_sha256"]=="207b791bed9d3d004fc55f407fb7a840efd81bd9180fed17f24b187ac0e69edb"
assert raw_doi["attribution_ledger_sha256"]==reports["docs/report/regions/nordic/source-capability/neotoma-attribution/report.json"]["sha256"]
assert raw_report["publication_ready"] is False and type(raw_report["lra_accepted_samples"]) is int and raw_report["lra_accepted_samples"]==raw_doi["lra_accepted_samples"]==0
help_receipts=[]
for name in ("prepare.py","execute_source.py","observe.py","run.py","runtime_guarded_runner.py","common_runner.py"):
    stdout=A/"preflight"/(name.removesuffix(".py")+"-help.stdout"); stderr=A/"preflight"/(name.removesuffix(".py")+"-help.stderr"); assert not stdout.exists() and not stderr.exists()
    argv=[*PREFIX,str(A/name),"--help"]
    with stdout.open("wb") as out,stderr.open("wb") as err: result=subprocess.run(argv,cwd=R,stdout=out,stderr=err,check=False)
    help_receipts.append({"argv":argv,"actual_exit":result.returncode,"stdout":pin(stdout),"stderr":pin(stderr)})
    (A/"preflight/help-command-receipts.json").write_text(json.dumps(help_receipts,indent=2)+"\n"); assert result.returncode==0,name
record={"schema_version":"neotoma-publication-source-forensics.v1","source_only_native_exit":0,"capture_authority":authority_pin,"original_private_files_declared":256,"declared_original_bytes":640035,"capture_sets":[{"root":row["root"],"manifest_sha256":row["manifest_sha256"],"member_count":row["member_count"],"response_count_claimed":row["response_count_claimed"]} for row in authority["capture_sets"]],"actual_owner":owner,"declared_owner_producer_path_correction_needed":False,"tracked_maintained_sources":sources,"tracked_comparison_products":reports,"selected_public_source_inputs":[pin(R/name) for name in owner["producer_inputs"]],"staged_attribution_generated_by_actual_first_producer_not_copied":True,"first_party_source_resource_closure":"All regular members and complete namespace/alias checks for all four source trees are dynamically pinned by the future root preparer; no runtime import or numerical-execution equivalence is claimed.","help_receipts":help_receipts,"raw_private_responses_or_private_manifests_opened_by_author":False,"runtime_native_census_or_preparer_producer_or_HTTP_executed_by_author":False,"original06f08e_acquisition_authenticated":False}
(A/"source-forensics.json").write_text(json.dumps(record,indent=2)+"\n"); print(json.dumps(pin(A/"source-forensics.json")))
