## Step 19 — Physics-based evaporation using psychrometrics

Step 18 is complete. The heat-routing and cooling-tower water balances are working correctly. The next step is to replace the assumed latent fraction with one calculated from the physical properties of moist air.

I've prepared a complete Step 19 specification, including the equations, tested Python implementation, expected results, and stopping criteria.

Download step19.md

Save it to `dc_resource_sim/context/step19.md`.

### 1. What we are trying to establish

Step 18 used:

\\[ V^{evap}=\frac{3.6\alpha\_{lat}Q^{wet}}{2.45} \\]

where \\(\alpha\_{lat}\\) was an assumed scenario parameter.

Step 19 calculates evaporation directly from the change in air humidity:

\\[ \boxed{V^{evap}=\dot m\_{da}(\omega\_{out}-\omega\_{in})} \\]

Here \\(\dot m\_{da}\\) is dry-air mass flow and \\(\omega\\) is humidity ratio.

The model also uses a moist-air energy balance to determine the leaving-air condition. The essential distinction is that we no longer need to specify a latent fraction in advance.

ASHRAE supports this approach and emphasizes that identical wet-bulb conditions can produce different sensible and latent heat transfers.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://handbook.ashrae.org\&sz=32)

handbook.ashrae.org



### 2. The important physical limitation

Knowing ambient temperature, relative humidity, and tower heat rejection is not sufficient to determine evaporation uniquely.

We also need airflow and information about the outlet-air condition or cooling-tower performance.

For this initial experiment, use one explicit assumption: the leaving air is saturated.

That gives us a complete, solvable forward model without introducing additional fitted parameters. It remains an illustrative physical scenario, not a calibrated tower model.

### 3. Minimal experiment

Keep the Step 18 central case: 1 MW IT, COP = 5, 1,200 kW of wet heat rejection, and COC = 4.

Use an illustrative airflow of 100,000 kg dry air/h and test three humidity conditions at 25°C.

Expected results — verified reference implementation

| Inlet RH | Evaporation | Makeup    | Derived latent ratio |
| -------- | ----------- | --------- | -------------------- |
| 30%      | 1,681 L/h   | 2,242 L/h | 0.953                |
| 50%      | 1,590 L/h   | 2,120 L/h | 0.902                |
| 70%      | 1,505 L/h   | 2,007 L/h | 0.854                |

The latent ratio now changes naturally with the air conditions. These numbers are conditional on the assumed airflow, exhaust saturation, pressure, and water temperature.

The most informative additional check compares inlet-air conditions with approximately the same wet-bulb temperature but different dry-bulb temperatures and relative humidities. In the tested example, evaporation varies from about 1,382 to 1,797 L/h despite essentially identical entering-air enthalpy.

This shows precisely why a water model based only on wet-bulb temperature can miss important physics.

### 4. Implementation and stopping rule

Create only:

`dc_resource_sim/src/experiments/w2_tower_psychrometric.py`

The attached Markdown contains the complete, executed reference code. It requires only the Python standard library.

The checks cover moisture conservation, heat balance, makeup/blowdown accounting, humidity sensitivity, and airflow sensitivity.

Close Step 19 when these checks pass. Do not add real weather data, optimization, calibration, or another cooling architecture.

### 5. What comes after Step 19?

The next issue is identifying realistic airflow and outlet conditions from equipment documentation, measurements, or a cooling-tower performance model.

Without those, psychrometrics gives us a physically consistent calculation conditional on assumed equipment behavior, not an independently validated prediction of water consumption.

We should avoid presenting the illustrative results as an ESIF or Prineville WUE.

Final recommendation: Implement the single psychrometric model in `step19.md`. Its main research value is replacing an arbitrary latent fraction with an explicit air-side mass and energy balance, while identifying exactly which cooling-system information must be obtained before we can make credible weather-dependent direct-water predictions.

--- 

Context:

# Step 19 — Psychrometric evaporation from an explicit cooling-tower air balance

## Objective

Replace Step 18's **assumed** latent fraction with one **calculated** from entering and leaving moist-air conditions. Keep the Step 18 water-cooled chiller -> open cooling tower architecture. Establish what information is required to map a known condenser heat load into tower evaporation, blowdown, and makeup.

**Only one new standalone script. No new data, fitting, optimization, weather downloads, or edits to Steps 00–18.** This is a thermodynamic scenario, **not a calibrated ESIF or Prineville model**.

