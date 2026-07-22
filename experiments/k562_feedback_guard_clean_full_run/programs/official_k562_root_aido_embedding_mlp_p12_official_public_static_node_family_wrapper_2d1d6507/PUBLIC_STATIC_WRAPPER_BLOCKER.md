# Public static wrapper blocker

- Node: `official_k562_root_aido_embedding_mlp_p12_official_public_static_node_family_wrapper_2d1d6507`
- Status: `implementation_skipped`
- Public code artifact: present at `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py`
- Hidden runtime artifacts: `/home/Models/AIDO.Cell-100M`, `/home/Models/STRING_GNN`
- Current pod state: `/home/Models` is absent.
- Decision: do not train fallback/proxy. Continue global queue with other executable candidates.

implementation-infeasible strict public wrapper: VCHarness public node code is present, but exact execution depends on undeclared runtime model directories /home/Models/AIDO.Cell-100M and /home/Models/STRING_GNN, and /home/Models is absent on this pod. No source-backed, shape/vocabulary/provenance-verified acquisition was available during this run, so no fallback/proxy model was trained.
