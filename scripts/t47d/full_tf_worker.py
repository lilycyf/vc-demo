"""Isolated TensorFlow runner for source-extracted TraCSED architecture."""
import ast
import hashlib
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('TF_NUM_INTRAOP_THREADS','4')
os.environ.setdefault('TF_NUM_INTEROP_THREADS','2')

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model

SOURCE=Path('/workspace/_external/TraCSED/model_scripts/TraCSED_final_model.ipynb')


def author_namespace():
    ns=dict(np=np,pd=pd,tf=tf,keras=keras,layers=layers,MinMaxScaler=MinMaxScaler,seq_len=8)
    extracted={}
    for cell in json.loads(SOURCE.read_text())["cells"]:
        s=''.join(cell.get('source',[]))
        try: tree=ast.parse(s)
        except SyntaxError: continue
        for item in tree.body:
            if isinstance(item,ast.FunctionDef) and item.name in {
                'transformer_encoder','build_model','lr_scheduler','transformer_train_test_split_dayiter','regr_train_test_split_dayiter'}:
                definition=ast.get_source_segment(s,item)
                exec(compile(definition,str(SOURCE),"exec"),ns)
                extracted[item.name]=hashlib.sha256(definition.encode()).hexdigest()
    if set(extracted)!={'transformer_encoder','build_model','lr_scheduler','transformer_train_test_split_dayiter','regr_train_test_split_dayiter'}:
        raise RuntimeError('Author function extraction incomplete')
    return ns,extracted


def model(ns,shape,attention=10,feedforward=10,jit_compile=False):
    result=ns['build_model'](input_shape=shape,head_size=5,num_heads=40,ff_dim=5,
        num_attention_blocks=attention,num_transformer_blocks=feedforward,
        mlp_units=[256],dropout=.14,mlp_dropout=.4)
    result.compile(optimizer=keras.optimizers.Adam(learning_rate=.001),loss='mean_squared_error',jit_compile=jit_compile)
    return result


def fit_batches(model,x,y,epochs=20):
    rng=np.random.default_rng(42)
    losses=[]
    for epoch in range(epochs):
        order=rng.permutation(len(x));values=[]
        for start in range(0,len(x),32):
            ids=order[start:start+32]
            value=float(model.train_on_batch(x[ids],y[ids]))
            if not np.isfinite(value):raise ValueError('Nonfinite genuine author model training loss')
            values.append(value)
        losses.append(float(np.mean(values)))
    return losses


def forecast(action,dest):
    ns,hashes=author_namespace()
    keras.utils.set_random_seed(42)
    if action=='fit':
        a=np.load(dest/'train.npz');net=model(ns,a['s'].shape[1:],jit_compile=True);losses=fit_batches(net,a['s'],a['y'])
        net.save(dest/'model.keras')
        (dest/'provenance.json').write_text(json.dumps({'author_notebook_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'extracted_function_sha256':hashes,'mode':'author architecture early-forecast adapter, not retrospective reference',
            'actual_parameters':net.count_params(),'epochs':20,'losses':losses,'physical_gpus':[str(x) for x in tf.config.list_physical_devices('GPU')]},indent=2))
    else:
        net=keras.models.load_model(dest/'model.keras')
        a=np.load(dest/'query.npz');np.save(dest/'pred.npy',net(a['s'],training=False).numpy().ravel())


