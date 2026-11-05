## Step 07 — Verify the 2023 overhead increase and close the power EDA

Recommendation: Reduce Step 07 to one accounting and component-consistency check. Then move to optimization.

The attached notebooks already establish that ESIF's overhead includes cooling, pumping, HVAC, and auxiliary electricity, and that these components respond differently to operating and weather conditions (Sections B, G5, and J).

We should not repeat the component EDA, fit weather models, or create additional plots.

### 1. The only question to answer

Our 2023 experiments show:

- Cool-month overhead: approximately 55–63 kW.
- Summer overhead: approximately 75–103 kW.
- M1-fixed misses about 34 kW of summer overhead.

Which measured components account for this increase in 2023, and does their sum agree with the PUE-implied overhead?

Use the same two periods as Step 06:

| Period         | Months       | Purpose                            |
| -------------- | ------------ | ---------------------------------- |
| Cool reference | Jan–Apr 2023 | Establish component-level baseline |
| Summer         | May–Aug 2023 | Identify additional overhead       |

This is a descriptive comparison, not a causal estimate of weather effects.

### 2. Minimal implementation

Modify only `dc_resource_sim/src/experiments/m0_daily.py`.

Add the four ESIF component columns to the existing Parquet read:

```
COMP = ["cooling_kw", "pump_kw", "hvac_kw", "plug_and_light_kw"]
```

Retain these columns when constructing each hourly DataFrame in the existing `hourly` dictionary. Keep the original day-validity rules unchanged; missing component readings should be reported separately, not used to redefine the original 300-day dataset.

Then append:

```
# Step 07 — Component consistency check (2023)h = pd.concat(hourly.values()).sort_index().copy()h["overhead_kw"] = h["ref_dc_kw"] - h["it_power_kw"]h = h.dropna(subset=COMP)# Compare the same periods used in Step 06h = h[h.index.month <= 8].copy()h["period"] = "Jan-Apr"h.loc[h.index.month >= 5, "period"] = "May-Aug"cols = ["overhead_kw", *COMP]tab = h.groupby("period")[cols].mean()tab["residual_kw"] = tab["overhead_kw"] - tab[COMP].sum(axis=1)print("Hours with complete component data:", len(h))print("\nAverage power (kW):")print(tab.round(1))print("\nSummer minus cool period (kW):")print((tab.loc["May-Aug"] - tab.loc["Jan-Apr"]).round(1))
```

This requires no new dependencies, model fitting, or additional data sources.

### 3. How to evaluate the results

There are only two checks.

A. Accounting consistency

\\[ P^{overhead}\approx P^{cooling}+P^{pump}+P^{HVAC}+P^{other} \\]

Here the fourth term is the reported plug-and-light component; any remaining discrepancy should be retained as an accounting residual.

Check whether the component sum reconstructs the PUE-implied overhead. If it does not, inspect the measurement definitions before interpreting the components.

Note that this may be an identity by construction, depending on how ESIF computes its reported PUE. It is not independent meter validation.

B. Contribution to the summer increase

Calculate the change in mean power for each component between January–April and May–August.

If cooling, pumps, or HVAC account for most of the increase, this is consistent with our previous EDA.

If not, identify the unexplained component or accounting discrepancy. Do not automatically attribute it to weather.

Because Step 06 reports a median absolute overhead error while this comparison uses mean component power, the differences need not equal exactly 33.7 kW.

### 4. Stopping rule

| Outcome                                                                 | Action                                       |
| ----------------------------------------------------------------------- | -------------------------------------------- |
| Components reconcile and explain the summer increase                    | Close Step 07                                |
| Components reconcile but the summer increase is distributed differently | Record the finding and close Step 07         |
| Large accounting residual or missing measurements                       | Investigate the data boundary before closing |

Do not add M2a merely to improve ESIF's predictive accuracy. We already know from the notebooks that weather-dependent overhead can matter, and that its usefulness differs by cooling architecture.

## 5. What follows

The next experiment should be S0 from the original research plan:

A 24-hour workload-scheduling optimization using M0/W0, fixed IT-energy requirements, hourly prices, and capacity constraints.

Then compare M0 and M1-fixed under the same optimization problem.

The key mathematical distinction is already clear:

- Fixed overhead changes total facility-energy accounting.
- With continuous operation, fixed overhead does not change unconstrained cost-optimal scheduling.
- Fixed overhead can change decisions when facility-power limits become binding.

This is substantially more valuable to test next than another regression on ESIF measurements.

Final recommendation: One short component table, one accounting check, no new plots, and no new models. Step 07 should close the predictive-model investigation sufficiently to begin testing decision value, which is the central remaining question in our original research plan.