# Step 22 — IT electricity → heat handled by server air

**Purpose.** Establish the smallest explicit thermal boundary between M0 IT electricity and the heat carried away by server air. **Do not model a cooling device, water use, fan electricity, weather, or optimization.**

## 1. What Step 21 already established

- The hypothetical reference has `P_IT = 1,000 kW`; M0 predicts `P_DC = 1,047.1 kW` and **aggregate** non-IT power of `47.1 kW`. The 47.1 kW cannot be independently assigned to fans, chillers, or pumps.
- At steady state, IT electrical input is approximately converted into heat, but **not necessarily into heat carried by room air**, and certainly not automatically into tower heat rejection or evaporative latent duty.
- Step 20 used a server air-side heat balance with an assumed 15°C supply-to-exhaust rise. Step 22 isolates and checks that balance, not the psychrometric cooling system.

## 2. Add one thermal routing variable

For a steady-state, one-hour model with no heat storage or nonthermal export:

$$
P^{IT}_t=\dot Q^{air}_t+\dot Q^{other}_t,\qquad
\dot Q^{air}_t=f_{air}P^{IT}_t,\qquad
\dot Q^{other}_t=(1-f_{air})P^{IT}_t.
$$

Here $f_{air}$ is **the assumed share of IT heat delivered to the server airstream**, not the wet-cooling share and not a measured property. The `other` route could represent liquid cooling or another explicitly separate heat path. Initial case: $f_{air}=1$. We exclude heat storage; if it matters, a transient balance must later include $dU/dt$.

Only after choosing that air-stream boundary, calculate airflow:

$$
\dot m_{da,t}=\frac{3600\,\dot Q^{air}_t}
{c_{p,ma}\,(T_{return}-T_{supply})}
\quad[\mathrm{kg\ dry\ air/h}].
$$

Use a **fixed illustrative** $\Delta T_{server}=15^\circ\mathrm C$ and $c_{p,ma}=1.006+1.86(0.010)=1.0246\ \mathrm{kJ/(kg\ dry\ air\,K)}$. The assumed humidity ratio `0.010 kg/kg dry air` is used only to fix moist-air specific heat; **this is not a weather or humidity/evaporation experiment**. Do not calculate fan energy from airflow.

## 3. Three small checks

| Scenario | IT power (kW) | IT energy / day (kWh) | Air heat energy / day (kWh thermal) | Peak air heat rate (kW thermal) | Peak dry-air flow (kg/h) |
|---|---:|---:|---:|---:|---:|
| A: 1 MW for 24 h, $f_{air}=1$ | 1,000 constant | 24,000 | 24,000 | 1,000 | 234,238 |
| B: 800 kW × 12 h, 1,200 kW × 12 h, $f_{air}=1$ | 800 / 1,200 | 24,000 | 24,000 | 1,200 | 281,085 |
| C: 1 MW for 24 h, $f_{air}=0.5$ | 1,000 constant | 24,000 | 12,000 | 500 | 117,119 |

For C, the **other heat route carries another 12,000 kWh thermal/day**. It has not disappeared. A and B must have identical total IT and air heat energy but different peak rates/flow. At $f_{air}=1$, the A airflow is close to the independent Step 20 numerical example (~234,242 kg dry air/h) **because that example uses the same air-side balance**; agreement is not independent validation.

## 4. Implementation

Create **only** `dc_resource_sim/src/experiments/it_heat_airflow_first.py`, or use one small self-contained assertion block. Keep existing scripts unchanged; standard Python is sufficient.

```python
from math import isclose

DT_H = 1.0
DELTA_T_C = 15.0
OMEGA = 0.010  # kg water/kg dry air: illustrative constant
CP_MA = 1.006 + 1.86 * OMEGA  # kJ/(kg dry air K)


def check_profile(load_kw, f_air):
    q_air = [f_air * p for p in load_kw]
    q_other = [(1 - f_air) * p for p in load_kw]
    flow = [3600 * q / (CP_MA * DELTA_T_C) for q in q_air]
    for p, qa, qo, m in zip(load_kw, q_air, q_other, flow):
        assert isclose(p, qa + qo, abs_tol=1e-9)
        assert isclose(qa, m * CP_MA * DELTA_T_C / 3600,
                       abs_tol=1e-9)
    return (sum(load_kw) * DT_H, sum(q_air) * DT_H,
            sum(q_other) * DT_H, max(q_air), max(flow))


A = check_profile([1000.0] * 24, 1.0)
B = check_profile([800.0] * 12 + [1200.0] * 12, 1.0)
C = check_profile([1000.0] * 24, 0.5)

assert isclose(A[0], 24000) and isclose(B[0], 24000)
assert isclose(A[1], B[1]) and isclose(A[1], 24000)
assert isclose(A[3], 1000) and isclose(B[3], 1200)
assert isclose(A[4], 234237.7513, rel_tol=1e-7)
assert isclose(B[4], 281085.3016, rel_tol=1e-7)
assert isclose(C[1], 12000) and isclose(C[2], 12000)
assert isclose(C[4], 117118.8757, rel_tol=1e-7)

for label, values in [('A constant', A), ('B variable', B), ('C split route', C)]:
    print(label, 'IT kWh, air kWhth, other kWhth, '
          'peak air kWth, peak kgda/h:', tuple(round(v, 1) for v in values))
print('PASS: thermal routing and server-airflow balances')
```

