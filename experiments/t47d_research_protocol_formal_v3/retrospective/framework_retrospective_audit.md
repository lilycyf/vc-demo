# T47D 正式实验 v3：框架复盘与改造建议

## 1. 结论与边界

这次实验证明了可执行性、完整范围交付和若干科学边界约束，但没有证明复杂模型稳定优于完整强基线，也没有证明 MCTS 优于等预算的简单搜索。

更重要的是：实际执行路径还存在评价口径、覆盖与优化状态隔离、候选生成、成本排序和语义验收的问题。不能把结果简单归结为“数据太少”“模型太复杂”或“还需要更多 epochs”。

审计基于完成时提交 `e0a06c6` 的代码、原始 OOF 预测、冻结测试预测、搜索树和 trace。没有修改原始奖励、模型选择、确认锁或训练结果；没有重新训练模型，也没有启动新实验。

新增计算见 `framework_audit_evidence.json`，可用同目录 `recompute_evidence.py` 复算。所有新增统计均为事后描述，不得回流本轮搜索。

## 2. 真正完成了什么

| 项目 | 实际完成 | 可以支持的结论 |
|---|---:|---|
| 强基线 | 6 个，包括历史 Ridge 完整配方 | 没有用改变编码的弱 Ridge 冒充历史参照 |
| 覆盖候选 | 26 个 | 指定模块可以在实际数据上训练 |
| 优化 rollout | 40 个 | 全局队列能选择、训练、回传并继续生成候选 |
| 正式 CV | 每节点 5 seeds × 3 clone folds | 对同一开发数据进行重复分组评价，不是15份独立证据 |
| 消融 | 8 项，另有 snapshot/abundance/null controls | 文件和训练均完成；是否具有归因效力仍须逐项判断 |
| LOCO | root/child 各46次 | 固定模型选择后的次要诊断，不是新的独立确认 |
| 公开参考 | R 预处理及464条TF/线性评价记录，29个有效barcode-treatment条目 | 公开数据重建实际执行；不等于私有 signature 数值复现 |
| 其他阶段 | 跨treatment、预测时距、早期预警、长期生物学 | 均有输出，但不能自动推出因果逆转或临床疗效 |
| 运行保护 | 无训练失败、fallback、proxy、非训练回传；主要确认零重训 | 必要的执行边界成立，不是性能优越性的证明 |

原始 `complete_scope=true` 是文件存在与预算计数检查。它不等于“统计获益成立”“每项消融有效”或“框架能力已在该运行中全部验证”。

## 3. 科学结果与证据强度

### 3.1 结果不是搜索优化成功

| 方法 | 开发集平均seed-level OOF Spearman | 冻结测试集ensemble Spearman | 冻结测试MAE |
|---|---:|---:|---:|
| 历史强 Ridge | 0.571480 | 0.489487 | 2.200448 |
| 覆盖阶段 CellRank + gated | 0.591806 | 0.283013 | 2.397227 |
| 40个优化rollout中的最佳候选 | 0.555864 | 未作为主要确认候选评价 | 未评价 |

最后选中的复杂模型来自预先列出的 coverage，不是40个优化rollout找出的改进。新增优化阶段没有超过完整强基线，也没有超过覆盖阶段最佳。

### 3.2 不能把小幅开发集增益视为可靠提升

开发集只有36个独立clone；每个三折训练集约24个clone。三个treatment产生更多行，但不是更多独立生物样本。测试集只有10个独立clone、30行。

候选在五个CV seed中4次高于root，平均增益为 `+0.020326`。用同一主指标、完整clone块重采样、固定已归档OOF预测计算的条件性95%区间为 `[-0.148147, 0.189077]`。

冻结测试的点估计差为 `-0.206475`，事后配对clone bootstrap区间为 `[-0.522290, 0.148347]`。因此可以说测试点估计明显下降，但不能凭这10个clone宣称复杂模型已被统计上证明更差。

