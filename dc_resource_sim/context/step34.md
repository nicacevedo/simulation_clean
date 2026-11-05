# Step 34 — A consistent cooling electricity–heat–water balance

**Status:** implementation plan for the local agent. **One previously used weather day, one fixed IT load, two inlet-conditioning modes, one new script.** Do not rerun or modify Steps 00–33. This is a controlled *physical counterfactual*, not a scheduling or cost optimization.

## 1. Research question and deliverable

> **For the same IT heat load, outdoor weather, airflow, and supply-air target, how much additional cooling electricity is required to avoid water evaporation?**

The first aim is to construct an internally consistent **electricity–heat–water accounting boundary**. The second is to quantify the resulting *conditional* electricity-versus-process-evaporation trade-off. This is the physical relationship missing from Steps 30–33, which kept facility electricity at M0 irrespective of cooling mode.

**Do not claim** that the result measures an actual data center, ranks real cooling technologies, or establishes groundwater withdrawal. The mechanical-cooling and auxiliary-power inputs below are **explicit illustrative assumptions, not calibrated equipment properties**.

## 2. Freeze the existing inputs

Inspect the actual Step 33 local code/data mapping first: `dc_resource_sim/eda/water_models/matched_price_weather_compare.py`, `data/frozen/signals_2023_v1`, and the existing Step 20 routine `direct_evap` in `src/experiments/w2_air_first.py` (locate it if the precise path differs). **Read/import the existing pure cooling function; do not import any module whose top-level code runs an experiment.**

Use only **2023-06-25, 00:00–23:00 UTC**, the verified Step 33 *high-evaporation* day at **Springfield, Illinois**. Reuse its clean-hour weather requirements, unit conversion, station identification and UTC parsing. Require 24 distinct, complete, valid hourly pairs of **outdoor dry-bulb `Tdb` (°C)** and **RH (%)**. Prices are **not needed**. No new downloads, new sites, or replacement day if verification fails.

Frozen operating inputs:

| Input | Value / rule |
|---|---|
| IT electric load / heat | `P_IT = Q_IT = 1,000 kW` in each hour; 24,000 kWh/day. Neglect stored heat and non-IT heat transfer into the server air. |
| Architecture | **100% outdoor-air, once-through air cooling**. Outdoor air is conditioned *before* servers; server exhaust carries IT heat outdoors. No return-air recirculation or other heat-rejection loop. |
| Supply / server air | `T_supply_max = 25 °C`, `DeltaT_server = 15 °C`; same airflow in both modes. |
| W2-Air equipment | Step 20 defaults, including `max wet-bulb effectiveness = 0.8`, `f_air = 1`; no parameter changes. |
| Water accounting | W2-Air **process evaporation** in L/h. Optional hypothetical treatment feed `evaporation / 0.8`; not withdrawal, pumping rate, or groundwater extraction. |
| Common air movement | `P_common = 20 kW` in **both** modes (illustrative, constant, not calibrated). Assume its electrical losses do not enter the preconditioning/supply-air heat balance. |
| Wet-only auxiliary | `P_wet_aux = 10 kW` **only when evaporation is active** (illustrative pump + extra pressure-loss allowance; not computed from make-up/feed flow). |
| Dry mechanical precooling | Constant **system COP = 3.0** (illustrative): thermal *inlet-air cooling* / mode-specific electrical input; includes all dry-mode refrigeration/condenser auxiliaries beyond `P_common`. No process-water use. |
| Hourly interval | `dt = 1 h`, so average kW over an hour equals kWh for that hour. |

**Preflight anchor:** W2 at 1,000 kW on this day should produce 21 wet hours and **approximately 8,203.3 L/day** evaporation, as reported by Step 33; all 24 hours must be W2-feasible. Check against the saved Step 33 record before proceeding (do not tune parameters to force agreement). Any failure: stop and report the discrepancy.

## 3. Compare only two modes within the **same** air-side system

Both supply the same temperature to servers, with the same IT load and flow. At `Tdb <= 25°C`, **both use dry/free outdoor-air supply**: no water, no mechanical refrigeration, only the common air-movement power.

At `Tdb > 25°C`:

- **Wet inlet conditioning:** apply the existing W2-Air direct evaporative model to cool outside air toward 25°C. Require `mode == wet` and the existing effectiveness/feasibility checks. Water is the returned W2 process evaporation; additional electricity is the assumed `P_wet_aux`.
- **Dry inlet conditioning:** instead cool that **same outside airstream** sensibly to 25°C using a waterless mechanical coil. The air keeps its inlet humidity ratio; no direct evaporation. Supply-air humidity acceptability beyond the existing W2 checks is **not** established for either option. Require outdoor-air dew point `<= 25°C` so that *condensation/dehumidification is not needed*. If this fails, stop with an explicit “dry sensible-only model insufficient” message; do not silently count condensation as zero water or invent a latent-load model.

**Important physical boundary:** The mechanical coil is only cooling **outdoor inlet air from `Tdb` to 25°C**. It is **not cooling the full `1,000 kW` IT heat load**; that heat goes out with the once-through exhaust air. Do not use a whole-facility or recirculating-water chiller formula here.

