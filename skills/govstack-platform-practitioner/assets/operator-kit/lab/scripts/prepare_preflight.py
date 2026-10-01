#!/usr/bin/env python3
"""Copy the three reviewed declarations for the upstream read-only preflight."""
import argparse,importlib.util,json,os
from pathlib import Path
spec=importlib.util.spec_from_file_location('chapter5_platform',Path(__file__).with_name('platform.py'))
assert spec and spec.loader
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',required=True);parser.add_argument('--output-dir',required=True);a=parser.parse_args()
    try:
        case=p.load_case(a.case);repo=p.pinned(case);out=p.absolute(a.output_dir,'output-dir')
        p.outside(out,[repo,p.LAB],'preflight output');p.require(not out.exists(),'use a new preflight output directory')
        declarations=[(name,p.declaration(case,role)[0].read_bytes()) for role,name in p.CLUSTERS.items()]
        os.umask(0o077);out.mkdir(parents=True,mode=0o700)
        for name,data in declarations:(out/(name+'.yml')).write_bytes(data)
        argv=['ansible-playbook','-i',case['inventory'],str(repo/'playbooks/01-preflight-readonly.yml'),'-e','@'+case['environment_config'],'-e',json.dumps({'environment_config_file':case['environment_config'],'preflight_clusters_dir':str(out)})]
        print(json.dumps({'scope':'local preparation only; no Ansible/cloud call','declarations':len(declarations),'argv':argv},indent=2))
    except (p.Refused,OSError,ValueError,KeyError) as e:parser.error(str(e))
if __name__=='__main__':main()
