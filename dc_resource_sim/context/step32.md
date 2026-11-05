# Step 32 — What does water-aware workload scheduling cost?

**Status:** implementation plan. **One new question, one day, three policies, one script, one table.** Do not change Steps 00–31, refit models, or implement a new cooling/power model.

## 1. Question and interpretation

> Under the *same workload, weather, and peak treatment-feed limit*, what is the electricity-cost opportunity cost of reducing **modeled onsite process evaporation** by shifting flexible IT work between hours?

This is a **scheduling trade-off**, *not* the electricity–water trade-off between cooling technologies. All cases use the same hypothetical direct-evaporative equipment and **M0 aggregate facility electricity**; no extra fan, chiller, pump, or water-treatment power may be added to M0. W2 evaporation is not municipal withdrawal or measured total facility consumption.

**What changes from Step 31:** introduce one existing hourly price vector and a cost objective. Hold everything else fixed.

## 2. Frozen 24-hour scenario and source checks

**Weather and W2:** Reuse Step 30–31 code and parameters from `dc_resource_sim/eda/water_models/peak_feed_capacity_compare.py`:

- ESIF observed weather, **2023-07-24, 00:00–23:00 UTC**, loaded from the **same `PARQUET`** path. Require 24 distinct consecutive hourly timestamps, `valid_weather` and `valid_it`, and finite `tdb_c`/`rh_pct`.
- Hypothetical baseline IT load **1,000 kWh each hour**; 80% inflexible (`fixed_t=800`), 20% flexible (`arrivals_t=200`); daily IT energy **24,000 kWh**; flexible work may be **deferred but never served before its arrival**, and must all finish by hour 23; IT capacity **1,250 kW**.
- W2-Air with supply target **25 °C**, max effectiveness **0.8**, server-air rise **15 °C**, and the established dry/wet/feasibility rules. For fixed weather, `w2_t = W2_evaporation_lph(t, 1000 kW)/1000` in **L/kWh IT**; dry hours give `0`, infeasible hours mean **stop**, not zero.
- Illustrative treatment recovery `eta = 0.8` (no storage/other water uses).
- Peak treatment-feed limit **`F_cap = max_t(w2_t * 1000)/eta`**, computed at full precision. This is **Step 31 scenario A, the no-shift peak**, not a measured infrastructure rating. Assert that it agrees with Step 31's `A_existing_peak` row within **0.01 L/h**.

**Electricity:** `P_DC,t = k * P_IT,t`, fixed `k=1.0471`; for one-hour bins, `E_DC,t = k*x_t` kWh. Price-based cost:

$$ C(x)=\sum_{t=0}^{23}p_t\,k\,x_t \quad [\$/\mathrm{day}]. $$

`k` is an existing illustrative constant-PUE coefficient. With fixed daily IT energy, **total modeled facility kWh is constant** across policies; only **when** those kWh are purchased changes cost. This experiment does not resolve cooling electricity as a function of operating mode.

**Price — reuse one file, no download:** `dc_resource_sim/runs/price_24h.csv` with `timestamp_utc,price_usd_per_kwh` from **2023-07-01 UTC** (existing earlier MISO-price case). Require exactly 24 unique consecutive UTC hours, 00–23, finite prices, correct units; do not interpolate or reorder beyond sorting the timestamps. Pair **hour-of-day index 0–23** with the July 24 ESIF weather hours. **This is an explicitly constructed cross-day, cross-region price–weather scenario**, NOT synchronized ESIF electricity prices or a reconstruction of actual July 24 operations. Verify the source provenance in the existing price-step note before describing it more specifically than “existing 2023-07-01 price trace.” If the file is missing or malformed, **stop**; do not invent prices or download replacements.

**Required anchored checks** (rounded values from saved Step 30/31 outputs):

- `W2(no_shift) ≈ 8680.498 L/day`, `peak_feed(no_shift) ≈ 1353.818 L/h`.
- Re-solve the **W2 water-only optimum subject to this same cap**; it must match Step 31's scenario A `W2` evaporation **≈ 8460.702 L/day** (within `0.01 L`).
- Exact values must be recomputed from the original W2 intensities and LP; never use rounded CSV values as optimization inputs.

## 3. One linear program, three policy choices

