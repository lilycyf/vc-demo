"""Write source-backed preparation and whole-study completion records."""
from __future__ import annotations

import hashlib
import argparse
import json
import subprocess
from pathlib import Path

from vc_demo.t47d_lineage.data import dump


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-dir",default="experiments/t47d_lineage_resistance_demo")
    args=parser.parse_args()
    run=Path(args.run_dir)
    result=json.loads((run/"search_results.json").read_text())
    raw=json.loads(Path("data/t47d_lineage/raw/download_manifest.json").read_text())
    matrix=[]
    for item in raw["artifacts"]:
        matrix.append({**item,"state":"present","provider":"NCBI GEO","scope":"T47D GSE260703",
                       "reusable":False,"required_by":["lineage task preparation"]})
    gmt=Path("data/t47d_lineage/pathways/h.all.v2025.1.Hs.symbols.gmt")
    matrix.append({"id":"hallmark_2025_1_human","path":str(gmt),"state":"present","status":"original_public",
                   "sha256":hashlib.file_digest(gmt.open("rb"),"sha256").hexdigest(),"size_bytes":gmt.stat().st_size,
                   "source_url":"https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2025.1.Hs/h.all.v2025.1.Hs.symbols.gmt",
                   "provider":"MSigDB/Broad","version":"2025.1.Hs","scope":"human","reusable":True,
                   "required_by":["pathway roots","pathway candidates","matched membership controls"]})
    for name in ["qc_counts.h5ad","clone_mean_log_expression.npz","clone_pseudobulk_counts.npz","clone_expression_rows.csv","gene_order.csv"]:
        path=Path("data/t47d_lineage/prepared")/name
        matrix.append({"id":name,"path":str(path),"state":"present","status":"derived","scope":"T47D GSE260703",
                       "reusable":False,"size_bytes":path.stat().st_size,
                       "sha256":hashlib.file_digest(path.open("rb"),"sha256").hexdigest(),
                       "build_command":"python scripts/t47d/prepare.py"})
    author_commit=subprocess.check_output(["git","-C","/workspace/_external/TraCSED","rev-parse","HEAD"],text=True).strip()
    matrix.append({"id":"tracsed_author_code","path":"/workspace/_external/TraCSED","state":"present",
                   "status":"original_public","source_url":"https://github.com/Genentech/TraCSED","revision":author_commit,
                   "license":"MIT","reusable":True,"runtime_ready":False,
                   "integration_gap":"Author R scripts depend on internal gp.sa.core/gstore objects and curated inputs; rebuild from public data, do not substitute a proxy"})
    dump(run/"artifact_alignment_matrix.json",{"artifacts":matrix,"missing_required_first_stage":[],
            "download_again":"python scripts/t47d/acquire.py; verified existing files are retained and altered checksums are rejected"})
    completion={
        "server_and_github":"completed", "public_data_acquisition":"completed", "qc_and_clone_mapping":"completed",
        "frozen_grouped_task_contract":"completed", "five_roots":"completed", "twenty_selected_rollouts":"completed",
        "locked_test_for_frozen_models":"completed", "matched_and_shuffled_pathway_controls":"completed",
        "eight_ablation_applicability_accounting":"completed_with_inapplicable_items_explicit",
        "combination_suppression_descriptive":"completed", "month6_transport":"completed_with_no_heldout_positive",
        "pseudocount_and_denominator_diagnostics":"completed", "root_dominance_audit":"completed",
        "parent_preserving_upgrade":"implemented_and_smoked_not_formally_evaluated",
        "node_local_execution_authority_upgrade":"implemented_and_unit_tested_not_retroactively_claimed",
        "exact_tracsed_reference":"not_completed", "scvi_cellrank_pertpy_hazard_extensions":"not_completed",
        "original_gene_program_method_replication":"not_completed", "whole_study_complete":False,
    }
    dump(run/"completion_matrix.json",completion)
    root,child=result["best_root"],result["best_child"]
    text=f"""# T47D 公开数据 Harness：首阶段实验与交接报告

## 当前结论

已完成服务器、GitHub、公开数据准备和首阶段真实模型搜索。**整个设计文档的全部实验尚未完成**，不能将首轮闭环通过写成原论文完整复现。

- 分支：`t47d-lineage-resistance-demo`。
- 运行目录：`{run}`。
- 原始表达：200,429 个细胞、58,302 个基因。
- QC 且单条码：47,718 个细胞；基线纳入条件得到 46 个克隆。
- 36 个开发克隆、10 个锁定测试克隆；共有 138 个 clone-treatment 行，但独立分组仍只有 46 个。
- 5 个 root、20 个正式 selected rollouts、79 个 proposals、59 个未选中且未训练。
- reward 是分组 OOF Spearman，不是旧 K562/HELF 的 Macro-F1。

| 模型 | 开发集分组验证 Spearman | 锁定测试 Spearman |
|---|---:|---:|
| best root：基线 pathway Ridge | {root['validation']:.4f} | {root['test']['ensemble']['spearman']:.4f} |
| best generated child：早期 pathway PLS | {child['validation']:.4f} | {child['test']['ensemble']['spearman']:.4f} |

生成模型没有超过 root。测试集的置信区间很宽，不支持宣称稳定的模型优越性。Ridge/PLS 的五次最终 seed 重拟合是确定性的重复，不是五份独立生物学验证。

## 做了什么，以及筛掉什么

1. 从 NCBI 下载七个原始处理文件，记录 URL、大小、SHA256；获取并固定原作者代码和 Hallmark 2025.1。
2. 逐细胞 ID 对齐表达矩阵与 GFP 矩阵。低基因数、高线粒体比例、零条码及多条码细胞不进入已知克隆监督任务。
3. 只按基线至少十个细胞纳入克隆；没有用未来是否存活筛选建模克隆。
4. 按克隆整体切分，同一克隆的全部 treatment/time 不跨 train/validation/test。
5. 120 个已实现候选组合覆盖真实 Ridge、Elastic Net、PLS、XGBoost、GRU、Transformer、非线性残差模型。scVI/CellRank/TraCSED 等另列 planned，不虚报可执行覆盖。
6. 复用仓库 UCT/backprop 核心。每轮补 proposals，全球队列选一个 rollout；只为正式训练成功的节点回传 reward。
7. 首轮按预注册规则在至少 20 个 rollout 后无提升停止。没有为追求超过 root 而反复改 test、标签或切分。

## 归因与长期样本

- 对同一冻结 child，测试了 matched random projection、真正打乱基因成员的 pathway 对照、早期时间平均等控制；没有将控制结果重新升级为已搜索到的 best child。
- 时间平均控制优于复杂时间顺序版本。这是下一版通用表征空间的设计信号，不是继续使用同一 test 调参的许可。
- 观察到五个克隆在至少一单药相对正选择、组合相对负选择；只属于所定义相对丰度指标的描述性结果。
- Month 6 在纳入队列中只有 `GFPBC_libB_92196` 达到至少三个细胞的持续检出条件。它不在十个 held-out 克隆里，所以不能声称 unseen-clone escape recall=100%。
- 终点零计数只是采样未检出，不等于证实灭绝。已输出 pseudocount 敏感性和保留基线分母的 endpoint 置乱诊断，避免把数学耦合误认为未来耐药预测能力。
- 分数不证明临床疗效，也不证明单个耐药细胞被逆转为药敏状态。

## 框架改进及证据边界

首轮发现 proposal 会替换强父模型，而非默认保留父路线。已新增 `parent_plus_residual`：每个训练 fold 内重拟合父模型，mutation 拟合训练残差，然后相加；不改原始标签。

该改进已通过单元测试、真实开发集 forward/backward 与 CPU 持久化 roundtrip 检查，**尚未进行新一轮正式搜索，不应把首轮分数归功于这项新实现**。首轮树、trace、冻结选择都保持原样。

另修正执行权限：首轮节点脚本与共享 helper 同构，但训练入口直接调用 helper；它不能证明任意 agent-written node-local 模型已被执行。现在 smoke、十五个 CV fold 和最终重拟合均显式调用节点 `model.py` 的工厂，已有节点代码不会被覆盖，并有调用次数回归测试。该升级也不倒写进首轮成绩。

## 尚未完成的部分

| 项目 | 需要做什么 | 资源与时间 |
|---|---|---|
| 精确 TraCSED 参考 | 从公开数据重建作者 R 对象、Slingshot 与 selection JSON，再调用原模型；不能拿普通 Transformer 充数 | 需要 R/Bioconductor 与 TensorFlow 环境。工程预计 1–3 天，训练需先 profile；当前未实测，不承诺固定 GPU 小时 |
| scVI/CellRank/pertpy/hazard | 建立 train-fold-only 表征、验证 query/时间/删失合同，再接入候选 | 24GB GPU/125GB RAM 可作为起点；每 fold 的耗时应先实测，再判断能否在 $20 首轮内完成 |
| 原论文 pathway 动态复现 | 区分当前 mean-log score 与作者 scuttle/自定义签名，完成配对克隆和伪时间分析 | 工程与统计审计任务，不能只靠现有 mean-log 趋势表宣称完成 |
| 全部适用消融 | 选择对应架构后实现 interaction 和 dense-parent 控制；无 clone mapping 时主标签本身不可定义 | `ablation_applicability.json` 明确已评估/不适用，不能伪造八项全通过 |

这些是可继续开展的工程/分析工作，并非已经证明公开原始数据不可获得。后续若突破本次批准的时间或费用，应先取得新的授权。

## 如何保存与继续

- `/workspace` 是持久化 Network Volume。原始数据、h5ad、克隆张量、虚拟环境与训练模型在此保留，不进入 Git。
- 代码、配置、校验和、轻量报告进入 GitHub。下载复用脚本检查已有文件，校验和改变时拒绝静默更新。
- 运行规范：`docs/T47D_LINEAGE_RESISTANCE_RUNBOOK.md`。
- 单入口：`PYTHONPATH=src /workspace/t47d_venv/bin/python scripts/t47d/demo.py --run-dir experiments/<fresh_registered_run>`。
- 已打开 test 的首轮不得 resume 搜索。进一步研究必须明确历史 test 暴露，优先使用开发集/嵌套评估，不制造“全新盲测”说法。
- GPU 暂停后保留 Network Volume；存储费仍持续，未授权删除数据卷。
- 用户选择先保持运行。已有 Pod-scoped 凭据经 REST v2 自检通过，费用保护进程设为北京时间 2026-11-07 15:30 停止当前 GPU；不删除数据卷。容器重启会使进程失效，需要重新配置。没有把 API 密钥写入 Git 或数据卷。

![首轮验证与控制](first_stage_summary.png)

完整节点关系见 `final_report.md` 的 Mermaid 图；逐步选择与回传见 `mcts_trace.jsonl`。
"""
    (run/"实验报告与交接.md").write_text(text)
    print(json.dumps(completion))


if __name__=="__main__":
    main()
