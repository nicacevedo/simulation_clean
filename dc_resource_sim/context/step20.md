# Step 20 — First direct-evaporative air-side water model (W2-Air)

## Why this is the next step

**Steps 17–19 are closed.** They verify a chiller/cooling-tower heat and water balance, but cannot be calibrated with the currently available data because tower airflow, exhaust state and water operation are not measured. Do not keep refining unidentifiable tower inputs.

The original research plan also distinguishes a **direct-evaporative outside-air architecture** (Prineville-type) from a cooling tower. Meta publicly documents outdoor air, a mixing room, and an evaporative misting/humidification chamber. This step establishes its simplest, **different** water physics before adding treatments, facility optimization or time-series simulations.

**Question:** for a chosen outside-air state, maximum supply temperature and server airflow requirement, does direct evaporation work, and how much water becomes vapor?

**Scope:** one standalone script, standard library, no additional data, no fitting, no new optimizations, no changes to Steps 00–19.

## Physical assumptions and boundary

- Direct evaporative conditioning of **outside air**, not a cooling tower: **do not use COC or the chiller condenser heat formula**.
- Ignore air mixing, heat recovery, dehumidification, pump/fan power, additional refrigeration and liquid-water treatment for this first experiment.
- Assume the entering air is the outside-air state $(T_{in}, RH_{in})$ at $p=101.325$ kPa (illustrative, **not actual Prineville site pressure**).
- Maximum desired supply-air dry-bulb $T_{sup,max}=25^\circ$C; maximum direct-evaporative saturation effectiveness $\epsilon_{max}=0.8$. Both are chosen scenarios, not site equipment specifications.
- Illustrative server IT electricity $P_{IT}=1000$ kW is fully transferred to the server airstream. Assume a supply-to-exhaust temperature rise $\Delta T_{server}=15^\circ$C for sizing dry-air mass flow. Ignore other electrical/thermal sources.
- Water enters evaporative stage at $T_{water}=25^\circ$C; its liquid enthalpy is included in the evaporative-stage energy balance, as in Step 19.
- Every reported water number is **evaporated water** (approximate consumption); do not call it total freshwater makeup, municipal withdrawal, or groundwater extraction without treatment/recovery/source data.

## Core equations

Reuse Step 19's $p_{ws}(T)$, $\omega(T,RH,p)$ and $h(T,\omega)$ psychrometric functions.

Find the saturation-equilibrium dry-bulb $T_{eq}$ for the inlet air by solving

$$
h(T_{eq},\omega_s(T_{eq}))-h_{in}=
[\omega_s(T_{eq})-\omega_{in}]c_{p,w}T_{water}.
$$

If $T_{in}\le T_{sup,max}$, turn off evaporation ($T_{sup}=T_{in}$). Otherwise the required saturation effectiveness is

$$
\epsilon_{req}=\frac{T_{in}-T_{sup,max}}{T_{in}-T_{eq}}.
$$

If $\epsilon_{req}>\epsilon_{max}$, **report infeasible**: this one-stage evaporative system cannot meet the chosen supply temperature. Do not force the temperature, claim zero water, or silently assume a different cooling system. If feasible, set $T_{sup}=T_{sup,max}$ and solve the adiabatic liquid-corrected energy balance for $\omega_{sup}$:

$$
h(T_{sup},\omega_{sup})-h_{in}
=(\omega_{sup}-\omega_{in})c_{p,w}T_{water}.
$$

Connect airflow to IT heat through the server air-side sensible balance:

$$
\dot m_{da}=\frac{3600P_{IT}}{[1.006+1.86\omega_{sup}]\Delta T_{server}}
\quad [\mathrm{kg_{dry\ air}/h}].
$$

Then calculate **evaporation only**:

$$
V^{evap}\simeq\dot m_{da}(\omega_{sup}-\omega_{in})\quad[\mathrm{L/h}].
$$

The humidified supply air must satisfy $0\le RH_{sup}\le1$ and $\omega_{sup}\ge\omega_{in}$. Keep all flows and temperatures as illustrative steady-state, not measured operations. These simplified design assumptions are separate from actual facility control logic.

## Four small test conditions

Use $P_{IT}=1000$ kW, $T_{sup,max}=25^\circ$C, $\Delta T_{server}=15^\circ$C, $\epsilon_{max}=0.8$. Tested results:

| Outside air | Expected mode | Evaporation | Key check |
|---|---|---:|---|
| 20°C, 50% RH | Dry | 0 L/h | No water is needed to meet the supply-temperature ceiling |
| 30°C, 30% RH | Wet | 489.4 L/h | Humidity/energy balances and $\epsilon_{req}\simeq0.418$ |
| 30°C, 50% RH | Wet | 489.4 L/h | More humidity increases needed effectiveness, not necessarily water for fixed sensible cooling duty |
| 30°C, 70% RH | **Infeasible** | n/a | At $\epsilon_{max}=0.8$, minimum supply is about 26.4°C |
| 35°C, 30% RH | Wet | 975.0 L/h | Greater air-temperature reduction increases evaporation |

For the 30°C/30% RH case, derived airflow is about **234,242 kg dry air/h**. This is a result of the illustrative server temperature-rise constraint, not measured fan airflow.

## Implementation

Create **only** `dc_resource_sim/src/experiments/w2_air_first.py` by copying the tested code below. Run:

```bash
python dc_resource_sim/src/experiments/w2_air_first.py
```

```python
"""Step 20: First direct-evaporative air-side water model (scenarios only).

No real Prineville facility calibration. Standard library only.
IT power is the sensible heat gained by server air in this idealized case.
"""
from math import exp, isclose

PRESSURE_KPA = 101.325
T_WATER_C = 25.0
CP_W = 4.186  # kJ/(kg K)
SUPPLY_MAX_C = 25.0
SERVER_RISE_C = 15.0
MAX_WB_EFFECTIVENESS = 0.80
IT_KW = 1000.0


def pws(t):
    return 0.61094 * exp(17.625 * t / (t + 243.04))


def humidity_ratio(t, rh):
    assert 0 < rh <= 1
    vapor_pressure = rh * pws(t)
    assert vapor_pressure < PRESSURE_KPA
    return 0.621945 * vapor_pressure / (PRESSURE_KPA - vapor_pressure)


def enthalpy(t, w):
    return 1.006 * t + w * (2501.0 + 1.86 * t)


def outlet_humidity(t_out, w_in, h_in):
    # h_out-h_in = (w_out-w_in)*cp_water*T_water (adiabatic stage)
    numerator = h_in - 1.006 * t_out - w_in * CP_W * T_WATER_C
    denominator = 2501.0 + 1.86 * t_out - CP_W * T_WATER_C
    return numerator / denominator


def equilibrium_temperature(t_in, rh_in):
    w_in = humidity_ratio(t_in, rh_in)
    h_in = enthalpy(t_in, w_in)

    def residual(t):
        return humidity_ratio(t, 1.0) - outlet_humidity(t, w_in, h_in)

    lo, hi = -30.0, t_in
    assert residual(lo) < 0 <= residual(hi), 'No bracketed saturation limit'
    for _ in range(70):
        mid = (lo + hi) / 2
        if residual(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def direct_evap(t_in, rh_in, *, it_kw=IT_KW):
    w_in = humidity_ratio(t_in, rh_in)
    h_in = enthalpy(t_in, w_in)
    t_eq = equilibrium_temperature(t_in, rh_in)
    if t_in <= SUPPLY_MAX_C:
        t_out, effectiveness, mode = t_in, 0.0, 'dry'
    else:
        effectiveness = (t_in - SUPPLY_MAX_C) / (t_in - t_eq)
        if effectiveness > MAX_WB_EFFECTIVENESS + 1e-10:
            return dict(mode='infeasible', t_eq_c=t_eq,
                        needed_effectiveness=effectiveness,
                        best_supply_c=t_in - MAX_WB_EFFECTIVENESS * (t_in - t_eq))
        t_out, mode = SUPPLY_MAX_C, 'wet'

    w_out = outlet_humidity(t_out, w_in, h_in)
    assert w_out >= w_in - 1e-10
    assert w_out <= humidity_ratio(t_out, 1.0) + 1e-10
    assert isclose(enthalpy(t_out, w_out) - h_in,
                   (w_out - w_in) * CP_W * T_WATER_C, abs_tol=1e-9)

    # IT heat carried away by server air with an assumed 15 C aisle rise.
    cp_moist_air = 1.006 + 1.86 * w_out  # kJ/(kg dry air K)
    m_da = 3600.0 * it_kw / (cp_moist_air * SERVER_RISE_C)
    evaporation_lph = max(0.0, m_da * (w_out - w_in))
    assert isclose(m_da * cp_moist_air * SERVER_RISE_C / 3600.0,
                   it_kw, rel_tol=1e-12)
    return dict(mode=mode, t_eq_c=t_eq, supply_c=t_out,
                effectiveness=effectiveness, air_kgda_h=m_da,
                evaporation_lph=evaporation_lph)


cases = [(20.0, 0.50), (30.0, 0.30), (30.0, 0.50),
         (30.0, 0.70), (35.0, 0.30)]
results = {}
for temp, rh in cases:
    z = direct_evap(temp, rh)
    results[(temp, rh)] = z
    print(f'{temp:g} C / {rh:.0%} RH: {z}')

assert results[(20.0, 0.50)]['mode'] == 'dry'
assert results[(20.0, 0.50)]['evaporation_lph'] < 1e-8
assert results[(30.0, 0.30)]['mode'] == 'wet'
assert isclose(results[(30.0, 0.30)]['evaporation_lph'], 489.36647, abs_tol=0.01)
assert results[(30.0, 0.70)]['mode'] == 'infeasible'
assert results[(30.0, 0.70)]['best_supply_c'] > SUPPLY_MAX_C
assert results[(35.0, 0.30)]['evaporation_lph'] > results[(30.0, 0.30)]['evaporation_lph']
print('PASS: zero-water dry operation, balances, feasible wet operation and infeasible humid case.')
print('All temperatures, IT load, air-rise, equipment effectiveness and water temperature are hypothetical.')
print('Evaporation estimates consumptive loss, NOT municipal makeup or groundwater withdrawal.')
```

