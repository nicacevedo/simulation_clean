## Step 02 — Fit M0 and test on unseen data

The previous experiments passed. The next useful question is:

Can a constant PUE estimated from one measured day accurately predict facility electricity on another day?

We need only one new script. Keep `m0_first.py`, `esif_day.py`, and the M0/W0 equations unchanged.

### 1. Experimental setup

|           | Training                  | Testing                 |
| --------- | ------------------------- | ----------------------- |
| Dataset   | NLR ESIF                  | NLR ESIF                |
| Date      | July 1, 2023              | December 1, 2023        |
| Input     | Measured IT power         | Measured IT power       |
| Reference | IT power × reported PUE   | IT power × reported PUE |
| Purpose   | Estimate constant \\(k\\) | Evaluate prediction     |

I recommend December rather than the following day because testing a different season is more informative about whether constant PUE generalizes.

Use December 1 only if it passes the existing completeness checks. Otherwise, select and record another complete December day.

### 2. Fit one parameter

M0 remains:

\\[ P^{DC}\_t=kP^{IT}\_t. \\]

For the first calibration, estimate \\(k\\) using the ratio of measured daily electricity totals:

\\[ \boxed{ \hat{k}=\frac{\sum\_{t\in train}E^{DC,ref}\_t} {\sum\_{t\in train}E^{IT}\_t} } \\]

This estimates the energy-weighted daily PUE. It is appropriate for our initial focus on facility energy accounting.

Then freeze \\(\hat{k}\\) and predict the held-out day:

\\[ \hat P^{DC}\_t=\hat{k}P^{IT}\_t. \\]

Compare against the previous \\(k=1.20\\). Report only daily energy error (%) and hourly MAE (kW).

### 3. Prepare the two small CSVs

From the repository root:

```
PY=/home/nacevedo/.conda/envs/dc_externalities/bin/python

$PY dc_resource_sim/src/data/esif_day.py 2023-07-01
mv esif_24h.csv esif_train.csv

$PY dc_resource_sim/src/data/esif_day.py 2023-12-01
mv esif_24h.csv esif_test.csv
```

Both files should contain `timestamp_utc`, `it_kw`, and `ref_dc_kw`, using the hourly reference calculated by your existing extraction script.

No raw Parquet changes or additional downloads are needed.

### 4. New script

Save this as `dc_resource_sim/src/experiments/m0_holdout.py`.

I created and tested a standalone version using synthetic CSV inputs matching the expected schema.

Download m0_holdout.py

```
"""Fit constant PUE on one day; evaluate on another."""from pathlib import Pathimport pandas as pdTRAIN = Path("esif_train.csv")TEST = Path("esif_test.csv")def read_day(path):    df = pd.read_csv(        path, usecols=["timestamp_utc", "it_kw", "ref_dc_kw"]    )    df["timestamp_utc"] = pd.to_datetime(        df["timestamp_utc"], utc=True    )    t = df["timestamp_utc"]    assert len(df) == 24 and t.dt.normalize().nunique() == 1    assert (t.diff().iloc[1:] == pd.Timedelta(hours=1)).all()    assert df[["it_kw", "ref_dc_kw"]].notna().all().all()    assert (df.it_kw > 0).all()    assert (df.ref_dc_kw >= df.it_kw).all()    return dftrain, test = read_day(TRAIN), read_day(TEST)assert train.timestamp_utc.iloc[0] != test.timestamp_utc.iloc[0]# Fit once, using training data onlyk_fit = train.ref_dc_kw.sum() / train.it_kw.sum()print(f"Fitted PUE: {k_fit:.4f}")print(f"Test reference PUE: {test.ref_dc_kw.sum() / test.it_kw.sum():.4f}")# Evaluate both models on the SAME held-out day
```

Run:

```
$PY dc_resource_sim/src/experiments/m0_holdout.py
```

### 5. What we should learn

There are three useful possibilities.

| Observation                                                    | Interpretation                                       |
| -------------------------------------------------------------- | ---------------------------------------------------- |
| Fitted \\(k\\) performs well on the test day                   | Constant PUE is a useful baseline                    |
| Fitted \\(k\\) improves over 1.20 but retains meaningful error | Calibration helps, but M0 may miss important effects |
| Fitted \\(k\\) changes substantially across seasons            | Weather or operating conditions may matter           |

One important caveat: this tests the stability of ESIF's reported PUE-based facility-power reference, not an independently metered facility load. Also, two days cannot establish generalization across the full operating range.

### 6. Minimal repository changes

Only one new committed file:

```
dc_resource_sim/
└── src/
    ├── data/
    │   └── esif_day.py           # unchanged
    └── experiments/
        ├── m0_first.py          # unchanged
        └── m0_holdout.py        # NEW
```

Keep the two CSVs uncommitted.

Completion criterion: Obtain \\(\hat{k}\\) from July 1 and compare its held-out prediction against \\(k=1.20\\) on one valid December day.

Do not introduce M1, weather regressors, cross-validation, or additional plots yet. Once we see these two errors, we can determine whether the first calibrated M0 is sufficient to justify testing a more complex power model.