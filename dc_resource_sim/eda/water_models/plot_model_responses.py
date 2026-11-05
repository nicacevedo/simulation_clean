"""EDA after Step 26: response of existing water models (no new physics).

Run from the repository root:
    python dc_resource_sim/eda/water_models/plot_model_responses.py

Reuses Step 20 `direct_evap`, Step 18 `tower`, and the Step 26 day. Importing
those scripts re-runs (and prints) their own tests.
"""
import sys
from math import isclose
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch

sys.dont_write_bytecode = True  # keep src/experiments untouched
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "src" / "experiments"))
import w2_air_first  # noqa: E402
from w2_air_first import direct_evap  # noqa: E402
from w2_tower_heat_boundary import tower  # noqa: E402
from w2_air_day_first import WEATHER, run_day, IT_KW, M0_K, W0_L_PER_KWH, RECOVERY  # noqa: E402

FIG = HERE / "figures"
FIG.mkdir(exist_ok=True)
BLUE, ORANGE, AQUA, GRAY, INK2 = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#52514e"
SEQ = LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#6da7ec", "#2a78d6", "#184f95", "#0d366b"])
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": GRAY, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": "#e6e5e0",
                     "grid.linewidth": 0.6, "lines.linewidth": 2, "font.size": 9})
ANCHORS = {(20, 50): 0.0, (30, 30): 489.36647, (35, 30): 975.03504, (30, 70): None}

# ---------------- Figure 1: weather-response and feasibility map ----------------
temps = np.arange(18, 39, 1.0)
rhs = np.arange(10, 91, 5.0)
intensity = np.full((len(rhs), len(temps)), np.nan)  # NaN = infeasible (N/A, not 0)
mode = np.empty(intensity.shape, dtype=object)
for i, rh in enumerate(rhs):
    for j, t in enumerate(temps):
        s = direct_evap(t, rh / 100, it_kw=1000.0)
        mode[i, j] = s["mode"]
        if s["mode"] != "infeasible":
            assert s["evaporation_lph"] >= 0
            intensity[i, j] = s["evaporation_lph"] / 1000.0  # L/kWh IT

for (t, rh), ref in ANCHORS.items():
    s = direct_evap(float(t), rh / 100)
    if ref is None:
        assert s["mode"] == "infeasible"
    else:
        assert isclose(s["evaporation_lph"], ref, abs_tol=0.01), (t, rh)

fig, ax = plt.subplots(figsize=(7.5, 4.8))
ax.grid(False)
dt, dr = 0.5, 2.5
extent = [temps[0] - dt, temps[-1] + dt, rhs[0] - dr, rhs[-1] + dr]
ax.imshow(np.ones_like(intensity), extent=extent, origin="lower", aspect="auto",
          cmap=LinearSegmentedColormap.from_list("g", ["#e6e5e0"] * 2))
infeas = np.ma.masked_where(mode != "infeasible", np.ones_like(intensity))
ax.pcolor(temps, rhs, infeas, hatch="///", facecolor="none", edgecolor="#b5b4ad",
          linewidth=0, shading="nearest")
im = ax.imshow(np.ma.masked_invalid(np.where(mode == "wet", intensity, np.nan)),
               extent=extent, origin="lower", aspect="auto", cmap=SEQ, vmin=0)
dry = np.ma.masked_where(mode != "dry", np.ones_like(intensity))
ax.imshow(dry, extent=extent, origin="lower", aspect="auto",
          cmap=LinearSegmentedColormap.from_list("w", ["#fcfcfb"] * 2))
ax.axvline(25.5, color=INK2, lw=1, ls=":")
ax.text(21.5, 75, "DRY\n0 L/kWh IT\n(T_db ≤ 25 °C supply target)", ha="center", va="center",
        color=INK2, fontsize=8)
ax.text(36.4, 75, "INFEASIBLE\nN/A (not 0)\nneeds ε > 0.8", ha="center", va="center",
        color="#0b0b0b", fontsize=8, bbox=dict(fc="#fcfcfb", ec=GRAY, lw=0.5))
