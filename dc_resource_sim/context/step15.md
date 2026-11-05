## Step 15 — First water-aware scheduling experiment (S2 baseline)

Step 14 is complete. I recommend closing the power-model experiments for now and moving to water.

The results support three conclusions:

- Weather-dependent overhead improves predictions and can prevent capacity violations.
- On the tested day, its economic decision value was very small (less than $1.25/day).
- Further power-model refinement is not currently justified without stronger evidence of operational benefit.

The next valuable question is whether accounting for water changes workload scheduling decisions, and which water information is responsible.

This follows the original S2 plan and builds on the preliminary scenario analysis in Section M of the reviewed notebook, without repeating the larger simulation.

### 1. Start with one fundamental distinction

Water consumption has two separate contributions:

\\[ \boxed{ V^{total}=\sum_t \underbrace{w_0x_t}\_{\text{Direct water}} + \underbrace{\gamma_t E^{DC}\_t}\_{\text{Grid-related water}} } \\]

where:

- \\(x_t\\): IT energy processed in hour \\(t\\), kWh.
- \\(w_0\\): direct water consumption intensity, L/kWh IT.
- \\(\gamma_t\\): electricity-related water consumption intensity, L/kWh facility electricity.
- \\(E^{DC}\_t\\): facility electricity, kWh.

The critical observation is that, under W0 and fixed total IT energy,

\\[ \sum_t w_0x_t=w_0E\_{\mathrm{required}}. \\]

Direct water consumption cannot change through scheduling under W0. But grid-related water may change if \\(\gamma_t\\) varies hourly.

This is the first mechanism we should isolate before adding cooling physics.

## 2. Minimal setup

Reuse the verified Step 08 scheduling problem.

| Input                  | Step 15 choice                                      |
| ---------------------- | --------------------------------------------------- |
| Facility               | One hypothetical facility                           |
| Horizon                | 24 hours                                            |
| Baseline IT load       | 1,000 kW                                            |
| Flexible fraction      | 20%                                                 |
| IT capacity            | 1,250 kW                                            |
| Workload constraints   | Same arrivals and daily completion                  |
| Facility power         | M0, \\(k=1.0471\\)                                  |
| Direct water           | W0, \\(w_0=0.5\\) L/kWh IT (illustrative)           |
| Electricity prices     | Existing Springfield/MISO July 1 profile            |
| Grid-water consumption | Existing source-derived hourly factors, if verified |

Why M0 rather than M2a-fixed?

We want to isolate the value of water information. Introducing weather-dependent facility electricity simultaneously would make the first water experiment harder to interpret. M0 is sufficient for this controlled test.

### Data preparation

Use the existing frozen signals in:

`06_runs/20261016T0527Z_m0m1/inputs/signals_2023_v1/`

Extract the same 24 UTC hours used in Step 10.

We need one small CSV:

```
timestamp_utc
price_usd_per_kwh
grid_water_consumption_l_per_kwh
```

Before running, verify that the grid-water factor:

- Uses a consumption basis, not withdrawal.
- Has known units and geographic coverage.
- Has valid values for all 24 hours.
- Is identified as a historical/model-derived average factor, not a measured marginal response.

Do not invent hourly variability if the available factor is constant or missing.

## 3. The experiment: Three schedules

Solve the same linear scheduling problem under two objectives, then compare against the unchanged baseline.

| Schedule      | Objective                        | Purpose                                               |
| ------------- | -------------------------------- | ----------------------------------------------------- |
| Baseline      | No shifting                      | Reference operation                                   |
| Cost-optimal  | Minimize electricity cost        | Existing scheduling objective                         |
| Water-optimal | Minimize total water consumption | Test whether water information favors different hours |

The objectives are:

\\[ \min_x \sum_t p_tkx_t \\]

and

\\[ \min_x \sum_t (w_0+k\gamma_t)x_t. \\]

The second objective is equivalent to minimizing \\(\sum_t\gamma_tx_t\\) under constant WUE and fixed total IT energy.

Important: The grid-water objective is an accounting-based scheduling scenario. Historical average factors do not establish the actual marginal water saved when electricity demand shifts.

Do not introduce a water budget, groundwater constraints, or wet/dry cooling choices yet.

## 4. Minimal implementation

Create one script:

`dc_resource_sim/src/experiments/s7_water_schedule.py`

Reuse the LP from `s0_schedule.py`, including its cumulative-arrival constraints.

The only essential new logic is:

```
# After loading and validating the 24-hour price/water CSV:p = df["price_usd_per_kwh"].to_numpy(float)g = df["grid_water_consumption_l_per_kwh"].to_numpy(float)k = 1.0471w0 = 0.5# Reuse the verified scheduling solver from Step 08.x_cost = solve_schedule(k * p)# Only water's time-varying component affects the decision.if g.max() - g.min() > 1e-10:    x_water = solve_schedule(w0 + k * g)else:    print("Grid-water factor is constant: water is schedule-invariant.")    x_water = x_cost.copy()for name, x in [    ("Baseline", baseline),    ("Cost", x_cost),    ("Water", x_water),]:    direct = w0 * x.sum()    grid_water = (g * k * x).sum()    cost = (p * k * x).sum()    print(        name,        "Cost:", round(cost, 2),        "Direct L:", round(direct, 1),        "Grid L:", round(grid_water, 1),        "Total L:", round(direct + grid_water, 1),    )assert np.isclose(w0*x_cost.sum(), w0*x_water.sum())
```