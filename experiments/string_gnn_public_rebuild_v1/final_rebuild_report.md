# STRING_GNN Public Rebuild v1 Report

This is a public rebuild trained from public graph and teacher embeddings, not the unpublished GenBio/VCHarness original STRING_GNN checkpoint.

## Export

- Export dir: `/workspace/models/STRING_GNN_PublicRebuild_v1`
- AutoModel smoke: `{'status': 'ok', 'class': 'StringGNNPublicRebuildModel', 'last_hidden_state_shape': [18866, 256]}`
- Best seed: `7`
- Best val cosine: `0.533744`

## Seed Results

- seed 3: epoch 99, val cosine 0.529594, val MSE 0.024509, test cosine 0.533334, top10 overlap 0.4250
- seed 7: epoch 98, val cosine 0.533744, val MSE 0.024540, test cosine 0.538918, top10 overlap 0.4371
- seed 11: epoch 100, val cosine 0.528345, val MSE 0.023506, test cosine 0.535617, top10 overlap 0.4267

## Provenance

- Teacher: `data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad`
- Graph: `data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt`
- Node order sha256: `42fffd3aa77b58ba08567ff58e7f2cd983396050b2b60a291c01719a162bd638`
- Graph sha256: `126b4a202837298c8b5cfd07a3dbe40baeaac84290471da78cedfefa37621d98`
- Teacher sha256: `58dee3dddb3332dbff43f21225460d20fc3c75f933a4d62c71bbca4699619e25`