## 5. Stop and interpret

Close Step 22 when all balances pass and the following interpretation is explicit:

> IT electricity supplies approximately equal thermal energy at steady state, but the amount entering **server air** depends on a declared heat-routing assumption. Airflow then depends on the chosen temperature rise and moist-air heat capacity. Neither airflow nor heat alone determines cooling electricity, water evaporation, process intake, or cooling feasibility.

No new datasets, wet-bulb calculations, COP, fan law, WUE, or optimization. **Step 23** will return to W0 and establish exactly what its constant direct-water coefficient counts, using the same two load profiles and distinct daily total versus peak water rate.

---

Context:

## Step 22 — From IT electricity to heat and server airflow

Step 21 is complete. The boundary audit confirmed that our models are internally consistent when treated separately, but that M0's aggregate overhead cannot be combined directly with an independently assumed chiller or fan-power model.

The next step should introduce only one physical relationship: how IT heat is carried away by the server airstream.

I've prepared the complete Step 22 specification, with tested reference code, expected results, assertions, and a stopping rule.

Download Step 22 — IT Heat and Airflow (.md)

Save it as `dc_resource_sim/context/step22.md`.

### 1. What we want to understand

Start with the steady-state IT heat balance:

\\[ P^{IT}=\dot Q^{air}+\dot Q^{other} \\]

where \\(\dot Q^{air}\\) is heat carried by server air and \\(\dot Q^{other}\\) is heat leaving through other paths, such as liquid cooling.

Define one routing parameter:

\\[ \dot Q^{air}=f\_{air}P^{IT}. \\]

Initially assume \\(f\_{air}=1\\): all IT heat is transferred to server air.

Then calculate the required airflow:

\\[ \boxed{\dot m\_{da}=\frac{3600\dot Q^{air}}{c\_{p,ma}\Delta T\_{server}}} \\]

This gives dry-air mass flow in kg/h when heat rate is in kW and heat capacity is in kJ/(kg dry air·K).

The airflow depends on two assumptions: the fraction of heat entering the air and the allowable temperature rise across the servers.

### 2. The smallest useful experiment

Use the same IT profiles as before, with a 15°C server-air temperature rise.

| Test                                 | Daily IT heat      | Peak heat carried by air | Peak airflow |
| ------------------------------------ | ------------------ | ------------------------ | ------------ |
| A — Constant 1 MW                    | 24,000 kWh thermal | 1,000 kW                 | 234,238 kg/h |
| B — 0.8/1.2 MW                       | 24,000 kWh thermal | 1,200 kW                 | 281,085 kg/h |
| C — Half the heat goes to server air | 24,000 kWh thermal | 500 kW                   | 117,119 kg/h |

Illustrative results using fixed moist-air heat capacity and a 15°C temperature rise. Case C retains the other 12,000 kWh thermal/day in a separate heat-rejection path.

The important insight is that equal daily IT energy does not imply equal peak thermal duty or airflow requirements.

And routing less heat into room air does not eliminate that heat—it changes the cooling-system boundary responsible for removing it.

### 3. What to confirm from previous steps

- Step 21: M0 still predicts 1,047.1 kW of facility electricity for a hypothetical 1 MW IT load. Its 47.1 kW overhead is not added to the server-air heat calculation.
- Step 20: Its approximately 234,242 kg/h airflow result is consistent with this formulation because the same air-side heat balance was used. This is a consistency check, not independent validation.
- Steps 17–19: No tower heat-rejection or evaporation equations are needed here.

### 4. Implementation and stopping rule

Create only:

`dc_resource_sim/src/experiments/it_heat_airflow_first.py`

The attached specification contains the complete reference code, which I tested successfully.

Close Step 22 when the script verifies that:

1. All IT heat is accounted for across the declared heat paths.
2. Equal daily energy produces equal daily total heat.
3. Changing workload distribution changes peak airflow.
4. Changing the heat-routing fraction changes airflow without violating energy conservation.

Do not introduce cooling electricity, fan laws, water evaporation, weather variability, or optimization yet.

## What should Step 23 address?

Return to W0:

\\[ V^{direct,con}=w_0E^{IT}. \\]

We should establish precisely what this constant coefficient represents, why total direct water remains unchanged when total IT energy is fixed, and why peak hourly water demand can still change.

That is a small, logical addition before reconnecting the heat and water models.

My recommendation: Step 22 should be limited to understanding the heat and airflow boundary. We already have the mathematical foundations for more sophisticated cooling; what matters now is understanding each physical relationship before combining them.