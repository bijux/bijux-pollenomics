"""Run frozen canonical report consumers and preserve producer/checker distinctions."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time


def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def changes(left,right,path='$'):
    if type(left) is type(right) and left==right:return []
    if isinstance(left,dict) and isinstance(right,dict):
        result=[]
        for key in sorted(left.keys()|right.keys()):
            if key not in left or key not in right:result.append({'path':path+'.'+key,'kind':'membership','old':left.get(key),'current':right.get(key)})
            else:result.extend(changes(left[key],right[key],path+'.'+key))
        return result
    if isinstance(left,list) and isinstance(right,list) and len(left)==len(right):return [item for i,(a,b) in enumerate(zip(left,right,strict=True)) for item in changes(a,b,f'{path}[{i}]')]
    return [{'path':path,'kind':'numeric' if type(left) in (int,float) or type(right) in (int,float) else 'scalar_or_type','old':left,'current':right}]

p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--registered-plan-sha256',required=True);a=p.parse_args()
assert digest(a.plan)==a.registered_plan_sha256
plan=json.loads(a.plan.read_bytes());root=Path(plan['repository']);output=Path(plan['output'])
assert not (output/'terminal.json').exists()
def identity():
    def git(*args):return subprocess.check_output(['git',*args],cwd=root)
    return {'candidate':git('rev-parse','HEAD').decode().strip(),'status':git('status','--porcelain').decode(),'tracked_inventory_sha256':hashlib.sha256(git('ls-files','-s','-z')).hexdigest()}
def mismatches():return [x['path'] for x in plan['input_pins'] if not Path(x['path']).is_file() or digest(Path(x['path']))!=x['sha256']]
before=identity();before_pins=mismatches()
assert before==plan['canonical_identity'] and not before_pins
assert all(not Path(x).exists() for x in plan['absent_input_paths'])
started=time.monotonic();results=[]
for stage in plan['stages']:
    # Do not launch a producer when its complete native timeout plus wrapper buffer
    # cannot fit. Inner maintained producers own independent session timeouts.
    if time.monotonic()-started+stage['timeout_seconds']>plan['resources']['overall_timeout_seconds']:break
    stdout=output/(stage['id']+'.stdout');stderr=output/(stage['id']+'.stderr');timeout=False;start=time.monotonic()
    with stdout.open('xb') as out,stderr.open('xb') as err:
        env=dict(os.environ)
        for key in ['PYTHONHOME','PYTEST_ADDOPTS']:env.pop(key,None)
        env.update(plan['environment'])
        child=subprocess.Popen(stage['argv'],cwd=root,env=env,stdout=out,stderr=err,start_new_session=True)
        try:exit_code=child.wait(timeout=stage['timeout_seconds'])
        except subprocess.TimeoutExpired:
            timeout=True
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait();exit_code=124
    result={**stage,'actual_exit':exit_code,'timed_out':timeout,'elapsed_seconds':time.monotonic()-start,'stdout':str(stdout),'stderr':str(stderr),'stdout_sha256':digest(stdout),'stderr_sha256':digest(stderr),'observed_cumulative_completed_child_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss}
    if stage.get('evidence_root'):
        evidence=Path(stage['evidence_root'])
        for name in ['producer-command.json','producer-execution.json','manifest.json']:
            path=evidence/name
            result[name.removesuffix('.json')]={'path':str(path),'sha256':digest(path),'value':json.loads(path.read_bytes())} if path.is_file() else None
        products=[]
        for relative in stage['tracked_outputs']:
            current=root/relative;generated=evidence/'output'/relative.removeprefix('docs/report/')
            item={'tracked_path':relative,'generated_path':str(generated),'generated_exists':generated.is_file()}
            if generated.is_file():
                item.update(tracked_sha256=digest(current),generated_sha256=digest(generated),byte_identical=current.read_bytes()==generated.read_bytes())
                if relative.endswith('.json'):
                    differences=changes(json.loads(current.read_bytes()),json.loads(generated.read_bytes()))
                    item.update(value_differences=differences,numeric_value_differences=sum(x['kind']=='numeric' for x in differences))
            products.append(item)
        result['products']=products
    results.append(result)
    (output/'stage-progress.json').write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps({'stage':stage['id'],'actual_exit':exit_code,'producer_native_exit':(result.get('producer-execution') or {}).get('value',{}).get('exit_code'),'manifest_exists':bool(result.get('manifest')),'elapsed_seconds':result['elapsed_seconds']}),flush=True)
    if stage.get('must_succeed') and exit_code:break
after=identity();after_pins=mismatches();absent_stable=all(not Path(x).exists() for x in plan['absent_input_paths'])
passed=before==after and not after_pins and absent_stable and len(results)==len(plan['stages']) and all(x['actual_exit']==0 for x in results)
products=[{'path':str(path),'sha256':digest(path),'bytes':path.stat().st_size} for path in sorted(output.rglob('*')) if path.is_file() and not path.is_symlink()]
terminal={'schema_version':'frozen-configured-report-account-qualification-terminal.v1','candidate':plan['candidate'],'plan_sha256':a.registered_plan_sha256,'actual_exit':0 if passed else 1,'status':'passed' if passed else 'failed','elapsed_seconds':time.monotonic()-started,'actual_launch_argv':[os.sys.executable,*os.sys.argv],'canonical_before':before,'canonical_after':after,'before_pin_mismatches':before_pins,'after_pin_mismatches':after_pins,'absent_input_paths_unchanged':absent_stable,'stages':results,'products':products,'output_bytes':sum(x['bytes'] for x in products),'resources':plan['resources'],'scope':plan['scope'],'limits':['Actual producer execution status, successful output manifest and configured tracked-byte checker status remain separate. No producer success is inferred from checker failure.','JSON numeric differences are exact leaf differences, not a tolerance or scientific equivalence claim. Immutable old numerical/R/source captures retain original scope.','Outer wrappers and native inner producers own separate process-group timeouts; complete descendant process census and enforced memory/storage quotas are not claimed.']}
(output/'terminal.json').write_text(json.dumps(terminal,indent=2)+'\n');print(json.dumps({'terminal':str(output/'terminal.json'),'sha256':digest(output/'terminal.json'),'status':terminal['status']}),flush=True);raise SystemExit(terminal['actual_exit'])
