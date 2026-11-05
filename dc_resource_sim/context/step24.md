# Step 24 — W0 versus W2-Air: first physical contrast

**Status:** Steps 21–23 are complete. Do not revisit their scripts. This step reuses the validated Step 20 direct-evaporative model, and adds no new cooling physics.

## Objective: one question

For the same IT load, why can W0 predict the same water use in every hour while a direct-evaporative cooler predicts **zero evaporation, positive evaporation, or an infeasible cooling target**, depending on ambient conditions?

## 1. Keep boundaries and assumptions fixed

- IT demand: **1,000 kW** for one hour. Model **W0**: `w0 = 0.5 L/kWh IT`, so `W0 = 500 L/h` (an illustrative **onsite direct-consumption proxy**).
- Model **W2-Air**: reuse the existing `direct_evap` function from `w2_air_first.py` unchanged. Its output is **process evaporation**, not total facility intake or municipal water delivery.
- Keep Step 20's **assumed**, not measured, operating parameters: all IT heat enters server air; 15°C server air rise; 25°C maximum supply temperature; maximum evaporative effectiveness 0.8; pressure 101.325 kPa; liquid-water temperature 25°C; one-stage direct evaporation, with no fallback equipment or treatment losses.
- Do **not** combine with the cooling-tower model or add fan/chiller electricity to M0's already aggregated facility power.

For a one-hour step, with IT power in kW:

$$F^{W0} = w_0 P^{IT}\;\;[\mathrm{L/h}].$$

Step 20 obtains the W2-Air evaporation rate from the air-side moisture balance:

$$F^{evap} \simeq \dot m_{da}(\omega_{supply}-\omega_{in})/\rho_w\;\;[\mathrm{L/h}],$$

with consistent mass-flow and density units. **Only when the cooling target is feasible** define a diagnostic effective evaporation intensity

$$w_{evap,eff}=F^{evap}/P^{IT}\;\;[\mathrm{L/kWh_{IT}}].$$

This diagnostic is **not** a calibrated facility WUE and is **not** an estimate of site water intake.

## 2. Reproduce three distinct outcomes

| Outside air | W0 proxy (L/h) | W2-Air mode | W2 evaporation (L/h) | Effective evaporation intensity (L/kWh IT) |
|---|---:|---|---:|---:|
| 20°C, 50% RH | 500 | dry | **0** | **0** |
| 30°C, 30% RH | 500 | wet, feasible | **489.37** | **0.48937** |
| 30°C, 70% RH | 500 | **infeasible** | **N/A, not zero** | **N/A** |

The infeasible case needs evaporative effectiveness about **1.113**, greater than the assumed maximum 0.8; its best achievable supply temperature is approximately **26.4°C**, above the 25°C target. The W0 numerical result does not make that cooling target feasible.

**Physical interpretation:** W0 has no weather or cooling-feasibility input. W2-Air uses outdoor air state, saturation limits, the required supply state, and airflow to calculate **evaporated water only**. Numerical proximity between W0's 500 and W2's 489.37 L/h is coincidence under the chosen assumptions—not calibration or evidence that they measure exactly the same facility quantity.

## 3. One small new check: hold weather fixed and change the IT load

Keep outside air at 30°C, 30% RH, and **do not change** the server air-temperature rise or supply target. Reuse `direct_evap(..., it_kw=...)`:

| IT power | W0 proxy | W2 evaporation | W2 intensity |
|---:|---:|---:|---:|
| 800 kW | 400 L/h | **391.49 L/h** | 0.48937 L/kWh IT |
| 1,000 kW | 500 L/h | **489.37 L/h** | 0.48937 L/kWh IT |
| 1,200 kW | 600 L/h | **587.24 L/h** | 0.48937 L/kWh IT |

**This is the new insight:** with **fixed weather, supply target, equipment assumptions, and constant server-air rise**, airflow is proportional to IT power and W2-Air also reduces to a linear intensity relationship. It is the *conditions and cooling feasibility* that make this physical intensity vary; simply calling a model “physics-based” does not guarantee a nonlinear dependence on IT load.

