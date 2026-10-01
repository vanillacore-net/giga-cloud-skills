"""Execute Chapter 4 documentation in isolated shells with synthetic targets only.

PATH contains only test-installed executables, never live cloud/Kubernetes clients.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/kubernetes-cluster-lifecycle-practitioner"
LAB = SKILL / "assets/operator-kit/lab"
BASH = shutil.which("bash")


def bash_blocks(path: Path) -> list[str]:
    return re.findall(r"(?m)^```bash\n(.*?)^```", path.read_text(), flags=re.S)


def documented_commands(path: Path, helper: str) -> list[str]:
    # Preserve shell syntax, including inline assignments and quoted arguments.
    return [
        line.strip()
        for block in bash_blocks(path)
        for line in block.replace("\\\n", " ").splitlines()
        if helper in line and not line.lstrip().startswith("#")
    ]


class DocumentedInvocationTests(unittest.TestCase):
    def setUp(self):
        if BASH is None:
            self.fail("Chapter 4 execution requires Bash")
        self.bash = BASH
        self.temporary = tempfile.TemporaryDirectory(prefix="chapter4-synthetic-")
        self.addCleanup(self.temporary.cleanup)
        # Spaces expose unquoted target expansion in documented commands.
        self.work = Path(self.temporary.name) / "synthetic work"
        self.work.mkdir()
        self.bin = self.work / "bin"
        self.bin.mkdir()
        (self.work / "scripts").mkdir()
        (self.bin / "python3").symlink_to(sys.executable)
        (self.bin / "bash").symlink_to(self.bash)
        self.environment = {"PATH": str(self.bin), "HOME": str(self.work)}

    def executable(self, path: Path, source: str):
        path.write_text(f"#!{sys.executable}\n" + source)
        path.chmod(0o755)

    def shell(self, commands: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [self.bash, "--noprofile", "--norc", "-c", "set -euo pipefail\n" + commands],
            cwd=self.work,
            env=self.environment,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )

    def test_runbook_preflight_passes_contract_and_cloud_in_fresh_shell(self):
        commands = documented_commands(
            SKILL / "references/operator-runbook.md", "./scripts/preflight-readonly.sh"
        )
        self.assertEqual(len(commands), 1)
        # This fake helper enforces the real helper's two required positional args.
        # No contract is validated and no OpenStack client is installed or invoked.
        self.executable(
            self.work / "scripts/preflight-readonly.sh",
            "import json, sys\n"
            "if len(sys.argv) != 3:\n"
            "    sys.exit('usage: preflight-readonly.sh CONTRACT OS_CLOUD')\n"
            "print(json.dumps(sys.argv[1:]))\n",
        )
        result = self.shell("OS_CLOUD='synthetic cloud only'\n" + commands[0])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            ["environment-contract.yaml", "synthetic cloud only"],
        )

    def test_cleanup_captures_both_children_after_fresh_shell_session_load(self):
        walkthrough = LAB / "walkthroughs/09-cleanup.md"
        commands = documented_commands(walkthrough, "scripts/capture-openstack-ids.py")
        self.assertEqual(len(commands), 2)
        startup = bash_blocks(walkthrough)[0]
        # Exercise the real confirmation guard and evidence writer. Only its API
        # clients are replaced; the cleanup/deletion commands are never executed.
        for helper in ("capture-openstack-ids.py", "require-context.sh"):
            shutil.copy2(LAB / "scripts" / helper, self.work / "scripts" / helper)
        (self.work / "evidence").mkdir()
        (self.work / "synthetic repo" / ".git").mkdir(parents=True)
        (self.work / "synthetic clouds.yaml").write_text("# synthetic, no credentials\n")
        contexts = {
            "management.kubeconfig": "synthetic management context",
            "service-a.kubeconfig": "synthetic service-a context",
            "loadbalancer.kubeconfig": "synthetic loadbalancer context",
        }
        for filename in contexts:
            (self.work / filename).write_text("# synthetic, not a usable kubeconfig\n")
        session = {
            "KUBECONFIG": str(self.work / "management.kubeconfig"),
            "MANAGEMENT_CONTEXT": contexts["management.kubeconfig"],
            "SERVICE_A_KUBECONFIG": str(self.work / "service-a.kubeconfig"),
            "SERVICE_A_CONTEXT": contexts["service-a.kubeconfig"],
            "LOADBALANCER_KUBECONFIG": str(self.work / "loadbalancer.kubeconfig"),
            "LOADBALANCER_CONTEXT": contexts["loadbalancer.kubeconfig"],
            "OS_CLOUD": "synthetic cloud only",
            "OS_CLIENT_CONFIG_FILE": str(self.work / "synthetic clouds.yaml"),
            "CONFIG_REPO": str(self.work / "synthetic repo"),
        }
        # Deliberately no exports or confirmation state from an earlier step.
        (self.work / "lab-session.env").write_text(
            "\n".join(f"{key}={shlex.quote(value)}" for key, value in session.items()) + "\n"
        )
        client = (
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "args = sys.argv[1:]\n"
            "tool = Path(sys.argv[0]).name\n"
            "with Path('client-calls.jsonl').open('a') as log:\n"
            "    log.write(json.dumps({'tool': tool, 'args': args, 'confirmation': "
            "os.environ.get('CONFIRM_MANAGEMENT_CONTEXT')}) + '\\n')\n"
            f"contexts = {contexts!r}\n"
            "if tool == 'kubectl':\n"
            "    assert args[0] == '--kubeconfig'\n"
            "    context = contexts[Path(args[1]).name]\n"
            "    if args[2:4] == ['config', 'current-context']:\n"
            "        print(context); sys.exit(0)\n"
            "    if args[2:4] == ['config', 'get-contexts']:\n"
            "        print(context); sys.exit(0)\n"
            "    if args[2:5] == ['config', 'view', '--minify']:\n"
            "        print('https://synthetic.invalid:6443'); sys.exit(0)\n"
            "    assert args[2:4] == ['--context', context]\n"
            "    if args[4:] == ['auth', 'can-i', 'get', 'pods', '--namespace', 'kube-system']:\n"
            "        print('yes'); sys.exit(0)\n"
            "    assert args[4] == '-n'\n"
            "    namespace = args[5]\n"
            "    assert namespace in ('service-a', 'loadbalancer')\n"
            "    if args[6:] == ['get', 'cluster', namespace, '-o', 'json']:\n"
            "        data = {'spec': {'infrastructureRef': {'name': namespace + '-infra'}}}\n"
            "    elif args[6:] == ['get', 'openstackmachines.infrastructure.cluster.x-k8s.io', '-o', 'json']:\n"
            "        data = {'items': [{'metadata': {'labels': {'cluster.x-k8s.io/cluster-name': namespace}}, "
            "'status': {'instanceID': 'synthetic-server-' + namespace}}]}\n"
            "    elif args[6:] == ['get', 'openstackcluster.infrastructure.cluster.x-k8s.io', namespace + '-infra', '-o', 'json']:\n"
            "        data = {'spec': {'apiServerFixedIP': '192.0.2.10'}}\n"
            "    else:\n"
            "        sys.exit('unexpected synthetic kubectl call: ' + repr(args))\n"
            "elif tool == 'openstack':\n"
            "    assert args[:2] == ['--os-cloud', 'synthetic cloud only']\n"
            "    if args[2:5] == ['port', 'list', '--server']:\n"
            "        assert args[5].startswith('synthetic-server-') and args[6:] == ['-f', 'json']\n"
            "        data = [{'ID': 'synthetic-port'}]\n"
            "    elif args[2:5] == ['server', 'volume', 'list']:\n"
            "        assert args[5].startswith('synthetic-server-') and args[6:] == ['-f', 'json']\n"
            "        data = [{'ID': 'synthetic-volume'}]\n"
            "    elif args[2:] == ['loadbalancer', 'list', '--vip-address', '192.0.2.10', '-f', 'json']:\n"
            "        data = [{'ID': 'synthetic-api-lb'}]\n"
            "    else:\n"
            "        sys.exit('unexpected synthetic openstack call: ' + repr(args))\n"
            "else:\n"
            "    sys.exit('unexpected test executable')\n"
            "print(json.dumps(data))\n"
        )
        for tool in ("kubectl", "openstack"):
            self.executable(self.bin / tool, client)
        for cluster, command in zip(("service-a", "loadbalancer"), commands):
            with self.subTest(cluster=cluster):
                log = self.work / "client-calls.jsonl"
                log.unlink(missing_ok=True)
                # Each child starts a separate clean process and sources the
                # documented session boundary before executing its capture line.
                result = self.shell(startup + "\n" + command)
                self.assertEqual(result.returncode, 0, result.stderr)
                evidence = json.loads(
                    (self.work / "evidence" / f"{cluster}-resource-ids.json").read_text()
                )
                self.assertEqual(evidence, {
                    "cluster": cluster,
                    "namespace": cluster,
                    "captured_before_deletion": True,
                    "server_ids": [f"synthetic-server-{cluster}"],
                    "port_ids": ["synthetic-port"],
                    "volume_ids": ["synthetic-volume"],
                    "loadbalancer_ids": ["synthetic-api-lb"],
                })
                calls = [json.loads(line) for line in log.read_text().splitlines()]
                capture_calls = [call for call in calls if call["confirmation"] is not None]
                self.assertEqual(len(capture_calls), 6)
                self.assertTrue(all(
                    call["confirmation"] == session["MANAGEMENT_CONTEXT"]
                    for call in capture_calls
                ))
                self.assertEqual(sum(call["tool"] == "openstack" for call in capture_calls), 3)


if __name__ == "__main__":
    unittest.main()
