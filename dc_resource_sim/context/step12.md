## Step 12 — Test whether weather improves facility-capacity predictions

Step 11 is complete. The results justify testing one weather-dependent overhead model, but not a more complicated power model.

The key findings are:

- Summer: M1-fixed underpredicts facility power in 94.1% of hours; 77% exceed its training-derived safety allowance.
- High-load months: M1-fixed is generally accurate, although occasional large errors remain. M0 is conservative throughout this particular held-out period.
- Decision implication: The violations in Steps 09–10 were counterfactual model comparisons. Step 11 identifies where underprediction actually occurs in historical ESIF measurements.

The strongest remaining question is:

Can one measured weather variable explain enough of the summer overhead increase to reduce capacity risk without sacrificing high-load performance?

### 1. Model to test

Keep the two existing baselines and add only one model.

| Model     | Facility power                 | Purpose                    |
| --------- | ------------------------------ | -------------------------- |
| M0        | \\(kP\_{IT}\\)                 | Constant-PUE baseline      |
| M1-fixed  | \\(P\_{IT}+a\\)                | Constant-overhead baseline |
| M2a-fixed | \\(P\_{IT}+a+c(T\_{wb}-T_0)\\) | Weather-dependent overhead |

Use outdoor wet-bulb temperature as the single new predictor, consistent with the earlier ESIF EDA. The notebooks already established weather associations in cooling electricity, so we are not repeating that exploratory work.

The purpose here is specifically to test held-out hourly underprediction and capacity headroom in 2023.

Keep the IT-power coefficient fixed at 1. Do not introduce unrestricted M2a, interactions, cooling-state classifications, or nonlinear temperature terms.

### 2. Data and training

Use the existing `esif_hourly_2023.csv` containing the 7,200 validated observations.

Add only an hourly outdoor wet-bulb series from the existing ESIF weather source used in the notebooks.

Before fitting:

- Confirm that the weather data actually cover 2023 and refer to the ESIF location.
- Preserve the existing UTC interpretation and verify alignment.
- Use the previously validated wet-bulb calculation; do not substitute Springfield weather.
- Use only timestamps where both power and weather are available, with identical rows for all models.
- Report coverage and the weather range in training versus testing. Do not silently fill missing observations.

Retain the same chronological experiments:

| Experiment               | Training | Testing |
| ------------------------ | -------- | ------- |
| Summer generalization    | Jan–Apr  | May–Aug |
| High-load generalization | Jan–Aug  | Sep–Dec |

Fit each model separately using its training period only.

Important: The summer test may contain temperatures outside the January–April training range. We must explicitly report that extrapolation rather than interpreting poor predictions as proof that weather is irrelevant.

### 3. Minimal implementation

Create one script:

`dc_resource_sim/src/experiments/s4_weather_overhead.py`

Leave the existing scripts unchanged.

Prepare a small weather CSV with `timestamp_utc,twb_c` using the existing EDA weather-processing code. Then compare the three models:

```
"""Step 12: Does wet-bulb improve hourly capacity predictions?"""import numpy as npimport pandas as pdROOT = "dc_resource_sim/runs/"power = pd.read_csv(ROOT + "esif_hourly_2023.csv")weather = pd.read_csv(ROOT + "esif_weather_hourly_2023.csv")for d in (power, weather):    d["timestamp_utc"] = pd.to_datetime(d["timestamp_utc"], utc=True)    assert d.timestamp_utc.is_uniquedf = power.merge(weather, on="timestamp_utc", validate="one_to_one")df = df.dropna(subset=["it_power_kw", "ref_dc_kw", "twb_c"])print(f"Matched hours: {len(df)} / {len(power)}")month = df.timestamp_utc.dt.monthsplits = {    "Summer": (month <= 4, month.between(5, 8)),    "High-load": (month <= 8, month >= 9),}for label, (tr, te) in splits.items():    train, test = df.loc[tr], df.loc[te]    assert len(train) > 0 and len(test) > 0    # Fit exclusively on training observations    k = train.ref_dc_kw.sum() / train.it_power_kw.sum()    a_fixed = (train.ref_dc_kw - train.it_power_kw).mean()    t0 = train.twb_c.mean()    X = np.column_stack([np.ones(len(train)), train.twb_c - t0])    a, c = np.linalg.lstsq(
```