This proportionality could fail if airflow, recirculation, control, part-load behavior, or equipment constraints change with load. None is modeled here.

## 4. Minimal implementation

Create only `dc_resource_sim/src/experiments/w0_w2_air_compare.py`. No new dependencies. The script imports the existing Step 20 module and uses its already-tested model; because Step 20 currently runs its demonstrations at import time, those messages will appear before the Step 24 output. That is harmless—do not modify Step 20 merely to suppress them.

```python
"""Step 24: W0 proxy versus W2-Air evaporation and feasibility."""
from math import isclose
from w2_air_first import direct_evap  # Reuse Step 20; import prints Step 20 checks.

W0 = 0.5  # L/kWh IT; illustrative direct-consumption proxy
IT_KW = 1000.0

cases = [(20.0, 0.50), (30.0, 0.30), (30.0, 0.70)]
for temp, rh in cases:
    result = direct_evap(temp, rh, it_kw=IT_KW)
    w0_lph = W0 * IT_KW
    if result["mode"] == "infeasible":
        assert result["needed_effectiveness"] > 0.8
        assert result["best_supply_c"] > 25.0
        print(f"{temp:g} C/{rh:.0%}: W0={w0_lph:.1f} L/h; "
              "W2=infeasible (evaporation N/A)")
    else:
        evap = result["evaporation_lph"]
        intensity = evap / IT_KW
        print(f"{temp:g} C/{rh:.0%}: W0={w0_lph:.1f} L/h; "
              f"W2={result['mode']}, evap={evap:.2f} L/h; "
              f"effective intensity={intensity:.5f} L/kWh IT")
        if result["mode"] == "dry":
            assert isclose(evap, 0.0, abs_tol=1e-8)
        else:
            assert isclose(evap, 489.36647, abs_tol=0.01)

# New comparison: proportionality at ONE fixed weather/operating state.
ref = direct_evap(30.0, 0.30, it_kw=1000.0)
for it_kw in (800.0, 1000.0, 1200.0):
    z = direct_evap(30.0, 0.30, it_kw=it_kw)
    assert z["mode"] == "wet"
    assert isclose(z["evaporation_lph"] / it_kw,
                   ref["evaporation_lph"] / 1000.0, rel_tol=1e-10)
    print(f"IT={it_kw:.0f} kW: W0={W0*it_kw:.1f} L/h; "
          f"W2 evaporation={z['evaporation_lph']:.2f} L/h")

print("PASS: W0 is constant-intensity; W2 depends on air state and feasibility;")
print("at fixed weather and controls W2 evaporation scales with IT load.")
print("W0 is a consumption proxy; W2 is process evaporation, not site intake.")
```

Run with:

```bash
python dc_resource_sim/src/experiments/w0_w2_air_compare.py
```

## 5. Stopping rule

Close Step 24 when (1) the three air-state cases match Step 20; (2) the humid case reports **infeasible**, never zero water or a successfully served load; (3) the 800/1,000/1,200 kW case establishes proportionality *under fixed operating assumptions*; and (4) the distinction between the **W0 onsite-consumption proxy** and **W2 process evaporation** is explicit.

**Do not** fit W0, introduce Prineville weather, treatment/recovery, fan/chiller electricity, a fallback cooler, any new regression, or optimization. These are not needed to learn the one physical distinction in this step.

## 6. Next, only after Step 24: Step 25

Introduce **one hypothetical process-water treatment yield**, e.g. $\eta=1$ versus $0.8$, to distinguish **W2 evaporation** from **water intake** and **treatment reject**. Check the balance $V^{intake}=V^{evap}+V^{reject}$ under clearly defined no-storage assumptions. Do not call the entire intake amount water consumption or groundwater withdrawal.

---

Context:

## Step 24 — From W0 to a physical water model (W2-Air)

