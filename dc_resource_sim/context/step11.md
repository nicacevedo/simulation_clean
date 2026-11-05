## Step 11 — Does model error create real hourly capacity risk?

Step 10 is complete. The real-price experiment confirms that model choice can affect facility-limit feasibility, while the cost penalty was very small for the selected day.

The most valuable next step is not another price simulation. We should now use the measured ESIF data to quantify how much facility power M0 and M1-fixed can underestimate.

This directly connects our predictive-model experiments (Steps 00–07) to our scheduling experiments (Steps 08–10).

### 1. What we know and what is missing

| Finding                                                        | Status                                 |
| -------------------------------------------------------------- | -------------------------------------- |
| Fixed overhead often predicts daily facility energy accurately | Established                            |
| Summer overhead differs systematically                         | Established                            |
| Model mismatch can make an optimized schedule infeasible       | Established under simulated references |
| Real prices can make cost regret small                         | Established for one selected day       |
| How much hourly power the models underestimate on unseen data  | Next question                          |

The last question is important: a small daily energy error does not guarantee accurate prediction of the hourly facility peak.

### 2. The minimum experiment

Use the same 300 complete ESIF days, without fitting new model structures.

Reuse the Step 06 chronological splits:

| Test      | Train   | Evaluate |
| --------- | ------- | -------- |
| Summer    | Jan–Apr | May–Aug  |
| High-load | Jan–Aug | Sep–Dec  |

Evaluate only M0 and M1-fixed. M1 was already shown to generalize poorly in these comparisons.

For each model, define the hourly prediction error:

\\[ e_t=P_t^{DC,ref}-\hat P_t^{DC}. \\]

Positive \\(e_t\\) means the model underestimates facility power, which is the dangerous direction for capacity constraints.

Report:

- Percentage of held-out hours with \\(e_t>0\\).
- 95th percentile of positive hourly error.
- Largest hourly underprediction.
- Percentage of held-out hours exceeding a headroom allowance calibrated on training data.

### 3. Test a simple headroom allowance

From training data only, calculate

\\[ h\_{95}=\max\left(0,Q\_{0.95}(e_t^{train})\right). \\]

Then check how often held-out errors exceed \\(h\_{95}\\).

This directly tests whether a simple fixed safety allowance remains useful across changing operating conditions.

Do not recalibrate the allowance on held-out data. Also, \\(h\_{95}\\) is a historical diagnostic, not a hard operational safety guarantee.

### 4. Minimal implementation

The existing `m0_daily.py` already retains the validated hourly observations. Export them once by adding:

```
pd.concat(hourly.values()).sort_index()[    ["it_power_kw", "ref_dc_kw"]].to_csv(    "dc_resource_sim/runs/esif_hourly_2023.csv",    index_label="timestamp_utc")
```

This should produce 7,200 hourly observations.

Create one short script:

`dc_resource_sim/src/experiments/s3_hourly_risk.py`

```
"""Step 11: Held-out hourly underprediction and headroom."""import pandas as pddf = pd.read_csv(    "dc_resource_sim/runs/esif_hourly_2023.csv")df["timestamp_utc"] = pd.to_datetime(    df["timestamp_utc"], utc=True)assert len(df) == 7200assert df.timestamp_utc.is_uniqueassert df[["it_power_kw", "ref_dc_kw"]].notna().all().all()month = df.timestamp_utc.dt.monthsplits = {    "Summer": (month <= 4, month.between(5, 8)),    "High-load": (month <= 8, month >= 9),}for label, (train_mask, test_mask) in splits.items():    train, test = df[train_mask], df[test_mask]    # Same calibration as Step 06    k = train.ref_dc_kw.sum() / train.it_power_kw.sum()    a = (train.ref_dc_kw - train.it_power_kw).mean()    for name in ["M0", "M1-fixed"]:        if name == "M0":            pred_train = k * train.it_power_kw            pred_test = k * test.it_power_kw        else:            pred_train = train.it_power_kw + a            pred_test = test.it_power_kw + a
```

No new source data, weather regressions, optimizations, or figures are required.

### 5. How to interpret the results

| Observation                                                 | Implication                                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------------------- |
| M1-fixed has small underprediction in high-load months      | Supports its use for that operating regime                                |
| M1-fixed frequently exceeds training headroom in summer     | Constant overhead is insufficient for robust year-round capacity planning |
| M0 performs better in summer but poorly in high-load months | Confirms that neither model is universally adequate                       |
| Training headroom works reliably in both holdouts           | A simple conservative model may be sufficient without additional physics  |

The last result must be interpreted cautiously: these are historically observed hourly prediction errors, not direct tests of the counterfactual power consumption of a shifted workload. Prediction errors can change when operating conditions or workloads change.

## 6. What should follow?

If the summer errors exceed the training-derived headroom substantially, the next justified refinement is a weather-dependent intercept, not unrestricted affine M1:

\\[ P_t^{DC}=P_t^{IT}+a+c(T_t-T_0). \\]

We already know from the notebooks that weather-conditioned overhead is worth considering. Step 11 would establish whether it is necessary specifically for safe facility-capacity decisions, rather than simply for prediction accuracy.

If hourly capacity risk proves modest, we should stop refining power models and advance to the original S2 water-model decision experiments.

Final recommendation: Run this single held-out hourly-risk experiment and stop. We have already established that inaccurate power models can change scheduling feasibility. Step 11 determines whether the observed ESIF errors are large and systematic enough to make that concern meaningful.

This is the most direct path toward the project's central objective: identifying which additional physical information is necessary for reliable optimization decisions, rather than adding model complexity for its own sake.