上述区间只描述固定预测的组抽样不确定性；没有重新拟合整个pipeline，没有校正自适应挑选最佳模型，也不产生新盲测。历史test已经暴露，重开branch或换seed不能改变这一事实。

### 3.3 其他结果与“没有可靠优越性”一致

- LOCO pooled Spearman：Ridge `0.545878`，复杂候选 `0.501684`；区间有较大重叠。复杂候选MAE略低，说明不同目标存在权衡，不是全面占优。
- 仅早期丰度等变量的基线已有 `0.560915` 开发集Spearman。复杂表征必须证明有条件增量，而不是只优于一个弱小模型。
- 分母耦合null诊断均值为 `0.207337`，最大一次约 `0.477047`。这提示比值标签包含可预测的统计结构，但不能据此把Ridge全部表现解释为伪信号；该null不是经过模型选择校正的确认性p值。
- 冻结测试中，复杂候选对两个monotherapy的排序更弱，对combination排序有所改善。总体相关系数不能替代业务问题的分组评价，也不能事后更换主指标来宣布胜利。
- Month6锁定测试中没有合格阳性clone，未见clone逃逸recall不可定义。描述性recall@5=1不构成前瞻成功。

## 4. 根因一：奖励与反馈不是同一个统计目标

证据：`src/vc_demo/t47d_research/study.py:148-159` 先按row平均多个seed预测，再调用 `paired_feedback`。正式奖励则先对每个seed的完整OOF预测算Spearman，再平均五个分数。

```text
奖励：mean_seed[Spearman(y, prediction_seed)]
反馈：Spearman(y, mean_seed[prediction_seed])
```

Spearman是非线性的，两个量不必相同。本轮同一候选因此得到相反方向的增益：

| 口径 | Root | Child | Delta |
|---|---:|---:|---:|
| 正式奖励：平均seed级OOF相关 | 0.571480 | 0.591806 | +0.020326 |
| 实际反馈：先ensemble再相关 | 0.621110 | 0.605627 | -0.015483 |

这不是浮点误差：选冠军与估计科学优先级在优化不同的量。ensemble指标本身合法，但只能以不同metric identity作为次要指标，不应无声明地替换主指标的delta。

**通用改造：** 引入可执行 `MetricSpec`，包含预测单位、独立组、跨fold/seed聚合顺序、方向和重采样单位。奖励、配对delta、排序、停止与promotion必须验证同一metric ID。保存 `[row, seed, fold]` 预测表，不在反馈入口提前丢失seed维度。

**验收：** 用相关聚合会反转的固定样例测试；主奖励减baseline必须等于主指标配对delta。次要ensemble结果可以不同，但须显式命名，不能参与主指标排序。

## 5. 根因二：覆盖预算隔离了，搜索状态却没有隔离

证据：`study.py:278-297` 将26个覆盖节点全部挂到 `root_historical_exact_ridge`，并把它们的奖励回传到该root。`generate()`用硬编码 `max_children=20`；共享 `mcts.py:61-70` 按所有children的长度过滤父节点。

实际结果：

- 优化开始前，强root已拥有26个children，超过20上限。
- 第一次parent-selection的候选中就没有强root。
- 40次优化parent-selection中，强root被选中 **0次**。
- coverage还改变了它的visits与subtree-Q，而不只是扩展额度。

所以“优化没有沿最强baseline有效研究”不完全是随机性。这是明确的控制流问题：覆盖统计把一个科学上应可继续研究的候选挤出了父节点集合。

**通用改造：** baseline comparison、coverage association与optimization lineage使用不同edge type。分开own score、coverage observations、optimization visits与subtree-Q；覆盖关系不能消耗优化扩展额度。剪枝/未选候选不应永久耗尽有效扩展能力，可采用注册的progressive widening。

**验收：** 给强root挂载超过上限的coverage records后，它仍能参与优化扩展；新增coverage不改变optimization-Q。共享库不能只看到无类型的children列表，task adapter也不能隐式写死20。

