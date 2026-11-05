## Step 04 — Understand overhead before fitting M1

The results justify investigating M1, but I recommend one final diagnostic before fitting it.

The important observation is that PUE and IT load are mathematically coupled:

\\[ PUE_t=1+\frac{P_t^{overhead}}{P_t^{IT}} \\]

Even if overhead is constant, PUE decreases as IT load increases. Therefore, the observed correlation of −0.79 does not establish that overhead depends on IT load.

We should examine overhead electricity directly, rather than PUE.

### 1. What we want to determine

Compare the two relationships:

M0 — Constant PUE

\\[ P_t^{overhead}=(k-1)P_t^{IT} \\]

M1 — Affine facility power

\\[ P_t^{DC}=a+bP_t^{IT} \\]

or equivalently,

\\[ \boxed{P_t^{overhead}=a+(b-1)P_t^{IT}} \\]

This gives us three possible outcomes:

| Observation                                          | Interpretation                                          |
| ---------------------------------------------------- | ------------------------------------------------------- |
| Overhead approximately constant                      | M1 with \\(b\approx1\\) is promising                    |
| Overhead changes approximately linearly with IT load | General affine M1 is promising                          |
| Overhead shows distinct operating regimes            | M1 may need additional operating or weather information |

Your reported monthly averages already suggest overhead might be relatively stable: roughly 55–60 kW at low load versus 60–80 kW at high load. These are only approximate values inferred from aggregated summaries, not direct measurements of hourly overhead.

### 2. Minimal code

Do not create another data-loading script. Reuse the validated `hourly` dictionary already constructed in `m0_daily.py`.

Append this code after the daily calculations:

```
# Step 04: overhead versus IT loadimport matplotlib.pyplot as plth = pd.concat(hourly, names=["day", "hour"])x = h["it_power_kw"]y = h["ref_kw"] - x  # Reference overhead (kW)# Simple numerical summary across IT-load levelsbins = pd.qcut(x, 4, duplicates="drop")summary = pd.DataFrame({"it_kw": x, "overhead_kw": y})print(    summary.groupby(bins, observed=True)    .agg(n=("overhead_kw", "size"),         it_kw=("it_kw", "median"),         overhead_kw=("overhead_kw", "median"))    .round(1))# Measured relationship versus the existing M0fig, ax = plt.subplots(figsize=(7, 4))sc = ax.scatter(    x, y,    c=h.index.get_level_values("hour").month,    cmap="viridis", s=6, alpha=0.25)limits = [x.min(), x.max()]ax.plot(    limits, [(k - 1) * v for v in limits],    "k--", label=f"M0 (k={k:.4f})")ax.set(xlabel="IT power (kW)", ylabel="Overhead power (kW)")ax.legend()fig.colorbar(sc, ax=ax, label="Month (2023)")fig.tight_layout()
```

This uses the same 300 complete days and the same hourly reference calculations as the previous experiment.

It produces just:

- One scatter plot showing hourly overhead against IT power, colored by month.
- One four-row table showing median overhead at different IT-load levels.

No additional fitting, dependencies, or datasets.

### 3. What matters when reviewing the result

Look for two things:

First: Does overhead actually increase with IT load?

If IT load increases substantially while overhead remains near the same value, this would strongly support the fixed-overhead interpretation underlying M1.

Second: Do different months show different overhead at similar IT loads?

This is essential because the high-load months coincide with autumn. We should avoid incorrectly attributing an operating or seasonal change to IT load alone.

The monthly colors will make that confounding easier to identify, although they cannot establish causality.

### 4. Next step, conditional on the evidence

If overhead appears reasonably affine, the next experiment should fit

\\[ \boxed{\hat P_t^{DC}=\hat a+\hat bP_t^{IT}} \\]

and compare M0 versus M1 on identical held-out days, using daily energy error and hourly MAE.

Unlike M0, M1 should be fitted on multiple days spanning different IT loads. We should use a chronological holdout and explicitly recognize when its test loads lie outside the training range.

Do not introduce weather or M2 yet.

Completion criterion: Determine whether the observed PUE variation primarily reflects fixed overhead divided by changing IT load, a genuinely load-dependent overhead, or distinct operating regimes.

That is the smallest meaningful experiment needed before moving from M0 to M1.