"""Isolated source-extracted TraCSED runtime; never imported into the metric process."""
import argparse
import ast
import hashlib
import importlib.metadata
import json
import joblib
import os
from pathlib import Path

os.environ.setdefault('TF_NUM_INTRAOP_THREADS', '2')
os.environ.setdefault('TF_NUM_INTEROP_THREADS', '2')
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import MinMaxScaler
from sklearn import linear_model


def namespace(source):
    ns = dict(np=np, pd=pd, tf=tf, keras=keras, layers=layers, MinMaxScaler=MinMaxScaler, seq_len=8)
    hashes = {}
    names = {'build_model', 'transformer_encoder', 'lr_scheduler',
             'transformer_train_test_split_dayiter', 'regr_train_test_split_dayiter'}
    for cell in json.loads(Path(source).read_text())['cells']:
        text = ''.join(cell.get('source', []))
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in names:
                code = ast.get_source_segment(text, node)
                exec(compile(code, str(source), 'exec'), ns)
                hashes[node.name] = hashlib.sha256(code.encode()).hexdigest()
    if set(hashes) != names:
        raise ValueError('Pinned author notebook functions are incomplete')
    return ns, hashes


def build(ns, shape, config):
    net = ns['build_model'](input_shape=shape, head_size=config.get('head_size', 5), num_heads=config.get('num_heads', 40),
        ff_dim=config.get('ff_dim', 5), num_attention_blocks=config.get('attention_blocks', 10),
        num_transformer_blocks=config.get('transformer_blocks', 10), mlp_units=config.get('mlp_units', [256]),
        dropout=config.get('dropout', .14), mlp_dropout=config.get('mlp_dropout', .4))
    optimizer = {'adam': keras.optimizers.Adam, 'adamw': keras.optimizers.AdamW, 'sgd': keras.optimizers.SGD}.get(config.get('optimizer', 'adam'))
    if optimizer is None:
        raise ValueError('Implement the declared optimizer; no hidden optimizer substitution')
    kwargs = {'learning_rate': config.get('learning_rate', .001)}
    if config.get('optimizer') == 'adamw':
        kwargs['weight_decay'] = config.get('weight_decay', .02)
    losses = {'mean_squared_error': 'mean_squared_error', 'mse': 'mean_squared_error',
              'mean_absolute_error': 'mean_absolute_error', 'huber': keras.losses.Huber(delta=config.get('huber_delta', 1.))}
    if config.get('loss', 'mean_squared_error') not in losses:
        raise ValueError('Implement the declared loss without changing the task labels')
    net.compile(optimizer=optimizer(**kwargs), loss=losses[config.get('loss', 'mean_squared_error')],
                jit_compile=config.get('jit_compile', False))
    return net


