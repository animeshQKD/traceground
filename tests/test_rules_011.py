"""Rules added for 0.1.1, from the false alarms found by hand on the RAGTruth test split and like cases on the
train split. The examples are written for these tests; none is RAGTruth text. Each rule has a test of what
it must still report."""
from traceground import check_answer
from traceground.numbers import find_numbers, number_kind

CAFE = {"name": "Blue Door Cafe", "business_stars": 3.5,
        "hours": {"Monday": "7:0-15:0", "Friday": "13:0-23:0"},
        "review_info": [{"review_stars": 5, "review_text": "A great breakfast, an experience in its self."},
                        {"review_stars": 2, "review_text": "Slow service."},
                        {"review_stars": 1, "review_text": "Cold coffee."}]}
TRACE = [{"name": "business_data", "args": {}, "result": CAFE}]


def _cafe(answer):
    return check_answer(answer, trace=TRACE)


def _high(r):
    return [f for f in r.findings if f.severity == "high"]


# ---- times written with one-digit minutes, as the data writes them
def test_time_with_one_digit_minutes():
    assert not _high(_cafe("On Friday it is open from 1:0 PM to 11:0 PM."))


def test_time_with_one_digit_minutes_still_checked():
    assert _high(_cafe("On Friday it is open from 1:0 PM to 11:30 PM."))


# ---- a number glued to a unit, written with a thousands separator or decimals
def test_glued_unit_is_not_cut_short():
    assert [n.text for n in find_numbers("He walked 29,200km, then 3.5km more.")] == []
    assert [n.text for n in find_numbers("It costs 1,200 dollars, version 3.5.")] == ["1,200", "3.5"]


def test_glued_unit_in_the_source_is_read_whole():
    src = {"S1": "Use the five-inch (12.7cm) blade."}
    assert not _high(check_answer("Use the five-inch (12.7 cm) blade.", src))
    assert _high(check_answer("Use the five-inch (13.7 cm) blade.", src))


# ---- the answer counting its own words, further from "summary"
def test_own_length_far_from_summary():
    src = {"S1": "The bridge opened in 1932."}
    assert not _high(check_answer("Here is a summary of the news article about the old bridge within 83 words: "
                                  "it opened in 1932.", src))
    assert _high(check_answer("Here is a summary of the news article: the bridge took 83 years to build.", src))


# ---- quotes
def test_censored_word_written_another_way():
    src = {"S1": 'One critic called the show "boring as s---" and left.'}
    assert not _high(check_answer('A critic called it "boring as s\\*\\*" and left.', src))
    assert not _high(check_answer('A critic called it "boring as s**" and left.', src))


def test_quote_one_letter_off_is_minor():
    r = _cafe('One reviewer called breakfast "an experience in itself."')
    assert not _high(r)
    assert [f.severity for f in r.findings if f.check == "quote"] == ["low"]


def test_quote_one_letter_off_in_a_short_word_or_a_digit_is_still_reported():
    src = {"S1": "He said it was now good at all here, and we sold 1990 units."}
    assert _high(check_answer('He said it was "not good at all here".', src))
    assert _high(check_answer('He said "we sold 1991 units".', src))


# ---- self-contradiction
def test_denial_on_another_topic_sharing_only_source_words():
    src = {"S1": "The benefits of drinking clove tea include soothing the senses and aiding digestion."}
    answer = ("The side effects of drinking clove tea are not mentioned in the given passages. Based on the "
              "given passages, the benefits of drinking clove tea include soothing the senses and aiding digestion.")
    assert not [f for f in check_answer(answer, src).findings if f.check == "self-contradiction"]


def test_denial_then_the_same_topic_still_reported():
    src = {"S1": "The warranty lasts two years from the date of purchase."}
    answer = "The passages do not say how long the warranty lasts. The warranty lasts two years from the date of purchase."
    assert [f for f in check_answer(answer, src).findings if f.check == "self-contradiction"]


# ---- value-to-field
def test_count_of_a_list_before_the_number():
    assert not _high(_cafe("* Number of reviews: 3"))


def test_count_of_a_list_wrong_still_reported_as_a_number():
    assert _high(_cafe("* Number of reviews: 37"))


def test_one_reviews_stars_said_of_the_business():
    assert not _high(_cafe("One customer gave the business a 5-star rating."))
    assert not _high(_cafe("The cafe has a mixed review of 3.5 stars."))


def test_stars_that_no_field_has_still_reported():
    assert _high(_cafe("One customer gave the business a 4.5-star rating."))


# ---- the closest values offered
def test_number_kind():
    text = "Founded in 1873; opened May 18, 2015-12-13 17:03:39, 1,472 seats."
    at = {"1873": text.index("1873"), "18": text.index("May 18") + 4, "03": text.index(":03") + 1, "1,472": text.index("1,472")}
    kinds = {m: number_kind(text, i, i + len(m)) for m, i in at.items()}
    assert kinds == {"1873": "year", "18": "day", "03": "stamp", "1,472": "other"}


def test_closest_values_are_of_the_same_kind():
    src = {"S1": "Tickets cost $1,500. The theatre opened in 1873 and survived the 1925 earthquake."}
    year = _high(check_answer("The match took place in 2015.", src))[0]
    assert "1,500" not in year.message and "1925" in year.message
    seats = _high(check_answer("The theatre has 1,472 seats.", src))[0]
    assert "1873" not in seats.message and "1925" not in seats.message and "1,500" in seats.message


def test_parts_of_a_time_stamp_are_never_offered():
    data = [{"name": "reviews", "args": {}, "result": {"review_date": "2015-12-13 17:03:39", "stars": 3.0}}]
    f = _high(check_answer("Reviews average 2.5 stars.", trace=data))[0]
    assert "03" not in f.message.replace("3.0", "")
