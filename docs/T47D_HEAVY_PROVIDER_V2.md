# T47D 重型表示与挑战分析：v2 专项接入

## 范围与分层

本文补充 T47D_RESEARCH_V2_RUNBOOK，不授权正式运行、扩容或预算延期。
共享框架只新增可选 postselection 生命周期：计划内容绑定、冻结、独立预算、
结果隔离、收据恢复。原始细胞、基因、时间、删失和模型算法属于 T47D provider，
没有把 T47D/scVI/CellRank 变成通用任务的强制模块或结构上限。

新增文件在 `src/vc_demo/t47d_provider_v2/`；旧 t47d_research、t47d_full、
t47d_lineage 和历史结果不改写。所有工程训练数据为临时合成 fixture。

## 数据准备与输入访问

准备器原命令增加三个显式参数即可导出重型源，仍为零模型拟合：

```bash
PYTHONPATH=src python scripts/t47d/prepare_research_v2.py \
  --prepared data/t47d_lineage/prepared \
  --pathways data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt \
  --historical-run experiments/t47d_research_protocol_formal_v3 \
  --baseline-tree experiments/t47d_lineage_resistance_demo/tree.json \
  --output-dir "$FRESH_PREPARATION_DIR" --heavy-sources \
  --tracsed-notebook /workspace/_external/TraCSED/model_scripts/TraCSED_final_model.ipynb \
  --tensorflow-python /workspace/t47d_tf_venv/bin/python
```

- 分开导出开发/确认原始 early cells；仅 day0/1/4、原始 count、固定 gene_id 顺序。
- obs 只留 clone_id、treatment、time_day、library_id；不携带 endpoint/QC 派生标签。
- 当前训练 fold 的 clone/treatment/time 在拟合前再次过滤；HVG/PCA/scaler/图均 train-only。
- 查询只变换自己的 early cells，不读取全 cohort 行缓存，不进行 scArches/query adaptation。
- 普通模型拿不到额外事件表。hazard 或显式声明 training_event_policy 的 agent 模型，
  才可拿到实际训练行、所声明最大日的事件结局；不是对外层验证/确认 endpoint 的许可。
- postselection 原始分析源独立登记；开发期不据确认数据计算模型或排名。

## 实际算法与配置

复建环境用 `requirements-t47d-provider-v2-heavy.txt`（主指标/重型表示）与
`requirements-t47d-provider-v2-tensorflow.txt`（独立 TensorFlow），不要混装。
这是已测直接依赖版本，不是跨平台完整 CUDA/transitive lock；实际环境身份仍由
recipe 与 runtime identity 封存。旧 requirements-t47d-lineage 属于历史运行，
不能直接覆盖新版主环境。现有冻结 session 不允许用 pip 升级“修复”；新环境须复验。

| 路径 | 实际算法 | 拟合与查询边界 |
|---|---|---|
| scvi | scvi-tools SCVI，负二项似然 encoder | train-only HVG、batch registry、权重及训练 AnnData 持久化；query eval/latent mean，不训练 |
| pseudotime | Scanpy neighbors/diffmap/DPT | 基线中心 root、真实 DPT；训练 KNN 投影到独立 query；不伪称 query 重建了原图 |
| cellrank | CellRank RealTimeKernel + POT Sinkhorn 真实时间耦合 | train-only temporal kernels，核 cell ID 重排核验、边际/行随机/收敛检查；固定 KNN 描述符投影 |
| distance | pertpy energy/MMD、OTT 正则 transport、POT sliced Wasserstein | train-only PCA 与真实基线分布，query 分布到训练参考；OTT/Sinkhorn 不收敛即报错 |
| hazard | lifelines LogNormal AFT 区间删失 + 训练标签校准 head | 真实采样未检出区间、右删失；H(0)=0 精确边界避免 autograd NaN；不把未检出称灭绝 |
| tracsed | 作者 notebook AST 提取的实际 Keras 架构 | 隔离 runtime 身份、源码 hash、实际优化器/loss/LR/seed、权重持久化；冻结 query 禁 fit |

`representation_parameters` 显式开放真实算法参数，不硬编码小模型：HVG、PCA、neighbors、
DPT、SCVI 架构与 train 参数、OT regularization/iterations/tolerance/backend 等。
默认 SCVI hidden128/latent16/layers2、50 epochs、GPU，OT 默认 Torch CUDA。
工程 fixture 明确用 CPU、1 epoch、小样本，不修改正式默认或作为科学分数。
没有 CUDA 时，已声明 CUDA backend 不得静默降级。

未知 scVI batch 默认报错。研究者可在登记前显式选 `unknown_batch=reference_baseline`：
映射到训练基线 batch、冻结 encoder，仅为明确的非适应性外推政策，不冒充新 batch 优化。
组合外推时 CellRank 使用仅训练单药构建的 pooled 核；query 允许自己的组合早期观察，
但不能用组合训练标签/组合训练细胞构建 encoder。其他忠实方案仍可由 agent 实现并封存。

hazard 的 `hazard_max_fit_day` 可为1/4/8/26，保存实际 censoring audit。
day180 生存外推只是分析项，不是已验证的临床预测。左删失为(0,首次未检出日]，
右删失保持无穷上界；没有用任意 epsilon 事件时间替代真实区间。

## TraCSED 来源与复现边界

