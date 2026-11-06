"""Real regression and temporal models; no pretrained-model stand-ins."""
from __future__ import annotations

import random
import warnings

import numpy as np
import torch
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.preprocessing import StandardScaler
from torch import nn
from xgboost import XGBRegressor


class View:
    def __init__(self, config):
        self.config = config

    def fit(self, bundle, idx):
        c = self.config
        expression = bundle["expression"][idx]
        if c.get("baseline_only", False):
            expression = expression[:, :1]
        # Only early observations from training clones determine the gene list.
        variance = expression.reshape(-1, expression.shape[-1]).var(axis=0)
        self.genes = np.argsort(variance)[-c.get("genes", 128):]
        self.scaler = StandardScaler().fit(expression[:, :, self.genes].reshape(-1, len(self.genes)))
        path_fit = bundle["pathway"][idx]
        if c.get("baseline_only", False):
            path_fit = path_fit[:, :1]
        self.path_scaler = StandardScaler().fit(path_fit.reshape(-1, path_fit.shape[-1]))
        self.aux_scaler = StandardScaler().fit(bundle["aux"][idx])
        if c["representation"] == "pca":
            raw = self.scaler.transform(expression[:, :, self.genes].reshape(-1, len(self.genes)))
            self.pca = PCA(n_components=min(8, len(idx)-1), random_state=0).fit(raw)
        return self

    def transform(self, bundle, idx):
        expr = bundle["expression"][idx][:, :, self.genes]
        expr = self.scaler.transform(expr.reshape(-1, len(self.genes))).reshape(len(idx), 3, -1)
        path = bundle["pathway"][idx]
        path = self.path_scaler.transform(path.reshape(-1, path.shape[-1])).reshape(len(idx), 3, -1)
        representation = self.config["representation"]
        if representation == "pathway":
            sequence = path
        elif representation == "both":
            sequence = np.concatenate([expr, path], axis=-1)
        elif representation == "pca":
            sequence = self.pca.transform(expr.reshape(-1, expr.shape[-1])).reshape(len(idx), 3, -1)
        else:
            sequence = expr
        if self.config.get("baseline_only", False):
            sequence = np.repeat(sequence[:, :1], 3, axis=1)
        aux = self.aux_scaler.transform(bundle["aux"][idx])
        if self.config.get("baseline_only", False):
            aux = aux.copy()
            aux[:, 1:3] = 0
            aux[:, 4:6] = 0
        if self.config.get("no_treatment", False):
            aux[:, -3:] = 0
        if self.config.get("no_clone_abundance", False):
            aux[:, :6] = 0
        return sequence.astype(np.float32), aux.astype(np.float32)


class TemporalRegressor(nn.Module):
    def __init__(self, width, aux_dim, family, hidden, dropout):
        super().__init__()
        self.family = family
        self.input = nn.Linear(width, hidden)
        self.position = nn.Parameter(torch.zeros(1, 3, hidden))
        if family == "gru":
            self.sequence = nn.GRU(hidden, hidden, batch_first=True)
        elif family == "transformer":
            layer = nn.TransformerEncoderLayer(hidden, 4, hidden * 2, dropout, batch_first=True, norm_first=True)
            self.sequence = nn.TransformerEncoder(layer, 2, enable_nested_tensor=False)
        else:
            self.sequence = nn.Sequential(nn.Linear(hidden * 3, hidden), nn.GELU(), nn.Dropout(dropout))
        self.head = nn.Sequential(nn.Linear(hidden + aux_dim, hidden), nn.GELU(), nn.Linear(hidden, 1))
        self.gate = nn.Parameter(torch.tensor(-2.0))

    def forward(self, sequence, aux):
        z = self.input(sequence) + self.position
        if self.family == "gru":
            z = self.sequence(z)[0][:, -1]
        elif self.family == "transformer":
            z = self.sequence(z).mean(dim=1)
        else:
            z = self.sequence(z.flatten(1))
        return torch.sigmoid(self.gate) * self.head(torch.cat([z, aux], dim=1)).squeeze(-1)


class Candidate:
    def __init__(self, config):
        self.config = config
        self.view = View(config)

    def fit(self, bundle, idx, seed=3):
        c = self.config
        self.view.fit(bundle, idx)
        sequence, aux = self.view.transform(bundle, idx)
        x = np.concatenate([sequence.reshape(len(idx), -1), aux], axis=1)
        y = bundle["meta"].iloc[idx].label.to_numpy(dtype=np.float64)
        self.y_mean, self.y_std = float(y.mean()), max(float(y.std()), .1)
        target = (y - self.y_mean) / self.y_std
        family, alpha = c["model"], c.get("alpha", 10.)
        if family == "frequency":
            x = np.concatenate([aux[:, :1], aux[:, -3:]], axis=1)
            self.estimator = Ridge(alpha=alpha).fit(x, target)
        elif family == "ridge":
            self.estimator = Ridge(alpha=alpha).fit(x, target)
        elif family == "elastic":
            self.estimator = ElasticNet(alpha=max(alpha * .001, .001), l1_ratio=.5, max_iter=10000).fit(x, target)
        elif family == "pls":
            self.estimator = PLSRegression(n_components=min(c.get("components", 3), len(idx)-2, x.shape[1]), scale=False).fit(x, target)
        elif family == "xgboost":
            self.estimator = XGBRegressor(n_estimators=160, max_depth=c.get("depth", 2), learning_rate=.035,
                                         reg_lambda=alpha, subsample=.9, colsample_bytree=.8,
                                         objective="reg:squarederror", random_state=seed, n_jobs=2).fit(x, target)
        elif family in {"gru", "transformer", "gated_residual"}:
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            torch.set_num_threads(2)
            self.estimator = Ridge(alpha=alpha).fit(x, target)
            residual = target - self.estimator.predict(x)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.network = TemporalRegressor(sequence.shape[-1], aux.shape[-1], family,
                                            c.get("hidden", 32), c.get("dropout", .15)).to(self.device)
            sx, ax = torch.tensor(sequence, device=self.device), torch.tensor(aux, device=self.device)
            ty = torch.tensor(residual, dtype=torch.float32, device=self.device)
            optimizer = torch.optim.AdamW(self.network.parameters(), lr=.001, weight_decay=.02)
            loss_fn = nn.HuberLoss() if c.get("loss", "huber") == "huber" else nn.MSELoss()
            self.network.train()
            self.losses = []
            for _ in range(c.get("epochs", 80)):
                optimizer.zero_grad()
                pred = self.network(sx, ax)
                loss = loss_fn(pred, ty)
                if not torch.isfinite(loss):
                    raise ValueError("Non-finite model training loss")
                loss.backward()
                nn.utils.clip_grad_norm_(self.network.parameters(), 1.)
                optimizer.step()
                self.losses.append(float(loss.detach().cpu()))
            self.network.eval()
        else:
            raise ValueError(f"No faithful implementation for {family}")
        return self

    def predict(self, bundle, idx):
        sequence, aux = self.view.transform(bundle, idx)
        x = np.concatenate([sequence.reshape(len(idx), -1), aux], axis=1)
        if self.config["model"] == "frequency":
            x = np.concatenate([aux[:, :1], aux[:, -3:]], axis=1)
        pred = np.asarray(self.estimator.predict(x)).reshape(-1)
        if hasattr(self, "network"):
            with torch.no_grad():
                pred = pred + self.network(torch.tensor(sequence, device=self.device),
                                           torch.tensor(aux, device=self.device)).cpu().numpy()
        return pred * self.y_std + self.y_mean