for (t, rh), ref in ANCHORS.items():
    label = "infeasible" if ref is None else f"{ref / 1000:.3f}"
    ax.plot(t, rh, "o", ms=8, mfc="#fcfcfb" if ref is None else "#0b0b0b", mec="#0b0b0b", mew=1.5)
    ax.annotate(f"{t}/{rh}: {label}", (t, rh), xytext=(6, 6), textcoords="offset points",
                fontsize=8, color="#0b0b0b",
                bbox=dict(fc="#fcfcfb", ec="none", alpha=0.85, pad=1))
cb = fig.colorbar(im, ax=ax, pad=0.02)
cb.set_label("Process evaporation intensity  F_evap / P_IT  (L/kWh IT)")
ax.set_xlabel("Outdoor dry-bulb temperature (°C)")
ax.set_ylabel("Outdoor relative humidity (%)")
ax.set_title("W2-Air direct evaporative — process evaporation boundary\n"
             "supply ≤ 25 °C, ε_max = 0.8, ΔT_server = 15 °C, f_air = 1, 101.325 kPa",
             fontsize=10, loc="left")
ax.legend(handles=[Patch(fc="#fcfcfb", ec=GRAY, label="dry: 0 modeled evaporation"),
                   Patch(fc="#e6e5e0", ec=GRAY, hatch="///", label="infeasible: N/A")],
          loc="lower right", fontsize=8, framealpha=0.9)
fig.tight_layout()
fig.savefig(FIG / "01_air_weather_feasibility.png", dpi=160)
plt.close(fig)

# RH dependence at fixed T among wet cells (variation across RH, relative to mean)
rh_spread = {t: np.nanmax(intensity[:, j]) / np.nanmin(intensity[:, j]) - 1
             for j, t in enumerate(temps) if t > 25 and np.isfinite(intensity[:, j]).sum() > 1}
feasible_rh_max = {t: rhs[np.isfinite(intensity[:, j])].max() for j, t in enumerate(temps) if t > 25}

# ---------------- Figure 2: heat/load -> water by architecture ----------------
it = np.linspace(500, 1500, 11)  # kW IT = server-air heat (f_air = 1)
air_curves = {}
for t, rh in [(20, 50), (30, 30), (35, 30)]:
    y = np.array([direct_evap(float(t), rh / 100, it_kw=p)["evaporation_lph"] for p in it])
    coef = y / it
    assert np.allclose(coef, coef[5], rtol=1e-12)  # straight line through zero
    air_curves[(t, rh)] = (y, coef[5])
assert isclose(air_curves[(30, 30)][1], 0.48937, abs_tol=1e-5)
assert isclose(air_curves[(35, 30)][1], 0.97504, abs_tol=1e-5)

q_wet = np.linspace(600, 1800, 13)  # kW thermal tower duty, NOT IT power
tw = np.array([tower(q, 0.8, 4.0) for q in q_wet])  # (evap, makeup) L/h with dt = 1 h
assert (tw[:, 1] >= tw[:, 0]).all()
e1200, m1200 = tower(1200.0, 0.8, 4.0)
assert isclose(e1200, 1410.6, abs_tol=0.1) and isclose(m1200, 1880.8, abs_tol=0.1)

fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
for (key, color) in zip([(35, 30), (30, 30), (20, 50)], [BLUE, AQUA, GRAY]):
    y, c = air_curves[key]
    a.plot(it, y, color=color)
    dy = -120 if key == (30, 30) else 0  # avoid the nearly coincident W0 label
    a.text(it[-1] + 15, y[-1] + dy, f"{key[0]} °C/{key[1]}%\n{c:.3f} L/kWh", va="center",
           fontsize=8, color="#0b0b0b")
a.plot(it, W0_L_PER_KWH * it, color=INK2, lw=1, ls="--")
a.text(it[-1] + 15, W0_L_PER_KWH * it[-1] + 140, "W0 proxy\n0.5 L/kWh", va="center", fontsize=8, color=INK2)
a.set_xlim(500, 1800)
a.set_xlabel("IT power = server-air heat (kW)")
a.set_ylabel("Water rate (L/h)")
a.set_title("A. W2-Air direct evaporative — process evaporation\n"
            "(dashed W0 = consumption proxy, not a meter quantity)", fontsize=10, loc="left")
