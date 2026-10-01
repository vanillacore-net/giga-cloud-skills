#!/usr/bin/env python3
"""Prepare synthetic OFFLINE inputs outside the installed lab. Never calls a cloud."""
import argparse, json, os
from pathlib import Path
import yaml
import importlib.util
spec=importlib.util.spec_from_file_location('chapter5_platform',Path(__file__).with_name('platform.py'))
assert spec is not None and spec.loader is not None
platform_lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(platform_lab)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bootstrap-repo',type=Path,required=True)
    ap.add_argument('--work-dir',type=Path,required=True)
    args=ap.parse_args();repo=args.bootstrap_repo.resolve();root=args.work_dir.resolve()
    platform_lab.outside(root,[repo,platform_lab.LAB],'work directory')
    platform_lab.pinned({'bootstrap_repo':str(repo)})
    if root.exists() and any(root.iterdir()):ap.error('work directory must be empty')
    os.umask(0o077);root.mkdir(parents=True,exist_ok=True,mode=0o700)
    fixture=yaml.safe_load((repo/'tests/fixtures/non-default-pod-cidr.yml').read_text())
    environment={'bootstrap_environment':'offline','bootstrap_profile':'integration-test',
      'openstack':{'region_name':'OfflineRegion'},'gitops':{'repository_url':'https://git.example.test/platform/bootstrap.git',
      'management_revision':platform_lab.PIN,'foundation_revision':platform_lab.PIN,'spoke_revision':'main'},
      'cluster_foundations':fixture['cluster_foundations'],'management_monitoring':{'remote_write_receiver':False}}
    routing=environment['cluster_foundations']['govstack_routing']
    routing.update(repository_url=environment['gitops']['repository_url'],revision=platform_lab.PIN,routes=[])
    def save(name,data,is_yaml=False):
        p=root/name;p.write_text(yaml.safe_dump(data,sort_keys=False) if is_yaml else json.dumps(data,indent=2)+'\n');return str(p)
    env=save('environment.yml',environment,True);inv=save('inventory.yml',{'all':{'hosts':{}}},True)
    outputs=save('outputs.json',{k:{'value':'offline-'+k} for k in ('network_id','subnet_id','ssh_key_name','seed_security_group_id')})
    image=save('image.json',{'id':'12345678-1234-1234-1234-123456789abc','status':'active','kubernetes_version':'v1.36.3','evidence':'synthetic fixture, not a cloud image'})
    configs={}
    for index,(role,name) in enumerate(platform_lab.CLUSTERS.items()):
        start=64+index*32
        c={'cluster':{'name':name,'role':'loadbalancer' if role=='loadbalancer' else 'spoke','namespace':'govstack-clusters',
          'kubernetes_version':'v1.36.3','control_plane':{'replicas':1,'flavor':'offline-control'},'workers':{'replicas':1,'flavor':'offline-worker'},
          'openstack':{'identity_secret':name+'-openstack','child_cloud_secret':name+'-cloud','resource_tag':'govstack.itu.int:cluster-token=offline-'+name+'-123456789',
          'network_mode':'existing','image':'state','machine_template_revision':'r1','control_plane_template_revision':'r1'},
          'gateway':{'enabled':False},'routing':routing,'networking':{'api_vip':f'172.20.0.{10+index*10}','api_server_port':6443,
          'pod_cidr':f'172.{21+index}.0.0/16','service_cidr':f'10.{80+index}.0.0/16','service_vip_range':f'172.20.0.{start}-172.20.0.{start+15}','service_vip_cidr':f'172.20.0.{start}/28'}}}
        if role!='loadbalancer':c['cluster']['workloads']={'tenants':[{'name':'learning','source_repos':['https://git.example.test/team/deploy.git'],'namespaces':['chapter5-probe']}]}
        configs[role]=save(name+'.yml',c,True)
    case={'schema':'platform-session/v1','case_id':'offline-chapter5','mode':'example','bootstrap_repo':str(repo),
      'environment_config':env,'inventory':inv,'infrastructure_outputs':outputs,'image_metadata':image,
      'management_context':'offline-management','management_server':'https://management.example.test:6443',
      'clusters':platform_lab.CLUSTERS.copy(),'cluster_configs':configs,'domains':{'mediator':'mediator.example.test','examples':'apps.example.test'},
      'tls':{'mode':'trusted','issuer':{'name':'reviewed-issuer','kind':'ClusterIssuer'}},
      'routing':{'private_ingress':{'mediator':'172.20.0.96','examples':'172.20.0.128'},'probe_image':'docker.io/hashicorp/http-echo@sha256:fcb75f691c8b0414d670ae570240cbf95502cc18a9ba57e982ecac589760a186'}}
    save('inputs.json',case)
    print('OFFLINE INPUTS PREPARED: '+str(root/'inputs.json'))
    print('Synthetic IDs, image metadata, domains and inventory. No resources exist. Keep mode=example.')
if __name__=='__main__':main()
