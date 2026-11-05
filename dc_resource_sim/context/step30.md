# Step 30 — Does the reduced water model preserve the scheduling decision?

**Status:** Proposed. **One experiment, one measured-weather day, two optimizations, one summary and (optional) one plot.** No model fitting, external data collection, or changes to Steps 00–29.

## 1. Purpose

Step 29 compared **predicted process evaporation** at hourly, daily, and monthly resolutions. C1 closely reproduced W2-Air *under the fixed direct-evaporative equipment scenario*. The next question is a decision-value test:

> Does C1 select a workload schedule that is almost as water-efficient as the schedule selected by W2-Air, when **both schedules are evaluated with the same W2 reference**?

This extends the earlier finding that W0-style constant coefficients cannot reward shifting a fixed amount of work between hours. It does **not** establish water savings at an operating ESIF data center: ESIF weather is measured, but the direct-evaporative cooling equipment is hypothetical.

## 2. Keep the setup controlled

- **One predetermined day:** 2023-07-24, 00:00–23:00 UTC, from the ESIF facility-hourly parquet already read by `replay_observed_weather.py` (the first day of its previously analyzed week). Check 24 distinct, consecutive, valid weather/IT hours. If incomplete or an hour is infeasible, stop and report it; do not pick a different date based on results.
- **Hypothetical constant IT demand:** 1,000 kW every hour (24,000 kWh/day); use ESIF **weather**, not ESIF's varying IT load, to isolate the weather effect. The IT baseline is assumed, not measured.
- **Exactly the Step 08 scheduling LP:** 20% of each hour's workload may be deferred, never advanced; total completed by the end of the 24 hours; 1,250 kW IT maximum. No prices, new power model, cooling-energy model, grid-water factors, or extra controls.
- **Same equipment settings as Step 20:** supply target 25 °C, maximum evaporative effectiveness 0.8, server-air rise 15 °C. Assume the same cooling architecture and settings for every candidate schedule.
- **Water boundary:** process **evaporation**, L, not facility withdrawal. Optionally convert to illustrative RO feed using previously assumed `eta=0.8`, but never label feed as observed municipal intake.

For hour `t`, evaluate W2 at 1 MW and divide the resulting L/h by 1,000 kW to obtain `w2_t` in L/kWh IT. Do the same with frozen C1:

$$
 w^{C1}_t = 0.09788\max(T_{db,t}-25,0), \quad
 V_t^m(x_t)=w_t^m x_t \quad (\Delta t=1\text{ h}).
$$

This linearization is appropriate **only because** the tested W2 model scales proportionally with IT load at fixed weather and equipment assumptions (Steps 24/29). Check cooling feasibility with **W2** before optimizing. C1 itself cannot determine feasibility.

## 3. Three policies, one reference

1. **No shifting:** `x_base[t] = 1000` kWh. This is a transparent, nonoptimized reference schedule.
2. **C1-water-optimal:** minimize `sum(w_C1[t] * x[t])` subject to the same workload constraints.
3. **W2-water-optimal:** minimize `sum(w_W2[t] * x[t])` with the identical constraints. This is the conditional reference optimum, not empirical truth.

**Evaluation:** Compute *all* reported process evaporation using `w_W2`, including the C1 schedule. Define conditional decision regret:

$$
 R_{C1} = V^{W2}(x_{C1})-V^{W2}(x_{W2}^*) \ge 0.
$$

Report also the W2 evaporation saved relative to no shifting and the peak illustrative feed rate `max_t(w_W2[t]*x[t])/0.8` (L/h). Peak feed may increase even when daily evaporation decreases.

**Constant-intensity negative control:** A model `V=c\sum x_t` cannot discriminate schedules here, irrespective of the value of `c`. You may print the **day-oracle** value `c = V_W2(x_base)/24000` solely to demonstrate that even a constant coefficient which exactly matches the baseline-day volume cannot rank the hours. Do *not* call that coefficient an out-of-sample predictor or use the frozen C0's 400% error as proof all constant models fail: C0 was calibrated on a different synthetic weather distribution.

## 4. Minimal implementation

Create only `dc_resource_sim/eda/water_models/schedule_decision_compare.py`. Reuse parquet reading and the suppressed `direct_evap` import from `replay_observed_weather.py`, and LP constraints from `s0_schedule.py`.

