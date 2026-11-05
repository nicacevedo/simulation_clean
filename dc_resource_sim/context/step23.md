# Step 23 — W0: define the water measure and verify the constant-intensity baseline

**Purpose.** Confirm exactly what W0 means and what it does (and cannot) predict, before returning to physical water modeling. **One new relationship only; no weather, cooling devices, meters, or optimization.**

## 1. What Steps 21–22 established

- Step 21: `M0` predicts aggregate *electricity*, `P_DC = 1.0471 P_IT`. Its overhead is not an independently identified cooling component. W0's previously used `0.5` is an **illustrative** water intensity, not a measured site coefficient.
- Step 22: a 1 MW IT load produces approximately 1 MW thermal at steady state. The heat split between room air and other routes is an assumption. **W0 does not depend on that split**; it is not a heat-to-water model.
- Water categories must be kept separate: **onsite consumption**, **site intake/withdrawal**, **process evaporation**, **tower makeup**, and **return/discharge** are not interchangeable. For this step W0 is explicitly an *onsite direct-water-consumption accounting proxy*.

## 2. One equation and one accounting label

For each one-hour interval ($\Delta t=1\,\mathrm{h}$):

$$
E_t^{IT}=P_t^{IT}\Delta t,\qquad
V_t^{W0,\mathrm{direct\,con}}=w_0E_t^{IT},
\qquad w_0=0.5\;\mathrm{L/kWh_{IT}}.
$$

The corresponding hourly *average modeled consumption rate* is $F_t^{W0}=V_t^{W0}/\Delta t$ in L/h. With a constant $w_0$:

$$
V_{\mathrm{day}}^{W0}=w_0\sum_t E_t^{IT},\qquad
F_{\mathrm{peak}}^{W0}=\max_t(V_t^{W0}/\Delta t).
$$

Record `water_basis = "onsite_direct_consumption_proxy"`. Do **not** relabel this modeled quantity as intake, municipal delivery, makeup, or groundwater withdrawal. **Its peak is a modeled consumption rate, not a measured peak supply requirement.**

## 3. Minimal comparison (reuse Step 22 IT profiles)

| Case | IT load (kW) | IT energy (kWh/day) | W0 water (L/day) | Peak modeled W0 rate (L/h) |
|---|---|---:|---:|---:|
| A — constant | 1,000 × 24 h | 24,000 | **12,000** | **500** |
| B — variable | 800 × 12 h, then 1,200 × 12 h | 24,000 | **12,000** | **600** |

**New insight:** time shifting at fixed *total IT energy* does not change W0's daily direct-consumption proxy; it can change the *hourly rate*. This is a mathematical consequence of constant intensity, not evidence about the behavior of a real cooler or water meter. W0 would also produce the same total for Step 22's half-air-routing case C, despite a different cooling architecture: W0 cannot resolve that difference.

## 4. One short verification script

Create **only** `dc_resource_sim/src/experiments/w0_water_basis.py`. Standard-library Python suffices. Leave earlier steps untouched.

```python
"""Step 23: illustrative W0 direct-consumption accounting, not site intake."""
from math import isclose

DT_H = 1.0
W0_L_PER_KWH_IT = 0.5  # assumed, not calibrated
WATER_BASIS = "onsite_direct_consumption_proxy"


def summarize(it_kw):
    it_kwh = [p * DT_H for p in it_kw]
    water_l = [W0_L_PER_KWH_IT * e for e in it_kwh]
    assert all(p >= 0 for p in it_kw)
    assert all(isclose(v, W0_L_PER_KWH_IT * e) for v, e in zip(water_l, it_kwh))
    return sum(it_kwh), sum(water_l), max(v / DT_H for v in water_l)


A = summarize([1000.0] * 24)
B = summarize([800.0] * 12 + [1200.0] * 12)

assert isclose(A[0], B[0]) and isclose(A[0], 24000.0)
assert isclose(A[1], B[1]) and isclose(A[1], 12000.0)
assert isclose(A[2], 500.0) and isclose(B[2], 600.0)

print("Water basis:", WATER_BASIS)
for label, (energy, water, peak) in (("A constant", A), ("B variable", B)):
    print(f"{label}: IT={energy:.0f} kWh/day; "
          f"W0={water:.0f} L/day; peak W0 rate={peak:.0f} L/h")
print("PASS: W0 conserved under equal IT energy; peak rate changes")
```

Expected: A and B both give 24,000 kWh IT and 12,000 L modeled onsite direct consumption, with peak rates 500 and 600 L/h respectively.

## 5. Stop and record the limitation

Close Step 23 after (i) both totals match, (ii) the rates differ, and (iii) the `water_basis` is printed and described correctly. Add only this interpretation to the results:

