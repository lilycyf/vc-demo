import copy
import numpy as np
import pandas as pd
import pytest
import torch
from vc_demo.t47d_full.models import FullView,FullCandidate,Network,secondary_labels
from vc_demo.t47d_full.study import manifest,required_choices


def synthetic():
    rng=np.random.default_rng(3)
    meta=pd.DataFrame([{'clone_id':'c'+str(c),'treatment':t,'label':float(c-1+(i==0)),
        'split':'development' if c<3 else 'test'} for c in range(4)
        for i,t in enumerate(('giredestrant','palbociclib','combination'))])
    return {'meta':meta,'expression':rng.normal(size=(12,3,128)).astype('float32'),
        'pathway':rng.normal(size=(12,3,50)).astype('float32'),'aux':rng.normal(size=(12,9)).astype('float32')}


def test_manifest_and_required_family_coverage():
    space=manifest();assert 80<=len(space)<=150
    assert len({str(sorted(c.items())) for c in space})==len(space)
    req=required_choices(space)
    assert {'scvi','distance','pseudotime','cellrank','pseudobulk','pathway'}<={c['representation'] for c in req}
    assert {'tracsed','hazard','cross_attention','bilinear','moe'}<={c['model'] for c in req}
    assert {'positive_selected','mono_resistant_combo_sensitive'}<={c['head'] for c in req}


def test_monotherapy_training_does_not_read_combination_class_label():
    b=synthetic();idx=np.flatnonzero(b['meta'].treatment.ne('combination'))
    labels,mask=secondary_labels(b,idx)
    assert np.all(mask[:,1]==0)
    changed=copy.deepcopy(b);changed['meta'].loc[changed['meta'].treatment.eq('combination'),'label']=999
    other,othermask=secondary_labels(changed,idx)
    np.testing.assert_array_equal(labels,other);np.testing.assert_array_equal(mask,othermask)


def test_no_barcode_inputs_really_remove_clone_information():
    b=synthetic();idx=np.arange(9)
    v=FullView({'representation':'pathway','no_barcode_inputs':True}).fit(b,idx,3)
    _,x,_=v.transform(b,np.arange(12))
    for treatment in b['meta'].treatment.unique():
        rows=x[b['meta'].treatment.eq(treatment)]
        np.testing.assert_allclose(rows,np.repeat(rows[:1],len(rows),axis=0))


def test_day1_cutoff_does_not_use_day4_expression():
    b=synthetic();other=copy.deepcopy(b);other['expression'][:,2]=1e9
    c={'representation':'pca','input_cutoff_day':1}
    a=FullView(c).fit(b,np.arange(9),3).transform(b,np.arange(12))[1]
    z=FullView(c).fit(other,np.arange(9),3).transform(other,np.arange(12))[1]
    np.testing.assert_allclose(a,z,atol=1e-5)


@pytest.mark.parametrize('family',['gru','temporal_transformer','cross_attention','bilinear','gated_pathway','moe'])
def test_real_neural_branches_forward_backward(family):
    net=Network(50,158,family,32,{})
    s=torch.randn(4,3,50);x=torch.randn(4,158);cross=torch.randn(4,3,3,50)
    pred,classes,path=net(s,x,cross)
    assert pred.shape==(4,) and classes.shape==(4,2) and path.shape==(4,50)
    loss=pred.square().mean()+classes.square().mean()+path.square().mean();loss.backward()
    assert any(p.grad is not None and torch.isfinite(p.grad).all() for p in net.parameters())


def test_probability_heads_do_not_replace_regression_reward_contract():
    b=synthetic();m=FullCandidate({'model':'ridge','representation':'pathway'}).fit(b,np.arange(9),3)
    assert m.predict(b,np.arange(9,12)).shape==(3,)


def test_withheld_combination_state_does_not_enter_monotherapy_training():
    b=synthetic();other=copy.deepcopy(b)
    idx=np.flatnonzero(b['meta'].treatment.ne('combination'))
    other['pathway'][b['meta'].treatment.eq('combination')]=1e6
    c={'representation':'pathway','heldout_treatment':'combination'}
    v=FullView(c).fit(b,idx,3).transform(b,idx)
    w=FullView(c).fit(other,idx,3).transform(other,idx)
    for a,z in zip(v,w):np.testing.assert_allclose(a,z)


def test_no_order_ablation_also_removes_abundance_time_order():
    b=synthetic();other=copy.deepcopy(b)
    other['pathway']=other['pathway'][:,::-1].copy()
    other['aux'][:,:3]=other['aux'][:,:3][:,::-1]
    other['aux'][:,3:6]=other['aux'][:,3:6][:,::-1]
    c={'representation':'pathway','no_temporal_order':True}
    a=FullView(c).fit(b,np.arange(9),3).transform(b,np.arange(12))[1]
    z=FullView(c).fit(other,np.arange(9),3).transform(other,np.arange(12))[1]
    np.testing.assert_allclose(a,z,atol=1e-5)


def test_no_dense_gated_branch_is_actually_absent():
    c={'no_dense_parent':True};net=Network(50,158,'gated_pathway',32,c)
    assert net.dense is None
    s=torch.randn(4,3,50);cross=torch.randn(4,3,3,50)
    net.eval()
    a=net(s,torch.randn(4,158),cross)[0]
    z=net(s,torch.randn(4,158)*1e6,cross)[0]
    torch.testing.assert_close(a,z)
