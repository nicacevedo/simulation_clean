# M0 — Minimal first implementation

## 1. What we should implement first

Recommendation: Start with a 24-hour forward simulation using M0 (constant PUE), one IT-load profile, and no optimization.

The objective is to establish the simplest possible mapping:

\\[ \boxed{ \text{IT load}\ \longrightarrow\ \text{Facility electricity} } \\]

We can also calculate direct water consumption using W0 (constant water intensity), keeping it clearly separate from M0.

For this first test, we do not need electricity prices, weather, emissions, groundwater measurements, or a physical cooling model.

### Which data source should we use?

I recommend two very small stages:

| Stage               | Data                                                                                                                              | Purpose                                                                                          |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| First run           | Synthetic 24-hour IT-load profile                                                                                                 | Verify all equations, units, and calculations                                                    |
| First empirical run | [NLR ESIF facility power dataset](https://data.nlr.gov/submissions/300?utm_source=chatgpt.com) already identified in our planning | Replace synthetic IT demand with measured observations and compare M0 with facility measurements |

The NLR ESIF dataset is especially appropriate because it contains `ts`, `it_power_kw`, `pue`, and component-level power measurements. We therefore have a useful real-world source for testing M0 without introducing cooling or grid models yet.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://data.nlr.gov\&sz=32)

NLR Data Catalog



Do not download or process the complete ESIF archive yet. Use the local copy from the previous EDA work when ready. We only need a representative day for the first empirical experiment.

The existing frozen MISO/ERCOT 2023 signals should wait until we introduce electricity-cost optimization.

## 2. Assumptions and inputs

For the very first run, use the following illustrative parameters, not facility-calibrated values.

| Input                  | Symbol          | Initial value | Meaning                            |
| ---------------------- | --------------- | ------------- | ---------------------------------- |
| Time step              | \\(\Delta t\\)  | 1 hour        | One observation per hour           |
| Horizon                | \\(T\\)         | 24 hours      | One day                            |
| IT demand              | \\(P^{IT}\_t\\) | 1,000 kW      | Constant hypothetical load         |
| PUE                    | \\(k\\)         | 1.20          | Constant facility multiplier       |
| Direct water intensity | \\(w_0\\)       | 0.5 L/kWh IT  | Optional W0 consumption assumption |

The last parameter is only an illustrative water-consumption coefficient. It is not a calibrated or observed WUE for ESIF.

We are assuming:

- One hypothetical facility, fully electrically powered.
- The IT load represents total IT equipment demand, not just GPU power.
- PUE is constant, regardless of workload or weather.
- No heat reuse, onsite generation, or energy storage is modeled.
- Direct water consumption is proportional to IT electricity for W0.

No computing jobs, utilization curves, server counts, or cooling-system parameters are required yet.

## 3. How the quantities connect

Input: IT power

\\(P^{IT}\_t\quad [\mathrm{kW}]\\)

Multiply by \\(\Delta t=1\\) hour

IT electricity

\\(E^{IT}\_t=P^{IT}\_t\Delta t\\)

M0: multiply by \\(k\\)

Facility electricity

\\(E^{DC}\_t=kE^{IT}\_t\\)

W0: multiply by \\(w_0\\)

Direct water

\\(V^{con}\_t=w_0E^{IT}\_t\\)

The facility overhead is then

\\[ E^{overhead}\_t=(k-1)E^{IT}\_t. \\]

This overhead includes the combined non-IT electricity accounted for by PUE. We cannot infer cooling electricity separately from M0.

The physical heat produced by IT equipment is approximately its electrical input, but we should not equate that quantity with a specific cooling-system duty at this stage.

### Expected first-run results

24-hour IT electricity

# 24,000 kWh

24-hour facility electricity

# 28,800 kWh

24-hour overhead electricity

# 4,800 kWh

24-hour modeled direct water

# 12,000 L

These values should be reproduced exactly, up to numerical tolerance.

## 4. How to organize and read the data

The repository already has a `simulation/` directory.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://github.com\&sz=32)

GitHub

&#x20;I would add just one script:



```
simulation/
    m0_first.py
```

Do not create the larger `dc_resource_sim/` architecture proposed in the planning document yet. Do not modify the existing prototypes.

### Initial data format

Use one row per hour, with only two columns:

| `timestamp_utc`      | `it_kw` |
| -------------------- | ------- |
| 2023-07-01T00:00:00Z | 1000    |
| 2023-07-01T01:00:00Z | 1000    |
| 2023-07-01T02:00:00Z | 1000    |
| ...                  | ...     |
| 2023-07-01T23:00:00Z | 1000    |

The first script will create this data internally. No CSV file is needed to run it.

When introducing real ESIF data, the input format stays exactly the same. This is important: changing the data source should not require changing the model equations.

### Instructions for the first empirical dataset

Once the synthetic test passes:

1. Locate the existing local ESIF power-metrics Parquet file. Avoid another download.
2. Inspect its schema and use only `ts`, `it_power_kw`, and optionally `pue`. Ignore weather and individual cooling components initially.
3. Select one representative 24-hour period, checking the timestamp's timezone and actual sampling frequency.
4. Convert IT power to hourly mean kW only if the observations have sufficiently complete, regular coverage. Otherwise, use time-weighted aggregation.
5. Do not interpolate missing data, silently remove anomalous values, or substitute zeros.
6. Save just the 24 hourly rows as a small temporary CSV with `timestamp_utc,it_kw`. Then pass it to the same M0 script.

For efficient reading of a large Parquet file, use column selection and, when possible, time filtering. For example, after confirming that `ts` is a timestamp column with the expected timezone:

```
import pyarrow.dataset as dsimport pandas as pdsource = ds.dataset("PATH_TO_ESIF_POWER.parquet", format="parquet")print(source.schema)start = pd.Timestamp("2023-07-01", tz="UTC")end = start + pd.Timedelta(days=1)raw = source.to_table(    columns=["ts", "it_power_kw", "pue"],    filter=(ds.field("ts") >= start.to_pydatetime()) &           (ds.field("ts") < end.to_pydatetime())).to_pandas()
```

This example assumes the file has a compatible timestamp type and UTC interpretation. Verify those before applying the filter; the exact local file path has not been verified here.

One important detail for future validation: if `pue` is available at the original measurement resolution, calculate the implied facility power as `it_power_kw * pue` before hourly aggregation. Multiplying hourly average IT power by hourly average PUE generally gives a different result.

We should also preserve the distinction between a scenario PUE of 1.20 and PUE estimated from measurements. Calibration belongs in the next empirical step, not this first arithmetic check.

## 5. Reference code — complete first experiment

Save the following as `simulation/m0_first.py`.

```
import pandas as pd# Assumptions (illustrative, not calibrated)PUE = 1.20WATER_L_PER_IT_KWH = 0.50DT_H = 1.0# Input: use synthetic data firstCSV = None  # Later: "path/to/it_24h.csv"if CSV is None:    df = pd.DataFrame({        "timestamp_utc": pd.date_range(            "2023-07-01", periods=24, freq="h", tz="UTC"        ),        "it_kw": [1000.0] * 24    })else:    df = pd.read_csv(CSV, usecols=["timestamp_utc", "it_kw"])    assert df["timestamp_utc"].str.contains(        r"(Z|\+00:00)$", regex=True    ).all(), "Input timestamps must explicitly be UTC"    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True)    df = df.sort_values("timestamp_utc").reset_index(drop=True)# Input checksassert PUE >= 1 and WATER_L_PER_IT_KWH >= 0assert len(df) == 24assert df["timestamp_utc"].notna().all()assert df["timestamp_utc"].is_uniqueassert (df["timestamp_utc"].diff().dropna()        == pd.Timedelta(hours=1)).all()assert df["it_kw"].notna().all() and df["it_kw"].ge(0).all()# M0 and W0
```

Run from the repository root:

```
python simulation/m0_first.py
```

I tested this calculation. Its output is:

```
it_kwh                 24,000.0
dc_kwh                 28,800.0
overhead_kwh            4,800.0
direct_consumption_l   12,000.0
peak_dc_kw: 1,200.0
```

Only `pandas` is required. There is no optimizer, no additional configuration file, and no model-fitting dependency.

## 6. Two minimal verification experiments

After the first run succeeds, I recommend exactly one additional experiment before using real data.

Experiment A — Constant load

Use the script as written. Confirm the five numerical results above.

Experiment B — Same energy, different hourly distribution

Immediately after creating the DataFrame, add:

```
df.loc[:11, "it_kw"] = 800.0df.loc[12:, "it_kw"] = 1200.0
```

Now verify that:

- Total IT electricity remains 24,000 kWh.
- Total facility electricity remains 28,800 kWh.
- Direct water remains 12,000 L.
- Facility peak increases from 1,200 to 1,440 kW.

This is our first elementary demonstration that, under M0/W0, the timing of IT demand can change peak electricity demand without changing total electricity or modeled direct water.

These are two forward simulations, not optimized scheduling outcomes.

## 7. How to keep track of the work

For now, I would use Git instead of building an experiment-management system.

After verifying the script:

```
git status --short
git add simulation/m0_first.py
git commit -m "Add minimal M0 forward-model test"
```

Keep the input parameters visible at the top of the script. Do not commit copies of the ESIF raw dataset or generate large output directories.

When the first measured IT-load profile is ready, the only necessary changes should be the CSV input and its preprocessing. The M0/W0 calculations should remain unchanged.

### What constitutes completion of this step?

M0 first-run checklist

5 checks

Synthetic 24-hour input created correctly

Power-to-energy conversion verified

Facility energy and overhead balance verified

Same-energy, different-peak test verified

One standalone script committed

0 of 5 completed

The water calculation is a model-accounting check, not physical validation against water measurements. That distinction should remain explicit.

My final recommendation: Complete these two synthetic M0 experiments first. Then replace the synthetic IT input with a representative measured ESIF profile, keeping the same code and equations. Only after that should we estimate PUE from observations and start comparing M0 with M1.

That will give us a clean, small, and reproducible foundation before introducing optimization or additional physical modeling.