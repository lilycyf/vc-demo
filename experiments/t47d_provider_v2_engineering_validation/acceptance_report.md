# T47D Provider v2 工程验收

**结论：主任务适配器与已列明路径工程验收通过；没有启动正式实验。**

## 做了什么

- 新增独立任务适配层，不修改通用策略、旧模型实现、旧搜索树或冻结结果。
- 实际使用共享入口 `scripts/run_research_harness.py`，不以旧 runner 冒充新版。
- 数据准备和研究执行分离；真实数据只做内容、任务/划分、标签公式和输入预检。
- 注册六个原基线的完整配方。历史 Ridge 的缩放/编码实现逐折与旧模型一致。
- OOF 测量、额外全开发集拟合和确认分开计数；确认只加载已冻结权重。
- Codex 可提交自己的 builder、融合/联合结构和真实 artifact，不受预置目录限制。

## 真实数据合同

| 项目 | 已核验值 |
|---|---:|
| 开发克隆 / 行 | 36 / 108 |
| 确认克隆 / 行 | 10 / 30 |
| Seed / 外层 OOF folds | 5 / 15 |
| 原基线配方 | 6 |
| 真实数据新拟合 / 新 Session | 0 / 0 |

主指标仍是每 seed 的 OOF Spearman 再平均，配对反馈使用同一 MetricSpec。
确认克隆历史暴露标记保持 true；不能称为新的盲测。

## 工程测试

- CPU 完整回归：141 passed，0 failed；其中新增任务适配器测试 26 项。
- 所有训练/得分闭环来自临时工程 fixtures，不是新 T47D 科学结果。

- exact historical Ridge fold predictions versus old implementation
- all six native baseline solver paths
- six standalone neural families, real CPU backward
- portable PCA/expression/pathway/both/pseudobulk/matched-control query transforms
- real grouped OOF stack and nested residual, actual inner audits
- separate residual targets and training-only true auxiliary labels
- agent-defined native model and feature fusion, not catalog replacement
- actual sealed artifact path injection and serialized use
- real shared CLI init/context/propose/select/seal/execute/freeze/confirm/report
- fresh-process provider execution and frozen checkpoint loading
- exactly-once execution/reward and cached confirmation
- validation/confirmation target poisoning and no-refit scaler/PCA checks
- row order/content/artifact-source mismatch rejection
- unused-pathway controls do not claim artifact consumption

## 保护与能力边界

- 原 T47D 配方、选择文件和全部登记权重 checksum 已再次核验未变。
- 原共享引擎和任务科学实现无改动；没有增加 GPU 训练、云资源或延长计费。
- 原始数据、合同标签、完整 OOF tables、拟合对象仅留 ignored 目录，不提交。
- 旧重型 fold cache 不等价于可移植 query encoder，不能据此宣称全部原模块已迁移。
- scVI/CellRank/distance/pseudotime、TraCSED/hazard 及旧挑战分析仍需忠实 builder/访问合同与专项验收。
- 这些是实现/验收工作，不是模型“公开不可获得”的证据；选中后 Codex 应实时处理。
- 复杂模型可靠胜过强基线、科学归因和框架迁移收益均未由本工程测试证明。

操作说明：`docs/T47D_RESEARCH_V2_RUNBOOK.md`。正式实验必须另获授权并登记实际范围和预算。
