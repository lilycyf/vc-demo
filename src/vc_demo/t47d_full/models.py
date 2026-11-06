"""Train-fold representations and real prospective candidate models."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy import sparse
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.preprocessing import StandardScaler
from torch import nn

from vc_demo.t47d_lineage.data import TREATMENTS
from vc_demo.t47d_full.features import build_fold


def sequence_counts(bundle):
    if "pseudobulk" in bundle:
        return bundle["pseudobulk"]
    root = Path("data/t47d_lineage/prepared")
    table = pd.read_csv(root/"clone_expression_rows.csv")
    matrix = sparse.load_npz(root/"clone_pseudobulk_counts.npz").astype(float)
    matrix = sparse.diags(1e4/np.maximum(np.asarray(matrix.sum(1)).ravel(),1)).dot(matrix).tocsr()
    matrix.data = np.log1p(matrix.data)
    lookup = {(r.clone_id,r.treatment,int(r.time_day)):i for i,r in table.iterrows()}
    out = np.zeros_like(bundle["expression"])
    for i,r in bundle["meta"].iterrows():
        for j,d in enumerate((0,1,4)):
            k=(r.clone_id,"baseline" if d==0 else r.treatment,d)
            if k in lookup:
                out[i,j] = matrix[lookup[k]].toarray()[0]
    bundle["pseudobulk"] = out
    return out


class FullView:
    def __init__(self, config):
        self.c = config

    def fit(self,bundle,idx,seed):
        c=self.c
        rep=c.get("representation","pathway")
        cutoff=0 if c.get('baseline_only') else c.get('input_cutoff_day',4)
        self.time_steps=sum(d<=cutoff for d in (0,1,4))
        if rep in {"scvi","pseudotime","distance","cellrank"}:
            allowed=[t for t in TREATMENTS if t!=c['heldout_treatment']] if c.get('heldout_treatment') else None
            arrays,meta,dest=build_fold(bundle,idx,seed,modules=(rep,),max_fit_day=cutoff,fit_treatments=allowed,
                no_time_direction=rep=='cellrank' and bool(c.get('no_temporal_order')))
            self.source=arrays[rep]
            self.artifact={"path":str(dest),"method":meta["stages"][rep],"train_only":True}
        elif rep in {"pseudobulk","pca","expression","both","matched_no_artifact"}:
            expr=sequence_counts(bundle) if rep=="pseudobulk" else bundle["expression"]
            fit=expr[idx,:self.time_steps]
            self.genes=np.argsort(fit.reshape(-1,fit.shape[-1]).var(0))[-c.get("genes",128):]
            raw=expr[:,:,self.genes]
            if rep=="both": raw=np.concatenate([raw,bundle["pathway"]],axis=-1)
            if rep=='matched_no_artifact':
                self.random_projection=np.random.default_rng(seed).normal(size=(raw.shape[-1],c.get('matched_width',50)))/np.sqrt(raw.shape[-1])
                raw=raw@self.random_projection
            if rep=="pca":
                self.pca=PCA(n_components=min(16,len(idx)-1),random_state=seed).fit(raw[idx,:self.time_steps].reshape(-1,raw.shape[-1]))
                raw=self.pca.transform(raw.reshape(-1,raw.shape[-1])).reshape(len(raw),3,-1)
            self.source=raw
            self.artifact={"method":rep,"train_only_gene_selection":True}
        else:
            self.source=bundle.get("ablation_pathway",bundle["pathway"])
            self.artifact={"method":"public Hallmark mean log expression"}
        if c.get('no_barcode_inputs'):
            pooled=np.zeros_like(self.source)
            for treatment in TREATMENTS:
                training=[i for i in idx if bundle['meta'].iloc[i].treatment==treatment]
                query=bundle['meta'].treatment.eq(treatment).to_numpy()
                pooled[query]=self.source[training].mean(0)
            self.source=pooled
            self.artifact['barcode_input_removal']='training-clone condition means only; true barcode remains solely for labels/grouping'
        source=self.source
        fit=source[idx,:self.time_steps]
        self.scaler=StandardScaler().fit(fit.reshape(-1,source.shape[-1]))
        self.aux_scaler=StandardScaler().fit(bundle["aux"][idx,:6])
        return self

    def transform(self,bundle,idx):
        s=self.scaler.transform(self.source[idx].reshape(-1,self.source.shape[-1])).reshape(len(idx),3,-1)
        if self.c.get("baseline_only"): s=np.repeat(s[:,:1],3,axis=1)
        if self.time_steps<3:s[:,self.time_steps:]=s[:,self.time_steps-1:self.time_steps]
        if self.c.get("no_temporal_order"): s=np.repeat(s[:,:self.time_steps].mean(1,keepdims=True),3,axis=1)
        aux=self.aux_scaler.transform(bundle["aux"][idx,:6])
        if self.c.get("baseline_only"): aux[:,[1,2,4,5]]=0
        for j in range(self.time_steps,3):
            aux[:,j]=0;aux[:,j+3]=0
        if self.c.get("no_clone_abundance"): aux[:]=0
        if self.c.get('no_barcode_inputs'):aux[:]=0
        if self.c.get('no_temporal_order') and self.time_steps>1:
            aux[:,:self.time_steps]=aux[:,:self.time_steps].mean(1,keepdims=True)
            aux[:,3:3+self.time_steps]=aux[:,3:3+self.time_steps].mean(1,keepdims=True)
        drug=np.array([[1,0] if t==TREATMENTS[0] else [0,1] if t==TREATMENTS[1] else [1,1]
                       for t in bundle["meta"].iloc[idx].treatment],dtype=np.float32)
        if self.c.get("no_treatment_interaction"): drug[:]=0
        seq=s.astype(np.float32)
        x=np.concatenate([seq.reshape(len(idx),-1),aux,drug],axis=1).astype(np.float32)
        cross=[]
        lookup={(r.clone_id,r.treatment):i for i,r in bundle["meta"].iterrows()}
        for i in idx:
            row=bundle["meta"].iloc[i]
            rows=[lookup[(row.clone_id,t)] for t in TREATMENTS]
            values=self.source[rows]
            if self.c.get("baseline_only"):values=np.repeat(values[:,:1],3,axis=1)
            if self.time_steps<3:values[:,self.time_steps:]=values[:,self.time_steps-1:self.time_steps]
            if self.c.get("no_temporal_order"):values=np.repeat(values[:,:self.time_steps].mean(1,keepdims=True),3,axis=1)
            if self.c.get('heldout_treatment'):
                values=values.copy();values[list(TREATMENTS).index(self.c['heldout_treatment'])]=0
            values=self.scaler.transform(values.reshape(-1,values.shape[-1])).reshape(3,3,-1)
            cross.append(values)
        return seq,x,np.asarray(cross,dtype=np.float32)


class Network(nn.Module):
    def __init__(self,width,xwidth,family,hidden,config):
        super().__init__()
        self.family,self.config=family,config
        self.project=nn.Linear(width,hidden)
        self.position=nn.Parameter(torch.zeros(1,3,hidden))
        self.drop=nn.Dropout(.15)
        self.dense=None if config.get('no_dense_parent') else nn.Sequential(nn.Linear(xwidth,hidden),nn.GELU(),nn.Linear(hidden,hidden))
        if family=="gru":self.temporal=nn.GRU(hidden,hidden,batch_first=True)
        elif family=="temporal_transformer":
            layer=nn.TransformerEncoderLayer(hidden,4,hidden*2,.15,batch_first=True,norm_first=True)
            self.temporal=nn.TransformerEncoder(layer,2,enable_nested_tensor=False)
        elif family=="cross_attention":self.attention=nn.MultiheadAttention(hidden,4,.1,batch_first=True)
        elif family=="bilinear":self.bilinear=nn.Bilinear(hidden,hidden,hidden)
        elif family=="moe":
            self.experts=nn.ModuleList([nn.Sequential(nn.Linear(hidden,hidden),nn.GELU(),nn.Linear(hidden,hidden)) for _ in range(3)])
            self.gate=nn.Sequential(nn.Linear(hidden,3),nn.Softmax(-1))
        elif family=="gated_pathway":self.gate=nn.Sequential(nn.Linear(hidden*2,hidden),nn.Sigmoid())
        self.head=nn.Linear(hidden,1)
        self.classifier=nn.Linear(hidden,2)
        self.pathway_reconstruction=nn.Linear(hidden,50)

    def forward(self,s,x,cross):
        tokens=self.project(s)+self.position
        z=tokens.mean(1)
        if self.family=="gru":z=self.temporal(tokens)[0][:,-1]
        elif self.family=="temporal_transformer":z=self.temporal(tokens).mean(1)
        elif self.family in {"cross_attention","bilinear"}:
            other=self.project(cross).mean(2)
            if self.config.get("no_treatment_interaction"):other=tokens[:,:1].repeat(1,3,1)
            if self.family=="cross_attention":
                mask=None
                if self.config.get('heldout_treatment'):
                    mask=torch.tensor([t==self.config['heldout_treatment'] for t in TREATMENTS],device=tokens.device).unsqueeze(0).expand(len(tokens),-1)
                z=self.attention(tokens,other,other,key_padding_mask=mask,need_weights=False)[0].mean(1)
            else:z=self.bilinear(other[:,0],other[:,1])+(0 if self.config.get('heldout_treatment')=='combination' else other[:,2])
        elif self.family=="moe":
            expert_in=[tokens[:,0],tokens[:,1]-tokens[:,0],tokens[:,2]]
            z=(torch.stack([m(v) for m,v in zip(self.experts,expert_in)],1)*self.gate(z).unsqueeze(-1)).sum(1)
        elif self.family=="gated_pathway":
            base=torch.zeros_like(z) if self.dense is None else self.dense(x)
            z=z*self.gate(torch.cat([base,z],-1))
        if not self.config.get("no_dense_parent"):z=z+self.dense(x)
        z=self.drop(z)
        return self.head(z).squeeze(-1),self.classifier(z),self.pathway_reconstruction(z)


def secondary_labels(bundle,idx):
    meta=bundle.get('truth_meta',bundle['meta']).iloc[idx]
    values=meta.pivot(index="clone_id",columns="treatment",values="label")
    available=all(t in values for t in TREATMENTS)
    sensitive=((values["giredestrant"]>0)|(values["palbociclib"]>0))&(values["combination"]<0) if available else pd.Series(False,index=values.index)
    labels=np.column_stack([(meta.label.to_numpy()>0).astype(float),meta.clone_id.map(sensitive).astype(float).to_numpy()])
    mask=np.ones_like(labels)
    if not available:mask[:,1]=0
    return labels,mask


class FullCandidate:
    def __init__(self,config):
        self.config=copy.deepcopy(config)

    def fit(self,bundle,idx,seed=3):
        c=self.config
        self.view=FullView(c).fit(bundle,idx,seed)
        s,x,cross=self.view.transform(bundle,idx)
        y=bundle["meta"].iloc[idx].label.to_numpy(dtype=float)
        self.mean=float(y.mean());self.std=max(float(y.std()),.1)
        t=(y-self.mean)/self.std
        family=c["model"]
        if family=="additive_null":
            mono=bundle['meta'].iloc[idx].treatment.ne('combination').to_numpy()
            self.additive=Ridge(alpha=10).fit(x[mono],t[mono])
            self.lookup={(r.clone_id,r.treatment):i for i,r in bundle["meta"].iterrows()}
        elif family in {"ridge","early_elastic","pls","frequency","xgboost"}:
            if family=="frequency":x=x[:,-8:]
            if family in {"ridge","frequency"}:self.estimator=Ridge(alpha=c.get("alpha",10)).fit(x,t)
            elif family=="early_elastic":self.estimator=ElasticNet(alpha=.01,l1_ratio=.5,max_iter=10000).fit(x,t)
            elif family=="pls":self.estimator=PLSRegression(n_components=min(c.get("components",3),len(idx)-2),scale=False).fit(x,t)
            else:
                from xgboost import XGBRegressor
                self.estimator=XGBRegressor(n_estimators=160,max_depth=2,learning_rate=.035,reg_lambda=10,
                    subsample=.9,colsample_bytree=.8,n_jobs=2,random_state=seed).fit(x,t)
        elif family=="hazard":
            from lifelines import LogNormalAFTFitter
            self.hazard_pca=PCA(n_components=min(5,len(idx)-2),random_state=seed).fit(x)
            frame=pd.DataFrame(self.hazard_pca.transform(x),columns=["z"+str(i) for i in range(self.hazard_pca.n_components_)])
            counts=pd.read_csv("data/t47d_lineage/prepared/clone_condition_counts.csv")
            n=counts.set_index(["clone_id","treatment","time_day"]).cell_count.to_dict()
            lower=[];upper=[]
            event_days=[d for d in (1,4,8,26) if d<=c.get('hazard_max_fit_day',26)]
            for r in bundle["meta"].iloc[idx].itertuples():
                seen=[n.get((r.clone_id,r.treatment,d),0)>=3 for d in event_days]
                start=next((j for j in range(len(event_days)) if not any(seen[j:])),None)
                lower.append(float(event_days[-1]) if start is None else float(([0]+event_days)[start]))
                upper.append(np.inf if start is None else float(event_days[start]))
            frame["lower"]=lower;frame["upper"]=upper
            self.hazard=LogNormalAFTFitter(penalizer=1.).fit_interval_censoring(frame,"lower","upper")
            survival=self.hazard.predict_survival_function(frame,times=[26]).to_numpy().ravel()
            self.estimator=Ridge(alpha=10).fit(np.column_stack([x,survival]),t)
            self.hazard_definition="persistent sampled-count non-detection (<3); interval/right-censored, not biological extinction"
        elif family=="tracsed":
            self.tf_dir=Path(tempfile.mkdtemp(prefix="tracsed_fit_",dir="/workspace"))
            np.savez(self.tf_dir/"train.npz",s=s,y=t)
            self._tf("fit")
        else:
            torch.manual_seed(seed);np.random.seed(seed);torch.set_num_threads(2)
            self.device=torch.device("cuda")
            self.network=Network(s.shape[-1],x.shape[-1],family,c.get("hidden",32),c).to(self.device)
            self.base=None if c.get("no_dense_parent") else Ridge(alpha=10).fit(x,t)
            target=t if self.base is None else t-self.base.predict(x)
            sx,xx,cx=[torch.tensor(v,device=self.device) for v in (s,x,cross)]
            ty=torch.tensor(target,dtype=torch.float32,device=self.device)
            labels,mask=secondary_labels(bundle,idx)
            classes=torch.tensor(labels,dtype=torch.float32,device=self.device)
            class_mask=torch.tensor(mask,dtype=torch.float32,device=self.device)
            positives=(classes*class_mask).sum(0).clamp(min=1);weight=(class_mask.sum(0)-positives).clamp(min=1)/positives
            optimizer=torch.optim.AdamW(self.network.parameters(),lr=.001,weight_decay=.02)
            path=torch.tensor(bundle.get('ablation_pathway',bundle['pathway'])[idx].mean(1),device=self.device)
            path=(path-path.mean(0))/path.std(0).clamp(min=.1)
            self.losses=[]
            self.network.train()
            for _ in range(c.get("epochs",80)):
                optimizer.zero_grad()
                pred,logits,reconstruction=self.network(sx,xx,cx)
                loss=nn.functional.huber_loss(pred,ty)
                kind=c.get("loss","huber")
                if kind in {"weighted_bce","focal"}:
                    bce=nn.functional.binary_cross_entropy_with_logits(logits,classes,pos_weight=weight,reduction="none")
                    if kind=="focal":bce=bce*(1-torch.exp(-bce)).pow(2)
                    active=class_mask.clone()
                    if c.get('head')=='positive_selected':active[:,1]=0
                    if c.get('head')=='mono_resistant_combo_sensitive':active[:,0]=0
                    loss=loss+.2*(bce*active).sum()/active.sum().clamp(min=1)
                if kind=="pairwise" or c.get("head")=="ranking":
                    dy=ty[:,None]-ty[None,:];dp=pred[:,None]-pred[None,:]
                    mask=dy.abs()>1e-6
                    if mask.any():loss=loss+.1*nn.functional.softplus(-dp[mask]*dy[mask].sign()).mean()
                if kind=="multitask" and not c.get('no_pathway_supervision'):loss=loss+.1*nn.functional.mse_loss(reconstruction,path)
                if not torch.isfinite(loss):raise ValueError("Nonfinite full candidate loss")
                loss.backward();nn.utils.clip_grad_norm_(self.network.parameters(),1);optimizer.step()
                self.losses.append(float(loss.detach().cpu()))
            self.network.eval()
        return self

    def _tf(self,action):
        env=dict(os.environ)
        lib=Path("/workspace/t47d_tf_venv/lib/python3.12/site-packages/nvidia")
        env["LD_LIBRARY_PATH"]=":".join(str(p) for p in lib.glob("*/lib"))+":"+env.get("LD_LIBRARY_PATH","")
        env["TF_FORCE_GPU_ALLOW_GROWTH"]="true"
        env["TF_CPP_MIN_LOG_LEVEL"]="2"
        subprocess.run(["/workspace/t47d_tf_venv/bin/python","scripts/t47d/full_tf_worker.py",action,str(self.tf_dir)],env=env,check=True,stdout=(self.tf_dir/(action+".log")).open("w"),stderr=subprocess.STDOUT)

    def predict(self,bundle,idx):
        s,x,cross=self.view.transform(bundle,idx)
        family=self.config["model"]
        if family=="additive_null":
            values=[]
            for i in idx:
                r=bundle["meta"].iloc[i]
                if r.treatment=="combination":
                    rows=[self.lookup[(r.clone_id,t)] for t in TREATMENTS[:2]]
                    _,xx,_=self.view.transform(bundle,rows)
                    values.append(float((self.additive.predict(xx)*self.std+self.mean).sum()))
                else:values.append(float(self.additive.predict(self.view.transform(bundle,[i])[1])[0]*self.std+self.mean))
            return np.array(values)
        if family=="frequency":x=x[:,-8:]
        if family=="hazard":
            frame=pd.DataFrame(self.hazard_pca.transform(x),columns=["z"+str(i) for i in range(self.hazard_pca.n_components_)])
            survival=self.hazard.predict_survival_function(frame,times=[26]).to_numpy().ravel()
            p=self.estimator.predict(np.column_stack([x,survival]))
        elif family=="tracsed":
            np.savez(self.tf_dir/"query.npz",s=s)
            self._tf("predict")
            p=np.load(self.tf_dir/"pred.npy")
        elif hasattr(self,"network"):
            with torch.no_grad():p=self.network(*[torch.tensor(v,device=self.device) for v in (s,x,cross)])[0].cpu().numpy()
            if self.base is not None:p=p+self.base.predict(x)
        else:p=np.asarray(self.estimator.predict(x)).ravel()
        return p*self.std+self.mean

    def close(self):
        if hasattr(self,"network"):
            self.network.to("cpu")
            self.device=torch.device('cpu')
            torch.cuda.empty_cache()


class ComposedCandidate:
    def __init__(self,config):
        self.config=config

    def fit(self,bundle,idx,seed=3):
        parent=self.config.get("parent_config")
        if parent and not self.config.get("no_dense_parent"):
            self.parent=ComposedCandidate(parent).fit(bundle,idx,seed)
            residual=dict(bundle)
            residual['truth_meta']=bundle.get('truth_meta',bundle['meta'])
            residual["meta"]=bundle["meta"].copy()
            residual["meta"].loc[idx,"label"]=bundle["meta"].iloc[idx].label.to_numpy()-self.parent.predict(bundle,idx)
            self.child=FullCandidate(self.config).fit(residual,idx,seed)
        else:self.child=FullCandidate(self.config).fit(bundle,idx,seed)
        return self

    def predict(self,bundle,idx):
        p=self.child.predict(bundle,idx)
        return self.parent.predict(bundle,idx)+.25*p if hasattr(self,"parent") else p

    def close(self):
        self.child.close()
        if hasattr(self,"parent"):self.parent.close()
