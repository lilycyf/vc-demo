# 通用研究框架 v2 升级与验证

## 目标与边界

将复盘中的指标不一致、覆盖污染搜索、候选路径不可达、成本符号反转和
数量型验收问题转为通用可执行合同。新代码位于 `harness/research_v2/`，
实际入口为 `scripts/run_research_harness.py`，不修改任何任务模型或已冻结结果。

这不是新的科研实验，也不承诺复杂模型一定获胜。只运行临时目录中的 CPU
工程 fixtures、负面测试和既有回归测试；模型数据与结果不冒充真实任务证据。

## 已实现机制

| 根因 | v2 机制 | 验证方式 |
|---|---|---|
| 指标名称相同，聚合量不同 | MetricSpec绑定单位、方向、seed聚合、类别词表和自定义scorer内容；配对反馈直接复用同一score | 聚合顺序导致正负反转的固定样例；混用metric_id拒绝 |
| 覆盖消耗优化额度/Q | benchmark/coverage仅建立comparison关系；own score与optimization visits/value分离 | 超过原始children数量的覆盖仍不排除强root；覆盖不能回传 |
| 开放组合仅停留在API | 当前Codex通过真实共享CLI提供假设、provider及封存配方；无family/modulo门槛 | 回归/分类完整CLI流程；真实分组OOF residual/stacking执行与内层audit |
| 存在品牌/可用性隐式加分 | 排序只接收有理由的增益、不确定性和分解成本；可修订队列估计 | artifact-present不改变priority；新snapshot约束estimate修订 |
| 负增益除成本反转 | 显式UCB式研究效用减成本，不将负值除以成本 | 正/零/负gain下成本单调测试 |
| 重复node当新结构 | 位置无关semantic identity，独立measurement/replicate identity | 相同代码换目录复用证据；训练预算/代码内容变化区分 |
| 单节点处理完就停 | phase状态机、每次优化后补池要求、明确skip/repair/真实exhaustion | 多轮执行、队列继续、pruned不可训练、freeze预算检查 |
| 模块未用也算消融成功 | 通用control_verdict，unused为not_applicable | 依赖移除未施加与真实N/A区分，不要求分数必降 |
| 训练后test参与下一轮 | confirmation单独接口和权重锁；研究snapshot无确认结果 | test poisoning、predict-only和不可重新选择测试 |
| cookbook与执行分离 | 新运行使用共享入口；旧分类执行须显式历史resume | 新旧入口guard与真实CLI集成测试 |

## 研究主动性

目录不是模型宇宙上限，父模型不是强制dense分支。Codex可以定义新模型、
替换、联合、融合、OOF组合或简化，并记录针对开发集失效的理由与对照。
选中后的合理设计改进允许通过actual recipe和revision reason封存。

没有预置内部Codex API。当前Codex消费next_action并当场研究、实施、repair、
acquire或透明skip；CLI工作边界不是“之后再处理”的科学停止理由。
UCT当前是父节点建议调度，不冒充完整论文树下降算法；有理由的研究者覆盖
建议会留下记录。其他队列策略是明确注册的不同策略。

## 不应误读的能力边界

- provider是可信、可审查代码，不是OS沙箱；分组audit和role自报需要真实源代码、
  poisoning/不变性与native loader测试支持，不能证明任意恶意Python不读取标签。
- 新共享入口能驱动provider，不等于所有历史任务已被自动转换成v2。新任务必须
  实现忠实接口和实际数据/metric合同，不得通过旧runner伪称完成迁移。
- 条件性OOF bootstrap不是独立确认或多重搜索选择校正；开发集promotion support
  不等于已经证明可迁移的科学收益。
- 分解成本排序仍是登记的可解释启发式，不声称Bayesian最优或完整MCTS复现。
- session在动作边界检查deadline；硬计费上限仍需独立执行/云资源watchdog。
- 本次没有运行新科研任务、等资源随机搜索对照或未见任务验证。

## 文档所有权

Cookbook只保留通用边界/研究自由；RESEARCH_PROTOCOL规定代码合同；
GENERIC_RESEARCH_RUNBOOK规定实际工具循环；分类runbook只负责分类provider；
acceptance区分执行、协议、能力、归因、科学和迁移；acquisition runbook不再
内置某个demo或模型品牌优先级；短prompt只给任务、分支、目录和资源授权。

旧协议代码与历史复盘保留版本身份，不按新规则重写既有树、奖励或确认结果。
旧分类入口不再允许无声明启动新的v1科学运行；仅显式历史开放run的resume。

## 验证记录

具体测试命令、数量、结果、冻结结果保护及staged检查记录于
`experiments/research_framework_v2_validation/validation_summary.json`。
该目录是工程验收记录，不是新科研实验。

下一步只能在用户授权后开展新的实际provider验收或科学实验；框架优越性还需
等资源random/simple-policy对照及未用于框架开发的任务，不能靠继续调同一个demo。