## Physical boundary and inputs

Use Step 18's central case: $P^{IT}=1000$ kW, $f_{ch}=1$, $COP=5$, one-hour time steps, so the condenser-to-tower heat duty is $Q^{wet}=1000(1+1/5)=1200$ kWh-thermal per hour. Keep $COC=4$.

At the tower air boundary, specify:

- Inlet dry-bulb temperature $T_{in}$, relative humidity $\phi_{in}$, and total pressure $p$;
- Dry-air mass flow $\dot m_{da}$, measured in **kg dry air/hour**, not kg moist air/hour;
- Either **measured leaving-air temperature and RH** (diagnostic use) or an **explicit assumption for the exhaust condition** (forward scenario).

For the smallest forward test only, assume **saturated tower exhaust**, $\phi_{out}=1$. ASHRAE explains that tower exhaust is often nearly saturated, but not invariably so, especially at light loads. Prescribe $\dot m_{da}=100{,}000$ kg dry air/h, $p=101.325$ kPa, and $T_{liq}=25^\circ$C for both makeup and blowdown. These are **unmeasured illustrative inputs**. The shared makeup/blowdown temperature allows a small liquid-enthalpy correction in the overall steady-state energy balance; there are no drift, storage, fan-heat, or external liquid-stream effects. Atmospheric pressure must be changed for a specific location.

**Critical identifiability point:** Inlet weather and $Q^{wet}$ **alone** do not determine evaporation. In this example, the assumed airflow and saturated-outlet condition supply the missing closure. No universal function of wet-bulb alone is being fitted or claimed.

## Equations

For temperatures $T$ in °C and pressures in kPa, define (illustrative Magnus saturation-pressure approximation for the tested moderate temperatures)

$$
p_{ws}(T)\approx0.61094\exp\!\left(\frac{17.625T}{T+243.04}\right),\quad
\omega(T,\phi,p)=\frac{0.621945\,\phi p_{ws}(T)}{p-\phi p_{ws}(T)}.
$$

Humidity ratio $\omega$ is in kg water vapor per kg dry air. Use the conventional moist-air enthalpy approximation

$$
h(T,\omega)=1.006T+\omega(2501+1.86T)
\quad[\mathrm{kJ/kg_{da}}].
$$

For an hourly heat duty $Q^{wet}$ in kWh-thermal, determine $T_{out}$ by solving the **single scalar equation**

$$
3600Q^{wet}=\dot m_{da}\left[h(T_{out},\omega_{out})-h(T_{in},\omega_{in})
-(\omega_{out}-\omega_{in})c_{p,w}T_{liq}\right],\qquad
\omega_{out}=\omega(T_{out},1,p),
$$

with $c_{p,w}=4.186$ kJ/(kg K). The last term accounts for the liquid-water enthalpy entering with makeup and leaving with blowdown **under the stated equal-temperature assumption**. If this correction is neglected, the common approximation is $3600Q^{wet}\approx\dot m_{da}(h_{out}-h_{in})$; do not present that approximation as exact. A bisection root finder suffices. Reject scenarios without a bracketed solution or with $\omega_{out}\le\omega_{in}$, rather than silently forcing evaporation.

Then calculate directly from the air moisture balance:

$$
\begin{aligned}
V^{evap}&\approx\dot m_{da}(\omega_{out}-\omega_{in})\quad[\mathrm{L/h}],\\
V^{blowdown}&=V^{evap}/(COC-1),\\
V^{makeup}&=V^{evap}+V^{blowdown},\\
\alpha^{apparent}_{lat}&=\frac{2.45\,V^{evap}}{3.6\,Q^{wet}}.
\end{aligned}
$$

Here 1 kg liquid water is approximated as 1 L, and the 2.45 MJ/kg latent heat is retained from Step 18 solely to **compare** calculated evaporation to its assumed $\alpha_{lat}$. An apparent ratio above 1 is possible when the air loses sensible heat while evaporation occurs; **do not clip it**. The residual $Q^{wet}-Q^{lat}$ is not an independently measured sensible-flow component.

## Required small checks

