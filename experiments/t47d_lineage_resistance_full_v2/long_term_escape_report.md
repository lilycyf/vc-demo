# Long-Term Escape

```json
{
  "weights": [
    0.4,
    0.25,
    0.2,
    0.15
  ],
  "weights_predeclared": true,
  "all_scalers_fit_on_development_only": true,
  "prediction_inputs": "days0/1/4 only; no observed late values enter query predictors",
  "persistence_model": "Actual interval-censored lognormal AFT trained on development endpoint counts; extrapolated survival to180 is exploratory and unvalidated",
  "month6_all_observed_clones": [
    {
      "clone_id": "GFPBC_libB_20186",
      "cell_count": 3
    },
    {
      "clone_id": "GFPBC_libB_77443",
      "cell_count": 1
    },
    {
      "clone_id": "GFPBC_libB_79970",
      "cell_count": 1
    },
    {
      "clone_id": "GFPBC_libB_92196",
      "cell_count": 5927
    }
  ],
  "eligible_positive_clones": [
    "GFPBC_libB_92196"
  ],
  "eligible_positive_ranks": {
    "GFPBC_libB_92196": 2
  },
  "descriptive_recall_at5": 1.0,
  "locked_test_positive_count": 0,
  "unseen_clone_escape_recall": null,
  "month6_claim": "No positive heldout eligible clone => unseen-escape recall undefined; do not report in-sample dominant-clone rank as prospective validation",
  "noneligible_month6_clones": [
    "GFPBC_libB_20186",
    "GFPBC_libB_77443",
    "GFPBC_libB_79970"
  ],
  "clinical_claim": "No causal reversal, restored drug sensitivity, absolute cell killing, or clinical efficacy established"
}
```
