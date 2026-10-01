import json,subprocess,sys,tempfile,unittest
from pathlib import Path
import test_platform as fixture

class PreflightCompanionTests(unittest.TestCase):
    case: dict
    setUp=fixture.PlatformTests.setUp
    def test_preflight_copies_exact_selected_declarations_and_prints_real_interface(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);case=root/'case.json';case.write_text(json.dumps(self.case));out=root/'preflight'
            r=subprocess.run([sys.executable,str(fixture.LAB/'scripts/prepare_preflight.py'),'--case',str(case),'--output-dir',str(out)],capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stderr);record=json.loads(r.stdout)
            self.assertEqual(record['declarations'],3)
            self.assertEqual({x.name for x in out.iterdir()},{name+'.yml' for name in fixture.p.CLUSTERS.values()})
            self.assertIn('01-preflight-readonly.yml',record['argv'][3]);self.assertEqual(json.loads(record['argv'][-1])['preflight_clusters_dir'],str(out))
            for role,name in fixture.p.CLUSTERS.items():self.assertEqual((out/(name+'.yml')).read_bytes(),Path(self.case['cluster_configs'][role]).read_bytes())
    def test_malformed_inputs_refuse_init_without_case_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);inputs=root/'bad.json';target=root/'new-case.json';bad=dict(self.case);bad.pop('management_context');inputs.write_text(json.dumps(bad))
            r=subprocess.run([sys.executable,str(fixture.LAB/'scripts/platform.py'),'init','--inputs',str(inputs),'--case',str(target)],capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,2);self.assertIn('management_context is required',r.stderr);self.assertFalse(target.exists())
if __name__=='__main__':unittest.main()
