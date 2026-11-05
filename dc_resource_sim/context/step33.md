# Step 33 — Is Step 32's cost–water alignment robust to matched hourly conditions?

**Status:** implementation specification for the local agent. **One new script; three preselected 2023 days from one existing regional dataset; one CSV and one short results note. No refitting, no new data downloads, no new models.**

## 1. Single research question

Step 32 found that electricity-cost minimization already captured **96.6%** of the maximum modeled evaporation saving in **one constructed cross-day, cross-region** price–weather pairing.

> **Does this near-alignment persist when hourly electricity prices and weather come from the same region and date, under the identical workload, electricity and water models?**

Assess **whether the objective conflict changes across a dry day, a representative wet day and a high-evaporation day**. A negative or opposite result is just as valuable as confirming Step 32. This remains hypothetical facility operation: neither facility water consumption nor utility electricity bills are measured.

## 2. Inputs: preflight before experimentation

**Preferred existing source:** repository `data/frozen/signals_2023_v1`, **Springfield, Illinois weather + MISO Illinois regional price signal** (one region only). This location and directory were identified in the previous project data inventory, **but their exact files, field names, units, timestamps and provenance have not been verified in this conversation**.

The agent must **inspect the local folder and its source documentation first**, then hard-code an explicit input path and field mapping in the new script. Requirements:

- The weather is localized to Springfield/central Illinois and provides observed (or clearly labeled source-derived) hourly **dry-bulb temperature in °C** and **relative humidity in %**. Never substitute a different site's weather or infer RH silently.
- The price is the documented Illinois/MISO **wholesale price proxy**, with known market product, location/hub, and original units ($/MWh or $/kWh). Convert once to **$/kWh**. Do not call it an actual data-center retail tariff.
- Weather and price must map to **the same UTC hour of 2023**. Parse source time zones explicitly, including daylight-saving conversion. Do not assume naive timestamps are UTC without documentation. Join on timestamp, never row number or hour-of-day across different dates.
- Inspect raw coverage first: the earlier inventory mentioned **8,904** signal rows, whereas 2023 contains **8,760 UTC hours**. Print raw date range, post-2023 count, duplicates, invalid/missing rows, and complete 24-hour days. Extra adjacent-year rows may be filtered by timestamp; **duplicate 2023 UTC hours are an error**. Never fill absent hours.
- Validate units/ranges and numeric finiteness; negative wholesale prices, if present, are legitimate and should **not** be clipped. Flag any source whose price or weather geography/time cannot be established.

**Hard stop:** If there is no documented, genuinely same-date and reasonable same-region price–weather pairing in the existing signals, **stop Step 33 with a short data-availability note**. Do not fabricate a pairing, download alternatives, silently reuse Step 32's mismatched data, or introduce a second scenario family. Ask for a separate data-preparation decision later.

## 3. Select exactly three days *before seeing optimization results*

First identify eligible UTC dates with **24 unique consecutive hours**, valid price, `Tdb` and RH, and **all 24 W2-Air hours feasible** under the unchanged cooling assumptions. Compute W2 **baseline** evaporation (1,000 kW every hour) for each eligible day using the existing `direct_evap` routine (not C1). Select deterministically, independent of price and LP outcome:

1. **Dry control:** earliest eligible 2023 date with `V_base = 0 L/day`.
2. **Typical wet:** the median eligible date among `V_base > 0`, ranked by baseline modeled evaporation; break ties by earlier UTC date.
3. **High wet:** eligible date with the **largest** baseline modeled evaporation; ties go to earlier UTC date.

Require these to be **three distinct dates**; otherwise stop with eligibility counts instead of substituting arbitrary dates. Print the selected dates, wet-hour counts, baseline modeled evaporation, mean/max temperature, and the number of incomplete/invalid/infeasible days excluded. This is a **small targeted robustness check, not a representative random sample**. The day selection uses weather and the W2 baseline, not electricity prices or realized optimization benefits.

An infeasible cooling hour means *the assumed equipment cannot maintain the target*; do not convert it to zero evaporation. Exclude such days from this fixed-mode experiment and explicitly report how many were excluded.

## 4. Keep the Step 32 optimization **identical** for every selected day

Reuse the LP formulation and tie-breaking from `dc_resource_sim/eda/water_models/cost_vs_evaporation.py` (read it locally; **do not modify or import it if it runs on import**). Only the hourly price/weather vectors change.

