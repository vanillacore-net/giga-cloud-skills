"""Offline behavioral fixtures: no OpenStack API is contacted by this suite.
The optional installed-client tests invoke --help only.
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'runtime/openstack_ops.py'
PROJECT = '11111111-1111-4111-8111-111111111111'
OTHER = '22222222-2222-4222-8222-222222222222'
RESOURCE = '33333333-3333-4333-8333-333333333333'
CREATED = '44444444-4444-4444-8444-444444444444'
FIXTURE = '''#!/usr/bin/env python3
# Explicitly offline fixture, NOT a cloud emulator or production CLI.
import json, os, sys
from pathlib import Path
args=sys.argv[1:]
p=Path(os.environ['FIXTURE_ROOT'])
with (p/'calls.jsonl').open('a') as f: f.write(json.dumps({'argv':args,'os_env':{k:v for k,v in os.environ.items() if k.startswith('OS_')}})+'\\n')
cfg=json.loads((p/'fixture.json').read_text())
cmd=args[6:]
if cmd[:2]==['token','issue']: print(json.dumps({'project_id': cfg.get('project','11111111-1111-4111-8111-111111111111')})); sys.exit()
key=' '.join(cmd[:2])
if key in cfg.get('fail',{}):
 print(cfg['fail'][key],file=sys.stderr); sys.exit(1)
if cmd[:2]==['quota','show']: print(json.dumps(cfg.get('quota',{}))); sys.exit()
if 'show' in cmd:
 i=cmd.index('show'); kind=' '.join(cmd[:i])
 data={'id':cmd[i+1], 'project_id':cfg.get('owner','11111111-1111-4111-8111-111111111111'), 'status':cfg.get('status','ACTIVE' if kind=='server' else 'available'), 'size':2, 'attachments':[], 'volume_id':'33333333-3333-4333-8333-333333333333','security_group_id':'33333333-3333-4333-8333-333333333333','router:external':True}
 if cmd[i+1]=='44444444-4444-4444-8444-444444444444': data['status']=cfg.get('created_status',data['status'])
 data.update(cfg.get('records',{}).get(kind,{}))
 print(json.dumps(data)); sys.exit()
if 'create' in cmd:
 print(json.dumps({'id':'44444444-4444-4444-8444-444444444444','project_id':'11111111-1111-4111-8111-111111111111','status':'BUILD'})); sys.exit()
if 'list' in cmd: print(json.dumps(cfg.get('lists',{}).get(key,[]))); sys.exit()
print('{}')
'''

class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.client = self.root/'fake-openstack'
        self.client.write_text(FIXTURE)
        self.client.chmod(0o700)
        self.cfg = {}
        self.write('fixture.json', self.cfg)
        self.context = dict(schema='openstack-context/v1', case_id='offline-case', cloud='local', project_id=PROJECT, region='RegionOne', ownership='direct', timeout_seconds=1)
        self.write('context.json', self.context)
        self.env = dict(os.environ, OPENSTACK_OPS_CLIENT=str(self.client), FIXTURE_ROOT=str(self.root), OS_PROJECT_ID=OTHER, OS_REGION_NAME='wrong', OS_TOKEN='TOP_SECRET')
    def write(self, name, value):
        (self.root/name).write_text(json.dumps(value))
    def run_cli(self, *args):
        return subprocess.run([sys.executable,str(SCRIPT),*args], cwd=self.root, env=self.env, capture_output=True,text=True,timeout=8)
    def calls(self):
        p=self.root/'calls.jsonl'
        return [json.loads(x) for x in p.read_text().splitlines()] if p.exists() else []
    def prepare(self, action='server-stop', **parameters):
        self.write('request.json',dict(action=action,parameters=parameters or {'server_id':RESOURCE}))
        return self.run_cli('prepare','--context','context.json','--request','request.json','--plan','plan.json')
    def execute(self, digest=None):
        if digest is None: digest=json.loads((self.root/'plan.json').read_text())['sha256']
        return self.run_cli('execute','--plan','plan.json','--approve',digest,'--evidence','evidence.json')
    def test_inventory_is_readonly_project_region_scoped_and_secret_safe(self):
        result=self.run_cli('inspect','--context','context.json','--domain','environment','--evidence','evidence.json')
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        record=json.loads((self.root/'evidence.json').read_text())
        self.assertEqual(record['schema'],'openstack-operation-record/v1')
        self.assertEqual(record['execution_level'],'read-only')
        self.assertTrue(self.calls())
        for call in self.calls():
            self.assertEqual(call['argv'][:6],['--os-cloud','local','--os-project-id',PROJECT,'--os-region-name','RegionOne'])
            self.assertNotIn('OS_TOKEN',call['os_env'])
            self.assertFalse(any(x in call['argv'][6:] for x in ['create','delete','set']))
        self.assertNotIn('TOP_SECRET',result.stdout+result.stderr)
        self.assertEqual((self.root/'evidence.json').stat().st_mode & 0o777,0o600)

    def test_prepare_reads_scope_and_never_mutates(self):
        result=self.prepare()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        plan=json.loads((self.root/'plan.json').read_text())
        self.assertEqual(len(plan['sha256']),64)
        self.assertEqual(plan['request']['action'],'server-stop')
        self.assertEqual(plan['context']['region'],'RegionOne')
        self.assertFalse(any('stop' in x['argv'] for x in self.calls()))
        self.assertEqual((self.root/'plan.json').stat().st_mode & 0o777,0o600)
    def test_wrong_identity_blocks_prepare(self):
        self.write('fixture.json',{'project':OTHER})
        result=self.prepare()
        self.assertEqual(result.returncode,2)
        self.assertIn('wrong-project',result.stdout)
        self.assertFalse((self.root/'plan.json').exists())
    def test_foreign_resource_and_external_owner_block_prepare(self):
        for owner in ['opentofu','capi','gitops','unknown']:
            self.context['ownership']=owner
            self.write('context.json',self.context)
            result=self.prepare()
            self.assertEqual(result.returncode,2,result.stdout)
        self.context['ownership']='direct'
        self.write('context.json',self.context)
        self.write('fixture.json',{'owner':OTHER})
        result=self.prepare()
        self.assertEqual(result.returncode,2)
        self.assertIn('resource-wrong-project',result.stdout)
    def test_ambiguous_target_and_unknown_parameters_block(self):
        for params in [{'server_id':'name-not-uuid'},{'server_id':RESOURCE,'argv':['server','delete',RESOURCE]}]:
            result=self.prepare(**params)
            self.assertEqual(result.returncode,2,result.stdout)
    def test_network_validation_and_delete_retention_decision(self):
        for action,params in [('subnet-create',{'name':'test','network_id':RESOURCE,'cidr':'invalid'}),('security-rule-create',{'security_group_id':RESOURCE,'protocol':'tcp','port_min':22,'port_max':22,'remote_cidr':'0.0.0.0/0'}),('volume-delete',{'volume_id':RESOURCE,'data_policy':'retain','confirm_delete':True})]:
            result=self.prepare(action,**params)
            self.assertEqual(result.returncode,2,result.stdout)
    def test_actions_list_exposes_real_supported_inventory(self):
        result=self.run_cli('actions')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        actions=json.loads(result.stdout)['actions']
        self.assertIn('volume-from-snapshot',actions)
        self.assertIn('router-add-subnet',actions)
        self.assertIn('server-resize-confirm',actions)

    def test_execute_approved_plan_mutates_once_and_validates_state(self):
        self.assertEqual(self.prepare('server-start',server_id=RESOURCE).returncode,0)
        result=self.execute()
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        record=json.loads((self.root/'evidence.json').read_text())
        self.assertEqual(record['status'],'complete')
        self.assertIn(RESOURCE,record['resource_ids'])
        self.assertEqual(len([c for c in self.calls() if 'start' in c['argv']]),1)
        (self.root/'evidence.json').unlink()
        repeat=self.execute()
        self.assertEqual(repeat.returncode,2)
        self.assertIn('replay-refused',repeat.stdout)
        self.assertEqual(len([c for c in self.calls() if 'start' in c['argv']]),1)
    def test_wrong_approval_and_tampered_plan_never_mutate(self):
        self.assertEqual(self.prepare().returncode,0)
        result=self.execute('0'*64)
        self.assertEqual(result.returncode,2)
        self.assertIn('approval-mismatch',result.stdout)
        plan=json.loads((self.root/'plan.json').read_text())
        plan['request']['parameters']['server_id']=OTHER
        self.write('plan.json',plan)
        result=self.execute()
        self.assertEqual(result.returncode,2)
        self.assertIn('plan-digest-mismatch',result.stdout)
        self.assertFalse(any('stop' in c['argv'] for c in self.calls()))
    def test_even_rehashed_injected_argv_is_rejected(self):
        self.assertEqual(self.prepare().returncode,0)
        plan=json.loads((self.root/'plan.json').read_text())
        plan['argv']=['server','delete',RESOURCE]
        import hashlib
        del plan['sha256']
        plan['sha256']=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
        self.write('plan.json',plan)
        result=self.execute()
        self.assertEqual(result.returncode,2)
        self.assertIn('invalid-plan',result.stdout)
    def test_created_id_survives_terminal_wait_failure(self):
        self.assertEqual(self.prepare('server-create',name='offline',image_id=RESOURCE,flavor_id=RESOURCE,network_id=RESOURCE,security_group_id=RESOURCE).returncode,0)
        self.write('fixture.json',{'created_status':'ERROR'})
        result=self.execute()
        self.assertEqual(result.returncode,2,result.stdout+result.stderr)
        record=json.loads((self.root/'evidence.json').read_text())
        self.assertIn(CREATED,record['resource_ids'])
        self.assertEqual(record['status'],'partial')
        self.assertIn('terminal-resource-error',result.stdout)
        self.assertFalse(any('delete' in c['argv'] for c in self.calls()))
    def test_evidence_existing_file_blocks_before_mutation(self):
        self.assertEqual(self.prepare().returncode,0)
        self.write('evidence.json',{'keep':True})
        result=self.execute()
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads((self.root/'evidence.json').read_text()),{'keep':True})
        self.assertFalse(any('stop' in c['argv'] for c in self.calls()))
    def test_symlink_and_escape_are_refused(self):
        (self.root/'alias.json').symlink_to(self.root/'context.json')
        result=self.run_cli('inspect','--context','alias.json','--domain','compute','--evidence','x.json')
        self.assertIn('symlink-refused',result.stdout)
        result=self.run_cli('inspect','--context','context.json','--domain','compute','--evidence','../escape.json')
        self.assertIn('path-outside-work-root',result.stdout)
    def test_execute_rechecks_identity_before_mutating(self):
        self.assertEqual(self.prepare().returncode,0)
        self.write('fixture.json',{'project':OTHER})
        result=self.execute()
        self.assertEqual(result.returncode,2)
        self.assertIn('wrong-project',result.stdout)
        self.assertFalse(any('stop' in c['argv'] for c in self.calls()))
    def test_wait_timeout_retains_created_id(self):
        self.assertEqual(self.prepare('server-create',name='offline',image_id=RESOURCE,flavor_id=RESOURCE,network_id=RESOURCE,security_group_id=RESOURCE).returncode,0)
        self.write('fixture.json',{'created_status':'BUILD'})
        result=self.execute()
        self.assertEqual(result.returncode,2)
        self.assertIn('timeout',result.stdout)
        self.assertIn(CREATED,json.loads((self.root/'evidence.json').read_text())['resource_ids'])

    def test_inspect_partial_permissions_never_leaks_client_stderr(self):
        self.write('fixture.json',{'fail':{'catalog list':'403 Forbidden password=TOP_SECRET','volume list':'Endpoint not found TOP_SECRET'}})
        result=self.run_cli('inspect','--context','context.json','--domain','environment','--evidence','evidence.json')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertNotIn('TOP_SECRET',result.stdout+result.stderr)
        record=json.loads((self.root/'evidence.json').read_text())
        self.assertEqual(record['status'],'partial')
        self.assertIn('permission-denied',result.stdout)
        self.assertIn('api-unavailable',result.stdout)
        self.assertTrue(any('server' in x['argv'] for x in self.calls()))
    def test_server_diagnostics_correlate_private_vm_without_fip_or_volume_requirement(self):
        self.write('fixture.json',{'records':{'server':{'volumes_attached':[]}}, 'lists':{'port list':[{'ID':RESOURCE,'device_id':RESOURCE,'network_id':RESOURCE,'security_group_ids':[RESOURCE],'fixed_ips':[{'subnet_id':RESOURCE,'ip_address':'10.0.0.2'}]}]}})
        result=self.run_cli('inspect','--context','context.json','--domain','troubleshooting','--resource-id',RESOURCE,'--evidence','evidence.json')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue(any('server' in c['argv'] and 'show' in c['argv'] for c in self.calls()))
        self.assertTrue(any('security' in c['argv'] and 'show' in c['argv'] for c in self.calls()))
        record=json.loads((self.root/'evidence.json').read_text())
        self.assertIn(RESOURCE,record['resource_ids'])
        self.assertEqual(record['status'],'complete')
        self.assertTrue(any(f.get('check')=='server-port-chain' for f in record['findings']))
    def test_userdata_content_digest_is_approval_bound(self):
        (self.root/'user-data.txt').write_text('#cloud-config\n{}')
        result=self.prepare('server-create',name='offline',image_id=RESOURCE,flavor_id=RESOURCE,network_id=RESOURCE,security_group_id=RESOURCE,user_data_file='user-data.txt')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        (self.root/'user-data.txt').write_text('changed')
        result=self.execute()
        self.assertEqual(result.returncode,2)
        self.assertIn('user-data-digest-mismatch',result.stdout)
        self.assertFalse(any('create' in c['argv'] for c in self.calls()))
    def test_previous_evidence_preserves_ids_in_new_generation(self):
        previous=dict(schema='openstack-operation-record/v1',case_id='offline-case',project_id=PROJECT,region='RegionOne',resource_ids=[CREATED],findings=[])
        self.write('old.json',previous)
        result=self.run_cli('inspect','--context','context.json','--domain','compute','--evidence','new.json','--previous-evidence','old.json')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn(CREATED,json.loads((self.root/'new.json').read_text())['resource_ids'])
        self.assertEqual(json.loads((self.root/'old.json').read_text()),previous)

    def test_quota_actual_values_are_safe(self):
        self.write('fixture.json',{'quota':{'cores':32,'ram':65536,'instances':10,'metadata':{'token':'TOP_SECRET'},'endpoint':'TOP_SECRET'}})
        r=self.run_cli('inspect','--context','context.json','--domain','environment','--evidence','q.json')
        self.assertIn('65536',r.stdout)
        self.assertNotIn('TOP_SECRET',r.stdout)
    def test_controller_parent_and_snapshot_source_block(self):
        for action,params,kind,marker in [('security-rule-delete',{'rule_id':RESOURCE,'confirm_delete':True},'security group',{'tags':['argocd:managed']}),('volume-from-snapshot',{'snapshot_id':RESOURCE,'name':'copy','size_gib':2},'volume',{'metadata':{'terraform':'managed'}})]:
            self.write('fixture.json',{'records':{kind:marker}})
            r=self.prepare(action,**params)
            self.assertEqual(r.returncode,2,r.stdout+r.stderr)
            self.assertIn('externally-owned',r.stdout)
    def test_plan_expiry_root_binding_and_stable_timestamps(self):
        self.assertEqual(self.prepare('server-start',server_id=RESOURCE).returncode,0)
        plan=json.loads((self.root/'plan.json').read_text())
        self.assertEqual(plan.get('work_root'),str(self.root))
        self.assertLessEqual(plan.get('expires_at',0)-plan.get('created_at',0),1800)
        self.assertGreater(plan.get('expires_at',0),0)
        self.write('fixture.json',{'records':{'server':{'updated':'changed'}}})
        self.assertEqual(self.execute().returncode,0)
    def test_expired_plan_blocks_before_api(self):
        self.assertEqual(self.prepare().returncode,0)
        plan=json.loads((self.root/'plan.json').read_text())
        plan['created_at']=1; plan['expires_at']=2
        import hashlib
        plan['sha256']=hashlib.sha256(json.dumps({k:v for k,v in plan.items() if k!='sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()
        self.write('plan.json',plan)
        n=len(self.calls())
        r=self.execute()
        self.assertIn('plan-expired',r.stdout)
        self.assertEqual(n,len(self.calls()))
    def test_repository_root_refused_but_actions_offline_anywhere(self):
        r=self.run_cli('--work-root',str(SCRIPT.parent.parent),'inspect','--context','missing.json','--domain','compute','--evidence','x.json')
        self.assertIn('protected-work-root',r.stdout)
        r=self.run_cli('--work-root',str(self.root/'missing'),'actions')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
    def test_target_diagnostics_denial_is_per_check(self):
        self.write('fixture.json',{'records':{'server':{'volumes_attached':[{'id':RESOURCE}]}},'fail':{'volume show':'403 Forbidden TOP_SECRET'}})
        r=self.run_cli('inspect','--context','context.json','--domain','troubleshooting','--resource-id',RESOURCE,'--evidence','d.json')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertIn('permission-denied',r.stdout)
        self.assertNotIn('TOP_SECRET',r.stdout+r.stderr)

    def test_all_ownership_marker_families_block(self):
        for field,marker in [('tags',['opentofu:managed']),('metadata',{'gitops':'managed'}),('properties',{'terraform':'managed'}),('tags',['capi:cluster']),('metadata',{'managed_by':'Argo'})]:
            self.write('fixture.json',{'records':{'server':{field:marker}}})
            r=self.prepare()
            self.assertEqual(r.returncode,2,r.stdout+r.stderr)
            self.assertFalse((self.root/'plan.json').exists())
    def test_secure_config_locator_preserved_and_credentials_dropped(self):
        self.env.update(OS_CLIENT_SECURE_FILE=str(self.root/'secure.yaml'),OS_PASSWORD='TOP_SECRET',OS_AUTH_URL='TOP_SECRET')
        r=self.run_cli('inspect','--context','context.json','--domain','compute','--evidence','c.json')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(self.calls()[0]['os_env'],{'OS_CLIENT_SECURE_FILE':self.env['OS_CLIENT_SECURE_FILE']})
    def test_diagnostics_follow_scoped_links_and_attached_volume(self):
        self.write('fixture.json',{'records':{'server':{'volumes_attached':[{'id':RESOURCE}]}},'lists':{'port list':[{'ID':RESOURCE,'device_id':RESOURCE,'network_id':RESOURCE,'security_group_ids':[RESOURCE],'fixed_ips':[{'subnet_id':RESOURCE}]}]}})
        r=self.run_cli('inspect','--context','context.json','--domain','troubleshooting','--resource-id',RESOURCE,'--evidence','chain.json')
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        commands=[' '.join(c['argv'][6:]) for c in self.calls()]
        for kind in ('port','network','subnet','volume'):
            self.assertTrue(any(c.startswith(kind+' show '+RESOURCE) for c in commands),commands)
        self.assertTrue(any(c.startswith('security group rule list '+RESOURCE) for c in commands),commands)
    def test_plan_cannot_move_to_another_work_root(self):
        self.assertEqual(self.prepare().returncode,0)
        sub=self.root/'elsewhere'; sub.mkdir()
        plan=json.loads((self.root/'plan.json').read_text())
        (sub/'plan.json').write_text(json.dumps(plan))
        r=self.run_cli('--work-root',str(sub),'execute','--plan','plan.json','--approve',plan['sha256'],'--evidence','x.json')
        self.assertIn('plan-work-root-mismatch',r.stdout)

if __name__=='__main__': unittest.main()
