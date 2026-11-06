"""Real, train-fold-only single-cell representation artifacts."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import time
from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.spatial.distance import cdist
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsRegressor, NearestNeighbors

from vc_demo.t47d_lineage.data import dump

CACHE_ROOT = Path("data/t47d_lineage/full_fold_artifacts")
SOURCE = Path("data/t47d_lineage/prepared/qc_counts.h5ad")
ALGORITHM = "full-features-v2.1"


def _aggregate(bundle, obs, values, treatment=None):
    result = np.zeros((len(bundle["meta"]), 3, values.shape[1]), dtype=np.float32)
    groups = obs.groupby(["clone_id", "treatment", "time_day"], observed=True).indices
    for i, row in bundle["meta"].iterrows():
        if treatment is not None and row.treatment != treatment:
            continue
        for j, day in enumerate((0, 1, 4)):
            trt = "baseline" if day == 0 else row.treatment
            locations = groups.get((row.clone_id, trt, day))
            if locations is not None:
                result[i, j] = values[locations].mean(axis=0)
    return result


def cache_identity(bundle, train_idx, seed, max_fit_day=4,fit_treatments=None,no_time_direction=False):
    clones = sorted(bundle["meta"].iloc[train_idx].clone_id.unique())
    payload = {"algorithm": ALGORITHM, "train_clones": clones, "seed": int(seed),
               "max_fit_day": int(max_fit_day), "scvi_max_epochs": 50, "hvg": 2000,
               "source_size": SOURCE.stat().st_size}
    if fit_treatments is not None:payload['fit_treatments']=sorted(fit_treatments)
    if no_time_direction:payload['cellrank_ablation']='stationary_no_time_direction'
    key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:20]
    return CACHE_ROOT/key, payload


def build_fold(bundle, train_idx, seed, modules=("scvi", "pseudotime", "distance", "cellrank"), max_fit_day=4,fit_treatments=None,no_time_direction=False):
    dest, identity = cache_identity(bundle, train_idx, seed,max_fit_day,fit_treatments,no_time_direction)
    dest.mkdir(parents=True, exist_ok=True)
    metadata_path = dest/"manifest.json"
    array_path = dest/"features.npz"
    metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {**identity, "stages": {}}
    if any(metadata.get(k) != v for k,v in identity.items()):
        raise ValueError("Fold cache provenance mismatch")
    arrays = dict(np.load(array_path)) if array_path.exists() else {}
    if all(name in arrays for name in modules):
        return arrays, metadata, dest
    start = time.monotonic()
    import scanpy as sc
    raw = ad.read_h5ad(SOURCE)
    wanted = raw.obs.time_day.le(max_fit_day) & raw.obs.clone_id.isin(bundle["meta"].clone_id.unique())
    query = raw[wanted].copy()
    del raw
    query.obs["library_id"] = query.obs.library_id.astype("category").cat.remove_unused_categories()
    train_mask = query.obs.clone_id.isin(identity["train_clones"]).to_numpy()
    if fit_treatments is not None:
        train_mask &= (query.obs.treatment.isin(fit_treatments)|query.obs.time_day.eq(0)).to_numpy()
    train = query[train_mask].copy()
    train.obs["library_id"] = train.obs.library_id.cat.remove_unused_categories()
    expressed = np.asarray((train.X > 0).sum(axis=0)).ravel() >= 3
    train = train[:, expressed].copy()
    sc.pp.highly_variable_genes(train, flavor="seurat_v3", n_top_genes=min(2000, train.n_vars), span=.5)
    genes = train.var_names[train.var.highly_variable].tolist()
    query = query[:, genes].copy()
    train = query[train_mask].copy()
    train.obs["library_id"] = train.obs.library_id.cat.remove_unused_categories()
    metadata.update(train_cells=train.n_obs, query_cells=query.n_obs,
                    fit_cell_ids_sha256=hashlib.sha256("\n".join(train.obs_names).encode()).hexdigest(),
                    gene_order_sha256=hashlib.sha256("\n".join(genes).encode()).hexdigest(),
                    package_versions={p:importlib.metadata.version(p) for p in ("scanpy","scvi-tools","cellrank","pertpy","POT")})
    pd.Series(genes).to_csv(dest/"gene_order.csv", index=False, header=False)
    if "scvi" in modules and "scvi" not in arrays:
        import scvi
        unseen=~query.obs.library_id.isin(train.obs.library_id.unique())
        if unseen.any():
            if fit_treatments is None:
                raise ValueError('Unseen query batch: requires an explicitly registered reference-batch transfer protocol')
            reference_batch=str(train.obs.loc[train.obs.time_day.eq(0),'library_id'].mode().iloc[0])
            metadata['reference_batch_transfer']={'query_cells':int(unseen.sum()),'batch':reference_batch,
                'meaning':'No heldout-treatment cells fit the model. Unseen nuisance batch IDs mapped to a learned baseline category for fixed-encoder inference; original metadata unchanged on disk.',
                'query_optimization_steps':0}
            query.obs.loc[unseen,'library_id']=reference_batch
            query.obs['library_id']=query.obs.library_id.cat.set_categories(train.obs.library_id.cat.categories)
        scvi.settings.seed = int(seed)
        scvi.model.SCVI.setup_anndata(train, batch_key="library_id")
        model = scvi.model.SCVI(train, n_hidden=128, n_latent=16, n_layers=2,
                               gene_likelihood="nb", dropout_rate=.1)
        fit_start = time.monotonic()
        model.train(max_epochs=50, batch_size=256, train_size=.9, accelerator="gpu", devices=1,
                    early_stopping=True, early_stopping_patience=10,
                    enable_progress_bar=False, enable_model_summary=False, logger=False,
                    enable_checkpointing=False, check_val_every_n_epoch=1)
        latent = model.get_latent_representation(adata=query, batch_size=512)
        if not np.isfinite(latent).all():
            raise ValueError("Non-finite scVI latent")
        model.save(dest/"scvi_model", overwrite=True, save_anndata=False)
        arrays["scvi"] = _aggregate(bundle, query.obs, latent)
        metadata["stages"]["scvi"] = {"seconds":time.monotonic()-fit_start,
            "epochs":int(model.trainer.current_epoch), "latent_shape":list(latent.shape),
            "train_only":True,"query_adaptation_steps":0,"device":"gpu"}
        np.savez_compressed(array_path, **arrays)
        dump(metadata_path, metadata)
        del model
    q_counts = query.X.astype(np.float32)
    library = np.asarray(q_counts.sum(axis=1)).ravel()
    normalized = sparse.diags(1e4/np.maximum(library,1)).dot(q_counts).tocsr()
    normalized.data = np.log1p(normalized.data)
    dense = normalized.toarray()
    pca = PCA(n_components=20, svd_solver="randomized", random_state=int(seed)).fit(dense[train_mask])
    z = pca.transform(dense).astype(np.float32)
    z /= np.maximum(z[train_mask].std(axis=0), .01)
    arrays["cell_pca"] = _aggregate(bundle, query.obs, z)
    train_z = z[train_mask]
    train_obs = query.obs.loc[train_mask].copy()
    if "pseudotime" in modules and "pseudotime" not in arrays:
        graph = ad.AnnData(train_z)
        graph.obsm["X_pca"] = train_z
        sc.pp.neighbors(graph, n_neighbors=30, use_rep="X_pca", random_state=int(seed))
        sc.tl.diffmap(graph, n_comps=15, random_state=int(seed))
        base = np.flatnonzero(train_obs.time_day.eq(0))
        graph.uns["iroot"] = int(base[np.argmin(np.sum((train_z[base]-train_z[base].mean(0))**2,axis=1))])
        sc.tl.dpt(graph,n_dcs=10)
        pt = graph.obs.dpt_pseudotime.to_numpy()
        finite = np.isfinite(pt)
        mapper = KNeighborsRegressor(n_neighbors=15, weights="distance").fit(train_z[finite],pt[finite])
        distances = NearestNeighbors(n_neighbors=1).fit(train_z[finite]).kneighbors(z)[0][:,0]
        per_cell = np.column_stack([mapper.predict(z),distances])
        arrays["pseudotime"] = _aggregate(bundle,query.obs,per_cell)
        metadata["stages"]["pseudotime"] = {"method":"scanpy diffusion pseudotime; train-only kNN query projection",
            "finite_training_cells":int(finite.sum()),"disconnected_training_cells":int((~finite).sum())}
        np.savez_compressed(array_path, **arrays)
        dump(metadata_path, metadata)
    if "distance" in modules and "distance" not in arrays:
        import pertpy as pt
        import ot
        reference = train_z[train_obs.time_day.eq(0)]
        query_groups = query.obs.groupby(["clone_id","treatment","time_day"],observed=True).indices
        from pertpy.tools._distances._distances import _sqeuclidean_std, _padded_uniform_weights
        import jax
        import jax.numpy as jnp
        from ott.geometry.pointcloud import PointCloud
        from ott.problems.linear.linear_problem import LinearProblem
        wasserstein = pt.tl.Distance("wasserstein").metric_fct
        solve_transport=wasserstein.solver
        energy=pt.tl.Distance('edistance').metric_fct
        energy_reference=energy.compute_within_distance(reference)
        mmd=pt.tl.Distance('mmd').metric_fct
        mmd_reference=mmd.compute_within_distance(reference,kernel='rbf',gamma=.05)
        distance_progress=dest/'distance_groups.json'
        result = np.zeros((len(bundle["meta"]),3,4),dtype=np.float32)
        memo = {}
        if distance_progress.exists():
            for entry in json.loads(distance_progress.read_text()):
                memo[tuple(entry['key'])]=np.asarray(entry['values'])
        for i,row in bundle["meta"].iterrows():
            for j,day in enumerate((0,1,4)):
                key=(row.clone_id,"baseline" if day==0 else row.treatment,day)
                if key not in memo:
                    ids=query_groups.get(key)
                    if ids is None:
                        memo[key]=np.zeros(4)
                    else:
                        x=z[ids]
                        epsilon=.05*_sqeuclidean_std(x,reference)
                        wa,wb=_padded_uniform_weights(len(x)),_padded_uniform_weights(len(reference))
                        xp=np.pad(x,((0,len(wa)-len(x)),(0,0)))
                        yp=np.pad(reference,((0,len(wb)-len(reference)),(0,0)))
                        geometry=PointCloud(jnp.asarray(xp),jnp.asarray(yp),epsilon=epsilon)
                        solved=solve_transport(LinearProblem(geometry,a=jnp.asarray(wa),b=jnp.asarray(wb)))
                        wcost=float(solved.reg_ot_cost)
                        if not np.isfinite(wcost) or not bool(solved.converged):
                            raise ValueError("pertpy/OTT Wasserstein solver did not converge; sentinel substitution forbidden")
                        memo[key]=np.array([energy.from_cached_values(energy.compute_within_distance(x),energy_reference,energy.compute_between_distance(x,reference)),
                            mmd.from_cached_values(mmd.compute_within_distance(x,kernel='rbf',gamma=.05),mmd_reference,
                                mmd.compute_between_distance(x,reference,kernel='rbf',gamma=.05)),wcost,
                            ot.sliced_wasserstein_distance(x,reference,n_projections=128,seed=int(seed))])
                        dump(distance_progress,[{'key':list(k),'values':v.tolist()} for k,v in memo.items()])
                        if len(memo)%20==0:print(json.dumps({'distance_groups_completed':len(memo),'fold':str(dest)}),flush=True)
                result[i,j]=memo[key]
        arrays["distance"]=result
        metadata["stages"]["distance"]={"energy":"pertpy.edistance","mmd":"pertpy.mmd",
            "wasserstein":"actual pertpy/OTT Sinkhorn solver; convergence checked instead of accepting provider's invalid-cost sentinel",
            "sliced_wasserstein":"POT sliced Wasserstein-2, 128 projections, separate metric",
            "reference":"training-clone baseline cells only","reference_cells":len(reference)}
        np.savez_compressed(array_path,**arrays)
        dump(metadata_path,metadata)
    if "cellrank" in modules and "cellrank" not in arrays:
        import cellrank as cr
        import ot
        import torch
        if not torch.cuda.is_available():raise RuntimeError('Registered CUDA OT backend unavailable; repair runtime rather than substitute a different kernel')
        result=np.zeros((len(bundle["meta"]),3,4),dtype=np.float32)
        summaries={}
        available_days=[d for d in (0,1,4) if d<=max_fit_day]
        for treatment in ("giredestrant","palbociclib","combination"):
            transfer=fit_treatments is not None and treatment not in fit_treatments
            flag=(train_obs.treatment.isin(fit_treatments)|train_obs.time_day.eq(0)) if transfer else (train_obs.treatment.eq(treatment)|train_obs.time_day.eq(0))
            obs=train_obs.loc[flag].copy()
            tz=train_z[flag]
            coupling={}
            for src,tgt in ([] if no_time_direction else zip(available_days[:-1],available_days[1:])):
                a,b=np.flatnonzero(obs.time_day.eq(src)),np.flatnonzero(obs.time_day.eq(tgt))
                cost=cdist(tz[a],tz[b],metric="sqeuclidean")
                cost/=max(float(np.median(cost)),1e-6)
                transport=ot.sinkhorn(torch.full((len(a),),1/len(a),dtype=torch.float64,device='cuda'),
                    torch.full((len(b),),1/len(b),dtype=torch.float64,device='cuda'),torch.as_tensor(cost,device='cuda'),
                    reg=.1,numItermax=1000,stopThr=1e-6,method='sinkhorn_stabilized').detach().cpu().numpy()
                if not np.isfinite(transport).all():
                    raise ValueError("Non-finite real-time OT coupling")
                coupling[(src,tgt)]=transport.astype(np.float32)
            kernel_adata=ad.AnnData(tz,obs=obs)
            kernel_adata.obs["time_category"]=pd.Categorical(obs.time_day,categories=available_days,ordered=True)
            kernel_adata.obsm["X_pca"]=tz
            if len(available_days)==1 or no_time_direction:
                sc.pp.neighbors(kernel_adata,n_neighbors=15,use_rep='X_pca',random_state=int(seed))
                kernel=cr.kernels.ConnectivityKernel(kernel_adata).compute_transition_matrix()
            else:
                kernel=cr.kernels.RealTimeKernel(kernel_adata,time_key="time_category",couplings=coupling)
                kernel.compute_transition_matrix(threshold="auto",self_transitions="all",conn_weight=.05,
                                                 conn_kwargs={"n_neighbors":15,"use_rep":"X_pca"})
            matrix=sparse.csr_matrix(kernel.transition_matrix)
            sums=np.asarray(matrix.sum(axis=1)).ravel()
            if not np.allclose(sums,1,atol=1e-4):
                raise ValueError("CellRank transition matrix is not row-stochastic")
            shift=matrix@tz-tz
            entropy=matrix.copy()
            entropy.data=-entropy.data*np.log(np.maximum(entropy.data,1e-30))
            expected_time=matrix@obs.time_day.to_numpy(dtype=float)-obs.time_day.to_numpy(dtype=float)
            if no_time_direction:expected_time=np.zeros(len(obs))
            descriptor=np.column_stack([shift[:,:2],expected_time,np.asarray(entropy.sum(axis=1)).ravel()])
            q_values=np.zeros((query.n_obs,4),dtype=float)
            for day in ([] if no_time_direction else available_days):
                qi=np.flatnonzero(query.obs.time_day.eq(day)&(query.obs.treatment.eq(treatment)|query.obs.time_day.eq(0)))
                ti=np.flatnonzero(obs.time_day.eq(day))
                projection=KNeighborsRegressor(n_neighbors=min(15,len(ti)),weights="distance").fit(tz[ti],descriptor[ti])
                q_values[qi]=projection.predict(z[qi])
            if no_time_direction:
                qi=np.flatnonzero(query.obs.treatment.eq(treatment)|query.obs.time_day.eq(0))
                projection=KNeighborsRegressor(n_neighbors=min(15,len(tz)),weights='distance').fit(tz,descriptor)
                q_values[qi]=projection.predict(z[qi])
            result+=_aggregate(bundle,query.obs,q_values,treatment=treatment)
            sparse.save_npz(dest/("cellrank_"+treatment+".npz"),matrix)
            summaries[treatment]={"cells":len(tz),"transition_nnz":matrix.nnz,
                "transport_backend":"POT Torch CUDA float64, numerically equivalent to original NumPy solver",
                "source_conditions":list(fit_treatments) if transfer else [treatment],
                "withheld_treatment_kernel":"pooled real monotherapy-training kernel projected to query, not a measured combination-training kernel" if transfer else None,
                "minimum_row_sum":float(sums.min()),"maximum_row_sum":float(sums.max())}
        arrays["cellrank"]=result
        metadata["stages"]["cellrank"]={"method":"CellRank RealTimeKernel with POT Sinkhorn couplings" if max_fit_day>0 and not no_time_direction else 'Explicit stationary CellRank ConnectivityKernel ablation; no temporal transport claimed',
            "ot_regularization":.1,"connectivity_weight":.05,"conditions":summaries}
        np.savez_compressed(array_path,**arrays)
        dump(metadata_path,metadata)
    metadata["last_call_seconds"]=time.monotonic()-start
    metadata["fit_max_time_day"]=int(train_obs.time_day.max())
    metadata["supervised_labels_used"]=False
    dump(metadata_path,metadata)
    print(json.dumps({"fold_artifacts":str(dest),"stages":list(metadata["stages"]),"seconds":metadata["last_call_seconds"]}),flush=True)
    return arrays,metadata,dest
