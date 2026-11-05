# Step 26 — One 24-hour W2-Air water/heat trajectory

**Purpose.** Step 25 established the *hourly* idealized treatment balance. This step adds only **time aggregation**: run the **unchanged** W2-Air + treatment equations for one controlled 24-hour weather sequence, keeping IT load and all equipment assumptions fixed. Confirm dry/wet operating hours, hourly/total process-water demand, peak feed rate, and correct treatment of an infeasible hour.

**Status of inputs.** This is a *constructed test day*, **not observed Prineville or ESIF weather**. It is deliberately made of previously verified Step 20 air states so hourly outputs are known in advance. Use real location-matched weather only after this integration passes. This step is a software/physical-consistency test, **not site calibration**.

## 1. Freeze the assumptions—one new input dimension only

- Time: 24 one-hour intervals; all day totals below are sums of rates × 1 h.
- IT power: **1,000 kW in every hour**; IT heat handled by server air is assumed **1,000 kW thermal**.
- Electricity baseline: **M0**, $P^{DC}=1.0471P^{IT}$ (aggregate meter predictor, **no separately added cooling electricity**).
- Water baseline: **W0**, $w_0=0.5$ L/kWh IT, explicitly a **direct-consumption proxy**.
- Physical water: **W2-Air** from Step 20; the unchanged $T_{supply,max}=25^\circ$C, $\Delta T_{server}=15^\circ$C, $\epsilon_{max}=0.8$, $p=101.325$ kPa, and entering liquid-water temperature of 25°C are all **illustrative**.
- Treatment: **$\eta=0.8$**, with *all treated permeate evaporating*, no storage, recapture or additional uses. As in Step 25, $V^{feed}=V^{evap}/\eta$ and $V^{reject}=V^{feed}-V^{evap}$.
- Weather (the only hour-varying input):

| Hours, zero-indexed | Outside air | Expected cooling mode |
|---|---|---|
| 00–07 | 20°C, 50% RH | Dry (no evaporation) |
| 08–15 | 30°C, 30% RH | Wet |
| 16–23 | 35°C, 30% RH | Wet |

**No optimization, airflow fitting, location-specific electricity coefficient, real weather download, or new cooling/fallback system.**

## 2. The small additional calculation

For each hour $t$, call the **existing** `direct_evap(T_t, RH_t, it_kw=1000)`:

- If the result is `dry` or `wet`, extract $F_t^{evap}$ (L/h) and calculate

  $$F_t^{feed}=F_t^{evap}/0.8,\qquad F_t^{reject}=F_t^{feed}-F_t^{evap}.$$

- If the result is `infeasible`, store `None`/`N/A` for valid cooling-service evaporation/feed/reject; **do not** treat it as a zero-water service hour.
- Aggregate rates to daily volumes using $V=\sum_tF_t\Delta t$, with $\Delta t=1$ hour. Report **peak hourly feed (L/h)** separately from daily feed (L).
- Do **not** claim a complete-day feasible W2 water total if *any* hour is infeasible and no fallback has been modeled.

This tests the temporal composition of the model, **not** any new thermodynamic equation.

## 3. Expected outputs (reference implementation executed successfully)

| Quantity | Expected value |
|---|---:|
| Dry / wet / infeasible hours | 8 / 16 / 0 |
| M0 facility electricity | **25,130.4 kWh/day** |
| IT heat transferred to air | **24,000 kWh thermal/day** |
| W0 direct-consumption proxy | **12,000.0 L/day** |
| W2-Air process evaporation | **11,715.2 L/day** |
| Treatment feed | **14,644.0 L/day** |
| Liquid reject | **2,928.8 L/day** |
| Peak treatment feed | **1,218.8 L/h** |

**Key insight:** The W0 daily result (12,000 L) happens to be close to the W2 evaporation result (11,715 L), **but for the wrong reason to call it validation**. During eight dry hours W0 continues predicting 500 L/h while W2 predicts zero; during hot hours W2 evaporation approaches 975 L/h. Similar daily totals can conceal very different hourly operations and peak supply requirements. **W0 consumption and W2 process evaporation remain different accounting categories**.

## 4. One new script (standard library only)

Create exactly:

`dc_resource_sim/src/experiments/w2_air_day_first.py`

It imports the unmodified Step 20 `direct_evap` function. **Step 20's existing check/print output will precede the Step 26 output** because the import currently executes that script's top-level checks. Do not edit Step 20 simply to suppress the output.

