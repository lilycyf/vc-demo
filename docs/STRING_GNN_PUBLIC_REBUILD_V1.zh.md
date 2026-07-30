# STRING_GNN Public Rebuild v1 中文说明

## 结论

`STRING_GNN_PublicRebuild_v1` 是一个用公开数据重建的 STRING_GNN 风格图表征 artifact。它已经完成训练、导出和加载验证，可以作为 VCHarness-style harness 中的可审计替代图基础模块使用。

它不是 GenBio/VCHarness 原文未公开的 `/home/Models/STRING_GNN` 原始 checkpoint，也不声称与原始模型数值等价。它的定位是：在原始 checkpoint 不可公开验证时，用公开 STRING 图和公开/已获得的 GNN Simple D256 teacher embedding 训练出一个可复用、可追溯、可重新生成的替代 artifact。

## 产物位置

大文件保存在 RunPod network volume，不进入 GitHub：

- 训练中间产物：`/workspace/artifacts/string_gnn_rebuild_v1_multiseed`
- 导出的模型目录：`/workspace/models/STRING_GNN_PublicRebuild_v1`
- 便捷 symlink：`/home/Models/STRING_GNN_PUBLIC_REBUILD`

导出的模型目录包含：

- `config.json`
- `configuration_string_gnn_rebuild.py`
- `modeling_string_gnn_rebuild.py`
- `graph_data.pt`
- `node_names.json`
- `model.safetensors`
- `README.md`

GitHub 只记录脚本、manifest 和报告，不提交 `.pt`、`.safetensors`、`.h5ad`、`.npz`、checkpoint 或权重文件。

## 数据来源与可审计信息

输入数据：

- Teacher embedding：`data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad`
- STRING graph：`data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt`

关键 provenance：

- node count：`18866`
- teacher shape：`[18866, 256]`
- graph raw edges：`393006`
- kept undirected pairs：`392832`
- directed edges：`785664`
- node coverage：`1.0`
- teacher sha256：`58dee3dddb3332dbff43f21225460d20fc3c75f933a4d62c71bbca4699619e25`
- graph sha256：`126b4a202837298c8b5cfd07a3dbe40baeaac84290471da78cedfefa37621d98`
- node order sha256：`42fffd3aa77b58ba08567ff58e7f2cd983396050b2b60a291c01719a162bd638`

## 训练配置

正式 v1 训练配置：

- GPU：NVIDIA L40
- PyTorch：`2.4.1+cu124`
- hidden dim：`512`
- output dim：`256`
- layers：`3`
- dropout：`0.1`
- optimizer：AdamW
- learning rate：`0.002`
- weight decay：`0.0001`
- loss：MSE + cosine loss + graph smoothness regularization
- smooth edges：`100000`
- epochs：`100`
- patience：`20`
- seeds：`3, 7, 11`
- train/val/test node split：`80% / 10% / 10%`

## 多 seed 结果

| seed | best epoch | val cosine | val MSE | test cosine | top10 neighbor overlap |
|---:|---:|---:|---:|---:|---:|
| 3 | 99 | 0.529594 | 0.024509 | 0.533334 | 0.4250 |
| 7 | 98 | 0.533744 | 0.024540 | 0.538918 | 0.4371 |
| 11 | 100 | 0.528345 | 0.023506 | 0.535617 | 0.4267 |

最佳 seed 是 `7`，已导出为 `/workspace/models/STRING_GNN_PublicRebuild_v1`。

## 加载方式

```python
from transformers import AutoModel

model = AutoModel.from_pretrained(
    "/workspace/models/STRING_GNN_PublicRebuild_v1",
    trust_remote_code=True,
)
out = model()
print(out.last_hidden_state.shape)  # torch.Size([18866, 256])
```

如果只需要特定 node 的 embedding：

```python
import torch

node_indices = torch.tensor([0, 1, 2])
out = model(node_indices=node_indices)
print(out.last_hidden_state.shape)  # torch.Size([3, 256])
```

## 如何重新生成

在 RunPod `/workspace/vc-demo` 中运行：

```bash
python scripts/string_gnn_rebuild/train_public_string_gnn.py \
  --output-dir /workspace/artifacts/string_gnn_rebuild_v1_multiseed \
  --export-dir /workspace/models/STRING_GNN_PublicRebuild_v1 \
  --epochs 100 \
  --patience 20 \
  --seeds 3 7 11 \
  --hidden-dim 512 \
  --layers 3 \
  --smooth-edges 100000 \
  --symlink /home/Models/STRING_GNN_PUBLIC_REBUILD
```

快速 smoke：

```bash
python scripts/string_gnn_rebuild/train_public_string_gnn.py \
  --output-dir /workspace/artifacts/string_gnn_rebuild_v1_smoke \
  --export-dir /workspace/models/STRING_GNN_PublicRebuild_v1_smoke \
  --epochs 5 \
  --patience 5 \
  --seeds 3 \
  --hidden-dim 256 \
  --layers 2 \
  --smooth-edges 20000 \
  --symlink /home/Models/STRING_GNN_PUBLIC_REBUILD_SMOKE
```

## 在 harness 中的推荐用法

推荐作为新的 artifact id 接入，而不是覆盖原始 `/home/Models/STRING_GNN`：

- `official_string_gnn_model_dir`：继续保留为 GenBio 原始 checkpoint，若不可验证公开则 strict block。
- `string_gnn_public_rebuild_v1_model_dir`：指向 `/workspace/models/STRING_GNN_PublicRebuild_v1`。
- `string_gnn_public_rebuild_v1_embedding`：由模型 forward 生成 `[18866, 256]`，按照 `node_names.json` 的 row order 使用。

这样可以在报告中清楚区分：

- 原文同款 checkpoint：不可公开验证/未获得。
- public rebuild：公开数据可重建，可用于科研级替代实验，但不做数值等价声明。

## 局限性

1. 该模型学习的是公开 GNN Simple D256 teacher embedding，不是 GenBio 原始 STRING_GNN 的隐藏训练目标。
2. 当前 v1 主要验证 graph foundation artifact 的可训练、可导出、可加载、可审计；尚未完成大规模 downstream 多 cell line 验证。
3. teacher reconstruction val cosine 约 0.53，说明它是有信息量的替代 embedding，但不是 teacher 的完全复制。
4. 若未来拿到原始 `/home/Models/STRING_GNN` checkpoint，应单独登记为 original artifact，不应与本 public rebuild 混用。

## 当前状态

- smoke：通过
- formal multi-seed training：通过
- `AutoModel.from_pretrained(..., trust_remote_code=True)`：通过
- 输出 shape：`[18866, 256]`
- 大文件存储：RunPod network volume
- GitHub 提交范围：脚本、manifest、报告、中文说明