Core algorithm (the existing data loader should supply ordered arrays `tdb_c`, `rh_pct` for 24 validated hours):

```python
import numpy as np
from scipy.optimize import linprog

T = 24
baseline = np.full(T, 1000.0)  # hourly IT kWh; 1-hour bins
phi, it_cap = 0.20, 1250.0
fixed, arrivals = (1 - phi) * baseline, phi * baseline

# From validated weather and existing W2-Air function:
w2 = np.zeros(T)
for t in range(T):
    if tdb_c[t] <= 25.0:
        continue  # dry-mode rule already used in the EDA replay
    result = direct_evap(float(tdb_c[t]), float(rh_pct[t]) / 100,
                         it_kw=1000.0)
    assert result['mode'] != 'infeasible', f'Hour {t} infeasible'
    w2[t] = result['evaporation_lph'] / 1000.0

c1 = 0.09788 * np.maximum(tdb_c - 25.0, 0.0)
assert np.isfinite(w2).all() and np.isfinite(c1).all()
assert np.any(w2 > 0) and np.any(w2 == 0), 'Need mixed wet/dry hours'


def solve(intensity):
    r = linprog(
        intensity,
        A_ub=np.tril(np.ones((T, T))),
        b_ub=np.cumsum(arrivals),
        A_eq=np.ones((1, T)),
        b_eq=[arrivals.sum()],
        bounds=[(0, it_cap - f) for f in fixed],
        method='highs',
    )
    assert r.success, r.message
    x = fixed + r.x
    assert np.isclose(x.sum(), baseline.sum())
    assert (x <= it_cap + 1e-6).all()
    assert (np.cumsum(r.x) <= np.cumsum(arrivals) + 1e-6).all()
    return x

x_c1, x_w2 = solve(c1), solve(w2)
policies = {'baseline': baseline, 'C1': x_c1, 'W2': x_w2}
water_ref_opt = w2 @ x_w2

for name, x in policies.items():
    evap = float(w2 @ x)
    peak_feed = float(np.max(w2 * x) / 0.8)
    regret = evap - water_ref_opt
    print(name, f'W2 evaporation={evap:.1f} L',
          f'peak process feed={peak_feed:.1f} L/h',
          f'conditional regret={regret:.3f} L')

assert w2 @ x_c1 >= water_ref_opt - 1e-5
assert w2 @ baseline >= water_ref_opt - 1e-5
print('Day-oracle constant intensity (illustrative):', w2 @ baseline / baseline.sum())
```

**Important implementation detail:** The parquet's `hour` timestamps are naive-as-UTC; confirm all 24 UTC timestamps, valid weather/IT flags, and dry/wet/infeasible counts *before* the optimization. Use arrays sorted by hour. No missing-hour filling.

Save **one table** (`schedule_decision_summary.csv`) with policy, total IT energy, reference W2 evaporation, conditional regret, and peak illustrative RO feed. **Optional one plot:** hourly `w2` and `c1` intensities above, and IT profiles for baseline/C1/W2 below. Do not generate additional figures if the table already makes the outcome clear.

## 5. Interpretation and stopping rule

- **Pass:** All candidate schedules meet work-arrival, deadline and IT-capacity constraints; IT energy stays 24,000 kWh; W2 reference evaporation is used consistently; regrets are nonnegative to solver tolerance; infeasible cooling hours cause an explicit stop (not zero evaporation).
- If C1's regret is negligible compared with the water saving achievable under W2, it is **decision-sufficient for this one equipment/day scenario**. If not, inspect differences in hourly water-intensity *ranking*, not merely mean error or monthly WAPE.
- A low regret on one day is not general robustness; no water-meter validation or actual site-level water saving is claimed. Avoid relying on exact schedule equality because dry-hour ties produce multiple optima.
- **Stop after this one day and one table.** Do not optimize electricity prices, water budgets, treatment systems, other sites, or cooling modes in Step 30.

**Step 31 if warranted:** Introduce a *single* electricity cost objective and a water constraint, using a clearly labeled price scenario or geographically matched price data, to test when water-aware scheduling is actually worth a trade-off in electricity cost. The G0/G1/groundwater research remains a later layer; do not jump to it yet.

---

Context:

## Step 30 — Does water-model complexity change the scheduling decision?

