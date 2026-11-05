"""Five-figure research summary: generates F1, F2, F5 and the supporting grid-water figure S1.

F3/F4 are reused unchanged from eda/water_models/figures/ (linked in README.md).
Run from the repository root:
    python dc_resource_sim/eda/summary/make_summary_figures.py

Nothing is refit beyond the F1 train-only holdout coefficients (same definitions as
src/experiments/s5_affine_weather.py); no optimization or water simulation is run. F1 and F5 read saved experiment outputs
(runs/esif_hourly_2023.csv, runs/m0_daily.csv, water_models/schedule_decision_summary.csv).
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[1] / "runs"
OUT = HERE / "figures"
OUT.mkdir(parents=True, exist_ok=True)

COLORS = {"M0": "#2a78d6", "M1-fixed": "#eb6834", "M2a-fixed": "#1baf7a",
          "C0": "#2a78d6", "C1": "#eb6834"}
INK, MUTED, GRID = "#222222", "#666666", "#e3e3e3"
plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "savefig.dpi": 180, "savefig.bbox": "tight",
})


def check(name, got, expected, tol):
    if abs(got - expected) > tol:
        raise SystemExit(f"Anchor mismatch {name}: got {got:.4f}, expected {expected} ± {tol}")


def save(fig, name):
    path = OUT / name
    if path.exists():
        print(f"Overwriting this script's own output {path.name}")
    fig.savefig(path)
    plt.close(fig)
    print(f"Wrote {path}")


power = pd.read_csv(RUNS / "esif_hourly_2023.csv")
weather = pd.read_csv(RUNS / "esif_weather_hourly_2023.csv")
for d in (power, weather):
    d["timestamp_utc"] = pd.to_datetime(d["timestamp_utc"], utc=True)

# ---------------- F1: facility overhead vs IT load and season ----------------
# k fixed from 2023-07-01 (Step 02); seasons are the Step 06/07 periods
k_m0 = pd.read_csv(RUNS / "m0_daily.csv", index_col="day").loc["2023-07-01 00:00:00+00:00", "ref_pue"]
check("F1 k", k_m0, 1.0474, 5e-5)
oh = power.assign(overhead_kw=power.ref_dc_kw - power.it_power_kw,
                  season=pd.cut(power.timestamp_utc.dt.month, [0, 4, 8, 12],
                                labels=["Jan–Apr", "May–Aug", "Sep–Dec"]))
season_colors = {"Jan–Apr": "#2a78d6", "May–Aug": "#eb6834", "Sep–Dec": "#1baf7a"}

fig, ax = plt.subplots(figsize=(8.5, 5))
for season, g in oh.groupby("season", observed=True):
    ax.scatter(g.it_power_kw, g.overhead_kw, s=5, alpha=0.25, color=season_colors[season],
               rasterized=True)
    ax.scatter([], [], s=30, color=season_colors[season],
               label=f"{season}: median {g.overhead_kw.median():.0f} kW (n = {len(g):,} h)")
xs = np.array([oh.it_power_kw.min(), oh.it_power_kw.max()])
ax.plot(xs, (k_m0 - 1) * xs, "k--", lw=1.5, label=f"M0 overhead, k = {k_m0:.4f} (fit Jul 1)")
ax.set_xlabel("IT power (kW)")
ax.set_ylabel("Facility overhead = facility − IT (kW)")
ax.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left", fontsize=9.5)
ax.set_title("F1. Facility overhead varies by operating season and is not simply proportional to IT load",
             loc="left", fontsize=13, fontweight="bold", pad=24)
ax.text(0, 1.03, f"2023 ESIF hourly, {len(oh):,} h on complete days. Reference = measured IT × reported PUE "
        "(not a facility meter).", transform=ax.transAxes, fontsize=9, color=MUTED)
save(fig, "01_facility_overhead.png")

# ---------------- F2: power-model transfer ----------------
# Inner merge + dropna: identical rows for every model, nothing filled
df = power.merge(weather, on="timestamp_utc", validate="one_to_one")
df = df.dropna(subset=["it_power_kw", "ref_dc_kw", "twb_c"])
assert len(df) == 7050, len(df)

month = df.timestamp_utc.dt.month
splits = {"Warm holdout\ntrain Jan–Jul, test Aug": (month <= 7, month == 8),
          "High-load holdout\ntrain Jan–Aug, test Sep–Dec": (month <= 8, month >= 9)}
expected = {  # (MAE kW, % test hours above training h95), visualizations01.md table
    ("Warm", "M0"): (14.36, 0.80), ("Warm", "M1-fixed"): (23.15, 2.71),
    ("Warm", "M2a-fixed"): (11.63, 0.32), ("High-load", "M0"): (84.89, 0.00),
    ("High-load", "M1-fixed"): (12.85, 0.25), ("High-load", "M2a-fixed"): (9.19, 0.71),
}

rows = []
for label, (tr, te) in splits.items():
    train, test = df.loc[tr], df.loc[te]
    t0 = train.twb_c.mean()
    overhead = train.ref_dc_kw - train.it_power_kw
    k = train.ref_dc_kw.sum() / train.it_power_kw.sum()
    a1 = overhead.mean()
    a2, c2 = np.linalg.lstsq(np.column_stack([np.ones(len(train)), train.twb_c - t0]),
                             overhead, rcond=None)[0]
    predictors = {
        "M0": lambda d: k * d.it_power_kw,
        "M1-fixed": lambda d: d.it_power_kw + a1,
        "M2a-fixed": lambda d: d.it_power_kw + a2 + c2 * (d.twb_c - t0),
    }
    for model, predict in predictors.items():
        # Positive error = underprediction; h95 from training errors only
        h95 = max(0.0, (train.ref_dc_kw - predict(train)).quantile(0.95))
        e_test = test.ref_dc_kw - predict(test)
        mae, exceed = e_test.abs().mean(), 100 * (e_test > h95).mean()
        key = (label.split(" ")[0], model)
        check(f"F1 MAE {key}", mae, expected[key][0], 0.1)
        check(f"F1 exceedance {key}", exceed, expected[key][1], 0.05)
        rows.append((label, model, mae, exceed, len(train), len(test)))
f1 = pd.DataFrame(rows, columns=["split", "model", "mae", "exceed", "n_train", "n_test"])

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharey=True)
models = list(predictors)
ypos, yticks, ylabels = {}, [], []
for i, label in enumerate(splits):
    for j, model in enumerate(models):
        ypos[(label, model)] = i * 4.2 + (2 - j)
    n = f1[f1.split == label].iloc[0]
    yticks.append(i * 4.2 + 1)
    ylabels.append(f"{label}\n(n train {n.n_train:,} h, test {n.n_test:,} h)")
for ax, col, xlabel, fmt in [
        (axes[0], "mae", "Held-out hourly MAE (kW)", "{:.1f}"),
        (axes[1], "exceed", "Held-out hours with underprediction > training $h_{95}$ (%)", "{:.2f}")]:
    xmax = f1[col].max()
    for r in f1.itertuples():
        y = ypos[(r.split, r.model)]
        v = getattr(r, col)
        ax.barh(y, v, height=0.75, color=COLORS[r.model], label=r.model)
        label = fmt.format(v) + (f" ({round(v * r.n_test / 100)} h)" if col == "exceed" else "")
        ax.text(v + xmax * 0.015, y, f"{label}  {r.model}", va="center",
                fontsize=10, color=INK)
    ax.set_xlim(0, xmax * 1.45)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
axes[0].set_yticks(yticks, ylabels)
axes[0].invert_yaxis()
handles, labels = axes[0].get_legend_handles_labels()
uniq = dict(zip(labels, handles))
fig.legend(uniq.values(), uniq.keys(), loc="lower center", ncol=3, frameon=False,
           bbox_to_anchor=(0.55, -0.11))
fig.suptitle("F2. Lower prediction error does not guarantee lower underprediction risk", x=0.02, y=1.0, ha="left",
             fontsize=14, fontweight="bold")
fig.text(0.02, 0.86, "2023 ESIF, same weather-matched hours per model; historical holdouts. "
         "Reference = ESIF measured IT / PUE-implied facility power (not a facility meter).\n"
         "Right panel: few held-out hours (counts in brackets); a prediction diagnostic, not observed violations.",
         fontsize=10, color=MUTED)
fig.subplots_adjust(top=0.76, wspace=0.08)
save(fig, "02_power_model_transfer.png")

# ---------------- S1 (supporting): cost vs grid-water decision ----------------
# Provenance: Step 15 (July 1 2023, Springfield/MISO prices + modeled average grid-water
# consumption factors in runs/price_water_24h.csv, scheduled with s7_water_schedule.py)
# did not save structured outputs; these are the three verified point values from
# visualizations01.md. Ranking-reversal threshold ±0.0239 L/kWh is from Step 16.
schedules = {  # name: ($/day, grid-water L/day)
    "Cost-optimal": (834.32, 43982.4),
    "Baseline": (862.05, 43944.9),
    "Water-optimal": (865.55, 43859.9),
}
ref_cost, ref_water = schedules["Cost-optimal"]
deltas = {k: (c - ref_cost, w - ref_water) for k, (c, w) in schedules.items()}
for k, (dc, dw) in zip(deltas, [(0, 0), (27.73, -37.5), (31.23, -122.5)]):
    check(f"S1 {k} cost", deltas[k][0], dc, 0.01)
    check(f"S1 {k} water", deltas[k][1], dw, 0.2)

fig, ax = plt.subplots(figsize=(8, 5.2))
offsets = {"Cost-optimal": (10, 8), "Baseline": (-10, 10), "Water-optimal": (-10, 10)}
for k, (dc, dw) in deltas.items():
    ax.scatter(dc, dw, s=80, color="#2a78d6", edgecolor="white", lw=1.5, zorder=3)
    ha = "left" if offsets[k][0] > 0 else "right"
    ax.annotate(f"{k}\n${schedules[k][0]:.2f}/day, {schedules[k][1]:,.1f} L/day",
                (dc, dw), textcoords="offset points", xytext=offsets[k], ha=ha,
                fontsize=9.5, color=INK)
ax.axhline(0, color=MUTED, lw=0.8)
ax.axvline(0, color=MUTED, lw=0.8)
ax.set_xlim(-6, 40)
ax.set_ylim(-200, 40)
ax.set_xlabel("Additional electricity cost vs cost-optimal ($/day)")
ax.set_ylabel("Change in modeled grid-water consumption\nvs cost-optimal (L/day)")
ax.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.text(0.02, 0.05,
        "122.5 L/day ranking advantage of water-optimal over cost-optimal reverses under an\n"
        "adversarial hour-patterned factor error of ±0.0239 L/kWh (Step 16 threshold, not a CI).\n"
        "≈0.2% of ≈56,000 L/day modeled total. All schedules: 12,000 L/day direct W0 (unchanged).",
        transform=ax.transAxes, fontsize=9, color=INK,
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GRID))
ax.set_title("S1. Modeled grid-water scheduling gains are small and fragile",
             loc="left", fontsize=13, fontweight="bold", pad=24)
ax.text(0, 1.03, "July 1 2023 Springfield/MISO scenario; modeled average grid-water consumption "
        "factors, not marginal or measured savings", transform=ax.transAxes, fontsize=9,
        color=MUTED)
save(fig, "s1_cost_gridwater_decision.png")

# ---------------- F5: Step 30 water-model decision value ----------------
s30 = pd.read_csv(HERE.parent / "water_models" / "schedule_decision_summary.csv").set_index("policy")
for name, (evap, regret, peak) in {"no_shift": (8680.498, 221.717, 1353.818),
                                   "C1_optimal": (8458.781, 0.0, 1451.983),
                                   "W2_optimal": (8458.781, 0.0, 1451.983)}.items():
    check(f"F5 {name} evap", s30.loc[name, "w2_evaporation_l"], evap, 0.01)
    check(f"F5 {name} regret", s30.loc[name, "conditional_regret_l"], regret, 0.01)
    check(f"F5 {name} peak", s30.loc[name, "peak_feed_lph"], peak, 0.01)

labels = {"no_shift": "No shift", "C1_optimal": "C1-optimal", "W2_optimal": "W2-optimal"}
bar_colors = ["#999999", COLORS["C1"], "#222222"]
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6))
for ax, col, ylabel, unit in [
        (axes[0], "w2_evaporation_l", "Daily W2 process evaporation (L)", "L"),
        (axes[1], "peak_feed_lph", "Peak treatment feed (L/h, 80% recovery)", "L/h")]:
    v = s30[col].to_numpy(float)
    ax.bar([labels[p] for p in s30.index], v, color=bar_colors, width=0.6)
    for xi, vi in enumerate(v):
        ax.text(xi, vi * 1.01, f"{vi:,.1f} {unit}", ha="center", fontsize=10, color=INK)
    ax.set_ylim(0, v.max() * 1.15)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
save_pct = 100 * s30.loc["no_shift", "conditional_regret_l"] / s30.loc["no_shift", "w2_evaporation_l"]
peak_pct = 100 * (s30.loc["W2_optimal", "peak_feed_lph"] / s30.loc["no_shift", "peak_feed_lph"] - 1)
axes[0].set_title(f"A. Shifting saves {save_pct:.1f}%; C1 regret under W2 = "
                  f"{s30.loc['C1_optimal', 'conditional_regret_l']:.0f} L", loc="left", fontsize=11)
axes[1].set_title(f"B. The same schedule raises peak feed {peak_pct:.1f}%", loc="left", fontsize=11)
fig.suptitle("F5. C1 keeps the W2 water-optimal decision, but lower daily water raises the peak",
             x=0.02, ha="left", fontsize=14, fontweight="bold")
fig.text(0.02, 0.885, "Step 30: one measured-weather day (2023-07-24), hypothetical 1 MW direct-air site, "
         "20% flexible load. Simulated evaporation, not observed savings;\nequal objectives need not mean "
         "identical hourly schedules.", fontsize=9.5, color=MUTED)
fig.subplots_adjust(top=0.76, wspace=0.3)
save(fig, "05_step30_decision_value.png")
