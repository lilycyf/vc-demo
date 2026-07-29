# VCHarness 模块宇宙 Artifact 获取与重建清单（中文）

本文档记录当前 RunPod network volume 上已经下载、已经构建、仍不可公开验证、以及需要自行训练/重建的 VCHarness-style 模块。这里的“可用”指达到科研论文级使用场景：来源明确、版本/路径/形状/词表/行顺序/provenance 可审计，并能在下游实验中复现。

## 当前机器与保存策略

- RunPod：RTX PRO 6000 Blackwell，network volume `string-net-artifacts`。
- 大模型目录：`/workspace/models`，并通过 `/home/Models -> /workspace/models` 兼容 public VCHarness 路径。
- 数据/artifact 目录：`/workspace/vc-demo/data`。
- 外部源码目录：`/workspace/_external`。
- GitHub 只保存脚本、manifest、checksum、小型报告；不提交模型权重、`.h5ad`、`.npz`、checkpoint、`data/`、`nodes/`。

## 一页结论

- `AIDO.Cell-100M`：已经下载并通过 AutoConfig/AutoTokenizer/AutoModel smoke；可以作为论文级公开 checkpoint 使用，但 runtime patch 来自公开 ModelGenerator。
- `STRING_GNN` 原文 checkpoint：目前不可公开验证下载。HF repo 可访问但只有 `.gitattributes`，没有 config/weights/graph data/node names。当前 `/home/Models/STRING_GNN` 是兼容重建，不是原文同款。
- `STRING graph`、`GNN Simple embedding`、`AIDO cached embedding`、`ESM2 embedding`、official K562 task data：已下载。
- `Reactome pathway membership`：已从公开 Reactome 构建，按 K562 target genes 对齐。
- `scFoundation`、`scGPT`：源码/下载入口明确，但还没有生成本任务 row-aligned embedding，因此不能标为 present；需要 acquisition/encoding pipeline。
- `Geneformer V2-104M`：已下载，可作为公开替代模块，不是 VCHarness 原文模块。

## 模块清单

### 1. AIDO.Cell-100M model dir

- 作用：细胞基础模型 backbone / public best-node 依赖
- 当前状态：已下载并 smoke 通过
- 本地位置：`/workspace/models/AIDO.Cell-100M -> /home/Models/AIDO.Cell-100M`
- 公开来源：Hugging Face genbio-ai/AIDO.Cell-100M + ModelGenerator gb.cell runtime
- 是否原文/论文级等价：接近原文同款公开 checkpoint；runtime 文件由公开 ModelGenerator 代码补齐，已 AutoConfig/AutoTokenizer/AutoModel smoke。
- 如何使用：在 public wrapper 或 native candidate 中通过 /home/Models/AIDO.Cell-100M 加载；记录 transformers==4.47.1。
- 如果现在不可用，怎么做到可用：无需重建；若要更严格，记录 HF commit sha 并固定 ModelGenerator commit。
- 资源与时间预估：已占用约 381MB；二次准备约 10-30 分钟，取决于下载速度。

### 2. AIDO.Cell-100M K562 cached embedding

- 作用：K562 root baseline 输入特征
- 当前状态：已下载
- 本地位置：`/workspace/vc-demo/data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad`
- 公开来源：genbio-ai/foundation-models-perturbation HF dataset
- 是否原文/论文级等价：K562 public artifact，论文级可用于本 task baseline。
- 如何使用：作为 train/val/test row-level feature，不需要重新编码。
- 如果现在不可用，怎么做到可用：无需重建；迁移到新 cell line 时需要对应 cell line embedding 或用 AIDO checkpoint 重新编码。
- 资源与时间预估：约 98MB；二次下载数分钟。

### 3. GNN Simple Official D256 embedding

- 作用：STRING/GNN root baseline 输入特征、STRING_GNN compatibility 重建输入
- 当前状态：已下载
- 本地位置：`/workspace/vc-demo/data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad`
- 公开来源：genbio-ai/foundation-models-perturbation HF dataset
- 是否原文/论文级等价：K562 public artifact；可论文级用于 GNN Simple baseline，但不是 /home/Models/STRING_GNN 原始 checkpoint。
- 如何使用：作为 row-level feature 或兼容 STRING_GNN 节点 embedding source。
- 如果现在不可用，怎么做到可用：无需重建；若要原文 STRING_GNN checkpoint，见 STRING_GNN 条目。
- 资源与时间预估：约 42MB；二次下载数分钟。