来源 https://github.com/Genentech/TraCSED ，本次工程锁定
`dc5a750ef6fc6adf50e362ba5c2d38bee6083289` 的 model_scripts/TraCSED_final_model.ipynb。
实际提取 build_model、transformer_encoder、lr_scheduler 和两个 dayiter splitter。
默认 head_size5、heads40、ff_dim5、声明 attention/transformer blocks10/10、MLP256、
dropout.14/.4、Adam.001、MSE、20epochs、batch32；实际配置写入 fit provenance。
import 的旧 author_Adam_0.001_MSE 描述经显式 canonical 转为真实 optimizer/loss，
不再出现声明 MSE 实际 Huber。显式 replicate seed 覆盖作者默认 seed 并记录。

保留原 notebook 的 inputs 重用与 channels_first pooling 等实际语义：声明10 blocks
不能宣称有效顺序深度就是10。early forecast 使用3个早期时点；作者 retrospective
reference 使用原 seq8/prefix-window/MinMax 语义，两者不可混为同一科学任务。
reference 跑 full/no_attention/no_feedforward/linear 的实际拟合，属于条码内部回顾分析，
不是未见克隆确认。本次未迁移/重跑旧 R 上游 pseudotime/作者完整预处理流水线；
已有代码不被本验收自动认证。没有作者原权重/同环境同数据时不声称数值复现。

## 十二类已接入挑战方法

| kind | 方法 | 访问/拟合说明 |
|---|---|---|
| loco | 全 cohort leave-one-clone-out | 必须 all_exposed_secondary，克隆严格留一；不是 primary test |
| monotherapy_to_combination | 只用单药训练，再预测确认组合 | encoder/标签皆去组合；固定未知 batch 政策 |
| late_interval | day8 response 训练到 day26 response | 辅助事件也裁至day8；只是 response transport，不伪称时间校准 |
| early_warning | 仅0、0/1、0/1/4输入截止 | 保留原 baseline-only 设定；positive cutoff仅描述，不造临床阈值 |
| ablations | 八种模块/输入/容量对照 | 实际未使用组件为 N/A；shuffle为固定基因置换保留集合大小及重叠 |
| last_snapshot | day4 snapshot 对照 | 开发 grouped OOF 重拟合，不用确认择优 |
| early_abundance | 早期丰度模型对照 | 开发 grouped OOF，独立报告 |
| denominator_null | 同治疗置换 endpoint fraction、保留 f0 | 仅开发标签，检查共享分母效应；非搜索校正 p 值 |
| biology_sensitivity | ER/E2F/EMT clone配对与epsilon敏感性 | 原始表达days1/4/8/26只用于事后描述；保留存活者偏差/非因果说明 |
| resistance_month6 | 预声明四分量描述评分与Month6命中 | 开发主预测用OOF；calibrator只fit开发；无heldout阳性时recall=None |
| secondary_metrics | AUROC/AUPRC/Brier、suppression、NDCG等 | logistic只fit开发OOF；不能用确认调阈值或选权重 |
| author_reference | 作者原seq8 splitter与4种模型 | 条码内回顾、显式重叠声明；独立来源/预算，不能混入主奖励 |

其中 ablations/last_snapshot/early_abundance/denominator_null 必须 development scope。
其余确认分析只能冻结后执行；full LOCO 必须承认历史暴露。所有统计是描述性，
未对自适应选模/多重比较提供新的确认性保证。单个组件无用、无显著增益都是合法结论。

## 登记与恢复

使用 `analysis_registration.register_analyses(task_spec, preparation, plans, directory)`，
或 `scripts/t47d/register_research_v2_analyses.py`。每个 plan 显式含 kind、settings、
data_scope、mode、fit_budget(model/calibration)、target_policy；作者 reference 另给
真实 source-backed reference_data 及 overlap=true。计划不运行分析、不初始化 Session。
公共层的 `plan-analysis` 允许开发期从当前 evidence 登记新问题；不得确认后再补为预注册。

冻结后共享 `analyze` 执行，真实 task-pipeline fit 逐个检查预算，内部 component 拟合
单独记账。预算不是 walltime/GPU硬保护，现有 watchdog 不得撤销或延期。
分析失败独立记录，不把科学节点改 failed，不回传奖励；已写 durable receipt 的恢复
核验文件后复用，不重复训练。权重/表达/逐克隆结果均保留 ignored nodes 目录。
fit_budget 的 scope 明确为 per_finalist：每个(analysis, finalist)单独分配，
计划总成本须据 finalist 数和内部 component 次数计算，不能把它当所有分析共享的总额。

## 验收与尚未证明

运行 tests/harness 与 tests/t47d，包括 actual scVI/CellRank/pertpy/OTT/lifelines/
隔离 TensorFlow CPU 拟合、保存/独立查询、禁fit、gene-order漂移、时间/标签隔离，
真实共享 Session 与 CLI、12类实际分析、N/A、分析预算和 durable receipt 恢复。
依赖或作者源缺失时不可把 skip 当通过。正式验收以聚合报告和当前源码内容为准。

真实 GSE数据只做导出、合同/来源/顺序/范围/历史冻结文件核验，拟合数为0。
未启动正式候选、搜索、GPU训练、科学确认或新实验；CPU合成测试不证明重型模型
优于历史强基线，也不证明真实规模GPU内存/收敛、作者数值复现或跨任务收益。

主要方法参考：
- https://docs.scvi-tools.org/en/stable/tutorials/notebooks/quick_start/api_overview.html
- https://cellrank.readthedocs.io/en/latest/api/_autosummary/kernels/cellrank.kernels.RealTimeKernel.html
- https://cellrank.readthedocs.io/en/stable/notebooks/tutorials/kernels/500_real_time.html
- https://lifelines.readthedocs.io/en/latest/fitters/regression/LogNormalAFTFitter.html
