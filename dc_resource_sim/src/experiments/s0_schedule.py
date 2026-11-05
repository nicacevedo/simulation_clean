"""Step 08: First 24-hour scheduling experiment."""
import numpy as np
from scipy.optimize import linprog

T = 24
phi = 0.20
it_max = 1250.0  # kW, with 1-hour steps
baseline = np.full(T, 1000.0)  # kWh per hour
water_intensity = 0.5  # L/kWh IT

# Synthetic $/kWh; distinct prices avoid tied optima
prices = np.r_[
    0.20 + 0.001 * np.arange(12),
    0.05 + 0.001 * np.arange(12)]

# y[t] = flexible energy processed in hour t
fixed = (1 - phi) * baseline
arrivals = phi * baseline
constraints = dict(
    A_ub=np.tril(np.ones((T, T))),
    b_ub=np.cumsum(arrivals),
    A_eq=np.ones((1, T)),
    b_eq=[arrivals.sum()],
    bounds=[(0, it_max - v) for v in fixed],
    method="highs",
)

# E_dc = a*dt + slope*x, with dt = 1 h
models = {
    "M0": (0.0, 1.0471),
    "M1-fixed": (73.13, 1.0),
}

schedules = {}
print("Model      Base cost   Opt cost   Facility kWh   Water L   Peak kW")
for name, (a, slope) in models.items():
    res = linprog(slope * prices, **constraints)
    assert res.status == 0, f"{name}: {res.message}"
    x = fixed + res.x
    schedules[name] = x

    e_base = a + slope * baseline
    e_opt = a + slope * x
    cost_base, cost_opt = prices @ e_base, prices @ e_opt

    # Four Step 08 checks (the fourth follows the loop)
    assert np.isclose(x.sum(), baseline.sum()), "IT work not completed"
    assert (np.cumsum(res.x) <= np.cumsum(arrivals) + 1e-6).all(), "Work before arrival"
    assert cost_opt < cost_base, "No cost reduction"
    assert np.isclose(e_opt.sum(), e_base.sum()), "Facility energy not conserved"
    assert np.isclose(water_intensity * x.sum(), water_intensity * baseline.sum()), "Water not conserved"

    print(f"{name:<9} {cost_base:>10,.2f} {cost_opt:>10,.2f} {e_opt.sum():>14,.1f}"
          f" {water_intensity * x.sum():>9,.0f} {e_opt.max():>9,.1f}")

assert np.allclose(schedules["M0"], schedules["M1-fixed"]), "Schedules differ"
print("Identical IT schedules: yes")
print("IT schedule (kWh):", np.round(schedules["M0"], 1).tolist())