def retrospective(dest):
    ns,hashes=author_namespace()
    ns['data']=json.loads((dest/'reference_data.json').read_text())
    ns['bar_dict']={key:i for i,key in enumerate(ns['data'])}
    output=dest/'tf_reference_results.jsonl'
    completed={}
    if output.exists():
        for line in output.read_text().splitlines():
            r=json.loads(line);completed[(r['barcode'],r['interval'],r['variant'])]=r
    variants={'full':(10,10),'no_attention':(0,10),'no_feedforward':(10,0)}
    for barcode in ns['data']:
        for interval in (.25,.5,.75,1.):
            key=(barcode,interval)
            x,y,vx,vy,cols=ns['transformer_train_test_split_dayiter'](barcode,.05,[False,False,False],interval)
            if len(x)==0 or len(vx)==0:
                r={'barcode':barcode,'interval':interval,'status':'insufficient author seq8 train/validation windows'}
                with (dest/'excluded_reference_windows.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
                continue
            for variant,(att,ff) in variants.items():
                if (barcode,interval,variant) in completed:continue
                keras.backend.clear_session();keras.utils.set_random_seed(42)
                net=model(ns,x.shape[1:],att,ff);losses=fit_batches(net,x.astype('float32'),y.astype('float32'))
                pred=net(vx.astype('float32'),training=False).numpy().ravel()
                if not np.isfinite(pred).all():raise ValueError('Nonfinite author reference prediction')
                checkpoint_dir=dest/'weights'/barcode.replace('::','__')
                checkpoint_dir.mkdir(parents=True,exist_ok=True)
                net.save(checkpoint_dir/(str(interval)+'_'+variant+'.keras'))
                r={'barcode':barcode,'interval':interval,'variant':variant,'mse':float(np.mean((pred-vy)**2)),
                   'mae':float(np.mean(np.abs(pred-vy))),'train_windows':len(x),'validation_windows':len(vx),
                   'actual_parameters':net.count_params(),'epochs':20,'final_training_loss':losses[-1],
                   'features':cols,'protocol':'author pseudotime prefix interpolation; not unseen-clone prospective performance'}
                np.savez_compressed(dest/(barcode+'_'+str(interval)+'_'+variant+'_pred.npz'),y=vy,pred=pred)
                if variant=='full' and interval==1.:
                    full_x,full_y,full_cols=ns['transformer_train_test_split_dayiter'](barcode,0,[False,False,False],1.)
                    base=float(np.abs(net(full_x.astype('float32'),training=False).numpy().ravel()-full_y).mean())
                    importance={};rng=np.random.default_rng(42)
                    for j,name in enumerate(cols):
                        scores=[]
                        for _ in range(30):
                            shuffled=full_x.copy();shuffled[:,:,j]=shuffled[rng.permutation(len(shuffled)),:,j]
                            p=net(shuffled.astype('float32'),training=False).numpy().ravel()
                            scores.append(float(np.mean(np.abs(p-full_y))))
                        importance[name]={'shuffled_mae_mean':float(np.mean(scores)),'mean_mae_increase':float(np.mean(scores))-base,
                            'std':float(np.std(scores)),'permutations':30,'baseline_mae':base,'source_protocol':'full prefix windows, feature-vector permutation'}
                    r['permutation_feature_importance']=importance
                with output.open('a') as f:f.write(json.dumps(r)+'\n')
                print(json.dumps({k:r[k] for k in ('barcode','interval','variant','mse')}),flush=True)
            if (barcode,interval,'linear_reference') not in completed:
                rx,ry,rvx,rvy=ns['regr_train_test_split_dayiter'](barcode,.05,[False,False,False],interval)
                reg=linear_model.LinearRegression().fit(rx,ry);rp=reg.predict(rvx)
                r={'barcode':barcode,'interval':interval,'variant':'linear_reference',
                   'mse':float(np.mean((rp-rvy)**2)),'mae':float(np.abs(rp-rvy).mean()),'train_windows':len(rx),'validation_windows':len(rvx)}
                with output.open('a') as f:f.write(json.dumps(r)+'\n')
    (dest/'tf_reference_provenance.json').write_text(json.dumps({'author_notebook_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'functions':hashes,'seed':42,'sequence_length':8,'epochs':20,'batch_size':32,
        'known_source_quirks':['Repeated blocks use original input; retained unchanged','Last dataframe column discarded by author splitter; retained unchanged',
        'MinMaxScaler fitted on full interval prefix before last5% split; retrospective only'],
        'keras_execution':'jit_compile=False restores author pre-Keras3 default; unchanged architecture/Adam/MSE/20epochs/batch32',
        'gpus':[str(x) for x in tf.config.list_physical_devices('GPU')]},indent=2))


if __name__=='__main__':
    action=sys.argv[1];dest=Path(sys.argv[2]);dest.mkdir(parents=True,exist_ok=True)
    if action=='reference':retrospective(dest)
    else:forecast(action,dest)
