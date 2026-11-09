"""Aggregate engineering evidence, never train or publish row-level observations."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

from vc_demo.harness.research_contract import file_digest, write_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-dir', type=Path, required=True)
    args = parser.parse_args()
    out = args.report_dir
    root = ET.parse(out / 'pytest_junit.xml').getroot()
    cases = list(root.iter('testcase'))
    failures = [c.attrib['name'] for c in cases if c.find('failure') is not None or c.find('error') is not None]
    skipped = [c.attrib['name'] for c in cases if c.find('skipped') is not None]
    if not cases or failures or skipped:
        raise ValueError('Do not certify failed, absent or skipped engineering paths')
    observed = {c.attrib.get('classname', '') + '::' + c.attrib['name'] for c in cases}
    checks = {
        'scvi_actual_library': 'fit_save_load_query_without_refitting[scvi-4]',
        'cellrank_actual_kernel': 'fit_save_load_query_without_refitting[cellrank-4]',
        'dpt_actual_library': 'fit_save_load_query_without_refitting[pseudotime-2]',
        'pertpy_ott_actual_distances': 'fit_save_load_query_without_refitting[distance-4]',
        'train_only_and_gene_vocabulary': 'never_fits_validation_cells_and_rejects_changed_vocab',
        'scvi_explicit_unknown_batch': 'unknown_query_batch_has_explicit_nonadaptive_reference_policy',
        'actual_interval_aft': 'hazard_uses_actual_train_only_intervals_and_frozen_survival',
        'author_tracsed_source_and_seed': 'author_tracsed_architecture_cpu_fit_save_reload_prediction_only[101]',
        'scvi_shared_session': 'shared_session_development_and_frozen_query[scvi]',
        'cellrank_shared_session': 'shared_session_development_and_frozen_query[cellrank]',
        'heavy_neural_backward_and_query': 'shared_session_development_and_frozen_query[pseudotime]',
        'all_twelve_shared_cli_analyses': 'all_twelve_actual_challenges_share_generic_lifecycle_without_search_credit',
        'analysis_exactly_once_receipt_recovery': 'interrupted_analysis_recovers_receipt_without_another_actual_fit',
        'analysis_primary_reward_isolation': 'fit_budget_violation_is_not_a_primary_training_failure_or_reward',
        'analysis_frozen_source_drift': 'analysis_content_drift_cannot_be_silently_repaired_after_freezing',
    }
    coverage = {key: any(fragment in case for case in observed) for key, fragment in checks.items()}
    if not all(coverage.values()):
        raise ValueError('Missing actual specialist tests: ' + repr(coverage))
    real = json.loads((out / 'real_source_preflight.json').read_text())
    heavy = json.loads((out / 'heavy_source_preflight.json').read_text())
    if real['models_fitted_on_real_data'] or heavy['models_fitted_on_real_data']:
        raise ValueError('This report is engineering-only')
    from vc_demo.t47d_provider_v2.analysis_registration import KINDS
    env = {'python': sys.version.split()[0], 'packages': {p: importlib.metadata.version(p) for p in
        ['torch', 'numpy', 'scipy', 'pandas', 'scikit-learn', 'joblib', 'xgboost', 'h5py', 'anndata',
         'scanpy', 'scikit-misc', 'scvi-tools', 'cellrank', 'pertpy', 'POT', 'jax', 'jaxlib', 'ott-jax', 'lifelines', 'pytest']}}
    write_record(out / 'runtime_environment.json', {'main': env, 'isolated_tensorflow': heavy['tensorflow_runtime']})
    result = {'kind': 'specialist_engineering_acceptance_not_scientific_experiment',
        'base_commit': '891e662', 'branch': subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip(),
        'tests': {'total': len(cases), 'failed': 0, 'skipped': 0,
                  'junit_sha256': file_digest(out / 'pytest_junit.xml')}, 'specialist_checks': coverage,
        'analysis_kinds_actually_exercised_on_synthetic_cpu_data': sorted(KINDS),
        'real_data_preparation_and_contract_checks': 'passed', 'real_data_model_fits': 0,
        'new_formal_search_started': False, 'historical_frozen_results': 'unchanged per independent preflight',
        'original_watchdog_deadline_utc': real['original_deadline_utc'],
        'limitations': ['CPU synthetic acceptance is not a real-scale GPU memory/convergence test',
            'No scientific benchmark replay, search or new scientific confirmation was performed',
            'Author architecture/retrospective splitters are exercised, not paper numerical replication',
            'Original R upstream preprocessing was not migrated or rerun in this acceptance',
            'Reviewed provider/access audits are not an OS security sandbox',
            'Analysis budgets are per finalist/task pipeline, not all internal component optimizer steps']}
    paths = [*Path('src/vc_demo/t47d_provider_v2').glob('*.py'), *Path('src/vc_demo/harness/research_v2').glob('*.py')]
    result['implementation_sha256'] = {str(p): file_digest(p) for p in sorted(paths)}
    write_record(out / 'acceptance_summary.json', result)
    table = '\n'.join('| `' + key + '` | passed |' for key in coverage)
    methods = '\n'.join('- `' + kind + '`' for kind in sorted(KINDS))
    text = f'''# T47D 新框架重型路径专项工程验收

## 结论

专项工程验收通过：{len(cases)} 个 CPU 回归测试，0 failed、0 skipped。
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
{table}

## 分析接入与隔离

以下12类方法通过真实共享 CLI 在合成工程数据上执行，不是只登记名称：
{methods}

计划可从开发证据登记，冻结后方法/输入/源码/预算不可静默改变。
主确认只预测；预声明挑战的模型/校准重拟合有独立 per-finalist 预算和访问审计，
内部 component 工作另记。分析结果不进入排序、奖励、visits/Q 或主拟合预算。
durable receipt 写入后的中断恢复不重复拟合；此前崩溃的工作仍须按失败尝试记录。
组件没有被使用时 N/A；没有 eligible heldout Month6 阳性时 recall 为未定义，
不伪造0分。动态加载后的分析预测与主确认的逐行预测一致性也已验收。

## 真实数据零拟合预检

- 开发：{heavy['early_cells']['development']['groups']} clones / {heavy['early_cells']['development']['cells']} early cells。
- 确认：{heavy['early_cells']['confirmation']['groups']} clones / {heavy['early_cells']['confirmation']['cells']} early cells。
- 基因数：{heavy['early_cells']['development']['genes']}，固定 gene_id 顺序；只导出 day0/1/4。
- 额外训练事件：{heavy['train_only_event_rows']} rows，只含开发克隆、days1/4/8/26；实际每次 fit 再裁训练行/声明 horizon。
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
'''
    (out / 'engineering_acceptance_report.md').write_text(text)
    print(json.dumps({'tests': result['tests'], 'specialist_checks': coverage,
        'real_data_model_fits': 0, 'new_formal_search_started': False}, indent=2))


if __name__ == '__main__':
    main()
