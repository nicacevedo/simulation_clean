# Step 35 — Cooling inlet-air feasibility and equipment sensitivity

**Local-agent implementation plan.** One existing 24-hour experiment; one new script; two small CSVs and one short results note. **Do not change or rerun Steps 00–34.** No optimization, additional dates, or equipment models.

## 1. Purpose and decisive question

> **Can the Step 34 wet and dry cooling configurations meet a recommended IT inlet-air environment, and how sensitive is their *conditional* electricity-for-water trade-off to COP and wet auxiliaries?**

Priority is **feasibility before sensitivity**. Step 34 confirmed that W2 can reach the 25°C *temperature target*, but did not test **humidity at the server inlet**. Its reported outdoor dew point reaches **21°C**; a sensible-only cooling coil preserves dew point, while direct evaporation adds moisture. Therefore, a full-day comparison may fail a recommended humidity screen even if all hours satisfy the W2 temperature/effectiveness test.

Step 35 is **a screen against one published recommended operating envelope**, not certification of specific IT hardware. An inlet-air failure does **not** establish physical impossibility: humidity conditioning, air mixing, and other control methods were excluded from Step 34 and remain unmodeled.

## 2. Freeze input and boundaries

Read **only** the saved Step 34 hourly output:

`dc_resource_sim/eda/water_models/cooling_mode_energy_water_hourly.csv`

Expect exactly 24 distinct UTC hours for **2023-06-25 00:00–23:00 UTC**, Springfield, Illinois. Require the existing columns:

`hour_utc, tdb_c, rh_pct, w2_mode, mdot_dry_air_kg_s, q_it_kw, q_inlet_precool_kw, wet_evap_lph, wet_aux_kw, dry_mech_kw, wet_total_kw, dry_total_kw`.

Use **the existing Step 34 architecture unchanged**: 1,000 kW IT continuously, once-through outdoor air, `DeltaT_server = 15°C`, target **25°C maximum supply**, same airflow in both modes, `20 kW` common fans, no M0/PUE addition. Direct wet conditioning is the existing W2 process; the dry alternative is a **sensible-only** coil, with no dehumidification, no process evaporation, and no additional air treatment. At `Tdb <= 25°C`, both use untreated outdoor air. For `Tdb > 25°C`, both deliver 25°C supply air if their respective Step 34 cooling calculations are valid. **Do not add a 25°C heater or assume a constant 25°C supply in free-cooling hours.**

Validate Step 34 anchors **before** analyzing: 21 wet hours, `sum(wet_evap_lph) ≈ 8203.34 L`, `sum(q_inlet_precool_kw) ≈ 5566.5 kWh_th`, `sum(wet_total_kw) ≈ 24690 kWh`, `sum(dry_total_kw) ≈ 26335.5 kWh`. Use absolute tolerances **0.1 L / 0.1 kWh** for rounded anchors, and validate every hourly value is finite and nonnegative where physically required. If a required field or anchor is wrong, **stop with an explicit error**; do not change Step 34 inputs or tune the model.

## 3. Screening test: supply temperature, humidity and dew point

Use the **ASHRAE 2021 A1–A4 recommended inlet envelope** solely as an explicit screen (not the more permissive *allowable* equipment-class limits):

- Supply dry-bulb **18–27°C**.
- Supply dew point **−9 to 15°C**.
- Supply relative humidity **at most 70%**, with **noncondensing** air. (A tighter 50% RH recommendation can apply with elevated gaseous corrosion risk; do not simulate that case.)

Reference: [ASHRAE Handbook — Data Centers and Telecommunication Facilities, recommended envelope](https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch20/a23_ch20_si.aspx). These are *recommended* conditions, not automatically mandatory or a substitute for hardware/vendor requirements.

Per hour, at `p_atm = 101325 Pa`, reconstruct supply-air conditions from the Step 34 data. Use the following **single consistent** psychrometric approximation (temperatures in °C, vapor pressures in Pa):

