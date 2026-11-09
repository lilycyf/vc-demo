"""Task-neutral predeclared, report-only analyses after scientific selection closes."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import time
import py_compile

from vc_demo.harness.research_contract import file_digest, freeze_record
from vc_demo.harness.research_contract import digest


def plans_for(spec, state):
    return {**spec.get('analyses', {}), **{name: value['plan'] for name, value in state.get('analysis_plan_additions', {}).items()}}


def validate_plans(spec):
    for name, plan in spec.get('analyses', {}).items():
        if not name or '/' in name or '..' in name:
            raise ValueError('Unsafe analysis identifier')
        if plan.get('protocol') != 'postselection_v1' or plan.get('mode') not in {'predict_only', 'registered_refits'}:
            raise ValueError('Declare a versioned postselection analysis mode')
        if plan.get('data_scope') not in {'development', 'confirmation', 'all_exposed_secondary'}:
            raise ValueError('Declare analysis data/exposure scope')
        if plan['data_scope'] == 'all_exposed_secondary' and not spec['prior_test_exposure']:
            raise ValueError('Do not relabel fresh confirmation data as historically exposed')
        if set(plan['fit_budget']) != {'model', 'calibration'} or any(type(n) != int or n < 0 for n in plan['fit_budget'].values()):
            raise ValueError('Analysis fits have explicit separate nonnegative budgets')
        if plan['mode'] == 'predict_only' and any(plan['fit_budget'].values()):
            raise ValueError('Predict-only analysis cannot register fitting')
        if plan.get('fit_unit') != 'task_pipeline_fit':
            raise ValueError('Name the analysis budget unit; nested component work must be separately reported')
        if plan.get('fit_budget_scope') != 'per_finalist':
            raise ValueError('Declare that each analysis allocation applies per frozen finalist')
        if plan.get('target_policy') not in {'any_finalist', 'each_finalist'}:
            raise ValueError('Declare which frozen finalists must receive the analysis')
        for key in ('contract', 'provider'):
            info = plan[key]
            if file_digest(Path(info['path'])) != info['sha256']:
                raise ValueError('Predeclare actual analysis content before selection: ' + key)
        py_compile.compile(plan['provider']['path'], doraise=True)
        for value in plan.get('code_files', {}).values():
            if file_digest(Path(value['path'])) != value['sha256']:
                raise ValueError('Analysis helper source changed')


def run(session, node, analysis_id):
    with session._transaction(search=False) as (spec, state):
        if not state['selection_closed']:
            raise ValueError('Freeze selection before postselection analysis')
        lock = json.loads((session.run / 'confirmation_lock_v2.json').read_text())
        if node not in lock['selected']:
            raise ValueError('Analysis must name a frozen finalist')
        plans = plans_for(spec, state)
        if lock.get('analysis_plan_sha256') != digest(plans):
            raise ValueError('Frozen analysis plan inventory changed')
        plan = plans.get(analysis_id)
        if plan is None:
            raise ValueError('Analysis was not preregistered; do not add post-hoc evaluation silently')
        for key in ('contract', 'provider'):
            if file_digest(Path(plan[key]['path'])) != plan[key]['sha256']:
                raise ValueError('Frozen analysis content changed')
        for value in plan.get('code_files', {}).values():
            if file_digest(Path(value['path'])) != value['sha256']:
                raise ValueError('Frozen analysis helper source changed')
        n = session._resolved(state['nodes'], node)
        session._provider(n)  # Register the actual fitted class definitions for deserialization.
        session._check_checkpoints(lock['selected'][node]['checkpoint_files'])
        key = analysis_id + '::' + node
        output = session.run / 'nodes' / n['id'] / 'analyses' / analysis_id
        summary_path = session.run / 'analyses' / analysis_id / (node + '.json')
        if key in state.get('analysis_reports', {}):
            if file_digest(summary_path) != state['analysis_reports'][key]:
                raise ValueError('Committed analysis summary changed')
            summary = json.loads(summary_path.read_text())
            if file_digest(Path(summary['receipt']['path'])) != summary['receipt']['sha256']:
                raise ValueError('Committed analysis receipt changed')
            for path, sha in summary['output_files'].items():
                if file_digest(Path(path)) != sha:
                    raise ValueError('Committed analysis output changed')
            return summary
        contract = json.loads(Path(plan['contract']['path']).read_text())
        for info in contract.get('inputs', {}).values():
            if file_digest(Path(info['path'])) != info['sha256']:
                raise ValueError('Preregistered analysis input changed')
        path = Path(plan['provider']['path'])
        name = 'postselection_provider_' + plan['provider']['sha256'][:16]
        loader = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(loader)
        sys.modules[name] = module
        loader.loader.exec_module(module)
        output.mkdir(parents=True, exist_ok=True)
        request = copy.deepcopy({'phase': 'postselection_report_only', 'analysis_id': analysis_id, 'plan': plan,
            'analysis_contract': contract, 'task_id': spec['task_id'], 'metric': spec['metric'],
            'metric_id': lock['metric_id'], 'node_id': node, 'recipe': n['sealed_recipe'],
            'execution': n['execution'], 'checkpoint_files': lock['selected'][node]['checkpoint_files'],
            'development_contract': json.loads(Path(spec['development_contract']).read_text()),
            'development_inputs': spec['inputs'], 'development_receipt': session._receipt(n),
            'output_dir': str(output), 'prior_test_exposure': spec['prior_test_exposure']})
        start = time.monotonic()
        try:
            receipt_path = output / 'analysis_receipt.json'
            recovered = json.loads(receipt_path.read_text()) if receipt_path.is_file() else None
            if recovered:
                if recovered.get('measurement_id') != n['measurement_id'] or recovered.get('contract_sha256') != plan['contract']['sha256'] or recovered.get('provider_sha256') != plan['provider']['sha256']:
                    raise ValueError('Interrupted analysis receipt belongs to another frozen execution')
                for path, sha in recovered['output_files'].items():
                    if file_digest(Path(path)) != sha:
                        raise ValueError('Interrupted analysis output changed')
                result = recovered['result']
            else:
                result = module.evaluate_analysis(request)
            session._deadline(spec)
            for field, budget in [('model_refits', 'model'), ('calibration_refits', 'calibration')]:
                actual = result.get(field)
                if type(actual) != int or actual < 0 or actual > plan['fit_budget'][budget]:
                    raise ValueError('Actual analysis fits exceed the declared budget: ' + field)
                if plan['mode'] == 'predict_only' and actual:
                    raise ValueError('Frozen-only analysis performed fitting')
            if len(result.get('fit_audit', [])) != result['model_refits']:
                raise ValueError('Each actual task-pipeline refit needs a separate access audit')
            for audit in result.get('fit_audit', []):
                if not audit.get('train_groups') or 'validation_groups' not in audit:
                    raise ValueError('Missing analysis training/query group audit')
                if set(audit['train_groups']) & set(audit['validation_groups']) and not plan.get('allow_training_query_group_overlap', False):
                    raise ValueError('Analysis train/query groups overlap without an explicit retrospective protocol')
                if not set(audit['train_groups']).issubset(contract.get('allowed_training_groups', [])) or not set(audit['validation_groups']).issubset(contract.get('allowed_query_groups', [])):
                    raise ValueError('Analysis fit/query groups exceed the preregistered data scope')
            session._check_checkpoints(lock['selected'][node]['checkpoint_files'])
            files = {}
            for filename in result.get('output_files', []):
                p = Path(filename).resolve()
                if not p.is_relative_to(output) or not p.is_file():
                    raise ValueError('Analysis outputs must stay in the private node analysis directory')
                files[str(p)] = file_digest(p)
            receipt = recovered or {'evidence_phase': 'postselection_report_only', 'analysis_id': analysis_id, 'node': node,
                'result': result, 'wall_seconds': time.monotonic() - start, 'data_scope': plan['data_scope'],
                'measurement_id': n['measurement_id'], 'contract_sha256': plan['contract']['sha256'],
                'provider_sha256': plan['provider']['sha256'], 'output_files': files}
            if not recovered:
                freeze_record(receipt_path, receipt)
            summary = {'evidence_phase': 'postselection_report_only', 'analysis_id': analysis_id,
                'node': node, 'data_scope': plan['data_scope'], 'prior_test_exposure': spec['prior_test_exposure'],
                'metrics': result['metrics'], 'model_refits': result['model_refits'],
                'calibration_refits': result['calibration_refits'], 'optimization_credit': 0,
                'wall_seconds': receipt['wall_seconds'], 'output_files': files,
                'receipt': {'path': str(receipt_path), 'sha256': file_digest(receipt_path)}}
            freeze_record(summary_path, summary)
            state.setdefault('analysis_reports', {})[key] = file_digest(summary_path)
            session._event(state, 'postselection_analysis_completed_no_search_credit', node=node, analysis_id=analysis_id)
            return summary
        except Exception as error:
            # The completed scientific node remains immutable; this is analysis work, not a training reward.
            state.setdefault('analysis_attempts', []).append({'analysis_id': analysis_id, 'node': node,
                'error': str(error), 'wall_seconds': time.monotonic() - start})
            session._event(state, 'postselection_analysis_failed_no_search_credit', node=node, analysis_id=analysis_id)
            failure = error
    raise ValueError('Repair/version the report-only analysis without reopening scientific selection: ' + str(failure)) from failure