b.plot(q_wet, tw[:, 1], color=ORANGE, label="tower makeup")
b.plot(q_wet, tw[:, 0], color=BLUE, label="tower evaporation")
b.plot([1200, 1200], [e1200, m1200], "o", ms=8, color="#0b0b0b")
b.annotate(f"1200 kW_th:\nevap {e1200:,.1f} L/h\nmakeup {m1200:,.1f} L/h", (1200, m1200),
           xytext=(-95, 25), textcoords="offset points", fontsize=8,
           arrowprops=dict(arrowstyle="-", color=GRAY))
for y, lab in [(tw[-1, 1], "makeup"), (tw[-1, 0], "evaporation")]:
    b.text(q_wet[-1] + 20, y, lab, va="center", fontsize=8, color="#0b0b0b")
b.set_xlim(600, 2000)
b.set_xlabel("Tower wet heat duty Q_wet (kW thermal — not IT power, not M0)")
b.set_title("B. W2-Tower (Step 18 simple) — evaporation & makeup\n"
            "α_lat = 0.8, COC = 4", fontsize=10, loc="left")
b.legend(loc="lower right", fontsize=8, frameon=False)
fig.suptitle("Heat → water slopes differ by architecture and boundary; panels are not one function",
             fontsize=10, x=0.01, ha="left")
fig.tight_layout()
fig.savefig(FIG / "02_heat_water_by_architecture.png", dpi=160)
plt.close(fig)

# Optional numeric sensitivity (no plot): server air rise and treatment recovery.
base = direct_evap(30.0, 0.30)["evaporation_lph"]
w2_air_first.SERVER_RISE_C = 10.0  # temporary override of the module default
rise10 = direct_evap(30.0, 0.30)["evaporation_lph"]
w2_air_first.SERVER_RISE_C = 15.0
rise_factor = rise10 / base
feed_factor = (base / 0.8) / (base / 1.0)

# ---------------- Figure 3: the Step 26 constructed day ----------------
rows, day = run_day(WEATHER)
assert day is not None and (day["dry_hours"], day["wet_hours"]) == (8, 16)
for r in rows:
    assert isclose(r["feed_lph"], r["evap_lph"] + r["reject_lph"], abs_tol=1e-9)
assert isclose(day["evap"], 11715.2, abs_tol=0.1)
assert isclose(day["feed"], 14644.0, abs_tol=0.1)
assert isclose(day["reject"], 2928.8, abs_tol=0.1)
assert isclose(day["peak_feed_lph"], 1218.8, abs_tol=0.1)
assert isclose(day["w0_direct_proxy_l"], 12000.0) and isclose(day["m0_facility_kwh"], 25130.4)

stress = list(WEATHER)
stress[10] = (30.0, 0.70)
stress_rows, stress_day = run_day(stress)
assert stress_rows[10]["mode"] == "infeasible" and stress_day is None  # test only, no figure

hours = np.arange(25)  # step edges
step = lambda key: np.append([r[key] for r in rows], rows[-1][key])
fig, (ax_t, ax_rh, ax_w) = plt.subplots(3, 1, figsize=(8.5, 6.6), sharex=True,
                                        gridspec_kw=dict(height_ratios=[1, 1, 2.2]))
for axx in (ax_t, ax_rh, ax_w):
    for r in rows:
        if r["mode"] == "wet":
            axx.axvspan(r["hour"], r["hour"] + 1, color="#cde2fb", alpha=0.35, lw=0)
ax_t.step(hours, step("temp_c"), where="post", color=ORANGE)
ax_t.axhline(25, color=INK2, lw=1, ls=":")
ax_t.text(0.2, 25.6, "25 °C supply target", fontsize=8, color=INK2)
ax_t.set_ylabel("Dry-bulb (°C)")
ax_t.set_ylim(15, 40)
ax_rh.step(hours, 100 * step("rh"), where="post", color=AQUA)
ax_rh.set_ylabel("RH (%)")
ax_rh.set_ylim(0, 70)
ax_t.set_title("Step 26 constructed day (NOT measured weather) — 1 MW IT constant, "
               f"M0 facility {M0_K * IT_KW:.1f} kW constant", fontsize=10, loc="left")
