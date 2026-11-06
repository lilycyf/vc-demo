"""One-command complete-scope T47D study; phases are resumable, not substitutes."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path

RUN=Path('experiments/t47d_lineage_resistance_full_v2')
AUTHOR=Path('/workspace/_external/TraCSED')
AUTHOR_SHA='dc5a750ef6fc6adf50e362ba5c2d38bee6083289'


def run(command,env=None):
    subprocess.run(command,env=env or os.environ,check=True)


def budget_check():
    file=Path('/workspace/t47d_budget_guard_state.json')
    if file.exists():
        deadline=datetime.fromisoformat(json.loads(file.read_text())['deadline_utc'])
        if datetime.now(timezone.utc)>=deadline:raise SystemExit('Approved initial allocation deadline reached; no automatic spending extension')


def author_source():
    if not AUTHOR.exists():
        AUTHOR.parent.mkdir(parents=True,exist_ok=True)
        run(['git','clone','https://github.com/Genentech/TraCSED',str(AUTHOR)])
        run(['git','-C',str(AUTHOR),'checkout',AUTHOR_SHA])
    actual=subprocess.check_output(['git','-C',str(AUTHOR),'rev-parse','HEAD'],text=True).strip()
    if actual!=AUTHOR_SHA:raise ValueError('Author source revision differs from registered reconstruction; do not silently replace it')


def reference():
    if not Path('data/t47d_lineage/reference_interchange/interchange.json').exists():
        run([sys.executable,'scripts/t47d/full_prepare.py','--run-dir',str(RUN)])
    run(['/workspace/t47d_r/bin/Rscript','scripts/t47d/full_reference.R','data/t47d_lineage/reference_interchange',str(RUN/'reference')])
    dest=RUN/'reference';data={}
    for trt in ('giredestrant','palbociclib','combination'):
        source=dest/(trt+'_reference.json')
        if not source.exists():raise ValueError('Missing real reference trajectory export '+str(source))
        for bar,records in json.loads(source.read_text()).items():data[trt+'::'+bar]=records
    if not data:raise ValueError('No source-valid barcode trajectory survived preprocessing; not a completed reference')
    (dest/'reference_data.json').write_text(json.dumps(data))
    env=dict(os.environ)
    root=Path('/workspace/t47d_tf_venv/lib/python3.12/site-packages/nvidia')
    env['LD_LIBRARY_PATH']=':'.join(str(p) for p in root.glob('*/lib'))+':'+env.get('LD_LIBRARY_PATH','')
    env['TF_FORCE_GPU_ALLOW_GROWTH']='true';env['TF_NUM_INTRAOP_THREADS']='4';env['TF_NUM_INTEROP_THREADS']='2'
    run(['/workspace/t47d_tf_venv/bin/python','scripts/t47d/full_tf_worker.py','reference',str(dest)],env)


def prepare():
    run([sys.executable,'scripts/t47d/acquire.py'])
    gmt=Path('data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt')
    if not gmt.exists():
        gmt.parent.mkdir(parents=True,exist_ok=True)
        run(['curl','--fail','--location','--retry','3','--output',str(gmt),
            'https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/h.all.v2025.1.Hs.symbols.gmt'])
    if not Path('data/t47d_lineage/prepared/dataset_manifest.json').exists():
        run([sys.executable,'scripts/t47d/prepare.py','--run-dir',str(RUN)])
    run([sys.executable,'scripts/t47d/full_prepare.py','--run-dir',str(RUN)])


def main():
    global RUN
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('all','prepare','search','reference','evaluate','biology','report'),default='all')
    parser.add_argument('--run-dir',type=Path,default=RUN)
    args=parser.parse_args();RUN=args.run_dir;budget_check();RUN.mkdir(parents=True,exist_ok=True)
    author_source()
    versions=subprocess.check_output([sys.executable,'-m','pip','freeze'],text=True)
    (RUN/'requirements_full.lock.txt').write_text(versions)
    tfversions=subprocess.check_output(['/workspace/t47d_tf_venv/bin/python','-m','pip','freeze'],text=True)
    (RUN/'requirements_tensorflow.lock.txt').write_text(tfversions)
    source={str(p):hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for base in ('src/vc_demo/t47d_full','scripts/t47d') for p in Path(base).glob('*.py')}
    (RUN/'implementation_snapshot.json').write_text(json.dumps({'source_sha256':source,'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'created_utc':datetime.now(timezone.utc).isoformat(),'scope':'original complete T47D document, not pilot subset',
        'prior_test_exposure':True,'approved_initial_limits':{'hours':24,'usd':20,'no_automatic_extension':True}},indent=2))
    phases=('prepare','search','reference','evaluate','biology','report') if args.phase=='all' else (args.phase,)
    for phase in phases:
        budget_check()
        if phase=='prepare':prepare()
        elif phase=='search':run([sys.executable,'-m','vc_demo.t47d_full.study','--run-dir',str(RUN)])
        elif phase=='reference':reference()
        elif phase=='evaluate':run([sys.executable,'-m','vc_demo.t47d_full.evaluation','--run-dir',str(RUN)])
        elif phase=='biology':run([sys.executable,'-m','vc_demo.t47d_full.biology','--run-dir',str(RUN)])
        else:run([sys.executable,'-m','vc_demo.t47d_full.report','--run-dir',str(RUN)])


if __name__=='__main__':main()
