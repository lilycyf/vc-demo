# Continue K562 Resume Pressure Test To 75+ Trained Nodes

- Branch: `official-k562-scientific-policy-run-50`
- Pre-commit HEAD: `4d7baf8`
- Status counts: `{'trained': 109, 'requires_artifact_acquisition': 9, 'failed': 1}`
- Trained target met: `True`
- Implementation queue items: `0`
- Acquisition queue items: `9`
- Acquisition artifacts: `regulatory_network_artifact, scfoundation_cell_embeddings, single_cell_foundation_model_artifact`
- Failure count: `1`
- Backend audit: `passed` issues=`[]`
- Fallback used: `False`

## Best Models

- Best root: `official_k562_native_public_best_reimplementation` (None), val=0.46794524788856506, test=0.5256422758102417
- Best overall: `official_k562_native_p1_official_aido_string_fusion_66a588f9` (official_aido_string_fusion), val=0.4884769916534424, test=0.518327534198761

## New Trained Nodes

| node | strategy | val Macro-F1 | test Macro-F1 |
|---|---|---:|---:|
| `official_k562_p1_official_swa_or_checkpoint_ensemble_63c03f89` | `official_swa_or_checkpoint_ensemble` | 0.29424625635147095 | 0.3001604378223419 |
| `official_k562_p1_official_aido_string_fusion_f4155be3` | `official_aido_string_fusion` | 0.31672731041908264 | 0.3241053819656372 |
| `official_k562_native_p1_official_native_public_best_reimplementation_f10eb662` | `official_native_public_best_reimplementation` | 0.4298854172229767 | 0.46175146102905273 |
| `official_k562_native_p1_official_string_gnn_attention_18d05ea9` | `official_string_gnn_attention` | 0.44279471039772034 | 0.48471513390541077 |
| `official_k562_native_p1_official_aido_lora_adapter_069eadbc` | `official_aido_lora_adapter` | 0.40285536646842957 | 0.4309944808483124 |
| `official_k562_native_p1_official_target_gene_head_9b50d297` | `official_target_gene_head` | 0.39018404483795166 | 0.44277575612068176 |
| `official_k562_native_p5_official_class_imbalance_training_e4044bff` | `official_class_imbalance_training` | 0.3981381356716156 | 0.4165184795856476 |
| `official_k562_native_p5_official_target_graph_conditioned_head_47986c6a` | `official_target_graph_conditioned_head` | 0.3505689203739166 | 0.35968366265296936 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_6be02781` | `official_string_gnn_attention` | 0.347951203584671 | 0.3755711615085602 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_b55aad86` | `official_aido_string_fusion` | 0.41199347376823425 | 0.435312420129776 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_8625f823` | `official_aido_lora_adapter` | 0.3996128737926483 | 0.4147969186306 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_03a94485` | `official_target_gene_head` | 0.3763342797756195 | 0.40293872356414795 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_9a3ff6ec` | `official_aido_string_fusion` | 0.40747591853141785 | 0.4492966830730438 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_gnn_attention_cb063325` | `official_string_gnn_attention` | 0.35522904992103577 | 0.3869852125644684 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_4bce1ac6` | `official_aido_lora_adapter` | 0.4063762128353119 | 0.42752036452293396 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_target_gene_head_37175f57` | `official_target_gene_head` | 0.3939136266708374 | 0.42985954880714417 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_string_fusion_c9e646ba` | `official_aido_string_fusion` | 0.41134604811668396 | 0.43606624007225037 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_string_neighborhood_attention_8e3eed47` | `official_string_neighborhood_attention` | 0.33373308181762695 | 0.3965429365634918 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_class_imbalance_training_badb57a0` | `official_class_imbalance_training` | 0.3868987560272217 | 0.4079239070415497 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_pathway_pooling_reactome_81fc3097` | `official_pathway_pooling_reactome` | 0.34909525513648987 | 0.35900840163230896 |
| `official_k562_root_aido_gnn_embedding_mlp_p2_official_string_gnn_attention_2c8ec64e` | `official_string_gnn_attention` | 0.40434786677360535 | 0.45158159732818604 |
| `official_k562_root_aido_gnn_embedding_mlp_p1_official_aido_lora_adapter_66952171` | `official_aido_lora_adapter` | 0.34161821007728577 | 0.3512040078639984 |
| `official_k562_native_p1_official_target_graph_conditioned_head_efba71d4` | `official_target_graph_conditioned_head` | 0.4250730574131012 | 0.4723019301891327 |
| `official_k562_native_p2_official_aido_string_cross_attention_f36612a4` | `official_aido_string_cross_attention` | 0.4106624126434326 | 0.47213658690452576 |
| `official_k562_native_p3_official_target_gene_head_80566b56` | `official_target_gene_head` | 0.4030698239803314 | 0.430056095123291 |
| `official_k562_native_p1_official_aido_string_fusion_0ca95dd5` | `official_aido_string_fusion` | 0.3590296804904938 | 0.4310344159603119 |
| `official_k562_native_p1_official_aido_string_fusion_aeb536e0` | `official_aido_string_fusion` | 0.4209045469760895 | 0.46624335646629333 |
| `official_k562_native_p1_official_aido_string_fusion_1462f243` | `official_aido_string_fusion` | 0.43346723914146423 | 0.4816721975803375 |
| `official_k562_native_p1_official_aido_string_fusion_153f19d3` | `official_aido_string_fusion` | 0.434207558631897 | 0.48632845282554626 |
| `official_k562_native_p1_official_aido_string_fusion_903c8f73` | `official_aido_string_fusion` | 0.4313340485095978 | 0.47613826394081116 |
| `official_k562_native_p1_official_aido_string_fusion_e283eea0` | `official_aido_string_fusion` | 0.4358552396297455 | 0.47353020310401917 |
| `official_k562_native_p1_official_aido_string_fusion_8ab5038c` | `official_aido_string_fusion` | 0.3817735016345978 | 0.4457017183303833 |
| `official_k562_native_p1_official_aido_string_fusion_453bde57` | `official_aido_string_fusion` | 0.40509283542633057 | 0.4663393795490265 |
| `official_k562_native_p1_official_aido_string_fusion_e41ea537` | `official_aido_string_fusion` | 0.4237285852432251 | 0.4721064269542694 |
| `official_k562_native_p1_official_aido_string_fusion_c3bb6a03` | `official_aido_string_fusion` | 0.4030437767505646 | 0.458575576543808 |
| `official_k562_native_p1_official_aido_string_fusion_697e7978` | `official_aido_string_fusion` | 0.435698002576828 | 0.4860762655735016 |
| `official_k562_native_p1_official_aido_string_fusion_6a51b4f1` | `official_aido_string_fusion` | 0.379447340965271 | 0.4485366642475128 |
| `official_k562_native_p1_official_aido_string_fusion_34dcef23` | `official_aido_string_fusion` | 0.4400881230831146 | 0.46426451206207275 |
| `official_k562_native_p1_official_aido_string_fusion_4d418087` | `official_aido_string_fusion` | 0.395025372505188 | 0.46553942561149597 |
| `official_k562_native_p1_official_aido_string_fusion_44ec01a4` | `official_aido_string_fusion` | 0.4049382209777832 | 0.4649399518966675 |
| `official_k562_native_p1_official_aido_string_fusion_cf14e3bf` | `official_aido_string_fusion` | 0.42894938588142395 | 0.46428677439689636 |
| `official_k562_native_p1_official_aido_string_fusion_3e3b60be` | `official_aido_string_fusion` | 0.4170222580432892 | 0.4762645959854126 |
| `official_k562_native_p1_official_aido_string_fusion_ad422419` | `official_aido_string_fusion` | 0.3870737850666046 | 0.44683775305747986 |
| `official_k562_native_p1_official_aido_string_fusion_7ffa279e` | `official_aido_string_fusion` | 0.42722058296203613 | 0.4679117500782013 |
| `official_k562_native_p1_official_aido_string_fusion_8d97d3db` | `official_aido_string_fusion` | 0.3978526294231415 | 0.45886334776878357 |
| `official_k562_native_p1_official_aido_string_fusion_3bc03a7b` | `official_aido_string_fusion` | 0.39865219593048096 | 0.45868924260139465 |
| `official_k562_native_p1_official_aido_string_fusion_334b1eb4` | `official_aido_string_fusion` | 0.4371725618839264 | 0.48447296023368835 |
| `official_k562_native_p1_official_aido_string_fusion_c881fe1c` | `official_aido_string_fusion` | 0.4129279851913452 | 0.47075650095939636 |
| `official_k562_native_p1_official_aido_string_fusion_b7bcad75` | `official_aido_string_fusion` | 0.43535804748535156 | 0.4752737581729889 |
| `official_k562_native_p1_official_aido_string_fusion_5404c348` | `official_aido_string_fusion` | 0.44112512469291687 | 0.4740440547466278 |
| `official_k562_native_p1_official_aido_string_fusion_dac145f0` | `official_aido_string_fusion` | 0.4008048474788666 | 0.47425732016563416 |
| `official_k562_native_p1_official_aido_string_fusion_406dbc47` | `official_aido_string_fusion` | 0.43158066272735596 | 0.4660038650035858 |