For each hour `t`, decision `y_t` is **flexible IT energy served**, `x_t=800+y_t`. Retain all Step 31 constraints **identically for every policy**:

$$
0\le y_t\le 450, \quad \sum_t y_t=4800,\quad
\sum_{\tau=0}^t y_\tau\le 200(t+1),\quad
\frac{w^{W2}_t(800+y_t)}{0.8}\le F_{cap}.
$$

The last constraint uses the *same W2 reference intensities for all three policies*. We are isolating the **cost–water objective**, not testing C1's cap prediction again (already addressed in Step 31).

Solve with SciPy `linprog(method="highs")`:

| Policy | Minimize | Additional constraint |
|---|---|---|
| **A. Cost-optimal** | `sum(p_t*k*x_t)` | None |
| **B. Water-optimal** | `sum(w2_t*x_t)` | None |
| **C. Intermediate water budget** | `sum(p_t*k*x_t)` | `sum(w2_t*x_t) <= V_mid` |

Derive the **single** budget after solving A and B:

$$ V_{mid}=\frac{V(x_A)+V(x_B)}{2}. $$

**Important:** the budget is in **L/day of W2 process evaporation**, not treatment feed or groundwater. In the `y`-form LP, the row is `w2 @ y <= V_mid - w2 @ fixed`.

**Essential tie-breaking for a valid cost comparison:** The water-only LP often has many equal-evaporation optima (especially in dry hours), which can have very different electricity costs. Avoid interpreting an arbitrary HiGHS solution as the cost of achieving the maximum water saving. After obtaining the optimal water volume `V_min`, **minimize electricity cost again** with `V(x) <= V_min + 0.001 L`; this is policy B (lowest-cost near-water-optimal schedule). Likewise, if there are cost-optimal ties, select policy A by **minimizing water** with `C(x) <= C_min + $0.001`. Check the chosen schedules remain within `0.01 L` / `$0.01` of the primary optima. These secondary LPs are numerical tie-breakers, **not new scenarios or models**. The midpoint policy C is then computed against the selected A and B, as defined above. This prevents spurious apparent trade-offs caused by arbitrary schedule ties.

**Degenerate case:** If `V(x_A)-V(x_B) <= 0.01 L/day`, there is no measurable water-vs-cost frontier in this scenario. Report **no trade-off** and **skip** the redundant budget optimization C; do **not** change the price trace, day, load, or constraints to manufacture a conflict.

## 4. What to save and how to interpret

Create exactly **one new script**:

`dc_resource_sim/eda/water_models/cost_vs_evaporation.py`

Follow Step 31's validated data-loader and LP setup without importing `peak_feed_capacity_compare.py` as a module (it runs work at import). Reuse the existing `direct_evap` import pattern; don't edit prior scripts.

Save **one CSV** in the same folder: `cost_evaporation_summary.csv` with rows `no_shift`, `cost_optimal`, `water_optimal`, and `budget_midpoint` (omit the last row only if degenerate). Suggested columns:

`policy, it_energy_kwh, facility_energy_kwh, electricity_cost_usd, w2_evaporation_l, saving_vs_no_shift_l, water_saving_vs_cost_opt_l, extra_cost_vs_cost_opt_usd, peak_w2_feed_lph, feed_cap_lph, cap_violation_lph, solver_status`

Also print a **short conclusion** (or save `step32_results.md`, ≤ 12 lines) answering:

1. **Does minimizing electricity cost increase W2 evaporation compared with water-optimal scheduling?** Give the difference **L/day** and as % of cost-optimal evaporation.
2. **What extra electricity expenditure** ($/day and %) is required to reach the minimum feasible evaporation? Compare to the **cost-optimal**, *not* necessarily to no shift.
3. **Does the midpoint budget capture a substantial fraction of water saving** at a small fraction of the maximum extra cost? Report the actual numbers; no presumption of a particular Pareto shape.

Optional, **only if nondegenerate**: one simple scatter/line plot, x = `W2 evaporation (L/day)` and y = `electricity cost ($/day)`, showing only A, C, B and a light marker for no-shift. **Three optimized points do not establish a smooth Pareto frontier.** A table alone is acceptable.

## 5. Verification requirements (must pass)

