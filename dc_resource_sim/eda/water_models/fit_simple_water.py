"""EDA 02: can a reduced model reproduce simulated W2-Air process evaporation?

Run from the repository root:
    python dc_resource_sim/eda/water_models/fit_simple_water.py

Target everywhere: W2-Air *simulated process evaporation* from Step 20 `direct_evap`.
C0 and C1 are surrogates of that simulator, not water-meter predictors.
"""
import sys
from math import isclose
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.dont_write_bytecode = True  # keep src/experiments untouched
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src" / "experiments"))
import w2_air_first  # noqa: E402
from w2_air_first import direct_evap, SUPPLY_MAX_C  # noqa: E402

FIG = HERE / "figures"
BLUE, ORANGE, AQUA, GRAY, INK, INK2 = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#0b0b0b", "#52514e"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRAY, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": "#e6e5e0",
                     "grid.linewidth": 0.6, "lines.linewidth": 2, "font.size": 9})
IT_KW = 1000.0


def w2_intensity(t, rh, it_kw=IT_KW):
    """W2 evaporation in L/kWh IT, or None if the supply target is infeasible."""
    s = direct_evap(float(t), rh / 100, it_kw=it_kw)
    return None if s["mode"] == "infeasible" else s["evaporation_lph"] / it_kw


def excess(t):
    return np.maximum(np.asarray(t, float) - SUPPLY_MAX_C, 0.0)


# ---------------- Fit on training states (18-31 C, RH 20 %, 1 MW) ----------------
train = [(t, 20) for t in range(18, 32)]
train = [(t, rh, y) for t, rh in train if (y := w2_intensity(t, rh)) is not None]
assert len(train) == 14  # all feasible at RH 20 %
t_tr = np.array([r[0] for r in train], float)
y_tr = np.array([r[2] for r in train])
c0 = y_tr.mean()  # OLS of F = c0 * P with P fixed => mean intensity
x_tr = excess(t_tr)
beta = (x_tr @ y_tr) / (x_tr @ x_tr)  # OLS through origin on temperature excess
assert 0.097 <= beta <= 0.098, beta

# ---------------- Held-out states (32-38 C, RH 10-90 %) ----------------
held = [(t, rh, w2_intensity(t, rh)) for t in range(32, 39) for rh in range(10, 91, 5)]
feas = [(t, rh, y) for t, rh, y in held if y is not None]
n_infeasible = len(held) - len(feas)
t_te = np.array([r[0] for r in feas], float)
y_te = np.array([r[2] for r in feas])
err = {"C0": np.full_like(y_te, c0) - y_te, "C1": beta * excess(t_te) - y_te}  # L/kWh IT


def metrics(e):
    a = np.abs(e) * IT_KW  # L/h at 1 MW
    return a.mean(), np.percentile(a, 95), a.max()


# Training errors too, so C0's failure in dry mode is visible
err_tr = {"C0": c0 - y_tr, "C1": beta * x_tr - y_tr}

# ---------------- Structural load scaling (assumed linear heat boundary) ----------------
scaling = []
for t, rh in [(35, 30), (38, 20)]:
    for p in (800.0, 1200.0):
        f_w2 = direct_evap(float(t), rh / 100, it_kw=p)["evaporation_lph"]
        f_c1 = beta * p * (t - SUPPLY_MAX_C)
        assert isclose(f_w2 / p, w2_intensity(t, rh), rel_tol=1e-12)
        scaling.append((t, rh, p, f_w2, f_c1))

# ---------------- Figure 04 ----------------
fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.2))
for axx in (a, b):
    axx.axvspan(31.5, 38.5, color="#cde2fb", alpha=0.35, lw=0)
a.axvline(SUPPLY_MAX_C, color=INK2, lw=1, ls=":")
a.text(SUPPLY_MAX_C - 0.3, 0.7, "25 °C supply target", ha="right", fontsize=8, color=INK2)
a.text(35, 0.3, "held-out\n32–38 °C, RH 10–90 %", ha="center", fontsize=8, color=INK2)
tt = np.linspace(18, 38, 201)
a.plot(tt, np.full_like(tt, c0), color=ORANGE, label=f"C0 constant: c0 = {c0:.4f} L/kWh")
a.plot(tt, beta * excess(tt), color=BLUE,
       label=f"C1 temp. excess: β = {beta:.5f} L/(kWh·°C)")
a.plot(t_tr, y_tr, "o", ms=8, mfc=INK, mec="#fcfcfb", mew=1.5, label="W2 train (RH 20 %)")
a.plot(t_te, y_te, "o", ms=8, mfc="#fcfcfb", mec=INK, mew=1.5,
       label=f"W2 held-out feasible (n = {len(feas)})")
a.set_xlabel("Outdoor dry-bulb temperature (°C)")
a.set_ylabel("Simulated process evaporation (L/kWh IT)")
a.set_title("A. W2-Air evaporation intensity vs surrogates", fontsize=10, loc="left")
a.legend(fontsize=8, frameon=False, loc="upper left")
a.set_xlim(17.5, 38.5)

b.axhline(0, color=INK2, lw=1)
for name, color, off in [("C0", ORANGE, -0.12), ("C1", BLUE, 0.12)]:
    b.plot(t_te + off, err[name], "o", ms=8, color=color, mec="#fcfcfb", mew=1, label=name)
    b.plot(t_tr, err_tr[name], "o", ms=6, mfc="none", mec=color, mew=1.2)
