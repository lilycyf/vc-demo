# T47D 新框架重型路径专项工程验收

## 结论

专项工程验收通过：160 个 CPU 回归测试，0 failed、0 skipped。
这不是正式实验；真实 T47D 上模型拟合为0，没有新科学分数或模型优越性结论。
旧源码/选择/checkpoint 的内容核验通过，原自动停止保护未修改。

## 实际接入

真实 scVI、Scanpy DPT、CellRank temporal kernels、pertpy/OTT/POT 距离表示均有
训练折拟合、持久化、独立 query 和冻结不拟合路径。TraCSED 使用固定作者 notebook
实际架构及回顾 splitter 的隔离 TensorFlow 运行时，hazard 使用实际区间删失 AFT。
scVI/CellRank 走真实共享 Session，重型表示后的 neural head 完成真实反向传播。
没有用旧 cohort 行缓存、随机输出或 compact/proxy 替代这些模块。

| 工程证据 | 结果 |
|---|---|
| `scvi_actual_library` | passed |
| `cellrank_actual_kernel` | passed |
| `dpt_actual_library` | passed |
| `pertpy_ott_actual_distances` | passed |
| `train_only_and_gene_vocabulary` | passed |
| `scvi_explicit_unknown_batch` | passed |
| `actual_interval_aft` | passed |
| `author_tracsed_source_and_seed` | passed |
| `scvi_shared_session` | passed |
| `cellrank_shared_session` | passed |
| `heavy_neural_backward_and_query` | passed |
| `all_twelve_shared_cli_analyses` | passed |
| `analysis_exactly_once_receipt_recovery` | passed |
| `analysis_primary_reward_isolation` | passed |
| `analysis_frozen_source_drift` | passed |

## 分析接入与隔离

以下12类方法通过真实共享 CLI 在合成工程数据上执行，不是只登记名称：
- `ablations`
- `author_reference`
- `biology_sensitivity`
- `denominator_null`
- `early_abundance`
- `early_warning`
- `last_snapshot`
- `late_interval`
- `loco`
- `monotherapy_to_combination`
- `resistance_month6`
- `secondary_metrics`

计划可从开发证据登记，冻结后方法/输入/源码/预算不可静默改变。
主确认只预测；预声明挑战的模型/校准重拟合有独立 per-finalist 预算和访问审计，
内部 component 工作另记。分析结果不进入排序、奖励、visits/Q 或主拟合预算。
durable receipt 写入后的中断恢复不重复拟合；此前崩溃的工作仍须按失败尝试记录。
组件没有被使用时 N/A；没有 eligible heldout Month6 阳性时 recall 为未定义，
不伪造0分。动态加载后的分析预测与主确认的逐行预测一致性也已验收。

## 真实数据零拟合预检

- 开发：36 clones / 14784 early cells。
- 确认：10 clones / 5009 early cells。
- 基因数：58302，固定 gene_id 顺序；只导出 day0/1/4。
- 额外训练事件：401 rows，只含开发克隆、days1/4/8/26；实际每次 fit 再裁训练行/声明 horizon。
- 原6基线完整配方、108/30任务行、5seeds×3folds、原标签公式和历史暴露标记保持不变。
- 真实数据没有初始化新 Session，没有训练新候选或跑正式搜索。

## 工程中修复的问题

1. 动态内容哈希导入下的相对 import 失败，改为稳定入口导入。
2. 动态类与常规导入类身份不同，分析 query 可能未真正替换原训练 bundle；
   新增对象自有 query rebind 接口及逐行一致性测试，防止旧行复用。
3. AFT 对左端点0的 autograd 数值边界：使用精确 H(0)=0，不用假时间替换删失区间。
4. H5ad nullable string 源注释不能安全导出：仅保留必要 obs 和基因身份，固定串类型。
5. CPU fixture 的 scVI 无验证集配置需要显式关闭 Lightning 验证循环，正式默认不变。
6. OT 必须核验真实收敛、边际、kernel cell order 和行随机性，不以有限输出冒充成功。
7. TraCSED 实际 optimizer/loss/seed 明确，隔离环境不污染主指标环境。

## 边界与下一步

GPU真实规模内存/收敛尚未验证；合成 CPU 测试不能替代正式科学运行。
作者原 R 上游完整预处理没有在本次迁移/重跑；固定源码架构不等于论文数值复现。
已暴露的确认克隆仍然暴露。描述性 LOCO/回顾窗口/Month6 外推不是新的独立确认，
也不保证复杂模型超过强基线。可信代码审查和访问测试不是 OS 沙箱。

下一步需用户另行授权正式范围与计算预算后，登记新的完整 TaskSpec/analysis plans，
再运行基线、覆盖/优化、冻结、确认和计划内挑战。本交付不自动启动该步骤。
详细方法、来源和复建边界见 docs/T47D_HEAVY_PROVIDER_V2.md。
