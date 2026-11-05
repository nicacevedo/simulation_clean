"""Step 18: Water-cooled chiller -> cooling tower heat boundary, illustrative only.

Q_wet = f_ch * E_IT * (1 + 1/COP): chiller load plus compressor heat at the condenser.
Pump, fan, and other auxiliary heat are excluded until their destinations are known.
alpha_lat is a scenario parameter, not a weather-calibrated function.
"""
from math import inf, isclose

DT_H = 1.0
EVAP_L_PER_KWH_TH = 3.6 / 2.45  # latent heat 2.45 MJ/kg, ~1 kg/L


def wet_heat(e_it_kwh, f_ch, cop):
    chiller_load = f_ch * e_it_kwh
    compressor = chiller_load / cop
    q_wet = chiller_load + compressor
    assert isclose(q_wet, f_ch * e_it_kwh * (1 + 1 / cop))  # condenser balance
    return q_wet


def tower(q_wet, alpha_lat, coc):
    assert q_wet >= 0 and 0 <= alpha_lat <= 1 and coc > 1
    evaporation = EVAP_L_PER_KWH_TH * alpha_lat * q_wet
    blowdown = evaporation / (coc - 1)
    return evaporation, evaporation + blowdown


def run(it_kw, f_ch=1.0, cop=5.0, alpha_lat=0.8, coc=4.0):
    q = [wet_heat(p * DT_H, f_ch, cop) for p in it_kw]
    water = [tower(qq, alpha_lat, coc) for qq in q]
    e, m = zip(*water)
    return sum(q), sum(e), sum(m), max(m) / DT_H


A = [1000.0] * 24
B = [800.0] * 12 + [1200.0] * 12

cases = {
    "Step 17 limiting case": run(A, cop=inf, alpha_lat=1.0),
    "Chiller, constant 1 MW": run(A),
    "Chiller, 0.8/1.2 MW": run(B),
    "Half IT heat via chiller": run(A, f_ch=0.5),
}

print(f"{'Case':<26} {'Q_wet kWh_th':>12} {'Evap L':>9} {'Makeup L':>9} {'Peak L/h':>9}")
for name, (q, e, m, peak) in cases.items():
    print(f"{name:<26} {q:>12,.0f} {e:>9,.0f} {m:>9,.0f} {peak:>9,.0f}")

# Step 17 reproduced as the limiting case (no compressor heat, fully latent)
assert all(isclose(u, v, rel_tol=1e-4) for u, v in
           zip(cases["Step 17 limiting case"], (24000, 35265.3, 47020.4, 1959.2)))
# Compressor heat raises tower duty; sensible share can still lower evaporation
assert cases["Chiller, constant 1 MW"][0] > cases["Step 17 limiting case"][0]
assert cases["Chiller, constant 1 MW"][1] < cases["Step 17 limiting case"][1]
# Load shape changes peak makeup only
assert all(isclose(u, v) for u, v in zip(cases["Chiller, constant 1 MW"][:3], cases["Chiller, 0.8/1.2 MW"][:3]))
assert cases["Chiller, 0.8/1.2 MW"][3] > cases["Chiller, constant 1 MW"][3]
# Routing half the heat to a dry route halves everything (linear model)
assert all(isclose(u, 2 * v) for u, v in zip(cases["Chiller, constant 1 MW"], cases["Half IT heat via chiller"]))

print("Latent ratio  Daily makeup L")
for alpha in [0.6, 0.8, 1.0]:
    print(f"{alpha:>12.1f} {run(A, alpha_lat=alpha)[2]:>15,.0f}")
