"""Step 23: illustrative W0 direct-consumption accounting, not site intake."""
from math import isclose

DT_H = 1.0
W0_L_PER_KWH_IT = 0.5  # assumed, not calibrated
WATER_BASIS = "onsite_direct_consumption_proxy"


def summarize(it_kw):
    it_kwh = [p * DT_H for p in it_kw]
    water_l = [W0_L_PER_KWH_IT * e for e in it_kwh]
    assert all(p >= 0 for p in it_kw)
    assert all(isclose(v, W0_L_PER_KWH_IT * e) for v, e in zip(water_l, it_kwh))
    return sum(it_kwh), sum(water_l), max(v / DT_H for v in water_l)


A = summarize([1000.0] * 24)
B = summarize([800.0] * 12 + [1200.0] * 12)

assert isclose(A[0], B[0]) and isclose(A[0], 24000.0)
assert isclose(A[1], B[1]) and isclose(A[1], 12000.0)
assert isclose(A[2], 500.0) and isclose(B[2], 600.0)

print("Water basis:", WATER_BASIS)
for label, (energy, water, peak) in (("A constant", A), ("B variable", B)):
    print(f"{label}: IT={energy:.0f} kWh/day; "
          f"W0={water:.0f} L/day; peak W0 rate={peak:.0f} L/h")
print("PASS: W0 conserved under equal IT energy; peak rate changes")
