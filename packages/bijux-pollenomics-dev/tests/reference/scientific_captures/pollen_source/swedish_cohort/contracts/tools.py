"""Run configured source tools without a source producer or runtime preparation."""
from pathlib import Path
import ast,json,subprocess,sys
P=Path(__file__).resolve().parent.parent
R=P.parents[2]
RUFF='/Users/bijan/.cache/uv/archive-v0/2XF0xMG3jR4vPhZZ/ruff-0.15.8.data/scripts/ruff'
files=sorted(p for p in P.glob('*.py') if p.name!='common_runner.py')
changed=[p for p in files if p.name not in {'runtime.py'}]
cache=P/'preflight/ruff-cache'
commands=[]
if '--format' in sys.argv:
 commands=[[RUFF,'format','--config',str(R/'configs/ruff.toml'),*map(str,changed)],[RUFF,'check','--fix','--config',str(R/'configs/ruff.toml'),'--cache-dir',str(cache),*map(str,changed)]]
else:
 commands=[[RUFF,'check','--config',str(R/'configs/ruff.toml'),'--cache-dir',str(cache),*map(str,files)],[RUFF,'format','--check','--config',str(R/'configs/ruff.toml'),*map(str,files)]]
for argv in commands:subprocess.run(argv,env={'PATH':'/usr/bin:/bin','RUFF_CACHE_DIR':str(cache)},check=True,timeout=90)
for p in P.glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
print(json.dumps({'source_only_actual_exit':0,'configured_source_files':len(files),'AST_files':len(list(P.glob('*.py')))}))