## 4. Exact per-hour equations

Use the existing W2-Air **dry-air mass-flow and moist-air heat-capacity conventions** wherever provided. If not returned by `direct_evap`, reproduce its frozen Step 20 formula/parameters in the new script (with a short code comment). The same `m_dot_da,t` (kg dry air/s) must apply to wet and dry modes. At the model's precision,

$$ Q_{IT,t} \simeq \dot m_{da,t}\,c_{p,ma,t}\,(15\ ^\circ\mathrm C)=1000\ \mathrm{kW}. $$

`c_p,ma` must use units **kJ/(kg dry air·K)** (or the exact equivalent in the existing model); `m_dot_da * c_p * DeltaT` then returns kW. Do not mix kg/h with kg/s or use a specific heat per kg moist air with a kg dry-air mass flow.

Required sensible **inlet-air precooling**:

$$ Q_{in,t}=\dot m_{da,t}c_{p,ma,t}\,\max(T_{db,t}-25,0)\quad[\mathrm{kW}_{th}]. $$

**Wet:**

$$\begin{aligned}
V_{wet,t}&=V^{W2}_{evap,t}\quad[\mathrm{L/h}],\\
P_{wet,t}&=1000+20+10\,\mathbf{1}_{\{T_{db,t}>25\}}\quad[\mathrm{kW}],\\
F_{wet,t}&=V_{wet,t}/0.8\quad[\mathrm{L/h}]\quad\text{(optional feed proxy).}
\end{aligned}$$

**Dry:**

$$\begin{aligned}
V_{dry,t}&=0\quad[\mathrm{L/h}],\\
P_{mech,t}&=Q_{in,t}/3.0\quad[\mathrm{kW}],\\
P_{dry,t}&=1000+20+P_{mech,t}\quad[\mathrm{kW}].
\end{aligned}$$

These are **modeled IT + selected cooling/air-movement electrical components**, **not** measured full-facility electricity or PUE. Both modes omit the same unspecified non-cooling facility loads. **Never add these components to M0 facility power:** M0 already includes cooling/overhead in an aggregate empirical boundary. Never use a 1-MW condenser/chiller duty in place of `Q_in`.

Heat accounting checks (do not impose false exact equalities):

- **Server heat removal:** `Q_IT ≈ m_dot * cp * 15°C`; IT exhaust transports the 1 MW away in both modes.
- **Wet air conditioning:** approximate latent transfer `Q_lat,t ≈ V_wet,t × 2.45 / 3.6` kW (1 L ≈ 1 kg; 2.45 MJ/kg); this should be *comparable* to `Q_in,t`, subject to moist-air enthalpy/liquid-water approximations. **Report the maximum relative discrepancy in wet hours; investigate any discrepancy exceeding 10%, rather than altering W2.** Do not present `Q_lat` as the heat rejected from IT equipment.
- **Dry condenser heat:** `Q_cond,t = Q_in,t + P_mech,t` kW under the chosen system COP boundary; this heat is released to ambient (not the modeled water supply).

For each mode and the 24 h total, compute `E_mode = sum(P_mode,t * 1 h)`, `E_cooling = E_mode - 24,000 kWh IT`, `V_mode = sum(V_mode,t * 1 h)`, and peak total modeled electrical kW. Compare `DeltaE = E_dry - E_wet` and `DeltaV = V_wet - V_dry`; report `DeltaE/DeltaV` in **kWh per liter avoided** only when `DeltaV > 0`. A positive `DeltaE` means waterless conditioning uses more electricity for this fixed configuration; negative means it uses less. The ratio is a **mode-switch energy trade-off, not a water price**.

**Useful single diagnostic (no sensitivity sweep):** compute the day-level break-even `COP* = sum(Q_in,t) / (10 kW × number_of_wet_hours)` for the assumed wet-only auxiliary (only if wet hours > 0). Show this *as an illustrative threshold* at which the two mode-specific daily electric inputs would tie; do not claim it characterizes real cooling equipment.

## 5. New files and minimal output

Create exactly one script:

`dc_resource_sim/eda/water_models/cooling_mode_energy_water.py`

Output **one hourly CSV**, `cooling_mode_energy_water_hourly.csv` (24 rows), with at least:

`hour_utc,tdb_c,rh_pct,w2_mode,mdot_dry_air_kg_s,q_it_kw,q_inlet_precool_kw,wet_evap_lph,wet_feed_lph,wet_aux_kw,dry_mech_kw,wet_total_kw,dry_total_kw,dry_condenser_heat_kw`

Write a **short** `step34_results.md` (≤ 20 meaningful lines) with one two-row daily summary table (`wet`/`dry`): modeled electricity (kWh), incremental cooling/air movement electricity (kWh), evaporation (L), peak power (kW). Include `DeltaE`, `DeltaV`, `DeltaE/DeltaV`, `COP*`, and the max wet-hour latent-versus-sensible discrepancy. State the architecture, illustrative assumptions, feasibility and water boundary. No new plot unless an unexpected time-dependent reversal makes an hourly figure essential; do not extend the experiment to additional weather days.

