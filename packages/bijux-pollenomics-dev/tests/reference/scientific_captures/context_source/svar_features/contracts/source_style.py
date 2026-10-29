from pathlib import Path
import subprocess
A=Path(__file__).resolve().parent.parent;R=A.parents[2]
files=sorted(str(p) for p in A.glob('*.py') if p.name not in {'common_runner.py','first_feature.py'})
for args in (["format"],["check","--fix"],["format"],["check"],["format","--check"]):
 subprocess.run(['/Users/bijan/.cache/uv/archive-v0/2XF0xMG3jR4vPhZZ/ruff-0.15.8.data/scripts/ruff',*args,'--config',str(R/'configs/ruff.toml'),'--cache-dir',str(A/'preflight/ruff-cache'),*files],check=True)
