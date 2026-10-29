"""Run only synthetic source guards, configured source checks and CLI help."""
from pathlib import Path
import ast,hashlib,json,subprocess
A=Path(__file__).resolve().parent.parent;R=A.parents[2];P=R/'artifacts/science/cached-source-validation-custody'
BASE='/opt/homebrew/Cellar/python@3.11/3.11.13/Frameworks/Python.framework/Versions/3.11/bin/python3.11';PREFIX=[BASE,'-I','-S','-B',str(P/'execute.py'),'--profile',str(P/'profile.json'),'--profile-sha256','3331ec5104b2d083c886dcb10ad62551c2f69ff7d00d604aba60b10023e9e08b']
files=sorted(str(p) for p in A.glob('*.py') if p.name not in {'common_runner.py','first_feature.py'})
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
receipts=[]
def call(label,argv):
 label='source-order-prefix-'+label
 out=A/'preflight'/(label+'.stdout');err=A/'preflight'/(label+'.stderr')
 with out.open('xb') as stdout,err.open('xb') as stderr:result=subprocess.run(argv,cwd=R,stdout=stdout,stderr=stderr)
 receipts.append({'id':label,'argv':argv,'actual_exit':result.returncode,'stdout':pin(out),'stderr':pin(err)})
 assert result.returncode==0,(label,result.returncode)
call('source-configured-style',PREFIX+['--mode','python','--',str(A/'preflight/source_style.py')])
call('source-synthetic-guards',PREFIX+['--mode','python','--',str(A/'check_contracts.py')])
call('source-strict',PREFIX+['--mode','mypy','--','--config-file',str(R/'configs/mypy.ini'),'--strict','--follow-imports=silent','--cache-dir',str(A/'preflight/mypy-cache'),*files])
for name in ('prepare.py','run.py','census.py','observe.py'):
 call('source-help-'+name,PREFIX+['--mode','python','--',str(A/name),'--help'])
for p in A.glob('*.py'):ast.parse(p.read_bytes())
(A/'source-command-receipts.json').write_text(json.dumps({'commands':receipts,'source_only':True,'actual_private_parsing_or_preparer_or_native_or_model':False},indent=2)+'\n')
print(json.dumps({'commands':len(receipts),'strict_files':len(files),'all_source_exit_zero':True}))
