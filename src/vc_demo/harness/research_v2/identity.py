"""Separate scientific identity from execution locations and deliberate replicates."""
from pathlib import Path
from vc_demo.harness.research_contract import digest, file_digest


COMPOSITIONS = {'replace','feature_fusion','joint','crossfit_residual','crossfit_stack','ablation'}


def artifact_identity(path):
    p=Path(path)
    if p.is_file():
        if p.stat().st_size==0:raise ValueError('Empty artifact file')
        return file_digest(p)
    if not p.is_dir():raise ValueError('Missing artifact: acquire the real resource before training')
    files=[f for f in p.rglob('*') if f.is_file() and f.stat().st_size>0
        and not any(part in {'.git','.cache','__pycache__'} for part in f.relative_to(p).parts)]
    useful=[f for f in files if f.name not in {'.gitattributes','README.md','LICENSE','.DS_Store'}]
    if not useful:raise ValueError('Empty/model-card-only directories are not usable artifacts')
    return digest({str(f.relative_to(p)):file_digest(f) for f in sorted(files)})


def semantic_identity(recipe, metric_id):
    required = {'parameters','training','code_sha256','input_sha256','artifact_sha256','environment'}
    if set(recipe)!=required or not recipe['code_sha256']:
        raise ValueError('A sealed scientific recipe requires explicit content-addressed components')
    def check(value):
        if isinstance(value,dict):
            for key,item in value.items():
                if key in {'node_name','node_id','run_dir','output_dir','provider_path','custom_model_path',
                           'checkpoint_path','artifact_path','data_path','model_dir','artifact_dir','data_dir'}:
                    raise ValueError('Execution locations do not belong in scientific parameters: '+key)
                check(item)
        elif isinstance(value,list):
            for item in value:check(item)
    check(recipe['parameters']);check(recipe['training'])
    return digest({'format':'research_semantics.v2','metric_id':metric_id,'recipe':recipe})


def measurement_identity(semantic_id, replicate=None):
    if replicate is not None:
        if set(replicate)!={'id','purpose','training_seed'} or not str(replicate['id']).strip() or not str(replicate['purpose']).strip():
            raise ValueError('Replicates require an explicit ID, purpose and training seed')
        if type(replicate['training_seed'])!=int or replicate['training_seed']<0:
            raise ValueError('A registered training seed must be a nonnegative integer')
    return digest({'semantic_id':semantic_id,'registered_replicate':replicate})