Step 29 is complete. The results strongly support C1 as a reduced representation of W2-Air under our fixed equipment assumptions.

The next step should move from prediction accuracy to decision value, using the optimization framework we already tested.

I reviewed the attached data and previous EDA implementation and prepared a small, reproducible experiment.

Download Step 30 — Water-Model Decision Value (.md)

Save it as `dc_resource_sim/context/step30.md`.

### 1. What Step 29 established

| Model                               | Main result        | Conclusion                                          |
| ----------------------------------- | ------------------ | --------------------------------------------------- |
| C0 — Constant evaporation intensity | 400.2% hourly WAPE | Poor transfer to the 2023 ESIF weather distribution |
| C1 — Temperature-dependent          | 0.19% hourly WAPE  | Excellent approximation of W2                       |
| W2-Air — Psychrometric              | Physical reference | Retain for feasibility and equipment sensitivity    |

One important qualification: C0's large error partly reflects its calibration on a different synthetic weather distribution. We should not conclude that every constant-intensity model necessarily performs this poorly.

More importantly, C1's near-perfect predictions do not yet establish that it produces the same optimal operational decisions as W2.

That is the missing experiment.

## 2. The question for Step 30

Can C1 reproduce the water-optimal workload scheduling decision obtained using W2-Air?

We want to find out whether the additional psychrometric complexity changes the decision, not merely the predicted volume.

### 3. Keep the experiment minimal

Reuse the same scheduling problem from Step 08.

| Input                    | Choice                              |
| ------------------------ | ----------------------------------- |
| Horizon                  | One day: July 24, 2023, UTC         |
| Weather                  | Existing measured ESIF weather      |
| Hypothetical IT baseline | 1,000 kW                            |
| Flexible workload        | 20%                                 |
| IT capacity              | 1,250 kW                            |
| Completion               | All work by the day's end           |
| Cooling equipment        | Same assumptions as Step 20         |
| Water models             | C1 and W2-Air                       |
| Objective                | Minimize modeled direct evaporation |

We use a day from the previously analyzed July 24–30 week, which contains both dry and wet conditions.

No new weather datasets, model fitting, cooling equations, or electricity prices are needed.

### 4. Compare three schedules

| Schedule   | How it is obtained                       |
| ---------- | ---------------------------------------- |
| Baseline   | No workload shifting                     |
| C1-optimal | Minimize evaporation predicted by C1     |
| W2-optimal | Minimize evaporation predicted by W2-Air |

Evaluate all three schedules using the same W2-Air reference.

The main quantity is:

\\[ \boxed{ R\_{C1}=V^{W2}(x\_{C1})-V^{W2}(x^\*\_{W2}) } \\]

This measures how much extra modeled evaporation results from using the simpler model.

Also report total evaporation, reduction relative to the baseline, and peak process-water feed using the existing assumed treatment recovery.

The most informative outcomes are:

- If C1 and W2 have almost identical water outcomes, C1 is sufficient for this scheduling scenario.
- If C1's small prediction errors produce different decisions, inspect the hourly water-intensity rankings.
- If the baseline and optimized schedules barely differ, weather-dependent water modeling may have little operational value under these constraints.

A constant-intensity model cannot distinguish hours when total IT energy is fixed. That is our negative control; it need not be re-fitted for this experiment.

## 5. Implementation and stopping rule

Create only:

`dc_resource_sim/eda/water_models/schedule_decision_compare.py`

The attached specification includes the LP formulation, reference code, data checks, outputs, and interpretation rules.

Produce one summary table, with an optional single hourly plot.

Close Step 30 when the scheduling constraints pass, the W2-based evaluation is consistent, and we can quantify the decision regret of C1 relative to W2.

Do not introduce electricity cost, water budgets, geographic shifting, or additional cooling technology in this step.

### What comes after?

If C1 preserves the W2-optimal decision, Step 31 can introduce one electricity-price objective and one water constraint to evaluate the electricity–direct-water trade-off.

That would be our first controlled optimization linking the weather-dependent direct-water model to the cost of operating a data center.

My recommendation: Step 30 should test whether C1's outstanding predictive approximation is also sufficient for water-aware scheduling. This is a small but meaningful advance toward our original goal: identifying exactly which physical complexity matters for optimization, rather than adding complexity merely to improve predictions.