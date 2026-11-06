# T47D 完整执行记录与解释边界

## 本次范围

执行依据为用户原始 H1-P2 文档，仓库内保存为
`docs/T47D_LINEAGE_ORIGINAL_SPEC.md`。正式目录为
`experiments/t47d_lineage_resistance_full_v2`。旧
`t47d_lineage_resistance_demo` 只作不可覆盖的 pilot 和历史参考。

本次没有把完整实验降为 smoke。107 个有效模板、五个 root、40 个
selected rollouts；每个正式候选都完成五 seed、三折 clone-group CV。
作者方法参考复现与早期预测是两条独立证据轨道，不能合并计算精度。

## 真实运行的实现与修复

- 在持久化卷建立独立的 PyTorch/scverse、TensorFlow 与 R 环境。
  安装的 R 稀疏矩阵依赖、GPU 动态库等缺失属于可修复依赖，不当作
  不可公开 artifact blocker。
- 原始表达矩阵和 QC 矩阵分别保存，前者不是后者的符号链接。完整
  细胞排除表、表达/条码对应、基因顺序和 GEO 样本映射保留。
- PCA、scVI、距离、DPT、CellRank 的估计仅使用训练克隆。scVI 实际
  训练 NB 模型，50 epoch 上限、patience10、latent16；query 不做优化。
- Wasserstein 调用真实 pertpy/OTT solver，检查有限性与收敛，不使用
  provider 在失败时返回的常数哨兵。仅复用训练参照统计量和无状态编译
  函数，没有删去全细胞分布以缩减范围。
- CellRank 使用真实 RealTimeKernel/POT 耦合；同一 float64 Sinkhorn
  的 CPU/CUDA 等价测试保存在 `ot_backend_equivalence.json`。
- 作者 R 方法重建公开 IO，执行 PLSR/Leiden/Slingshot/KS/六细胞平滑。
  无法公开的 private SCE、内部签名及原 cluster ID 不伪称数值复现。
- TensorFlow 提取并校验作者原函数，保留原图的 pooling/重复块行为。
  early forecast 使用 seq3 adapter；作者参考使用 seq8、20 epochs、
  batch32、四个 prefix 区间、full/no-attention/no-feedforward/linear。
- Keras3 的自动 XLA 与原环境默认不同。参考轨道统一设置
  `jit_compile=False` 后完整重跑；早先 29 个自动 XLA 拟合只留作
  compiler diagnostic，不计入正式 464 次参考拟合。forecast 保留已有
  `jit_compile=True` 协议，未改变主搜索奖励。
- 搜索进程恢复已完成的折。实际 trace 有45次唯一 trained backprop，
  三个中断恢复节点缺少冗余的 rollout-completed 日志，但训练、回传及
  后续 proposal 重生均有原始事件证明。只修复未来日志，不编造过去事件。
- 修复 No-pathway 消融使其只移除通路，不一并移除独立距离等表征。
  旧版保存在诊断目录；正式采用 ablation contract v2。
- 修复 early-warning horizon，缩短窗口但不扩展 baseline-only parent
  的输入权限。旧比较归档，三个 horizon 重新拟合，保留冻结架构。
- Raw-ratio suppression 用真实 f26/f0；预测反演注册 eps 变换，不把
  `2**log_label` 误当未经平滑的原始频率比。

上述修复不改变固定 clone split、任务标签、主搜索 reward 或冻结后的
winner。源代码最终 SHA、环境锁、作者源函数 hash、协议诊断记录均保存。

## 明确不应被掩盖的结果

1. 搜索 child 虽超过本次五个 root，却没有超过旧 pilot 强 Ridge。
   treatment 编码/缩放变更会削弱正则化基线，后续通用框架必须同时冻结
   baseline preprocessing，而不只冻结 label/split。
2. Baseline-only、无时序、day4 快照和早期丰度对照不弱于完整 child。
   不应把“使用了真实动态模型”写成“动态结构有预测优势”。
3. 频率同时进入输入和 log-ratio 标签分母。保留基线、置换终点的20次
   分母耦合诊断仍有明显相关；它不是确认性置换 p 值。
4. 本 baseline-qualified 46-clone 队列中，联合正选择克隆数并不比单药
   更少；只有部分单药正选择克隆在联合中转为负选择。不能改分母或资格
   来制造论文方向一致。部分 ER/E2F 下降也不代表 EMT 始终下降。
5. Month6 四个已观测条码中只有一个满足早期资格，且属于开发组。
   保留组没有长期阳性，未见克隆逃逸 recall 不可识别，而不是100%。
6. 先前 pilot 已暴露相同 test 克隆和 Month6。当前选择仍仅用开发 OOF，
   但最终 test 不是全新盲测。LOCO 是模型冻结后的全队列次级跨拟合。

完成判定只由 `completion_matrix.json` 与独立的
`complete_study_acceptance_audit.json` 决定；科学假设可被否定，不能为了
获得正结果重新选择 test、减少比较或把控制组改为新的 winner。

## 保存、成本与权限

数据、模型、参考中间文件、折内 artifact 与环境均在 Network Volume。
GitHub 仅保存源码、合同、轻量预测/指标、审计和报告，不上传权重。
GitHub deploy 私钥只在容器 root 目录，不放到权限宽松的共享卷。

用户授权首轮24小时/$20；独立预算停止器仍保持运行，最迟
2026-11-07 07:30 UTC 停止 GPU，不自行延长预算。依用户选择，任务结束后
不提前手动停 Pod。报告中的小时成本是估算，不是账单。
