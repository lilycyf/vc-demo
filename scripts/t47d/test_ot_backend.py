"""Numerical equivalence check before accelerating the identical POT solver."""
import json,time
from pathlib import Path
import numpy as np
import ot,torch
from scipy.spatial.distance import cdist

def main():
    rng=np.random.default_rng(3)
    x=rng.normal(size=(1000,20));y=rng.normal(size=(1400,20))+1
    cost=cdist(x,y,metric='sqeuclidean');cost/=np.median(cost)
    a,b=np.full(len(x),1/len(x)),np.full(len(y),1/len(y))
    start=time.monotonic()
    cpu=ot.sinkhorn(a,b,cost,.1,method='sinkhorn_stabilized',numItermax=1000,stopThr=1e-6)
    cpu_seconds=time.monotonic()-start
    start=time.monotonic()
    gpu=ot.sinkhorn(torch.as_tensor(a,device='cuda'),torch.as_tensor(b,device='cuda'),
        torch.as_tensor(cost,device='cuda'),.1,method='sinkhorn_stabilized',numItermax=1000,stopThr=1e-6).cpu().numpy()
    gpu_seconds=time.monotonic()-start
    record={'algorithm':'POT stabilized Sinkhorn, same float64 cost/masses/reg=.1/1000 iterations/tolerance1e-6',
        'max_absolute_transport_difference':float(np.max(np.abs(cpu-gpu))),
        'transport_L1_difference':float(np.abs(cpu-gpu).sum()),'cpu_seconds':cpu_seconds,'gpu_seconds':gpu_seconds,
        'shape':list(cost.shape),'seed':3,'data':'synthetic numerical implementation test, not biological result'}
    assert np.allclose(cpu,gpu,atol=1e-10,rtol=1e-5)
    Path('experiments/t47d_lineage_resistance_full_v2/ot_backend_equivalence.json').write_text(json.dumps(record,indent=2))
    print(json.dumps(record),flush=True)


if __name__=='__main__':main()
