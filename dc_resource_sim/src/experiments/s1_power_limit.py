"""Step 09: Decision value of a facility-power limit."""
import numpy as np
from scipy.optimize import linprog

T = 24
phi = 0.20
it_max = 1250.0  # kW, with 1-hour steps
baseline = np.full(T, 1000.0)  # kWh per hour

# Same synthetic $/kWh as Step 08
prices = np.r_[
    0.20 + 0.001 * np.arange(12),
    0.05 + 0.001 * np.arange(12)]

fixed = (1 - phi) * baseline
arrivals = phi * baseline

# P_dc = a + b*x, with dt = 1 h
models = {
    "M0": (0.0, 1.0471),
    "M1-fixed": (73.13, 1.0),
}


def optimize(a, b, limit):
    it_cap = min(it_max, (limit - a) / b)
    res = linprog(
        b * prices,
        A_ub=np.tril(np.ones((T, T))),
        b_ub=np.cumsum(arrivals),
        A_eq=np.ones((1, T)),
        b_eq=[arrivals.sum()],
        bounds=[(0, it_cap - v) for v in fixed],
        method="highs",
    )
    assert res.status == 0, res.message
    return fixed + res.x


for limit in [1400.0, 1250.0]:
    print(f"\nFacility limit: {limit:,.0f} kW")
    schedules = {name: optimize(a, b, limit) for name, (a, b) in models.items()}
    for name, x in schedules.items():
        print(f"{name} schedule peak IT {x.max():,.2f} kW:", np.round(x, 1).tolist())

    print("Reference  Schedule   Peak kW   Violation kW      Cost $   Regret $")
    for ref, (a, b) in models.items():
        power = {name: a + b * x for name, x in schedules.items()}
        cost = {name: prices @ p for name, p in power.items()}
        best = cost[ref]  # each reference's own schedule is optimal under it
        for name, p in power.items():
            violation = max(0.0, p.max() - limit)
            regret = "Infeasible" if violation > 1e-6 else f"{cost[name] - best:,.2f}"
            print(f"{ref:<10} {name:<10} {p.max():>7,.2f} {violation:>14,.2f}"
                  f" {cost[name]:>11,.2f} {regret:>10}")

    if limit == 1400.0:
        assert np.allclose(schedules["M0"], schedules["M1-fixed"]), "Step 08 not reproduced"
    else:
        assert not np.allclose(schedules["M0"], schedules["M1-fixed"]), "Schedules identical"
