"""springs.py: motion ratios, spring rates and stroke land on buyable MTB shocks."""
import springs


def test_springs_and_stroke_are_buyable():
    for axle in ("front", "rear"):
        r = springs.size(axle)
        assert 0.3 < r["mr"] < 1.2
        assert 170 <= r["lbs_in"] <= 700, r["lbs_in"]
        assert r["stroke"] <= 60, r["stroke"]


def test_spring_split_gives_mild_understeer_balance():
    import roll, loads
    ll, _ = roll.lltd()     # front share of lateral load transfer vs front weight share (was: rear ride Hz >= front)
    assert loads.FRONT_SPLIT <= ll <= loads.FRONT_SPLIT + 0.12, ll


def test_motion_ratio_and_travel_meet_targets():
    assert springs.TRAVEL + springs.DROOP >= 50          # V.3.1.1: 50 mm usable wheel travel
    for axle in ("front", "rear"):
        assert 0.7 <= springs.size(axle)["mr"] <= 1.0   # review notes' motion-ratio target
