## Step 17 — First physics-based cooling-tower water model

Step 16 is complete. The next step is to move from assumed water intensity (W0) to a physical relationship between heat rejection and water use.

The duplicated `step17.md` is an administrative mistake, not a modeling problem. Step 17 has not been implemented.

I recommend keeping this step very small: one cooling-tower archetype, one forward calculation, and a few physical consistency checks. No optimization, new datasets, or model fitting.

The key research question is:

Given a known amount of heat rejected through a cooling tower, how much water evaporates, how much additional water is discharged, and how much freshwater makeup is required?

This directly advances the original plan's W2-Tower model, while keeping the distinction between water consumption and withdrawal needed for our eventual groundwater-planning framework.

### 1. Physical model

For each hour, assume the IT electricity becomes heat and, for this first illustrative case only, all that heat is rejected through a wet cooling tower:

\\[ Q_t^{wet}=P_t^{IT}\Delta t. \\]

Then calculate:

\\[ \boxed{ \begin{aligned} V_t^{evap}&\approx1.4694Q_t^{wet}\\\\[3pt] V_t^{blowdown}&=\frac{V_t^{evap}}{COC-1}\\\\[3pt] V_t^{makeup}&=V_t^{evap}+V_t^{blowdown}. \end{aligned}} \\]

The coefficient assumes that all wet heat rejection is carried by evaporation, with representative latent heat of 2.45 MJ/kg and water density of approximately 1 kg/L.

The blowdown and makeup relationships are consistent with DOE cooling-tower guidance.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.energy.gov\&sz=32)

energy.gov+1



Crucially, makeup is not automatically groundwater withdrawal. It is the tower's water-supply requirement; we still need to identify its source and the destination of discharged water.

### 2. Three checks worth implementing

Use the same 24-hour profiles from Step 00, with \\(COC=4\\).

| Test                        | What to verify                                  |
| --------------------------- | ----------------------------------------------- |
| A — Constant 1 MW IT load   | Evaporation, blowdown, and makeup balance       |
| B — 800/1,200 kW IT profile | Same daily water totals, different peak makeup  |
| C — Change COC from 3 to 6  | Lower makeup requirement, unchanged evaporation |

I wrote and executed the reference code. The expected results are:

| Output      | Constant load | Variable load |
| ----------- | ------------- | ------------- |
| Evaporation | 35,265 L      | 35,265 L      |
| Blowdown    | 11,755 L      | 11,755 L      |
| Makeup      | 47,020 L      | 47,020 L      |
| Peak makeup | 1,959 L/h     | 2,351 L/h     |

Increasing COC from 3 to 6 reduces daily makeup from approximately 52,898 L to 42,318 L, or 20%, without changing the evaporation requirement.

These results illustrate two distinct planning quantities: total consumptive demand and peak water-supply demand.

### 3. Implementation instructions

I prepared the complete Step 17 specification, including the assumptions, mathematical model, tested Python code, expected results, and stopping rule.

Download the corrected step17.md

Save it to:

`dc_resource_sim/context/step17.md`

It replaces the accidental Step 16 duplicate.

The implementation requires only one new Python file:

`dc_resource_sim/src/experiments/w2_tower_first.py`

No external data, dependencies, new plots, or changes to the previous experiments are needed.

### 4. What not to claim yet

This is a physics-based illustrative cooling-tower model, not an empirically validated water model for ESIF, Prineville, or a particular data center.

In particular, real wet heat rejection need not equal IT heat. Chiller compressor heat, heat-rejection equipment, sensible heat transfer, and operating configuration may matter. We deliberately leave these for the next stage.

Nor should we treat the calculated water intensity as a calibrated replacement for W0.

### 5. What should follow Step 17?

The next critical step should be to establish a defensible connection between cooling-system architecture and \\(Q^{wet}\\), the heat actually rejected through wet equipment.

That is the physical input our tower model needs before introducing weather dependence or optimization.

Final recommendation: Implement the three checks in the attached specification and stop. Step 17 should establish a trusted heat-to-water balance, not another complete water-modeling framework. Once verified, we can focus on the physically meaningful missing relationship: how much of a data center's generated heat reaches its wet cooling system under different operating conditions?

---

Explicit step 17:

# Step 17 — First physics-based cooling-tower water model (W2-Tower)

## Objective

Implement and verify **one forward mapping** from wet heat rejection to evaporation, blowdown, and cooling-tower makeup. No optimization, weather data, new measurements, or fitting.

This is a **hypothetical open-recirculating cooling tower**, not a calibration of NLR ESIF or Prineville. It does **not** replace the earlier W0 coefficient with a purported measured value.

## Model boundaries and assumptions

- One-hour intervals; use the same two 24-hour IT-load profiles as Step 00: A = 1,000 kW in each hour; B = 800 kW for 12 hours then 1,200 kW for 12 hours.
- IT electricity becomes IT heat: $Q^{IT}_t \approx E^{IT}_t$ (kWh thermal per hour).
- **Illustrative coupling only:** all IT heat reaches wet heat-rejection equipment, so $Q^{wet}_t = Q^{IT}_t$. No chiller-compressor heat or auxiliary electricity is added. In later architectures, **$Q^{wet}$ must be supplied by a cooling-system heat balance**, not simply inferred from fitted PUE.
- Assume all wet rejection is latent: $\alpha_{lat}=1$. Neglect sensible heat transfer, drift, leaks, basin storage changes, and treatment reject. Use representative latent heat $h_{fg}=2.45$ MJ/kg and water density approximately 1 kg/L.
- Cycles of concentration: $COC=4$ initially ($COC>1$), held fixed.

