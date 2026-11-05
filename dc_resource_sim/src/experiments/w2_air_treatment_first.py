"""Step 25: idealized treatment feed and reject for W2-Air evaporation.

Recovery is assumed, not measured. Feed is not facility withdrawal or
consumption; infeasible cooling remains infeasible.
"""
from math import isclose
from w2_air_first import direct_evap


def treatment_balance(evap_lph, recovery):
    if evap_lph < 0 or not (0 < recovery <= 1):
        raise ValueError("Require evaporation >= 0 and 0 < recovery <= 1")
    feed_lph = evap_lph / recovery
    reject_lph = feed_lph - evap_lph
    assert isclose(feed_lph, evap_lph + reject_lph, abs_tol=1e-9)
    assert reject_lph >= -1e-9
    return feed_lph, reject_lph


wet = direct_evap(30.0, 0.30, it_kw=1000.0)
assert wet["mode"] == "wet"
evap = wet["evaporation_lph"]
assert isclose(evap, 489.36647, abs_tol=0.01)

for eta, expected_feed, expected_reject in (
    (1.0, 489.36647, 0.0),
    (0.8, 611.70809, 122.34162),
):
    feed, reject = treatment_balance(evap, eta)
    assert isclose(feed, expected_feed, abs_tol=0.02)
    assert isclose(reject, expected_reject, abs_tol=0.02)
    print(f"eta={eta:.1f}: evaporation={evap:.2f}, "
          f"feed={feed:.2f}, reject={reject:.2f} L/h")

# Cooling conditions still govern whether the process runs.
dry = direct_evap(20.0, 0.50, it_kw=1000.0)
assert dry["mode"] == "dry"
assert treatment_balance(dry["evaporation_lph"], 0.8) == (0.0, 0.0)

humid = direct_evap(30.0, 0.70, it_kw=1000.0)
assert humid["mode"] == "infeasible"
assert "evaporation_lph" not in humid  # No valid cooling-service water estimate.
print("Dry: evaporation=feed=reject=0 L/h (idealized process)")
print("Humid: cooling infeasible; no valid treatment-flow estimate")
print("PASS: feed = evaporation + reject; lower recovery raises feed only")