- Horizon: **24 one-hour UTC slots**; synthetic IT demand `x_base[t] = 1000 kWh` each hour.
- Workload: `fixed[t]=800 kWh`, flexible arrivals `a[t]=200 kWh`, flexible served `y[t]>=0`, `x[t]=800+y[t]`; `sum(y)=4800 kWh`, `cumsum(y)<=cumsum(a)`, `0<=y[t]<=450 kWh`, completion by hour 23; IT peak <=1,250 kW.
- M0 facility electricity: `E_DC[t]=1.0471*x[t]` kWh; **no extra cooling or water-treatment electricity**. For each policy daily facility energy must equal **25,130.4 kWh**.
- W2-Air: same 25°C supply target, 0.8 max effectiveness, 15°C server-air rise; `w[t]=W2_evap_lph(t,1000 kW)/1000` in **L/kWh IT**. Modeled process evaporation `V(x)=sum(w[t]*x[t])`, **not measured facility consumption**.
- Treatment recovery `eta=0.8`; for comparability with Step 32 use **each day's W2 no-shift peak** as that day's hypothetical feed cap:
  `F_cap(day)=max_t(w[t]*1000)/eta` in **L/h**.
  Add `w[t]*(800+y[t])/eta <= F_cap(day)` hourly. A different cap value on different days preserves the **no-expansion relative rule**, not a single fixed installed capacity across days.
- Electricity cost: `C(x)=sum(price_usd_per_kwh[t]*1.0471*x[t])` in **$/day**. This values shifted purchases at regional wholesale prices; it does **not** represent facility electricity tariffs.

**Only two optimized policies**, plus no-shift reference, for each of the three selected days:

- **Cost-optimal A:** minimize `C(x)`, then among schedules within **$0.001** of minimum cost, minimize `V(x)`.
- **Water-optimal B:** minimize `V(x)`, then among schedules within **0.001 L** of minimum evaporation, minimize `C(x)`.

Use `scipy.optimize.linprog(method="highs")`; do not add the Step 32 midpoint water-budget policy or any flexibility/price sweep. For dry-control days with `w[:] == 0`, B is the cost-optimal schedule by definition (water optimum is tied everywhere); mark water-trade-off metrics **N/A**. If a model is infeasible or a solve fails, disclose rather than changing the date or relaxing constraints.

## 5. Outputs: one table, no plot needed

Create **one new script**:

`dc_resource_sim/eda/water_models/matched_price_weather_compare.py`

Save **one CSV**:

`dc_resource_sim/eda/water_models/matched_price_weather_summary.csv`

Expected **nine policy rows** (3 dates × {no_shift, cost_optimal, water_optimal}); recommended fields:

`scenario, date_utc, policy, weather_source, price_source, valid_hours, wet_hours, baseline_evap_l, feed_cap_lph, it_energy_kwh, facility_energy_kwh, cost_usd_day, w2_evap_l_day, peak_feed_lph, solver_status`

From the same values print **one small day-level comparison table**, with:

- **Achievable water saving** `S_max = V(no_shift) - V(water_optimal)` (L/day).
- **Water saving obtained by cost-only scheduling** `S_cost = V(no_shift) - V(cost_optimal)` (L/day).
- **Share captured** `S_cost / S_max` (may be **negative** if cost optimization increases evaporation; do not clamp to [0,1]). Show **N/A when `S_max <= 1 L`**.
- **Remaining water gap** `V(cost_optimal) - V(water_optimal)` (L/day).
- **Extra cost** `C(water_optimal) - C(cost_optimal)` ($/day).
- **Incremental scheduling cost** (extra $ / gap L), **N/A if gap <= 1 L**; this is **not the price or societal value of water**.
- **Optional explanatory diagnostic:** within-day Pearson correlation of hourly price and `w[t]` (N/A if either has zero variance); descriptive only, not a causal explanation or substitute for the LP.

Write **one short** `step33_results.md` (≤ 15 lines) giving: source/time validity, selected dates and why, comparison with Step 32's single constructed scenario, and the main conclusion (aligned, conflicting, or mixed), with limitations. **No new plot by default.**

## 6. Nonnegotiable verification

