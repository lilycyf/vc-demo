# AIVC Perturbation Demo Day 1 Dataset Audit
Source: `data/raw/merged_data.h5ad`
## Dataset Shape
- Cells: `9156`
- Genes: `31942`
- X type: _CSRDataset
- X density: None

## Key Columns
- Present: `['Treat', 'Drug', 'Dose', 'FixedTimePoint', 'CellLines', 'BioRep', 'Batch', 'Well', 'Sample']`
- Missing: `[]`

## Column Cardinality
### Treat
- Unique values: 2
- Top values:
  - `Treat`: 7958
  - `Ctrl`: 1198
### Drug
- Unique values: 12
- Top values:
  - `HY-N0112-Dihydromyricetin`: 890
  - `HY-16405-PR-104`: 850
  - `HY-16209-Forodesine (hydrochloride)`: 826
  - `HY-75800-Lomibuvir`: 823
  - `HY-108969-Pyrazoloacridine`: 785
  - `HY-13744-Rubitecan`: 770
  - `HY-10443-Balapiravir`: 765
  - `HY-16503-Treosulfan`: 758
  - `HY-13543-Tretazicar`: 752
  - `HY-B0021-Doxifluridine`: 739
  - `DMSO`: 610
  - `medium`: 588
### Dose
- Unique values: 1
- Top values:
  - `10umol`: 9156
### FixedTimePoint
- Unique values: 1
- Top values:
  - `48h`: 9156
### CellLines
- Unique values: 1
- Top values:
  - `HELF`: 9156
### BioRep
- Unique values: 1
- Top values:
  - `Rep1`: 9156
### Batch
- Unique values: 2
- Top values:
  - `S3`: 7958
  - `S1`: 1198
### Well
- Unique values: 14
- Top values:
  - `47`: 890
  - `27`: 850
  - `34`: 826
  - `10`: 823
  - `31`: 785
  - `23`: 770
  - `45`: 765
  - `59`: 758
  - `73`: 752
  - `21`: 739
  - `85`: 339
  - `92`: 309
  - `84`: 301
  - `93`: 249
### Sample
- Unique values: 14
- Top values:
  - `S3_47`: 890
  - `S3_27`: 850
  - `S3_34`: 826
  - `S3_10`: 823
  - `S3_31`: 785
  - `S3_23`: 770
  - `S3_45`: 765
  - `S3_59`: 758
  - `S3_73`: 752
  - `S3_21`: 739
  - `S1_85`: 339
  - `S1_92`: 309
  - `S1_84`: 301
  - `S1_93`: 249

## Control Candidates
```json
{
  "Treat": [
    "Ctrl"
  ],
  "Drug": [
    "DMSO"
  ]
}
```

## Condition Feasibility
```json
{
  "columns": [
    "CellLines",
    "Drug",
    "Dose",
    "FixedTimePoint"
  ],
  "n_conditions": 12,
  "n_cells_per_condition": {
    "min": 588,
    "median": 767.5,
    "mean": 763.0,
    "max": 890
  },
  "top_conditions": [
    {
      "CellLines": "HELF",
      "Drug": "HY-N0112-Dihydromyricetin",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 890
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-16405-PR-104",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 850
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-16209-Forodesine (hydrochloride)",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 826
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-75800-Lomibuvir",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 823
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-108969-Pyrazoloacridine",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 785
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-13744-Rubitecan",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 770
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-10443-Balapiravir",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 765
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-16503-Treosulfan",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 758
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-13543-Tretazicar",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 752
    },
    {
      "CellLines": "HELF",
      "Drug": "HY-B0021-Doxifluridine",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 739
    },
    {
      "CellLines": "HELF",
      "Drug": "DMSO",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 610
    },
    {
      "CellLines": "HELF",
      "Drug": "medium",
      "Dose": "10umol",
      "FixedTimePoint": "48h",
      "n_cells": 588
    }
  ]
}
```

## Split Feasibility
```json
{
  "heldout_Drug": {
    "n_groups": 12,
    "min_cells_per_group": 588,
    "median_cells_per_group": 767.5
  },
  "heldout_CellLines": {
    "n_groups": 1,
    "min_cells_per_group": 9156,
    "median_cells_per_group": 9156.0
  },
  "heldout_Batch": {
    "n_groups": 2,
    "min_cells_per_group": 1198,
    "median_cells_per_group": 4578.0
  },
  "heldout_BioRep": {
    "n_groups": 1,
    "min_cells_per_group": 9156,
    "median_cells_per_group": 9156.0
  }
}
```

## Recommended Demo Task
Predict target-gene DEG class for each `CellLines x Drug x Dose x FixedTimePoint` pseudobulk condition, then rank drug-dose-time conditions by predicted response strength.

## Day 1 Decision
This dataset is suitable for a real perturbation-response harness demo if matched control/baseline conditions can be identified from `Treat` or `Drug`. The next step is to build pseudobulk condition tables and DEG labels.