```text
p_ws(T)   = 610.94 * exp(17.625*T/(T + 243.04))
p_v,in    = (RH_out_pct/100) * p_ws(Tdb)
w_in      = 0.621945 * p_v,in/(101325 - p_v,in)    # kg water/kg dry air
T_supply  = min(Tdb, 25.0)
w_dry     = w_in
w_wet     = w_in + wet_evap_lph/(3600 * mdot_dry_air_kg_s)
p_v(w)    = 101325*w/(0.621945 + w)
RH_supply = 100 * p_v(w)/p_ws(T_supply)
r         = ln(p_v(w)/610.94)
T_dp      = 243.04*r/(17.625 - r)
```

Assumptions: 1 L evaporated water ≈ 1 kg added to the supply air; W2's process evaporation enters the once-through air stream; 1-hour timestep; dry-air mass-flow denominator in kg/s. This is a reproducible **approximate psychrometric reconstruction**, not new fitted cooling physics.

Check both modes independently. Require `0 <= RH_supply <= 100%` up to a tiny numerical tolerance; if not, flag a **psychrometric/model inconsistency** rather than silently clipping. For each mode/hour report `recommended_pass` and an explicit reason (temperature too low/high, dew point too low/high, RH too high, condensation/inconsistency). W2's existing `mode == wet/dry` feasibility is a **different** condition from this inlet-air screen. For a dry sensible-only mode, no outdoor dew point may exceed the coil's 25°C supply temperature in mechanically cooled hours; Step 34 reported max outdoor dew point 21°C, but verify it from the computed humidity rather than assuming it.

**Do not adjust the wet evaporation rate or the mechanical-coil load to force a pass.** Both modes have no modeled dehumidification and may fail the recommended envelope during the *same* hour.

## 4. Minimal one-at-a-time equipment sensitivity

Use Step 34's **same** 24 hourly heat duties, W2 evaporation, and airflow; change **only** two assumed electrical equipment parameters, with one-factor-at-a-time cases:

| Case | Dry system COP | Wet-only auxiliary when `w2_mode == wet` |
|---|---:|---:|
| COP-low | 2.0 | 10 kW |
| **Baseline — Step 34** | **3.0** | **10 kW** |
| COP-high | 5.0 | 10 kW |
| Wet-aux-low | 3.0 | 5 kW |
| Wet-aux-high | 3.0 | 20 kW |

These values are **illustrative sensitivity bounds, not documented specifications or empirical performance ranges**. Keep them separate; **no 3×3 grid**.

For each case (1-hour intervals), with `I_wet,t = 1` only for Step 34's wet-mode hours:

$$E_{wet}=24(1000+20)+P_{wet,aux}\sum_t I_{wet,t}\quad[\mathrm{kWh}],$$

$$E_{dry}=24(1000+20)+\frac{\sum_t Q_{in,t}}{COP}\quad[\mathrm{kWh}].$$

$$\Delta E=E_{dry}-E_{wet},\qquad \Delta V=\sum_t V_{wet,t},\qquad R=\Delta E/\Delta V\quad[\mathrm{kWh/L}].$$

`R` is **additional electricity per modeled process-liter avoided by the hypothetical dry switch**, not a water price. Record `R` only when `DeltaV > 0`. The per-hour and peak electric loads must remain consistent with those equations. The water volumes and inlet-air pass/fail classifications **must not change** with COP or auxiliary kW under this frozen model.

**Interpretation gate:** if either mode fails the recommended screen in **any** hour, label **all five 24-hour electricity–water comparisons “hypothetical / not a fully recommended-envelope-feasible day.”** Still report their conditional arithmetic, but **do not** claim they are full-day operating choices. Report counts of wet-feasible, dry-feasible, and jointly feasible hours separately. Do **not** drop failing hours and call the remaining subtotal a 24-hour result; do not introduce humidity-control electricity or a hybrid dispatch.

## 5. Deliverables (exactly these files)

Create:

`dc_resource_sim/eda/water_models/cooling_mode_feasibility_sensitivity.py`

Generate:

1. **`cooling_mode_feasibility_hourly.csv`**, 24 rows, at least `hour_utc,tdb_c,rh_pct,w2_mode,t_supply_c,wet_supply_rh_pct,wet_supply_dp_c,wet_recommended_pass,wet_fail_reason,dry_supply_rh_pct,dry_supply_dp_c,dry_recommended_pass,dry_fail_reason`.
2. **`cooling_mode_sensitivity_summary.csv`**, 5 rows, at least `case,cop,wet_aux_kw,wet_electricity_kwh,dry_electricity_kwh,wet_evap_l,delta_e_kwh,delta_e_per_l_kwh_per_l,wet_pass_hours,dry_pass_hours,joint_pass_hours,full_day_recommended_feasible`.
3. **`step35_results.md`**, concise: one short feasibility table (pass counts and dominant failure reasons), one five-row sensitivity table, and **3–5 sentences** answering whether Step 34 can be interpreted as a full-day feasible trade-off and whether the sign/order of the conditional electricity penalty changes across the assumed settings.

