# K562 Best-Child Multi-Seed Validation

Run dir: `experiments/k562_best_child_multiseed_validation`

## Objective

Validate whether the discovered K562 best child architecture is stable across seeds, not just a lucky single run.

Fixed child architecture: parent dense logits plus official target-gene-aware low-rank / bilinear residual.

## Artifact Policy

No fallback and no compact/proxy implementation was used. `/home/Models` checkpoints are not required by this fixed architecture; missing `/home/Models` does not block this validation.

## Per-Seed Results

| Seed | Root val | Root test | Child val | Child test | Child-root val delta | Beats root? | Child val >= 0.50? |
|---:|---:|---:|---:|---:|---:|---|---|
| 3 | 0.474003 | 0.537038 | 0.486995 | 0.526746 | 0.012992 | yes | no |
| 7 | 0.462884 | 0.514589 | 0.482620 | 0.517917 | 0.019736 | yes | no |
| 11 | 0.484272 | 0.551009 | 0.482567 | 0.527186 | -0.001705 | no | no |
| 17 | 0.470629 | 0.536450 | 0.473422 | 0.527710 | 0.002793 | yes | no |
| 23 | 0.489312 | 0.534322 | 0.479917 | 0.523146 | -0.009395 | no | no |

## Aggregate

| Quantity | Mean | Std | Min | Max |
|---|---:|---:|---:|---:|
| Root val Macro-F1 | 0.476220 | 0.010610 | 0.462884 | 0.489312 |
| Root test Macro-F1 | 0.534682 | 0.013030 | 0.514589 | 0.551009 |
| Child val Macro-F1 | 0.481104 | 0.004989 | 0.473422 | 0.486995 |
| Child test Macro-F1 | 0.524541 | 0.004115 | 0.517917 | 0.527710 |
| Child-root val delta | 0.004884 | 0.011597 | -0.009395 | 0.019736 |

## Conclusion

Child beats root on average: **True**.
Child reaches target validation Macro-F1 0.50 on average: **False**.
Per-seed beat-root rate: **0.60**.
Per-seed target-reaching rate: **0.00**.

Test Macro-F1 is reported only for final comparison and was not used for selection or tuning.
