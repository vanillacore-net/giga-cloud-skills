import importlib.util,json,os,shlex,subprocess,sys,tempfile,unittest
from pathlib import Path
import yaml
LAB=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('storage',LAB/'scripts/render_storage_smoke.py')
assert spec is not None and spec.loader is not None
storage=importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)
class CompanionTests(unittest.TestCase):
 def test_example_real_cli_chain(self):
  repo=os.environ.get('CH5_BOOTSTRAP_REPO');self.assertTrue(repo,'Set CH5_BOOTSTRAP_REPO')
  with tempfile.TemporaryDirectory(prefix='chapter5-example-') as tmp:
   root=Path(tmp);case=root/'case.json';script=LAB/'scripts/platform.py'
   commands=[[sys.executable,str(LAB/'scripts/prepare_example.py'),'--bootstrap-repo',repo,'--work-dir',str(root/'inputs')],
    [sys.executable,str(script),'init','--inputs',str(root/'inputs/inputs.json'),'--case',str(case)]]
   commands += [[sys.executable,str(script),verb,'--case',str(case)] for verb in ['doctor','render','route','handoff']]
   for command in commands:
    r=subprocess.run(command,capture_output=True,text=True,timeout=120);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
   saved=json.loads(case.read_text());self.assertEqual(saved['mode'],'example')
   output=json.loads((root/'generated/handoff.json').read_text());self.assertEqual(output['evidence'],'prepared-only')
   self.assertEqual(len(list((root/'generated/spokes').glob('*/cluster.yaml'))),3)
 def test_storage_explicit_class_and_scope(self):
  writer,reader=storage.documents('reviewed-storage','1Gi','registry.example.test/shell@sha256:'+'a'*64)
  self.assertEqual(writer[0]['spec']['storageClassName'],'reviewed-storage')
  self.assertEqual(writer[1]['spec']['volumes'][0]['persistentVolumeClaim']['claimName'],reader[0]['spec']['volumes'][0]['persistentVolumeClaim']['claimName'])
  self.assertEqual(reader[0]['spec']['containers'][0]['volumeMounts'][0]['readOnly'],True)
  self.assertTrue(all(x['kind']!='Namespace' for x in writer+reader))
 def test_storage_marker_commands_real_local_shell(self):
  with tempfile.TemporaryDirectory(prefix='chapter5-marker-') as tmp:
   marker=Path(tmp)/'marker';path=shlex.quote(str(marker))
   for command in [storage.WRITE,storage.READ]:
    r=subprocess.run(['sh','-eu','-c',command.replace('/data/marker',path)],capture_output=True,text=True,timeout=5);self.assertEqual(r.returncode,0,r.stderr)
   self.assertEqual(marker.read_text().strip(),storage.MARKER)
   marker.write_text('wrong-marker')
   r=subprocess.run(['sh','-eu','-c',storage.READ.replace('/data/marker',path)],capture_output=True,text=True,timeout=5);self.assertNotEqual(r.returncode,0)
 def test_storage_rejects_unreviewed_inputs(self):
  for args in [('', '1Gi','r@sha256:'+'a'*64),('s','0Gi','r@sha256:'+'a'*64),('s','1Gi','image:latest')]:
   with self.assertRaises(ValueError):storage.documents(*args)
if __name__=='__main__':unittest.main()
