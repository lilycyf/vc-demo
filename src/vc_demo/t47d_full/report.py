"""Evidence-gated, complete-scope report with scientific figures and tree."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
import subprocess
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from vc_demo.t47d_full.study import RUN,bundle
from vc_demo.t47d_lineage.data import dump


def read(path,default=None):
    return json.loads(path.read_text()) if path.exists() else default


def number(value):
    return 'undefined' if value is None else f'{value:.4f}'


def report(run=RUN):
    b=bundle(run);tree=read(run/'tree.json',{'nodes':{}});nodes=list(tree['nodes'].values())
    trained=[n for n in nodes if n['status']=='trained'];children=[n for n in trained if n.get('parent')]
    selection=read(run/'frozen_selection.json',{});tests=read(run/'frozen_test_metrics.json',{})
    abl=read(run/'eight_ablations.json',{});loco=read(run/'loco_results.json',{})
    challenges=read(run/'challenge_metrics.json',{});biology=read(run/'biological_and_sensitivity_analysis.json',{})
    ras=read(run/'resistance_attractor_and_month6.json',{})
    denominator=read(run/'denominator_null_diagnostic.json',{})
    trace=[json.loads(line) for line in (run/'mcts_trace.jsonl').read_text().splitlines()] if (run/'mcts_trace.jsonl').exists() else []
    references=[]
    ref=run/'reference';source_ref=read(ref/'reference_preprocessing_provenance.json',{})
    if (ref/'tf_reference_results.jsonl').exists():
        references=[json.loads(line) for line in (ref/'tf_reference_results.jsonl').read_text().splitlines()]
    guards={'fallback':0,'proxy':0,'nontrained_backprop':0,'pruned_training':0,'test_clone_training_in_primary_cv':0,'wrong_external_backend':0}
    for e in trace:
        if e['event']=='backpropagation':
            guards['nontrained_backprop']+=int(e.get('status')!='trained' or tree['nodes'][e['node']]['status']!='trained')
            guards['pruned_training']+=int(tree['nodes'][e['node']]['status'].startswith('pruned'))
    for p in (run/'programs').glob('*/pipeline.json'):
        item=read(p);guards['fallback']+=int(bool(item.get('fallback')));guards['proxy']+=int(bool(item.get('proxy')))
        guards['wrong_external_backend']+=int(item.get('backend')=='external_static_node')
    for f in b['splits']['folds']:
        guards['test_clone_training_in_primary_cv']+=int(bool(set(f['train_clones'])&set(b['splits']['test_clones'])))
    for n in nodes:
        if n['status'].startswith('pruned'):
            guards['pruned_training']+=int((run/'programs'/n['id']/'fold_results.json').exists())
    audit={'checks':guards,'passed':not any(guards.values()),'evidence':'tree, fold results, fixed splits, node contracts and MCTS trace'}
    dump(run/'guardrail_audit.json',audit)
    modes=Counter(r['variant'] for r in references)
    required_dynamics={'early_elastic','gru','temporal_transformer','tracsed','hazard'}
    observed={n['config']['model'] for n in children};reps={n['config']['representation'] for n in children}
    coverage={
        'raw_unfiltered_archive':Path('data/t47d_lineage/prepared/raw_counts.h5ad').exists(),
        'five_formal_roots':sum(n.get('parent') is None for n in trained)==5,
        'forty_formal_selected_rollouts':len(children)>=40,
        'all_six_representations':{'pseudobulk','pca','scvi','pathway','distance','pseudotime'}<=reps,
        'all_dynamics_including_cellrank':required_dynamics<=observed and 'cellrank' in reps,
        'all_five_interactions':{'additive_null','bilinear','gated_pathway','cross_attention','moe'}<=observed,
        'four_prediction_heads':{'regression','positive_selected','mono_resistant_combo_sensitive','ranking'}<={n['config'].get('head','regression') for n in children},
        'five_training_losses':{'huber','weighted_bce','focal','pairwise','multitask'}<={n['config'].get('loss','huber') for n in children},
        'author_R_reference_all_treatments':bool(source_ref) and all((ref/(t+'_reference.json')).exists() for t in ('giredestrant','palbociclib','combination')),
        'author_TF_reference_and_ablation_models':all(modes[m]>0 for m in ('full','no_attention','no_feedforward','linear_reference')),
        'five_seed_primary_CV':bool(trained) and all(n.get('formal_fold_fits')==15 for n in trained),
        'frozen_test_root_child':bool(selection) and all(selection.get(k) in tests for k in ('root','child')),
        'all_eight_formal_ablations':len(abl)==8 and all(v.get('formal_fold_fits')==15 for v in abl.values()),
        'complete_46_clone_LOCO':bool(selection) and all(len(loco.get(selection[k],{}).get('folds',[]))==46 for k in ('root','child')),
        'late_time_challenge':'late_interval_holdout' in challenges,
        'monotherapy_transfer_challenge':'monotherapy_to_combination' in challenges,
        'early_warning_per_cutoff':'early_warning' in challenges,
        'long_term_escape_evaluated_with_identifiability_limits':bool(ras),
        'ER_E2F_EMT_and_label_sensitivity':bool(biology),
        'guardrails':audit['passed']}
    whole=all(coverage.values());dump(run/'completion_matrix.json',{'whole_original_document_complete':whole,'requirements':coverage})
    table=[]
    for n in trained:
        table.append({'node':n['id'],'parent':n.get('parent'),'model':n['config']['model'],'representation':n['config']['representation'],
            'head':n['config'].get('head','regression'),'loss':n['config'].get('loss','huber'),'validation_spearman':n['validation_reward'],
            'validation_seed_std':n['validation_std'],'validation_mae':n['validation_mae'],'seconds':n['duration_seconds']})
    pd.DataFrame(table).to_csv(run/'trained_node_catalog.csv',index=False)
    with (run/'selected_rollouts.jsonl').open('w') as f:
        for row in table:
            if row['parent']:f.write(json.dumps(row)+'\n')
    dump(run/'root_metrics.json',{n['id']:n for n in trained if n.get('parent') is None})
    stats={'trained_roots':sum(n.get('parent') is None for n in trained),'trained_selected_rollouts':len(children),
        'generated_proposals':sum(n.get('parent') is not None for n in nodes),'statuses':dict(Counter(n['status'] for n in nodes)),
        'formal_primary_fold_fits':sum(n.get('formal_fold_fits',0) for n in trained),
        'formal_ablation_fold_fits':sum(n.get('formal_fold_fits',0) for n in abl.values()),
        'LOCO_fits':sum(len(r.get('folds',[])) for r in loco.values()),'retrospective_reference_fits':len(references),
        'formal_denominator_diagnostic_fits':sum(d.get('formal_fold_fits',0) for d in denominator.get('draws',[])),
        'whole_original_document_complete':whole,'test_exposure_caveat':True,'guardrails':guards}
    if selection:
        r,c=[tree['nodes'][selection[k]] for k in ('root','child')]
        deltas=[cc['spearman']-rr['spearman'] for cc,rr in zip(c['seed_metrics'],r['seed_metrics'])]
        stats.update(best_root=r['id'],best_child=c['id'],validation_child_minus_root=c['validation_reward']-r['validation_reward'],
            per_seed_child_minus_root=deltas,child_beats_root_seeds=sum(d>0 for d in deltas),
            best_root_test=tests.get(r['id']),best_child_test=tests.get(c['id']))
        dump(run/'root_dominance_audit.json',{'validation_delta':stats['validation_child_minus_root'],'paired_seed_deltas':deltas,
            'test_not_used_to_reselect':True,'context':'Repeated OOF winner is selection-optimistic; prior pilot test exposure prohibits a new-blind confirmation claim',
            'controls':{k:v['validation_reward'] for k,v in abl.items()},
            'denominator_null_diagnostic':denominator,
            'assessment':'Scientific superiority is assessed independently from framework completion; neither smoke nor mandatory family coverage proves superiority'})
    dump(run/'full_study_results.json',stats)
    figdir=run/'figures';figdir.mkdir(exist_ok=True)
    if trained:
        fig,ax=plt.subplots(figsize=(12,5));xx=np.arange(len(table));colors=['#555555' if not r['parent'] else '#16887d' for r in table]
        ax.bar(xx,[r['validation_spearman'] for r in table],color=colors,yerr=[r['validation_seed_std'] for r in table],capsize=2)
        ax.set(xlabel='Evaluated candidate (five roots, then selected rollouts)',ylabel='Repeated clone-group OOF Spearman',title='Formal search: validation only');ax.axhline(0,color='black',lw=.7)
        fig.tight_layout();fig.savefig(figdir/'search_validation.png',dpi=160);plt.close(fig)
    if abl and selection:
        names=list(abl);values=[abl[k]['validation_reward'] for k in names]
        fig,ax=plt.subplots(figsize=(11,6));ax.barh(names,values,color='#557fc0');ax.axvline(tree['nodes'][selection['child']]['validation_reward'],color='#c63843',label='Frozen best child')
        ax.set(xlabel='Repeated clone-group OOF Spearman',title='Eight prespecified ablations');ax.legend();fig.tight_layout();fig.savefig(figdir/'eight_ablations.png',dpi=160);plt.close(fig)
    if references:
        refdf=pd.DataFrame(references);refdf[['barcode','interval','variant','mse','mae']].to_csv(ref/'reference_metric_catalog.csv',index=False)
        fig,ax=plt.subplots(figsize=(8,5));refdf.boxplot(column='mse',by='variant',ax=ax,showfliers=False);ax.set(title='Author reference: retrospective interpolation MSE',ylabel='Normalized selection MSE');fig.suptitle('');fig.tight_layout();fig.savefig(figdir/'author_reference.png',dpi=160);plt.close(fig)
        importance=[]
        for r in references:
            for name,value in r.get('permutation_feature_importance',{}).items():
                importance.append({'condition_barcode':r['barcode'],'pathway':name,**value})
        if importance:pd.DataFrame(importance).to_csv(ref/'pathway_permutation_importance.csv',index=False)
    if biology:
        pd.DataFrame([{'comparison':k,**v} for k,v in biology['pathway_pairs'].items()]).to_csv(run/'paired_pathway_comparisons.csv',index=False)
    manifest=read(Path('data/t47d_lineage/prepared/dataset_manifest.json'),{})
    artifact={'GSE260703_processed_counts':{'status':'original_public','source':'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE260703','path':'data/t47d_lineage/raw','checksums':'initial acquisition manifest + source file manifest'},
        'raw_and_QC_AnnData':{'status':'derived_public_data','raw':'data/t47d_lineage/prepared/raw_counts.h5ad','QC':'data/t47d_lineage/prepared/qc_counts.h5ad'},
        'Hallmark':{'status':'original_public','release':'2025.1.Hs','sha256':b['contract']['pathways']['sha256'],'license':'MSigDB terms; source memberships not silently relicensed','source':'https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/h.all.v2025.1.Hs.symbols.gmt'},
        'scVI':{'status':'trained_from_public_counts_per_fold','path':'data/t47d_lineage/full_fold_artifacts/*/scvi_model','query_adaptation_steps':0},
        'CellRank':{'status':'derived_real_time_OT_kernel','path':'data/t47d_lineage/full_fold_artifacts/*/cellrank_*.npz','query_method':'train-kernel descriptors projected from train cells only'},
        'TraCSED_source':{'status':'original_public_code','commit':'dc5a750ef6fc6adf50e362ba5c2d38bee6083289','license':'MIT','path':'/workspace/_external/TraCSED','source':'https://github.com/Genentech/TraCSED'},
        'TraCSED_private_preprocessed_SCE_and_custom_signature':{'status':'not_publicly_reproduced_numerically','resolution':'reconstruct from public counts and public memberships, report differences, not a placeholder model'},
        'persistence_model':{'status':'fitted_interval_censored_AFT','endpoint':'persistent sampled non-detection, not biological death'}}
    dump(run/'artifact_registry.json',artifact)
    artifact['raw_download_manifest']=read(Path('data/t47d_lineage/raw/download_manifest.json'),{})
    artifact['unfiltered_archive']=read(run/'raw_archive_audit.json',{})
    dump(run/'artifact_registry.json',artifact)
    (run/'artifact_acquisition_report.md').write_text('# Artifact Acquisition\n\nAll required executable public-data modules were downloaded, installed, or trained from the public matrix.\n\nPrivate gp.sa.core/gstore IO and the exact custom gene-set revision are not asserted to be public artifacts. The R adapter reconstructs their input from public counts; exact numerical equivalence is not claimed.\n\nWeights, count matrices, fold latents and transition kernels persist on the Network Volume and are not committed to GitHub. Rebuild with the complete-study command in the runbook.\n')
    packages={p:importlib.metadata.version(p) for p in ('scanpy','scvi-tools','cellrank','pertpy','POT','lifelines','torch','xgboost')}
    dump(run/'package_versions.json',packages)
    cost={'gpu':'RTX 3090 24GB','allocation_start_utc':'2026-11-06T07:53:00+00:00','report_time_utc':datetime.now(timezone.utc).isoformat(),
        'gpu_and_container_rate_usd_per_hour':.507,'network_volume_monthly_usd':7,'initial_authorization_usd':20,
        'compute_hours_to_report':(datetime.now(timezone.utc)-datetime.fromisoformat('2026-11-06T07:53:00+00:00')).total_seconds()/3600,
        'server_still_running_per_user_request':True,'automatic_stop_deadline_utc':'2026-11-07T07:30:00+00:00',
        'billing_note':'Allocation-time estimate, not an invoice or sum of CUDA kernel times'}
    cost['estimated_initial_allocation_cost_including_full_volume_month_usd']=cost['compute_hours_to_report']*.507+7
    dump(run/'cost_and_runtime.json',cost)
    lines=['# T47D 谱系耐药完整 Demo：正式实验报告','',f"生成时间：{datetime.now(timezone.utc).isoformat()}",
        f"原文档范围全部完成：**{whole}**。完成矩阵见 `completion_matrix.json`，未执行项目不会被勾选。",'',
        '## 研究与证据边界','',
        '用真实 GSE260703 TraCe-seq 数据，预测同一克隆在 giredestrant、palbociclib 和联合处理下第 26 天的相对选择。输入仅为第 0、1、4 天；标签为预注册 eps=1e-5 的 log2 终点／基线频率比。',
        '这不是患者疗效、绝对增长率或单细胞状态逆转的证明。相对丰度受群体组成影响；未检出不等于生物学灭绝。',
        '**重要：同一批 heldout 克隆在先前 pilot 已报告过。此次架构选择仅使用开发集 OOF 分数，但不能将这组 test 再称为全新盲测或外部生物学复现。**','',
        '## 数据与分组','',
        f"- 原始矩阵：200,429 cells × 58,302 genes；表达 QC 通过 79,535，唯一条码且通过 QC 47,718。",
        f"- 基线至少 10 个细胞的 46 个克隆；开发集 36、保留组 10；合计 138 个 clone×treatment 预测单位。",
        '- clone ID、时间、处理、文库、GEO replicate 标签均保留。文库不等于独立生物学重复，详见混杂审计。',
        '- 所有监督分组以 clone 为单位；5 seeds × 3 folds，共 15 次拟合产生每个候选的正式 reward。',
        '- 基因选择、标准化、PCA/scVI、伪时间、距离参照及 CellRank 核均只用相应训练克隆拟合。','',
        '## 搜索与模型范围','',
        f"5 roots；{len(children)} 个正式 selected rollouts；{stats['generated_proposals']} 个生成 proposal。完整结果见 `trained_node_catalog.csv`。",
        '107 个可执行结构模板，覆盖文档的全部表征、动力学、交互、head 和 loss。预先声明的模块覆盖需求先保证每种方法得到正式评估，之后以 UCT parent selection 和全局队列继续搜索；artifact 是否 present 不加科学优先级。',
        'node-local model.py 是实际执行入口；保留 parent 的预测，再拟合训练残差。只有完整 15 折 reward 的 trained 节点才 backprop。每次完成 rollout 后重新生成候选。队列全局容量 48，pruned 不训练。',
        '作者 TraCSED 函数从公开 notebook 提取并保存 hash：正式 early-forecast adapter 使用其真实架构；另外完整运行 R PLSR/Slingshot 与 seq8 retrospective reference，二者分开报告。','',
        '## 原方法参考复现','',
        f"R 预处理状态：{source_ref.get('status','未完成')}；TensorFlow／线性参考已完成拟合 {len(references)} 次。各模式计数：{dict(modes)}。",
        'R 使用作者规则的 count>3 基因过滤、30-component PLSR、Leiden 网格、Slingshot、相邻实时时间 KS 和六细胞平滑。private SCE、内部 gene-set revision 与不可移植 cluster IDs 均明确记录重建差异，不能声称逐数值复现。',
        'TensorFlow 保留作者实际 build_model 的计算图，包括重复块和 channels_first pooling 的原代码行为；20 epochs、seq8、40 heads、head size5、ff_dim5、Dense256，以及 no-attention/no-feedforward/线性对照。',
        '这些 retrospective prefix-window 分数有同克隆窗口依赖和伪时间 hindsight，不能与早期→day26 heldout-clone Spearman 混作同一个 benchmark。','',
        '![正式验证搜索](figures/search_validation.png)','',
        '## Best Root 与 Generated Child','',
        '| 模型 | 重复 OOF Spearman | seed 标准差 | 保留克隆 Spearman | 保留克隆 MAE |','|---|---:|---:|---:|---:|']
    for k in ('root','child'):
        if k in selection:
            n=tree['nodes'][selection[k]];t=tests.get(n['id'],{}).get('ensemble',{})
            lines.append(f"| {n['id']} | {n['validation_reward']:.4f} | {n['validation_std']:.4f} | {number(t.get('spearman'))} | {number(t.get('mae'))} |")
    if selection:
        lines.extend(['',f"Child-root validation 差值：{stats['validation_child_minus_root']:+.4f}；5 个配对 seed 中超过 root：{stats['child_beats_root_seeds']}/5。",
        '95% CI 以 clone block bootstrap 计算，保留同一克隆的全部处理。分类 AUPRC/AUROC、NDCG、Brier/ECE 和联合抑制正确率详见 `frozen_test_metrics.json`；概率校准仅拟合开发 OOF。'])
    lines+=['','## 八项消融','','![八项正式消融](figures/eight_ablations.png)','',
        '| 消融 | 重复 OOF Spearman | 相对原 child |','|---|---:|---:|']
    for name,v in abl.items():
        baseline=tree['nodes'][selection['child']]['validation_reward']
        lines.append(f"| {name} | {v['validation_reward']:.4f} | {v['validation_reward']-baseline:+.4f} |")
    lines+=['','无条码输入消融仍保留真实条码作为标签与分组依据，但预测特征只用训练克隆的处理条件均值，删除克隆丰度；不是破坏 ground truth。打乱通路用全局基因置换，保持集合大小与重叠；不是简单换列名。matched-capacity control 保持各层表示宽度。去 dense parent 同时移除继承预测及神经内部 dense 分支。','',
        '## 五层评估','','1. 开发集 repeated clone-group CV：每个正式候选 15 fits。',
        '2. 冻结模型选择后的 46-clone LOCO：完整数据的次级跨拟合，不代替主保留组评估。',
        '3. late holdout：仅以 day8 selection 训练、day26 作未见终点，输入最高 day4。',
        '4. monotherapy→combination：训练不读取联合监督标签；用独立化学指示量 [1,1] 表达组合。',
        '5. Month6：冻结早期预测、AFT persistence 与探索性吸引子评分后，核对所有已观察到的长期克隆。',
        '早期预警按 day0/day1/day4 分别重拟合，报告 lead time 与 AUPRC，而非用 day4 模型伪称 day1 预警。','',
        '## 联合抑制与生物学解释','',
        f"观测到单药正选择、联合负选择的克隆：{biology.get('mono_positive_combo_negative_count','未完成')} / {biology.get('mono_positive_count','未完成')} 个单药正选择克隆。",
        'ER／E2F／EMT 的 clone-paired 动态差异及 bootstrap CI 见 `paired_pathway_comparisons.csv`。所有比较为描述性、存在幸存者偏倚与多重比较，不把 nominal p 值当作临床机制证明。',
        '原文 raw-ratio suppression 与变换后的 log2 差值分开计算，不混淆两种量纲。eps=1e-6/1e-5/1e-4 与 endpoint 未检出敏感性已记录。','',
        '## 长期逃逸与吸引子评分','',
        'RAS 权重预先固定为 .40/.25/.20/.15，标准化及负选择克隆参照仅来自开发集；query 不读取自己的未来标签或未来表达。persistence 为真实区间删失 AFT 从训练终点拟合后的 day180 尾部外推，只能探索。',
        f"保留组可评估长期阳性克隆数：{ras.get('locked_test_positive_count','未完成')}；未见克隆逃逸 recall：{ras.get('unseen_clone_escape_recall')}。",
        '若保留组没有阳性，则 recall 不可识别；不能把开发集中的长期优势克隆排得靠前写成 100% 泛化。基线不足的长期稀有条码单独列出，不伪造早期输入。','',
        '## 审计与成本','',f"Guardrails：{guards}。",f"正式主搜索拟合 {stats['formal_primary_fold_fits']}；消融拟合 {stats['formal_ablation_fold_fits']}；LOCO 拟合 {stats['LOCO_fits']}。",
        f"GPU：RTX3090；截至报告分配 {cost['compute_hours_to_report']:.2f} 小时，按配置费率加完整月 volume 估计 ${cost['estimated_initial_allocation_cost_including_full_volume_month_usd']:.2f}，非账单。",
        '代码、版本锁、split、轻量结果和报告进 GitHub；原始数据、模型权重、完整参考中间矩阵和折内 artifact 仅存 Network Volume。首轮预算停止器不被自动延长。','',
        '## 完成矩阵','', '| 原文档要求 | 已有执行证据 |','|---|---|']
    lines.extend(f'| {key} | {value} |' for key,value in coverage.items())
    lines+=['','## 已训练节点关系','','```mermaid','flowchart TD']
    ids={n['id']:'n'+str(i) for i,n in enumerate(trained)}
    for n in trained:
        lines.append(f'  {ids[n["id"]]}["{n["config"]["model"]} / {n["config"]["representation"]} / rho {n["validation_reward"]:.3f}"]')
        if n.get('parent'):lines.append(f'  {ids[n["parent"]]} --> {ids[n["id"]]}')
    lines+=['```','','## 一条命令复现','', '```bash',
        'cd /workspace/vc-demo','export PYTHONPATH=src OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 NUMBA_NUM_THREADS=4 JAX_PLATFORMS=cpu',
        '/workspace/t47d_full_venv/bin/python scripts/t47d/full_demo.py --phase all','```','',
        '已完成折、冻结选择和参考拟合按文件恢复，不会把 smoke 奖励冒充正式结果。若更改冻结 task/split/科学协议，必须使用新注册运行；修复记录和 source hash 需保留。','',
        '## 结论','',
        '流程完整性、预测优越性和生物学因果性是三个不同问题。只有完成矩阵全部有证据，才称原文档 demo 完成；child 没有超过 root 时输出 root-dominance audit，不通过减少比较、改变 split 或查看 test 来追分。',
        '即使预测改善，独立生物学重复、外部 ER+ 模型和功能性再挑战仍缺失，因此不能推断患者疗效或真正状态逆转。','',
        '## 原始来源','',
        '- https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE260703',
        '- https://pmc.ncbi.nlm.nih.gov/articles/PMC11723929/',
        '- https://github.com/Genentech/TraCSED',
        '- https://docs.scvi-tools.org/', '- https://cellrank.readthedocs.io/', '- https://pertpy.scverse.org/']
    (run/'final_report.md').write_text('\n'.join(lines)+'\n')
    (run/'ablation_report.md').write_text('# Eight Formal Ablations\n\n'+ '\n'.join(f'- {k}: OOF Spearman {v["validation_reward"]:.4f}; {v["interpretation"]}' for k,v in abl.items())+'\n')
    (run/'long_term_escape_report.md').write_text('# Long-Term Escape\n\n```json\n'+json.dumps(ras,indent=2)+'\n```\n')
    (run/'qc_report.md').write_text('# QC\n\nOriginal thresholds: detected genes >=500, mitochondrial fraction <=.25. Only single GFP barcode assignments enter clone endpoints. Raw unfiltered and QC-filtered AnnData are separate. See raw archive checksum, initial clone assignment audit, and confounding audit.\n')
    print(json.dumps({'whole_original_document_complete':whole,'missing_evidence':[k for k,v in coverage.items() if not v],'stats':stats}),flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--run-dir',type=Path,default=RUN)
    report(parser.parse_args().run_dir)
