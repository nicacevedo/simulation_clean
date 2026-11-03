"""Step 06: M0 versus M1 on two chronological holdouts."""
import numpy as np
import pandas as pd

CSV = "dc_resource_sim/runs/m0_daily.csv"

df = pd.read_csv(CSV, parse_dates=["day"])


def compare(train, test, label):
    # Fit using daily average power (kW)
    x = train.it_kwh / 24
    y = train.ref_dc_kwh / 24
    k = train.ref_dc_kwh.sum() / train.it_kwh.sum()  # M0: energy-weighted PUE
    b, a = np.polyfit(x, y, 1)                       # M1: unrestricted affine
    a_fixed = (y - x).mean()                         # M1-fixed: constant overhead

    predictions = {
        "M0": k * test.it_kwh,
        "M1": 24 * a + b * test.it_kwh,
        "M1-fixed": test.it_kwh + 24 * a_fixed,
    }

    x_test = test.it_kwh / 24
    print(f"\n{label}: {len(train)} train, {len(test)} test days")
    print(f"M0 k={k:.4f}; M1 a={a:.1f} kW, b={b:.4f}; M1-fixed a={a_fixed:.1f} kW")
    # Shows whether the test requires extrapolation in IT load.
    print(f"IT load range (kW): train {x.min():.0f}-{x.max():.0f}, "
          f"test {x_test.min():.0f}-{x_test.max():.0f}")
    for name, pred in predictions.items():
        err = 100 * (pred / test.ref_dc_kwh - 1)
        # IT is known, so facility error equals overhead error.
        overhead_err = (pred - test.ref_dc_kwh) / 24
        print(f"{name:9s}: median={err.abs().median():.2f}% "
              f"p90={err.abs().quantile(.9):.2f}% "
              f"bias={err.mean():+.2f}% "
              f"overhead_median={overhead_err.abs().median():.1f} kW")


month = df.day.dt.month
compare(df[month <= 4], df[month.between(5, 8)], "Summer")
compare(df[month <= 8], df[month >= 9], "High-load")
