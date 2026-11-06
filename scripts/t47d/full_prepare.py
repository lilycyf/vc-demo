"""Complete raw-data archive, reference R interchange, and confounding audit."""
from pathlib import Path
import hashlib
import json
import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse,io
from threadpoolctl import threadpool_limits

from vc_demo.t47d_lineage.data import dump,TREATMENTS

ROOT=Path('data/t47d_lineage')
DEST=ROOT/'reference_interchange'
DEST.mkdir(exist_ok=True)
RUN=Path('experiments/t47d_lineage_resistance_full_v2')


def export_metadata(a):
    obs=a.obs.copy()
    if 'cell_barcode' not in obs:obs.insert(0,'cell_barcode',a.obs_names.astype(str))
    sample_path=RUN/'sample_manifest.csv'
    if not sample_path.exists():
        import importlib.util
        spec=importlib.util.spec_from_file_location('t47d_source_prepare',Path(__file__).with_name('prepare.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.read_samples(ROOT/'raw/GSE260703_family.soft.gz').to_csv(sample_path,index=False)
    if sample_path.exists():
        samples=pd.read_csv(sample_path)
        labels=samples.groupby('sample_id').replicate_label.agg(lambda x:';'.join(sorted(set(x.astype(str)))))
        obs['geo_replicate_label']=obs.sample_id.map(labels)
    obs.to_csv(DEST/'cell_metadata.csv',index=False)
    return obs


def main():
    cells=pd.read_csv(ROOT/'prepared/cell_qc_and_assignments.csv.gz')
    print('qc_columns',list(cells),flush=True)
    a=ad.read_h5ad(ROOT/'prepared/qc_counts.h5ad')
    if not (RUN/'clone_assignment_audit.json').exists():
        dump(RUN/'clone_assignment_audit.json',json.loads((ROOT/'prepared/dataset_manifest.json').read_text()))
    if not (ROOT/'prepared/raw_counts.h5ad').exists():
        with threadpool_limits(limits=8):counts=io.mmread(ROOT/'raw/GSE260703_count_matrix.mtx.gz').T.tocsr()
        genes=pd.read_csv(ROOT/'prepared/gene_order.csv')
        if len(cells)!=counts.shape[0] or len(genes)!=counts.shape[1]:raise ValueError('Raw order/shape mismatch')
        obs=cells.copy();obs.index=obs.cell_barcode.astype(str)
        var=genes.copy();var.index=var.iloc[:,0].astype(str)
        raw=ad.AnnData(counts.astype(np.int32),obs=obs,var=var)
        raw.uns['source']='GSE260703 processed UMI matrix, unfiltered; not FASTQ-derived BAM'
        raw.write_h5ad(ROOT/'prepared/raw_counts.h5ad',compression='gzip')
        dump(RUN/'raw_archive_audit.json',{'shape':list(raw.shape),'cells_before_qc':len(cells),
            'filtered_archive_is_separate':True,'sha256':hashlib.file_digest((ROOT/'prepared/raw_counts.h5ad').open('rb'),'sha256').hexdigest()})
        del raw,counts
    if not (RUN/'raw_archive_audit.json').exists():
        archive=ad.read_h5ad(ROOT/'prepared/raw_counts.h5ad',backed='r')
        dump(RUN/'raw_archive_audit.json',{'shape':list(archive.shape),'cells_before_qc':len(cells),
            'filtered_archive_is_separate':True,'sha256':hashlib.file_digest((ROOT/'prepared/raw_counts.h5ad').open('rb'),'sha256').hexdigest()})
        archive.file.close()
    totals=np.asarray(a.X.sum(1)).ravel()
    qc_col=next((k for k in ('qc_pass','qc_status','qc_pass_expression','expression_qc_pass') if k in cells),None)
    total_col=next((k for k in ('total_counts','total_umi','umi_count','sum') if k in cells),None)
    if not qc_col or not total_col:raise ValueError('Cannot reconstruct all-QC library centering without audited columns')
    qc=cells[qc_col]
    if qc.dtype!=bool:qc=qc.astype(str).str.lower().isin(['true','pass','passed','1'])
    center=float(cells.loc[qc,total_col].mean())
    normalized=sparse.diags(center/np.maximum(totals,1)).dot(a.X).tocsr().astype(np.float32)
    normalized.data=np.log2(1+normalized.data)
    pathways=[];names=[]
    symbols=pd.read_csv(ROOT/'prepared/gene_order.csv').gene_symbol.fillna('').to_numpy()
    for line in (ROOT/'pathways/h.all.v2025.1.Hs.symbols.gmt').read_text().splitlines():
        terms=line.split('\t');ids=np.flatnonzero(np.isin(symbols,terms[2:]));names.append('Score.'+terms[0]);pathways.append(ids)
    scores=np.column_stack([np.asarray(normalized[:,ids].mean(1)).ravel() for ids in pathways])
    pd.DataFrame(scores,columns=names).to_csv(DEST/'pathway_scores.csv',index=False)
    export_metadata(a)
    selection={};mask=np.zeros(a.n_vars,dtype=bool)
    for trt in TREATMENTS:
        use=(a.obs.treatment.eq(trt)|a.obs.time_day.eq(0))&a.obs.time_day.le(26)
        selected=np.asarray((a.X[use.to_numpy()]>3).sum(0)).ravel()>int(use.sum())/10
        selection[trt]=selected;mask|=selected
    base=a.obs.time_day.eq(0)
    base_genes=np.asarray((a.X[base.to_numpy()]>3).sum(0)).ravel()>int(base.sum())/4
    mask|=base_genes;ids=np.flatnonzero(mask)
    pathway_coverage={}
    for trt,filter_mask in selection.items():
        kept=[np.intersect1d(p,np.flatnonzero(filter_mask)) for p in pathways]
        good=[(name,p) for name,p in zip(names,kept) if len(p)]
        values=np.column_stack([np.asarray(normalized[:,p].mean(1)).ravel() for _,p in good])
        pd.DataFrame(values,columns=[name for name,_ in good]).to_csv(DEST/('pathway_scores_'+trt+'.csv'),index=False)
        pathway_coverage[trt]={name:len(p) for name,p in zip(names,kept)}
    dump(DEST/'pathway_filtered_gene_coverage.json',pathway_coverage)
    # R readBin fills columns: transpose bytes retain a precise cells x genes contract.
    normalized[:,ids].toarray().astype('<f4').T.tofile(DEST/'logcounts_float32.bin')
    selection_table=pd.DataFrame({'gene_id':a.var_names[ids],'baseline':base_genes[ids],**{k:v[ids] for k,v in selection.items()}})
    selection_table.to_csv(DEST/'selected_gene_order.csv',index=False)
    dump(DEST/'interchange.json',{'n_cells':a.n_obs,'n_genes':len(ids),'binary_dtype':'little endian float32',
        'binary_layout':'gene-major, then cells; R matrix(nrow=n_cells)',
        'normalization':'log2(1 + counts / (all_gene_cell_total / mean_total_all_expression_QC_cells)))',
        'all_expression_qc_cells':int(qc.sum()),'centering_total':center,
        'source_gene_filters':'>3 UMI in >10% condition cells; baseline innate >25%; no arbitrary HVG truncation',
        'mapping':'public Hallmark 2025.1, not inaccessible author GMTY42 revision1/custom ER set'})
    table=cells.groupby(['library_id','replicate_id','treatment','time_day'],dropna=False).size().reset_index(name='cells')
    table.to_csv(RUN/'library_treatment_time_confounding.csv',index=False)
    dump(RUN/'confounding_audit.json',{'libraries':int(cells.library_id.nunique()),'replicate_independence_verified':False,
        'caveat':'GEO replicate tags and library prefixes are recorded; do not treat cell counts as biological replication',
        'libraries_per_condition':table.groupby(['treatment','time_day']).library_id.nunique().astype(int).to_dict().__str__(),
        'barcode_assignment':'exactly one nonzero barcode; multibarcode and zero-barcode excluded from clone endpoints',
        'barcode_collision_risk':'shared observed sequence defines operational lineage; actual molecular collision not identifiable from processed matrices'})
    print('reference_interchange_complete',a.n_obs,len(ids),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,default=RUN);parser.add_argument('--metadata-only',action='store_true')
    args=parser.parse_args();RUN=args.run_dir;RUN.mkdir(parents=True,exist_ok=True)
    if args.metadata_only:
        source=ad.read_h5ad(ROOT/'prepared/qc_counts.h5ad',backed='r');export_metadata(source);source.file.close()
    else:main()