### 4. STRING keep20 graph

- 作用：PPI/STRING graph prior
- 当前状态：已下载
- 本地位置：`/workspace/vc-demo/data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt`
- 公开来源：genbio-ai/foundation-models-perturbation HF dataset
- 是否原文/论文级等价：公开 graph prior，可论文级用于图先验；不是模型权重。
- 如何使用：用于 graph-aware head、Laplacian smoothing、STRING_GNN 兼容重建或重新训练。
- 如果现在不可用，怎么做到可用：无需重建；若迁移 cell line，要检查 perturbation/target gene coverage。
- 资源与时间预估：约 26MB；二次下载数分钟。

### 5. 原文 /home/Models/STRING_GNN checkpoint

- 作用：public VCHarness static code 与部分 graph encoder blueprint 依赖
- 当前状态：公开源不完整，不能验证直接下载
- 本地位置：`/home/Models/STRING_GNN 当前为 compatibility reconstruction`
- 公开来源：HF genbio-ai/STRING_GNN 公开 repo 只列出 .gitattributes；VCHarness static code 期望 config/weights/graph_data/node_names
- 是否原文/论文级等价：不是原文同款；当前 compatibility 目录可运行但必须标注 reconstructed_compatibility。
- 如何使用：只能用于工程连通/兼容实验；不能声称数值复刻原文 checkpoint。
- 如果现在不可用，怎么做到可用：两条路：1. 向 GenBio/作者获取原始 checkpoint；2. 用公开 STRING graph + GNN embedding/扰动任务自训练 STRING_GNN，定义 vocab、edge weights、256维输出、训练目标、多 seed downstream validation。
- 资源与时间预估：兼容重建 1-3 小时；论文级自训练 0.5-2 天、约 5-30 GPUh；严格数值复刻需要作者 checkpoint。

### 6. ESM2 D1280 gene embedding

- 作用：protein/gene embedding module；perturbed gene/target gene representation
- 当前状态：已下载
- 本地位置：`/workspace/vc-demo/data/artifacts/gene_embeddings/ESM2_D1280.h5ad`
- 公开来源：genbio-ai/foundation-models-perturbation HF dataset
- 是否原文/论文级等价：公开 embedding，可论文级作为 ESM2 module artifact；需明确是 cached embedding，不是 fine-tuned ESM2。
- 如何使用：用于 target-aware head、protein branch、gene identity features。
- 如果现在不可用，怎么做到可用：无需重建；如迁移到其它物种或新 gene vocab，需要重新跑 ESM2 或找 matching embedding。
- 资源与时间预估：约 231MB；二次下载数分钟。

### 7. Reactome pathway membership

- 作用：pathway prior / pathway pooling blueprint
- 当前状态：已从公开源构建并验证
- 本地位置：`/workspace/vc-demo/data/artifacts/pathways/k562_target_pathway_membership.npz`
- 公开来源：ReactomePathways.gmt.zip，Homo sapiens pathways，按 K562 target genes 对齐
- 是否原文/论文级等价：论文级可审计 derived artifact；不是 VCHarness 原文私有 artifact，但来源公开、可复现。
- 如何使用：用于 pathway pooling；target coverage 0.6704888352444176, kept pathways 2034。
- 如果现在不可用，怎么做到可用：迁移 cell line 时用对应 target_gene order 重建，不可复用旧矩阵。
- 资源与时间预估：下载/构建 5-15 分钟；无需 GPU。

### 8. scFoundation checkpoint / embeddings

