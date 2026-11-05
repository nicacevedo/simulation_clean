## Step 03 — Check whether constant PUE is sufficient

The next step should be a small multi-day validation of M0, not M1 or weather modeling yet.

Your results establish two things:

1. Calibration matters: fitting \\(k\\) reduced hourly MAE from 443.0 to 65.3 kW on December 1.
2. PUE varies between the two days: July had \\(k=1.0474\\), while December had \\(k=1.0210\\).

There is one particularly important observation:

Although the December facility-energy error is only +2.59%, M0 predicts overhead of 4.74% of IT electricity, compared with approximately 2.10% in the reference.

That means M0 overestimates December's non-IT electricity by approximately 126%.

This distinction matters for our research: a model can predict total facility electricity reasonably well while being substantially less accurate at predicting cooling and other overhead loads.

The ESIF dataset is particularly useful here because, beyond IT power and PUE, it includes measured cooling, pumping, and HVAC electricity. We can use those later to understand the underlying differences rather than attributing everything to weather.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://data.nlr.gov\&sz=32)

NLR Data Catalog



### 1. The single next experiment

Use all complete days in 2023, keeping the existing July 1 estimate fixed at \\(\hat{k}=1.0474\\).

For each day \\(d\\), calculate:

\\[ k_d^{ref}=\frac{E_d^{DC,ref}}{E_d^{IT}} \\]

\\[ \text{Error}\_d=100\left(\frac{\hat{k}E_d^{IT}}{E_d^{DC,ref}}-1\right). \\]

Report three things:

- Distribution of daily reference PUE.
- Median and 90th-percentile absolute daily energy error.
- Monthly median PUE, to see whether there is a persistent seasonal pattern.

No new model fitting is necessary yet.

### 2. Minimal implementation

Add just `dc_resource_sim/src/experiments/m0_daily.py`. Read the same local ESIF Parquet file once, selecting only three columns.

```
"""Check M0 accuracy across complete days in 2023."""import pandas as pdSOURCE = "other_sources/nlr_esif_fullstack/data_raw/esif_pue/esif.influx.buildingData.PUE.combined.parquet"TRAIN_DAY = pd.Timestamp("2023-07-01", tz="UTC")MAX_GAP = pd.Timedelta(minutes=5)df = pd.read_parquet(SOURCE, columns=["ts", "it_power_kw", "pue"])# Source timestamps are naive; follow the existing UTC assumption.df["ts"] = pd.to_datetime(df["ts"], utc=True)df = df[(df.ts >= "2023-01-01") & (df.ts < "2024-01-01")]df = df.sort_values("ts")rows, hourly = [], {}for day, g in df.groupby(df.ts.dt.floor("D")):    # Same basic completeness checks as esif_day.py    if (        g.ts.duplicated().any()        or g[["it_power_kw", "pue"]].isna().any().any()        or not (g.it_power_kw > 0).all()        or not (g.pue >= 1).all()        or g.ts.iloc[0] - day > MAX_GAP        or day + pd.Timedelta(days=1) - g.ts.iloc[-1] > MAX_GAP        or g.ts.diff().dropna().gt(MAX_GAP).any()    ):        continue    g = g.assign(ref_kw=g.it_power_kw * g.pue)    h = g.set_index("ts")[["it_power_kw", "ref_kw"]].resample("h").mean()    if len(h) != 24 or h.isna().any().any():        continue    it, ref = h.it_power_kw.sum(), h.ref_kw.sum()
```

Run from the repository root using the existing Conda environment.

The CSV is an uncommitted experimental output. No changes to M0, W0, or the existing scripts are required.

Before accepting the results, verify that the computed July 1 and December 1 PUE values reproduce the previous experiments. The current code assumes the same UTC interpretation and hourly averaging as `esif_day.py`; any difference in preprocessing should be resolved before comparing results.

### 3. How to interpret the outcome

| Result                                        | Next action                                          |
| --------------------------------------------- | ---------------------------------------------------- |
| PUE is reasonably stable and errors are small | Keep M0 as the initial electricity model             |
| PUE changes consistently across months        | Investigate weather dependence                       |
| PUE appears strongly related to IT load       | Compare M0 with affine M1                            |
| Large errors occur on particular days         | Inspect data coverage and operating conditions first |

Importantly, seasonal variation does not establish weather causality. IT utilization, facility operating conditions, and cooling configuration could also explain changes.

If M0 proves insufficient, I would first examine the measured facility overhead,

\\[ P_t^{overhead}=P_t^{DC,ref}-P_t^{IT}, \\]

against IT load. That will tell us whether the affine M1 is worth evaluating before introducing weather.

## 4. What not to do yet

Do not add weather regressions, M1/M2 fitting, optimization, parameter sweeps, or water modeling refinements.

Also, remember that ESIF is an exceptionally efficient HPC facility; NLR reports an annualized PUE near 1.036.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://nrel.sitefinity.cloud\&sz=32)

NLR

&#x20;A constant-PUE model that works well here is not necessarily adequate for other cooling architectures.



Completion criterion: One small table showing how much reference PUE varies across 2023, how often the July-calibrated M0 is inaccurate, and whether the discrepancies exhibit a systematic pattern.

That evidence will give us a defensible reason either to retain M0 or to introduce M1/M2a.