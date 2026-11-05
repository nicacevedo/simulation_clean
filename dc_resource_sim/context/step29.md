# Step 29 — Water-model complexity versus temporal aggregation

## Objective
Determine how much of the **simulated direct-evaporative process-water behavior** is retained by a constant-intensity model versus a temperature-excess model when viewed hourly, daily, or monthly. **This is model-sufficiency against W2-Air simulations, not validation against water meters.**

The earlier *Prineville monthly-pattern Step 29* is postponed, not implemented. This document replaces its proposed next step.

## Reuse; do not refit

Use the same source and frozen model assumptions as `dc_resource_sim/eda/water_models/replay_observed_weather.py` (EDA Figure 06):

- Source: 2023 ESIF hourly `tdb_c`, `rh_pct`, `it_power_kw`, `valid_weather`, `valid_it`, `hour` from the **existing** `esif_facility_hourly.parquet` path in that script. The IT/weather inputs are measured at ESIF; the **direct-evaporative equipment is hypothetical**.
- **C0 — constant *evaporation* intensity**: `v_c0 = 0.14688 * it_power_kw` L/h. This was fit to W2-generated states in EDA 02. It is W0-*shaped*, but **is not** the original W0 `0.5 L/kWh` onsite direct-consumption proxy.
- **C1 — temperature-excess evaporation**: `v_c1 = 0.09788 * it_power_kw * max(tdb_c - 25.0, 0.0)` L/h. Frozen from EDA 02.
- **W2-Air — process-evaporation reference**: `direct_evap(tdb_c, rh_pct/100, it_kw=it_power_kw)` from `src/experiments/w2_air_first.py`; use the same 25°C dry-mode rule, 0.80 feasibility limit, and unchanged equipment settings. If `tdb_c <= 25`, evaporation is 0 under this operating rule. Do not fill an infeasible case with 0.

Do not recompute C0/C1 coefficients on 2023, change equipment assumptions, use municipal water bills, introduce additional models, or run optimization.

## Scope and support

1. Filter to **2023 UTC**, valid weather **and** valid IT. Check timestamp uniqueness, plausible inputs, and positive IT power. The earlier replay used **7,990 valid hours** (7,214 dry, 776 wet, 0 infeasible), leaving 770 missing hours; these are upstream sanity checks, not numbers to impute.
2. Evaluate all three models on those **same** hours. Report dry/wet/infeasible counts. An infeasible W2 hour is marked N/A, never 0; any aggregation containing it cannot be represented as a feasible full-period outcome without a fallback model.
3. For the main hourly/daily/monthly comparison, retain only **complete 24-hour UTC days** with 24 matched hourly records and no infeasible hours. Compute **monthly sums across those same retained complete days**, and label them **complete-day sampled subtotals**, not true calendar-month totals. Report the number of retained days per month. This keeps all aggregation levels on precisely the same data support.

## Three metrics only

For each C0 and C1, relative to W2-Air on the identical evaluation hours:

**(A) Volume error at each resolution:** use weighted absolute percentage error (WAPE) so the scales are comparable:

\[
\operatorname{WAPE}_{G}=\frac{\sum_{g\in G}\left|\sum_{t\in g}(\hat V_t-V^{W2}_t)\right|}{\sum_t V^{W2}_t}\times100\%,
\]

where `G` is the grouping into hours, complete days, or calendar months *of included complete days*. Do not average per-group percentage errors; dry periods may have a zero denominator. **Expected mathematical check:** hourly WAPE >= daily WAPE >= monthly WAPE, because opposite-signed errors can cancel under aggregation.

**(B) Peak-rate error:** difference between model and W2 peak hourly evaporation, L/h, over the included hours. Daily/monthly volumes do not establish hourly supply-capacity needs.

**(C) Wet-hour MAE:** mean absolute difference on hours W2 classifies as `wet`, L/h. This prevents the large fraction of zero-evaporation hours from dominating the reported accuracy.

Keep original W0 `0.5 L/kWh IT` out of the error ranking: it represents an illustrative **direct-consumption proxy**, not process evaporation. Mention it only as the accounting baseline from Step 23.

## Implementation — one small script

Create `dc_resource_sim/eda/water_models/aggregation_compare.py`. Reuse the existing parquet-loading/`direct_evap` calling pattern from `replay_observed_weather.py` without changing that script; prevent the Step 20 demonstration printout during import as in the existing EDA script.

Outputs under `dc_resource_sim/eda/water_models/`:

1. Console table (and optionally one `aggregation_summary.csv`): C0 and C1; hourly/daily/monthly WAPE; wet-hour MAE; signed peak-rate error. Include counts of all valid hours, retained complete days, and W2 modes.
2. **One figure** `figures/07_water_aggregation.png`: upper panel shows monthly **complete-day sampled** evaporation subtotals for C0, C1, W2 (m³); lower panel shows the number of complete days contributing in each month. Note the shared comparison period and missing-day limitation. Avoid plotting W0 together with process evaporation on an unlabeled common water basis.

Implementation sketch for aggregation: one row per included hour with `v_w2`, `v_c0`, `v_c1`; group by `hour.floor('D')` to require 24 records, then sum those retained hours by day and by `hour.to_period('M')`. Compute WAPE for each of the three sets of groups using the formula above. UTC timestamps remain UTC throughout.