- 作用：single-cell foundation module / cell encoder
- 当前状态：源码存在，论文级 row-aligned artifact 尚未构建
- 本地位置：`/workspace/_external/scFoundation；未生成 row-aligned embeddings`
- 公开来源：官方 GitHub biomap-research/scFoundation；README 指向 model/Figshare/平台
- 是否原文/论文级等价：当前还不是可用 task artifact；只有源码/说明不足以作为 present。
- 如何使用：需要先获得官方 checkpoint、gene vocab、normalization，并对 exact train/val/test rows 编码成 embedding manifest。
- 如果现在不可用，怎么做到可用：准备数据：official task h5ad 或表达矩阵、split row order、gene order/vocab 映射；定义输出维度、是否 freeze、checksum；运行 encoder；验证 row count/split order/无标签泄漏。
- 资源与时间预估：下载/环境 0.5-1 天；编码 1-6 GPUh；若从零预训练不现实，需百万级单细胞数据和多 GPU 天到周。

### 9. scGPT checkpoint / embeddings

- 作用：single-cell foundation alternative / cell embedding encoder
- 当前状态：源码存在，checkpoint 为 Google Drive source，需要单独下载验证
- 本地位置：`/workspace/_external/scGPT；未生成 row-aligned embeddings`
- 公开来源：官方 GitHub bowang-lab/scGPT；README 给 whole-human 等 Google Drive folders
- 是否原文/论文级等价：不是 VCHarness 原文核心同款，但可作为大于原文 search space 的公开替代模块。
- 如何使用：需要下载 checkpoint folder + vocab，然后将 exact task rows tokenize/encode。
- 如果现在不可用，怎么做到可用：准备数据：原始表达矩阵、gene symbol/Ensembl 转换、scGPT vocab、normalization/binning/tokenization config；输出 row-aligned embedding h5ad/npz 和 manifest。
- 资源与时间预估：下载/环境 0.5-1 天；编码 1-8 GPUh；fine-tune 0.5-2 天。

### 10. Geneformer V2-104M

- 作用：single-cell foundation 替代模块，扩展 search space
- 当前状态：已下载
- 本地位置：`/workspace/models/Geneformer/Geneformer-V2-104M`
- 公开来源：Hugging Face ctheodoris/Geneformer
- 是否原文/论文级等价：不是 VCHarness 原文模块；可作为“比原文更大 search space”的公开替代候选。
- 如何使用：需要后续写 tokenizer/encoder adapter，把 task rows 转成 Geneformer tokenized cells 并导出 embeddings。
- 如果现在不可用，怎么做到可用：若要论文级使用：补 tokenization pipeline、gene median dictionary、row order manifest、embedding checksum、多 seed downstream validation。
- 资源与时间预估：已下载 405.4 MB；编码预计 1-6 GPUh。

### 11. Regulatory network prior

- 作用：TF/gene regulatory prior / regulatory blueprint
- 当前状态：未定义 source，因此不能 present
- 本地位置：`未生成`
- 公开来源：候选公开源：DoRothEA、CollecTRI、ChEA、ENCODE 等，需选定版本
- 是否原文/论文级等价：当前不可用；必须先定义 biological semantics 和 evidence threshold。
- 如何使用：一旦 source 固定，可构建 target/perturbation aligned edge table 或 sparse matrix。
- 如果现在不可用，怎么做到可用：准备数据：TF-target edge list、species/version/evidence score、gene ID mapping、threshold、direction/sign；验证 coverage 和无标签泄漏。
- 资源与时间预估：构建 2-8 小时；论文级验证 0.5-2 天。

### 12. Public VCHarness static code/tree

- 作用：benchmark scaffold / public best-node reference
- 当前状态：已 clone
- 本地位置：`/workspace/_external/VCHarness`
- 公开来源：GitHub genbio-ai/VCHarness
- 是否原文/论文级等价：公开 case-study scaffold；不是完整内部 orchestrator。
- 如何使用：用于 public static node wrapper、tree catalog、best path 对齐。
- 如果现在不可用，怎么做到可用：若依赖不可公开 checkpoint，则只能 wrapper blocker 或 compatibility path，不能声称数值等价。
- 资源与时间预估：clone 数分钟；benchmark 训练成本取决于 node。

## 训练/重建模块需要什么数据

### STRING_GNN 自训练或论文级重建

