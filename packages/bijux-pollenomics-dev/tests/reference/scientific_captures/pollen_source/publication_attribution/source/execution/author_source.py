"""Author a source-only bounded Neotoma publication replay from reviewed mechanics."""
import ast
import hashlib
import json
from pathlib import Path
import shutil

A=Path(__file__).resolve().parent.parent; R=A.parents[2]
OLD=R/"artifacts/science/empd2-nfi-source-telemetry-custody"
MODULES={"contracts.py","metadata.py","execute_source.py","observe.py","prepare.py","run.py","check_contracts.py","source_runtime.py","runtime_contracts.py","runtime_guarded_runner.py","common_runner.py"}
prefix='''_entry_path = Path(__file__).absolute()
if _entry_path != _entry_path.resolve(strict=True) or any(p.is_symlink() for p in (_entry_path, *_entry_path.parents)):
    raise ValueError("Physical absolute controller entry and ancestors required")
_entry_directory = _entry_path.parent
_expected_python = '''+repr(MODULES)+'''
_present_python = set()
for _entry in _entry_directory.iterdir():
    if _entry.is_symlink() or not (_entry.is_dir() or _entry.is_file()):
        raise ValueError("Controller alias/special entry before helper import")
    if _entry.is_dir() and _entry.name != "preflight":
        raise ValueError("Unexpected controller directory before helper import")
    if _entry.suffix in {".py", ".pyc", ".so", ".dylib", ".pyd"}:
        if _entry.name not in _expected_python:
            raise ValueError("Unexpected controller import before helper import")
        _present_python.add(_entry.name)
if _present_python != _expected_python:
    raise ValueError("Incomplete exact controller import namespace")
sys.path.insert(0, str(_entry_directory))
'''
(A/"preflight/entry-prefix.txt").write_text(prefix)
original=(OLD/"contracts.py").read_text(); tree=ast.parse(original)
names={"require","sha","pin","exact","load","dump","output_root","identity","union","first_party_snapshot","verify_inputs"}
functions="\n\n".join(ast.get_source_segment(original,node) for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names)
functions=functions.replace('    namespace()\n','    namespace()\n').replace('verify_base_namespaces(plan["first_party_namespaces"])','verify_base_namespaces(plan["first_party_namespaces"])\n    verify_base_namespaces(plan["capture_namespaces"])')
constants='''ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
PRIVATE = Path("/Users/bijan/bijux/-bijux-pollenomics-data")
POLICY = "configs/ci/report-ownership.json"
OWNER = "regions/nordic/source-capability/neotoma-attribution/report-products"
REPORT = "docs/report/regions/nordic/source-capability/neotoma-attribution"
ENTITY = "docs/report/regions/nordic/source-capability/neotoma-entities/report.json"
DATASETS = "data/neotoma/relational/surfaces/datasets/part-00001.json"
POLICY_REVIEW = "docs/public/pollenomics-data/sources/neotoma.md"
PRODUCERS = {
    "publication": "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma_publication_readiness.py",
    "doi": "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/neotoma_doi_review.py",
}
CAPTURE_AUTHORITY = ROOT / "artifacts/science/neotoma-publication-capture-input-custody/physical-capture-custody.json"
CAPTURE_AUTHORITY_SHA = "bf1ff4e05cb656f96bf3f06d7f3c0dcc40f3b8d910a3c9829705eaa4ec2d7e92"
CAPTURES = {
    "doi": (PRIVATE / "neotoma/doi-metadata/used-nordic", "207b791bed9d3d004fc55f407fb7a840efd81bd9180fed17f24b187ac0e69edb", 27),
    "publication": (PRIVATE / "neotoma/publication-links/2026-09-29", "d6dee3065e6fcfae8a7e484406cf37e2b5aa0424bee66d3a6922bbbdc1e867da", 170),
    "older_publication": (PRIVATE / "neotoma/publication-links/2026-09-21", "8b187c88213415f17e866abc172b972a65db5a1e01513a0e917b0faec625f294", 59),
}
PACKAGE_ROOTS = [ROOT / "packages" / name / "src" for name in ("bijux-pollenomics", "bijux-pollenomics-dev", "bijux-pollenomics-lra", "pollenomics")]
MODULES = '''+repr(MODULES)+'''\n
'''
namespace='''def namespace() -> None:
    require(SOURCE == SOURCE.resolve() and not any(p.is_symlink() for p in (SOURCE,*SOURCE.parents)), "Controller source alias ancestor")
    actual = set()
    for path in SOURCE.iterdir():
        require(not path.is_symlink() and (path.is_file() or path.is_dir()), "Controller alias/special entry")
        require(not path.is_dir() or path.name == "preflight", "Unknown controller directory")
        if path.suffix in {".py", ".pyc", ".so", ".dylib", ".pyd"}:
            require(path.name in MODULES, "Unknown controller import")
            actual.add(path.name)
    require(actual == MODULES, "Incomplete controller imports")
'''
(A/"contracts.py").write_text('"""Authenticate exact source, retained response and current clean-candidate custody."""\nfrom __future__ import annotations\nimport hashlib\nimport json\nfrom pathlib import Path\nimport subprocess\nfrom typing import Any\n\n'+constants+namespace+'\n\n'+functions+'\n')
for name in ("source_runtime.py","runtime_contracts.py","common_runner.py"):
    assert not (A/name).exists(); shutil.copyfile(OLD/name,A/name)
runner=(OLD/"runtime_guarded_runner.py").read_text()
start=runner.index('_source_directory = '); end=runner.index('from source_runtime import',start)
runner=runner[:start]+prefix+runner[end:]
runner=runner.replace('around outcome-blind source metadata stages','around current publication source stages').replace('actual current EMPD2 metadata source epoch','actual current Neotoma publication source epoch')
(A/"runtime_guarded_runner.py").write_text(runner)
run=(OLD/"run.py").read_text(); start=run.index('_entry_directory = '); end=run.index('from contracts import',start)
run=run[:start]+prefix+run[end:]
run=run.replace('pairing-terminal.json','neotoma-publication-terminal.json').replace('len(actual) == len(expected) == 2','len(actual) == len(expected) == 3').replace('("pairs.csv", "report.json")','("doi-review.json", "report.json")').replace('produced = output / "producer" / name','produced = output / "producer" / REPORT / name').replace('outcome-blind-empd2-nfi-source-replay-terminal.v1','neotoma-publication-source-replay-terminal.v1')
(A/"run.py").write_text(run)
source_refs={name:{"path":str(OLD/name),"sha256":hashlib.sha256((OLD/name).read_bytes()).hexdigest(),"bytes":(OLD/name).stat().st_size} for name in ("contracts.py","source_runtime.py","runtime_contracts.py","common_runner.py","runtime_guarded_runner.py","run.py")}
(A/"preflight/predecessor-source-records.json").write_text(json.dumps(source_refs,indent=2)+"\n")
print(json.dumps({"source_only":True,"reused_runtime_common_helpers":3,"entry_module_count":len(MODULES),"private_response_or_runtime_census_performed":False}))