ax_w.step(hours, step("feed_lph"), where="post", color=ORANGE)
ax_w.step(hours, step("evap_lph"), where="post", color=BLUE)
ax_w.step(hours, step("w0_proxy_lph"), where="post", color=INK2, lw=1, ls="--")
lbl = [(day["feed"], step("feed_lph")[-1], "W2 treatment feed (η = 0.8)", ORANGE),
       (day["evap"], step("evap_lph")[-1], "W2 process evaporation", BLUE),
       (day["w0_direct_proxy_l"], 500.0, "W0 direct-consumption proxy", INK2)]
for total, y, name, _ in lbl:
    ax_w.text(24.2, y, f"{name}\nday total {total:,.0f} L", va="center", fontsize=8, color="#0b0b0b")
ax_w.annotate(f"peak feed {day['peak_feed_lph']:,.1f} L/h (rate)", (20, day["peak_feed_lph"]),
              xytext=(-150, 12), textcoords="offset points", fontsize=8,
              arrowprops=dict(arrowstyle="-", color=GRAY))
ax_w.text(4, 650, "dry: W2 = 0\n(W0 proxy still 500 L/h)", ha="center", fontsize=8, color=INK2)
ax_w.text(12, 1080, "wet (shaded)", ha="center", fontsize=8, color=INK2)
ax_w.set_ylabel("Water rate (L/h)")
ax_w.set_ylim(-30, 1400)
ax_w.set_xlabel("Hour of day")
ax_w.set_xlim(0, 24)
ax_w.set_xticks(range(0, 25, 4))
fig.text(0.01, 0.005, "W0 (consumption proxy) and W2 (process evaporation / treatment feed) have "
         "different water boundaries; overlay is model behavior, not a prediction error.",
         fontsize=7.5, color=INK2)
fig.tight_layout(rect=(0, 0.02, 0.8, 1))
fig.savefig(FIG / "03_constructed_day_profiles.png", dpi=160)
plt.close(fig)

# ---------------- Summary for results.md ----------------
print("\n=== EDA summary ===")
print(f"Fig1 grid {len(temps)}x{len(rhs)}: dry={np.sum(mode == 'dry')}, "
      f"wet={np.sum(mode == 'wet')}, infeasible={np.sum(mode == 'infeasible')}")
for t in [27.0, 30.0, 33.0, 35.0, 38.0]:
    j = list(temps).index(t)
    col = intensity[:, j]
    print(f"  T={t:g}: intensity {np.nanmin(col):.3f}-{np.nanmax(col):.3f} L/kWh "
          f"(RH spread {rh_spread[t]:.3%}), feasible up to RH {feasible_rh_max[t]:g}%")
print(f"Fig2 W2-Air coefs (L/kWh IT): " +
      ", ".join(f"{k[0]}/{k[1]}={v[1]:.5f}" for k, v in air_curves.items()))
print(f"Fig2 tower: evap {tw[0, 0] / q_wet[0]:.4f} L/kWh_th, makeup {tw[0, 1] / q_wet[0]:.4f} L/kWh_th; "
      f"at 1200 kW_th evap={e1200:.1f}, makeup={m1200:.1f} L/h")
print(f"Sensitivity @30C/30%: rise 15->10 C x{rise_factor:.3f} evaporation; "
      f"eta 1->0.8 x{feed_factor:.3f} feed (evaporation unchanged)")
print(f"Fig3: evap={day['evap']:.1f} L, feed={day['feed']:.1f} L, reject={day['reject']:.1f} L, "
      f"peak feed={day['peak_feed_lph']:.1f} L/h, W0={day['w0_direct_proxy_l']:.0f} L, "
      f"M0={day['m0_facility_kwh']:.1f} kWh")
print("Stress hour 10 at 30C/70%: infeasible -> full-day W2 total N/A")
print("PASS: anchors, linear scaling, balances, masking, Step 26 totals")
