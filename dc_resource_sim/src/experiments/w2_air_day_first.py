"""Step 26: one controlled 24-hour W2-Air trajectory.

All weather values and equipment parameters are illustrative.
Model outputs are not measured site water intake or total consumption.
"""
from math import isclose
from w2_air_first import direct_evap

IT_KW = 1000.0
M0_K = 1.0471
W0_L_PER_KWH = 0.5
RECOVERY = 0.8
HOURS = 24

# Three known Step 20 cases, 8 hours each. NOT measured weather.
WEATHER = [(20.0, 0.50)] * 8 + [(30.0, 0.30)] * 8 + [(35.0, 0.30)] * 8
assert len(WEATHER) == HOURS


def run_day(weather, print_hours=False):
    """Return results only if ALL hours meet the modeled supply target."""
    assert len(weather) == HOURS
    rows = []
    for hour, (temp_c, rh) in enumerate(weather):
        state = direct_evap(temp_c, rh, it_kw=IT_KW)
        row = {"hour": hour, "temp_c": temp_c, "rh": rh,
               "mode": state["mode"], "m0_kw": M0_K * IT_KW,
               "it_heat_kw": IT_KW, "w0_proxy_lph": W0_L_PER_KWH * IT_KW}
        if state["mode"] != "infeasible":
            evap = state["evaporation_lph"]
            feed = evap / RECOVERY
            reject = feed - evap
            assert isclose(feed, evap + reject, abs_tol=1e-9)
            assert evap >= 0 and reject >= 0
            row.update(evap_lph=evap, feed_lph=feed, reject_lph=reject)
        else:
            # Unknown fallback: no valid amount of water for fully served cooling.
            row.update(evap_lph=None, feed_lph=None, reject_lph=None)
        rows.append(row)

    if print_hours:
        print("hour  T(C)  RH   mode        evap(L/h)  feed(L/h)  reject(L/h)")
        for r in rows:
            fmt = lambda key: "n/a" if r[key] is None else f"{r[key]:.1f}"
            print(f"{r['hour']:02d}    {r['temp_c']:>4.0f}  {r['rh']:.0%}  "
                  f"{r['mode']:<10}  {fmt('evap_lph'):>9}  "
                  f"{fmt('feed_lph'):>9}  {fmt('reject_lph'):>11}")

    n_infeasible = sum(r["mode"] == "infeasible" for r in rows)
    if n_infeasible:
        return rows, None  # Never add partial hours into a "daily cooling" total.

    totals = {name: sum(r[f"{name}_lph"] for r in rows)
              for name in ["evap", "feed", "reject"]}  # 1 hour per row => L/day
    totals["peak_feed_lph"] = max(r["feed_lph"] for r in rows)
    totals["m0_facility_kwh"] = sum(r["m0_kw"] for r in rows)
    totals["it_heat_kwh_th"] = sum(r["it_heat_kw"] for r in rows)
    totals["w0_direct_proxy_l"] = sum(r["w0_proxy_lph"] for r in rows)
    totals["dry_hours"] = sum(r["mode"] == "dry" for r in rows)
    totals["wet_hours"] = sum(r["mode"] == "wet" for r in rows)
    return rows, totals


rows, day = run_day(WEATHER, print_hours=True)
assert day is not None
assert (day["dry_hours"], day["wet_hours"]) == (8, 16)
assert isclose(day["m0_facility_kwh"], 25130.4, abs_tol=1e-6)
assert isclose(day["it_heat_kwh_th"], 24000.0, abs_tol=1e-6)
assert isclose(day["w0_direct_proxy_l"], 12000.0, abs_tol=1e-6)
assert isclose(day["feed"], day["evap"] + day["reject"], abs_tol=1e-6)
assert isclose(day["evap"], 8 * (489.36647 + 975.03504), abs_tol=0.01)
print("\n24h: dry=%d, wet=%d, infeasible=0" % (day["dry_hours"], day["wet_hours"]))
print(f"M0 facility={day['m0_facility_kwh']:.1f} kWh; "
      f"IT heat={day['it_heat_kwh_th']:.1f} kWh thermal; "
      f"W0 proxy={day['w0_direct_proxy_l']:.1f} L")
print(f"W2 evaporation={day['evap']:.1f} L; "
      f"treatment feed={day['feed']:.1f} L; "
      f"reject={day['reject']:.1f} L; "
      f"peak feed={day['peak_feed_lph']:.1f} L/h")

# One-hour failure test: humid weather cannot achieve temperature target.
stress = list(WEATHER)
stress[10] = (30.0, 0.70)
stress_rows, stress_day = run_day(stress)
assert stress_rows[10]["mode"] == "infeasible"
assert stress_rows[10]["feed_lph"] is None
assert stress_day is None
print("Humid-hour control: infeasible; full-day W2 total = N/A (no fallback).")
print("PASS: hourly heat/water accounting, feasibility, 24h totals and peak water feed")