No plots, new dependencies, refitting, optimization, additional weather days, README changes, or editing prior Step 34 outputs.

## 6. Must-pass checks and stop rule

1. The saved Step 34 24-hour anchors match, with exact same hourly input rows and modes; no additional cooling model or price input.
2. `w_wet >= w_in` (within numerical tolerance), `w_dry == w_in`; when the wet mode is inactive, both inlet-air humidity results agree and evaporation equals zero.
3. All calculated supply vapor pressures, humidity ratios, relative humidities and dew points are finite and physically possible; no RH clipping. **Supply target feasibility and recommended IT inlet feasibility are distinct flags.**
4. Baseline `(COP=3, wet aux=10)` reproduces `24,690`, `26,335.5`, `8,203.34` and `DeltaE ≈ 1645.5` using Step 34 rounding tolerances.
5. Raising COP lowers dry electricity; raising wet auxiliary power raises wet electricity; all five cases keep **24,000 kWh IT**, the same common fans, the same modeled water, and unchanged feasibility flags.
6. If any hourly recommended-envelope failures occur, every whole-day `R` is clearly tagged **conditional / not full-day feasible** in the CSV and note. Do not conceal the failures by reporting zero or by treating undefined cases as successful.

**Stop here.** The result should decide whether Step 34's energy–water comparison is operationally interpretable under the selected recommended envelope. If not, the *next* research question is how to represent humidity conditioning or an appropriate alternative air-handling architecture—not another round of COP or scheduling sweeps.


---

Discussion context:

## Step 35 — Cooling feasibility and electricity–water sensitivity

Fundamental question: Does the electricity–water trade-off established in Step 34 remain meaningful when we check IT supply-air conditions and vary the most important equipment assumptions?

One important issue deserves priority: Step 34 reported outdoor dew points up to 21°C, while the ASHRAE recommended inlet-air envelope has a maximum dew point of 15°C, alongside temperature and relative-humidity limits.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://handbook.ashrae.org\&sz=32)

handbook.ashrae.org



This means the existing dry sensible-only configuration cannot meet the recommended humidity envelope during at least some hours. Direct evaporation may face the same problem or worsen it.

Step 35 must first establish which modeled operating hours are acceptable. Only then should we interpret the electricity–water comparison as a feasible operating trade-off. Changing COP alone cannot solve humidity violations.

I've prepared the complete, implementation-ready plan for the local agent.

Download Step 35 — Cooling Feasibility and Equipment Sensitivity (.md)

Save it as `dc_resource_sim/context/step35.md`.

### Exact experiment

| Component    | Specification                                                                             |
| ------------ | ----------------------------------------------------------------------------------------- |
| Input        | Saved Step 34 hourly CSV, June 25, 2023                                                   |
| Feasibility  | Check both modes against recommended supply temperature, relative humidity, and dew point |
| Sensitivity  | COP = 2, 3, 5; wet auxiliaries = 5, 10, 20 kW                                             |
| Design       | Five one-factor-at-a-time cases, not a full parameter grid                                |
| Outputs      | One hourly feasibility CSV, one five-row sensitivity CSV, one short findings note         |
| Code changes | One new script; no changes to previous experiments                                        |

### Most valuable possible conclusions

First: Determine whether the configurations in Step 34 can actually satisfy the selected IT inlet-air recommendations.

Second: Determine whether the additional electricity required to avoid evaporation remains positive and substantial across the assumed equipment settings.

If the humidity screen fails, the agent must preserve the conditional electricity–water results but not describe them as feasible full-day operating alternatives.

This is the critical safeguard. We should not continue building optimization models around cooling configurations that may require additional, unmodeled humidity control.

Recommendation: Execute this limited experiment and stop. The result will establish whether the next step should improve the air-handling physics or move toward broader electricity–water planning.