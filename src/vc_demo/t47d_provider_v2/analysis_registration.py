"""Explicit task-analysis plans; no evaluation, search or implicit scientific budget."""
import copy
from pathlib import Path

from vc_demo.harness.research_contract import file_digest, freeze_record
from .cell_sources import info


KINDS = {'loco', 'monotherapy_to_combination', 'late_interval', 'early_warning', 'ablations',
         'last_snapshot', 'early_abundance', 'denominator_null', 'biology_sensitivity',
         'resistance_month6', 'secondary_metrics', 'author_reference'}


def register_analyses(task_spec, preparation, plans, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    result = copy.deepcopy(task_spec)
    result.setdefault('analyses', {})
    for name, plan in plans.items():
        if plan['kind'] not in KINDS:
            raise ValueError('Implement/register a real analysis provider for a new scientific question')
        scope = plan['data_scope']
        development_only = {'ablations', 'last_snapshot', 'early_abundance', 'denominator_null'}
        confirmation = {'monotherapy_to_combination', 'late_interval', 'early_warning',
                        'biology_sensitivity', 'resistance_month6', 'secondary_metrics'}
        if plan['kind'] in development_only and scope != 'development':
            raise ValueError('Development diagnostics must not open confirmation outcomes')
        if plan['kind'] in confirmation and scope not in {'confirmation', 'all_exposed_secondary'}:
            raise ValueError('This challenge requires an explicit confirmation/exposure scope')
        if plan['kind'] == 'loco' and scope != 'all_exposed_secondary':
            raise ValueError('Full-cohort LOCO is explicitly exposed secondary evidence')
        if plan['kind'] == 'author_reference' and not plan.get('allow_training_query_group_overlap'):
            raise ValueError('Author windows overlap barcode groups; declare retrospective scope')
        if name in result['analyses']:
            raise ValueError('Do not silently replace a registered analysis')
        inputs = dict(preparation['development_inputs'])
        inputs['development_contract'] = info(preparation['development_contract'])
        inputs['confirmation_contract'] = preparation['confirmation_contract']
        source = preparation.get('postselection_sources', {})
        inputs.update({'source:' + key: value for key, value in source.items()})
        assets = {}
        for role in ('hallmark', 'tracsed_notebook', 'tensorflow_runtime'):
            if role in preparation:
                assets[role] = preparation[role]
                inputs['asset:' + role] = info(preparation[role]['path'])
        extra = plan.get('extra_inputs', {})
        if set(extra) & set(inputs):
            raise ValueError('Additional analysis sources cannot shadow registered task inputs')
        inputs.update(copy.deepcopy(extra))
        # Contracts describe data and methods, not the result of an unrun analysis.
        contract = {'kind': plan['kind'], 'settings': copy.deepcopy(plan['settings']),
            'inputs': inputs, 'assets': assets, 'source_context': 'GSE260703; retrospective exposure retained',
            'label_semantics': preparation['task_contract']['label']}
        groups = preparation['scope_groups']
        if plan['kind'] == 'author_reference':
            import json
            source = extra.get('reference_data')
            if source is None:
                raise ValueError('Register real source-backed author reference data')
            allowed = sorted(json.loads(Path(source['path']).read_text()))
            contract.update(allowed_training_groups=allowed, allowed_query_groups=allowed)
        elif plan['data_scope'] == 'all_exposed_secondary':
            allowed = sorted(set(groups['development']) | set(groups['confirmation']))
            contract.update(allowed_training_groups=allowed, allowed_query_groups=allowed)
        else:
            contract.update(allowed_training_groups=groups['development'],
                allowed_query_groups=groups['development'] if plan['data_scope'] == 'development' else groups['confirmation'])
        path = directory / (name + '.json')
        freeze_record(path, contract)
        provider = Path(__file__).with_name('analysis_provider.py')
        result['analyses'][name] = {'protocol': 'postselection_v1', 'mode': plan['mode'],
            'fit_unit': 'task_pipeline_fit', 'fit_budget': copy.deepcopy(plan['fit_budget']),
            'fit_budget_scope': 'per_finalist',
            'target_policy': plan['target_policy'], 'data_scope': plan['data_scope'],
            'allow_training_query_group_overlap': plan.get('allow_training_query_group_overlap', False),
            'contract': info(path), 'provider': info(provider),
            'code_files': {p.stem: info(p) for p in Path(__file__).parent.glob('*.py')}}
    return result
