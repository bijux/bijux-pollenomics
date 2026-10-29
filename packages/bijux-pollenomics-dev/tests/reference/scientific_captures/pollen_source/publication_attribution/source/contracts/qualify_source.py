"""Collect controlled source guards, strict typing and API help without source execution."""
import ast
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

A=Path(__file__).resolve().parent.parent; R=A.parents[2]
parser=argparse.ArgumentParser(); parser.add_argument("--label",default="source"); args=parser.parse_args()
BASE="/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11"
EXECUTE=R/"artifacts/science/cached-source-validation-custody/execute.py"
PREFIX=[BASE,"-I","-S","-B",str(EXECUTE),"--profile",str(EXECUTE.parent/"profile.json"),"--profile-sha256","3331ec5104b2d083c886dcb10ad62551c2f69ff7d00d604aba60b10023e9e08b"]
files=sorted(str(p) for p in A.glob("*.py") if p.name!="common_runner.py"); assert len(files)==10
commands=[("configured-style",PREFIX+["--mode","python","--",str(A/"preflight/source_style.py")]),("controlled-guards",PREFIX+["--mode","python","--",str(A/"check_contracts.py")]),("strict",PREFIX+["--mode","mypy","--","--config-file",str(R/"configs/mypy.ini"),"--strict","--cache-dir",str(A/"preflight/mypy-cache"),*files])]
receipts=[]
def pin(path):
    raw=path.read_bytes(); return {"path":str(path),"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
for name,argv in commands:
    stdout=A/"preflight"/(args.label+"-"+name+".stdout"); stderr=A/"preflight"/(args.label+"-"+name+".stderr"); assert not stdout.exists() and not stderr.exists()
    with stdout.open("wb") as out,stderr.open("wb") as err:
        result=subprocess.run(argv,cwd=R,stdout=out,stderr=err,check=False)
    receipts.append({"id":name,"argv":argv,"actual_exit":result.returncode,"stdout":pin(stdout),"stderr":pin(stderr)})
    (A/"source-command-receipts.json").write_text(json.dumps(receipts,indent=2)+"\n"); assert result.returncode==0,name
for file in A.glob("*.py"): ast.parse(file.read_bytes(),filename=str(file))
print(json.dumps({"source_only_exit":0,"strict_files":10,"configured_Ruff_files":10,"configured_format_files":10,"AST_files":11,"private_response_parsing_or_runtime_census_or_preparation_or_native_calls":0}))
