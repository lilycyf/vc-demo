# Public-data reconstruction of the author PLSR/Slingshot/TraCSED preprocessing.
suppressPackageStartupMessages({library(jsonlite);library(pls);library(slingshot);library(scran);library(igraph);library(BiocNeighbors);library(BiocParallel)})
args=commandArgs(trailingOnly=TRUE)
input=if(length(args))args[1] else 'data/t47d_lineage/reference_interchange'
output=if(length(args)>=2)args[2] else 'experiments/t47d_lineage_resistance_full_v2/reference'
dir.create(output,recursive=TRUE,showWarnings=FALSE)
info=fromJSON(file.path(input,'interchange.json'))
meta=read.csv(file.path(input,'cell_metadata.csv'),stringsAsFactors=FALSE)
genes=read.csv(file.path(input,'selected_gene_order.csv'))
for(column in c('baseline','giredestrant','palbociclib','combination'))genes[[column]]=as.logical(genes[[column]])
paths=read.csv(file.path(input,'pathway_scores.csv'),check.names=FALSE)
con=file(file.path(input,'logcounts_float32.bin'),'rb')
expression=matrix(readBin(con,'numeric',n=info$n_cells*info$n_genes,size=4,endian='little'),nrow=info$n_cells)
close(con)
stopifnot(nrow(expression)==nrow(meta),ncol(expression)==nrow(genes))
colnames(expression)=make.names(genes$gene_id,unique=TRUE)
days=c(0,1,4,8,26)
treatments=c('giredestrant','palbociclib','combination')
bars=paste0('GFPBC_libB_',c(92196,20182,90850,10678,37798,31581,40758,94397,83026,10737,81397))
resolutions=c(.2,.25,.3,.35,.4,.45,.5,.75,1)
reference=list()

minMax=function(x){(x-min(x))/(max(x)-min(x))}
cellbounds=function(change,scebar){
  norm=minMax(change);position=which(norm>=.15);half=length(change)/2
  poslow=if(length(position[position<=half]))max(position[position<=half]) else 1
  poshigh=if(length(position[position>half]))min(position[position>half]) else length(change)
  scebar[poslow:poshigh,,drop=FALSE]
}