Step 23 is complete. W0 correctly predicts the same daily water consumption for equal IT energy, while allowing different peak consumption rates.

The next step should introduce only one conceptual improvement: water use should depend on whether evaporative cooling is needed and physically feasible.

We already implemented the necessary physics in Step 20. Rather than develop another model, I recommend reusing it and comparing its behavior directly with W0.

I've prepared and tested the complete Step 24 specification.

Download Step 24 — W0 versus W2-Air (.md)

Save it as `dc_resource_sim/context/step24.md`.

### 1. The main question

W0 uses:

\\[ V_t^{W0}=w_0E_t^{IT}. \\]

It has no information about weather or the cooling system.

W2-Air instead calculates evaporation from the air-side moisture balance:

\\[ \boxed{\dot V^{evap}\approx\dot m\_{da}(\omega\_{supply}-\omega\_{in})} \\]

The question is: What additional behavior does this physical relationship capture that W0 cannot?

### 2. First comparison: same IT load, different weather

Keep IT power at 1,000 kW and every Step 20 equipment assumption unchanged.

| Outdoor conditions | W0 consumption proxy | W2-Air evaporation | Cooling feasibility   |
| ------------------ | -------------------- | ------------------ | --------------------- |
| 20°C, 50% RH       | 500 L/h              | 0 L/h              | Feasible, no misting  |
| 30°C, 30% RH       | 500 L/h              | 489.4 L/h          | Feasible, wet cooling |
| 30°C, 70% RH       | 500 L/h              | N/A                | Infeasible            |

Three conclusions follow:

- W0 predicts the same amount regardless of cooling conditions.
- W2-Air predicts evaporation only when the modeled cooling process requires it.
- W2-Air identifies conditions where the assumed equipment cannot achieve the target temperature.

Important: W0 represents an assumed onsite direct-consumption proxy, while W2-Air calculates process evaporation. These are not identical accounting boundaries, so the numbers cannot establish which model predicts total facility water use more accurately.

### 3. The small new experiment I recommend

Keep weather fixed at 30°C and 30% RH, and change only IT power.

| IT power | W0      | W2-Air evaporation |
| -------- | ------- | ------------------ |
| 800 kW   | 400 L/h | 391.5 L/h          |
| 1,000 kW | 500 L/h | 489.4 L/h          |
| 1,200 kW | 600 L/h | 587.2 L/h          |

This reveals something particularly useful.

Under fixed weather and cooling assumptions, W2-Air is also proportional to IT load.

Its equivalent evaporation intensity in this example is:

\\[ w\_{\mathrm{evap,eff}} =\frac{\dot V^{evap}}{P^{IT}} \approx0.4894\ \mathrm{L/kWh\_{IT}}. \\]

Thus, W2-Air is not necessarily nonlinear in IT power. Its additional value is explaining how the effective evaporation intensity depends on weather, cooling requirements, and equipment feasibility.

That is an important connection between our simple W0 model and the physical model.

### 4. Implementation and stopping rule

Create only:

`dc_resource_sim/src/experiments/w0_w2_air_compare.py`

The attached Markdown contains the complete tested code. It imports Step 20's existing `direct_evap` function without changing that script.

Close Step 24 when:

1. The three weather cases reproduce Step 20.
2. The infeasible case is explicitly marked as infeasible, not assigned zero water.
3. W2-Air's proportionality to IT power is verified under fixed operating conditions.
4. W0 consumption and W2-Air evaporation remain correctly distinguished.

No new data, calibration, fan power, treatment assumptions, or optimization.

### 5. What follows: Step 25

The next small relationship should be:

\\[ \text{Water evaporation} \longrightarrow \text{Water intake and treatment reject}. \\]

We can introduce one illustrative treatment-efficiency parameter and check the water balance without changing anything else.

My recommendation: Complete Step 24 exactly as specified. Its value is not producing more evaporation estimates; it is understanding precisely how W2-Air extends W0, when they behave similarly, and why cooling feasibility must be represented separately from water intensity.