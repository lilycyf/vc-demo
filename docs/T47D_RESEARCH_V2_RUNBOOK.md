# T47D Provider v2：任务接入与工程验收

## 范围

本适配器把现有 T47D 任务接到 `scripts/run_research_harness.py`，不重新定义任务，
不改变通用搜索策略，不修改旧模型源码、旧树、奖励或冻结结果。K562 或 T47D
都不是通用框架的默认任务。本文不授权正式实验、资源扩容或延长计费。

先读 `CODEX_AGENT_COOKBOOK.md`、`docs/RESEARCH_PROTOCOL.md` 和
`docs/GENERIC_RESEARCH_RUNBOOK.md`。本文件只拥有 T47D 数据和 provider 接口。

## 不变的科学合同

- 来源 GSE260703；单位为 clone × treatment，三个 treatment 的行按 clone 分组。
- 输入仍是 day 0/1/4，标签仍是 day 26 相对克隆频率的平滑 log2 selection。
- 分母、至少 10 个基线细胞的资格规则、基因顺序和 Hallmark GMT 保持原合同。
- 原有 development/test 克隆划分及 5 seeds × 3 grouped OOF folds 原样转换，不重抽。
- 主指标 `spearman/maximize/mean_seed/clone_x_treatment/clone_id`，开发反馈共用此定义。
- 历史 test 已暴露：`prior_test_exposure=true`，新目录或新版本不能重置这一事实。
- 相对频率不等于绝对生长/杀伤；采样未检出不等于灭绝。这些解释边界不变。

## 仅准备数据：不会启动研究

在 RunPod 的仓库根目录，用一个全新的、ignored 的数据目录：

```bash
PYTHONPATH=src python scripts/t47d/prepare_research_v2.py \
  --prepared data/t47d_lineage/prepared \
  --pathways data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt \
  --historical-run experiments/t47d_research_protocol_formal_v3 \
  --baseline-tree experiments/t47d_lineage_resistance_demo/tree.json \
  --output-dir "$FRESH_PREPARATION_DIR"
```

准备器核验原 task/split，绑定源文件内容，导出独立的开发/确认 early arrays、
标签合同、feature schema 和 preparation manifest。开发 inputs 只有早期特征，
不包含确认特征、确认标签、day26 counts/fractions 或其他 endpoint metadata。
实际模型的 meta 只含 clone、treatment 和当前训练子集的 label，其他 label 置空。
组合模型另外保留同样训练子集遮蔽的 truth_meta，用于真实 selection 的辅助标签；
不能把残差响应的正负号误当作真实 selection 分类标签，也不泄漏外层验证标签。
原始来源中的公开 endpoint 不因为公开就自动成为可用输入。

此步骤 fit 次数为 0，不初始化 Session，不生成科学分数，不读旧分数做选模。
确认合同和任何原始数组都留在 ignored 数据目录，不提交到 GitHub。

可复核的真实来源工程预检（同样不初始化 Session、不拟合）：

```bash
PYTHONPATH=src python scripts/t47d/audit_provider_v2.py \
  --preparation-dir "$FRESH_PREPARATION_DIR" \
  --historical-run experiments/t47d_research_protocol_formal_v3 \
  --budget-guard /workspace/t47d_formal_budget_guard_state.json \
  --output "$ENGINEERING_REPORT_DIR/real_source_preflight.json"
```

预检独立重算标签公式，检查分组/特征/schema、六基线配方、已有 watchdog 和旧冻结
checksum；只输出聚合验收信息，不输出新科学分数或 raw arrays。watchdog 属于执行
环境，必须指向当前已授权的保护记录，不能复制本例文件名当作重新授权。

## 注册与实际执行

`vc_demo.t47d_provider_v2.registration.make_task_spec` 接收 preparation manifest，
必须由研究者显式提供 `budget/policy/resources/minimum_effect`，没有暗设的正式规模。
它冻结原六个基线：exact historical Ridge、frequency、Ridge、early ElasticNet、PLS、XGBoost。
historical Ridge 的类别编码、缩放、baseline-only 和 alpha 来自原始配方，不弱化。
注册环境和实际源码内容，而不只记录模型名字。原完整任务中的挑战/敏感性分析，
仍应在正式任务计划中显式注册；接入 provider 不表示这些分析自动迁移或已经执行。

