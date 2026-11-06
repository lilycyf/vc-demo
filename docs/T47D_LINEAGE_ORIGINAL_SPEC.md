# H1-P2 公开数据完整 Demo：ER 降解剂与 CDK4/6 抑制剂能否阻止耐药吸引子形成？

> Sample question：在 ER+ T-47D 乳腺癌中，giredestrant 与 palbociclib 联合是否比任一单药更能抑制耐药克隆、削弱适应性耐药程序，并将细胞群维持在药物敏感状态？  
> Pipeline：`lineage_resolved_resistance_state_predictor`  
> Demo 类型：完全使用公开数据、公开代码和公开 Python 模型完成的 retrospective harness demo。  
> 预计执行时间：数据下载顺利时 3–7 天；不需要新增湿实验。  
> 边界：这是公开数据复现与模型搜索 demo，不是临床用药结论。

---

## 1. 为什么选择这个 sample question

前一个 EGFR/奥希替尼方案虽然生物学意义明确，但公开数据没有同时覆盖完整组合、单药、多时间点、克隆来源和功能性再挑战，因此难以只靠公开数据证明“状态逆转”而非“选择性杀伤”。

本方案使用的公开数据 `GSE260703` 同时具备：

- untreated baseline；
- giredestrant 单药；
- palbociclib 单药；
- giredestrant + palbociclib 联合；
- 1、4、8、26 天时间序列；
- 联合处理的 6 个月长期样本；
- 单细胞 RNA 表达；
- 与每个细胞关联的 TraCe-seq 克隆条码；
- 单药和联合处理下同一批起始克隆的选择结果。

这使我们可以区分：

1. **克隆选择**：某些预先存在的克隆在治疗后扩增；
2. **状态适应**：同一克隆在治疗过程中改变表达程序；
3. **联合抑制**：单药下耐药的克隆是否在组合中消失或转为负选择；
4. **长期逃逸**：联合处理 6 个月后是否仍出现少数逃逸克隆。