```python
"""Step 26: one controlled 24-hour W2-Air trajectory.

All weather values and equipment parameters are illustrative.
Model outputs are not measured site water intake or total consumption.
"""
from math import isclose
from w2_air_first import direct_evap

IT_KW = 1000.0
M0_K = 1.0471
W0_L_PER_KWH = 0.5
RECOVERY = 0.8
HOURS = 24

# Three known Step 20 cases, 8 hours each. NOT measured weather.
WEATHER = [(20.0, 0.50)] * 8 + [(30.0, 0.30)] * 8 + [(35.0, 0.30)] * 8
assert len(WEATHER) == HOURS


def run_day(weather, print_hours=False):
    """Return results only if ALL hours meet the modeled supply target."""
    assert len(weather) == HOURS
    rows = []
    for hour, (temp_c, rh) in enumerate(weather):
        state = direct_evap(temp_c, rh, it_kw=IT_KW)
        row = {"hour": hour, "temp_c": temp_c, "rh": rh,
               "mode": state["mode"], "m0_kw": M0_K * IT_KW,
               "it_heat_kw": IT_KW, "w0_proxy_lph": W0_L_PER_KWH * IT_KW}
        if state["mode"] != "infeasible":
            evap = state["evaporation_lph"]
            feed = evap / RECOVERY
            reject = feed - evap
            assert isclose(feed, evap + reject, abs_tol=1e-9)
            assert evap >= 0 and reject >= 0
            row.update(evap_lph=evap, feed_lph=feed, reject_lph=reject)
        else:
            # Unknown fallback: no valid amount of water for fully served cooling.
            row.update(evap_lph=None, feed_lph=None, reject_lph=None)
        rows.append(row)

    if print_hours:
        print("hour  T(C)  RH   mode        evap(L/h)  feed(L/h)  reject(L/h)")
        for r in rows:
            fmt = lambda key: "n/a" if r[key] is None else f"{r[key]:.1f}"
            print(f"{r['hour']:02d}    {r['temp_c']:>4.0f}  {r['rh']:.0%}  "
                  f"{r['mode']:<10}  {fmt('evap_lph'):>9}  "
                  f"{fmt('feed_lph'):>9}  {fmt('reject_lph'):>11}")

    n_infeasible = sum(r["mode"] == "infeasible" for r in rows)
    if n_infeasible:
        return rows, None  # Never add partial hours into a "daily cooling" total.

    totals = {name: sum(r[f"{name}_lph"] for r in rows)
              for name in ["evap", "feed", "reject"]}  # 1 hour per row => L/day
    totals["peak_feed_lph"] = max(r["feed_lph"] for r in rows)
    totals["m0_facility_kwh"] = sum(r["m0_kw"] for r in rows)
    totals["it_heat_kwh_th"] = sum(r["it_heat_kw"] for r in rows)
    totals["w0_direct_proxy_l"] = sum(r["w0_proxy_lph"] for r in rows)
    totals["dry_hours"] = sum(r["mode"] == "dry" for r in rows)
    totals["wet_hours"] = sum(r["mode"] == "wet" for r in rows)
    return rows, totals


rows, day = run_day(WEATHER, print_hours=True)
assert day is not None
assert (day["dry_hours"], day["wet_hours"]) == (8, 16)
assert isclose(day["m0_facility_kwh"], 25130.4, abs_tol=1e-6)
assert isclose(day["it_heat_kwh_th"], 24000.0, abs_tol=1e-6)
assert isclose(day["w0_direct_proxy_l"], 12000.0, abs_tol=1e-6)
assert isclose(day["feed"], day["evap"] + day["reject"], abs_tol=1e-6)
assert isclose(day["evap"], 8 * (489.36647 + 975.03504), abs_tol=0.01)
print("\n24h: dry=%d, wet=%d, infeasible=0" % (day["dry_hours"], day["wet_hours"]))
print(f"M0 facility={day['m0_facility_kwh']:.1f} kWh; "
      f"IT heat={day['it_heat_kwh_th']:.1f} kWh thermal; "
      f"W0 proxy={day['w0_direct_proxy_l']:.1f} L")
print(f"W2 evaporation={day['evap']:.1f} L; "
      f"treatment feed={day['feed']:.1f} L; "
      f"reject={day['reject']:.1f} L; "
      f"peak feed={day['peak_feed_lph']:.1f} L/h")

# One-hour failure test: humid weather cannot achieve temperature target.
stress = list(WEATHER)
stress[10] = (30.0, 0.70)
stress_rows, stress_day = run_day(stress)
assert stress_rows[10]["mode"] == "infeasible"
assert stress_rows[10]["feed_lph"] is None
assert stress_day is None
print("Humid-hour control: infeasible; full-day W2 total = N/A (no fallback).")
print("PASS: hourly heat/water accounting, feasibility, 24h totals and peak water feed")
```

Run from repository root:

```bash
python dc_resource_sim/src/experiments/w2_air_day_first.py
```

## 5. Checks and stopping rule

