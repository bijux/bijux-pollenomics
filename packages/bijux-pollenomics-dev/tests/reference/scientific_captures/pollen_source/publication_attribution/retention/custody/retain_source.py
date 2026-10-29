import hashlib,json,stat
from pathlib import Path
R=Path('/Users/bijan/bijux/bijux-pollenomics')
D=Path(__file__).resolve().parent
P=R/'artifacts/science/current-neotoma-publication-source-replay/plan.json'
payload=P.read_bytes();assert hashlib.sha256(payload).hexdigest()=='ca4003d9c94379843d7803d8cc213c7fe89be4789615dce58fcc4a0c779fb11f'
p=json.loads(payload);assert p['candidate']=='82c8fc4ed3d847909d14162f51b77dc59ccc0a70'
assert len(p['input_pins'])==66723
roots=[R/'packages'/name/'src' for name in ['bijux-pollenomics','bijux-pollenomics-dev','bijux-pollenomics-lra','pollenomics']]
bootstrap=R/'artifacts/science/current-offline-isolated-source-runtime-bootstrap'
rows=[];members={};counts={}
for i,pin in enumerate(p['input_pins']):
 path=Path(pin['path']);member=None
 firstparty=any(path.is_relative_to(root) for root in roots)
 bytecode=firstparty and (path.suffix=='.pyc' or '__pycache__' in path.parts)
 retain=path.is_relative_to(R) and not path.is_relative_to(bootstrap) and not bytecode
 if retain:
  assert path.resolve()==path and stat.S_ISREG(path.lstat().st_mode),path
  data=path.read_bytes();assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],path
  member='source/'+path.relative_to(R).as_posix();target=D/member
  target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
  target.write_bytes(data);members[member]={'sha256':pin['sha256'],'bytes':pin['bytes']}
  role='retained_public_first_party_source_or_resource' if firstparty else 'retained_controller_protocol_or_public_declared_metadata'
 elif bytecode:role='omitted_first_party_bytecode_identity_only'
 elif path.is_relative_to(R.parent/'-bijux-pollenomics-data'):role='omitted_private_capture_payload_identity_only'
 else:role='omitted_runtime_or_dependency_identity_only'
 counts[role]=counts.get(role,0)+1
 rows.append(dict(pin,original_index=i,retention_role=role,retained_member=member))
assert counts['omitted_private_capture_payload_identity_only']==256
(D/'execution-plan.json').write_bytes(payload)
(D/'ordered-original-input-identities.json').write_text(json.dumps(rows,indent=2)+'\n')
for name in ['execution-plan.json','ordered-original-input-identities.json']:
 path=D/name;members[name]={'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
for name,pin in members.items():
 data=(D/name).read_bytes();assert len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256']
result={'schema_version':'neotoma-publication-execution-source-retention.v1','original_execution_candidate':p['candidate'],'original_plan':{'path':str(P),'sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)},'ordered_original_input_identities':66723,'retention_role_counts':counts,'members':members,'member_count':len(members),'logical_retained_bytes':sum(x['bytes'] for x in members.values()),'scope':{'artifact_only_source_retention':True,'all_four_first_party_regular_source_and_resources_from_original_plan_retained':True,'private_capture_runtime_and_bytecode_payloads_omitted':True,'all_original_identities_retained_in_original_order':True,'current_runtime_reauthentication_native_source_export_or_new_consumer_outcome_claimed':False,'original_native_job_terminal_not_yet_collected':True}}
result['members_sha256']=hashlib.sha256(json.dumps(members,sort_keys=True,separators=(',',':')).encode()).hexdigest()
M=D/'source-retention.json';M.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'path':str(M),'sha256':hashlib.sha256(M.read_bytes()).hexdigest(),'bytes':M.stat().st_size,'counts':counts,'members':len(members),'retained_bytes':result['logical_retained_bytes']}))