for(trt in treatments){
  target=file.path(output,paste0(trt,'_reference.json'))
  if(file.exists(target))next
  cat('BEGIN_REFERENCE',trt,'\n');flush.console()
  paths=read.csv(file.path(input,paste0('pathway_scores_',trt,'.csv')),check.names=FALSE)
  use=which((meta$treatment==trt|meta$time_day==0)&meta$time_day%in%days)
  m=meta[use,];x=expression[use,genes[[trt]],drop=FALSE]
  x=x[,apply(x,2,sd)>1e-8,drop=FALSE]
  y=match(m$time_day,days)
  set.seed(1)
  fitpath=file.path(output,paste0(trt,'_time_plsr.rds'))
  fit=if(file.exists(fitpath))readRDS(fitpath) else plsr(y~x,ncomp=min(30,ncol(x)-1),scale=TRUE,validation='CV',segments=10)
  plsscores=unclass(pls::scores(fit))[,1:5,drop=FALSE]
  saveRDS(fit,fitpath)
  pca=prcomp(x,center=TRUE,scale.=TRUE,rank.=5)$x[,1:5,drop=FALSE]
  representations=list(PLSR=plsscores,PCA=pca)
  candidates=list();best=NULL;bestks=-Inf
  gridpath=file.path(output,paste0(trt,'_grid_checkpoint_v2.rds'))
  if(file.exists(gridpath)){
    cached=readRDS(gridpath);candidates=cached$candidates;best=cached$best;bestks=cached$bestks
  }
  for(representation in names(representations)){
    z=representations[[representation]]
    set.seed(42)
    graph=buildSNNGraph(t(z),d=NA,k=50,BNPARAM=AnnoyParam(),BPPARAM=MulticoreParam(4))
    for(res in resolutions){
      set.seed(42)
      membership=as.character(cluster_leiden(graph,objective_function='CPM',resolution_parameter=res)$membership)
      means=tapply(m$time_day,membership,mean)
      start=names(which.min(means));end=names(which.max(means))
      key=paste(representation,res,sep='_')
      if(!is.null(candidates[[key]]))next
      if(start==end){candidates[[key]]=list(status='single_time_cluster',resolution=res,representation=representation);next}
      result=tryCatch({
        sl=slingshot(z,clusterLabels=membership,start.clus=start,end.clus=end,stretch=0,approx_points=200)
        pt=rowMeans(slingPseudotime(sl),na.rm=TRUE)
        ok=is.finite(pt);q=quantile(pt[ok],c(.01,.99))
        norm=pmax(0,pmin(1,(pt-q[1])/diff(q)))
        ks=sum(sapply(seq_len(4),function(i){a=norm[m$time_day==days[i]&ok];b=norm[m$time_day==days[i+1]&ok];as.numeric(ks.test(a,b,exact=FALSE)$statistic)}))
        list(status='evaluated',representation=representation,resolution=res,clusters=length(unique(membership)),
             start_cluster=start,end_cluster=end,finite_cells=sum(ok),excluded_cells=sum(!ok),ks_sum=ks,pt=pt,norm=norm)
      },error=function(e)list(status='trajectory_failure',error=conditionMessage(e),resolution=res,representation=representation))
      candidates[[key]]=result[setdiff(names(result),c('pt','norm'))]
      if(result$status=='evaluated'&&is.finite(result$ks_sum)&&result$ks_sum>bestks){best=result;bestks=result$ks_sum}
      saveRDS(list(candidates=candidates,best=best,bestks=bestks),gridpath)
      write_json(candidates,file.path(output,paste0(trt,'_trajectory_grid.json')),auto_unbox=TRUE,pretty=TRUE)
      cat('TRAJECTORY_GRID',trt,key,result$status,if(!is.null(result$ks_sum))result$ks_sum else '', '\n');flush.console()
    }
  }
  if(is.null(best))stop(paste('No valid real Slingshot trajectory',trt))
  order=order(best$pt,na.last=NA);order=order[is.finite(best$pt[order])]
  mm=m[order,];pt=best$norm[order];n=nrow(mm)
  sv=numeric(n)
  for(bar in unique(mm$clone_id)){
    flag=as.numeric(mm$clone_id==bar);left=cumsum(flag);right=rev(cumsum(rev(flag)))
    ids=which(flag==1)
    sv[ids]=log2((right[ids]/(n-ids+1))/(left[ids]/ids))
  }
  scores=paths[use[order],,drop=FALSE]
  allrows=data.frame(cell_barcode=mm$cell_barcode,clone_id=mm$clone_id,time_day=mm$time_day,pseudotime=pt,selection=sv)
  write.csv(allrows,file.path(output,paste0(trt,'_pseudotime_selection.csv')),row.names=FALSE)
  built=list();excluded=list()
  for(bar in bars){
    loc=which(mm$clone_id==bar)
    if(length(loc)<=5){excluded[[bar]]=list(reason='not enough cells for source six-cell smoothing',cells=length(loc));next}
    rolling=function(v)vapply(seq_len(length(v)-5),function(i)mean(v[i:(i+5)]),numeric(1))
    # Source smooths Survival/Pseudotime, but retains unsmoothed pathway values.
    sm=scores[loc[6:length(loc)],,drop=FALSE]
    sy=rolling(sv[loc]);sp=rolling(pt[loc]);actual=mm$time_day[loc][6:length(loc)]
    frame=data.frame(Pseudotime=sp,RealTime=paste0('Day',actual),Survival=sy,sm,check.names=FALSE)
    change=abs(diff(sy));frame=cellbounds(change,frame)
    if(nrow(frame)>200){built[[bar]]=frame}else excluded[[bar]]=list(reason='source notebook minimum >200 after trimming',cells=nrow(frame))
  }
  write_json(built,target,auto_unbox=TRUE,pretty=FALSE,na='null')
  write_json(excluded,file.path(output,paste0(trt,'_excluded_barcodes.json')),auto_unbox=TRUE,pretty=TRUE)
  write_json(best[setdiff(names(best),c('pt','norm'))],file.path(output,paste0(trt,'_selected_trajectory.json')),auto_unbox=TRUE,pretty=TRUE)
  # Innate resistance reference uses raw day26/baseline frequency ratios, not log2+eps.
  baseline=which(meta$time_day==0)
  basecounts=table(meta$clone_id[baseline]);endcounts=table(meta$clone_id[meta$treatment==trt&meta$time_day==26])
  endpoint=as.numeric(endcounts[names(basecounts)]);endpoint[is.na(endpoint)]=0
  ratios=(endpoint/sum(endcounts))/(as.numeric(basecounts)/sum(basecounts));names(ratios)=names(basecounts)
  xi=expression[baseline,genes$baseline,drop=FALSE];xi=xi[,apply(xi,2,sd)>1e-8,drop=FALSE]
  yi=ratios[meta$clone_id[baseline]]
  set.seed(1);innate=plsr(yi~xi,ncomp=min(30,ncol(xi)-1),scale=TRUE,validation='CV',segments=10)
  saveRDS(innate,file.path(output,paste0(trt,'_innate_plsr.rds')))
  write_json(list(components=30,source_protocol='random-cell CV retrospective innate reference, NOT clone-heldout forecast',
       n_cells=length(baseline),n_genes=ncol(xi),raw_ratio_by_clone=as.list(ratios),cv_RMSEP=as.numeric(RMSEP(innate)$val)),
       file.path(output,paste0(trt,'_innate_plsr_metrics.json')),auto_unbox=TRUE,pretty=TRUE)
  cat('REFERENCE_EXPORTED',trt,length(built),'\n');flush.console()
}
write_json(list(status='complete',resolutions=resolutions,
  implementation='Actual R pls::plsr, scran SNN, igraph Leiden, Slingshot; no private IO dependency',
  deliberate_alignment_differences=c('Public Hallmark release replaces private GMTY42/custom signature',
  'Cluster IDs selected by minimum/maximum mean real time rather than nonportable author IDs',
  'Full-data retrospective reference is never used as prospective forecast feature',
  'PCA recreated from public filtered normalized matrix; internal PCA object unavailable'),
  source='https://github.com/Genentech/TraCSED',author_commit='dc5a750ef6fc6adf50e362ba5c2d38bee6083289'),
  file.path(output,'reference_preprocessing_provenance.json'),auto_unbox=TRUE,pretty=TRUE)