1. Price file 24-hour identity/units and ESIF weather 24-hour support validated; explicitly mark the **noncoincident dates and regions** in the output.
2. All schedules obey `sum(x)=24,000 kWh`, `max(x)<=1250 kW`, flexible-arrival constraints, and `max(w2*x)/eta <= F_cap + 0.01 L/h`; no infeasible weather hour is converted to 0.
3. Constant facility energy `k*24000 = 25,130.4 kWh/day` in *every* row; no added cooling electricity.
4. Reproduce Step 30 baseline and Step 31 cap-A water optimum within `0.01 L` as above.
5. With the same constraints, **water-optimal minimizes W2 evaporation**, **cost-optimal minimizes electricity cost**: `V_B <= V_C <= V_A` and `C_A <= C_C <= C_B` to numerical tolerance (unless C is skipped).
6. If C exists, `V_C <= V_mid + 0.01 L`; all cost and water quantities are re-evaluated from the *same* price and W2 vectors, regardless of policy.
7. If differences are very small or zero, report that result faithfully. Do not imply a water saving is measured, or infer water-pricing, groundwater, cooling-mode energy penalties, or externality reductions.

## 6. Stopping rule and decision gate

**Stop after one new script, one table and ≤12 lines of findings** (plus at most one optional plot). No C1 recalibration, multi-day sweep, flexible-fraction sweep, price download, wet/dry cooling decision, or region-network model in Step 32.

- **If a meaningful cost–evaporation conflict appears:** the next smallest step can test its robustness to an *actually co-timed* price trace or a small, predeclared flexibility change.
- **If no conflict appears:** that's still a useful negative control; do not invent one. Before expanding the model, prioritize matched price–weather conditions or an explicit physical cooling-mode comparison.

**Research boundary:** The findings show the opportunity cost of *temporally reallocating a fixed amount of IT energy*. They do not measure the extra electricity consumption required to operate a water-saving cooling system. Source-specific water withdrawal, groundwater depletion, and network planning remain future layers.

---

Discussion context (for reference):

## Step 32 — Electricity cost versus onsite cooling-water demand

I prepared the implementation plan using the verified Step 30–31 experiments. It introduces one new element: hourly electricity prices, while preserving the existing physical models, scheduling constraints, and peak-feed limit.

Download Step 32 — Complete Local-Agent Plan (.md)

Save it as `dc_resource_sim/context/step32.md`.

### 1. Fundamental research question

How much additional electricity expenditure is required to reduce modeled onsite evaporation through workload scheduling?

This tests the economic value of water-aware scheduling, not the electricity consumption of different cooling technologies.

### 2. Exactly three optimization cases

| Case | Optimization                                                | What we learn                                       |
| ---- | ----------------------------------------------------------- | --------------------------------------------------- |
| A    | Minimize electricity cost                                   | Water consequences of cost-optimal scheduling       |
| B    | Minimize evaporation                                        | Maximum achievable water saving and its cost        |
| C    | Minimize electricity cost with an intermediate water budget | Whether most savings can be obtained at modest cost |

All three share the same 24-hour workload, weather, W2-Air model, and Step 31 baseline peak-feed constraint.

The plan also includes a necessary tie-breaking rule: among equally water-efficient schedules, choose the least expensive. Otherwise, solver ties could create a misleading electricity–water trade-off.

### 3. Important data limitation

The existing price trace is dated July 1, 2023, whereas our verified ESIF weather scenario is July 24, 2023.

To minimize changes, the plan uses their hourly profiles as an explicitly constructed price–weather scenario. The result will demonstrate the conditional trade-off, not actual synchronized facility operating economics.

### 4. Minimal implementation

Create only:

`dc_resource_sim/eda/water_models/cost_vs_evaporation.py`

Deliver one summary CSV and a short results note. Add one simple plot only if a meaningful trade-off emerges.

The plan specifies the equations, source files, model parameters, constraints, numerical tolerances, validation checks, and stopping conditions.

### 5. What would make this experiment valuable?

Two possible outcomes are equally informative:

- Meaningful conflict: Water-aware scheduling increases electricity expenditure. Quantify the cost per additional liter of modeled evaporation avoided.
- Little or no conflict: The two objectives are largely aligned under this scenario, so extra optimization complexity offers little demonstrated value.

My recommendation: Execute Step 32 exactly as specified, without adding other models, sensitivity analyses, or datasets. This is the smallest useful advance from water-only scheduling toward coupled electricity–water optimization.