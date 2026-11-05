"""Step 22: IT electricity -> heat carried by server air (illustrative, steady state).

f_air, temperature rise and humidity ratio are assumptions, not measurements.
No cooling device, water, fan power or weather.
"""
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
print('Heat entering server air depends on the declared f_air; airflow then depends on the chosen\n'
      'temperature rise and moist-air heat capacity. Neither sets cooling electricity, evaporation,\n'
      'process intake, or cooling feasibility.')
