import contextlib,io,json,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import yaml
import test_platform as fixture
p=fixture.p
BOOTSTRAP=fixture.BOOTSTRAP

class ApplyGateTests(unittest.TestCase):
    case: dict
    setUp=fixture.PlatformTests.setUp
    def live(self):
        env=Path(self.case['environment_config']);doc=yaml.safe_load(env.read_text())
        doc.update({'bootstrap_profile':'integration-test','bootstrap_apply':True,'controller':{'expected_hostname':'fixture-controller','inventory_host':'fixture-host'}})
        env.write_text(yaml.safe_dump(doc));self.case.update({'mode':'live','controller_hostname':'fixture-controller','controller_inventory_host':'fixture-host'})
    def arguments(self,**changes):
        values=dict(command='bootstrap',target='management',stage='infrastructure',execute=False,apply=False,confirm=None,timeout=30)
        values.update(changes);return SimpleNamespace(**values)
    def invoke(self,args):
        with contextlib.redirect_stdout(io.StringIO()),patch.object(p,'run',return_value='fixture recap') as run:
            p.bootstrap(self.case,BOOTSTRAP,args)
            return run
    def test_plan_forces_apply_false_even_if_environment_true(self):
        self.live()
        with contextlib.redirect_stdout(io.StringIO()) as out,patch.object(p,'run') as run:
            p.bootstrap(self.case,BOOTSTRAP,self.arguments())
        argv=json.loads(out.getvalue().splitlines()[0])['argv'];self.assertIs(json.loads(argv[-1])['bootstrap_apply'],False);run.assert_not_called()
    def test_remote_plan_does_not_apply(self):
        self.live();run=self.invoke(self.arguments(execute=True,confirm='bootstrap:management'))
        self.assertIs(json.loads(run.call_args.args[0][-1])['bootstrap_apply'],False)
    def test_explicit_apply_requires_separate_confirmation(self):
        self.live()
        with self.assertRaises(p.Refused):self.invoke(self.arguments(execute=True,apply=True,confirm='bootstrap:management'))
        run=self.invoke(self.arguments(execute=True,apply=True,confirm='bootstrap:management:apply'))
        self.assertIs(json.loads(run.call_args.args[0][-1])['bootstrap_apply'],True)
    def test_apply_refuses_wrong_stage_and_missing_execute(self):
        self.live()
        for args in [self.arguments(apply=True),self.arguments(stage='gateway',apply=True,execute=True,confirm='bootstrap:management:apply')]:
            with self.assertRaises(p.Refused):self.invoke(args)
    def test_apply_example_cannot_execute(self):
        with self.assertRaises(p.Refused):self.invoke(self.arguments(execute=True,apply=True,confirm='bootstrap:management:apply'))

if __name__=='__main__':unittest.main()
