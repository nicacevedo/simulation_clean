# Step 25 — From W2-Air evaporation to treatment-water intake

**Purpose.** Step 24 confirmed that W2-Air predicts process evaporation and can detect infeasible cooling conditions. Add only **one parameter**—the water-treatment recovery fraction—to distinguish evaporation from the water supplied to the treatment system. Keep the existing 1 MW reference case, and leave every earlier script unchanged.

## 1. Exactly one new assumption and balance

Assume a once-through idealized treatment + direct-evaporative process:

- A fraction $\eta$ of feedwater becomes treated permeate, $0<\eta\le1$.
- **All permeate evaporates** in the cooling stage; no product-water storage, recapture, drift, carryover, purge or other uses.
- The rejected feedwater exits as a separate **liquid reject stream**; its eventual destination and whether it returns to the source basin are *unknown*.
- The air-side conditions, IT load, and cooling feasibility remain exactly those of Step 24. $\eta$ is hypothetical, **not measured Prineville RO recovery**.

For a *feasible* hourly evaporative demand $V_t^{evap}$ (L/h),

$$
V_t^{feed}=\frac{V_t^{evap}}{\eta},\qquad
V_t^{reject}=V_t^{feed}-V_t^{evap}.
$$

Check the simplified balance:

$$V_t^{feed}=V_t^{evap}+V_t^{reject}.$$

