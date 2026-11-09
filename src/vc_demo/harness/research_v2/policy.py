"""Task-neutral scheduling; coverage observations never spend optimization credit."""
import math


SEARCH_RELATIONS = {'replace','feature_fusion','joint','crossfit_residual','crossfit_stack','ablation'}
INACTIVE = {'pruned_not_selected','skipped','failed','duplicate','invalidated'}


def priority(estimate, policy):
    gain=float(estimate['expected_gain']);unknown=float(estimate['uncertainty'])
    costs=estimate['cost_seconds']
    if set(costs)!={'acquisition','cache_miss','fit','evaluation'}:
        raise ValueError('Cost must distinguish acquisition, cache misses, fitting and evaluation')
    cost_values=[float(v) for v in costs.values()]
    weight=float(policy['uncertainty_weight']);penalty=float(policy['cost_penalty_per_hour'])
    if not all(math.isfinite(v) for v in [gain,unknown,weight,penalty,*cost_values]) or min(unknown,weight,penalty,*cost_values)<0:
        raise ValueError('Invalid scheduling assumptions')
    if estimate.get('basis') not in {'hypothesis','measured'} or not estimate.get('rationale'):
        raise ValueError('Distinguish a numeric research assumption from measured evidence')
    value=gain+weight*unknown-penalty*sum(cost_values)/3600
    return {'scientific_priority':value,'expected_gain':gain,'uncertainty':unknown,
        'cost_seconds':costs,'basis':estimate['basis'],'rationale':estimate['rationale'],
        'formula':'gain + registered_weight * uncertainty - registered_hour_penalty * cost_hours',
        'artifact_availability_is_quality_signal':False}


def eligible_parents(nodes, active_limit=None):
    result=[]
    for name,node in nodes.items():
        if node['status']!='trained':continue
        active=sum(child.get('parent_id')==name and child['phase']=='optimization'
            and child['status'] in {'selected','repair_needed'} for child in nodes.values())
        if active_limit is None or active<active_limit:result.append(name)
    return result


def parent_ranking(nodes, metric, policy):
    candidates=eligible_parents(nodes,policy.get('parent_active_limit'))
    total=max(2,sum(nodes[name].get('optimization_visits',0)+1 for name in candidates))
    exploration=float(policy['exploration'])
    if exploration<0 or not math.isfinite(exploration):raise ValueError('Invalid exploration coefficient')
    ranked=[]
    for name in candidates:
        node=nodes[name];visits=node.get('optimization_visits',0)
        q=node.get('optimization_value',0)/visits if visits else metric.sign*node['score']
        term=exploration*math.sqrt(math.log(total)/(visits+1))
        ranked.append({'node':name,'own_score':node['score'],'optimization_visits':visits,
            'optimization_q':q,'exploration':term,'score':q+term})
    return sorted(ranked,key=lambda r:(-r['score'],r['node']))


def backpropagate(nodes, name, utility):
    leaf=nodes[name]
    if leaf['status']!='trained' or leaf['phase']!='optimization' or leaf.get('reward_applied'):
        raise ValueError('Only one completed optimization measurement may backpropagate once')
    if not math.isfinite(utility):raise ValueError('Nonfinite reward')
    path=[];current=name
    while current is not None:
        if current in path or current not in nodes:raise ValueError('Invalid optimization ancestry')
        node=nodes[current]
        if node['status']!='trained':raise ValueError('An optimization ancestor must be trained')
        path.append(current)
        if node['phase']!='optimization' or node.get('relation') not in SEARCH_RELATIONS:break
        current=node.get('parent_id')
    for current in path:
        node=nodes[current]
        node['optimization_visits']=node.get('optimization_visits',0)+1
        node['optimization_value']=node.get('optimization_value',0.)+utility
    leaf['reward_applied']=True
    return path
