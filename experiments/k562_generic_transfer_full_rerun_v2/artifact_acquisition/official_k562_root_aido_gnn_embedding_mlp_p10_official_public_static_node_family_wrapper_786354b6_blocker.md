# Strict Framework/Contract Blocker: official_k562_root_aido_gnn_embedding_mlp_p10_official_public_static_node_family_wrapper_786354b6

- strategy: `official_public_static_node_family_wrapper`
- required public code: `/workspace/_external/VCHarness/K562_cls/static/node2-1-1-1-1-1_code.py` present
- blocker: the generated family-wrapper proposal did not materialize a specific public static node id plus `external_static_node` execution config. Current program_agent only maps `official_public_best_node` to external_static.
- strict decision: no PyTorch proxy `model.py` was written and no fallback was trained.
- next action: add framework support to select a concrete public scaffold node id and emit an external_static benchmark/smoke config for `official_public_static_node_family_wrapper`.
