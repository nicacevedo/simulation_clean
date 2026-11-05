"""Step 10: Decision value of facility-power limits under real hourly prices."""
import numpy as np
import pandas as pd
from scipy.optimize import linprog

T = 24
phi = 0.20
it_max = 1250.0  # kW, with 1-hour steps
baseline = np.full(T, 1000.0)  # kWh per hour
LIMITS = [1400.0, 1320.0, 1300.0, 1250.0]

# One verified 24-hour price profile (MISO ILLINOIS.HUB, 2023-07-01 UTC)
df = pd.read_csv("dc_resource_sim/runs/price_24h.csv")
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
df = df.sort_values("timestamp_utc")
expected = pd.date_range(df.timestamp_utc.iloc[0], periods=24, freq="h")
assert len(df) == 24
assert df.timestamp_utc.iloc[0].hour == 0
assert (df.timestamp_utc.to_numpy() == expected.to_numpy()).all()
assert df.price_usd_per_kwh.notna().all()
prices = df.price_usd_per_kwh.to_numpy(float)

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
    x = fixed + res.x
    assert np.isclose(x.sum(), baseline.sum()), "IT work not completed"
    assert (np.cumsum(res.x) <= np.cumsum(arrivals) + 1e-6).all(), "Work before arrival"
    assert (x <= it_cap + 1e-6).all(), "IT capacity exceeded"
    return x


print("Limit kW  Reference  Schedule   Peak kW   Violation kW      Cost $   Regret $")
for limit in LIMITS:
    schedules = {name: optimize(a, b, limit) for name, (a, b) in models.items()}
    for ref, (a, b) in models.items():
        power = {name: a + b * x for name, x in schedules.items()}
        cost = {name: prices @ p for name, p in power.items()}
        best = cost[ref]  # each reference's own schedule is optimal under it
        for name, p in power.items():
            violation = max(0.0, p.max() - limit)
            regret = "Infeasible" if violation > 1e-6 else f"{cost[name] - best:,.2f}"
            print(f"{limit:>8,.0f}  {ref:<10} {name:<10} {p.max():>7,.2f} {violation:>14,.2f}"
                  f" {cost[name]:>11,.2f} {regret:>10}")

    if limit == 1400.0:
        # Compare objective values, not schedules, in case real prices have ties
        for ref, (a, b) in models.items():
            other = schedules["M1-fixed" if ref == "M0" else "M0"]
            assert np.isclose(prices @ (a + b * other), prices @ (a + b * schedules[ref])), \
                "Nonbinding case: decisions not equivalent"
