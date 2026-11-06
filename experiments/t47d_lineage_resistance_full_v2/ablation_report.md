# Eight Formal Ablations

- no_barcode_informed_inputs: OOF Spearman 0.3649; True barcode kept for endpoint labels/group splitting only; predictive state pooled across TRAIN clones per condition; abundance removed
- baseline_only: OOF Spearman 0.5804; baseline_only
- no_temporal_order: OOF Spearman 0.5747; no_temporal_order
- no_pathway: OOF Spearman 0.4768; Only pathway/both views and curated pathway supervision removed; independent scVI/CellRank/PCA components preserved
- shuffled_gene_memberships: OOF Spearman 0.4600; One fixed global gene permutation preserves all pathway sizes and overlaps; NOT pathway-column permutation
- matched_capacity_no_artifact: OOF Spearman 0.4898; Each pipeline level retains original representation width using fixed random gene projection; gene selection/scalers training-only
- no_treatment_interaction: OOF Spearman 0.3868; Removes drug covariates at every inherited level; cross-attention/bilinear condition interaction disabled
- no_dense_parent_branch: OOF Spearman 0.5563; Removes inherited prediction branch AND neural internal dense branch; readout itself remains necessary
