"""Fit one constant PUE on a training day; assess on one held-out day."""
from pathlib import Path
import pandas as pd

TRAIN = Path("dc_resource_sim/runs/esif_train.csv")
TEST = Path("dc_resource_sim/runs/esif_test.csv")


def read_day(path):
    df = pd.read_csv(path, usecols=["timestamp_utc", "it_kw", "ref_dc_kw"])
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    t = df["timestamp_utc"]
    assert len(df) == 24 and t.dt.normalize().nunique() == 1, f"Not one 24h day: {path}"
    assert (t.diff().iloc[1:] == pd.Timedelta(hours=1)).all(), f"Missing hours: {path}"
    assert df[["it_kw", "ref_dc_kw"]].notna().all().all(), f"Missing power: {path}"
    assert (df.it_kw > 0).all() and (df.ref_dc_kw >= df.it_kw).all(), f"Invalid power: {path}"
    return df


train, test = read_day(TRAIN), read_day(TEST)
assert train.timestamp_utc.iloc[0] != test.timestamp_utc.iloc[0], "Train/test overlap"

# Energy-weighted PUE; hourly data are mean kW for one-hour intervals.
k_fit = train.ref_dc_kw.sum() / train.it_kw.sum()
print(f"Training PUE: {k_fit:.4f}")
print(f"Held-out reference PUE: {test.ref_dc_kw.sum() / test.it_kw.sum():.4f}")
print("Model        Daily energy error (%)   Hourly MAE (kW)")
for name, k in [("Fixed 1.20", 1.20), ("Fitted", k_fit)]:
    pred = k * test.it_kw
    energy_error = 100 * (pred.sum() / test.ref_dc_kw.sum() - 1)
    mae = (pred - test.ref_dc_kw).abs().mean()
    print(f"{name:<12} {energy_error:>+16.2f} {mae:>21.1f}")
