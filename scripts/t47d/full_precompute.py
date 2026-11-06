"""Parallelize independent fold artifacts for an already-selected rollout."""
import argparse
import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np

from vc_demo.t47d_lineage.data import load_bundle
from vc_demo.t47d_full.features import build_fold

DATA=None


def initialize():
    global DATA
    dest=Path('/workspace/t47d_prefetch_contracts')/str(os.getpid());dest.mkdir(parents=True,exist_ok=True)
    DATA=load_bundle(Path('data/t47d_lineage/prepared'),Path('data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt'),dest)


def worker(index):
    f=DATA['splits']['folds'][index]
    idx=np.flatnonzero(DATA['meta'].clone_id.isin(f['train_clones']))
    _,metadata,path=build_fold(DATA,idx,f['seed'],modules=('cellrank',))
    return {'fold_index':index,'path':str(path),'cellrank':metadata['stages']['cellrank']}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--start-fold',type=int,default=3);parser.add_argument('--end-fold',type=int,default=15);parser.add_argument('--workers',type=int,default=3)
    args=parser.parse_args()
    with ProcessPoolExecutor(max_workers=args.workers,mp_context=mp.get_context('spawn'),initializer=initialize) as pool:
        for result in pool.map(worker,range(args.start_fold,args.end_fold)):print(result,flush=True)