原研究报告：单药下耐药的克隆大多在联合处理下转为敏感，仅有一个克隆在长期联合处理中持续出现；ER、E2F 和 EMT 等程序与动态选择有关。[原论文](https://pmc.ncbi.nlm.nih.gov/articles/PMC11723929/)

因此，这个问题非常适合作为 harness 的真实闭环 demo：结果不是靠随机 cell split 预测，而是用克隆命运作为独立、可追踪的监督信号。

---

## 2. 公开资源清单

### 2.1 数据

| 资源 | 公开位置 | 内容 | Demo 中的作用 |
| --- | --- | --- | --- |
| GSE260703 | [NCBI GEO](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE260703) | T-47D 在 giredestrant、palbociclib、联合处理下的 TraCe-seq/scRNA-seq 时间序列 | 核心训练与评估数据 |
| Processed count matrix | GSE260703 supplementary files | 约 1.1 GB MTX，加 barcodes/features 文件 | 构建 AnnData |
| GFP/barcode matrix | GSE260703 supplementary files | 克隆条码相关矩阵 | 将细胞映射到 clone_id |
| Raw sequencing | BioProject `PRJNA1082726` / SRA | 原始 reads | 只有在需要从头重建 counts 时使用 |
| 论文与方法 | [npj Systems Biology and Applications](https://pmc.ncbi.nlm.nih.gov/articles/PMC11723929/) | 处理设计、克隆选择值、TraCSED 方法和结果 | 复现依据和验收参照 |

GEO 页面列出 18 个样本，并提供 processed matrix，因此第一版 demo 不需要从 FASTQ 重新比对。数据包含 baseline、单药与组合的多时间点以及联合长期样本。[GSE260703](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE260703)

### 2.2 公开模型与软件

| 模型/软件 | 公开位置 | 是否需要自己预训练 | 用途 |
| --- | --- | --- | --- |
| TraCSED | [Genentech/TraCSED](https://github.com/Genentech/TraCSED) | 需要在本数据上训练，但不需要外部 checkpoint | 原论文动态克隆选择模型 |
| Scanpy/AnnData | [Scanpy](https://scanpy.readthedocs.io/) | 否 | QC、标准化、PCA、邻居图、聚类 |
| scVI | [scvi-tools](https://docs.scvi-tools.org/en/latest/index.html) | 在本数据上训练，无需大型 checkpoint | 批次感知的单细胞 latent representation |
| CellRank | [CellRank](https://cellrank.readthedocs.io/en/stable/about/index.html) | 否 | 使用时间或 pseudotime 构建状态转移概率 |
| pertpy | [pertpy](https://pertpy.scverse.org/en/latest/api/tools_index.html) | 否 | E-distance、MMD、Wasserstein 等扰动分布距离 |
| Elastic Net / PLSR | scikit-learn | 否 | 低方差、可解释 root baseline |
| XGBoost | XGBoost | 否 | 非线性 tabular root |
| GRU/Temporal Transformer | PyTorch | 在本数据上训练 | 与 TraCSED 比较的动态模型 |

scVI 直接接收单细胞 count matrix，可学习 latent representation 并显式建模 batch covariate；官方接口提供训练和 latent 导出方法。[scvi-tools 文档](https://github.com/scverse/scvi-tools/blob/main/docs/user_guide/models/scvi.md?plain=1)

### 2.3 不需要的资源

本 demo 不依赖：

- scGPT、Geneformer 或 scFoundation checkpoint；
- 私有患者数据；
- 自建 foundation model；
- STRING_GNN 私有/不完整 checkpoint；
- 新的单细胞测序实验。

Reactome、PROGENy 或 Hallmark gene set 可以作为 source-backed pathway artifact，但必须记录版本和许可证。

---

## 3. 研究问题和可检验假设

### 3.1 主问题

> 对同一批起始克隆，giredestrant + palbociclib 联合是否比任一单药更有效地降低耐药克隆的 endpoint selection value，并抑制 ER、E2F、EMT 等适应性耐药程序？

### 3.2 三个子问题

1. **Innate resistance**：治疗前的表达状态能否预测哪些克隆会在第 26 天被正向选择？
2. **Adaptive resistance**：治疗过程中的哪些动态程序最早预示克隆最终耐药？
3. **Combination suppression**：单药下正向选择的克隆，在联合处理中是否转为负选择或消失？

### 3.3 主假设

- 单药下出现的 ER/E2F/EMT 适应性程序在联合处理中减弱；
- 联合处理的正向选择克隆数量和 selection value 低于两个单药；
- 使用时间序列与克隆信息的模型优于只看单一时间点的模型；
- 真实 pathway dynamics 能带来超过 matched-capacity no-artifact control 的增益。

### 3.4 可证伪条件

下列结果意味着主假设不成立或证据不足：

- 联合处理仅减少总细胞数，但耐药克隆的相对选择优势不下降；
- 模型仅在随机 cell split 上表现良好，在 heldout clone 上失效；
- pathway artifact 的增益被 matched-capacity control 完全解释；
- 不同随机种子或 clone-heldout folds 的结论方向不一致；
- 联合处理长期样本显示新的强逃逸克隆，而模型完全无法预警。

---

## 4. 预测单位和标签

### 4.1 预测单位

一行训练样本不是“一个随机细胞”，而是：

```text
clone_id × treatment × time/pseudotime interval
```

单细胞表达先用于构建 clone-time representation，再进入监督模型。这样避免把同一克隆的高度相关细胞拆到 train 和 test。

### 4.2 Endpoint selection value

对 clone `c` 和 treatment `d`：

```text
endpoint_selection_value(c, d)
= clone_fraction_at_day26(c, d) / clone_fraction_at_baseline(c)
```

实际实现使用 log2 变换并加预注册 pseudocount：

```text
log2_selection_value = log2((fraction_day26 + eps) / (fraction_day0 + eps))
```

标签：

- `positive_selected = 1`：selection value 高于预注册阈值；
- `negative_selected = 0`：clone 在终点显著下降或消失；
- 连续标签：`log2_selection_value`。

### 4.3 Combination rescue / suppression label

对同一 clone：

```text
combination_suppression
= max(selection_giredestrant, selection_palbociclib)
 - selection_combination
```

若单药下正向选择而联合下变为负选择，则标记：

```text
mono_resistant_combo_sensitive = 1
```

### 4.4 状态吸引子分数

公开数据不能直接证明临床意义上的“恢复药敏”，因此 demo 使用更严格的可观测定义：

```text
Resistance Attractor Score =
  0.40 × predicted clone selection
+ 0.25 × ER/E2F/EMT adaptive program
+ 0.20 × distance from negatively selected clones
+ 0.15 × persistence across late time points
```

权重仅在 train folds 内确定。最终 test fold 不能重新调权重。

---

## 5. 数据字段和数据合同

### 5.1 必须字段

| 字段 | 来源 | 说明 |
| --- | --- | --- |
| `cell_barcode` | count matrix | 单细胞 ID |
| `clone_id` | GFP/barcode matrix | 克隆身份；低置信度细胞标记 unknown |
| `treatment` | GEO sample metadata | DMSO、giredestrant、palbociclib、combination |
| `time_day` | GEO sample metadata | 1、4、8、26 天；组合另有长期样本 |
| `replicate_id` | GEO sample metadata | 生物/技术重复 |
| `library_id` | GEO sample metadata | 上机文库 |
| `raw_counts` | MTX | 基因 UMI counts |
| `gene_id` / `gene_symbol` | feature file | 必须冻结映射版本 |
| `qc_status` | 派生 | 细胞 QC 是否通过 |
| `clone_fraction` | 派生 | 每个 treatment-time 中 clone 比例 |
| `selection_value` | 派生 | 克隆选择标签 |
| `pathway_scores` | 派生 | ER、E2F、EMT 等程序 |

### 5.2 必须检查的数据问题

1. GEO sample title 与论文处理条件是否完全对应；
2. giredestrant 剂量在不同文字来源中如有差异，以 GEO sample metadata 和原始实验表为准，并在 audit 中记录；
3. barcode matrix 与 expression matrix 的列顺序是否一致；
4. clone assignment 是否存在多条码、低计数或碰撞；
5. replicate、time 和 treatment 是否被 library batch 混淆；
6. day 26 消失的 clone 是真实负选择还是采样不足；
7. 6 个月样本是否与早期样本具有可比较的批次和培养条件。

### 5.3 QC 规则

- 使用原论文阈值作为第一优先；
- 若需自行设定，记录 `min_genes`、`max_mito_fraction`、doublet 规则；
- clone assignment 必须设最低 barcode count 和相对优势阈值；
- 不可根据 test 标签调整 QC；
- 至少保留一个包含所有细胞和排除理由的 QC 表。

---

## 6. Train / validation / test 设计

### 6.1 核心原则

**按 clone 分组切分，不按 cell 随机切分。**

同一个 clone 的任何细胞都不能同时出现在 train 和 test。

### 6.2 推荐评估层级

| 层级 | Split | 用途 |
| --- | --- | --- |
| Level 1 | GroupKFold by clone | 基础模型选择 |
| Level 2 | Leave-one-clone-out | 检验对完全未见克隆的泛化 |
| Level 3 | Hold out late time interval | 检验是否能从早期预测终点 |
| Level 4 | Train on monotherapies, test combination | 检验组合外推；作为挑战任务，不作为唯一主结果 |
| Level 5 | 6-month combination sample locked test | 检验长期逃逸预警 |

由于满足足够细胞数的高质量 clone 数量有限，主报告应使用 repeated group cross-validation 和 bootstrap CI，而不是只报告单次 split。

---

## 7. 模型 search space

### 7.1 Root baselines

| Root | 输入 | 预测目标 | 必须保留的原因 |
| --- | --- | --- | --- |
| Clone frequency prior | baseline clone abundance | endpoint selection | 检查丰度本身能解释多少 |
| Mean/pathway baseline | baseline pathway score | endpoint selection | 最简单生物学基线 |
| Elastic Net | pseudobulk expression/pathway | 连续 selection value | 可解释、低方差 |
| PLSR | pathway features | selection value | 对齐原论文 innate resistance 分析 |
| XGBoost | clone-time tabular features | selection/class | 非线性 tabular root |

### 7.2 表征节点

| Blueprint | 输入 | 输出 |
| --- | --- | --- |
| `clone_pseudobulk_encoder` | clone × treatment × time counts | pseudobulk vector |
| `pca_state_encoder` | normalized expression | PCA latent |
| `scvi_state_encoder` | raw counts + batch | scVI latent |
| `hallmark_pathway_encoder` | gene expression + gene sets | ER/E2F/EMT 等 pathway scores |
| `distribution_distance_encoder` | clone/treatment cell distributions | E-distance/MMD/Wasserstein |
| `pseudotime_state_encoder` | longitudinal cells | pseudotime/trajectory position |

### 7.3 动态模型节点

| Blueprint | 说明 |
| --- | --- |
| `early_timepoint_elastic_net` | 只使用 day 1/4 预测 day 26 |
| `gru_clone_trajectory` | 对 clone 的时间序列表示建模 |
| `temporal_transformer` | 学习时间点间依赖和 treatment interaction |
| `tracsed_reference_backend` | 调用公开 TraCSED 代码，作为论文对齐候选 |
| `cellrank_time_kernel` | 用实验时间构建方向性状态转移概率 |
| `survival_or_hazard_head` | 将 clone 消失/持续视为事件过程 |

### 7.4 组合交互节点

| Blueprint | 作用 |
| --- | --- |
| `additive_monotherapy_baseline` | 组合响应 = 两单药简单加和 |
| `bilinear_treatment_interaction` | 学习 giredestrant × palbociclib 交互 |
| `gated_pathway_residual` | 保留强 dense parent，再加入 pathway residual |
| `cross_treatment_attention` | 比较同一 clone 在三种 treatment 下的状态 |
| `mixture_of_resistance_experts` | 分别建模 innate、adaptive、persistent resistance |

### 7.5 Heads 和 losses

```yaml
heads:
  - continuous_selection_regression
  - resistant_clone_classification
  - mono_resistant_combo_sensitive_classification
  - early_warning_ranking

losses:
  - huber
  - weighted_bce
  - focal_loss
  - pairwise_ranking_loss
  - multitask_selection_plus_pathway_loss
```

### 7.6 规模建议

第一版 manifest 可定义约 80–150 个结构组合，但不需要全部训练。Harness 每轮从 global proposal queue 选择最值得训练的 rollout：

- roots：5；
- representations：6；
- dynamics：6；
- interaction/fusion：5；
- heads/losses：8–12 种有效组合；
- 实际训练预算：20–40 个 selected rollouts。

---

## 8. Harness 执行流程

```text
下载并校验 GSE260703
    -> 构建 AnnData 与 clone assignment
    -> 冻结 task contract 和 grouped splits
    -> 训练 root baselines
    -> 生成 global proposal pool
    -> MCTS/全局队列选择一个 rollout
    -> artifact 检查
    -> materialize model.py
    -> compile + native smoke（仅接口检查）
    -> 正式训练
    -> validation reward
    -> trained-only backprop
    -> 继续生成/选择下一节点
    -> 预算或 no-improvement 停止
    -> locked test + ablation + final report
```

### 严格规则

- selected planned node 必须实时实现、训练或明确 skip；不保留“之后人工处理”的 pending；
- pruned proposal 不训练；
- smoke 只验证 shape/forward/backward，不计入科学结果；
- 不允许 compact/proxy/fallback 冒充原 blueprint；
- test clone 和长期样本不参与 selection；
- 只有 trained node 可以 backprop；
- 所有随机种子、split、artifact checksum 和 package version 写入 manifest。

---

## 9. 主要评判标准

### Primary endpoint

在 heldout clones 上预测 `log2 endpoint selection value`：

- Spearman correlation；
- MAE；
- bootstrap 95% CI。

### Secondary endpoints

| 指标 | 目的 |
| --- | --- |
| AUPRC | 识别少数正向选择耐药克隆 |
| AUROC | 辅助分类指标 |
| NDCG@K | 是否把最危险克隆排在前面 |
| Early-warning AUPRC | 仅用 day 1/4 预测 day 26 |
| Combination suppression accuracy | 是否正确识别单药耐药、组合敏感 clone |
| Long-term escape recall | 是否预警 6 个月逃逸 clone |
| Calibration error | 风险概率是否可信 |
| Best child vs best root delta | 搜索是否带来真实提升 |

### Demo 成功标准

1. 数据、clone mapping 和 splits 全部可复现；
2. 至少 5 个 root 和 5 类 child blueprint 可执行；
3. 至少 20 个 selected rollouts 正式训练；
4. best child 在 grouped validation 上超过 best root；
5. 早期时间点模型对 day 26 克隆选择优于 abundance-only baseline；
6. 联合处理的 clone suppression 方向与公开研究一致；
7. 结论在至少 5 个 seeds 或 repeated grouped folds 中稳定；
8. fallback、proxy、non-trained backprop、pruned training 均为 0。

如果 best child 未超过 root，demo 仍可完成，但必须输出 root-dominance audit，不能把流程成功写成模型成功。

---

## 10. 必做消融

| 消融 | 回答的问题 |
| --- | --- |
| No clone barcode | 克隆信息是否真的重要？ |
| Baseline only | 治疗前状态能预测多少 innate resistance？ |
| No temporal dynamics | 时间序列是否优于终点快照？ |
| No pathway artifact | ER/E2F/EMT pathway 是否贡献增益？ |
| Shuffled pathway membership | 增益是否来自真实生物结构？ |
| Matched-capacity no-artifact | 增益是否只是参数量？ |
| No treatment interaction | 模型是否真正学习组合而非单药平均？ |
| No dense parent | pathway/dynamic branch 能否独立工作？ |

---

## 11. 从零执行步骤

### Phase 1：数据准备（0.5–1 天）

1. 下载 GSE260703 processed MTX、barcodes、features 和 GFP/barcode files。
2. 保存 URL、文件大小、SHA256、下载日期。
3. 读取 GEO sample metadata，生成 `sample_manifest.csv`。
4. 构建 `raw_counts.h5ad`，不提交大数据到 GitHub。
5. 将 artifact 放到持久化 volume 或对象存储。

### Phase 2：QC 与克隆映射（0.5–1 天）

1. 复现论文 QC；
2. 从 GFP/barcode matrix 分配 clone_id；
3. 输出 clone × treatment × time 的细胞数表；
4. 标记低覆盖 clone；
5. 冻结 grouped split。

### Phase 3：参考复现（1 天）

1. 计算 clone endpoint selection value；
2. 复现 positive/negative selected clones；
3. 复现 ER、E2F、EMT pathway trends；
4. 运行原论文 PLSR 与 TraCSED；
5. 记录与论文图表/统计方向是否一致。

### Phase 4：Harness search（1–3 天）

1. 跑 roots；
2. 用 validation reward 搜索 representation、dynamic、interaction 和 head；
3. 每个 selected rollout 当场完成实现和训练；
4. 跑到训练预算、no-improvement 或明确 blocker；
5. 不因某一个 blocker 停止整个队列。

### Phase 5：Locked test 与报告（0.5–1 天）

1. 冻结 best pipeline；
2. 解锁 heldout clones 和 6-month sample；
3. 完成所有消融；
4. 输出模型、克隆和 pathway 层面的解释；
5. 生成下一实验建议，但不把 retrospective 结果写成临床结论。

---

## 12. 预期输出文件

```text
experiments/t47d_lineage_resistance_demo/
  task_contract.json
  sample_manifest.csv
  artifact_registry.json
  artifact_acquisition_report.md
  qc_report.md
  clone_assignment_audit.json
  grouped_splits.json
  search_space_manifest.json
  root_metrics.json
  tree.json
  mcts_trace.jsonl
  selected_rollouts.jsonl
  ablation_report.md
  long_term_escape_report.md
  final_report.md
```

GitHub 只提交代码、配置、轻量 metadata 和报告；不提交 MTX、h5ad、checkpoint 或大模型权重。

---

## 13. 这个 demo 能回答什么，不能回答什么

### 能回答

- 单药下哪些起始克隆更可能产生耐药；
- 哪些转录程序在耐药形成前出现；
- 联合处理是否压制单药耐药克隆及其适应程序；
- 哪种公开模型 pipeline 最能从早期状态预测晚期克隆选择；
- 克隆、时间和 pathway artifact 各自贡献多少。

### 不能回答

- 该组合是否对患者临床有效；
- 是否适用于其他 ER+ 细胞系或患者；
- 是否具有足够治疗窗和安全性；
- 是否真正把单个细胞“转化”为敏感细胞，而非清除耐药克隆；
- 是否存在公开数据之外的替代耐药机制。

要升级到 prospective 研究，下一步应在独立 ER+ 细胞系或 PDO 中，用相同 treatment/time design 前瞻采集 lineage-resolved 单细胞数据。

---

## 14. 最终判断

这是目前最适合完整完成的公开数据 demo 之一，因为它同时提供：

```text
真实单药与组合
+ 多时间点
+ 单细胞表达
+ 克隆条码
+ 长期逃逸样本
+ 公开原论文模型代码
+ 可执行的现代开源模型替代项
```

因此，demo 不需要伪造 foundation artifact，也不需要新增测序，就可以完整跑通：

```text
公开数据 acquisition
-> lineage-aware task contract
-> root baselines
-> paper model + expanded search space
-> selected-rollout search
-> clone-heldout evaluation
-> ablation
-> long-term escape audit
-> final report
```

它比单纯预测药物 synergy 更接近“耐药吸引子”问题，也比没有克隆信息的单细胞数据更能区分预存选择和适应性状态变化。