## 6. 根因三：实际候选生成仍是固定目录采样，不是充分开放的研究循环

`study.py:189-228` 的实际路径是打乱manifest，随机设置hidden/epochs/lr，再生成4个候选。多数config与选中的parent没有计算或研究假设上的对应关系。

本轮160个新proposal全部为 `composition=replace`，40个训练的优化候选也全部是replace。代码虽然支持OOF residual/stacking，但生成门槛仅对“cheap model + cheap parent + iteration取模”开放。本次根本没有走到这些路径。

因此应纠正之前的表述：**共享组合API存在并通过测试，不等于本次正式搜索已经使用了开放组合。** 我实现的T47D adapter没有把cookbook赋予Codex的主动研究能力完整接入真实执行路径，这属于框架实现责任。

独立替换不是错误，也不应强迫每个child继承root。但如果父节点选择不影响提案分布，随机目录候选的结果却按任意parent回传，那么树形关系并不能证明真正的MCTS模型工程搜索。

另外，`research_hypothesis.json`主要是“Test {config}”模板，evidence refs统一指向持续覆盖写入的 `development_feedback.json`。这不足以复原每次决策当时看到的证据，更不足以证明agent基于残差、失效模式提出了新结构。

**通用改造：** 由共享runner向当前Codex提供不可变研究上下文和可调用工具：强baseline完整配方、父节点证据、成对误差、已试/失败假设、实际artifact合同、剩余预算。Codex可以提出manifest外的新方案、简化方案或说明无需复杂化；实现、repair和acquisition仍在当前Codex会话实时完成，不需要内置Codex API。

每个提案应写明针对的失效模式、具体改动、预期增量、可证伪对照和快照hash。replacement、feature fusion、joint、OOF residual/stacking都按合同开放，不能靠廉价模型名单和取模限制可达性。

研究上下文边、计算依赖边与搜索回传边必须分清。要么建立真正具有条件行动语义的树搜索，要么诚实提供flat/contextual-bandit queue模式；不能只因JSON呈树形就宣称论文式搜索能力。

**验收：** 声明能力有可达性测试，真实集成测试能走到组合与agent-defined路径；不要求每次真实实验强制使用所有组合。一个“不需要复杂模型”的任务应允许最终保留root。

## 7. 根因四：科学排序过于粗糙，且成本公式有符号风险

`priority()`仅按model family聚合历史gain与cost，把同一family内不同representation、loss、composition和训练预算混在一起。它使用配置间delta的标准差作为uncertainty，再随候选数量缩小；这不是clone抽样不确定性，也不是校准的学习后验。

本轮最优覆盖候选使用CellRank；优化阶段没有训练任何CellRank候选。生成的4个CellRank候选全部变成 `pruned_not_selected`。这说明“覆盖找到有希望的模块”没有有效转化成后续可检验的研究计划。它不证明继续CellRank必然更好，但证明当前搜索没有充分检验这个方向。

共享排序分数为 `(gain + uncertainty) / sqrt(cost)`。如果分子为负，更高成本反而让分数更接近0、排序更靠前。例如 `-0.1/sqrt(1)=-0.1`，而 `-0.1/sqrt(100)=-0.01`。本轮40次选择中34次priority为负，因此该风险并非完全无关的边界情形；但不能未经反事实实验就断言34次均因成本反转而入选。

**通用改造：** 以模型、representation、composition、parent关系、loss与数据制度联合建模，并在稀疏证据下分层收缩。区分数据不确定性、训练随机性、搜索未知性与选择乐观偏差。调度使用可解释、经测试的非负expected improvement/value-of-information或明确成本惩罚，不靠负值除成本隐式改变偏好。

成本需拆为acquisition、cache miss、训练、评价；artifact已存在不构成科学加分，可复用缓存只影响预计成本。保留有理由的探索额度，而不是保证某个模型品牌必须得到名额。

**验收：** 其他输入固定时，纯增大成本不能提高同一候选的利用优先级；一个representation成功、同family其他representation失败时，不能无条件把整个family判坏。用等预算policy ablation评估改进，不回写本轮搜索。