## Equations (per hour)

$E^{IT}_t = P^{IT}_t\Delta t$; $Q^{wet}_t = E^{IT}_t$ for **this illustrative case only**.

$V^{evap}_t = \alpha_{lat}\, Q^{wet}_t\,(3.6/h_{fg}) \approx 1.4694\, Q^{wet}_t$ L, when $Q^{wet}$ is in kWh thermal and $h_{fg}$ is in MJ/kg.

$V^{blowdown}_t = V^{evap}_t/(COC-1)$.

$V^{makeup}_t = V^{evap}_t + V^{blowdown}_t = V^{evap}_t\,COC/(COC-1)$.

**Accounting:** $V^{evap}$ is the approximate **consumptive loss** at the tower; $V^{makeup}$ is the **tower inlet requirement**; $V^{blowdown}$ is a liquid discharge. Only with an explicitly stated freshwater source, return-flow location, and other losses can makeup be interpreted as source withdrawal or net basin depletion. Nothing here identifies groundwater extraction.

## Implementation

Add only `dc_resource_sim/src/experiments/w2_tower_first.py`. No extra dependencies and no changes to previous scripts.

```python
"""Step 17: Cooling-tower heat-to-water balance, illustrative only."""
from math import isclose

DT_H = 1.0
LATENT_MJ_KG = 2.45
EVAP_L_PER_KWH_TH = 3.6 / LATENT_MJ_KG  # assumes ~1 kg/L
COC = 4.0


def tower(q_wet_kwh_th, coc=COC):
    assert q_wet_kwh_th >= 0 and coc > 1
    evaporation = EVAP_L_PER_KWH_TH * q_wet_kwh_th
    blowdown = evaporation / (coc - 1)
    return evaporation, blowdown, evaporation + blowdown


def run(it_kw, coc=COC):
    # Initial test only: IT heat = heat rejected through wet tower.
    water = [tower(p * DT_H, coc) for p in it_kw]
    e, b, m = zip(*water)
    assert all(isclose(mm, ee + bb) for ee, bb, mm in water)
    return sum(e), sum(b), sum(m), max(m) / DT_H


A = [1000.0] * 24
B = [800.0] * 12 + [1200.0] * 12
assert isclose(sum(A), sum(B))

constant = run(A)
shifted = run(B)
assert all(isclose(u, v) for u, v in zip(constant[:3], shifted[:3]))
assert shifted[3] > constant[3]

for name, result in [('A constant', constant), ('B shifted', shifted)]:
    e, b, m, peak = result
    print(f'{name}: evaporation={e:.1f} L, blowdown={b:.1f} L, '
          f'makeup={m:.1f} L, peak makeup={peak:.1f} L/h')

low_coc, high_coc = run(A, 3), run(A, 6)
assert isclose(low_coc[0], high_coc[0])
assert high_coc[2] < low_coc[2]
print(f'COC=3 makeup: {low_coc[2]:.1f} L; COC=6: {high_coc[2]:.1f} L')
```

Run from the repository root with `python dc_resource_sim/src/experiments/w2_tower_first.py`.

## Expected checks and outputs

| Profile | Evaporation | Blowdown | Makeup | Peak makeup |
|---|---:|---:|---:|---:|
| A: constant 1 MW | 35,265.3 L | 11,755.1 L | 47,020.4 L | 1,959.2 L/h |
| B: 0.8 then 1.2 MW | 35,265.3 L | 11,755.1 L | 47,020.4 L | 2,351.0 L/h |

- Every hour: **makeup = evaporation + blowdown**.
- Identical total IT energy gives identical total evaporation and makeup **under constant physical coefficients**; changing hourly load changes **peak makeup demand**.
- At fixed heat rejection, increasing $COC$ from 3 to 6 leaves evaporation unchanged and reduces daily makeup from **52,898.0 L to 42,318.4 L** (~20%). This assumes water chemistry permits those cycles.

## Stop condition and next step

Stop when these balances, invariances, and peak results reproduce. **Do not fit a WUE, apply this to ESIF or Prineville, or optimize water scheduling yet.** These are physics-based *scenario* calculations, not measured facility consumption or groundwater withdrawals.

The next step is to supply a **defensible, architecture-specific** $Q^{wet}_t$ (wet heat-rejection duty) and latent fraction, using existing cooling references and/or measured thermal loops. Only after verifying that heat boundary should weather and workload scheduling be coupled to the tower water model.

Physical water-balance references: US DOE, *Cooling Towers: Understanding Key Components of Cooling Towers and How to Improve Water Efficiency* (https://www.energy.gov/sites/default/files/2013/10/f3/waterfs_coolingtowers.pdf); DOE FEMP, *Best Management Practice #10: Cooling Tower Management* (https://www.energy.gov/cmei/femp/best-management-practice-10-cooling-tower-management).