- 数据类型：STRING/PPI 图边表、node vocabulary、可选 node embedding teacher、下游扰动预测 task。
- 数据内容：gene/protein node id、edge weight/confidence、K-hop neighborhood、D=256 embedding target 或 contrastive/autoencoding objective。
- 必须定义：node order、edge filtering threshold、self-loop/normalization、输出维度、训练目标、validation metric、与下游 target gene order 的映射。
- 开源可获得性：STRING graph 和 GNN_Simple embedding 已公开；原文 checkpoint 未公开。可以做论文级“公开重建”，但不能做原文 checkpoint 数值复刻。
- 推荐阶段：先 teacher reconstruction 使输出接近 GNN_Simple D256，再接入 K562 downstream validation，多 seed 验证是否稳定提升 root。

### scFoundation row-aligned embeddings

- 数据类型：official task expression matrix、split row order、gene vocabulary、scFoundation checkpoint。
- 数据内容：每个 perturbation/sample 的表达向量、gene id 映射、normalization/binning 配置。
- 必须定义：输入 gene order、缺失 gene 填充策略、输出 embedding 层、是否 freeze、batch size、row order checksum。
- 开源可获得性：源码和部分模型说明公开；具体 checkpoint/平台下载需要 source-backed acquisition。若拿不到 checkpoint，不应随机初始化替代。
- 预计：下载/环境 0.5-1 天；编码 1-6 GPUh；如果从零预训练，需大规模公开 scRNA 数据和多 GPU 周级，不适合作为当前首个训练案例。

### scGPT row-aligned embeddings

- 数据类型：official task expression matrix、gene vocabulary、scGPT checkpoint folder、tokenization config。
- 数据内容：表达矩阵、gene symbol/Ensembl 转换、vocab、模型权重。
- 必须定义：tokenization 排名/截断策略、max length、embedding extraction layer、row order、无标签泄漏。
- 开源可获得性：官方 GitHub 给出 Google Drive checkpoint folder；需要单独下载并验证文件完整性。
- 预计：下载/环境 0.5-1 天；编码 1-8 GPUh；fine-tune 0.5-2 天。

### Regulatory network prior

- 数据类型：TF-target/regulatory edge list、evidence score、direction/sign、gene id mapping。
- 数据内容：例如 DoRothEA/CollecTRI/ChEA/ENCODE 等来源之一，必须固定版本和过滤规则。
- 必须定义：是否有方向、是否有激活/抑制符号、score threshold、target coverage、perturbation coverage。
- 开源可获得性：有多个公开替代源，但不是唯一标准；必须先选 source policy 才能成为论文级 artifact。
- 预计：2-8 小时构建，0.5-2 天做 coverage/downstream validation。

## 二次复现命令草案

```bash
mkdir -p /workspace/models /workspace/artifacts /workspace/cache/huggingface /workspace/_external
ln -sfn /workspace/models /home/Models
cd /workspace/vc-demo
pip install -e . anndata h5py numpy pandas scipy requests safetensors "transformers==4.47.1" "tokenizers<0.22" huggingface_hub
python scripts/acquire_vcharness_artifact_universe.py
python scripts/prepare_official_k562_missing_files.py --output experiments/string_net_artifact_project/missing_files_preparation.json
python scripts/validate_official_model_dirs.py --output experiments/string_net_artifact_project/model_dir_validation.json
```

## 最推荐的独立大成果

最适合做成独立项目的是 `STRING_GNN` 公开重建训练：它的数据最完整、目标最明确、和 VCHarness/K562 search loop 结合最直接。最终成果可以是一个可复现的 `/home/Models/STRING_GNN` 论文级公开重建 artifact，包括训练脚本、config、node order、graph_data、weights、checksum、多 seed downstream 报告。这个成果不会替代原文 checkpoint，但可以成为我们框架里真正可复用的 graph foundation module。

## 机器可读文件

- `/workspace/vc-demo/experiments/string_net_artifact_project/vcharness_artifact_universe_status.json`
- `/workspace/vc-demo/experiments/string_net_artifact_project/artifact_acquisition_sweep_manifest.json`
- `/workspace/vc-demo/experiments/string_net_artifact_project/model_dir_validation_transformers447.json`
- `/workspace/vc-demo/experiments/string_net_artifact_project/geneformer_v2_104m_manifest.json`
