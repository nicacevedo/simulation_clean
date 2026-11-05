# Step 31 — Water-saving schedules under a peak treatment-feed limit

**Research question:** *Can hourly workload shifting reduce daily process evaporation **without expanding peak water-feed capacity**? If a reduced water model (C1) chooses a schedule, does it actually satisfy that capacity when checked against W2-Air?*

**Keep Step 30 fixed.** This is one additional physical constraint, not a new cooling model, calibration, price optimization, or groundwater model. ESIF provides **observed weather**, while the data center, workload flexibility, air-side cooling system and treatment recovery are **hypothetical**.

## 1. Freeze the input and reproducibility anchors

Reuse `dc_resource_sim/eda/water_models/schedule_decision_compare.py` as the implementation reference, **without editing or importing/running it as a module** (the original performs work at import). The new script should read the **same ESIF hourly parquet** already used there and call the same `direct_evap` function (Step 20). Keep:

- **Day:** July 24, 2023, 00:00–23:00 **UTC**; require exactly 24 consecutive, unique, valid weather/IT hours, no missing or infeasible conditions.
- **Hourly baseline:** 1,000 kWh IT per 1-hour interval (24,000 kWh/day); fixed (nonflexible) share = 80%; flexible arrivals = 200 kWh/hour; IT capacity = 1,250 kW; all flexible work completed by hour 23; no early processing. Preserve Step 30's cumulative-arrival constraints.
- **Equipment:** W2-Air as in Step 20; target supply 25°C, effectiveness limit 0.8, server temperature rise 15°C; treatment recovery `eta = 0.8`, without storage or other feed uses.
- **Models:** W2 hourly intensity `w2[t] = direct_evap(Tdb[t], RH[t]/100, it_kw=1000)['evaporation_lph']/1000` (L/kWh IT) when in wet mode, otherwise 0; frozen C1 `c1[t] = 0.09788 * max(Tdb[t]-25, 0)` (L/kWh IT). Retain the existing dry-mode and feasibility rules, including the `Tdb <= 25°C` handling.

Read **`dc_resource_sim/eda/water_models/schedule_decision_summary.csv`** for **rounded-output QC anchors** (not exact capacities):

| Policy, Step 30 | W2 evaporation, L/day | W2 peak treatment feed, L/h |
|---|---:|---:|
| No shifting | 8,680.498 | 1,353.818 |
| W2-optimal without feed limit | 8,458.781 | 1,451.983 |
| C1-optimal without feed limit | 8,458.781 | 1,451.983 |

**Important:** saved values were rounded to 0.001. Reconstruct baseline and unconstrained W2 optimum **in full precision** from the original weather/model/LP, and assert they agree with saved anchors to **0.01 L or L/h**. Use these *full-precision* peak rates to set capacities; otherwise rounding 1,353.818 or 1,451.983 downward could cause spurious infeasibility.

## 2. Only one new constraint

Let `y[t]` be flexible IT energy served in hour `t` (kWh), with `x[t] = fixed[t] + y[t]`. For model `m` in `{C1, W2}` and a process-feed capacity `F_cap` (L/h), impose:

$$
\frac{w^m_t x_t}{\eta} \le F_{cap} \qquad \text{for every }t,\quad \Delta t=1\ \mathrm{h}.
$$

This is **linear** under our frozen equipment assumptions: W2 and C1 both give evaporation proportional to IT load at fixed outdoor conditions. For the LP in `y`, append one inequality per hour:

$$
 w^m_t y_t\le \eta F_{cap}-w^m_t\,fixed_t.
$$

Keep **all** original Step 30 workload constraints unchanged, including `sum(y) = 4,800 kWh`, `cumsum(y) <= cumsum(arrivals)`, `0 <= y <= it_cap-fixed`, and total `sum(x) = 24,000 kWh`. The objective is still `min sum_t(w^m_t * y_t)` (the fixed-load term is constant).

**Critical fairness rule:** Each model uses **its own water intensities in both objective and cap constraint**. Then evaluate *every* resulting schedule ex post with the same W2 physical-reference intensities. Never quietly impose the W2 cap inside the C1 optimization: that would give C1 information it does not have.

## 3. Three predeclared scenarios, no sweep

Compute the W2-evaluated full-precision no-shift peak `F_base` and unrestricted W2-optimal peak `F_opt` from Step 30. Require `F_opt > F_base` for this case.

| Scenario | Feed limit `F_cap` | Intended question |
|---|---|---|
| **A — Existing-peak cap** | `F_base` (~1,353.8 L/h) | Is *any* evaporation saving achievable without raising the peak above the baseline? |
| **B — Intermediate cap** | `(F_base + F_opt)/2` (~1,402.9 L/h) | What additional saving, if any, does half the extra capacity provide? |
| **C — Step 30 peak** | `F_opt` (~1,452.0 L/h) | Does the constraint recover the unconstrained Step 30 W2 optimum? |

For **each cap**, run **two** LPs: C1-optimal and W2-optimal (six solves total), plus the already verified no-shift baseline for comparison. Do not invent capacity levels from actual municipal or treatment infrastructure: these are **illustrative hourly process-feed limits** only.