b.text(24.5, -0.3, "training residuals\n(open markers)", ha="center", fontsize=8, color=INK2)
b.set_xlabel("Outdoor dry-bulb temperature (°C)")
b.set_ylabel("Prediction − W2 (L/kWh IT)")
b.set_title("B. Residuals (filled = held-out feasible)", fontsize=10, loc="left")
b.legend(fontsize=8, frameon=False, loc="lower left")
b.set_xlim(17.5, 38.5)
fig.suptitle("Surrogates of W2-Air simulated process evaporation (1 MW IT; supply 25 °C, ε_max 0.8, "
             "ΔT_server 15 °C) — not water-meter validation", fontsize=10, x=0.01, ha="left")
fig.text(0.01, 0.005, f"Held-out grid: {len(held)} states; {len(feas)} feasible (scored), "
         f"{n_infeasible} infeasible (excluded; N/A — C0/C1 cannot flag feasibility).",
         fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(FIG / "04_w2_air_surrogate_fit.png", dpi=160)
plt.close(fig)

# ---------------- Figure 05: transfer across server-air rise ----------------
T_OUT, RH_OUT = 30.0, 0.30
rises = [10.0, 15.0, 20.0]
original_rise = w2_air_first.SERVER_RISE_C
w2_rise = {}
try:
    for r in rises:
        w2_air_first.SERVER_RISE_C = r  # temporary EDA override; source unchanged
        w2_rise[r] = direct_evap(T_OUT, RH_OUT, it_kw=IT_KW)["evaporation_lph"]
finally:
    w2_air_first.SERVER_RISE_C = original_rise
assert w2_air_first.SERVER_RISE_C == 15.0
assert isclose(w2_rise[15.0], 489.36647, abs_tol=0.01)
c1_frozen = beta * IT_KW * (T_OUT - SUPPLY_MAX_C)
analytic = {r: c1_frozen * 15.0 / r for r in rises}

fig, ax = plt.subplots(figsize=(7, 4.2))
rr = np.linspace(9, 21, 121)
ax.plot(rr, c1_frozen * 15.0 / rr, color=AQUA, ls=":", label="β₁₅·(15/ΔT) analytical (not fitted)")
ax.axhline(c1_frozen, color=BLUE, label=f"C1 frozen at ΔT = 15 °C ({c1_frozen:.1f} L/h)")
ax.plot(rises, [w2_rise[r] for r in rises], "o", ms=9, color=INK, mec="#fcfcfb", mew=1.5,
        label="W2-Air simulated evaporation")
for r in rises:
    ax.annotate(f"{w2_rise[r]:.1f} L/h\n(×{w2_rise[r] / w2_rise[15.0]:.3f})", (r, w2_rise[r]),
                xytext=(8, 6), textcoords="offset points", fontsize=8, color=INK)
ax.set_xlabel("Assumed server-air temperature rise ΔT_server (°C)")
ax.set_ylabel("Simulated process evaporation (L/h)")
ax.set_xticks(rises)
ax.set_ylim(0, 900)
ax.set_title("W2-Air at 30 °C / 30 % RH, 1 MW IT: a temperature-only coefficient does not transfer",
             fontsize=10, loc="left")
ax.legend(fontsize=8, frameon=False, loc="lower left")
fig.text(0.01, 0.005, "Same heat input, different allowed air rise → different airflow and evaporation.\n"
         "IT energy is unchanged; fan power and return-air feasibility are not modeled.",
         fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(FIG / "05_airflow_control_transfer.png", dpi=160)
plt.close(fig)

# ---------------- Printed summary ----------------
print("\n=== EDA 02 summary ===")
print(f"Fit (n={len(train)} train, 18-31 C, RH 20%): c0={c0:.5f} L/kWh IT, beta={beta:.5f} L/(kWh IT*C)")
print(f"Held-out: {len(held)} states, feasible={len(feas)}, infeasible={n_infeasible} (excluded)")
print("Model  MAE L/h  P95 L/h  Max L/h   (held-out feasible, 1 MW)")
for name in ("C0", "C1"):
    mae, p95, mx = metrics(err[name])
    print(f"{name:<5} {mae:>8.2f} {p95:>8.2f} {mx:>8.2f}")
for name in ("C0", "C1"):
    mae, p95, mx = metrics(err_tr[name])
    print(f"{name} train: MAE {mae:.2f}, max {mx:.2f} L/h")
print("Load scaling (W2 vs C1, L/h):")
for t, rh, p, f_w2, f_c1 in scaling:
    print(f"  {t} C/{rh}% @ {p:.0f} kW: W2={f_w2:.1f}, C1={f_c1:.1f}, err={f_c1 - f_w2:+.2f}")
print("Server-rise transfer at 30 C/30%, 1 MW (L/h):")
for r in rises:
    print(f"  dT={r:g}: W2={w2_rise[r]:.2f} (x{w2_rise[r] / w2_rise[15.0]:.3f}), "
          f"C1 frozen={c1_frozen:.2f} (err {c1_frozen - w2_rise[r]:+.1f}), "
          f"analytic={analytic[r]:.2f} (err {analytic[r] - w2_rise[r]:+.2f})")
print("PASS: beta in expected range, infeasible excluded, scaling linear, SERVER_RISE_C restored")