1. **Humidity effect at equal heat and airflow:** at $T_{in}=25^\circ$C, test RH = 30%, 50%, and 70%. Confirm that $V^{evap}$ changes, that the solved air energy balance closes, and that makeup = evaporation + blowdown.
2. **Similar wet-bulb is insufficient:** construct inlet states at 20°C and 30°C with the **same entering-air enthalpy** as 25°C/50% RH. Their wet-bulb temperatures are approximately equal; check that evaporation still differs. This is the most useful physical insight.
3. **Airflow matters:** keep load and ambient condition fixed and compare $\dot m_{da}=80{,}000$ and $120{,}000$ kg dry air/h.
4. **No hidden empirical validation:** print that all states, airflow, saturation assumption, liquid temperature, and heat duty are illustrative, not measured site inputs.

## Implementation

Create **only** `dc_resource_sim/src/experiments/w2_tower_psychrometric.py` using the following tested standard-library reference. Run from repository root:

```bash
python dc_resource_sim/src/experiments/w2_tower_psychrometric.py
```

```python
"""Step 19: Illustrative air-side psychrometric tower balance.

One-hour heat input in kWh thermal; air flow in kg dry air/h.
Not an empirically validated site model.
"""
from math import exp, isclose

P = 101.325           # kPa; sea-level illustrative pressure
M_DA = 100_000.0      # kg dry air/hour; illustrative fan/airflow setting
T_LIQ = 25.0          # C; makeup and blowdown at same temperature
CP_W = 4.186          # kJ/(kg K)
H_FG = 2.45           # MJ/kg; comparative apparent-latent calculation
COC = 4.0
Q_WET = 1000.0 * (1.0 + 1.0 / 5.0)  # kWh thermal/h, Step 18 COP=5


def pws(t):
    return 0.61094 * exp(17.625 * t / (t + 243.04))  # kPa


def omega(t, rh, p=P):
    assert 0 < rh <= 1
    pv = rh * pws(t)
    assert pv < p
    return 0.621945 * pv / (p - pv)


def enthalpy(t, w):
    return 1.006 * t + w * (2501 + 1.86 * t)  # kJ/kg dry air


def rh_at_enthalpy(t, h_target, p=P):
    w = (h_target - 1.006 * t) / (2501 + 1.86 * t)
    assert w > 0
    pv = p * w / (0.621945 + w)
    rh = pv / pws(t)
    assert 0 < rh <= 1
    return rh


def tower(t_in, rh_in, *, q=Q_WET, m_da=M_DA,
          t_liq=T_LIQ, coc=COC, p=P):
    assert q > 0 and m_da > 0 and coc > 1
    wi = omega(t_in, rh_in, p)
    hi = enthalpy(t_in, wi)
    h_liquid = CP_W * t_liq

    def state(t_out):
        wo = omega(t_out, 1.0, p)  # assumed saturated outlet
        ho = enthalpy(t_out, wo)
        evap = m_da * (wo - wi)    # kg/h, approximately L/h
        air_minus_water = (m_da * (ho - hi) - evap * h_liquid) / 3600
        return wo, ho, evap, air_minus_water

    lo, hi_t = 0.0, 60.0  # chosen for moderate-temperature scenarios only
    assert state(lo)[3] < q < state(hi_t)[3], 'Unbracketed tower state'
    for _ in range(70):
        mid = (lo + hi_t) / 2
        if state(mid)[3] < q:
            lo = mid
        else:
            hi_t = mid

    t_out = (lo + hi_t) / 2
    wo, ho, evap, q_check = state(t_out)
    assert wo > wi, 'No positive net evaporation in scenario'
    assert isclose(q_check, q, abs_tol=1e-8)
    blow = evap / (coc - 1)
    makeup = evap + blow
    assert isclose(makeup, evap + blow, rel_tol=1e-12)
    return {
        'out_c': t_out,
        'evap_lph': evap,
        'makeup_lph': makeup,
        'blow_lph': blow,
        'alpha': evap * H_FG / (3.6 * q),
    }


print('RH sensitivity at 25 C, 1200 kWh-th/h, 100000 kg-da/h:')
rh_cases = [tower(25, rh) for rh in (0.3, 0.5, 0.7)]
for rh, z in zip((0.3, 0.5, 0.7), rh_cases):
    print(f'  RH={rh:.0%}: exit={z["out_c"]:.2f} C, '
          f'evap={z["evap_lph"]:.1f} L/h, '
          f'makeup={z["makeup_lph"]:.1f} L/h, '
          f'alpha={z["alpha"]:.3f}')
assert rh_cases[0]['evap_lph'] > rh_cases[1]['evap_lph'] > rh_cases[2]['evap_lph']

h_ref = enthalpy(25, omega(25, 0.5))
print('Same inlet enthalpy, different dry-bulb/RH:')
same_h = []
for t in (20, 25, 30):
    rh = rh_at_enthalpy(t, h_ref)
    z = tower(t, rh)
    same_h.append(z)
    print(f'  {t} C, RH={rh:.1%}: evap={z["evap_lph"]:.1f} L/h, '
          f'alpha={z["alpha"]:.3f}')
assert abs(same_h[0]['out_c'] - same_h[2]['out_c']) < 0.1
assert abs(same_h[0]['evap_lph'] - same_h[2]['evap_lph']) > 100

print('Airflow sensitivity at 25 C / 50% RH:')
for m in (80_000, 100_000, 120_000):
    z = tower(25, 0.5, m_da=m)
    print(f'  {m} kg-da/h: evap={z["evap_lph"]:.1f} L/h, '
          f'makeup={z["makeup_lph"]:.1f} L/h')

print('PASS: psychrometric state, energy balance, evaporation and makeup')
print('All operating conditions and exhaust saturation are hypothetical.')
```

