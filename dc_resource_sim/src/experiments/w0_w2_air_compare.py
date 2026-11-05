"""Step 24: W0 proxy versus W2-Air evaporation and feasibility."""
from math import isclose
from w2_air_first import direct_evap  # Reuse Step 20; import prints Step 20 checks.

W0 = 0.5  # L/kWh IT; illustrative direct-consumption proxy
IT_KW = 1000.0

cases = [(20.0, 0.50), (30.0, 0.30), (30.0, 0.70)]
for temp, rh in cases:
    result = direct_evap(temp, rh, it_kw=IT_KW)
    w0_lph = W0 * IT_KW
    if result["mode"] == "infeasible":
        assert result["needed_effectiveness"] > 0.8
        assert result["best_supply_c"] > 25.0
        print(f"{temp:g} C/{rh:.0%}: W0={w0_lph:.1f} L/h; "
              "W2=infeasible (evaporation N/A)")
    else:
        evap = result["evaporation_lph"]
        intensity = evap / IT_KW
        print(f"{temp:g} C/{rh:.0%}: W0={w0_lph:.1f} L/h; "
              f"W2={result['mode']}, evap={evap:.2f} L/h; "
              f"effective intensity={intensity:.5f} L/kWh IT")
        if result["mode"] == "dry":
            assert isclose(evap, 0.0, abs_tol=1e-8)
        else:
            assert isclose(evap, 489.36647, abs_tol=0.01)

# New comparison: proportionality at ONE fixed weather/operating state.
ref = direct_evap(30.0, 0.30, it_kw=1000.0)
for it_kw in (800.0, 1000.0, 1200.0):
    z = direct_evap(30.0, 0.30, it_kw=it_kw)
    assert z["mode"] == "wet"
    assert isclose(z["evaporation_lph"] / it_kw,
                   ref["evaporation_lph"] / 1000.0, rel_tol=1e-10)
    print(f"IT={it_kw:.0f} kW: W0={W0*it_kw:.1f} L/h; "
          f"W2 evaporation={z['evaporation_lph']:.2f} L/h")

print("PASS: W0 is constant-intensity; W2 depends on air state and feasibility;")
print("at fixed weather and controls W2 evaporation scales with IT load.")
print("W0 is a consumption proxy; W2 is process evaporation, not site intake.")
