# HELF_PERTURB_DEG Harness Demo Report

- Task type: `drug_perturbation_target_gene_deg_direction_prediction`
- Stop reason: `trained-node budget exhausted (32/32)`
- Generated proposals: `128`
- Trained selected rollouts: `32`
- Generated artifact-usefulness controls: `32`
- Trained foundation-artifact children: `24`
- Pruned not selected: `128`
- Requires artifact acquisition / blocked: `0`
- Skipped: `0`
- Failed: `0`
- Fallback/proxy count: `0`
- Backprop non-trained count: `0`

## Artifact Policy

Foundation blueprints are generated with priority. If their required source-backed artifacts are present and aligned, they are materialized as parent-preserving gated residual augmentations: dense parent logits remain intact and the artifact branch adds a learnable correction. Missing or unaligned foundation model artifacts are acquired or blocked; no fallback/proxy is allowed.

## Best Root

- Val Macro-F1: `0.4041658937931061`
- Test Macro-F1: `0.4001896381378174`

## Best Generated Child

- Strategy: `foundation_pathway_drug_target_fusion`
- Val Macro-F1: `0.4286476671695709`
- Test Macro-F1: `0.41343602538108826`

## Artifact Usefulness

- Best foundation-artifact child: `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_h1dc11733ec_p66_foundation_pathway_drug_target_fusion` val=0.4286476671695709
- Best dense matched no-artifact control: `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_h176f8c786e_p58_dense_matched_capacity_no_artifact_control_control` val=0.4149172008037567
- Foundation vs root val gain: `0.024481773376464844`
- Foundation vs dense-control val gain: `0.013730466365814209`
- Interpretation: `artifact useful beyond capacity`

| Artifact child | Dense control | Artifact val | Control val | Incremental val gain |
|---|---|---:|---:|---:|
| `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_h4e9bcc3104_p33_foundation_drug_target_cross_attention` | `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_hbe505e5f20_p33_dense_matched_capacity_no_artifact_control_control` | 0.4167056977748871 | 0.40963152050971985 | 0.007074177265167236 |
| `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_h4e9bcc3104_p34_foundation_string_graph_message_passing` | `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_h1dc11733ec_p34_dense_matched_capacity_no_artifact_control_control` | 0.4157048463821411 | 0.4131428003311157 | 0.0025620460510253906 |
| `aivc_helf_perturb_root_gated_mlp_h2cb273d962_p9_hcfea836af8_p41_foundation_string_graph_message_passing` | `aivc_helf_perturb_root_gated_mlp_h2cb273d962_p9_h63eb2b3125_p41_dense_matched_capacity_no_artifact_control_control` | 0.41326066851615906 | 0.4110938012599945 | 0.0021668672561645508 |
| `aivc_helf_perturb_root_gated_mlp_h2cb273d962_p9_hcfea836af8_p42_foundation_graph_laplacian_head` | `aivc_helf_perturb_root_gated_mlp_h2cb273d962_p9_hbd135ea3af_p42_dense_matched_capacity_no_artifact_control_control` | 0.40656495094299316 | 0.4128110110759735 | -0.006246060132980347 |
| `aivc_helf_perturb_root_mlp_h926f19760f_p2_founda_h8782aedba2_p49_foundation_graph_laplacian_head` | `aivc_helf_perturb_root_mlp_h926f19760f_p2_founda_h8239c4eebf_p49_dense_matched_capacity_no_artifact_control_control` | 0.41408810019493103 | 0.4138367176055908 | 0.00025138258934020996 |
| `aivc_helf_perturb_root_mlp_h926f19760f_p2_founda_h8782aedba2_p50_foundation_pathway_pooling_encoder` | `aivc_helf_perturb_root_mlp_h926f19760f_p2_founda_h4f0ed908b8_p50_dense_matched_capacity_no_artifact_control_control` | 0.4101537764072418 | 0.41020119190216064 | -4.741549491882324e-05 |
| `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_hbe505e5f20_p57_foundation_graph_laplacian_head` | `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_h0da2fcf5db_p57_dense_matched_capacity_no_artifact_control_control` | 0.4168378412723541 | 0.40950778126716614 | 0.007330060005187988 |
| `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_hbe505e5f20_p58_foundation_pathway_pooling_encoder` | `aivc_helf_perturb_root_mlp_h926f19760f_p1_founda_h176f8c786e_p58_dense_matched_capacity_no_artifact_control_control` | 0.4153420925140381 | 0.4149172008037567 | 0.00042489171028137207 |
