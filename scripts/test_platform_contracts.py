import copy,importlib.util,json,re
from pathlib import Path
import yaml
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('vc',root/'skills/govstack-platform-practitioner/scripts/validate_contract.py')
assert spec is not None and spec.loader is not None
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
text=(root/'docs/handoff-contracts.md').read_text()
match=re.search(r'```yaml\n(platform_runtime_record:\n.*?\n)```',text,re.S)
assert match,'Missing handoff YAML'
record=yaml.safe_load(match.group(1))
record['platform_runtime_record']['case_id']='offline-contract-fixture'
record['platform_runtime_record']['review']={k:'unverified' for k in ['architecture','content','syntax','evidence']}
record['platform_runtime_record']['operator_execution']['execution_level']='offline-validated'
record['platform_runtime_record']['operator_execution']['status']='passed'
record['platform_runtime_record']['operator_execution']['changed_resource_ids']=[]
record['platform_runtime_record']['live_validation']=[]
errors=m.validate_record(record);assert not errors,errors
checks=['offline-positive']
def reject(name,fn):
 x=copy.deepcopy(record);fn(x['platform_runtime_record']);errors=m.validate_record(x);assert errors,name;checks.append(name)
reject('missing-schema',lambda x:x.pop('schema'))
reject('wrong-schema',lambda x:x.update(schema='invented/v1'))
reject('missing-second-spoke',lambda x:x['clusters'].pop('examples'))
reject('wrong-workload-boundary',lambda x:x.update(workload_installation_boundary='chapter-5'))
reject('premature-live',lambda x:x.update(live_validation=['invented']))
reject('premature-changed-id',lambda x:x['operator_execution'].update(changed_resource_ids=['invented']))
reject('live-without-evidence',lambda x:x['operator_execution'].update(execution_level='live-executed',evidence=[]))
reject('cleanup-with-blockers',lambda x:(x['operator_execution'].update(operation='cleanup',status='passed'),x.update(cleanup_blockers=['retirement blocked'])))
print(json.dumps({'contract_checks':checks,'count':len(checks)},indent=2))
