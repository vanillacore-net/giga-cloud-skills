#!/usr/bin/env python3
"""Portable, tenant-only OpenStack operator. Stdlib; never invokes a shell."""
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

class Blocked(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def uid(value):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value.lower():
            raise ValueError()
    except (ValueError, AttributeError):
        raise Blocked('uuid-required')
    return value

class Files:
    def __init__(self, root):
        try:
            raw = Path(root).absolute()
            if any(p.is_symlink() for p in (raw, *raw.parents)): raise Blocked('symlink-refused')
            self.root = raw.resolve(strict=True)
            if not self.root.is_dir() or self.root.stat().st_uid != os.getuid(): raise Blocked('unsafe-work-root')
            installed = Path(__file__).resolve().parent.parent
            if self.root == installed or installed in self.root.parents: raise Blocked('protected-work-root')
            for parent in (self.root, *self.root.parents):
                if (parent / '.git').exists() or (parent / 'SKILL.md').exists(): raise Blocked('protected-work-root')
            self.root.chmod(0o700)
        except (OSError, ValueError, RuntimeError):
            raise Blocked('invalid-work-root')
    def path(self, name):
        p = Path(name)
        if not p.is_absolute():
            p = self.root / p
        try:
            p.relative_to(self.root)
        except ValueError:
            raise Blocked('path-outside-work-root')
        if '..' in p.parts:
            raise Blocked('path-outside-work-root')
        current = self.root
        for part in p.relative_to(self.root).parts:
            current = current / part
            if current.is_symlink():
                raise Blocked('symlink-refused')
        if p.parent.resolve() != p.parent or not p.parent.is_dir():
            raise Blocked('unsafe-parent')
        return p
    def read(self, name):
        p = self.path(name)
        try:
            fd = os.open(p, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
            with os.fdopen(fd) as f:
                st = os.fstat(f.fileno())
                if not p.is_file() or st.st_uid != os.getuid():
                    raise Blocked('unsafe-input')
                os.fchmod(f.fileno(), 0o600)
                return json.load(f)
        except (OSError, ValueError):
            raise Blocked('invalid-input-file')
    def write(self, name, value, replace=False):
        p = self.path(name)
        temp = None
        try:
            fd, temp = tempfile.mkstemp(prefix='.ops-', dir=p.parent)
            with os.fdopen(fd, 'wb') as f:
                os.fchmod(f.fileno(), 0o600)
                f.write(canonical(value) + b'\n')
                f.flush()
                os.fsync(f.fileno())
            if replace:
                os.replace(temp, p)
            else:
                os.link(temp, p)  # exclusive atomic publication; never clobber
            dfd = os.open(p.parent, os.O_RDONLY)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        except FileExistsError:
            raise Blocked('output-already-exists')
        except OSError:
            raise Blocked('output-write-failed')
        finally:
            if temp:
                Path(temp).unlink(missing_ok=True)

def context(value):
    required = {'schema','case_id','cloud','project_id','region','ownership','timeout_seconds'}
    if not isinstance(value, dict) or set(value) != required or value['schema'] != 'openstack-context/v1':
        raise Blocked('invalid-context')
    uid(value['project_id'])
    for key in ('case_id','cloud','region'):
        if not isinstance(value[key], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', value[key]):
            raise Blocked('invalid-context')
    if value['ownership'] not in ('direct','opentofu','capi','gitops','unknown'):
        raise Blocked('invalid-context')
    if type(value['timeout_seconds']) is not int or not 1 <= value['timeout_seconds'] <= 300:
        raise Blocked('invalid-timeout')
    return value

class Client:
    def __init__(self, ctx):
        self.ctx = ctx
        self.env = {k:v for k,v in os.environ.items() if not k.startswith('OS_') or k in ('OS_CLIENT_CONFIG_FILE','OS_CLIENT_SECURE_FILE')}
        self.executable = os.environ.get('OPENSTACK_OPS_CLIENT', 'openstack')
    def call(self, argv, columns=None, formatted=True, timeout=None):
        args = [self.executable, '--os-cloud', self.ctx['cloud'], '--os-project-id', self.ctx['project_id'], '--os-region-name', self.ctx['region']] + list(argv)
        if formatted:
            args += ['-f', 'json']
        if columns:
            for column in columns:
                args += ['-c', column]
        try:
            completed = subprocess.run(args, env=self.env, capture_output=True, text=True, timeout=timeout or self.ctx['timeout_seconds'], shell=False)
        except subprocess.TimeoutExpired:
            raise Blocked('timeout')
        except OSError:
            raise Blocked('client-unavailable')
        if completed.returncode:
            error = completed.stderr.lower()
            # Never disclose raw stdout/stderr, endpoints, credentials or tokens.
            if re.search(r'\b401\b|unauthorized', error): code = 'authentication-denied'
            elif re.search(r'\b403\b|forbidden', error): code = 'permission-denied'
            elif 'endpoint' in error: code = 'api-unavailable'
            elif re.search(r'\b404\b|no .* found|not found', error): code = 'not-found'
            elif 'timeout' in error or 'timed out' in error: code = 'timeout'
            elif 'not a' in error or 'unrecognized arguments' in error or 'invalid choice' in error: code = 'client-command-unsupported'
            else: code = 'api-error'
            raise Blocked(code)
        if not formatted:
            return {}
        try:
            return json.loads(completed.stdout)
        except ValueError:
            raise Blocked('invalid-client-response')
    def identity(self):
        data = self.call(['token','issue'], columns=['project_id'])
        if not isinstance(data, dict) or data.get('project_id') != self.ctx['project_id']:
            raise Blocked('wrong-project')

DOMAINS = ('environment','compute','networking','storage','troubleshooting')
INVENTORY = {
    'environment': [('quota',['quota','show']), ('catalogue',['catalog','list']), ('servers',['server','list']), ('networks',['network','list']), ('volumes',['volume','list']), ('images',['image','list']), ('flavors',['flavor','list'])],
    'compute': [('servers',['server','list']), ('images',['image','list']), ('flavors',['flavor','list'])],
    'networking': [('networks',['network','list']), ('subnets',['subnet','list']), ('routers',['router','list']), ('ports',['port','list']), ('security_groups',['security','group','list']), ('floating_ips',['floating','ip','list'])],
    'storage': [('volumes',['volume','list']), ('snapshots',['volume','snapshot','list'])],
    'troubleshooting': [('servers',['server','list']), ('ports',['port','list']), ('routers',['router','list']), ('security_groups',['security','group','list']), ('floating_ips',['floating','ip','list']), ('volumes',['volume','list'])],
}

def record(ctx, domain, action, level, plan_hash=None):
    return dict(schema='openstack-operation-record/v1', case_id=ctx['case_id'], domain=domain, action=action, project_id=ctx['project_id'], region=ctx['region'], execution_level=level, checks=[], resource_ids=[], findings=[], status='pending', next_action='review-evidence', plan_hash=plan_hash)

# Public evidence uses a positive field allowlist, never arbitrary metadata.
PUBLIC_FIELDS = {'id','name','status','ram','vcpus','disk','size','project_id','tenant_id','network_id','device_id','security_group_id','volume_id','port_id','protocol','port_range_min','port_range_max','remote_ip_prefix','direction','ethertype','cidr','gateway_ip','ip_version','router:external'}
QUOTA_FIELDS = {'cores','ram','instances','volumes','snapshots','gigabytes','networks','subnets','ports','routers','floating_ips','security_groups','security_group_rules','key_pairs','fixed_ips','injected_files','injected_file_content_bytes','injected_file_path_bytes','properties','backup_gigabytes','backups','per_volume_gigabytes'}
def safe_values(data, quota=False):
    if isinstance(data,list): return [safe_values(row,quota) for row in data if isinstance(row,dict)]
    if not isinstance(data,dict): return {}
    allowed = QUOTA_FIELDS if quota else PUBLIC_FIELDS
    return {str(k).lower():v for k,v in data.items() if str(k).lower() in allowed and type(v) in (str,int,float,bool,type(None))}

def diagnose(ctx, client, result, identifier):
    uid(identifier)
    def check(label, fn):
        try:
            data=fn()
            result['findings'].append({'check':label,'status':'available','values':safe_values(data)})
            for row in data if isinstance(data,list) else [data]:
                if isinstance(row,dict):
                    rid=row.get('id',row.get('ID'))
                    try: uid(rid)
                    except Blocked: continue
                    if rid not in result['resource_ids']: result['resource_ids'].append(rid)
            return data
        except Blocked as error:
            result['findings'].append({'check':label,'status':'limited','code':error.code})
            return None
    server=check('server',lambda:scoped(client,'server',identifier))
    if server is None: return
    ports=check('server-port-chain',lambda:client.call(['port','list','--device-id',identifier]))
    for row in ports if isinstance(ports,list) else []:
        if not isinstance(row,dict): continue
        port=check('port',lambda row=row:scoped(client,'port',uid(row.get('id',row.get('ID')))))
        if port is None: continue
        # Some clients omit link fields from show; combine with the scoped list.
        links=dict(row); links.update(port)
        if links.get('device_id') not in (None,identifier):
            result['findings'].append({'check':'port-device','status':'limited','code':'resource-wrong-server'}); continue
        if links.get('network_id'): check('network',lambda:scoped(client,'network',uid(links['network_id'])))
        for ip in links.get('fixed_ips',[]):
            if isinstance(ip,dict) and ip.get('subnet_id'): check('subnet',lambda ip=ip:scoped(client,'subnet',uid(ip['subnet_id'])))
        for sg in links.get('security_group_ids',links.get('security_groups',[])):
            group=check('security-group',lambda sg=sg:scoped(client,'security group',uid(sg)))
            if group is not None:
                check('security-group-rules',lambda sg=sg:client.call(['security','group','rule','list',uid(sg)]))
        check('floating-ips-optional',lambda:client.call(['floating','ip','list','--port',uid(links.get('id',links.get('ID')))]))
    for volume in server.get('volumes_attached',server.get('os-extended-volumes:volumes_attached',[])):
        if isinstance(volume,dict): check('attached-volume',lambda volume=volume:scoped(client,'volume',uid(volume.get('id'))))

def inspect(ctx, domain, client, resource_id=None):
    result = record(ctx, domain, 'inspect', 'read-only')
    client.identity()
    result['checks'].append({'check':'identity','status':'passed'})
    if domain == 'troubleshooting' and resource_id:
        diagnose(ctx,client,result,resource_id)
    for label, command in ([] if domain == 'troubleshooting' and resource_id else INVENTORY[domain]):
        try:
            data = client.call(command)
            count = len(data) if isinstance(data, list) else None
            result['findings'].append({'api':label,'status':'available','count':count,'values':safe_values(data,label=='quota')})
            if isinstance(data, list):
                for row in data:
                    if isinstance(row, dict):
                        identifier = row.get('ID',row.get('id'))
                        try: uid(identifier)
                        except Blocked: continue
                        if identifier not in result['resource_ids']: result['resource_ids'].append(identifier)
        except Blocked as error:
            result['findings'].append({'api':label,'status':'limited','code':error.code})
    result['status'] = 'partial' if any(x['status']=='limited' for x in result['findings']) else 'complete'
    return result

# Required / optional fields. Arbitrary command lines and options are never accepted.
FIELDS = {
 'server-create': ('name image_id flavor_id network_id security_group_id', 'key_name user_data_file'),
 'server-start': ('server_id',''), 'server-stop': ('server_id',''),
 'server-reboot': ('server_id',''), 'server-resize': ('server_id flavor_id',''),
 'server-resize-confirm': ('server_id',''), 'server-resize-revert': ('server_id',''),
 'server-delete': ('server_id confirm_delete data_policy',''),
 'network-create': ('name',''), 'subnet-create': ('name network_id cidr','gateway'),
 'router-create': ('name',''), 'router-add-subnet': ('router_id subnet_id',''),
 'router-set-external': ('router_id external_network_id allow_external',''),
 'security-group-create': ('name',''),
 'security-rule-create': ('security_group_id protocol port_min port_max remote_cidr','allow_world'),
 'security-rule-delete': ('rule_id confirm_delete',''),
 'floating-ip-create': ('external_network_id allow_external',''),
 'floating-ip-associate': ('floating_ip_id port_id fixed_ip allow_external',''),
 'floating-ip-disassociate': ('floating_ip_id',''),
 'floating-ip-delete': ('floating_ip_id confirm_delete',''),
 'volume-create': ('name size_gib',''),
 'volume-attach': ('server_id volume_id data_policy',''),
 'volume-detach': ('server_id volume_id data_policy',''),
 'volume-extend': ('volume_id size_gib',''),
 'volume-snapshot': ('volume_id name',''),
 'volume-from-snapshot': ('snapshot_id name size_gib',''),
 'volume-delete': ('volume_id confirm_delete data_policy',''),
}
TYPES = {'server_id':'server','image_id':'image','flavor_id':'flavor','network_id':'network','external_network_id':'network','subnet_id':'subnet','router_id':'router','security_group_id':'security group','rule_id':'security group rule','floating_ip_id':'floating ip','port_id':'port','volume_id':'volume','snapshot_id':'volume snapshot'}

def request(value):
    if not isinstance(value,dict) or set(value) != {'action','parameters'} or not isinstance(value['action'],str) or value['action'] not in FIELDS or not isinstance(value['parameters'],dict):
        raise Blocked('invalid-request')
    action, p = value['action'], value['parameters']
    required, optional = (set(x.split()) for x in FIELDS[action])
    if not required <= set(p) or not set(p) <= required | optional:
        raise Blocked('invalid-parameters')
    for k,v in p.items():
        if k in TYPES: uid(v)
        if k in ('name','key_name') and (not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,63}',v)):
            raise Blocked('invalid-name')
        if k in ('allow_world','allow_external','confirm_delete') and type(v) is not bool:
            raise Blocked('explicit-boolean-required')
        if k == 'size_gib' and (type(v) is not int or not 1 <= v <= 65536):
            raise Blocked('invalid-size')
    if 'confirm_delete' in p and p['confirm_delete'] is not True:
        raise Blocked('deletion-not-approved')
    if 'data_policy' in p:
        expected = 'delete' if action.endswith('-delete') else 'retain'
        if p['data_policy'] != expected: raise Blocked('data-retention-decision-required')
    if 'allow_external' in p and p['allow_external'] is not True:
        raise Blocked('external-exposure-not-approved')
    if action == 'subnet-create':
        try:
            net = ipaddress.ip_network(p['cidr'], strict=True)
            if net.prefixlen == 0: raise ValueError()
            if 'gateway' in p and p['gateway'] != 'none' and ipaddress.ip_address(p['gateway']) not in net: raise ValueError()
        except (ValueError,TypeError): raise Blocked('invalid-cidr-or-gateway')
    if action == 'security-rule-create':
        try: net = ipaddress.ip_network(p['remote_cidr'],strict=True)
        except (ValueError,TypeError): raise Blocked('invalid-cidr')
        if net.prefixlen == 0 and p.get('allow_world') is not True: raise Blocked('world-exposure-not-approved')
        if p['protocol'] not in ('tcp','udp'): raise Blocked('unsupported-protocol')
        if any(type(p[k]) is not int or not 1 <= p[k] <= 65535 for k in ('port_min','port_max')) or p['port_min'] > p['port_max']:
            raise Blocked('invalid-port-range')
    if 'fixed_ip' in p:
        try: ipaddress.ip_address(p['fixed_ip'])
        except (ValueError,TypeError): raise Blocked('invalid-ip')
    return value

def show(client, kind, identifier):
    data = client.call(kind.split()+['show',identifier])
    if not isinstance(data,dict) or data.get('id',data.get('ID')) != identifier:
        raise Blocked('invalid-resource-response')
    return data

def scoped(client, kind, identifier):
    data = show(client,kind,identifier)
    owner = data.get('project_id',data.get('tenant_id',data.get('os-vol-tenant-attr:tenant_id')))
    if owner != client.ctx['project_id']: raise Blocked('resource-wrong-project')
    return data

def ownership(data):
    markers = canonical({k:data[k] for k in ('properties','metadata','tags') if k in data}).decode().lower()
    if re.search(r'cluster\.x-k8s\.io|capi|cluster-api|opentofu|terraform|gitops|argocd|\bargo\b|argo[./:_-]|fluxcd',markers):
        raise Blocked('externally-owned-or-unknown')

def stable_state(data):
    selected = PUBLIC_FIELDS | {'flavor','image','volumes_attached','os-extended-volumes:volumes_attached','attachments','fixed_ips','security_group_ids','security_groups','external_gateway_info','subnets','properties','metadata','tags','admin_state_up','shared','port_security_enabled'}
    return {str(k).lower():v for k,v in data.items() if str(k).lower() in selected}

def preflight(ctx, req, client):
    if ctx['ownership'] != 'direct': raise Blocked('externally-owned-or-unknown')
    client.identity()
    observed = {}
    for key,kind in TYPES.items():
        if key not in req['parameters']: continue
        identifier = req['parameters'][key]
        if key in ('image_id','flavor_id'):
            data = show(client,kind,identifier)  # shared read-only reference
        elif key == 'external_network_id':
            data = show(client,kind,identifier)
            if data.get('router:external') is not True: raise Blocked('network-not-external')
        elif key == 'rule_id':
            data = show(client,kind,identifier)
            parent = scoped(client,'security group',uid(data.get('security_group_id')))
            ownership(parent); observed['rule_parent'] = parent
        elif key == 'snapshot_id':
            data = scoped(client,kind,identifier)
            parent = scoped(client,'volume',uid(data.get('volume_id')))
            ownership(parent); observed['snapshot_source'] = parent
        else:
            data = scoped(client,kind,identifier)
        ownership(data)
        observed[key] = data
    action, p = req['action'], req['parameters']
    if action in ('server-resize-confirm','server-resize-revert') and str(observed['server_id'].get('status','')).upper() != 'VERIFY_RESIZE':
        raise Blocked('server-not-awaiting-resize-decision')
    if action == 'server-delete':
        # Avoid implicit deletion of Cinder volumes: detach them in a separate approved action.
        if observed['server_id'].get('volumes_attached') or observed['server_id'].get('os-extended-volumes:volumes_attached'):
            raise Blocked('detach-and-review-volumes-before-server-delete')
    if action in ('volume-delete','volume-extend','volume-snapshot'):
        v = observed['volume_id']
        if str(v.get('status','')).lower() != 'available' or v.get('attachments'):
            raise Blocked('volume-must-be-available-and-unattached')
    if action == 'volume-extend' and p['size_gib'] <= observed['volume_id'].get('size',65536):
        raise Blocked('extension-must-increase-size')
    if action == 'volume-from-snapshot' and str(observed['snapshot_id'].get('status','')).lower() != 'available':
        raise Blocked('snapshot-not-available')
    return [{'check':'identity-and-resource-project','status':'passed'}, {'check':'ownership-operator-attestation','status':'passed','basis':'reviewed-ownership-records; live markers checked, absence is not proof'}, {'check':'live-preflight-state','status':'passed','sha256':digest({k:stable_state(v) for k,v in observed.items()})}]

def build(req):
    """Return whitelist-derived domain, argv, output-kind, target-kind and target-id."""
    a,p = req['action'],req['parameters']
    domain = 'compute' if a.startswith('server-') else 'storage' if a.startswith('volume-') else 'networking'
    created = None
    kind = TYPES.get(next((k for k in p if k in TYPES), ''), '')
    identifier = next((p[k] for k in p if k in TYPES), None)
    if a == 'server-create':
        cmd = ['server','create','--image',p['image_id'],'--flavor',p['flavor_id'],'--network',p['network_id'],'--security-group',p['security_group_id']]
        for key,flag in [('key_name','--key-name'),('user_data_file','--user-data')]:
            if key in p: cmd += [flag,p[key]]
        cmd += [p['name']]; created = kind = 'server'
    elif a in ('server-start','server-stop','server-reboot'):
        cmd=['server',a.split('-')[1]] + (['--soft'] if a=='server-reboot' else []) + [p['server_id']]; kind='server'; identifier=p['server_id']
    elif a.startswith('server-resize'):
        cmd=['server','resize']
        cmd += [a.rsplit('-',1)[1]] if a != 'server-resize' else ['--flavor',p['flavor_id']]
        cmd += [p['server_id']]; kind='server'; identifier=p['server_id']
    elif a == 'server-delete': cmd=['server','delete',p['server_id']]; kind='server'; identifier=p['server_id']
    elif a in ('network-create','router-create','security-group-create'):
        kind={'network-create':'network','router-create':'router','security-group-create':'security group'}[a]
        cmd=kind.split()+['create']
        if a == 'network-create': cmd += ['--internal','--no-share']
        cmd += [p['name']]; created=kind
    elif a == 'subnet-create':
        cmd=['subnet','create','--network',p['network_id'],'--subnet-range',p['cidr'],'--ip-version',str(ipaddress.ip_network(p['cidr']).version)]
        if 'gateway' in p: cmd+=['--gateway',p['gateway']]
        cmd += [p['name']]; created=kind='subnet'
    elif a == 'router-add-subnet': cmd=['router','add','subnet',p['router_id'],p['subnet_id']]; kind='router'; identifier=p['router_id']
    elif a == 'router-set-external': cmd=['router','set','--external-gateway',p['external_network_id'],p['router_id']]; kind='router'; identifier=p['router_id']
    elif a == 'security-rule-create':
        cmd=['security','group','rule','create','--ingress','--protocol',p['protocol'],'--dst-port',str(p['port_min'])+':'+str(p['port_max']),'--remote-ip',p['remote_cidr'],'--ethertype','IPv'+str(ipaddress.ip_network(p['remote_cidr']).version),p['security_group_id']]; created=kind='security group rule'
    elif a == 'security-rule-delete': cmd=['security','group','rule','delete',p['rule_id']]; kind='security group rule'; identifier=p['rule_id']
    elif a == 'floating-ip-create': cmd=['floating','ip','create',p['external_network_id']]; created=kind='floating ip'
    elif a == 'floating-ip-associate': cmd=['floating','ip','set','--port',p['port_id'],'--fixed-ip-address',p['fixed_ip'],p['floating_ip_id']]; kind='floating ip'; identifier=p['floating_ip_id']
    elif a == 'floating-ip-disassociate': cmd=['floating','ip','unset','--port',p['floating_ip_id']]; kind='floating ip'; identifier=p['floating_ip_id']
    elif a == 'floating-ip-delete': cmd=['floating','ip','delete',p['floating_ip_id']]; kind='floating ip'; identifier=p['floating_ip_id']
    elif a in ('volume-create','volume-from-snapshot'):
        cmd=['volume','create','--size',str(p['size_gib'])]
        if a == 'volume-from-snapshot': cmd += ['--snapshot',p['snapshot_id']]
        cmd += [p['name']]; created=kind='volume'
    elif a in ('volume-attach','volume-detach'):
        cmd=['server','add' if a=='volume-attach' else 'remove','volume']
        if a=='volume-attach': cmd += ['--disable-delete-on-termination']
        cmd += [p['server_id'],p['volume_id']]; kind='volume'; identifier=p['volume_id']
    elif a == 'volume-extend': cmd=['volume','set','--size',str(p['size_gib']),p['volume_id']]; kind='volume'; identifier=p['volume_id']
    elif a == 'volume-snapshot': cmd=['volume','snapshot','create','--volume',p['volume_id'],p['name']]; created=kind='volume snapshot'
    elif a == 'volume-delete': cmd=['volume','delete',p['volume_id']]; kind='volume'; identifier=p['volume_id']
    else: raise Blocked('unsupported-action')
    return domain,cmd,created,kind,identifier

def user_data(files, req):
    name = req['parameters'].get('user_data_file')
    if name is None: return None
    p = files.path(name)
    try:
        if not p.is_file() or p.stat().st_uid != os.getuid(): raise Blocked('unsafe-user-data')
        p.chmod(0o600)
        content=p.read_bytes()
        if len(content) > 1024*1024: raise Blocked('user-data-too-large')
        return hashlib.sha256(content).hexdigest()
    except OSError: raise Blocked('user-data-unavailable')

def prepare(files, ctx, req, client):
    req = request(req)
    checks = preflight(ctx,req,client)
    now = time.time()
    plan = dict(schema='openstack-plan/v1', context=ctx, request=req, user_data_sha256=user_data(files,req), checks=checks, work_root=str(files.root), created_at=now, expires_at=now+1800)
    plan['sha256']=digest(plan)
    return plan

def validate_state(client, req, kind, identifier, deadline):
    action,p = req['action'], req['parameters']
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0: raise Blocked('timeout')
        try:
            data = client.call(kind.split()+['show',identifier], timeout=remaining)
        except Blocked as error:
            if action.endswith('-delete') and error.code == 'not-found': return
            raise
        if action.endswith('-delete'):
            ready = False
        else:
            if not isinstance(data,dict) or data.get('id',data.get('ID')) != identifier:
                raise Blocked('invalid-resource-response')
            # All mutation targets except rule (whose parent is checked) must remain tenant-owned.
            if kind != 'security group rule':
                owner = data.get('project_id',data.get('tenant_id',data.get('os-vol-tenant-attr:tenant_id')))
                if owner != client.ctx['project_id']: raise Blocked('resource-wrong-project')
            status = str(data.get('status','')).upper()
            if status in ('ERROR','ERROR_DELETING','ERROR_EXTENDING','ERROR_RESTORING'):
                raise Blocked('terminal-resource-error')
            expected={'server-create':'ACTIVE','server-start':'ACTIVE','server-stop':'SHUTOFF','server-reboot':'ACTIVE','server-resize':'VERIFY_RESIZE','server-resize-confirm':'ACTIVE','server-resize-revert':'ACTIVE','volume-create':'AVAILABLE','volume-from-snapshot':'AVAILABLE','volume-snapshot':'AVAILABLE','volume-extend':'AVAILABLE'}
            ready = status == expected[action] if action in expected else True
            if action == 'volume-extend': ready = ready and data.get('size') == p['size_gib']
            if action in ('volume-attach','volume-detach'):
                attached = any(x.get('server_id') == p['server_id'] for x in data.get('attachments',[]) if isinstance(x,dict))
                ready = attached if action == 'volume-attach' else not attached and status == 'AVAILABLE'
            if action == 'router-set-external': ready = isinstance(data.get('external_gateway_info'),dict) and data['external_gateway_info'].get('network_id') == p['external_network_id']
            if action == 'router-add-subnet':
                ports=client.call(['port','list','--device-id',p['router_id'],'--fixed-ip','subnet='+p['subnet_id']], columns=['ID'],timeout=max(0.01,deadline-time.monotonic()))
                ready=isinstance(ports,list) and bool(ports)
            if action == 'floating-ip-associate': ready = data.get('port_id') == p['port_id'] and data.get('fixed_ip_address') == p['fixed_ip']
            if action == 'floating-ip-disassociate': ready = 'port_id' in data and data['port_id'] in (None,'')
            if action == 'volume-snapshot': ready = ready and data.get('volume_id') == p['volume_id']
            if action == 'security-rule-create': ready = data.get('security_group_id') == p['security_group_id'] and data.get('remote_ip_prefix') == p['remote_cidr'] and data.get('protocol') == p['protocol'] and data.get('port_range_min') == p['port_min'] and data.get('port_range_max') == p['port_max']
        if ready: return
        time.sleep(min(0.2,max(0,deadline-time.monotonic())))

def approved(files, value, approval):
    keys={'schema','context','request','user_data_sha256','checks','sha256','work_root','created_at','expires_at'}
    if not isinstance(value,dict) or set(value)!=keys or value['schema']!='openstack-plan/v1': raise Blocked('invalid-plan')
    body={k:v for k,v in value.items() if k!='sha256'}
    if value['sha256'] != digest(body): raise Blocked('plan-digest-mismatch')
    if approval != value['sha256']: raise Blocked('approval-mismatch')
    if value['work_root'] != str(files.root): raise Blocked('plan-work-root-mismatch')
    start,end=value['created_at'],value['expires_at']
    if type(start) not in (int,float) or type(end) not in (int,float) or not 0 < end-start <= 1800 or not start <= time.time() < end: raise Blocked('plan-expired')
    context(value['context']); request(value['request'])
    if user_data(files,value['request']) != value['user_data_sha256']: raise Blocked('user-data-digest-mismatch')
    return value

def execute(files, plan, evidence, previous=None):
    ctx,req = plan['context'],plan['request']
    domain,cmd,created,kind,identifier=build(req)
    if 'user_data_file' in req['parameters']:
        cmd[cmd.index('--user-data') + 1] = str(files.path(req['parameters']['user_data_file']))
    client=Client(ctx)
    result=record(ctx,domain,req['action'],'mutation',plan['sha256'])
    result['checks']=preflight(ctx,req,client)
    if result['checks'] != plan['checks']: raise Blocked('preflight-state-changed-new-plan-required')
    if identifier: result['resource_ids'].append(identifier)
    files.write(evidence,result)  # refuse an existing artifact BEFORE any mutation
    receipt='.openstack-ops-'+plan['sha256']+'.receipt.json'
    try:
        files.write(receipt,{'schema':'openstack-receipt/v1','plan_hash':plan['sha256'],'status':'attempted','evidence':str(files.path(evidence))})
    except Blocked as error:
        result.update(status='blocked',next_action='inspect-existing-evidence-no-retry')
        result['findings'].append({'code':'replay-refused' if error.code=='output-already-exists' else error.code})
        files.write(evidence,result,replace=True)
        return result
    try:
        output=client.call(cmd,formatted=bool(created) or req['action']=='volume-attach')
        if created:
            if not isinstance(output,dict): raise Blocked('invalid-create-response-id-unknown')
            identifier=uid(output.get('id',output.get('ID')))
            if identifier not in result['resource_ids']: result['resource_ids'].append(identifier)
            result['status']='validating'
            files.write(evidence,result,replace=True)  # durable ID before any show/wait
        validate_state(client,req,kind,identifier,time.monotonic()+ctx['timeout_seconds'])
        result['checks'].append({'check':'postcondition','status':'passed'})
        result.update(status='complete',next_action='review-evidence')
    except Blocked as error:
        result['findings'].append({'code':error.code})
        result.update(status='partial',next_action='inspect-recorded-ids-and-reconcile-no-automatic-retry')
    files.write(evidence,result,replace=True)
    return result

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-root', default=os.getcwd(), help='approved directory; all runtime files must remain inside it')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('inspect')
    p.add_argument('--context', required=True)
    p.add_argument('--domain', choices=DOMAINS, required=True)
    p.add_argument('--resource-id')
    p.add_argument('--previous-evidence')
    p.add_argument('--evidence', required=True)
    p = sub.add_parser('prepare', help='read live scope; produce approval plan without mutation')
    p.add_argument('--context', required=True)
    p.add_argument('--request', required=True)
    p.add_argument('--plan', required=True)
    p = sub.add_parser('execute', help='execute one exact approved plan; replay is refused')
    p.add_argument('--plan', required=True)
    p.add_argument('--approve', required=True)
    p.add_argument('--evidence', required=True)
    sub.add_parser('actions', help='list supported single-request actions')
    args = parser.parse_args(argv)
    try:
        if args.command == 'actions':
            print(json.dumps({'actions':list(FIELDS),'schema':'openstack-actions/v1'}))
            return 0
        files = Files(args.work_root)
        if args.command == 'execute':
            plan=approved(files,files.read(args.plan),args.approve)
            result=execute(files,plan,args.evidence)
            print(json.dumps(result,sort_keys=True))
            return 0 if result['status']=='complete' else 2
        ctx = context(files.read(args.context))
        client = Client(ctx)
        if args.command == 'inspect':
            result = inspect(ctx,args.domain,client,args.resource_id)
            if args.previous_evidence:
                previous=files.read(args.previous_evidence)
                if not isinstance(previous,dict) or any(previous.get(k)!=ctx[k] for k in ('case_id','project_id','region')) or previous.get('schema')!='openstack-operation-record/v1': raise Blocked('previous-evidence-context-mismatch')
                for identifier in previous.get('resource_ids',[]):
                    uid(identifier)
                    if identifier not in result['resource_ids']: result['resource_ids'].append(identifier)
            files.write(args.evidence,result)
            print(json.dumps(result, sort_keys=True))
            return 0
        if args.command == 'prepare':
            plan = prepare(files,ctx,files.read(args.request),client)
            files.write(args.plan,plan)
            domain = build(plan['request'])[0]
            result = record(ctx,domain,plan['request']['action'],'read-only',plan['sha256'])
            result.update(status='prepared',checks=plan['checks'],next_action='review-plan-then-approve-exact-sha256')
            print(json.dumps(result,sort_keys=True))
            return 0
    except Blocked as error:
        print(json.dumps({'schema':'openstack-operation-record/v1','status':'blocked','code':error.code,'next_action':'review-input-and-evidence'}))
        return 2

if __name__ == '__main__':
    sys.exit(main())