1. **Integration:** all 24 hours have a mode and the modes are 8 dry, 16 wet, 0 infeasible.
2. **Energy:** IT thermal energy is 24,000 kWh thermal; M0 electrical energy is 25,130.4 kWh. Do not add cooling-fan/chiller electricity to M0.
3. **Water:** every feasible hour, $F^{feed}=F^{evap}+F^{reject}$; daily totals reconcile; peak treatment feed is reported in L/h.
4. **Infeasible control:** replace just hour 10 with `30°C, 70% RH`; confirm the mode is infeasible, its flows are `None`, and the full-day W2 result is **N/A**. Do not force a full-day total or assume an unmodeled fallback.
5. **Evidence:** weather and equipment conditions are assumed; flows are calculated. Process feed is **not** established to be municipal delivery, facility-wide water consumption, or groundwater withdrawal.

**Stop after one controlled day and this single infeasible-hour test.** No new weather file, model fitting, charts, optimization, Prineville reconciliation, or additional recovery scenarios.

## 6. Next small step only after completion

**Step 27:** audit the relevant Prineville meter categories and units so that we can state exactly **which** of these modeled quantities, if any, are comparable with the existing monthly records. This is a **measurement-boundary audit, not calibration**. Later, a verified location-matched weather day can replace this constructed day *without changing the physical equations*.

---

Context:

## Step 26 — First 24-hour electricity, heat, and water calculation

Step 25 is complete. We have now verified the distinction between evaporation, treatment feed, and liquid reject.

The next step should introduce only one change: allow weather to vary hourly while keeping IT load, cooling equipment, and treatment recovery fixed.

I prepared and tested the complete Step 26 specification.

Download Step 26 — 24-hour W2-Air Model (.md)

Save it as `dc_resource_sim/context/step26.md`.

### 1. What we want to understand

We already know that W2-Air can predict evaporation for individual operating conditions.

Now we want to establish:

- When does the cooling system operate without evaporation?
- How does hourly weather change evaporation and treatment feed?
- How do hourly rates translate into daily water volumes and peak supply requirements?
- What happens to the daily calculation if cooling becomes infeasible during one hour?

No additional cooling equations are necessary.

### 2. Minimal experiment

Use one constructed 24-hour weather profile so we can verify the calculations before using actual measured weather.

Keep IT load at 1,000 kW, M0 coefficient \\(k=1.0471\\), W0 intensity \\(w_0=0.5\\) L/kWh, and treatment recovery \\(\eta=0.8\\).

| Hours | Outdoor conditions | Expected operation  |
| ----- | ------------------ | ------------------- |
| 00–07 | 20°C, 50% RH       | Dry, no evaporation |
| 08–15 | 30°C, 30% RH       | Evaporative cooling |
| 16–23 | 35°C, 30% RH       | Evaporative cooling |

All equipment assumptions remain exactly as in Steps 20–25.

### 3. Expected results

I executed the reference implementation successfully.

| Quantity                | 24-hour result |
| ----------------------- | -------------- |
| IT electricity          | 24,000 kWh     |
| M0 facility electricity | 25,130.4 kWh   |
| W0 consumption proxy    | 12,000 L       |
| W2-Air evaporation      | 11,715.2 L     |
| Treatment feed          | 14,644.0 L     |
| Liquid reject           | 2,928.8 L      |
| Peak treatment feed     | 1,218.8 L/h    |

The most important insight: W0 and W2-Air produce surprisingly similar daily values, but very different hourly behavior.

During the first eight hours, W0 predicts 500 L/h while W2-Air predicts zero evaporation. During the hottest hours, W2-Air predicts approximately 975 L/h of evaporation.

Their similar daily totals are coincidental, not evidence of agreement with measurements. W0's consumption proxy and W2's process evaporation also remain distinct accounting categories.

### 4. One essential additional check

Replace one of the 24 hours with 30°C and 70% RH.

The existing W2-Air model should report that cooling is infeasible under its assumed equipment limits.

Do not assign zero water or report a valid full-day water total when the model cannot meet cooling requirements. A fallback cooling system has not been modeled.

### 5. Implementation and stopping rule

Create only:

`dc_resource_sim/src/experiments/w2_air_day_first.py`

The attached Markdown includes the complete tested code, the 24-hour output, and assertions.

Close Step 26 when:

1. All 24 hours are evaluated correctly.
2. The hourly and daily energy and water balances reconcile.
3. Peak water feed is distinguished from daily water volume.
4. The deliberately infeasible hour invalidates the complete-day W2 result.

Do not introduce real weather downloads, calibration, additional cooling equipment, or optimization in this step.

### What follows?

Step 27 should be a small measurement-boundary audit: establish which of our modeled quantities can actually be compared with the existing Prineville municipal water records, and which remain unidentified.

Then we can replace the constructed weather profile with a verified, location-matched day without changing the physical equations.

My recommendation: Complete this one-day integration test and stop. It is a small but necessary transition from individual physical equations to a time-dependent electricity–heat–water model.