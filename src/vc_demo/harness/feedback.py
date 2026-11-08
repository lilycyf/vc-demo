"""Development-only research feedback; confirmation never feeds search."""
from __future__ import annotations
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from vc_demo.harness.research_contract import selection_context, write_record


def _number(value):
    try:
        result=float(value)
        return result if math.isfinite(result) else None
    except (TypeError,ValueError):return None


def _value(node):
    for key in ('validation_reward','best_val_macro_f1','validation_score'):
        result=_number(node.get(key))
        if result is not None:return result
    return None


def build_framework_feedback(run_dir: Path, tree: dict[str,Any] | None=None,
                             memory: dict[str,Any] | None=None, target_val_macro_f1=None):
    path=run_dir/'tree.json'
    if tree is None:tree=json.loads(path.read_text()) if path.exists() else {'nodes':{}}
    raw=tree.get('nodes',{})
    nodes=raw if isinstance(raw,dict) else {str(n.get('id',i)):n for i,n in enumerate(raw) if isinstance(n,dict)}
    trained={k:n for k,n in nodes.items() if n.get('status')=='trained'
             and n.get('evidence_phase')!='confirmation' and _value(n) is not None}
    roots={k:n for k,n in trained.items() if not n.get('parent')}
    children={k:n for k,n in trained.items() if n.get('parent')}
    metric=(tree.get('research_metric') or (memory or {}).get('research_metric') or {'name':'validation_reward','direction':'maximize'})
    sign=-1 if metric.get('direction')=='minimize' else 1
    best=lambda items:max(items.items(),key=lambda kv:sign*_value(kv[1]),default=('',{}))
    root,child=best(roots),best(children)
    root_val,child_val=_value(root[1]),_value(child[1])
    by_strategy=defaultdict(list);by_family=defaultdict(list)
    for name,node in children.items():
        config=node.get('config') if isinstance(node.get('config'),dict) else {}
        strategy=str(node.get('strategy') or config.get('model') or 'unknown')
        family=str(node.get('family') or (node.get('scientific_selection') or {}).get('family') or strategy)
        parent_val=_value(nodes.get(str(node.get('parent')),{}));value=_value(node)
        row={'node':name,'val':value,'parent':node.get('parent'),'family':family,
             'delta_vs_parent':sign*(value-parent_val) if parent_val is not None else None}
        by_strategy[strategy].append(row);by_family[family].append(row)
    def stats(rows):
        vals=[r['val'] for r in rows];deltas=[r['delta_vs_parent'] for r in rows if r['delta_vs_parent'] is not None]
        mean=lambda x:sum(x)/len(x) if x else None
        std=lambda x:math.sqrt(sum((v-mean(x))**2 for v in x)/(len(x)-1)) if len(x)>1 else None
        return {'n':len(rows),'mean_val':mean(vals),'std_val':std(vals),'mean_delta_vs_parent':mean(deltas),
                'std_delta_vs_parent':std(deltas),'win_rate_vs_parent':sum(v>0 for v in deltas)/len(deltas) if deltas else None,
                'inference':'Descriptive across configurations; not independent repeated-seed confirmation'}
    findings=[]
    if root_val is not None and child_val is not None:
        delta=sign*(child_val-root_val)
        findings.append('root_dominance' if delta<=0 else f'development_child_lift:{delta:.6g}')
    evidence_path=run_dir/'development_feedback.json'
    evidence=json.loads(evidence_path.read_text()) if evidence_path.exists() else {}
    if evidence and evidence.get('evidence_phase')!='development':raise ValueError('Non-development feedback cannot enter search memory')
    guidance=[
        'Treat each blueprint as a falsifiable hypothesis, not a fixed architecture.',
        'Choose replacement, feature fusion, joint training, cross-fitted residual, stacking, or simplification from development evidence.',
        'Retain the exact strongest historical recipe as a benchmark; retaining its computation graph is optional.',
        'Use grouped OOF predictions to train stackers/residuals and learn combination weights; no global fixed .25 rule.',
        'Record effective training policy, convergence, independent sample groups, costs and paired comparisons.',
        'An honest null result is valid. Do not add complexity solely to beat a baseline.',
    ]
    policy={'ranking_boosts':{},'ranking_penalties':{},'implementation_guidance':guidance,
            'validation_recommendations':['Use matched group folds, strong controls and paired development gains; reserve confirmation until selection freezes.'],
            'suppressed_families':[],'hardcoded_model_preferences':False}
    return {'format':'vc_demo_framework_feedback.v2','evidence_phase':'development',
        'created_at':datetime.now(timezone.utc).isoformat(),'run_dir':str(run_dir),'metric':metric,
        'target_val_macro_f1':target_val_macro_f1,'best_root':{'node':root[0],'val':root_val},
        'best_child':{'node':child[0],'val':child_val},'strategy_stats':{k:stats(v) for k,v in by_strategy.items()},
        'family_stats':{k:stats(v) for k,v in by_family.items()},'development_evidence':selection_context(evidence),
        'artifact_usefulness':{},'findings':findings,'policy':policy}


def write_framework_feedback(run_dir: Path, feedback: dict[str,Any]) -> Path:
    if feedback.get('evidence_phase')!='development':raise ValueError('Search feedback must be development-only')
    path=run_dir/'framework_feedback.json';write_record(path,selection_context(feedback))
    lines=['# Development Research Feedback','','Confirmation metrics are not read or exported into this artifact.','',
           '## Findings','',*[f'- {v}' for v in feedback.get('findings',[])],
           '','## Agent Decisions','',*[f'- {v}' for v in feedback.get('policy',{}).get('implementation_guidance',[])]]
    (run_dir/'framework_feedback.md').write_text('\n'.join(lines)+'\n')
    return path
