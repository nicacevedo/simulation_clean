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