## Stopping rule

Close Step 20 once the script reproduces the expected cases and all asserts pass. Record explicitly:

1. Zero direct evaporation when outside air already meets the target.
2. Nonzero evaporation when wet cooling is needed and physically feasible.
3. An **infeasible** result when humid air prevents meeting the supply temperature with the assumed equipment.
4. The air-side energy, humidity and server-heat balances close; **no site water-volume calibration is claimed**.

**Do not** yet introduce hourly Prineville weather, RO water recovery, annual meter fitting, optimization, a groundwater conversion or treatment-specific water allocation. Do not add arbitrary nonlinear regressions.

## Next, only after Step 20

For W2-Air, identify a defensible air-flow/control range and evaporative effectiveness, then add a separately parameterized water supply/treatment balance. The available Prineville **monthly city billing** can eventually constrain annual/seasonal supply-water accounting, but cannot validate the per-hour physics against IT workload without synchronized measurements. The cooling-tower and W2-Air branches must remain distinct.

## Authoritative technical sources

- EnergyPlus, *Engineering Reference: Evaporative Coolers*, direct evaporative energy balance and wet-bulb effectiveness: https://energyplus.readthedocs.io/en/stable/guides/engineering-reference/16.3-evaporative-coolers.html
- Meta Engineering (2024), *Simulator-based reinforcement learning for data center cooling optimization*, outside-air misting and airflow controls: https://engineering.fb.com/2024/09/10/data-center-engineering/simulator-based-reinforcement-learning-for-data-center-cooling-optimization/
- The project's existing Step 19 psychrometric formulation and Research Plan, W2-Air cooling archetype.


---

Context:

## Project review — Steps 00–19

Step 19 is complete and should be closed. The psychrometric model reproduces the expected results, and its energy, moisture, and makeup-water balances pass.

The next experiment should therefore be Step 20, not another Step 19.

### 1. Where the project stands

After reviewing the reported results, the original research plan, the notebooks, and `runs4.zip`, I would summarize our progress as follows.

| Research component     | Current conclusion                                                                                       | Status                                  |
| ---------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| Facility electricity   | M2a-fixed is the best-supported simple model across the selected ESIF holdouts                           | Empirically evaluated                   |
| Power-aware scheduling | Model accuracy can affect capacity feasibility, but tested cost differences were very small              | Demonstrated in controlled optimization |
| Grid-related water     | Scheduling changes accounting-based water estimates, but the ranking is sensitive to small hourly errors | Scenario evidence only                  |
| Cooling-tower water    | Steps 17–19 establish heat, evaporation, blowdown, and makeup balances                                   | Physically consistent, not calibrated   |
| Groundwater impacts    | Water sources, withdrawals, return flows, and groundwater response remain unmodeled                      | Main research objective still ahead     |

The most important gap is no longer the equations themselves. It is connecting the correct physical model to a real cooling architecture and defensible equipment inputs.

For example, Step 19 predicts approximately 50,887 L/day of tower makeup under one illustrative configuration. That is a valid conditional calculation, but it cannot be interpreted as measured water use at ESIF or Prineville.

### 2. My assessment of Step 19

Three results are particularly valuable:

- Evaporation can be calculated from air humidity changes instead of an assumed latent fraction.
- Two inlet-air conditions with nearly identical wet-bulb temperatures can produce substantially different evaporation.
- A physics-based water balance still requires airflow and equipment-performance information.

The apparent latent ratio of 1.019 in one case is not automatically an error: air-side sensible and latent contributions can have opposite signs.

I would not add more sensitivity cases to the cooling-tower model yet. We have established its core relationships. Further sophistication without tower operating data would mainly introduce additional assumptions.

## Step 20 — First direct-evaporative cooling model (W2-Air)