## 4. Output and interpretation

Create **one new script**:

`dc_resource_sim/eda/water_models/peak_feed_capacity_compare.py`

Produce **one CSV** in the same folder: `peak_feed_capacity_summary.csv` (six solver-policy rows). Suggested columns:

`scenario, model, cap_lph, solver_status, w2_evaporation_l, saving_vs_no_shift_l, realized_w2_peak_feed_lph, peak_violation_lph, w2_feasible, conditional_regret_l`

For each schedule:

- **W2-evaluated daily evaporation** = `dot(w2, x)` (L/day), and **saving** = `W2(no_shift) - W2(x)` (L/day).
- **Actual modeled peak feed** = `max(w2*x)/eta` (L/h); **violation** = `max(0, actual_peak - F_cap)` (L/h).
- **C1 conditional regret** = `W2_evap(C1_schedule) - W2_evap(W2_cap-optimal_schedule)` **only if the C1 schedule is feasible under the W2 cap**. Otherwise put `N/A` for regret and report the capacity violation. The W2-cap-optimal schedule is the common feasible reference **within each scenario**, not the unconstrained Step 30 optimum.
- If C1's own LP is infeasible, record `model_infeasible` and `N/A` downstream values; this is informative and must not be hidden by switching weather days or relaxing constraints.
- Do not claim that the C1 and W2 schedules are *identical* merely because objective values agree. Exact schedules can differ under ties.

**Optional one plot, only if it adds information:** x = assumed feed cap (L/h), y = W2-evaluated evaporation saved vs no shift (L/day), separate W2-optimal and C1-scheduled points, explicitly mark any W2-infeasible C1 point rather than presenting it as a valid saving. A 6-row table is enough if all points coincide. No extra dashboard or figures.

## 5. Nonnegotiable checks

1. The unbounded W2 and baseline replicates match the **saved Step 30** evaporation and peak anchors at the stated tolerance. Don't refit C1 or modify Step 30 files.
2. Every successful LP has **24,000 kWh IT**, satisfies flexible-arrival/completion constraints and the **1,250 kW** IT cap.
3. W2-optimal schedules obey `W2_peak <= F_cap + tolerance` (suggest `0.01 L/h` to absorb floating-point solver noise); the baseline is W2-feasible at **all three** caps.
4. The W2-cap-optimal daily evaporation must be **nonincreasing** as capacity increases; scenario C reproduces Step 30's W2 optimum within `0.01 L`. Do **not** require strict improvements: a capacity limit can be nonbinding.
5. Re-evaluate C1 under W2 independently and disclose positive cap violations. **Do not interpret a lower W2 evaporation from an infeasible C1 schedule as better optimization.**
6. Every reported `feed` quantity is **hypothetical treatment feed**, not facility-wide withdrawal, municipal delivery, or groundwater extraction. Daily volume (L/day) and hourly peak (L/h) stay separate.

## 6. Stop and record the scientific result

Add a **short** `step31_results.md` beside the new CSV (or console summary if the established local convention is only CSV), answering exactly:

1. *How much of Step 30's 221.7 L/day modeled saving survives when peak feed cannot exceed the no-shift peak?*
2. *How much additional evaporation saving, if any, becomes possible as peak capacity increases?*
3. *Does C1 continue to deliver a W2-feasible, near-optimal schedule under tight capacity?*

**Stop after one script, one CSV and a short conclusion** (plus at most one optional plot). Do not introduce electricity prices, combined direct/grid-water objectives, new cooling controls, groundwater planning, or new locations here. A flat capacity–saving relationship is a valid finding; it means **this particular limit is not decision-relevant under this setup**, not that water infrastructure limits never matter.

**Next decision gate:** If cap constraints materially change feasible scheduling or C1 decision quality, this is a strong basis for adding capacity-aware water demand to the planning model. Otherwise, the more informative next experiment may be a single electricity-cost versus direct-water trade-off, **after** Step 31's numerical outcome is checked.

---

Discussion (for reference):

## Step 31 — Does limiting peak water demand change the optimal scheduling decision?

I recommend prioritizing water-supply capacity over electricity-cost trade-offs for Step 31. It is the more direct and informative extension of what we just established.

### 1. Why this is the highest-value next question

Step 30 produced an important result:

| Quantity                  | No shifting | Water-optimal |
| ------------------------- | ----------- | ------------- |
| Daily modeled evaporation | 8,680.5 L   | 8,458.8 L     |
| Peak treatment feed       | 1,353.8 L/h | 1,452.0 L/h   |

Optimizing daily water reduced evaporation by 2.6%, but increased peak process-water supply requirements by 7.3%.

This raises a fundamental planning question:

> Can we achieve the modeled water savings without increasing the peak capacity required from the water-supply infrastructure?

This is more immediately valuable than adding electricity prices because it tests whether the previously optimal solution remains desirable under a physical resource constraint.

It also moves us closer to infrastructure planning, although treatment-feed capacity is not equivalent to groundwater extraction capacity.

### 2. The proposed experiment

Keep the same July 24, 2023 weather, workload, C1/W2 models, and Step 30 optimization.

Add only one constraint:

\\[ \boxed{\frac{w_t x_t}{\eta}\leq F\_{\max}\quad\forall t} \\]

where \\(F\_{\max}\\) is the assumed maximum hourly treatment-feed rate.

Test three capacity limits:

| Scenario                   | Maximum feed | Purpose                                        |
| -------------------------- | ------------ | ---------------------------------------------- |
| Existing baseline capacity | 1,353.8 L/h  | Can we save water without increasing capacity? |
| Intermediate capacity      | 1,402.9 L/h  | How much value comes from additional capacity? |
| Unconstrained-optimum peak | 1,452.0 L/h  | Recover the Step 30 optimum                    |

For each limit, optimize using C1 and W2 independently, then evaluate both solutions under W2.

### 3. What we should measure

Only four outcomes are necessary:

1. Daily evaporation saved relative to no shifting.
2. Peak treatment feed and whether the assumed constraint is satisfied.
3. C1 decision regret relative to the W2 optimum, when the C1 solution is feasible under W2.
4. Capacity value: How much additional modeled water saving becomes possible when the feed limit increases?

The critical possibility is that C1's excellent prediction accuracy may no longer guarantee an acceptable decision when a tight physical constraint is introduced.

If C1 violates the W2-evaluated feed limit, report the violation explicitly rather than assigning an ordinary optimality regret.

### 4. Why not electricity cost yet?

I would rank the immediate research directions as follows:

| Direction                                         | Priority | Reason                                                                       |
| ------------------------------------------------- | -------- | ---------------------------------------------------------------------------- |
| Peak-water capacity constraint                    | Highest  | Directly tests Step 30's unresolved operational trade-off                    |
| Electricity-cost versus onsite-water optimization | Next     | Important, but adds price assumptions and another objective                  |
| Groundwater-network constraints                   | Later    | Central research goal, but requires an explicit source-to-withdrawal mapping |

The peak-capacity experiment provides a clean intermediate result between predicting water demand and planning infrastructure.

### 5. Scope and stopping rule

Use one new script, the same 24-hour scenario, two existing water models, and three capacity limits.

Produce one small numerical table and, only if informative, a single figure showing daily evaporation versus peak feed capacity.

No new calibration, cooling physics, weather datasets, or full network optimization.

The result remains conditional on hypothetical equipment, workload flexibility, and treatment recovery.

## Final recommendation

Step 31 should test whether water-aware optimization remains beneficial and feasible when peak supply capacity is constrained.

This would extend our central research result:

- Step 29: Does a simpler model predict water accurately relative to W2?
- Step 30: Does it preserve the optimal scheduling decision?
- Step 31: Does it preserve that decision when water infrastructure capacity matters?

If these results are clear, the following step can add electricity costs and evaluate the economic value of water flexibility.

This is a small, scientifically meaningful progression toward the final infrastructure-planning problem.

---

## Step 31 — Peak water-supply capacity and scheduling

I've prepared the complete implementation plan, based on the verified Step 30 code and results.

Download Step 31 — Peak Water Capacity Experiment (.md)

Save it as `dc_resource_sim/context/step31.md`.

### 1. Fundamental question

Can workload scheduling reduce daily water consumption without increasing the peak capacity required from the cooling-water supply system?

And, importantly, does C1 remain decision-sufficient when this physical constraint becomes binding?

### 2. Exact experiment

Keep Step 30's weather, workload, optimization constraints, and C1/W2 models unchanged.

Add only:

\\[ \boxed{\frac{w_t x_t}{\eta}\leq F\_{\max}} \\]

Test three assumed peak treatment-feed limits:

| Scenario | Limit       | Purpose                       |
| -------- | ----------- | ----------------------------- |
| A        | 1,353.8 L/h | Existing baseline peak        |
| B        | 1,402.9 L/h | Intermediate capacity         |
| C        | 1,452.0 L/h | Step 30 optimal-schedule peak |

These are displayed approximations; the implementation plan requires calculating the limits at full numerical precision.

For each limit, solve the C1 and W2 optimization problems independently and evaluate both schedules against W2.

### 3. Critical outputs

Only four quantities matter: daily evaporation saved, peak treatment feed, physical constraint violations, and C1's regret relative to the capacity-constrained W2 optimum.

The most important methodological requirement is that a C1-optimal schedule violating the W2-evaluated water limit must be reported as infeasible, not as a better solution.

### 4. Minimal repository changes

Create:

`dc_resource_sim/eda/water_models/peak_feed_capacity_compare.py`

Produce one results CSV and a short interpretation. A single plot is optional if the capacity–water-saving relationship is informative.

No refitting, new datasets, electricity prices, or modifications to previous experiments.

### 5. What makes this valuable?

The experiment distinguishes three possibilities:

- Water savings are achievable without additional peak capacity.
- Water savings require increasing peak supply capacity.
- C1's small prediction errors become consequential when a physical constraint is tight.

Each outcome advances our understanding of when model complexity matters for infrastructure decisions.

Recommendation: Execute this one experiment, verify the physical constraints and model comparisons, and stop. Its results will determine whether capacity-aware water modeling deserves further development before introducing electricity-cost trade-offs.