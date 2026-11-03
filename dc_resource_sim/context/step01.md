## Step 01 — First M0 experiment with measured data

Step 00 is complete. Both results are correct, and the existing script location is appropriate. Keep `dc_resource_sim/src/experiments/m0_first.py` exactly where it is.

The next step should be one real 24-hour IT-load profile from NLR ESIF, without introducing optimization or changing the M0/W0 equations.

### 1. What we want to learn

We now want to answer two questions:

1. What does M0 predict when IT demand actually varies throughout a day?
2. How different is that prediction from the facility electricity reported by the dataset?

The [NLR ESIF power dataset](https://data.nlr.gov/submissions/300?utm_source=chatgpt.com) provides all three necessary fields: `ts`, `it_power_kw`, and `pue`.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://data.nlr.gov\&sz=32)

NLR Data Catalog



| Quantity                  | Source / calculation                |
| ------------------------- | ----------------------------------- |
| IT power \\(P_t^{IT}\\)   | Measured `it_power_kw`              |
| Facility power, M0        | \\(P_t^{M0}=1.20P_t^{IT}\\)         |
| Facility power, reference | \\(P_t^{ref}=P_t^{IT}\cdot pue_t\\) |

The reference is reconstructed using the dataset's reported PUE; it is not an independent facility-meter measurement.

Keep \\(k=1.20\\) initially. We are testing a fixed assumption, not calibrating M0 yet.

W0 remains unchanged. Its water output is illustrative because we have no corresponding hourly water observations.

### 2. Read only the necessary data

First, locate the existing Parquet file within the known data directory, rather than scanning the entire shared cluster filesystem:

```
find /path/to/your/data -maxdepth 6 -type f \
  -iname '*.parquet' | grep -Ei 'esif|power.metrics'
```

If the file is already indexed in your previous EDA scripts, use that path instead.

Then extract one complete 24-hour period. The code below reads only three columns from the Parquet file, computes hourly means, and exports a small CSV that the existing M0 script can read.

```
import pandas as pdPARQUET = "/path/to/esif_power_metrics.parquet"DAY = "2023-07-01"  # Change if this day is unavailable# Read only the required columnsdf = pd.read_parquet(    PARQUET, columns=["ts", "it_power_kw", "pue"])# Only use utc=True after confirming the source timestamps# are UTC; otherwise localize to the documented timezone first.df["ts"] = pd.to_datetime(df["ts"], utc=True)start = pd.Timestamp(DAY, tz="UTC")df = df[(df.ts >= start) &        (df.ts < start + pd.Timedelta(days=1))].copy()df = df.sort_values("ts")assert len(df) > 1, "No data for this day"assert df.ts.is_uniqueassert df[["it_power_kw", "pue"]].notna().all().all()assert (df.it_power_kw > 0).all() and (df.pue >= 1).all()# Require a complete, uniformly sampled 24-hour daystep = df.ts.diff().dropna().mode().iloc[0]expected = pd.date_range(    start, start + pd.Timedelta(days=1),    freq=step, inclusive="left")assert df.ts.tolist() == expected.tolist(), "Incomplete day"# Derive reference before hourly averagingdf["ref_dc_kw"] = df.it_power_kw * df.puehourly = df.set_index("ts").resample("h").agg(
```

This uses `pandas` and a Parquet engine such as `pyarrow`. For a roughly 105 MB source file, column-selective reading is adequate for this first experiment; more elaborate data-loading infrastructure is unnecessary.

If the selected day fails the completeness check, choose another day. Do not fill gaps or interpolate for this experiment.

### 3. Run the existing script

Change only:

```
CSV = "esif_24h.csv"
```

Run:

```
python dc_resource_sim/src/experiments/m0_first.py
```

Keep Experiments A and B intact. The measured-data case should use their existing model functions.

### 4. What we should report

Only these four results are necessary:

| Result                        | Why it matters                                      |
| ----------------------------- | --------------------------------------------------- |
| Reference daily PUE           | Establishes actual facility efficiency for that day |
| M0 daily energy error (%)     | Tests aggregate electricity prediction              |
| M0 hourly MAE (kW)            | Tests hourly prediction                             |
| IT and facility load profiles | Shows how the measured load affects the prediction  |

For the last result, a simple plot with two curves—M0 facility power and reference facility power—is sufficient. No additional figures or sensitivity analysis.

### 5. Minimal repository changes

I recommend keeping the experiment code in the existing location. The only permanent addition should be a small ESIF data-preparation script if the one-off extraction needs to be repeated. Otherwise, the current M0 script and a recorded data-source path are sufficient.

Do not modify the original ESIF file. Keep the extracted CSV outside version control initially, and record the selected date, source path, and timestamp interpretation.

Ignore the unrelated Lmod shell warnings for now.

Completion criterion: One complete measured day successfully runs through M0, with an explicit comparison against its reported facility electricity and without changing the equations.

After this, the next meaningful step is estimating a constant \\(k\\) from measured data and evaluating M0 on a different day. That will give us a legitimate first predictive baseline before introducing M1.