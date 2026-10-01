#!/usr/bin/env python3
"""Prepare a two-step PVC marker exercise. Never applies resources."""
import argparse,os,re
from pathlib import Path
import yaml
MARKER='chapter5-pvc-marker'
WRITE="printf '%s\\n' 'chapter5-pvc-marker' > /data/marker"
READ="test \"$(cat /data/marker)\" = 'chapter5-pvc-marker'"
def documents(storage_class,size,image):
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',storage_class):raise ValueError('explicit StorageClass name required')
    if not re.fullmatch(r'[1-9][0-9]*(?:Mi|Gi)',size):raise ValueError('size must be a positive Mi/Gi request')
    if not re.fullmatch(r'[^@\s]+@sha256:[0-9a-f]{64}',image):raise ValueError('digest-pinned shell-compatible image required')
    ns='chapter5-probe';name='chapter5-storage';meta={'name':name,'namespace':ns}
    pvc={'apiVersion':'v1','kind':'PersistentVolumeClaim','metadata':meta,'spec':{'accessModes':['ReadWriteOnce'],'storageClassName':storage_class,'resources':{'requests':{'storage':size}}}}
    def pod(suffix,command,readonly):
        return {'apiVersion':'v1','kind':'Pod','metadata':{'name':name+'-'+suffix,'namespace':ns},'spec':{'restartPolicy':'Never','securityContext':{'runAsNonRoot':True,'runAsUser':10001,'runAsGroup':10001,'fsGroup':10001},'containers':[{'name':'marker','image':image,'command':['sh','-eu','-c',command],'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}},'resources':{'requests':{'cpu':'10m','memory':'16Mi'},'limits':{'cpu':'100m','memory':'64Mi'}},'volumeMounts':[{'name':'data','mountPath':'/data','readOnly':readonly}]}],'volumes':[{'name':'data','persistentVolumeClaim':{'claimName':name}}]}}
    return [pvc,pod('writer',WRITE,False)],[pod('reader',READ,True)]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--storage-class',required=True);p.add_argument('--size',required=True);p.add_argument('--image',required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    try:
        writer,reader=documents(a.storage_class,a.size,a.image);out=a.output_dir.resolve();lab=Path(__file__).resolve().parents[1]
        if out==lab or out.is_relative_to(lab):raise ValueError('output must be outside installed lab')
        if out.exists() and any(out.iterdir()):raise ValueError('output directory must be empty')
        os.umask(0o077);out.mkdir(parents=True,exist_ok=True,mode=0o700)
        (out/'storage-writer.yaml').write_text(yaml.safe_dump_all(writer,sort_keys=False));(out/'storage-reader.yaml').write_text(yaml.safe_dump_all(reader,sort_keys=False))
        print('PREPARED ONLY: deliver writer, verify success, remove writer through its Git owner, then deliver reader. Keep the PVC until the approved retention decision.')
    except ValueError as e:p.error(str(e))
if __name__=='__main__':main()
