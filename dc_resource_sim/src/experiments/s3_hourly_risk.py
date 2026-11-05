"""Step 11: Held-out hourly underprediction and headroom."""
import pandas as pd

df = pd.read_csv("dc_resource_sim/runs/esif_hourly_2023.csv")
df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
assert len(df) == 7200
assert df.timestamp_utc.is_unique
assert df[["it_power_kw", "ref_dc_kw"]].notna().all().all()

month = df.timestamp_utc.dt.month
splits = {
    "Summer": (month <= 4, month.between(5, 8)),
    "High-load": (month <= 8, month >= 9),
}

print("Split      Model      Coef      Under %   p95 pos kW   Max under kW   h95 kW   >h95 %")
for label, (train_mask, test_mask) in splits.items():
    train, test = df[train_mask], df[test_mask]

    # Same calibration as Step 06
    k = train.ref_dc_kw.sum() / train.it_power_kw.sum()
    a = (train.ref_dc_kw - train.it_power_kw).mean()

    for name in ["M0", "M1-fixed"]:
        if name == "M0":
            coef = f"k={k:.4f}"
            pred_train = k * train.it_power_kw
            pred_test = k * test.it_power_kw
        else:
            coef = f"a={a:.2f}"
            pred_train = train.it_power_kw + a
            pred_test = test.it_power_kw + a

        # e > 0: model underestimates facility power (the unsafe direction)
        e_train = train.ref_dc_kw - pred_train
        e_test = test.ref_dc_kw - pred_test
        h95 = max(0.0, e_train.quantile(0.95))  # training data only, never recalibrated

        under = e_test[e_test > 0]
        print(f"{label:<10} {name:<10} {coef:<9} {100 * (e_test > 0).mean():>7.1f}"
              f" {under.quantile(0.95):>12.1f} {e_test.max():>14.1f}"
              f" {h95:>8.1f} {100 * (e_test > h95).mean():>8.1f}")
