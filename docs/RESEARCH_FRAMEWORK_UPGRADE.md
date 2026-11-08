# 通用研究 Harness 升级复盘

## 目标与边界

本次把 T47D 复盘揭示的问题转成通用研究机制，而不是给某个任务添加
专用模型或继续调整分数。保留原分支 `t47d-lineage-resistance-demo`。
不修改已经完成的 T47D 实验数据、标签、树、奖励、预测或结论。

代码通过测试，不等于复杂模型应当超过基线，更不等于已经证明跨任务有效。
当前改造区分：共享研究组件、分类任务执行适配器、冻结的历史任务实现。

## 逐项改造

| 问题 | 通用改造 | 实际边界 |
|---|---|---|
| 只保留基线名称，编码/缩放改变后仍当同一基线 | 执行配方包含配置、代码、输入与 artifact 内容 SHA256、环境、真实 epoch override；根节点注册 benchmark；显式历史基线不得静默遗漏 | 未声明的外部输入必须由任务适配器补入配方，不能仅凭模型名称证明复现 |
| 默认保留父模型并固定残差权重 | cookbook 允许替换、融合、联合、交叉拟合残差/stacking、简化与消融；加入开放候选；保留 agent 自写模型，不再模板覆盖 | 模型仍必须忠实实现其声明，不能将小模型冒充 foundation model |
| 用父模型训练集误差拟合残差 | 新增按独立组的 OOF 残差和嵌套交叉拟合权重；不足组数明确拒绝 | 当前共享实现针对连续回归；分类组合器不能直接套用类别编号 |
| 名称优先级与 held-out 指标影响搜索 | development-only 反馈；删除特定模型品牌加分；清除记忆与 parent summary 中的 test/confirmation 信息 | 不可信自由文本仍需要研究者审计，结构化过滤不能证明来源的真实性 |
| 方法覆盖消耗优化预算，滞留候选不重新判断 | 独立 coverage/optimization/confirmation 预算；每轮重新排序 global queue；选中时刷新研究阶段 | 原分类适配器仍采用其已登记的 validation Macro-F1 奖励，不伪装通用回归训练器 |
| 每个任务都被同一 epoch/维度限制 | 删除统一 epoch 下限、隐含维度/LR clamp；记录有效训练配置；训练充分性由任务协议规定 | 不声称所有优化器或训练算法已经预实现，Codex 可按任务扩展并登记执行配方 |
| 每节点训练后都查看 test | 搜索默认不构建/迭代 test loader；确认前冻结选择与权重校验和；确认只读原 checkpoint、禁止重训；输出隔离 | 已经暴露过的历史 test 永远不是新盲测；本次不重写历史暴露事实 |
| 零异常计数被当成科研成功 | acceptance 分为执行、协议、科学结论、归因、迁移；支持配对组 bootstrap 与分层诊断 | 真正的科学收益需要后续未用于开发的任务与等资源对照 |

## 执行链修复

- 回传只接受已训练的 development rollout，拒绝重复、非有限奖励与非法祖先路径。
- `train_pending` 的叶节点从零累计，避免重复初始化访问统计。
- 缺失 `data/dataset` 明确报错，不再隐式使用 synthetic。
- 新搜索先登记 `research_protocol.json`；禁止 reset 覆盖已有树；确认后禁止 resume。
- acquisition 调用传递当前任务与 registry，不再漏传参数。
- 空路径、空目录、仅含 `.gitattributes` 的目录不能被认定为可用 artifact。
- 已验证不可获取 artifact 的终态记录必须有来源核查与内容校验和；只阻塞相关候选。
- 尚未研究的 acquisition 仍需要当前 Codex 实时执行，不会自动伪装为已核查。
- 外部静态脚本不能证明开发集隔离时，不允许进入搜索；这属于比较缺口，不回退伪模型。
- 报表用 `withheld` 显示未开放的 test 指标，不把它写成 0。

## 文档所有权

1. `CODEX_AGENT_COOKBOOK.md`：通用不变量、Codex 主动权与研究闭环。
2. `docs/RESEARCH_PROTOCOL.md`：配方/基线/预算/反馈/确认的实际 API。
3. `docs/GENERIC_CELLLINE_TRANSFER_RUNBOOK.md`：分类适配器执行流程。
4. `docs/GENERIC_CELLLINE_TRANSFER_ACCEPTANCE.md`：分层验收，不用分数替代工程验收。
5. `ARTIFACT_ACQUISITION_RUNBOOK.md`：真实来源、构建/下载、核查、局部阻塞。
6. `OFFICIAL_K562_IMPLEMENTATION_LOOP.md`：K562 专属接口，不能反向约束其他任务。

旧实验文件保留作历史证据，不是新任务的政策来源。不要逐个删除历史产物，
也不要把旧实验的固定 `.25` 或 parent-preserving 测试当成新框架要求。

## 验证方法

所有验证均在 RunPod 上运行。只执行 CPU 单元/接口测试，不启动正式实验。
现有临时 CPU 实例只有约 512MB cgroup 内存；CUDA 版 PyTorch 测试曾被内核终止。
隔离安装 CPU 版后可以执行训练接口和旧任务神经网络回归测试，未更改正式环境。

```bash
python -m pip install --no-deps --target /tmp/research_torch_cpu \
  torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
PYTHONPATH=/tmp/research_torch_cpu:src \
VC_DEMO_FORCE_CPU=1 CUDA_VISIBLE_DEVICES='' \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
python -m pytest tests/harness/test_research_framework.py tests/t47d -q
```

测试包括：输入同大小内容改变、编码/缩放/代码/预算改变、历史基线缺失、
test poisoning 不改变反馈、确认选择/权重冻结、真实搜索不读取 test、确认不重训、
分组嵌套 OOF、agent 模型不被覆盖、真实 acquisition 参数、不可用资源局部阻塞、
非法/重复回传，以及原有 T47D 测试。

最终测试数量与结果保存在
`experiments/research_framework_upgrade_validation/validation_summary.json`。
测试内的小样本训练只是接口断言，不是新的 T47D 科研结果。

## 不应声称已经完成的验证

- 没有重新执行 T47D 正式搜索，也没有宣称修复后复杂模型必然超过历史 Ridge。
- 历史 T47D runner 保持原版本行为以保护可复现性；新实验若使用它，必须显式
  建立新版本任务适配器，接入共享 OOF/反馈/确认协议，而不是原目录直接 resume。
- 分类执行器不是自动支持所有任务的通用训练器。回归、纵向轨迹等仍需忠实的任务适配器。
- 尚未完成新的独立任务、等资源随机搜索对照、多次搜索复验和正式 artifact 归因。
- 共享规则不能增加独立 clone 数，也不能恢复已暴露 test 的盲性。

这轮交付是有负面测试与执行器验证的框架升级。后续应以冻结协议的新任务检验
这些机制是否真的改善研究效率，而不是继续给当前示例添加针对性的模型补丁。
