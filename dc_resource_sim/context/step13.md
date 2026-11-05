## Step 13 — Does fitting the IT-load slope improve the weather model?

### 1. Why we should consider \\(a+bP^{IT}\\)

I agree: the unrestricted affine model is the more natural general starting point. Fixing \\(b=1\\) was an empirical simplification, not a physical requirement.

The appropriate hierarchy is:

| Model     | Equation                              | Assumption                                 |
| --------- | ------------------------------------- | ------------------------------------------ |
| M1-fixed  | \\(P^{DC}=P^{IT}+a\\)                 | Overhead independent of IT load            |
| M1        | \\(P^{DC}=a+bP^{IT}\\)                | Overhead may depend on IT load             |
| M2a-fixed | \\(P^{DC}=P^{IT}+a+c(T\_{wb}-T_0)\\)  | Weather-dependent overhead, fixed IT slope |
| M2a       | \\(P^{DC}=a+bP^{IT}+c(T\_{wb}-T_0)\\) | Load- and weather-dependent overhead       |

We previously tested M1 in Steps 05–06. It performed worse than M1-fixed on the high-load holdout (2.20% versus 0.32% median daily error). Its fitted slope was apparently influenced by seasonal differences.

But that does not justify permanently fixing \\(b=1\\). It means we need to test whether the IT-load coefficient becomes more reliable once weather is included.

This is also consistent with the original EDA notebooks, where M1 and unrestricted M2a were explicitly included among the main model families.

### 2. What Step 12 establishes

The latest results provide two different conclusions.

Summer holdout: The weather model was trained only on January–April, and 54.5% of test temperatures exceeded the training range. Its failure is therefore primarily evidence of poor out-of-range generalization, not evidence against wet-bulb dependence.

High-load holdout: M2a-fixed improved hourly MAE from 12.8 to 9.2 kW and reduced the 95th-percentile positive error from 28.3 to 17.6 kW compared with M1-fixed. This is useful, although it did not uniformly improve every risk metric.

The next critical question is:

Does estimating \\(b\\), instead of fixing it at 1, improve prediction and underprediction risk when the model has already seen warm operating conditions?

This is worth testing once before taking the model into capacity-constrained optimization.

## 3. Recommended minimal experiment

Use the same 2023 ESIF hourly data. No new measurements, data extraction, or physical models.

Change the first training period so the weather model has actually observed summer conditions.

| Test                         | Train   | Hold out | Main purpose                                        |
| ---------------------------- | ------- | -------- | --------------------------------------------------- |
| A — Warm generalization      | Jan–Jul | August   | Predict unseen warm days after learning from summer |
| B — High-load generalization | Jan–Aug | Sep–Dec  | Predict higher IT loads and cooler conditions       |

Use exactly the same weather-matched observations for all four models.

For each fitted model, report:

- \\(b\\), the fitted IT-power coefficient, and \\(c\\), the weather coefficient.
- Held-out hourly MAE and 95th-percentile underprediction.
- Training-derived headroom \\(h\_{95}\\) and fraction of test hours exceeding it.
- Percentage of test observations outside the training IT-load and wet-bulb ranges.

Also flag any predictions where facility power falls below IT power. Do not silently clip them.

## 4. Minimal implementation

Create one script:

`dc_resource_sim/src/experiments/s5_affine_weather.py`

Reuse `esif_hourly_2023.csv` and `esif_weather_hourly_2023.csv`. The following is the essential comparison:

```
import numpy as npimport pandas as pdROOT = "dc_resource_sim/runs/"power = pd.read_csv(ROOT + "esif_hourly_2023.csv",                    parse_dates=["timestamp_utc"])weather = pd.read_csv(ROOT + "esif_weather_hourly_2023.csv",                      parse_dates=["timestamp_utc"])df = power.merge(weather, on="timestamp_utc", validate="one_to_one")df = df.dropna(subset=["it_power_kw", "ref_dc_kw", "twb_c"])assert df.timestamp_utc.is_uniquemonth = df.timestamp_utc.dt.monthsplits = {    "Warm": (month <= 7, month == 8),    "High-load": (month <= 8, month >= 9),}models = {    "M1-fixed": (),    "M1": ("load",),    "M2a-fixed": ("weather",),    "M2a": ("load", "weather"),}for label, (tr, te) in splits.items():    train, test = df.loc[tr], df.loc[te]    p0 = train.it_power_kw.mean()    t0 = train.twb_c.mean()    print(f"\n{label}: {len(train)} train, {len(test)} test")    for col in ["it_power_kw", "twb_c"]:        outside = ~test[col].between(train[col].min(), train[col].max())
```

All four models are fitted through identical least-squares procedures. The centered formulation for M2a is algebraically equivalent to \\(P^{DC}=a+bP^{IT}+c(T\_{wb}-T_0)\\).

No plots or additional optimization are needed.

## 5. What result would justify proceeding?

| Result                                                               | Decision                                                                       |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| M1 improves over M1-fixed on both holdouts                           | Retain the fitted IT-load slope                                                |
| M2a improves over M1 and M2a-fixed without worsening capacity risk   | Retain unrestricted M2a                                                        |
| Fitted \\(b\\) changes substantially between training periods        | Treat load dependence as poorly identified                                     |
| Weather helps warm conditions but still causes large underprediction | Do not claim the linear model is sufficient for capacity safety                |
| No model improves consistently                                       | Stop model refinement and use explicit overhead uncertainty/headroom scenarios |

An important qualification: even if we obtain a well-fitted \\(b\\), it is still an observational coefficient. We cannot automatically interpret it as the causal change in facility power when an optimizer shifts workload.

The original notebooks already warned about this distinction. It is particularly important before allowing the slope to influence scheduling decisions.

### Final recommendation

Step 13 should be our final small comparison of the existing linear power-model family, not the beginning of another EDA cycle.

The key advancement is to determine whether allowing \\(b\neq1\\) improves prediction after accounting for weather, using training data that actually contain warm conditions.

Once this comparison is complete, I would return to the original research plan's decision experiments, using the best-supported model or explicit uncertainty bounds.

The objective is not to find the lowest possible prediction error. It is to establish which facility-power relationships are sufficiently reliable to support meaningful energy, water, and capacity-constrained decisions.