只有在用户另行授权正式运行后，才将生成的 TaskSpec 交给共享 CLI `init`。
不要继续调用旧 `research_demo.py` 并声称它已经使用 v2。

当前 Codex 用共享 `context/propose/select/seal/execute` 循环提出、实现和运行候选。
`registration.implementation(config, preparation, ...)` 生成真实源码/输入/artifact
绑定，不负责生成研究假设、排序，也不会覆盖 agent 实现。

### 数据与模型接口

- `parameters.model_config` 是真实任务模型配置。
- `training.model_parameters` 可显式指定训练参数，冲突值会拒绝，不能悄悄覆盖。
- `training.seed_policy=registered_seed_or_explicit_replicate`。
- `training.confirmation_fit_policy=full_development_per_seed_before_freeze`：
  OOF 测量后在开发集为每个 seed 拟合正式预测模型，成本/拟合次数分开记录，
  保存到 ignored `RUN_DIR/nodes/`。确认不是临时重新训练，也不是暗换 fold ensemble。
- 默认桥接真实 `ResearchCandidate`；其历史 Ridge 原路径保持不变。
- 外层和内层拟合都只拿到其训练行标签；预处理、辅助标签和组合权重不得接触外层验证标签。
- `crossfit_stack` / `crossfit_residual` 必须显式给 parent config、inner_splits、
  combiner_alpha；使用真实 grouped OOF/nested OOF，返回实际 inner audit。
- 冻结预测只加载已保存模型、基因选择、投影和 scaler，按新 query 行重建早期特征。
  禁止 `fit`、scaler/PCA refit、校准 refit 或使用确认标签。

## Codex 的研究自由与重型路径

可使用 `implementation(..., model_builder=path, extra_code=..., artifacts=...)`。
`model_builder` 提供 `build_model(config, *, artifact_files)`；运行时路径从已封存的
`artifact_files` 注入，不把权重路径塞进科学参数或硬编码进模型。返回对象需要：

```python
fit(bundle, training_indices, seed)  # 返回实际拟合对象
predict(bundle, query_indices)      # 接受独立 query bundle，不拟合
# 可选 close()，用于将真实模型移到 CPU/释放 GPU，不销毁预测状态
# 拟合对象必须按真实使用报告 artifact_roles、module_roles；losses 可选
```

自定义类源码通过内容哈希导入并绑定 checkpoint，不被预置模板替换。
可提出新结构、替换、融合、联合、组合或简化，不强制保留 dense/root 分支。
额外 helper、依赖环境、权重和任务对齐也应完整封存。接口为可信代码审查边界，
不是能证明任意 Python 不越权读取数据的 OS 沙箱。

默认桥接可直接处理原有 pathway/expression/both/pseudobulk/PCA 等冻结可变换路径。
**旧 scVI/CellRank/distance/pseudotime 缓存不能冒充 frozen query encoder**。
新版默认桥接为这些路径提供真实训练折编码器、独立 query 变换、拟合 sidecar 和
内容核验。TraCSED 使用隔离 TensorFlow、固定作者 notebook 源码提取；hazard 使用
训练行限定的真实区间删失 AFT。没有用旧全行缓存、弱代理或随机输出替代。
专项配置、原文差异、挑战分析登记和验收边界见
`docs/T47D_HEAVY_PROVIDER_V2.md`。CPU 工程验收不等于 GPU 大规模运行或数值复现。

## 工程验收与交付

只使用 CPU 临时 fixtures 跑训练闭环；真实 T47D 只做源、合同、特征与注册预检。
工程 fixture 的小样本/少 seeds/少 steps 不能当成正式配置或科学结果。

```bash
CUDA_VISIBLE_DEVICES='' PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=src:. \
  OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
  python -m pytest tests/harness tests/t47d -q
```

验收检查：原基线数值实现一致；实际共享 CLI 的训练/反馈/冻结/确认；独立 query；
确认和外层验证标签 poisoning；fit 禁用后的预测；真实 nested OOF；agent 自定义模型；
内容漂移/行顺序/artifact 来源不符拒绝；resume 恰好一次；历史冻结文件完全未变。

报告分开写：真实数据合同已核验、CPU 路径已验收、未行使的重型模块、未运行的
正式基线重放/搜索/科学确认。不能以工程通过宣称复杂模型优于基线或旧全范围已迁移。