def fit(net, x, y, config, ns):
    rng = np.random.default_rng(config.get('author_seed', 42))
    losses, rates = [], []
    for epoch in range(config.get('epochs', 20)):
        if config.get('lr_schedule') == 'author_warmup_decay':
            rate = ns['lr_scheduler'](epoch, float(net.optimizer.learning_rate.numpy()), **config.get('schedule_parameters', {}))
            net.optimizer.learning_rate.assign(rate)
        elif config.get('lr_schedule', 'none') != 'none':
            raise ValueError('Unknown declared author LR schedule')
        rates.append(float(net.optimizer.learning_rate.numpy()))
        values = []
        order = rng.permutation(len(x))
        for start in range(0, len(x), config.get('batch_size', 32)):
            ids = order[start:start + config.get('batch_size', 32)]
            loss = float(net.train_on_batch(x[ids], y[ids]))
            if not np.isfinite(loss):
                raise ValueError('Actual source model has nonfinite training loss')
            values.append(loss)
        losses.append(float(np.mean(values)))
    return losses, rates


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--action', choices=['fit', 'predict', 'reference'], required=True)
    p.add_argument('--request', type=Path, required=True)
    a = p.parse_args()
    request = json.loads(a.request.read_text())
    for package, version in request['runtime_identity']['packages'].items():
        if importlib.metadata.version(package) != version:
            raise ValueError('Isolated TensorFlow runtime changed: ' + package)
    source = Path(request['notebook'])
    if hashlib.sha256(source.read_bytes()).hexdigest() != request['notebook_sha256']:
        raise ValueError('Author source content changed')
    ns, hashes = namespace(source)
    config = {'head_size': 5, 'num_heads': 40, 'ff_dim': 5, 'attention_blocks': 10, 'transformer_blocks': 10,
        'mlp_units': [256], 'dropout': .14, 'mlp_dropout': .4, 'optimizer': 'adam',
        'learning_rate': .001, 'loss': 'mean_squared_error', 'epochs': 20, 'batch_size': 32,
        'author_seed': 42, 'lr_schedule': 'none', **request['config']}
    keras.utils.set_random_seed(config.get('author_seed', 42))
    directory = Path(request['directory'])
    if a.action == 'predict':
        def forbidden(*args, **kwargs):
            raise RuntimeError('Frozen source-model inference forbids fitting')
        keras.Model.fit = forbidden
        keras.Model.train_on_batch = forbidden
        net = keras.models.load_model(directory / 'model.keras', compile=False)
        x = np.load(request['query'])['s']
        prediction = net(x, training=False).numpy().ravel()
        if not np.isfinite(prediction).all():
            raise ValueError('Nonfinite frozen source-model prediction')
        np.save(request['prediction'], prediction)
        Path(request['prediction_metadata']).write_text(json.dumps({'model_refits': 0, 'calibration_refits': 0}))
        return
    if a.action == 'fit':
        arrays = np.load(request['training'])
        x, y = arrays['s'], arrays['y']
        net = build(ns, x.shape[1:], config)
        losses, rates = fit(net, x, y, config, ns)
        net.save(directory / 'model.keras')
        provenance = {'author_notebook_sha256': request['notebook_sha256'], 'functions': hashes,
            'effective_config': config, 'actual_parameters': net.count_params(), 'losses': losses, 'learning_rates': rates,
            'source_quirks_retained': ['source loops reuse original inputs; declared blocks are not an assertion of sequential effective depth',
                'GlobalAveragePooling1D channels_first retained'],
            'mode': 'author architecture early-forecast adapter, not original seq8 retrospective task'}
        (directory / 'fit_provenance.json').write_text(json.dumps(provenance, indent=2))
        return
    # Source splitter and scaler semantics remain retrospective and report-only.
    ns['data'] = json.loads(Path(request['reference_data']).read_text())
    ns['bar_dict'] = {key: i for i, key in enumerate(ns['data'])}
    results = []
    fits = 0
    for barcode in ns['data']:
        for interval in request['intervals']:
            x, y, q, truth, columns = ns['transformer_train_test_split_dayiter'](barcode, .05, [False] * 3, interval)
            if not len(x) or not len(q):
                results.append({'status': 'insufficient_source_windows', 'barcode': barcode, 'interval': interval})
                continue
            for variant, blocks in {'full': (10, 10), 'no_attention': (0, 10), 'no_feedforward': (10, 0)}.items():
                if fits >= request['model_fit_budget']:
                    raise ValueError('Registered retrospective-reference fitting allocation exhausted')
                fits += 1
                keras.backend.clear_session()
                keras.utils.set_random_seed(config.get('author_seed', 42))
                actual = dict(config, attention_blocks=blocks[0], transformer_blocks=blocks[1])
                net = build(ns, x.shape[1:], actual)
                losses, rates = fit(net, x.astype('float32'), y.astype('float32'), actual, ns)
                prediction = net(q.astype('float32'), training=False).numpy().ravel()
                path = directory / (hashlib.sha256((barcode + str(interval) + variant).encode()).hexdigest()[:16] + '.keras')
                net.save(path)
                np.savez_compressed(path.with_suffix('.npz'), prediction=prediction, truth=truth)
                results.append({'variant': variant, 'barcode': barcode, 'interval': interval,
                    'train_windows': len(x), 'validation_windows': len(q), 'parameters': net.count_params(),
                    'mse': float(np.mean((prediction - truth) ** 2)), 'mae': float(np.mean(np.abs(prediction - truth))),
                    'last_train_loss': losses[-1], 'checkpoint': str(path), 'features': columns})
            rx, ry, qx, qy = ns['regr_train_test_split_dayiter'](barcode, .05, [False] * 3, interval)
            if fits >= request['model_fit_budget']:
                raise ValueError('Registered reference linear-fit allocation exhausted')
            fits += 1
            reg = linear_model.LinearRegression().fit(rx, ry)
            pred = reg.predict(qx)
            path = directory / (hashlib.sha256((barcode + str(interval) + 'linear').encode()).hexdigest()[:16] + '.joblib')
            joblib.dump(reg, path)
            np.savez_compressed(path.with_suffix('.npz'), prediction=pred, truth=qy)
            results.append({'variant': 'linear_reference', 'barcode': barcode, 'interval': interval,
                            'mse': float(np.mean((pred - qy) ** 2)), 'mae': float(np.mean(np.abs(pred - qy)))})
    Path(request['result']).write_text(json.dumps({'results': results, 'source_function_sha256': hashes,
        'protocol': 'author prefix/time-window retrospective interpolation, not unseen-clone forecasting'}))


if __name__ == '__main__':
    main()