## 6. Must-pass checks

1. Exactly 24 valid June 25 Springfield UTC weather hours; same raw data and W2 defaults as Step 33. No invalid/infeasible hours, no condensation under the *dry sensible-only* hypothesis, and the reported Step 33 evaporation anchor matches within sensible stored-output precision.
2. Every hour: identical IT load, supply-air setpoint and airflow; `Q_IT ≈ 1,000 kW` with consistent units. **Do not replace `Q_in` by `Q_IT`**.
3. At `Tdb <= 25°C`: identical wet/dry electricity, zero evaporation, `Q_in = 0`, `P_mech=0` and `P_wet_aux=0`. At `Tdb > 25°C`: W2 wet process is feasible, `Q_in > 0`, and `P_mech >= 0`.
4. `E_wet` and `E_dry` both include exactly **24,000 kWh IT**; difference is entirely the **mode-specific** electrical terms. Both have the same `20 kW` common-air-movement term. No M0/PUE addition or double-counting.
5. Wet process evaporation and optional feed are clearly distinct (`feed=evap/0.8`); dry mode has **zero modeled process evaporation**, not a proven zero facility withdrawal. COP and wet auxiliaries are visibly labeled illustrative.
6. A negative or negligible result is allowed. Do not retune COP, auxiliary power, weather, or modes to force a water–electricity trade-off.

## 7. Stop rule and next research gate

**Stop with one script, one hourly CSV, and one short note.** No LP, electricity prices, C1 refitting, pumps sized from treatment feed, tower/chilled-water architecture, cooling-mode switching optimizer, calibration to M0, groundwater inference, or multi-site expansion.

The key new conclusion should be limited to: **under this one explicit once-through architecture and assumed equipment parameters, how much electricity is exchanged for avoided W2 process evaporation, and whether the heat/electricity/water bookkeeping is coherent.** If the boundary is internally consistent, a later experiment can test a physically richer cooling configuration or source-specific water supply. If not, repair the boundary *before* expanding the optimization model.

**Physics reference:** ASHRAE Handbook, Chapter 41, *Evaporative Air-Cooling Equipment* (direct-air evaporative cooling changes supply temperature and humidity by air–water heat/mass transfer): https://handbook.ashrae.org/Handbooks/S24/SI/S24_Ch41/S24_Ch41_si.aspx. Use this for physical interpretation, not as a calibration of the illustrative COP/fan/pump values.

---

Context discussion:

## Step 34 — Physical electricity–water trade-off in cooling

I've prepared the detailed implementation plan for the local agent, keeping the experiment small and focused.

Download Step 34 — Complete Implementation Plan (.md)

Save it as `dc_resource_sim/context/step34.md`.

### 1. Fundamental research question

For the same IT heat load and weather, how much additional cooling electricity is required to avoid onsite water evaporation?

Unlike Steps 32–33, this experiment explicitly models how cooling electricity changes with the cooling method.

### 2. Exact experiment

Use the previously verified Springfield weather day, June 25, 2023, and a constant 1 MW IT load.

Compare two ways of conditioning the same outdoor air:

|                        | Direct evaporative cooling     | Dry mechanical cooling           |
| ---------------------- | ------------------------------ | -------------------------------- |
| Supply temperature     | 25°C target                    | 25°C target                      |
| Water evaporation      | Existing W2-Air model          | Zero modeled process evaporation |
| Additional electricity | Assumed wet-system auxiliaries | Inlet-air cooling duty ÷ COP     |
| IT load and airflow    | Identical                      | Identical                        |

Both use free outdoor-air cooling when the outdoor temperature is at or below 25°C.

The plan explicitly defines the illustrative equipment assumptions and requires verifying feasibility for both modes.

### 3. Critical physical distinction

The mechanical cooling requirement is:

\\[ Q\_{\mathrm{cool}}=\dot m\_{\mathrm{air}}c_p(T\_{\mathrm{out}}-25)\_+ \\]

It is not automatically the full 1 MW of IT heat. In this defined once-through architecture, the IT heat leaves through the exhaust air.

Also, we do not add these cooling components to M0, which already includes aggregate facility overhead.

This makes the accounting boundary much clearer.

### 4. Required outputs

The local agent will generate one script, one 24-hour results CSV, and a short findings note.

The essential results are:

- Electricity required by each cooling mode, in kWh/day.
- W2 process evaporation, in L/day.
- Additional electricity required per liter of evaporation avoided, in kWh/L.
- Verification of the electricity, heat, and water balances.

No new optimization, electricity prices, model fitting, or extensive sensitivity analysis.

### 5. Why this step matters

Steps 30–33 primarily examined when computational work is performed.

Step 34 begins examining how cooling requirements jointly determine electricity and water demand.

The results will remain conditional on an illustrative cooling configuration, but the experiment establishes a foundation for physically meaningful electricity–water comparisons.

My recommendation: Execute Step 34 exactly within this scope. The priority is a correct, transparent physical accounting model—not another optimization result.