**Labels matter:** $V^{evap}$ is process evaporation; $V^{feed}$ is *treatment-system feedwater* (not necessarily the complete facility's municipal intake); $V^{reject}$ is a liquid stream (not automatically water consumed or wastewater returned to the same source). Do **not** equate any of these with groundwater withdrawal or infer site consumption from feedwater alone.

## 2. Minimal tests and expected results

Reuse `direct_evap(30.0, 0.30, it_kw=1000.0)` from Step 20; it returns approximately **489.366 L/h evaporation**.

| Recovery $\eta$ | Evaporation (L/h) | Treatment feed (L/h) | Liquid reject (L/h) |
|---|---:|---:|---:|
| 1.0 | 489.37 | 489.37 | 0.00 |
| 0.8 | 489.37 | 611.71 | 122.34 |

Also verify the two previous controls:

- **Dry:** `20°C, 50% RH` needs no evaporation; with the simplified no-other-use assumptions, treatment feed and reject are both zero.
- **Infeasible:** `30°C, 70% RH` is still infeasible. Do **not** calculate a valid cooling-service feedwater demand or turn its evaporation into zero. Treatment recovery does not fix cooling infeasibility.

A lower treatment recovery raises feedwater and reject **without changing the evaporation required by the cooling process**. This is a boundary/accounting effect, not better cooling performance.

## 3. One new script (standard library only)

Create `dc_resource_sim/src/experiments/w2_air_treatment_first.py`. This imports the existing Step 20 model and intentionally does not modify it. Step 20's test printout will appear on import, as in Step 24.

```python
"""Step 25: idealized treatment feed and reject for W2-Air evaporation.

Recovery is assumed, not measured. Feed is not facility withdrawal or
consumption; infeasible cooling remains infeasible.
"""
from math import isclose
from w2_air_first import direct_evap


def treatment_balance(evap_lph, recovery):
    if evap_lph < 0 or not (0 < recovery <= 1):
        raise ValueError("Require evaporation >= 0 and 0 < recovery <= 1")
    feed_lph = evap_lph / recovery
    reject_lph = feed_lph - evap_lph
    assert isclose(feed_lph, evap_lph + reject_lph, abs_tol=1e-9)
    assert reject_lph >= -1e-9
    return feed_lph, reject_lph


wet = direct_evap(30.0, 0.30, it_kw=1000.0)
assert wet["mode"] == "wet"
evap = wet["evaporation_lph"]
assert isclose(evap, 489.36647, abs_tol=0.01)

for eta, expected_feed, expected_reject in (
    (1.0, 489.36647, 0.0),
    (0.8, 611.70809, 122.34162),
):
    feed, reject = treatment_balance(evap, eta)
    assert isclose(feed, expected_feed, abs_tol=0.02)
    assert isclose(reject, expected_reject, abs_tol=0.02)
    print(f"eta={eta:.1f}: evaporation={evap:.2f}, "
          f"feed={feed:.2f}, reject={reject:.2f} L/h")

# Cooling conditions still govern whether the process runs.
dry = direct_evap(20.0, 0.50, it_kw=1000.0)
assert dry["mode"] == "dry"
assert treatment_balance(dry["evaporation_lph"], 0.8) == (0.0, 0.0)

humid = direct_evap(30.0, 0.70, it_kw=1000.0)
assert humid["mode"] == "infeasible"
assert "evaporation_lph" not in humid  # No valid cooling-service water estimate.
print("Dry: evaporation=feed=reject=0 L/h (idealized process)")
print("Humid: cooling infeasible; no valid treatment-flow estimate")
print("PASS: feed = evaporation + reject; lower recovery raises feed only")
```

Run from the repository root:

```bash
python dc_resource_sim/src/experiments/w2_air_treatment_first.py
```

## 4. Stopping rule

Close Step 25 after verifying: (1) the two recovery cases reproduce the table, (2) treatment feed equals evaporation plus liquid reject, (3) changing recovery does not alter air-side evaporation, and (4) dry and infeasible cases retain their distinct meanings. Record all assumed versus identified quantities. **No new weather, monthly calibration, reverse-osmosis process model, cooling-power model, optimizer, or further losses.**

## 5. Next only after completion

**Step 26:** run the same fixed physical model through **one** verified 24-hour weather profile, keeping 1 MW IT, the same air-side controls, and one treatment recovery. Compute hourly feasibility, evaporation, feed and reject. If any hour is infeasible, do not report a physically feasible full-day water total without an explicit fallback model.

---

Context:

## Step 25 — From evaporation to water intake and treatment losses

Step 24 is complete. It established that W2-Air responds to weather and cooling feasibility, while W0 is a constant water-consumption proxy.

The next improvement should be small: connect the evaporation predicted by W2-Air to the amount of water required by the treatment system.

I've prepared the full Step 25 specification and tested its reference code successfully.

Download Step 25 — Water Treatment Balance (.md)

Save it as `dc_resource_sim/context/step25.md`.

### 1. The one new relationship

Step 24 gave us:

\\[ V^{evap}=489.37\ \mathrm{L/h} \\]

for the illustrative 1 MW facility at 30°C and 30% relative humidity.

But that is evaporated water, not necessarily the water taken into the treatment system.

Introduce one parameter, \\(\eta\\), representing treatment recovery:

\\[ \boxed{ V^{feed}=\frac{V^{evap}}{\eta} } \\]

and

\\[ V^{reject}=V^{feed}-V^{evap}. \\]

Here we assume all treated water evaporates, with no storage, recapture, or other losses. Treatment reject remains a separate liquid stream.

### 2. The minimal experiment

Keep the same IT load, weather, airflow, and cooling assumptions from Step 24. Change only treatment recovery.

| Quantity       | Recovery 100% | Recovery 80% |
| -------------- | ------------- | ------------ |
| Evaporation    | 489.37 L/h    | 489.37 L/h   |
| Treatment feed | 489.37 L/h    | 611.71 L/h   |
| Liquid reject  | 0 L/h         | 122.34 L/h   |

Main insight: Lower treatment recovery increases the water required from the supply system without increasing the evaporation needed for cooling.

This is a simple but essential distinction for eventual comparisons with municipal water records.

### 3. What to verify

Four checks are sufficient:

1. Water balance: treatment feed equals evaporation plus reject.
2. Recovery: changing \\(\eta\\) does not change the air-side evaporation.
3. Dry operation: when cooling does not require evaporation, the simplified process uses no treatment water.
4. Infeasible operation: the 30°C/70% RH case remains infeasible. Do not assign it zero water or a valid cooling-service intake.

Most importantly, treatment feed is not automatically total facility intake, and reject is not automatically water consumption. Their hydrologic meaning depends on the physical supply and discharge boundaries.

### 4. Implementation

Create only:

`dc_resource_sim/src/experiments/w2_air_treatment_first.py`

The attached specification includes the tested Python implementation, expected numerical results, assertions, and stopping rule.

It reuses Step 20's `direct_evap` function. No changes to previous scripts, new data, or additional dependencies are necessary.

### 5. What follows

Step 26 should be the first 24-hour physical water calculation, using the same model with hourly weather.

We will keep IT load and treatment recovery fixed, then observe when the model predicts dry cooling, evaporative cooling, or infeasibility. Only after that should we consider additional equipment assumptions.

My recommendation: Complete Step 25 and stop. Its value is establishing a trustworthy distinction between evaporation, treatment feed, and liquid reject before attempting realistic facility water accounting.