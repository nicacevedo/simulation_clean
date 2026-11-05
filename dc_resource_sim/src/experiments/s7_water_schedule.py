"""Step 15: Does grid-water information change the schedule? (M0, W0)

Grid water uses modeled hourly AVERAGE consumption factors (MISO), not marginal
responses, so water savings here are accounting-based, not physical.
"""
import numpy as np
import pandas as pd
from scipy.optimize import linprog

T = 24
phi = 0.20
it_max = 1250.0  # kW, with 1-hour steps
baseline = np.full(T, 1000.0)  # kWh per hour
k = 1.0471  # M0: E_dc = k * x
w0 = 0.5  # W0: L/kWh IT (illustrative)

# Springfield/MISO, 2023-07-01 UTC; written by src/data/price_day.py
df = pd.read_csv("dc_resource_sim/runs/price_water_24h.csv")
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
expected = pd.date_range("2023-07-01", periods=T, freq="h", tz="UTC")
assert (df.timestamp_utc.to_numpy() == expected.to_numpy()).all()
assert df.notna().all().all()
p = df["price_usd_per_kwh"].to_numpy(float)
g = df["grid_water_consumption_l_per_kwh"].to_numpy(float)

fixed = (1 - phi) * baseline
arrivals = phi * baseline


def solve_schedule(c):
    """Step 08 LP: min c @ x with cumulative arrivals and daily completion."""
    res = linprog(
        c,
        A_ub=np.tril(np.ones((T, T))),
        b_ub=np.cumsum(arrivals),
        A_eq=np.ones((1, T)),
        b_eq=[arrivals.sum()],
        bounds=[(0, it_max - v) for v in fixed],
        method="highs",
    )
    assert res.status == 0, res.message
    assert (np.cumsum(res.x) <= np.cumsum(arrivals) + 1e-6).all(), "Work before arrival"
    x = fixed + res.x
    assert np.isclose(x.sum(), baseline.sum()), "IT work not completed"
    return x


x_cost = solve_schedule(k * p)
# Direct water w0 is constant per kWh, so only g's variation can move the schedule.
if g.max() - g.min() > 1e-10:
    x_water = solve_schedule(w0 + k * g)
else:
    print("Grid-water factor is constant: water is schedule-invariant.")
    x_water = x_cost.copy()

print(f"Grid water: {g.min():.3f}-{g.max():.3f} L/kWh (range {g.max() - g.min():.3f})")
print("Schedule      Cost $   Direct L     Grid L    Total L")
for name, x in [("Baseline", baseline), ("Cost", x_cost), ("Water", x_water)]:
    direct = w0 * x.sum()
    grid_water = (g * k * x).sum()
    cost = (p * k * x).sum()
    print(f"{name:<9} {cost:>9,.2f} {direct:>10,.1f} {grid_water:>10,.1f} {direct + grid_water:>10,.1f}")

assert np.isclose(w0 * x_cost.sum(), w0 * x_water.sum()), "Direct water should be schedule-invariant"
print("Same schedule (cost vs water):", np.allclose(x_cost, x_water))
print("Cost-opt IT (kWh): ", np.round(x_cost, 0).astype(int).tolist())
print("Water-opt IT (kWh):", np.round(x_water, 0).astype(int).tolist())

# Step 16 — Sensitivity of the water-schedule advantage.
# A common additive or positive multiplicative error in g cannot reverse the ranking
# (equal total energy); only hourly-pattern errors can. Bounds below are worst cases,
# not probabilities.
dx = x_cost - x_water
assert np.isclose(dx.sum(), 0)  # Same total IT energy
gain_l = k * np.dot(g, dx)
sensitivity = k * np.abs(dx).sum()
epsilon = gain_l / sensitivity
print(f"Modeled water advantage: {gain_l:.2f} L")
print(f"Absolute schedule difference: {np.abs(dx).sum():.0f} kWh")
print(f"Reversal threshold: {epsilon:.4f} L/kWh ({epsilon / g.mean():.1%} of mean factor)")

# Worst-case pairwise advantage under illustrative error bounds
for bound in [0.01, 0.02, 0.03]:
    worst_gain = gain_l - bound * sensitivity
    print(f"±{bound:.2f} L/kWh: worst-case advantage = {worst_gain:.1f} L")