1. Every chosen date has 24 same-UTC-hour price/weather pairs. No shifted dates, duplicated hours, invented units, silent missing-hour interpolation, or W2 infeasibility.
2. Every schedule: `sum(x)=24000 kWh IT`, `sum(E_DC)=25130.4 kWh`, 1,250 kW IT cap, workload arrivals/deadline, and **W2 peak feed <= that day's baseline cap +0.01 L/h**.
3. Each day: `C(cost_optimal)<=C(water_optimal)+0.01 $`; `V(water_optimal)<=V(cost_optimal)+0.01 L`; baseline is feasible. Secondary tie-breaks preserve primary objectives to the documented tolerances.
4. Dry day has zero W2 evaporation in every feasible schedule; no division by zero or misleading percentages.
5. No presumption that pricing and evaporation align. **Report the direction and magnitude of conflict even when cost-optimal scheduling increases water relative to no shift.**
6. Source and model boundaries must be stated: **co-timed regional proxy prices/weather, not a measured facility; W2 simulated process evaporation; M0 fixed-energy facility cost; feed is hypothetical, not municipal withdrawal or groundwater extraction.**

## 7. Stop and decision gate

**Stop after the one script, one CSV, and one short note.** No C1 comparisons (Steps 29–31 answered that), no price downloading, additional sites, new cooling technology, ML fitting, groundwater modeling, or expansion to weekly optimization.

If cost-only scheduling captures most W2 saving on both wet days, that is **limited evidence of alignment for the selected matched conditions**. If the outcomes are mixed or opposing, Step 32's apparent alignment was scenario-sensitive. Neither result is a general rule from three selected days.

**Following step, only if justified:** target the **physical electricity–water interaction of an actual alternative cooling mode**, because the present scheduling framework does not model electricity demand changing with cooling technology. Alternatively, if the real goal is regional planning, shift toward source-specific water accounting rather than repeatedly varying operating schedules.


----

Discussion context (just for reference):

## Step 33 — Robustness of electricity-cost versus water-saving decisions

I've prepared the detailed implementation plan for the local agent.

Download Step 33 — Complete Implementation Plan (.md)

Save it as `dc_resource_sim/context/step33.md`.

### 1. Fundamental question

Does the alignment between electricity-cost minimization and water-saving optimization persist when electricity prices and weather are matched in time and region?

Step 32 showed that cost minimization captured 96.6% of the achievable modeled evaporation saving. However, its price and weather profiles came from different dates and regions.

Step 33 tests whether that conclusion is sensitive to the input conditions.

### 2. Exact experiment

Reuse the existing Springfield, Illinois/MISO regional signals, subject to verifying their availability, timestamps, and provenance.

Select three 2023 days deterministically, before evaluating optimization outcomes.

| Scenario             | Purpose                                         |
| -------------------- | ----------------------------------------------- |
| Dry day              | Negative control: no modeled evaporative demand |
| Typical wet day      | Test ordinary evaporative-cooling conditions    |
| High-evaporation day | Test conditions with greater water demand       |

For each day, compare only three schedules: no shifting, cost-optimal, and water-optimal.

Everything else remains unchanged: M0 electricity, W2-Air evaporation, 20% workload flexibility, hourly capacity, completion constraints, and the existing no-peak-expansion rule.

### 3. Most important outputs

| Metric                                  | What it tells us                                   |
| --------------------------------------- | -------------------------------------------------- |
| Achievable water saving                 | How much scheduling can reduce modeled evaporation |
| Saving captured by cost optimization    | Whether electricity and water objectives align     |
| Additional cost for minimum evaporation | The economic consequence of water-aware scheduling |
| Remaining water gap                     | How much water cost-only scheduling leaves unsaved |

The plan includes exact equations, day-selection rules, tie-breaking, units, input-validation requirements, and stopping conditions.

### 4. Minimal implementation

Create one script:

`dc_resource_sim/eda/water_models/matched_price_weather_compare.py`

Generate one results CSV and one short Markdown interpretation. No plot is required.

Important safeguard: The existing regional signal files must be verified locally. If appropriately matched price and weather data are unavailable, the agent should report that limitation rather than construct another mismatched scenario.

### What makes Step 33 valuable?

It distinguishes two possibilities:

- Consistent alignment: Cost optimization often delivers most modeled water savings under the selected matched conditions.
- Scenario-dependent alignment: Electricity and water objectives sometimes conflict, showing why water-aware scheduling may matter.

Either result advances our understanding. Three selected days will not establish general robustness, but they provide a much stronger test than the single constructed pairing in Step 32.

My recommendation: Execute Step 33 exactly within this scope. Afterward, prioritize advancing the physical electricity–water coupling or regional resource-planning model rather than continuing indefinitely with scheduling sensitivities.