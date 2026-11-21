"""Rules added for 0.1.2, from the false alarms and misses found by hand on the second held-out set
(eval/results/review_heldout2_2026-11-20.md). The examples are written for these tests. Each rule has a
test of what it must still report."""
from traceground import check_answer
from traceground.binding import key_unit

KETTLE = {"name": "Copper Kettle", "rating": 4.1, "review_count": 3, "price_level": 2,
          "reviews": [{"stars": 5, "text": "Great scones."}, {"stars": 3, "text": "Slow."},
                      {"stars": 4, "text": "Nice tea."}]}
INN = {"name": "Linden Inn", "rate_eur": 125.0, "breakfast_eur": 18.0, "guest_rating": 4.4, "rooms_free": 6,
       "station_km": 1.2, "airport_km": 20.5}
TRAINS = [{"name": "get_train", "args": {"train_no": "A1"},
           "result": {"departs": "6:0", "arrives": "7:40", "delay_min": 9, "platform": 3, "stops": 5}},
          {"name": "get_train", "args": {"train_no": "B2"},
           "result": {"departs": "8:0", "arrives": "10:5", "delay_min": 0, "platform": 7, "stops": 2}}]


def _high(answer, result=None, trace=None, question=""):
    trace = trace if trace is not None else [{"name": "lookup", "args": {}, "result": result}]
    return [f for f in check_answer(answer, trace=trace, question=question).findings if f.severity == "high"]


# ---- a rating said in stars
def test_rating_named_before_stars():
    assert not _high("Copper Kettle has an overall rating of 4.1 stars.", KETTLE)


def test_rating_named_before_stars_still_reported():
    assert _high("Copper Kettle has an overall rating of 4.8 stars.", KETTLE)
    assert _high("Copper Kettle has an overall rating of 3 stars.", KETTLE)        # 3 is one review's stars


def test_stars_of_the_whole_when_reviews_are_not_mentioned():
    assert not _high("It is a good pick (4.1 stars) for tea.", KETTLE)


def test_stars_said_of_a_review_still_reported():
    assert _high("One review gave it 4.1 stars.", KETTLE)


# ---- a difference of two durations the answer states
def test_difference_of_stated_durations():
    answer = ("A1 takes 1 hour 40 minutes and B2 takes 2 hours 5 minutes, so A1 is faster by 25 minutes.")
    assert not _high(answer, trace=TRAINS)


def test_wrong_difference_of_durations_still_reported():
    answer = ("A1 takes 1 hour 40 minutes and B2 takes 2 hours 5 minutes, so A1 is faster by 35 minutes.")
    assert _high(answer, trace=TRAINS)


# ---- a product the answer shows next to its result
def test_product_shown_next_to_its_result():
    assert not _high("Two nights cost €250 for the room (2 × €125).", INN, question="Price for two nights?")
    assert not _high("The room comes to 2 × €125 = €250.", INN)


def test_product_shown_wrong_or_made_up_still_reported():
    assert _high("The room comes to 2 × €125 = €260.", INN)
    assert _high("The room comes to €250.", INN)
    assert _high("If a wall is 30 feet long, 30 x 20 = 600 square feet.", INN)


# ---- a comparison after "is"
def test_field_value_compared_after_is_is_checked():
    assert _high("Linden Inn's guest rating of 125 is higher than the cafe's.", INN)


# ---- two fields in one unit, told apart by the word near the number
def test_km_fields_told_apart_by_the_place():
    assert not _high("It is 1.2 km from the train station and 20.5 km from the airport.", INN)
    assert _high("It is 20.5 km from the train station and 1.2 km from the airport.", INN)


def test_money_fields_told_apart_by_a_price_word():
    assert not _high("A night costs €125, and breakfast is not included.", INN)
    assert _high("A night costs €18, and breakfast is not included.", INN)


# ---- minutes in a key
def test_minutes_key_unit():
    assert key_unit("delay_min") == ("time", "minute") and key_unit("duration_mins") == ("time", "minute")
    assert key_unit("days_min") is None and key_unit("days_max") is None


def test_minutes_late_compared_with_the_delay():
    assert not _high("A1 is running 9 minutes late.", trace=TRAINS[:1])
    assert _high("A1 is running 3 minutes late.", trace=TRAINS[:1])
