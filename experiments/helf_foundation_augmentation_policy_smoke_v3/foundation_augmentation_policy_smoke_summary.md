# HELF Foundation Augmentation Policy Smoke

This smoke validates the parent-preserving foundation-artifact policy.

- Generated proposals: 32
- Trained selected rollouts: 6
- Trained foundation-artifact children: 5
- Blocked/acquisition: 0
- Failed: 0
- Fallback/proxy: 0
- Best generated child: `foundation_graph_laplacian_head`
- Best child val Macro-F1: 0.4183642864
- Best child test Macro-F1: 0.4072152674

The key behavioral fix is that source-backed STRING/Reactome foundation proposals are now materialized as parent-preserving gated residual augmentations instead of being skipped, blocked, or pruned behind missing-checkpoint families.
