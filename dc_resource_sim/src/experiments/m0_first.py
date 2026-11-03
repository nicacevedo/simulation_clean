"""
M0 first run: 24-hour forward simulation, no optimization.

    IT power  --(x dt)-->  IT energy  --(x PUE)-->  facility energy   (M0)
                                     --(x w0)--->  direct water       (W0)

Runs two synthetic experiments and checks them against hand-computed values:
    A) constant 1,000 kW IT load
    B) same total energy, but 800 kW for hours 0-11 and 1,200 kW for hours 12-23

Run from the repository root:
    python dc_resource_sim/src/experiments/m0_first.py
"""

import pandas as pd

# ---------------------------------------------------------------------------
# Assumptions (illustrative, NOT calibrated to any real facility)
# ---------------------------------------------------------------------------
PUE = 1.20                  # k: facility energy / IT energy, constant
WATER_L_PER_IT_KWH = 0.50   # w0: direct water consumption per kWh of IT energy
DT_H = 1.0                  # time step length [hours]
HOURS = 24                  # horizon [hours]

# Input: None -> synthetic profile. Later: path to a CSV with columns timestamp_utc,it_kw
CSV = None


def load_it_profile(csv_path):
    """Return a DataFrame with one row per hour: timestamp_utc (UTC), it_kw."""
    if csv_path is None:
        return pd.DataFrame({
            "timestamp_utc": pd.date_range("2023-07-01", periods=HOURS, freq="h", tz="UTC"),
            "it_kw": [1000.0] * HOURS,
        })

    df = pd.read_csv(csv_path, usecols=["timestamp_utc", "it_kw"])
    assert df["timestamp_utc"].str.contains(r"(Z|\+00:00)$", regex=True).all(), \
        "Input timestamps must explicitly be UTC"
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)
    return df.sort_values("timestamp_utc").reset_index(drop=True)


def check_inputs(df):
    """Fail loudly on anything that would make the arithmetic meaningless."""
    assert PUE >= 1 and WATER_L_PER_IT_KWH >= 0
    assert len(df) == HOURS
    assert df["timestamp_utc"].notna().all() and df["timestamp_utc"].is_unique
    assert (df["timestamp_utc"].diff().dropna() == pd.Timedelta(hours=DT_H)).all()
    assert df["it_kw"].notna().all() and df["it_kw"].ge(0).all()


def run_m0_w0(df):
    """Apply M0 (constant PUE) and W0 (constant water intensity) hour by hour."""
    out = df.copy()
    out["it_kwh"] = out["it_kw"] * DT_H                          # E_IT = P_IT * dt
    out["dc_kwh"] = PUE * out["it_kwh"]                          # E_DC = k * E_IT
    out["overhead_kwh"] = out["dc_kwh"] - out["it_kwh"]          # (k - 1) * E_IT
    out["direct_consumption_l"] = WATER_L_PER_IT_KWH * out["it_kwh"]  # V = w0 * E_IT
    out["dc_kw"] = out["dc_kwh"] / DT_H                          # average facility power
    return out


def summarize(name, out):
    """Print 24-hour totals and facility peak; return them as a dict."""
    totals = out[["it_kwh", "dc_kwh", "overhead_kwh", "direct_consumption_l"]].sum()
    peak_dc_kw = out["dc_kw"].max()
    print(f"\n=== {name} ===")
    print(totals.map("{:,.1f}".format).to_string())
    print(f"peak_dc_kw: {peak_dc_kw:,.1f}")
    return {**totals.to_dict(), "peak_dc_kw": peak_dc_kw}


def assert_close(result, expected):
    """Compare each result against its hand-computed expected value."""
    for key, value in expected.items():
        assert abs(result[key] - value) < 1e-6, f"{key}: got {result[key]}, expected {value}"
    # Energy balance must hold exactly: facility = IT + overhead
    assert abs(result["dc_kwh"] - (result["it_kwh"] + result["overhead_kwh"])) < 1e-6


if __name__ == "__main__":
    # Experiment A: constant load (or the measured CSV profile, once CSV is set)
    profile_a = load_it_profile(CSV)
    check_inputs(profile_a)
    result_a = summarize("Experiment A: constant load", run_m0_w0(profile_a))

    if CSV is None:
        # Hand-computed: 1000 kW * 24 h = 24,000 kWh; x1.2 = 28,800; x0.5 L = 12,000 L
        assert_close(result_a, {"it_kwh": 24_000, "dc_kwh": 28_800, "overhead_kwh": 4_800,
                                "direct_consumption_l": 12_000, "peak_dc_kw": 1_200})

        # Experiment B: same total IT energy, shifted in time
        profile_b = load_it_profile(None)
        profile_b.loc[:11, "it_kw"] = 800.0
        profile_b.loc[12:, "it_kw"] = 1200.0
        check_inputs(profile_b)
        result_b = summarize("Experiment B: same energy, different timing", run_m0_w0(profile_b))

        # Totals unchanged; only the peak grows: 1200 kW * 1.2 = 1,440 kW
        assert_close(result_b, {"it_kwh": 24_000, "dc_kwh": 28_800, "overhead_kwh": 4_800,
                                "direct_consumption_l": 12_000, "peak_dc_kw": 1_440})

        print("\nAll checks passed.")
