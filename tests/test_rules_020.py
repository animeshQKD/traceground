"""Rules added for 0.2.0, from the false alarms found by hand on the third held-out set
(eval/results/review_heldout3_2026-11-21.md). The examples are written for these tests. Each rule has a
test of what it must still report."""
from traceground import check_answer
from traceground.numbers import shown_workings

GYM = {"name": "Oakline Gym", "rating": 4.4, "monthly_fee_eur": 45.0, "joining_fee_eur": 30.0,
       "classes": [{"name": "Row", "duration_min": 40}]}
FLIGHTS = [{"name": "flight", "args": {"flight_no": "QX-1"}, "result": {"price_eur": 210.0, "metro_km": 0.0}},
           {"name": "flight", "args": {"flight_no": "QX-2"}, "result": {"price_eur": 168.0}}]
FLATS = [{"name": "flat", "args": {"listing_id": "C-31"}, "result": {"rent_eur": 980.0, "metro_km": 0.7,
                                                                    "centre_km": 2.2, "size_m2": 49}},
         {"name": "flat", "args": {"listing_id": "D-08"}, "result": {"rent_eur": 1210.0, "metro_km": 2.5,
                                                                    "centre_km": 0.9, "size_m2": 61}}]


def _high(answer, result=None, trace=None, sources=None):
    if sources is not None:
        return [f for f in check_answer(answer, sources).findings if f.severity == "high"]
    trace = trace if trace is not None else [{"name": "lookup", "args": {}, "result": result}]
    return [f for f in check_answer(answer, trace=trace).findings if f.severity == "high"]


# ---- arithmetic said in words
def test_difference_said_with_less_or_more_expensive():
    assert not _high("QX-2 costs €168 and QX-1 €210, so QX-2 is €42 less.", trace=FLIGHTS)
    assert not _high("QX-1 costs €210, €42 more expensive than QX-2 at €168.", trace=FLIGHTS)


def test_wrong_difference_said_with_less_still_reported():
    assert _high("QX-2 costs €168 and QX-1 €210, so QX-2 is €52 less.", trace=FLIGHTS)


def test_percentage_points():
    src = {"S1": "The margin fell to 6.5% from 7.1%."}
    assert not _high("The margin fell from 7.1% to 6.5%, a decline of 0.6 percentage points.", sources=src)
    assert _high("The margin fell from 7.1% to 6.5%, a decline of 0.8 percentage points.", sources=src)
    assert _high("The margin fell from 7.1% to 6.5%, a decline of 0.6%.", sources=src)


# ---- a working the answer shows
def test_shown_workings_are_read():
    found = [(v, [o.text for o in ops]) for v, ops, _a, _b in
             shown_workings("It is €165 (€45 × 3 months + €30 joining fee); €9.80 ÷ 4 ≈ €2.45; flat C-31.")]
    assert found == [(165.0, ["45", "3", "30"]), (2.45, ["9.80", "4"])]


def test_result_of_a_shown_working():
    assert not _high("Three months cost €165 (€45 × 3 months + €30 joining fee).", GYM)
    assert not _high("Per month that is €45 × 3 + €30 = €165 in all.", GYM)
    assert not _high("Split four ways, €45 ÷ 4 ≈ **€11.25** each.", GYM)


def test_wrong_or_made_up_working_still_reported():
    assert _high("Three months cost €175 (€45 × 3 months + €30 joining fee).", GYM)
    assert _high("If a room is 30 feet long, 30 x 20 = 600 square feet.", GYM)


# ---- value-to-field
def test_calculator_value_worked_out_from_a_field():
    trace = FLATS[:1] + [{"name": "calculator", "args": {"expression": "980/49"}, "result": {"result": 20.0}}]
    assert not _high("The rent is about €20.00 per square metre.", trace=trace)


def test_field_named_after_a_time_unit():
    trace = [{"name": "recipe", "args": {}, "result": {"prep_min": 15, "cook_min": 40}}]
    assert not _high("It takes 55 minutes in all (15 minutes prep + 40 minutes cook).", trace=trace)
    assert _high("It needs 40 minutes prep and 15 minutes cook.", trace=trace)     # swapped, no total to keep


def test_time_unit_then_article_names_nothing():
    trace = [{"name": "loan", "args": {"years": 5}, "result": {"total_paid": 11322.74}}]
    assert not _high("Over 5 years the total paid rises to €11,322.74.", trace=trace)


def test_parts_of_a_duration_are_not_field_values():
    trace = [{"name": "train", "args": {"train_no": "RX-30"}, "result": {"delay_min": 0, "platform": 11}}]
    assert not _high("RX-30 takes about 2 hours 11 minutes.", trace=trace)


def test_same_field_in_two_calls_told_apart_by_the_item_named():
    assert not _high("Flat C-31 is 0.7 km from the metro, and flat D-08 is 2.5 km from the metro.", trace=FLATS)
    assert _high("Flat C-31 is 0.7 km from the metro, and flat D‑08 is 1210 km from the metro.", trace=FLATS)
