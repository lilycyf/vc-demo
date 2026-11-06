"""Execute all author reference models as each real R export becomes ready."""
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime,timezone
from pathlib import Path

DEST=Path('experiments/t47d_lineage_resistance_full_v2/reference')
TREATMENTS=('giredestrant','palbociclib','combination')


def main():
    DEST.mkdir(parents=True,exist_ok=True);previous=None
    while True:
        budget=Path('/workspace/t47d_budget_guard_state.json')
        if budget.exists() and datetime.now(timezone.utc)>=datetime.fromisoformat(json.loads(budget.read_text())['deadline_utc']):
            raise RuntimeError('Approved compute allocation reached; preserve partial reference and request additional authorization')
        data={};ready=[]
        for trt in TREATMENTS:
            file=DEST/(trt+'_reference.json')
            if not file.exists():continue
            try:content=json.loads(file.read_text())
            except json.JSONDecodeError:continue
            ready.append(trt)
            for bar,records in content.items():data[trt+'::'+bar]=records
        identity=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
        if data and identity!=previous:
            temporary=DEST/'reference_data.next.json';temporary.write_text(json.dumps(data));temporary.replace(DEST/'reference_data.json')
            env=dict(os.environ);root=Path('/workspace/t47d_tf_venv/lib/python3.12/site-packages/nvidia')
            env['LD_LIBRARY_PATH']=':'.join(str(p) for p in root.glob('*/lib'))+':'+env.get('LD_LIBRARY_PATH','')
            env['TF_FORCE_GPU_ALLOW_GROWTH']='true';env['TF_NUM_INTRAOP_THREADS']='4';env['TF_NUM_INTEROP_THREADS']='2'
            print(json.dumps({'reference_conditions_ready':ready,'barcode_trajectories':len(data)}),flush=True)
            subprocess.run(['/workspace/t47d_tf_venv/bin/python','scripts/t47d/full_tf_worker.py','reference',str(DEST)],check=True,env=env)
            previous=identity
        if len(ready)==3 and previous==identity and (DEST/'reference_preprocessing_provenance.json').exists():break
        time.sleep(20)


if __name__=='__main__':main()