> W0 is a constant *onsite direct-consumption* proxy per kWh of IT electricity. It is invariant to workload timing if total IT energy is fixed. Its hourly output is not a measured intake/makeup flow. It contains no information about cooling architecture, weather, temperature, airflow, treatment losses, or the origin of the water.

**Do not** use the Prineville monthly city-meter totals to fit `w0` in this step: the meter boundary and the denominator are not identified well enough for that inference. Do not combine W0 with Step 17 tower makeup or Step 20 air evaporation as if they are additive contributions from the same site.

## 6. Next, Step 24 — physical contrast, not a new model family

Reuse the **existing Step 20** W2-Air code. With the *same* 1 MW IT load, examine only three outdoor-air states: (20°C, 50% RH), (30°C, 30% RH), and (30°C, 70% RH). Ask whether the specified supply temperature is feasible and, if so, how much water **evaporates**. That will show the first qualitative difference from W0 (constant 500 L/h): zero evaporation in the dry/no-mist case, positive evaporation under feasible misting, and an explicit infeasible state at high humidity. **Do not equate W2 evaporation with W0 onsite consumption**; their physical and reporting boundaries differ. No new datasets, components, or optimization are necessary.

---

Context:

## Step 23 — Understand and verify the W0 water model

Step 22 is complete. We have established how IT electricity becomes heat and how the heat carried by server air determines airflow.

The next step should be small: understand precisely what W0 predicts, verify its behavior, and establish why we eventually need a physical water model.

I've prepared the complete specification, including tested Python code, expected results, and stopping criteria.

Download Step 23 — W0 Water Model and Accounting Basis (.md)

Save it as `dc_resource_sim/context/step23.md`.

### 1. The one relationship to study

Keep our original W0 model:

\\[ \boxed{V_t^{direct,con}=w_0E_t^{IT}} \\]

where \\(w_0=0.5\\) L/kWh IT is an illustrative direct-water-consumption intensity, not a measured coefficient.

W0 predicts water from IT electricity without explicitly representing heat rejection, cooling equipment, temperature, or humidity.

### 2. The minimal experiment

Reuse the two workload profiles from Step 22.

| Quantity                      | A: Constant 1 MW | B: 0.8/1.2 MW |
| ----------------------------- | ---------------- | ------------- |
| Daily IT energy               | 24,000 kWh       | 24,000 kWh    |
| Daily W0 consumption          | 12,000 L         | 12,000 L      |
| Peak modeled consumption rate | 500 L/h          | 600 L/h       |

Three checks are sufficient:

1. Conservation: Both profiles use the same daily IT energy and therefore predict the same daily water consumption.
2. Peak behavior: Changing the load distribution increases the peak modeled water-consumption rate by 20%.
3. Accounting boundary: W0 consumption is not automatically facility water intake, cooling-tower makeup, or groundwater withdrawal.

The third point matters especially. A peak W0 consumption rate is not necessarily the peak water supply required by a facility.

### 3. What we should learn

This establishes a useful limitation:

Under a constant WUE coefficient, shifting IT energy between hours cannot reduce total modeled direct-water consumption if total IT energy remains fixed.

Moreover, W0 cannot distinguish different cooling architectures.

For example, Step 22's case C sends half the IT heat through another cooling route. W0 would still predict exactly 12,000 L/day because its only input is IT electricity.

That is not a computational error. It is a limitation of the model itself.

### 4. Implementation

Create just one file:

`dc_resource_sim/src/experiments/w0_water_basis.py`

The attached Markdown contains a complete reference implementation. I executed it and verified that all assertions pass.

Do not change earlier scripts, fit new coefficients, use Prineville water bills, or add new physical equations.

### 5. What follows: Step 24

Once Step 23 passes, we can make the first meaningful comparison against the existing W2-Air model.

At the same 1 MW IT load:

| Outdoor condition | W0      | W2-Air evaporation        |
| ----------------- | ------- | ------------------------- |
| 20°C, 50% RH      | 500 L/h | 0 L/h                     |
| 30°C, 30% RH      | 500 L/h | 489.4 L/h                 |
| 30°C, 70% RH      | 500 L/h | Cooling target infeasible |

These are different water-accounting quantities, so their values are not directly interchangeable. The comparison illustrates their different model behavior, not prediction accuracy.

W0 remains constant, whereas W2-Air responds to cooling conditions and feasibility constraints.

My recommendation: Complete only Step 23 now. Its main contribution is to establish W0 as a clear, reproducible accounting baseline and understand exactly why additional cooling physics may be necessary.

After that, we can revisit the physical W2-Air equations one relationship at a time, without adding new complexity or repeating the previous exploratory work.