## 8. 根因五：完整性验收和去重仍偏向记录数量

72个训练节点只有66个完全不同的声明config，存在6组重复；按相同15折合同，约90次fit属于重复配置预算，除非有另行登记的replicate目的。部分重复在coverage内部，部分出现在coverage与optimization之间。

现有recipe很好地保存执行位置与来源，但不同node目录会导致不同身份。应另设位置无关的semantic candidate identity，不能用node ID表示科学新颖性；同时保留有明确新seed/目的的正式replicate。

选中模型本身不消费Hallmark通路作为主要表征，loss也是Huber；其 `no_pathway` 与 `shuffled_gene_memberships` 分数完全不变是合理的“不适用/未消费”信号，不是通路功能验证通过。`no_dense_parent_branch`在replace模型里主要移除内部dense支路，不能据此声称验证了“继承强root”的贡献。

**通用改造：** 将 `complete_scope`拆成执行、协议、能力路径、artifact实际消费、归因、科学收益和跨任务可迁移性等独立结论。消融合同依据实际依赖图生成，结果允许 `not_applicable`；记录改动是否确实进入forward/loss、输入维度与是否读取artifact。必须区分“不需要该模块”“模块无效”“对照没有施加成功”。

**验收：** 重复config不能伪装成新结构；未登记replicate不得重复耗费正式预算。移除未消费artifact返回N/A；移除已消费组件有可验证的依赖变化，但不强求分数必须下降。

## 9. 根因六：缺少从研究候选到可靠替代的证据门槛

本轮保存了 `promotion_supported=false`，但最终选择仍只是按点估计挑best child。把它作为研究finalist进行预登记确认可以接受；把它自动视作优于root的推荐替代则不可以。

同时，当前归档没有系统保存每个神经候选的收敛曲线、训练/内层验证差、有效自由度、梯度和适当学习曲线。不能只根据结果把失败确定归因于epochs不足、过拟合或某个正则化系数。

**通用改造：** 分开 `best_observed_candidate`、`confirmation_finalist`、`promotion_supported`和 `retained_baseline`。最小实用效应、组级不确定性、稳定性、成本与必要分组约束应在看确认结果前登记。没有充分证据时保留强baseline是正确研究结论，不是runner需要绕过的失败。

训练诊断由模型provider统一导出；早停、调参使用训练内的分组数据，不能用外层评价fold挑checkpoint后仍称无偏OOF。允许不同模型使用合理、真实记录的算法与预算，而非统一epoch下限。

## 10. 哪些应进入通用框架，哪些留在任务插件

| 通用框架拥有 | 任务插件拥有 |
|---|---|
| MetricSpec聚合与identity检查 | Spearman、预测单位、clone分组、预测时距 |
| EvidenceLedger、不可变快照与暴露历史 | 数据源、处理步骤、标签与split合同 |
| 有类型研究/计算/搜索关系与回传 | 某个provider真实forward/fit、张量与vocabulary |
| 全局队列、调度、预算与语义去重 | 表征适用性、task-specific负对照和挑战 |
| Codex研究上下文、实施/repair/acquisition工具 | 历史benchmark完整配方、实际模块来源 |
| capability与科学验收、多层报告 | 哪些分组指标构成任务成功标准 |

不能把T47D的20个children上限、某个family名单或固定40次训练搬进全局规则。也不能每个任务写一个私有 `generate/priority/backprop`，让cookbook和真实runner逐渐脱节。

共享runner应编排TaskSpec + CandidateProvider + MetricSpec + EvidenceLedger + SearchPolicy + ArtifactResolver + TrainingDiagnostics；adapter只提供任务与模型接口。现有可靠的grouped composition、recipe与confirmation锁应保留，不必全部推倒重写。

## 11. Cookbook应怎样改，而不是继续叠加禁令

