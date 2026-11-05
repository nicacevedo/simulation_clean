## Step 10 — Test decision value with real prices and different facility limits

Step 09 is complete. It demonstrated that a facility-power modeling error can lead to either an infeasible schedule or an unnecessarily expensive one.

The next step should test whether this result is robust, rather than relying on one selected facility limit and synthetic electricity prices.

### 1. What Step 09 established

| Finding                                                                     | Status             |
| --------------------------------------------------------------------------- | ------------------ |
| M0 and M1-fixed choose identical schedules without a binding facility limit | Verified           |
| A binding facility limit can change their schedules                         | Verified           |
| M0 can violate the limit when evaluated under M1-fixed                      | Verified: 16.90 kW |
| M1-fixed can be unnecessarily conservative under M0                         | Verified: $30.77   |
| These differences matter under realistic hourly electricity prices          | Not tested         |
| Results are robust to the chosen facility limit                             | Not tested         |

One important qualification: the 16.90 kW violation is a modeled counterfactual, not an observed physical violation. Neither M0 nor M1-fixed should be treated as measured ground truth.

### 2. Recommended minimal experiment

Keep exactly the same scheduling model, IT workload, constraints, and fitted coefficients from Step 09.

Make only two changes:

1. Replace synthetic prices with one real 24-hour electricity-price profile.
2. Compare four facility-power limits.

| Limit    | Purpose                                            |
| -------- | -------------------------------------------------- |
| 1,400 kW | Nonbinding control                                 |
| 1,320 kW | Near the transition between binding and nonbinding |
| 1,300 kW | Moderately restrictive                             |
| 1,250 kW | Reproduce the original binding case                |

The middle values are informative because the unconstrained schedule reaches approximately 1,308.9 kW under M0 and 1,323.1 kW under M1-fixed.

Thus, 1,320 kW is a particularly useful test: M0 can regard the unrestricted schedule as feasible while M1-fixed may still require adjustment.

This tests model sufficiency near the actual operating constraint, rather than selecting only a scenario where differences are guaranteed to be large.

### 3. Data source — use what we already have

Use the existing frozen regional signals identified in our original plan:

`data/frozen/signals_2023_v1`

Start with Springfield, Illinois (MISO) and one predetermined date, preferably July 1, 2023, if the data are complete.

Extract only:

| Column              | Requirement                             |
| ------------------- | --------------------------------------- |
| `timestamp_utc`     | 24 consecutive UTC hours, no duplicates |
| `price_usd_per_kwh` | Real hourly price, with verified units  |

Read only the relevant columns and day from the existing data. Do not download anything.

Important checks:

- Confirm whether source prices are in $/MWh; divide by 1,000 if needed.
- Verify timestamps and timezone conversion.
- Reject incomplete or duplicated days rather than filling values.
- Treat regional wholesale prices as an illustrative marginal electricity-price signal, not an actual ESIF electricity tariff.

The original data inventory noted a discrepancy between 8,904 records and the expected 8,760 hours for 2023. For this experiment, verify the selected 24-hour window explicitly; a full-year audit can wait.

Save the extracted data as `dc_resource_sim/runs/price_24h.csv`.

### 4. Implementation — reuse Step 09

Keep `s1_power_limit.py` unchanged as our verified synthetic baseline.

Create:

`dc_resource_sim/src/experiments/s2_real_prices.py`

Reuse its optimization equations and constraints. Only replace the price input and facility-limit loop.

The essential changes are:

```
import pandas as pd# Load one verified 24-hour price profiledf = pd.read_csv("dc_resource_sim/runs/price_24h.csv")df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)df = df.sort_values("timestamp_utc")expected = pd.date_range(    df.timestamp_utc.iloc[0], periods=24, freq="h")assert len(df) == 24assert df.timestamp_utc.iloc[0].hour == 0assert (df.timestamp_utc.to_numpy() == expected.to_numpy()).all()assert df.price_usd_per_kwh.notna().all()prices = df.price_usd_per_kwh.to_numpy(float)# Run the existing Step 09 optimization at each limitLIMITS = [1400.0, 1320.0, 1300.0, 1250.0]# For every limit:# 1. Optimize using M0 and M1-fixed separately.# 2. Evaluate both schedules under both reference models.# 3. Report reference feasibility and cost regret.
```

Keep the existing `linprog` formulation intact. Do not change model coefficients or workload assumptions.

For every limit, solve twice, then evaluate each schedule under each reference. That is only eight optimization runs.

### 5. Report only the quantities that matter

| Output                   | Why                                                  |
| ------------------------ | ---------------------------------------------------- |
| Facility limit (kW)      | Identifies the constraint                            |
| Schedule-producing model | Identifies the decision                              |
| Reference model          | Defines the evaluation assumptions                   |
| Maximum violation (kW)   | Measures feasibility                                 |
| Regret ($)               | Measures the cost of a feasible, suboptimal decision |

Compute regret under each common reference:

\\[ R_i=J\_{\mathrm{ref}}(x_i)-J\_{\mathrm{ref}}(x^\*\_{\mathrm{ref}}) \\]

Only report numerical regret when the schedule satisfies the reference facility constraint. Otherwise report infeasible, as in Step 09.

Also preserve the original checks for completed workload, work arrivals, IT capacity, and solver status.

For the nonbinding case, check equality of optimal objective values rather than demanding identical schedules if the real price data contain ties.

### 6. Stopping rule and next direction

Step 10 is complete when:

1. The 1,400 kW case confirms that the cost-optimal decisions remain equivalent without binding facility limits.
2. The other cases establish how reference violations and regret change with available headroom.
3. All comparisons use the same real hourly prices and reference assumptions.
4. No infeasible schedule is incorrectly reported as a cost-saving improvement.

There is no need for plots, additional price regions, weather models, or water refinements yet.

One useful physical caveat: the ESIF-based coefficients are being applied to a hypothetical 1 MW workload and a regional price scenario. This is a controlled transfer of a technology model, not a simulation of an actual ESIF electricity contract or facility limit.

## Final assessment

The next contribution is to move from:

“A modeling error can change the scheduling decision.”

to:

“Under what facility-capacity conditions does the modeling error materially affect feasibility or cost?”

That is the question Step 10 should answer.

Afterward, I would prioritize a common-reference model-sufficiency assessment across the limited operating conditions already studied, rather than immediately adding further physical complexity.

The original objective remains identifying the simplest electricity and water models that preserve the decisions that matter.