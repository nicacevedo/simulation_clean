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
print('Illustrative, not measured site inputs: inlet states, airflow, saturated '
      'exhaust, pressure, makeup/blowdown temperature, and heat duty.')