## Checks and stopping rule

- All compared values use **the same valid hours and the same process-evaporation boundary**.
- Daily sums reconcile to underlying hourly values; monthly sampled subtotals reconcile to their included daily sums.
- All incomplete days and infeasible hours are counted and disclosed, never silently zero-filled or extrapolated to a year.
- Assert the expected WAPE ordering (within numerical tolerance); if it fails, audit grouping/support rather than changing model parameters.
- Report peak-rate error and wet-hour MAE alongside aggregate error; do not conclude a model is operationally sufficient from small monthly-volume error alone.
- **Stop after one table and one figure.** No new fit, weather data hunt, Prineville reconciliation, or additional cooling physics.

## Decision gate for Step 30

If C1 remains close to W2 at hourly and aggregated resolutions, freeze it as the reduced **process-evaporation** mapping for this equipment scenario; keep W2 for feasibility and sensitivity to equipment settings. If aggregate agreement masks large hourly peak errors, preserve W2 for hourly constraints even if C1 suffices for planning volumes. This cannot establish actual facility water predictive accuracy without measured, boundary-matched water data.


---

Context:

## Step 29 — Water-model complexity versus temporal aggregation

I recommend replacing the previous Prineville-focused Step 29. The new experiment should test whether simpler water models remain accurate relative to our physics-based reference when predictions are aggregated from hours to days and months.

The completed experiments establish:

- W0: A constant onsite direct-water-consumption proxy.
- C0: A constant-intensity approximation of W2-Air evaporation, developed in the water EDA.
- C1: A temperature-dependent approximation that closely reproduces W2-Air.
- W2-Air: The psychrometric reference, including cooling-feasibility checks.

The distinction between W0 and C0 is essential. We can compare C0, C1, and W2-Air quantitatively because all three represent process evaporation. W0 should remain a separate accounting baseline, not be ranked using evaporation-prediction errors.

### 1. The research question

Does the additional information used by C1 and W2-Air matter for hourly peaks, daily volumes, and monthly volumes?

We already know C1 performs extremely well on the simulated states and real-weather replay. Step 29 should determine whether that finding remains useful at different aggregation levels, without repeating model fitting.

### 2. Minimal experiment

Reuse the 2023 ESIF weather-and-IT dataset from Figure 06, with all parameters frozen.

| Model  | Relationship                                                  | New fitting? |
| ------ | ------------------------------------------------------------- | ------------ |
| C0     | \\(\dot V=c_0P^{IT}\\), \\(c_0=0.14688\\)                     | No           |
| C1     | \\(\dot V=\beta P^{IT}(T\_{db}-25)\_+\\), \\(\beta=0.09788\\) | No           |
| W2-Air | Existing `direct_evap` function                               | No           |

These coefficients were obtained from W2-generated training scenarios, not measured water use.

Use the same valid observations and evaluate three levels:

| Resolution | Principal comparison                     |
| ---------- | ---------------------------------------- |
| Hourly     | Absolute error and peak evaporation      |
| Daily      | Error in daily evaporation volume        |
| Monthly    | Error in accumulated modeled evaporation |

Important: The existing dataset contains 7,990 valid hours out of 8,760. We must not silently turn incomplete observations into full-day or full-month water totals.

For a clean comparison, I recommend using only complete 24-hour days, then accumulating those same days into monthly observed-day subtotals. This maintains the same evaluation sample across all three resolutions.

### 3. What should count as success?

The central metric is weighted absolute percentage error (WAPE) at each aggregation level. It measures total absolute modeled-volume error relative to total W2-Air evaporation, using the same observations.

Because errors can cancel when aggregated, hourly WAPE should be at least as large as daily WAPE, which should be at least as large as monthly WAPE. This mathematical property also tells us why agreement at the monthly level can conceal poor hourly predictions.

We should additionally retain two diagnostics: wet-hour MAE, to avoid artificially favorable results from the many dry hours, and hourly peak error, because monthly water volumes do not capture peak supply requirements.

### 4. Implementation

I prepared the complete local experiment specification:

Download Step 29 — Water Model Aggregation (.md)

Save it to `dc_resource_sim/context/step29.md`, replacing the previous proposal for a Prineville monthly-pattern plot.

Create one script, `dc_resource_sim/eda/water_models/aggregation_compare.py`, producing one comparison table and one monthly plot. Reuse the existing ESIF inputs and frozen model parameters. Do not modify earlier experiments.

### 5. What this step should establish

The main expectation is that C1 remains close to W2-Air for hourly and aggregate evaporation, while C0 loses important temperature-dependent behavior.

If confirmed, it supports a practical hierarchy:

- C0: Minimal constant-intensity approximation.
- C1: Reduced physical mapping for evaporation volumes under fixed equipment assumptions.
- W2-Air: Detailed physical reference, retained for cooling feasibility and equipment sensitivity.

The resulting comparison will not establish actual water-use accuracy, since the reference is still simulated. But it will clarify which model complexity is necessary at which temporal resolution.

My recommendation: Complete this one experiment and stop. It is directly aligned with our original model-sufficiency objective, reuses what we have established, and avoids adding more physical assumptions before we understand the existing models at the aggregation levels relevant to planning.