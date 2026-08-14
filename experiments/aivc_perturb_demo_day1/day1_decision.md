# Day 1 Decision: AIVC HELF Drug Perturbation Demo

## Decision

Use `data/raw/merged_data.h5ad` to build a real VCHarness-style demo around **heldout-drug perturbation response prediction and drug response ranking**.

This is feasible because the dataset contains:

- 9,156 cells
- 31,942 genes
- 1 cell line: `HELF`
- 1 dose: `10umol`
- 1 fixed timepoint: `48h`
- 10 treated drugs plus `DMSO` and `medium` controls
- 588-890 cells per `CellLines x Drug x Dose x FixedTimePoint` condition

## Final Research Question for the Demo

Given HELF cells treated with a drug at 10uM for 48h, can the harness predict and rank target-gene transcriptional perturbation responses for heldout drugs?

## Scope Correction

The original broad proposal mentioned `Drug x Dose x Time x CellLine`. Day 1 audit shows that this dataset only supports variation across `Drug`; `Dose`, `FixedTimePoint`, and `CellLines` are fixed.

Therefore the first runnable demo should **not** claim dose optimization, time optimization, or cross-cell-line generalization.

Correct first demo scope:

```text
HELF, 10uM, 48h
Drug -> target-gene DEG response / response ranking
```

## Recommended Split

Primary split:

```text
heldout_drug
```

Secondary robustness checks:

```text
control-vs-treated sanity check
batch caveat audit
```

Do not use random-cell split for final claims.

## Recommended Labels

Build pseudobulk profiles for each drug condition and compare treated drugs against matched controls:

- primary control: `DMSO`
- secondary baseline/control: `medium`

Target label:

```text
target_gene_DEG_three_class = down / unchanged / up
```

Initial target gene set should be 512-2000 genes selected by expression/variance and Reactome/STRING mapping coverage.

## First Search Space

Roots:

- residual MLP on pseudobulk expression features
- drug identity / metadata MLP
- pseudobulk delta MLP

Source-backed artifact children:

- Reactome pathway residual
- STRING target-gene graph residual / smoothing
- RDKit drug fingerprint fusion, if drug names can be mapped to SMILES

Optional foundation branches:

- ChemBERTa drug embedding, only after SMILES mapping passes
- UCE/scGPT/Geneformer/scFoundation cell embedding, as frozen embedding artifact only

## Success Criteria for Next Step

The next implementation step should generate:

- `condition_pseudobulk.parquet/csv`
- `deg_labels.npz/json`
- `target_genes.tsv`
- `split.json`
- `task_contract.json`
- a root baseline training command

Guardrails:

- no fallback/proxy foundation artifacts
- no test metric in search reward
- no random-cell split claim
- data files are not committed to Git
