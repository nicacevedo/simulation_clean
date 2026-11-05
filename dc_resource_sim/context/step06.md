## Step 06 — Test whether M1-fixed generalizes across operating conditions

Step 05 is complete. The results strongly favor M1-fixed for the held-out September–December period. I would retain this as our current best simple electricity model for ESIF, but not yet declare it the best year-round model.

### 1. What we have established

| Model    | Test median error | Interpretation                                                    |
| -------- | ----------------- | ----------------------------------------------------------------- |
| M0       | 2.70%             | Proportional overhead is inadequate at high IT loads              |
| M1       | 2.20%             | The fitted slope extrapolates poorly                              |
| M1-fixed | 0.32%             | Approximately constant overhead predicts high-load operation well |

The key remaining question is:

Does M1-fixed also predict summer operation accurately, or does it only work well in cooler conditions?

This is more valuable than immediately fitting another model because the existing results suggest two different overhead regimes.

## 2. The minimal next experiment

Use the same `m0_daily.csv` and three models, with one additional held-out comparison.

| Experiment           | Train   | Test    | Purpose                                         |
| -------------------- | ------- | ------- | ----------------------------------------------- |
| A — Summer holdout   | Jan–Apr | May–Aug | Test generalization to elevated summer overhead |
| B — Existing holdout | Jan–Aug | Sep–Dec | Test generalization to higher IT loads          |

The second experiment is already complete. We simply want to reproduce it alongside the first.

For each experiment, refit all three models using its training period only.

Report the existing daily energy-error metrics and one additional metric: median absolute overhead error in kW.

This is important because a small facility-energy percentage error can conceal a substantial error in non-IT electricity.

## 3. Minimal code change

Modify only `dc_resource_sim/src/experiments/m1_compare.py`.

Replace the current single train/test evaluation with a small function and two calls:

```
def compare(train, test, label):    x = train.it_kwh / 24    y = train.ref_dc_kwh / 24    k = train.ref_dc_kwh.sum() / train.it_kwh.sum()    b, a = np.polyfit(x, y, 1)    a_fixed = (y - x).mean()    predictions = {        "M0": k * test.it_kwh,        "M1": 24 * a + b * test.it_kwh,        "M1-fixed": test.it_kwh + 24 * a_fixed,    }    print(f"\n{label}: {len(train)} train, {len(test)} test days")    print(f"M0 k={k:.4f}; M1 a={a:.1f}, b={b:.4f}; "          f"M1-fixed a={a_fixed:.1f}")    print("IT load range (train/test, kW):",          (train.it_kwh / 24).agg(["min", "max"]).round(),          (test.it_kwh / 24).agg(["min", "max"]).round())    for name, pred in predictions.items():        err = 100 * (pred / test.ref_dc_kwh - 1)        overhead_err = (pred - test.ref_dc_kwh) / 24        print(f"{name:9s}: median={err.abs().median():.2f}% "              f"p90={err.abs().quantile(.9):.2f}% "              f"bias={err.mean():+.2f}% "              f"overhead_MAE={overhead_err.abs().mean():.1f} kW")month = df.day.dt.monthcompare(df[month <= 4], df[month.between(5, 8)], "Summer")compare(df[month <= 8], df[month >= 9], "High-load")
```

Keep the existing CSV loading, imports, and date parsing.

The train/test IT-load ranges are essential: they show when the comparison involves extrapolation rather than interpolation.

No additional figures, datasets, or model fitting are required.

## 4. What the results will tell us

| Observation                                           | Conclusion / next action                                                                                 |
| ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| M1-fixed wins both experiments                        | Strong evidence that a simple constant-overhead model is sufficient for daily facility-energy prediction |
| M1-fixed wins in cool months but underpredicts summer | Investigate weather-dependent overhead                                                                   |
| M1 improves substantially in summer                   | Revisit whether load dependence is genuine or confounded with operating conditions                       |
| All models exhibit systematic summer errors           | Test a weather or cooling-operating variable rather than adding arbitrary model complexity               |

One caution: the summer comparison simultaneously changes weather and IT load. It tests predictive generalization but does not independently identify their effects.

## 5. What should follow Step 06?

If summer overhead errors remain systematic, the next experiment should be very small:

\\[ P^{DC}\_t=P^{IT}\_t+a+c(T_t-T_0). \\]

This is a weather-dependent fixed-overhead model, equivalent to M2a with \\(b=1\\).

It is a particularly appropriate candidate because our evidence currently suggests that:

- IT load contributes approximately one-for-one to facility power.
- Non-IT overhead has a relatively stable baseline.
- Summer introduces additional overhead that may depend on cooling conditions.

We should first check whether temperature or wet-bulb measurements explain the residual. We should not assume that summer necessarily means a cooling-temperature effect.

### One important research implication

There is already a useful connection to the eventual optimization problem:

M1-fixed can improve facility-energy predictions substantially without changing the unconstrained cost-optimal workload schedule.

Its constant overhead contributes to electricity cost but does not change the relative marginal cost of scheduling an additional unit of IT energy in different hours. It can, however, affect facility-capacity constraints.

This distinction between prediction accuracy and decision value is central to our research.

Recommendation: Run exactly the two held-out comparisons above, then stop and examine the results. Do not introduce M2a or optimization yet.

Also commit the validated `m0_daily.py` and `m1_compare.py` changes when this check passes, keeping generated CSVs and plots uncommitted.

The goal of Step 06 is simply to decide whether constant overhead is an adequate general model, or whether we have sufficient evidence to justify one weather-dependent term.