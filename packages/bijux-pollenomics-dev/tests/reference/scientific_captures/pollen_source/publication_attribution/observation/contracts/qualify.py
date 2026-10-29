from pathlib import Path
import subprocess,json,ast
B=Path(__file__).resolve().parent.parent
R=B.parents[2]
ruff='/Users/bijan/.cache/uv/archive-v0/2XF0xMG3jR4vPhZZ/ruff-0.15.8.data/scripts/ruff'
files=[str(p) for p in sorted(B.glob('*.py')) if p.name != 'common_runner.py']
changed=[p for p in files if Path(p).name not in ['source_runtime.py','runtime_contracts.py']]
for name,argv in [('format',[ruff,'format','--config',str(R/'configs/ruff.toml'),'--cache-dir',str(B/'preflight/ruff-cache'),*changed]),('ruff',[ruff,'check','--fix','--config',str(R/'configs/ruff.toml'),'--cache-dir',str(B/'preflight/ruff-cache'),*changed])]:
 x=subprocess.run(argv,text=True,capture_output=True);(B/'preflight'/f'{name}.stdout').write_text(x.stdout);(B/'preflight'/f'{name}.stderr').write_text(x.stderr);assert x.returncode==0,(name,x.stdout,x.stderr)
for f in files:ast.parse(Path(f).read_bytes())
print(json.dumps({'actual_exit':0,'AST_files':len(files),'configured_mutating_style_only_unheld_successor_files':len(changed)}))
