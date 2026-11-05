"""Step 12: Does wet-bulb improve hourly capacity predictions?"""
import numpy as np
import pandas as pd

ROOT = "dc_resource_sim/runs/"
power = pd.read_csv(ROOT + "esif_hourly_2023.csv")
weather = pd.read_csv(ROOT + "esif_weather_hourly_2023.csv")
for d in (power, weather):
    d["timestamp_utc"] = pd.to_datetime(d["timestamp_utc"], utc=True)
    assert d.timestamp_utc.is_unique

# Inner merge + dropna: identical rows for all models, nothing filled
df = power.merge(weather, on="timestamp_utc", validate="one_to_one")
df = df.dropna(subset=["it_power_kw", "ref_dc_kw", "twb_c"])
print(f"Matched hours: {len(df)} / {len(power)}")

month = df.timestamp_utc.dt.month
splits = {
    "Summer": (month <= 4, month.between(5, 8)),
    "High-load": (month <= 8, month >= 9),
}

for label, (tr, te) in splits.items():
    train, test = df.loc[tr], df.loc[te]
    assert len(train) > 0 and len(test) > 0

    # Fit exclusively on training observations
    k = train.ref_dc_kw.sum() / train.it_power_kw.sum()
    a_fixed = (train.ref_dc_kw - train.it_power_kw).mean()
    t0 = train.twb_c.mean()
    X = np.column_stack([np.ones(len(train)), train.twb_c - t0])
    a, c = np.linalg.lstsq(X, train.ref_dc_kw - train.it_power_kw, rcond=None)[0]

    lo, hi = train.twb_c.min(), train.twb_c.max()
    outside = 100 * (~test.twb_c.between(lo, hi)).mean()
    print(f"\n{label}: train n={len(train)}, Twb {lo:.1f} to {hi:.1f} C;"
          f" test n={len(test)}, Twb {test.twb_c.min():.1f} to {test.twb_c.max():.1f} C;"
          f" test hours outside training range {outside:.1f}%")
    print(f"  k={k:.4f}  a_fixed={a_fixed:.2f}  M2a: a={a:.2f}, c={c:.2f} kW/C, T0={t0:.2f} C")

    predict = {
        "M0": lambda d: k * d.it_power_kw,
        "M1-fixed": lambda d: d.it_power_kw + a_fixed,
        "M2a-fixed": lambda d: d.it_power_kw + a + c * (d.twb_c - t0),
    }
    print("  Model      Under %   p95 pos kW   Max under kW   h95 kW   >h95 %   MAE kW")
    for name, f in predict.items():
        # e > 0: model underestimates facility power (the unsafe direction)
        e_train = train.ref_dc_kw - f(train)
        e_test = test.ref_dc_kw - f(test)
        h95 = max(0.0, e_train.quantile(0.95))  # training data only, never recalibrated
        under = e_test[e_test > 0]
        p95 = f"{under.quantile(0.95):.1f}" if len(under) else "n/a"
        print(f"  {name:<10} {100 * (e_test > 0).mean():>6.1f} {p95:>12}"
              f" {e_test.max():>14.1f} {h95:>8.1f} {100 * (e_test > h95).mean():>8.1f}"
              f" {e_test.abs().mean():>8.1f}")
