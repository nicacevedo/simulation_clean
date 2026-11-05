"""Step 13: Does fitting the IT-load slope b improve the weather model?"""
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
    "Warm": (month <= 7, month == 8),
    "High-load": (month <= 8, month >= 9),
}
models = {
    "M0": None,  # P_DC = k * P_IT, k = training energy ratio (as in m0_holdout.py)
    "M1-fixed": (),
    "M1": ("load",),
    "M2a-fixed": ("weather",),
    "M2a": ("load", "weather"),
}

for label, (tr, te) in splits.items():
    train, test = df.loc[tr], df.loc[te]
    assert len(train) > 0 and len(test) > 0
    p0, t0 = train.it_power_kw.mean(), train.twb_c.mean()

    print(f"\n{label}: train n={len(train)}, test n={len(test)}, P0={p0:.1f} kW, T0={t0:.2f} C")
    for col in ["it_power_kw", "twb_c"]:
        lo, hi = train[col].min(), train[col].max()
        outside = 100 * (~test[col].between(lo, hi)).mean()
        print(f"  {col}: train {lo:.1f} to {hi:.1f}, test {test[col].min():.1f} to"
              f" {test[col].max():.1f}, test outside training range {outside:.1f}%")

    def design(d, terms):
        cols = [np.ones(len(d))]
        if "load" in terms:
            cols.append(d.it_power_kw - p0)
        if "weather" in terms:
            cols.append(d.twb_c - t0)
        return np.column_stack(cols)

    def fit(terms):
        # Fixed-slope models (b=1) regress the overhead DC - IT; otherwise regress DC directly.
        offset_train = 0 if "load" in terms else train.it_power_kw
        coef = np.linalg.lstsq(design(train, terms), train.ref_dc_kw - offset_train, rcond=None)[0]
        b = coef[1] if "load" in terms else 1.0
        c = coef[-1] if "weather" in terms else 0.0

        def predict(d):
            return design(d, terms) @ coef + (0 if "load" in terms else d.it_power_kw)

        return b, c, predict

    print("  Model         b       c kW/C   MAE kW   p95 under kW   h95 kW   >h95 %   DC<IT n")
    for name, terms in models.items():
        if terms is None:
            b, c = train.ref_dc_kw.sum() / train.it_power_kw.sum(), 0.0

            def predict(d, k=b):
                return k * d.it_power_kw
        else:
            b, c, predict = fit(terms)

        # e > 0: model underestimates facility power (the unsafe direction)
        e_train = train.ref_dc_kw - predict(train)
        e_test = test.ref_dc_kw - predict(test)
        h95 = max(0.0, e_train.quantile(0.95))  # training data only, never recalibrated
        under = e_test[e_test > 0]
        p95 = f"{under.quantile(0.95):.1f}" if len(under) else "n/a"
        # Flag (do not clip) physically impossible predictions
        below_it = int((predict(test) < test.it_power_kw).sum())
        print(f"  {name:<10} {b:>7.4f} {c:>10.2f} {e_test.abs().mean():>8.1f} {p95:>14}"
              f" {h95:>8.1f} {100 * (e_test > h95).mean():>8.1f} {below_it:>9}")
