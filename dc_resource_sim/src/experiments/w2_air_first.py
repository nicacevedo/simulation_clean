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