This is my recommended next step.

The original research plan distinguishes cooling towers from the outside-air evaporative cooling architecture relevant to Prineville.

That distinction matters. Meta describes a system that brings outside air through a mixing room, filtration and evaporative misting chamber before supplying server areas. It is not equivalent to the water-cooled chiller and cooling tower modeled in Steps 17–19.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://engineering.fb.com\&sz=32)

Engineering at Meta



### The central question

Given outdoor temperature, humidity, IT heat load, and a required supply-air temperature, how much water must evaporate—and when is direct evaporative cooling insufficient?

This is more relevant to the Prineville water data than continuing to refine a hypothetical cooling tower.

### 3. The model

Use the same psychrometric functions validated in Step 19, but change the physical architecture.

Outside air

Dry-bulb temperature and relative humidity

Direct evaporative cooling

Water evaporation lowers air temperature

Supply air and servers

Airflow carries away IT heat

Unlike a cooling tower, the evaporating water directly conditions the air delivered to the servers.

Three relationships are enough.

1\. Cooling feasibility

\\[ \epsilon\_{req}=\frac{T\_{in}-T\_{supply}}{T\_{in}-T\_{eq}} \\]

where \\(T\_{eq}\\) is the saturation-equilibrium temperature obtained from the psychrometric balance.

If the required effectiveness exceeds the installed equipment's maximum effectiveness, the selected supply temperature is infeasible using this cooling method alone.

2\. Airflow from IT heat

\\[ \dot m\_{da}=\frac{3600P^{IT}} {c\_{p,air}\Delta T\_{server}} \\]

This gives airflow from an assumed allowable supply-to-server-exhaust temperature rise, rather than choosing an arbitrary airflow independently of the IT load.

3\. Water evaporation

\\[ \boxed{V^{evap}=\dot m\_{da}(\omega\_{supply}-\omega\_{in})} \\]

The outlet humidity is calculated from the adiabatic moist-air energy balance, including the liquid-water enthalpy correction. This is consistent with the approach documented in EnergyPlus.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://energyplus.readthedocs.io\&sz=32)

energyplus.readthedocs.io



### 4. Minimal experiment

Use one hypothetical 1 MW facility, a 25°C maximum supply temperature, 15°C server air-temperature rise, and maximum evaporative effectiveness of 0.8.

I executed a reference implementation using these assumptions.

| Outdoor condition | Cooling mode                            | Evaporation |
| ----------------- | --------------------------------------- | ----------- |
| 20°C, 50% RH      | Dry / no misting needed for temperature | 0 L/h       |
| 30°C, 30% RH      | Evaporative                             | 489 L/h     |
| 30°C, 50% RH      | Evaporative                             | 489 L/h     |
| 30°C, 70% RH      | Infeasible                              | —           |
| 35°C, 30% RH      | Evaporative                             | 975 L/h     |

The equality of evaporation in the two 30°C feasible cases is a consequence of fixing the same supply temperature and idealized sensible-cooling duty; humidity instead changes the required effectiveness.

The most important result is the infeasible case. At 30°C and 70% RH, the assumed evaporative system cannot reach 25°C. An optimization model must not presume that wet cooling can satisfy every weather condition.

### 5. Implementation

I prepared and tested the complete specification.

Download step20.md

Save it as `dc_resource_sim/context/step20.md`.

It creates only:

`dc_resource_sim/src/experiments/w2_air_first.py`

The specification contains the tested Python code, equations, reference results and assertions. It requires only the Python standard library.

The stopping rule is straightforward: reproduce the dry, wet and infeasible cases; verify moisture and energy conservation; and explicitly distinguish evaporated water from freshwater supply requirements.

### 6. What remains after Step 20?

The next priority should be relating airflow, temperature setpoints, and evaporative effectiveness to defensible equipment specifications. We must then account separately for purification losses, recovered water, and supply sources before relating model outputs to Prineville's municipal water records.

We should not yet fit hourly water demand to monthly bills or claim groundwater impacts from modeled evaporation.

## Final recommendation

Close Step 19. Stop refining the hypothetical cooling tower until we have equipment evidence. Proceed with Step 20, the first direct-evaporative W2-Air model.

This is the more valuable direction because it:

1. Introduces a genuinely different and relevant cooling architecture.
2. Connects IT heat, airflow, cooling feasibility, and evaporation.
3. Identifies when water-based cooling is physically possible.
4. Moves toward interpreting the Prineville water data without confusing tower makeup, evaporation, municipal withdrawal, and groundwater consumption.

The broader research objective remains unchanged: build the simplest defensible electricity–water model that can eventually support geographically distributed data-center planning and groundwater-aware decisions.