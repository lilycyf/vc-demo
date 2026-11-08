# T47D 正式实验 v3：共享研究协议适配器

## 目的

这是原 T47D 完整任务的新版本执行，不是复用旧树的 resume，也不是仅有接口 smoke。
保留原始数据、clone split、标签语义和全部任务范围。新增代码位于
`src/vc_demo/t47d_research/`，旧 `t47d_full` 与历史结果保持不变。

## 任务与评价

- 输入：同一 clone 的 day0/1/4 状态、treatment 与允许的早期丰度。
- 目标：day26 平滑 log2 相对 clone selection；不是临床疗效或绝对细胞杀伤。
- 奖励：5 seeds × 3 clone-grouped folds 的平均 seed-level OOF Spearman。
- 次要评价：MAE、组 bootstrap、within-treatment、AUPRC/AUROC、NDCG、校准、组合抑制和长期逃逸。
- 原 test clones 和 Month6 已在历史实验中暴露，不能再称为新的盲测。

## 完整范围

1. 复用并核验公开准备数据、QC、clone mapping、split 和原作者代码 revision。
2. 5 个原 full-v2 roots，加上历史强 Ridge 的完整分类编码/缩放配方，共 6 个 roots。
3. 原完整 manifest 仍保留；先完成单独登记的模块 coverage，再进行 40 个
   optimization selected rollouts。Coverage 不冒充 optimization 成功。
4. 每个正式候选 15 个 grouped-CV fits；每次 rollout 后补充和重排全局队列。
5. 八项消融、day4 snapshot、early abundance、分母耦合 null controls。
6. 冻结选择、development-fitted 权重与 calibrator 后，主要确认只加载权重，零重训。
7. 固定 LOCO、跨 treatment、day8→26、day0/1/4 warning、长期/生物学分析。
8. 完整公开 R/TF reference reconstruction，不声称是私有 signature 的数值复现。
9. 图表、node 关系、成本/失败/归因和完整性报告。

## 与旧实现的区别

- 不强制 parent computation graph，不使用固定 `.25`，不拟合训练集内残差。
- 新神经模型直接学习响应，不隐含训练集 Ridge residual。
- 显式 residual/stacking 使用共享 grouped OOF / nested OOF 学习权重。
- 当前预算方案只生成单层跨模型组合；不是共享框架禁止更深组合。
- 完整强基线保留，不用改变编码的弱 root 代替历史参照。
- 覆盖与优化分账，不用 `+10` 科学优先级强行伪装 coverage。
- 排序只使用 development 增益、描述性不确定性和成本，无 artifact-present/品牌加分。
- 缓存绑定完整输入内容、代码、package versions、训练 rows、seed、时间窗。
- 新命名空间表征缓存，不把旧 `full_fold_artifacts` 当成已验证的新缓存。
- 代码/配方变化不能静默复用旧 fold results。

神经训练默认 80 epochs，可声明 160；不是通用 epoch 下限。
公开 TraCSED worker 实际为 20 epochs / batch32 / Adam / MSE。
scVI 真实训练的上限为 50 epochs，不是小模型 proxy。

## 资源与启动

用户授权首轮最多 24 小时、增量总费用 $20；新增存储整月费用保守纳入。
GPU $0.24/小时，容器盘约 $0.007/小时，新 100GB 卷 $7/月。旧卷临时 CPU
复制约 $0.26/小时，完成即停。不能减少范围伪称完成，也不能自动延长授权。

数据、R/TF/Python、GPU、独立 watchdog 检查通过后，使用全新目录：

```bash
PYTHONPATH=src:. /workspace/t47d_full_venv/bin/python -u \
  scripts/t47d/research_demo.py \
  --run-dir experiments/t47d_research_protocol_formal_v3 \
  --optimization-rollouts 40 --phase all
```

阶段 checkpoint 支持恢复。Search 必须在 confirmation lock 之前；主要确认以后
不能再生成/选择模型。预登记 secondary diagnostics 的 refits 与主要确认分开
标注，不回传、不用于模型选择。

持久卷上的 `t47d_public_migration.tar.gz` 保存完整环境备份，SHA256 为
`b7509b246a2f130912d0b327ef8d65df2c69b8811f707ba0fe2eba9eeb49bdd2`。
为避免共享卷大量小文件 IO，活跃 Python/TF/R 环境放在容器本地盘，
`/workspace/t47d_*` 是指向它们的链接；数据、代码、缓存和结果仍在持久卷。
Pod 重启后先运行 `python scripts/t47d/restore_research_runtime.py` 恢复环境，
重新验证 GPU/依赖并设置预算 watchdog，不能假设旧临时盘仍然存在。

## 验收

完成须同时满足 coverage、optimization、参考复现、消融、全部挑战和报告的
文件/计数检查。遇到失败或计算上限，保留进度并报告未完成项。
零 guardrail 计数不是模型更优的证据；child 未超过完整强基线是合法结论。
该任务参与过框架开发，不能单独用它证明跨任务收益。
