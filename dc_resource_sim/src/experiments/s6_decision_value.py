"""Step 14: Does weather-dependent overhead improve capacity-constrained scheduling?

One held-out day (2023-09-01 UTC), models trained on Jan-Aug 2023. Every schedule is
judged against the observed overhead H_ref = DC - IT, held fixed when IT is shifted
(a counterfactual approximation, not a measured response to shifting).
"""
import numpy as np
import pandas as pd
from scipy.optimize import linprog

ROOT = "dc_resource_sim/runs/"
DAY = "2023-09-01"
T = 24
phi = 0.20
LIMITS = [4400.0, 3400.0]  # kW, hypothetical: control and binding scenario

power = pd.read_csv(ROOT + "esif_hourly_2023.csv")
weather = pd.read_csv(ROOT + "esif_weather_hourly_2023.csv")
prices_df = pd.read_csv(ROOT + f"price_{DAY}.csv")
for d in (power, weather, prices_df):
    d["timestamp_utc"] = pd.to_datetime(d["timestamp_utc"], utc=True)
    assert d.timestamp_utc.is_unique

# Same weather-matched observations as s5_affine_weather.py
df = power.merge(weather, on="timestamp_utc", validate="one_to_one")
df = df.dropna(subset=["it_power_kw", "ref_dc_kw", "twb_c"])
train = df[df.timestamp_utc.dt.month <= 8]
day = df[df.timestamp_utc.dt.strftime("%Y-%m-%d") == DAY].sort_values("timestamp_utc")
prices_df = prices_df.sort_values("timestamp_utc")

expected = pd.date_range(DAY, periods=T, freq="h", tz="UTC")
assert len(day) == T and (day.timestamp_utc.to_numpy() == expected.to_numpy()).all()
assert len(prices_df) == T and (prices_df.timestamp_utc.to_numpy() == expected.to_numpy()).all()
assert prices_df.price_usd_per_kwh.notna().all()
assert day.it_power_kw.between(train.it_power_kw.min(), train.it_power_kw.max()).all()
prices = prices_df.price_usd_per_kwh.to_numpy(float)

baseline = day.it_power_kw.to_numpy(float)  # kWh per hour
h_ref = day.ref_dc_kw.to_numpy(float) - baseline
it_max = 1.25 * baseline.max()
fixed = (1 - phi) * baseline
arrivals = phi * baseline

# Training-only coefficients (same conventions as m0_holdout.py and s5_affine_weather.py)
k = train.ref_dc_kw.sum() / train.it_power_kw.sum()
t0 = train.twb_c.mean()
oh_train = train.ref_dc_kw - train.it_power_kw
a1 = oh_train.mean()
X = np.column_stack([np.ones(len(train)), train.twb_c - t0])
a2, c = np.linalg.lstsq(X, oh_train, rcond=None)[0]

# Each model: P_DC = intercept_t + slope * x_t
models = {
    "M0": (np.zeros(T), k, k * train.it_power_kw),
    "M1-fixed": (np.full(T, a1), 1.0, train.it_power_kw + a1),
    "M2a-fixed": (a2 + c * (day.twb_c.to_numpy() - t0), 1.0, train.it_power_kw + a2 + c * (train.twb_c - t0)),
}
h95 = {name: max(0.0, (train.ref_dc_kw - pred).quantile(0.95)) for name, (_, _, pred) in models.items()}
print(f"{DAY}: IT {baseline.min():.0f}-{baseline.max():.0f} kW, IT cap {it_max:.0f} kW, "
      f"observed overhead {h_ref.min():.1f}-{h_ref.max():.1f} kW")
print(f"Train Jan-Aug n={len(train)}: k={k:.4f}, a(M1-fixed)={a1:.1f} kW, "
      f"a(M2a-fixed)={a2:.1f} kW, c={c:.2f} kW/C, T0={t0:.2f} C")
print("h95 kW: " + ", ".join(f"{n} {v:.1f}" for n, v in h95.items()))
for name, (intercept, slope, _) in models.items():
    pred = intercept + slope * baseline
    print(f"  {name:<10} baseline-day error vs observed: mean {np.mean(h_ref + baseline - pred):+.1f} kW, "
          f"max under {np.max(h_ref + baseline - pred):+.1f} kW")


def optimize(intercept, slope, limit, headroom=0.0):
    """Cheapest schedule satisfying intercept + slope*x + headroom <= limit; None if infeasible."""
    it_cap = np.minimum(it_max, (limit - headroom - intercept) / slope)
    if (it_cap < fixed).any():
        return None
    res = linprog(
        slope * prices,
        A_ub=np.tril(np.ones((T, T))),
        b_ub=np.cumsum(arrivals),
        A_eq=np.ones((1, T)),
        b_eq=[arrivals.sum()],
        bounds=list(zip(np.zeros(T), it_cap - fixed)),
        method="highs",
    )
    if res.status == 2:
        return None
    assert res.status == 0, res.message
    x = fixed + res.x
    assert np.isclose(x.sum(), baseline.sum()), "IT work not completed"
    assert (np.cumsum(res.x) <= np.cumsum(arrivals) + 1e-6).all(), "Work before arrival"
    assert (x <= it_max + 1e-6).all(), "IT capacity exceeded"
    return x


print("\nLimit kW  Model      Headroom  Ref peak kW  Max violation kW   Ref cost $   Regret $")
for limit in LIMITS:
    x_ref = optimize(h_ref, 1.0, limit)
    assert x_ref is not None, "Reference problem infeasible"
    best = prices @ (x_ref + h_ref)
    print(f"{limit:>8,.0f}  {'Reference':<10} {'-':<8} {(x_ref + h_ref).max():>12,.1f}"
          f" {0.0:>17,.1f} {best:>12,.2f} {0.0:>10,.2f}")
    for name, (intercept, slope, _) in models.items():
        for policy, headroom in [("none", 0.0), ("h95", h95[name])]:
            x = optimize(intercept, slope, limit, headroom)
            if x is None:
                print(f"{limit:>8,.0f}  {name:<10} {policy:<8} {'LP infeasible':>12}")
                continue
            p_ref = x + h_ref
            violation = max(0.0, p_ref.max() - limit)
            cost = prices @ p_ref
            regret = "Infeasible" if violation > 1e-6 else f"{cost - best:,.2f}"
            print(f"{limit:>8,.0f}  {name:<10} {policy:<8} {p_ref.max():>12,.1f}"
                  f" {violation:>17,.1f} {cost:>12,.2f} {regret:>10}")
            if limit == LIMITS[0]:
                # Nonbinding: same optimal reference cost up to solver ties
                assert np.isclose(cost, best), "Nonbinding case: decisions not equivalent"
