"""Shared execution loop operated by the active Codex, never an internal LLM API."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
import copy
import fcntl
import importlib.util
import importlib.metadata
import json
from pathlib import Path
import py_compile
import re
import sys
import time

from vc_demo.harness.research_contract import digest, file_digest, freeze_record, write_record
from .identity import COMPOSITIONS, artifact_identity, measurement_identity, semantic_identity
from .metrics import MetricSpec, paired_evidence
from .policy import backpropagate, parent_ranking, priority
from .verdicts import control_verdict


class Session:
    def __init__(self, run_dir):
        self.run=Path(run_dir).resolve()

    @classmethod
    def initialize(cls, run_dir, spec):
        self=cls(run_dir)
        if self.run.exists() and any(self.run.iterdir()):
            raise ValueError('Initialize a fresh directory; never reset an executed run')
        spec=copy.deepcopy(spec)
        required={'task_id','dataset_sha256','split_sha256','label_semantics','input_policy','prior_test_exposure',
            'metric','development_contract','inputs','benchmarks','benchmark_recipes','reference_benchmark','budget','policy','resources','minimum_effect'}
        if not required.issubset(spec) or spec.get('schema_version')!='research_v2':
            raise ValueError('A full versioned task, metric, baseline and resource contract is required')
        metric=MetricSpec.from_dict(spec['metric'])
        if spec['reference_benchmark'] not in spec['benchmarks'] or len(set(spec['benchmarks']))!=len(spec['benchmarks']):
            raise ValueError('Declare the exact strong reference and required baseline IDs')
        for name in spec['benchmarks']:self._name(name)
        if set(spec['budget'])!={'coverage','optimization','confirmation'} or any(type(v)!=int or v<0 for v in spec['budget'].values()):
            raise ValueError('Separate nonnegative phase budgets are required')
        p=spec['policy']
        if p.get('parent_policy') not in {'uct_parent_scheduler','global_queue'}:
            raise ValueError('Name the actual policy; a flat parent scheduler is not full tree-descent MCTS')
        if type(p.get('queue_capacity'))!=int or p['queue_capacity']<1 or type(p.get('min_new_proposals'))!=int or p['min_new_proposals']<1:
            raise ValueError('Declare queue and replenishment budgets')
        if p['queue_capacity']<p['min_new_proposals']:
            raise ValueError('Queue capacity cannot be smaller than the proposal batch')
        limit=p.get('parent_active_limit')
        if limit is not None and (type(limit)!=int or limit<1):raise ValueError('Invalid active proposal limit')
        if spec['minimum_effect']<0:raise ValueError('Minimum practical effect cannot be negative')
        self._deadline(spec)
        from .postselection import validate_plans
        validate_plans(spec)
        contract=Path(spec['development_contract']).resolve()
        self._validate_contract(json.loads(contract.read_text()),metric)
        spec['development_contract']=str(contract)
        spec['development_contract_sha256']=file_digest(contract)
        if not spec['inputs']:raise ValueError('Explicit source-backed development inputs are required')
        for info in spec['inputs'].values():
            if info.get('scope') not in {'development','public'} or file_digest(Path(info['path']))!=info['sha256']:
                raise ValueError('Search inputs must be content-verified development/public sources')
        if set(spec['benchmark_recipes'])!=set(spec['benchmarks']):
            raise ValueError('Register complete expected recipes, not only benchmark names')
        actual=self._environment()
        identities={}
        for name,recipe in spec['benchmark_recipes'].items():
            recipe['environment']={**actual,**recipe['environment']}
            if recipe['input_sha256']!={r:v['sha256'] for r,v in spec['inputs'].items()}:
                raise ValueError('Expected benchmark input identity differs from the registered task')
            identities[name]=semantic_identity(recipe,metric.identity)
        spec['benchmark_identities']=identities
        engine_files=[*Path(__file__).parent.glob('*.py'),Path(sys.modules[digest.__module__].__file__)]
        spec['engine_sha256']={str(p.resolve()):file_digest(p) for p in engine_files}
        spec['engine_environment']=self._environment()
        freeze_record(self.run/'research_protocol_v2.json',spec)
        freeze_record(self.run/'protocol_identity.json',{'sha256':digest(spec),'metric_id':metric.identity})
        state={'schema_version':'research_v2','cycle':0,'replenishments':{},'nodes':{},'events':[],
            'selection_closed':False,'budget_used':{'coverage':0,'optimization':0,'confirmation':0}}
        write_record(self.run/'session_state.json',state)
        return self

    @staticmethod
    def _name(value):
        if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}',value):
            raise ValueError('Unsafe node ID')

    @staticmethod
    def _deadline(spec):
        r=spec['resources']
        if not r.get('authorization_id'):raise ValueError('Record the user-authorized resource allocation')
        deadline=datetime.fromisoformat(r['deadline_utc'])
        if deadline.tzinfo is None or datetime.now(timezone.utc)>=deadline:
            raise ValueError('Approved deadline reached; no automatic spending extension')

    @staticmethod
    def _validate_contract(c, metric):
        rows=c['row_ids'];groups=c['groups'];seeds=c['seeds']
        if not rows or len(set(rows))!=len(rows) or len(groups)!=len(rows) or len(c['targets'])!=len(rows) or not seeds or len(set(seeds))!=len(seeds):
            raise ValueError('Invalid source row/group/label/seed contract')
        expected=[]
        for i,group in enumerate(groups):
            row=[]
            for seed in seeds:
                folds=[f for f in c['folds'] if f['seed']==seed and group in f['validation_groups']]
                if len(folds)!=1:raise ValueError('Each row needs exactly one OOF fold per seed')
                row.append(folds[0]['fold_id'])
            expected.append(row)
        identifiers=[]
        for f in c['folds']:
            train,valid=set(f['train_groups']),set(f['validation_groups'])
            if not train or not valid or train&valid or train|valid!=set(groups) or f['seed'] not in seeds:
                raise ValueError('Fold training/validation groups must partition development groups')
            identifiers.append((f['seed'],f['fold_id']))
        if len(set(identifiers))!=len(identifiers):raise ValueError('Duplicate fold identifiers')
        if c.get('fold_ids')!=expected:raise ValueError('Stored OOF row-to-fold assignment differs')
        if metric.name=='macro_f1' and not set(c['targets']).issubset(metric.labels):raise ValueError('Labels differ from fixed vocabulary')

    def _load(self):
        spec=json.loads((self.run/'research_protocol_v2.json').read_text())
        if digest(spec)!=json.loads((self.run/'protocol_identity.json').read_text())['sha256']:
            raise ValueError('Frozen task contract changed')
        for path,sha in spec['engine_sha256'].items():
            if file_digest(Path(path))!=sha:raise ValueError('Engine code drift: register a new version/run')
        if spec['engine_environment']!=self._environment():raise ValueError('Metric/engine environment changed')
        if file_digest(Path(spec['development_contract']))!=spec['development_contract_sha256']:
            raise ValueError('Source development contract changed')
        return spec,json.loads((self.run/'session_state.json').read_text())

    @staticmethod
    def _environment():
        return {'python':sys.version.split()[0],**{p:importlib.metadata.version(p) for p in ('numpy','scipy','scikit-learn')}}

    @contextmanager
    def _transaction(self, *, search=True):
        with (self.run/'session.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            spec,state=self._load();self._deadline(spec)
            if search and state['selection_closed']:raise ValueError('Confirmation closed this run to further search')
            yield spec,state
            write_record(self.run/'session_state.json',state)
            # A derived trace is rewritten from the committed state, not independently appended.
            trace=''.join(json.dumps(e,sort_keys=True)+'\n' for e in state['events'])
            temporary=self.run/'events.jsonl.tmp';temporary.write_text(trace);temporary.replace(self.run/'events.jsonl')

    @staticmethod
    def _event(state, kind, **fields):
        state['events'].append({'sequence':len(state['events']),'event':kind,'cycle':state['cycle'],
            'utc':datetime.now(timezone.utc).isoformat(),**fields})

    def context(self):
        spec,state=self._load()
        return self._context(spec,state)

    def plan_analysis(self, analysis_id, plan, reason, evidence_id):
        self._name(analysis_id)
        if not reason:
            raise ValueError('Explain the development-conditioned analysis question')
        from .postselection import plans_for, validate_plans
        with self._transaction() as (spec,state):
            if self._context(spec,state)['evidence_id']!=evidence_id:
                raise ValueError('Use the current development-only evidence snapshot')
            if analysis_id in plans_for(spec,state):
                raise ValueError('Version a new analysis ID rather than replacing a registered question')
            self._development_only(plan)
            validate_plans({**spec,'analyses':{analysis_id:plan}})
            state.setdefault('analysis_plan_additions',{})[analysis_id]={'plan':copy.deepcopy(plan),
                'reason':reason,'evidence_id':evidence_id,'evidence_phase':'development'}
            self._event(state,'analysis_planned_before_freeze',analysis_id=analysis_id)
        return {'registered_analysis':analysis_id,'phase':'development','opens_confirmation':False}

    def _context(self,spec,state):
        metric=MetricSpec.from_dict(spec['metric'])
        nodes=state['nodes']
        summaries={name:{k:n.get(k) for k in ('status','phase','parent_id','relation','score','paired_evidence',
            'semantic_id','optimization_visits','optimization_value','hypothesis','diagnostics','attempts',
            'proposed_recipe','required_artifacts','sealed_recipe','execution')}
            for name,n in nodes.items()}
        for name,n in nodes.items():
            if n['status']=='trained':summaries[name]['development_receipt']=str(self.run/'nodes'/name/'development_receipt.json')
        result={'schema_version':'research_v2','evidence_phase':'development','task_id':spec['task_id'],
            'metric':asdict(metric),'metric_id':metric.identity,'cycle':state['cycle'],
            'budget':spec['budget'],'budget_used':state['budget_used'],'nodes':summaries,
            'inputs':spec['inputs'],'prior_test_exposure':spec['prior_test_exposure'],
            'scientific_contract':{k:spec[k] for k in ('dataset_sha256','split_sha256','label_semantics',
                'input_policy','development_contract','development_contract_sha256','benchmarks','reference_benchmark','minimum_effect')},
            'allowed_compositions':sorted(COMPOSITIONS),'agent_defined_candidates_allowed':True,
            'parent_ranking':parent_ranking(nodes,metric,spec['policy']),
            'policy_identity':spec['policy']['parent_policy'],'next_action':self._action(spec,state)}
        from .postselection import plans_for
        result['registered_analysis_ids']=sorted(plans_for(spec,state))
        self._development_only(result)
        identity=digest(result)
        freeze_record(self.run/'evidence'/f'{identity}.json',result)
        return {**result,'evidence_id':identity}

    @staticmethod
    def _development_only(value):
        if isinstance(value,dict):
            if value.get('evidence_phase','development')!='development':raise ValueError('Non-development evidence cannot guide research')
            for key,item in value.items():
                if key in {'test_score','test_metrics','heldout_metrics','confirmation_metrics','test_macro_f1','test_loss'}:
                    raise ValueError('Heldout evidence cannot enter a research decision')
                Session._development_only(item)
        elif isinstance(value,list):
            for item in value:Session._development_only(item)

    def _action(self,spec,state):
        if state['selection_closed']:
            lock=json.loads((self.run/'confirmation_lock_v2.json').read_text())
            finalists=list(lock['selected'])
            if any(name not in state.get('confirmation_reports',{}) for name in finalists):
                return 'predict_frozen_confirmation_without_refitting'
            from .postselection import plans_for
            reports=state.get('analysis_reports',{})
            for aid,plan in plans_for(spec,state).items():
                done=all(aid+'::'+name in reports for name in finalists) if plan['target_policy']=='each_finalist' else any(k.startswith(aid+'::') for k in reports)
                if not done:return 'execute_registered_report_only_analyses'
            return 'write_final_report_selection_remains_closed'
        active=[n for n in state['nodes'].values() if n['status'] in {'selected','repair_needed'}]
        if active:return 'implement_repair_acquire_or_execute_selected_now'
        for name in spec['benchmarks']:
            if self._resolved(state['nodes'],name) is None:return 'submit_or_execute_required_benchmarks'
        if self._coverage_handled(state)<spec['budget']['coverage']:return 'submit_or_execute_registered_coverage'
        if state['budget_used']['optimization']>=spec['budget']['optimization']:return 'freeze_finalists_or_report_null_result'
        if state.get('proposal_exhaustion'):
            queued=any(n['status']=='candidate_queued' and n['phase']=='optimization' for n in state['nodes'].values())
            return 'rerank_global_queue_and_select' if queued else 'freeze_documented_feasible_pool_exhaustion'
        if state['replenishments'].get(str(state['cycle']),0)<spec['policy']['min_new_proposals']:
            return 'research_and_submit_new_proposals_now'
        return 'rerank_global_queue_and_select'

    @staticmethod
    def _coverage_handled(state):
        return sum(n['phase']=='coverage' and n['status'] in {'trained','duplicate','skipped','failed'}
            for n in state['nodes'].values())

    @staticmethod
    def _resolved(nodes,name):
        visited=set()
        while name in nodes and name not in visited:
            visited.add(name);node=nodes[name]
            if node['status']=='trained':return node
            if node['status']!='duplicate':return None
            name=node['duplicate_of']
        return None

    def propose(self,proposals):
        accepted=[]
        with self._transaction() as (spec,state):
            context=self._context(spec,state)
            metric=MetricSpec.from_dict(spec['metric'])
            for raw in proposals:
                n=copy.deepcopy(raw);self._name(n['id'])
                self._development_only(n)
                if n['id'] in state['nodes']:raise ValueError('Node IDs are immutable; revise with a new ID')
                if n.get('phase') not in {'benchmark','coverage','optimization'}:raise ValueError('Unknown research phase')
                if n['phase']=='benchmark' and n['id'] not in spec['benchmarks']:raise ValueError('Unknown required baseline')
                if n['phase']!='benchmark' and spec['budget'][n['phase']]==0:raise ValueError('No registered phase budget')
                h=n['hypothesis']
                for key in ('statement','expected_change','falsification','evidence_ids','composition'):
                    if not h.get(key):raise ValueError('Incomplete research hypothesis: '+key)
                if h['composition'] not in COMPOSITIONS:raise ValueError('Unknown open composition')
                if not n.get('proposed_recipe') or set(n['proposed_recipe'])!={'parameters','training'}:
                    raise ValueError('Declare the intended model/training policy, not only a family name')
                if context['evidence_id'] not in h['evidence_ids']:raise ValueError('Use the current immutable development context')
                parent=n.get('parent_id')
                if parent is not None:
                    resolved=self._resolved(state['nodes'],parent)
                    if resolved is None:raise ValueError('Parent evidence must be trained')
                    n['requested_parent_id']=parent
                    parent=resolved['id'];n['parent_id']=parent
                if n['phase']=='optimization' and spec['policy']['parent_policy']=='uct_parent_scheduler':
                    eligible={r['node'] for r in context['parent_ranking']}
                    if parent not in eligible:raise ValueError('Choose an eligible trained parent or register a flat-queue policy')
                    if not h.get('parent_conditioning'):raise ValueError('Explain how parent evidence changes this proposal')
                    if parent!=context['parent_ranking'][0]['node'] and not h.get('parent_override_reason'):
                        raise ValueError('Explain an intentional override of the UCT parent recommendation')
                n['relation']=h['composition'] if n['phase']=='optimization' else 'comparison'
                if n['phase']!='optimization':n['reference_id']=parent;n['parent_id']=None
                estimate=n['estimate'];self._validate_estimate(estimate,metric,state)
                n.update(status='candidate_queued',optimization_visits=0,optimization_value=0.,attempts=[],created_cycle=state['cycle'])
                n['ranking']=priority(estimate,spec['policy'])
                state['nodes'][n['id']]=n;accepted.append(n['id'])
                self._event(state,'proposal_submitted',node=n['id'],phase=n['phase'],evidence_ids=h['evidence_ids'])
            count=sum(state['nodes'][name]['phase']=='optimization' for name in accepted)
            cycle=str(state['cycle']);state['replenishments'][cycle]=state['replenishments'].get(cycle,0)+count
            self._prune(spec,state)
        return accepted

    def _validate_estimate(self,estimate,metric,state):
        self._development_only(estimate)
        if estimate.get('metric_id')!=metric.identity:raise ValueError('Ranking metric differs from reward')
        if estimate['basis']=='measured':
            source=state['nodes'].get(estimate.get('evidence_node'),{})
            evidence=source.get('paired_evidence')
            if not evidence or evidence['metric_id']!=metric.identity or estimate['expected_gain']!=evidence['paired_delta']:
                raise ValueError('Measured gain must reference actual matching paired development evidence')
            if estimate.get('uncertainty_type')!='conditional_group_bootstrap':raise ValueError('Name the uncertainty actually used')
            ci=evidence['delta_ci95']
            if not ci or estimate['uncertainty']!=(ci[1]-ci[0])/2:raise ValueError('Measured uncertainty differs from the stored group interval')

    def rerank(self,updates,evidence_id):
        with self._transaction() as (spec,state):
            if self._context(spec,state)['evidence_id']!=evidence_id:raise ValueError('Use the current evidence snapshot')
            for name,estimate in updates.items():
                n=state['nodes'][name]
                if n['status']!='candidate_queued':raise ValueError('Do not revise completed measurements or selected implementations')
                self._validate_estimate(estimate,MetricSpec.from_dict(spec['metric']),state)
                priority(estimate,spec['policy'])
                self._event(state,'research_estimate_revised',node=name,old=n['estimate'],new=estimate,evidence_id=evidence_id)
                n['estimate']=copy.deepcopy(estimate)
            self._prune(spec,state)

    def declare_exhaustion(self,reason,attempts):
        if not reason or not attempts or any(not a.get('action') or not a.get('evidence') for a in attempts):
            raise ValueError('Feasible-space exhaustion requires actual research/implementation attempts')
        with self._transaction() as (spec,state):
            if not spec['policy'].get('allow_documented_exhaustion',False):raise ValueError('Exhaustion stopping was not registered')
            state['proposal_exhaustion']={'reason':reason,'attempts':copy.deepcopy(attempts)}
            self._event(state,'new_proposal_exhaustion_declared_continue_existing_queue',reason=reason)

    def _prune(self,spec,state):
        queued=[n for n in state['nodes'].values() if n['phase']=='optimization' and n['status']=='candidate_queued']
        for n in queued:n['ranking']=priority(n['estimate'],spec['policy'])
        ranked=sorted(queued,key=lambda n:(-n['ranking']['scientific_priority'],n['id']))
        for n in ranked[spec['policy']['queue_capacity']:]:
            n['status']='pruned_not_selected'
            self._event(state,'global_prune',node=n['id'],reason='registered global queue capacity')

    def select(self):
        with self._transaction() as (spec,state):
            if any(n['status'] in {'selected','repair_needed'} for n in state['nodes'].values()):
                raise ValueError('Handle the selected candidate now: implement, repair, acquire or documented skip')
            missing=[name for name in spec['benchmarks'] if self._resolved(state['nodes'],name) is None]
            if missing:
                queued=[state['nodes'][name] for name in missing if name in state['nodes'] and state['nodes'][name]['status']=='candidate_queued']
                if not queued:raise ValueError('Required benchmarks still need source-backed implementation')
                queued.sort(key=lambda n:(n['id']!=spec['reference_benchmark'],n['id']))
            else:
                phase='coverage' if self._coverage_handled(state)<spec['budget']['coverage'] else 'optimization'
                if state['budget_used'][phase]>=spec['budget'][phase]:raise ValueError('Registered training allocation exhausted')
                if phase=='optimization' and not state.get('proposal_exhaustion') and state['replenishments'].get(str(state['cycle']),0)<spec['policy']['min_new_proposals']:
                    raise ValueError('Replenish the research pool after the last completed rollout before selecting again')
                self._prune(spec,state)
                queued=[n for n in state['nodes'].values() if n['phase']==phase and n['status']=='candidate_queued']
                queued.sort(key=lambda n:(-priority(n['estimate'],spec['policy'])['scientific_priority'],n['id']))
                if not queued:raise ValueError('No queued candidate: research/propose or document real exhaustion; not a completed study')
            n=queued[0];n['status']='selected'
            self._event(state,'candidate_selected',node=n['id'],phase=n['phase'],ranking=n['ranking'])
            return copy.deepcopy(n)

    def seal(self,name,execution,recipe):
        with self._transaction() as (spec,state):
            n=state['nodes'][name]
            if n['status'] not in {'selected','repair_needed'}:raise ValueError('Only the selected candidate can be implemented/sealed')
            recipe=copy.deepcopy(recipe)
            self._development_only(recipe)
            if recipe['parameters']!=n['proposed_recipe']['parameters'] or recipe['training']!=n['proposed_recipe']['training']:
                if not execution.get('design_revision_reason'):
                    raise ValueError('Record why the actual implementation improves/changes the selected proposal')
            files=execution['code_files']
            if 'provider' not in files:raise ValueError('Implement the actual provider, not an automatic architecture proxy')
            hashes={role:file_digest(Path(p)) for role,p in files.items()}
            if recipe['code_sha256']!=hashes:raise ValueError('Declared implementation differs from actual source')
            for p in files.values():
                if Path(p).suffix=='.py':py_compile.compile(str(p),doraise=True)
            if recipe['input_sha256']!={role:v['sha256'] for role,v in spec['inputs'].items()}:
                raise ValueError('Recipe must bind the actual registered development inputs')
            actual=self._environment()
            for package,version in recipe['environment'].items():
                current=actual.get(package) or importlib.metadata.version(package)
                if current!=version:raise ValueError('Declared environment differs from installed dependency: '+package)
            recipe['environment']={**actual,**recipe['environment']}
            artifacts=execution.get('artifact_files',{})
            required=n.get('required_artifacts',{})
            if not set(required)<=set(artifacts):
                raise ValueError('Acquire required artifacts or propose an explicitly different candidate; no silent omission/fallback')
            if recipe['artifact_sha256']!={role:artifact_identity(v['path']) for role,v in artifacts.items()}:
                raise ValueError('Acquire and verify declared artifact files before executing')
            for role,v in artifacts.items():
                if not v.get('source') or not v.get('alignment') or v.get('status') not in {'original_public','derived','reconstructed_compatibility'}:
                    raise ValueError('Artifact provenance and task-appropriate alignment are required')
                requirement=required.get(role,{})
                if requirement.get('kind') and requirement['kind']!=v.get('kind'):
                    raise ValueError('Artifact type is not the required module; a graph is not a pretrained checkpoint')
                if v['status'] not in requirement.get('allowed_statuses',['original_public','derived','reconstructed_compatibility']):
                    raise ValueError('Actual artifact provenance is not allowed by this hypothesis')
                for name in requirement.get('required_files',[]):
                    relative=Path(name)
                    expected=Path(v['path'])/relative
                    if relative.is_absolute() or '..' in relative.parts or not expected.is_file() or not expected.stat().st_size:
                        raise ValueError('Required artifact contents are missing: '+name)
            semantic=semantic_identity(recipe,MetricSpec.from_dict(spec['metric']).identity)
            if n['phase']=='benchmark' and semantic!=spec['benchmark_identities'][name]:
                raise ValueError('Exact benchmark recipe changed; a weaker same-name reference is not allowed')
            measurement=measurement_identity(semantic,n.get('replicate'))
            for prior in state['nodes'].values():
                if prior['id']!=name and prior.get('measurement_id')==measurement and prior['status']=='trained':
                    n.update(status='duplicate',duplicate_of=prior['id'],semantic_id=semantic,measurement_id=measurement)
                    self._event(state,'duplicate_measurement_reused',node=name,original=prior['id'])
                    return {'duplicate_of':prior['id']}
            n.update(execution=copy.deepcopy(execution),sealed_recipe=recipe,semantic_id=semantic,
                measurement_id=measurement,status='selected')
            self._event(state,'implementation_sealed',node=name,semantic_id=semantic,measurement_id=measurement)
            return {'semantic_id':semantic,'measurement_id':measurement}

    def _verify_implementation(self,n):
        for role,path in n['execution']['code_files'].items():
            if file_digest(Path(path))!=n['sealed_recipe']['code_sha256'][role]:raise ValueError('Sealed implementation changed; explicitly revise the candidate')
        for role,v in n['execution'].get('artifact_files',{}).items():
            if artifact_identity(v['path'])!=n['sealed_recipe']['artifact_sha256'][role]:raise ValueError('Sealed artifact changed')
        for package,version in n['sealed_recipe']['environment'].items():
            current=sys.version.split()[0] if package=='python' else importlib.metadata.version(package)
            if current!=version:raise ValueError('Sealed execution environment changed: '+package)
        return Path(n['execution']['code_files']['provider'])

    def _provider(self,n):
        path=self._verify_implementation(n)
        spec=importlib.util.spec_from_file_location('research_provider_'+file_digest(path)[:16],path)
        module=importlib.util.module_from_spec(spec)
        sys.modules[spec.name]=module
        spec.loader.exec_module(module)
        return module

    def execute(self,name):
        # One execution lease covers provider evaluation and the atomic reward commit.
        # Context remains readable; another execute cannot retrain the same selected node.
        error=None;receipt=None
        with self._transaction() as (spec,state):
            n=state['nodes'][name]
            if n['status']=='trained':
                self._verify_implementation(n)
                self._check_checkpoints(n['receipt']['checkpoint_files'])
                return self._receipt(n)
            if n['status']!='selected' or 'sealed_recipe' not in n:raise ValueError('Implement and seal the selected candidate first')
            directory=self.run/'nodes'/name;directory.mkdir(parents=True,exist_ok=True)
            receipt_path=directory/'development_receipt.json'
            attempt_start=time.monotonic()
            try:
                for info in spec['inputs'].values():
                    if file_digest(Path(info['path']))!=info['sha256']:raise ValueError('Registered source input changed')
                module=self._provider(n)
                contract=json.loads(Path(spec['development_contract']).read_text())
                request={'task_id':spec['task_id'],'phase':'development','node_id':name,'metric':spec['metric'],
                    'metric_id':MetricSpec.from_dict(spec['metric']).identity,'development_contract':contract,
                    'inputs':spec['inputs'],'recipe':n['sealed_recipe'],'execution':n['execution'],
                    'output_dir':str(directory),'replicate':n.get('replicate'),'composition':n['hypothesis']['composition'],
                    'measurement_id':n['measurement_id'],'semantic_id':n['semantic_id']}
                if receipt_path.is_file():
                    receipt=json.loads(receipt_path.read_text())
                    if receipt['measurement_id']!=n['measurement_id']:raise ValueError('Cached receipt belongs to another measurement')
                    self._check_checkpoints(receipt['checkpoint_files'])
                else:
                    start=time.monotonic();result=module.evaluate_development(request)
                    self._deadline(spec)
                    table=result['prediction_table'];metric=MetricSpec.from_dict(spec['metric'])
                    if table.get('metric_id')!=metric.identity or table.get('evidence_phase')!='development':raise ValueError('Wrong metric or heldout evidence returned by development provider')
                    for key in ('row_ids','groups','targets','seeds','fold_ids'):
                        if table[key]!=contract[key]:raise ValueError('Prediction contract changed: '+key)
                    if result['fit_audit']!=contract['folds']:raise ValueError('Provider OOF fit groups differ from the registered splits')
                    if n['hypothesis']['composition'] in {'crossfit_residual','crossfit_stack'}:
                        self._composition_audit(result.get('composition_audit'),contract)
                    score=metric.score(table)
                    diagnostics=result['diagnostics']
                    for key in ('solver','converged','train_loss','inner_validation_policy','outer_fit_count'):
                        if key not in diagnostics:raise ValueError('Missing actual training diagnostic: '+key)
                    if diagnostics['outer_fit_count']!=len(contract['folds']):raise ValueError('Outer fit count differs from OOF audit')
                    roles=result.get('consumed_artifact_roles',[])
                    modules=result.get('consumed_module_roles',[])
                    if not isinstance(roles,list) or not isinstance(modules,list) or any(not isinstance(r,str) for r in roles+modules):
                        raise ValueError('Consumed resource/module roles must be explicit string lists')
                    consumed=set(roles)
                    if consumed!=set(n['sealed_recipe']['artifact_sha256']):raise ValueError('Declared artifacts were not actually consumed; do not claim their use')
                    checkpoints={}
                    for path in result['checkpoint_files']:
                        p=Path(path).resolve()
                        if not p.is_relative_to(directory) or p.stat().st_size==0:raise ValueError('Persist actual fitted checkpoints in the node output directory')
                        checkpoints[str(p)]=file_digest(p)
                    if not checkpoints:raise ValueError('Save fitted artifacts before confirmation, not only a score')
                    receipt={'measurement_id':n['measurement_id'],'semantic_id':n['semantic_id'],'metric_id':metric.identity,
                        'score':score,'prediction_table':table,'fit_audit':result['fit_audit'],'diagnostics':diagnostics,
                        'composition_audit':result.get('composition_audit'),
                        'inner_group_audit_validated':bool(result.get('composition_audit')),
                        'consumed_module_roles':result.get('consumed_module_roles',[]),
                        'checkpoint_files':checkpoints,'wall_seconds':time.monotonic()-start,'evidence_phase':'development'}
                    freeze_record(receipt_path,receipt)
                table=receipt['prediction_table'];metric=MetricSpec.from_dict(spec['metric'])
                if receipt.get('metric_id')!=metric.identity or table.get('metric_id')!=metric.identity or table.get('evidence_phase')!='development':
                    raise ValueError('Cached receipt does not contain matching development evidence')
                for key in ('row_ids','groups','targets','seeds','fold_ids'):
                    if table[key]!=contract[key]:raise ValueError('Cached predictions differ from source contract')
                if receipt['fit_audit']!=contract['folds'] or receipt['score']!=metric.score(table):
                    raise ValueError('Cached OOF audit or reward changed')
                if n['hypothesis']['composition'] in {'crossfit_residual','crossfit_stack'}:
                    self._composition_audit(receipt.get('composition_audit'),contract)
                compact={k:v for k,v in receipt.items() if k not in {'prediction_table','fit_audit','composition_audit'}}
                n.update(status='trained',score=receipt['score'],receipt=compact,diagnostics=receipt['diagnostics'],
                    receipt_sha256=file_digest(receipt_path))
                reference=self._resolved(state['nodes'],spec['reference_benchmark'])
                if reference is not None and name!=spec['reference_benchmark']:
                    n['paired_evidence']=paired_evidence(MetricSpec.from_dict(spec['metric']),receipt['prediction_table'],
                        self._receipt(reference)['prediction_table'],draws=spec['policy'].get('bootstrap_draws',500),
                        minimum_effect=spec['minimum_effect'])
                if n['phase']=='optimization':
                    path=backpropagate(state['nodes'],name,MetricSpec.from_dict(spec['metric']).sign*n['score'])
                    self._event(state,'optimization_backpropagated',node=name,path=path)
                    state['cycle']+=1
                if n['phase']!='benchmark':state['budget_used'][n['phase']]+=1
                self._event(state,'development_completed',node=name,phase=n['phase'],score=n['score'],metric_id=receipt['metric_id'])
            except Exception as exc:
                n['status']='repair_needed';n['attempts'].append({'stage':'execution','error':str(exc),
                    'wall_seconds':time.monotonic()-attempt_start})
                self._event(state,'repair_required_now',node=name,error=str(exc))
                error=exc
        if error is not None:raise ValueError('Repair the selected candidate now or document a real skip: '+str(error)) from error
        return receipt

    @staticmethod
    def _composition_audit(records,contract):
        if not records or len(records)!=len(contract['folds']):raise ValueError('Grouped OOF combination requires an actual per-fit inner audit')
        by_id={(r['seed'],r['fold_id']):r for r in records}
        if len(by_id)!=len(records):raise ValueError('Duplicate composition audit fits')
        for outer in contract['folds']:
            audit=by_id[(outer['seed'],outer['fold_id'])]
            allowed=set(outer['train_groups'])
            if audit.get('weight_training')!='grouped_oof' or set(audit.get('weight_fit_groups',[]))!=allowed:
                raise ValueError('Combination weights must use training-only grouped OOF designs')
            inner=audit.get('inner_folds',[])
            if not inner:raise ValueError('Missing inner OOF folds')
            covered=set()
            for f in inner:
                train,valid=set(f['train_groups']),set(f['validation_groups'])
                if not train or not valid or train&valid or not (train|valid)<=allowed:
                    raise ValueError('Inner OOF leaks outer validation or overlaps group roles')
                covered|=valid
            if covered!=allowed:raise ValueError('Incomplete training-only inner OOF design')

    @staticmethod
    def _check_checkpoints(checkpoints):
        if not checkpoints:raise ValueError('Missing fitted checkpoint provenance')
        for path,sha in checkpoints.items():
            if file_digest(Path(path))!=sha:raise ValueError('Saved fitted checkpoint changed')

    def _receipt(self,node):
        path=self.run/'nodes'/node['id']/'development_receipt.json'
        if file_digest(path)!=node['receipt_sha256']:raise ValueError('Committed development evidence changed')
        return json.loads(path.read_text())

    def skip(self,name,reason,attempts):
        if not reason or not attempts or any(not a.get('action') or not a.get('evidence') for a in attempts):
            raise ValueError('Same-session implementation/acquisition attempts need concrete evidence')
        with self._transaction() as (spec,state):
            n=state['nodes'][name]
            if n['status'] not in {'selected','repair_needed'}:raise ValueError('Only an actively handled candidate may be skipped')
            n.update(status='skipped',skip_reason=reason)
            n['attempts'].extend(copy.deepcopy(attempts))
            self._event(state,'candidate_skipped_continue_queue',node=name,reason=reason)

    def record_control(self,control_id,target,removed_roles,intervention=None,rationale=''):
        self._name(control_id)
        if not removed_roles or not rationale:raise ValueError('State the intended intervention and matched-control rationale')
        with self._transaction() as (spec,state):
            before=self._resolved(state['nodes'],target)
            after=self._resolved(state['nodes'],intervention) if intervention else None
            if before is None:raise ValueError('Controls require actual trained development evidence')
            consumed=set(before['receipt'].get('consumed_module_roles',[]))|set(before['sealed_recipe']['artifact_sha256'])
            remaining=(set(after['receipt'].get('consumed_module_roles',[]))|set(after['sealed_recipe']['artifact_sha256'])) if after else consumed
            value=control_verdict(removed_roles=removed_roles,consumed_roles=consumed,
                changed_dependency_identity=bool(after and after['semantic_id']!=before['semantic_id']),
                removed_roles_still_consumed=remaining)
            value.update(target=target,intervention=intervention,removed_roles=removed_roles,rationale=rationale,
                evidence_phase='development')
            if after and value['control_applied']:
                value['paired_development_evidence']=paired_evidence(MetricSpec.from_dict(spec['metric']),
                    self._receipt(after)['prediction_table'],self._receipt(before)['prediction_table'],
                    draws=spec['policy'].get('bootstrap_draws',500),minimum_effect=spec['minimum_effect'])
            freeze_record(self.run/'controls'/(control_id+'.json'),value)
            state.setdefault('controls',{})[control_id]=value
            self._event(state,'control_applicability_recorded',control=control_id,applicability=value['applicability'],applied=value['control_applied'])
            return value

    def freeze(self,names):
        with self._transaction() as (spec,state):
            from .postselection import plans_for, validate_plans
            analysis_plans=plans_for(spec,state)
            validate_plans({**spec,'analyses':analysis_plans})
            if not names or len(set(names))!=len(names) or len(names)>spec['budget']['confirmation']:
                raise ValueError('Finalists exceed the declared confirmation allocation')
            if any(n['status'] in {'selected','repair_needed'} for n in state['nodes'].values()):raise ValueError('Handle active work before closing search')
            exhausted=state.get('proposal_exhaustion') and not any(n['status']=='candidate_queued' and n['phase']=='optimization' for n in state['nodes'].values())
            if self._coverage_handled(state)<spec['budget']['coverage'] or (state['budget_used']['optimization']<spec['budget']['optimization'] and not exhausted):
                raise ValueError('Registered allocations remain; do not call one handled node a finished run')
            if any(self._resolved(state['nodes'],name) is None for name in spec['benchmarks']):raise ValueError('Required comparison baselines remain incomplete')
            if set(spec.get('required_controls',[]))-set(state.get('controls',{})):
                raise ValueError('Record the registered applicable/N/A development controls before confirmation')
            selected={}
            identities=set()
            for name in names:
                n=self._resolved(state['nodes'],name)
                if n is None:raise ValueError('Only actually trained finalists may enter confirmation')
                if n['measurement_id'] in identities:raise ValueError('Choose unique measured finalists, not aliases of the same result')
                identities.add(n['measurement_id'])
                self._check_checkpoints(n['receipt']['checkpoint_files']);self._verify_implementation(n)
                selected[name]={'measurement_id':n['measurement_id'],'checkpoint_files':n['receipt']['checkpoint_files']}
            lock={'schema_version':'research_v2','metric_id':MetricSpec.from_dict(spec['metric']).identity,
                'selected':selected,'further_search_allowed':False,'prior_test_exposure':spec['prior_test_exposure']}
            lock['analysis_plan_sha256']=digest(analysis_plans)
            freeze_record(self.run/'confirmation_lock_v2.json',lock)
            state['selection_closed']=True
            self._event(state,'selection_frozen',nodes=names)
        return lock

    def confirm(self,name):
        with self._transaction(search=False) as (spec,state):
            if not state['selection_closed']:raise ValueError('Freeze selection before opening heldout data')
            lock=json.loads((self.run/'confirmation_lock_v2.json').read_text())
            if name not in lock['selected']:raise ValueError('Candidate was not selected before confirmation')
            n=self._resolved(state['nodes'],name)
            self._check_checkpoints(lock['selected'][name]['checkpoint_files'])
            self._verify_implementation(n)
            path=self.run/'confirmation'/name/'metrics.json'
            if path.is_file():
                if state.get('confirmation_reports',{}).get(name)!=file_digest(path):raise ValueError('Committed confirmation output changed')
                cached=json.loads(path.read_text())
                pred=cached['prediction_receipt']
                if file_digest(Path(pred['path']))!=pred['sha256']:raise ValueError('Frozen confirmation predictions changed')
                return cached
            contract_info=spec.get('confirmation_contract')
            if not contract_info or file_digest(Path(contract_info['path']))!=contract_info['sha256']:
                raise ValueError('Source-backed confirmation adapter contract is missing or changed')
            contract=json.loads(Path(contract_info['path']).read_text())
            if set(contract['groups'])&set(json.loads(Path(spec['development_contract']).read_text())['groups']):
                raise ValueError('Confirmation and development groups overlap')
            module=self._provider(n)
            request={'phase':'confirmation_predict_only','node_id':name,'metric':spec['metric'],
                'metric_id':lock['metric_id'],'checkpoint_files':lock['selected'][name]['checkpoint_files'],
                'confirmation_contract':contract,'output_dir':str(path.parent),'recipe':n['sealed_recipe'],
                'execution':n['execution'],'task_id':spec['task_id']}
            result=module.predict_confirmation(request)
            if result.get('model_refits')!=0 or result.get('calibration_refits')!=0:
                raise ValueError('Confirmation may only load previously fitted artifacts')
            table=result['prediction_table']
            if table.get('evidence_phase')!='confirmation' or table.get('metric_id')!=lock['metric_id']:
                raise ValueError('Wrong confirmation metric/phase')
            for key in ('row_ids','groups','targets','seeds'):
                if table[key]!=contract[key]:raise ValueError('Confirmation data contract differs')
            self._check_checkpoints(lock['selected'][name]['checkpoint_files'])
            report={'score':MetricSpec.from_dict(spec['metric']).score(table),'metric_id':lock['metric_id'],
                'evidence_phase':'confirmation','model_refits':0,'calibration_refits':0,
                'prior_test_exposure':spec['prior_test_exposure']}
            prediction_path=self.run/'nodes'/n['id']/'confirmation_predictions.json'
            freeze_record(prediction_path,table)
            report['prediction_receipt']={'path':str(prediction_path),'sha256':file_digest(prediction_path)}
            freeze_record(path,report);state['budget_used']['confirmation']+=1
            state.setdefault('confirmation_reports',{})[name]=file_digest(path)
            self._event(state,'confirmation_reported_no_feedback',node=name)
            return report

    def analyze(self, name, analysis_id):
        from .postselection import run
        return run(self, name, analysis_id)

    def verdict(self):
        spec,state=self._load();nodes=state['nodes']
        trained=[n for n in nodes.values() if n['status']=='trained']
        evidence=[n for n in trained if n.get('paired_evidence',{}).get('promotion_supported')]
        ref=self._resolved(nodes,spec['reference_benchmark'])
        exhausted=bool(state.get('proposal_exhaustion')) and not any(n['status']=='candidate_queued' and n['phase']=='optimization' for n in nodes.values())
        complete=all(self._resolved(nodes,name) is not None for name in spec['benchmarks']) and self._coverage_handled(state)>=spec['budget']['coverage'] and (state['budget_used']['optimization']>=spec['budget']['optimization'] or exhausted)
        complete=complete and not any(n['status'] in {'selected','repair_needed'} for n in nodes.values())
        reports=state.get('analysis_reports',{})
        lock_path=self.run/'confirmation_lock_v2.json'
        finalists=list(json.loads(lock_path.read_text())['selected']) if lock_path.is_file() else []
        from .postselection import plans_for
        plans=plans_for(spec,state)
        analysis_complete=all((all(aid+'::'+name in reports for name in finalists) if plan['target_policy']=='each_finalist'
            else any(k.startswith(aid+'::') for k in reports)) for aid,plan in plans.items())
        if plans and not finalists:analysis_complete=False
        return {'execution_complete':complete,'proposal_exhaustion':state.get('proposal_exhaustion'),
            'protocol_version':'research_v2','declared_compositions_exercised':sorted({n['hypothesis']['composition'] for n in trained}),
            'combination_fits_with_validated_inner_group_audits':sum(bool(n['receipt'].get('inner_group_audit_validated')) for n in trained),
            'capability_claim_basis':'validated interface/OOF receipts and trusted-provider declarations, not architecture-equivalence certification',
            'trained_measurements':len(trained),'unique_semantic_candidates':len({n['semantic_id'] for n in trained}),
            'unexercised_compositions':sorted(COMPOSITIONS-{n['hypothesis']['composition'] for n in trained}),
            'coverage':state['budget_used']['coverage'],'optimization':state['budget_used']['optimization'],
            'coverage_inventory_handled':self._coverage_handled(state),
            'coverage_gaps':[n['id'] for n in nodes.values() if n['phase']=='coverage' and n['status'] in {'skipped','failed'}],
            'development_promotion_supported':[n['id'] for n in evidence],
            'reference_benchmark':spec['reference_benchmark'],
            'retained_baseline':spec['reference_benchmark'] if ref else None,
            'default_decision':'retain the reference unless a separately justified confirmatory decision supports replacement',
            'scientific_superiority':'not established by execution completion or adaptive development evidence',
            'artifact_attribution':'requires applicable matched controls; availability/use is not benefit',
            'control_results':state.get('controls',{}),
            'postselection_analysis_scope_complete':analysis_complete,
            'postselection_analysis_completed':sorted(reports),
            'postselection_analysis_attempts':len(state.get('analysis_attempts',[])),
            'missing_registered_controls':sorted(set(spec.get('required_controls',[]))-set(state.get('controls',{}))),
            'transfer_verdict':'not established; requires unseen tasks and equal-resource policy comparisons',
            'candidate_status_counts':{s:sum(n['status']==s for n in nodes.values()) for s in {n['status'] for n in nodes.values()}},
            'selection_closed':state['selection_closed']}
