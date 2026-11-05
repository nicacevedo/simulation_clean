## Step 05 — Compare M0 with M1 on held-out data

The next critical experiment is to determine whether a fixed-overhead model generalizes better than constant PUE and unrestricted affine M1.

I checked the attached `runs.zip`, including `m0_daily.csv` and the overhead scatter plot. The results reveal something particularly valuable: allowing M1 to fit an unrestricted slope may actually reduce its ability to predict high-load periods because summer overhead and IT load are confounded.

### 1. The three models worth comparing

| Model                        | Equation               | Question                                        |
| ---------------------------- | ---------------------- | ----------------------------------------------- |
| M0 — Constant PUE            | \\(P^{DC}=kP^{IT}\\)   | Is proportional overhead sufficient?            |
| M1 — Affine                  | \\(P^{DC}=a+bP^{IT}\\) | Does fitting intercept and slope help?          |
| M1-fixed — Constant overhead | \\(P^{DC}=a+P^{IT}\\)  | Is overhead essentially independent of IT load? |

M1-fixed is simply M1 with \\(b=1\\). It is worth including because the cool-month observations strongly support this special case.

### 2. Recommended experiment

Use the existing `m0_daily.csv`, with no additional Parquet reads or preprocessing.

- Training: January–August 2023.
- Testing: September–December 2023.
- Data: 300 validated daily observations.
- Evaluation: Median and 90th-percentile absolute daily facility-energy error.
- Important: Fit all three models using exactly the same training days. Do not use the testing data to estimate coefficients.

Preliminary results from your attached data

Training days

# 218

Held-out days

# 82

| Model    | Fitted parameters                | Test median absolute error |
| -------- | -------------------------------- | -------------------------- |
| M0       | \\(k=1.0471\\)                   | 2.70%                      |
| M1       | \\(a=15.05\\) kW, \\(b=1.0374\\) | 2.20%                      |
| M1-fixed | \\(a=73.13\\) kW, \\(b=1\\)      | 0.32%                      |

These are calculations from the attached daily CSV, not independent facility-meter validation.

The result is revealing: the restricted one-parameter M1 model performs substantially better than the unrestricted two-parameter M1 in this chronological test.

The unrestricted model learns a positive load-dependent overhead slope, but the training period contains summer days with elevated overhead at intermediate loads. That makes its extrapolation to higher autumn loads inaccurate.

This supports testing whether constant overhead is a more useful representation for this facility. It does not yet establish that the true overhead slope is exactly zero.

### 3. Minimal code

Create one file:

`dc_resource_sim/src/experiments/m1_compare.py`

```
"""Step 05: M0 versus M1, chronological holdout."""import numpy as npimport pandas as pdCSV = "dc_resource_sim/runs/m0_daily.csv"df = pd.read_csv(CSV, parse_dates=["day"])train = df[df.day.dt.month <= 8]test = df[df.day.dt.month >= 9]assert len(train) == 218 and len(test) == 82# Fit using daily average power (kW)x = train.it_kwh / 24y = train.ref_dc_kwh / 24# M0: energy-weighted constant PUEk = train.ref_dc_kwh.sum() / train.it_kwh.sum()# M1: unrestricted affine powerb, a = np.polyfit(x, y, 1)# M1-fixed: constant overheada_fixed = (y - x).mean()print(f"M0:       k={k:.4f}")print(f"M1:       a={a:.2f} kW, b={b:.4f}")print(f"M1-fixed: a={a_fixed:.2f} kW, b=1")predictions = {    "M0": k * test.it_kwh,    "M1": 24 * a + b * test.it_kwh,    "M1-fixed": test.it_kwh + 24 * a_fixed,}
```

Run from the repository root using the established Conda environment.

The output should approximately reproduce:

| Model    | Median absolute error | 90th percentile | Mean signed error |
| -------- | --------------------- | --------------- | ----------------- |
| M0       | 2.70%                 | 2.95%           | +2.54%            |
| M1       | 2.20%                 | 2.44%           | +2.06%            |
| M1-fixed | 0.32%                 | 0.68%           | +0.22%            |

No new data extraction, solver, configuration file, or plot is needed.

### 4. What we should conclude

The experiment tests an important modeling choice:

- M0: Assumes overhead increases proportionally with IT power.
- M1: Allows fixed and load-dependent overhead.
- M1-fixed: Assumes overhead remains constant across different IT loads.

The preliminary results favor M1-fixed for this particular held-out period.

But two qualifications matter:

First, the result applies to the ESIF operating conditions represented by these data. It should not be generalized to all data-center architectures.

Second, this is not yet a definitive comparison of year-round model accuracy. The training period contains a summer overhead regime, while much of the test period represents high-load, cooler-month operation. A different time split could favor a different model.

### 5. What comes immediately afterward?

I recommend just one follow-up check before introducing weather:

Evaluate the three models separately for the summer and cool-month operating regimes.

This will help determine whether M1-fixed is adequate for general facility energy prediction or whether its errors are systematically concentrated during summer.

Only then should we test a weather-dependent overhead model such as

\\[ P^{DC}\_t=a+c(T_t-T_0)+bP^{IT}\_t. \\]

Do not implement it yet.

Step 05 completion criterion: Reproduce the three-model comparison, confirm that the fitted parameters make physical sense, and establish which model gives the most accurate held-out daily facility energy.

If the reported results reproduce, we have a particularly useful finding: a simpler fixed-overhead representation can predict facility energy more reliably than either constant PUE or an unrestricted affine model when the training data contain confounded operating regimes.