当前cookbook已经写明研究自由、独立样本、准确基线、开放组合和等资源随机搜索验证。主要问题不是再加一句“Codex应该主动”，而是没有检查实际runner是否兑现这些规则。

下一版应把每条硬边界映射到可执行合同与测试，把研究自由映射到真实工具/API可达性：

1. 不可变：数据/标签/分组/主要评价与暴露历史、真实provenance、资源授权。
2. 可研究：结构、训练策略、公开模块、替换/联合/OOF组合，以及合理简化。
3. 必须提供：针对开发集失效模式的理由、快照证据、可证伪对照与实际成本。
4. 不承诺：复杂模型一定更强、一定达到阈值、MCTS一定优于随机搜索。
5. 遇到实际问题：当前Codex尽力implement/repair/acquire；确实不可行时透明skip并继续；不得让resolver缺失、未调用agent或模板限制冒充科学不可行。

无需把完整规则再次复制进实验prompt。简短prompt调用共享runbook，runner给出合同符合性与未覆盖能力清单。

## 12. 推荐实施顺序与验收

| 优先级 | 改造 | 必须通过的验收 |
|---|---|---|
| P0 | 统一主指标聚合与配对反馈 | 能捕获本轮正负反转；同metric的reward delta与feedback一致 |
| P0 | coverage与optimization的拓扑/信用隔离 | 26个coverage不能使强root失去优化资格或改变优化Q |
| P0 | 语义去重与实际能力报告 | 同config不同node ID不算新结构；replicate显式登记 |
| P1 | 真正的Codex研究上下文与条件提案 | 可达agent-defined/联合/OOF组合路径；证据快照可复原 |
| P1 | 更细粒度证据与成本调度 | 负值成本测试、缓存成本测试、repr差异测试通过 |
| P1 | 多层验收、适用性与promotion | 未用artifact为N/A；弱证据不自动替代强root |
| P1 | 训练诊断provider接口 | 能辨别未收敛、容量和分组不稳定，而不借确认集调参 |
| P2 | 框架本身的对照实验 | 等资源随机/简单greedy/候选研究策略比较，报告收益-成本曲线 |
| P2 | 跨任务验证 | 至少一个未参与本轮框架开发的任务，冻结规则后执行 |

先做task-neutral CPU集成场景：没有额外信号时可靠保留root；有可学习的新增信息时能提出/训练相应候选；覆盖不能污染优化；队列补充、skip、resume、freeze边界仍成立。合成fixture只用于机制测试，不当作科研收益。

再做小规模真实协议验收，最后才进行框架对照与未见任务验证。不建议立即追加T47D节点、反复看同一测试集、强制所有child加dense分支，或继续提高模型体量来追正结果。

## 13. 最终判断

这不是“复杂模型理论上不行”的证据，也不是“闭环正常所以框架已完成”的证据。

它说明执行基础已经稳定，而下一阶段最重要的工作是：让实际候选生成、搜索信用、统计目标与科学验收真正兑现cookbook的研究自由和可审计原则。

框架的目标应是更可靠地决定哪些复杂性值得保留、哪些应该删除，并在有增量时更有效地找到它；不是通过继续调整一个demo，使复杂模型最终必须战胜root。

## 证据入口

- 原报告：`../final_report.md`
- 配对统计和搜索审计：`framework_audit_evidence.json`
- 复算脚本：`recompute_evidence.py`
- 原始主指标：`../programs/*/development_metrics.json` 与 `oof_predictions.csv`
- 冻结确认：`../frozen_test_metrics.json`、`../frozen_selection.json`
- 搜索行为：`../tree.json`、`../mcts_trace.jsonl`
- T47D adapter：`src/vc_demo/t47d_research/study.py`
- 共享父节点调度：`src/vc_demo/harness/mcts.py`
- 共享反馈/成本排序：`src/vc_demo/harness/research_feedback.py`
- 原运行范围验收：`src/vc_demo/t47d_research/experiment.py`
- 通用规则：`CODEX_AGENT_COOKBOOK.md`