## Expected results (tested)

All scenarios use $Q^{wet}=1200$ kWh thermal/h, $COC=4$, $p=101.325$ kPa and, unless noted, $\dot m_{da}=100{,}000$ kg dry air/h.

| Inlet at 25°C | Outlet saturated temperature | Evaporation | Makeup | Apparent $\alpha_{lat}$ |
|---|---:|---:|---:|---:|
| RH 30% | 27.03°C | 1,681.1 L/h | 2,241.5 L/h | 0.953 |
| RH 50% | 29.13°C | 1,590.2 L/h | 2,120.3 L/h | 0.902 |
| RH 70% | 31.07°C | 1,505.0 L/h | 2,006.6 L/h | 0.854 |

At 25°C/50% RH held constant for 24 hours, makeup is **50,886 L/day**. The corresponding Step 18 number was **45,140 L/day**, because its latent fraction was assumed to be 0.8. This difference is not model validation or evidence that either estimate is site-accurate.

| Same inlet air enthalpy (~50.26 kJ/kg dry air) | RH | Evaporation | Apparent $\alpha_{lat}$ |
|---|---:|---:|---:|
| 20°C | 81.4% | 1,381.7 L/h | 0.784 |
| 25°C | 50.0% | 1,590.2 L/h | 0.902 |
| 30°C | 29.8% | 1,797.2 L/h | 1.019 |

The inlet states have **approximately equal wet-bulb temperatures**, yet distinct evaporation. An apparent ratio greater than 1 reflects an offsetting negative sensible contribution under the chosen convention; it is not a numerical error.

At 25°C/50% RH, airflow of 80k, 100k and 120k kg dry air/h gives approximately 1,551, 1,590 and 1,635 L/h evaporation, respectively. Therefore, the airflow/exhaust closure is a relevant input, not something that can be inferred from ambient humidity alone.

## Stopping rule

Close Step 19 when all checks pass and the script clearly states the unmeasured **airflow, outlet saturation, pressure, and makeup/blowdown temperature** assumptions. Do not fit a weather-only water coefficient, present a site WUE, infer groundwater extraction, or connect the model to optimization yet.

**Next decision:** assess whether we have actual equipment-level airflow/exhaust or tower design data (or a justified Merkel/tower-performance model). Without those inputs, retain the transparent tower scenarios and avoid claiming realistic weather-driven tower evaporation predictions. Direct evaporative air cooling is a separate archetype, not a parameter change to this chiller/tower system.

## Sources / verification

- ASHRAE, *2024 HVAC Systems and Equipment*, Chapter 40, **Cooling Towers**: https://handbook.ashrae.org/Handbooks/S24/SI/S24_Ch40/S24_Ch40_si.aspx — air normally leaves nearly saturated; humidity ratio change determines evaporation; identical wet-bulb conditions can yield different sensible/latent shares.
- ASHRAE, *2025 Fundamentals*, Chapter 1, **Psychrometrics**: https://handbook.ashrae.org/Handbooks/F25/SI/F25_Ch01/F25_Ch01_si.aspx — moist-air humidity ratio, enthalpy, saturation and atmospheric pressure relations.
- U.S. DOE FEMP, **Cooling Tower Management**: https://www.energy.gov/cmei/femp/best-management-practice-10-cooling-tower-management — water makeup, evaporation, blowdown, drift and cycles of concentration.
