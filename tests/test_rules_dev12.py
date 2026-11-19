"""Rules added while measuring on the RAGTruth train split (0.1.0.dev12). The examples are written for
these tests; none is RAGTruth text."""
from traceground import check_answer

SHOP = {"name": "7 Seas Grill", "address": "118 Harbor Rd", "business_stars": 3.5,
        "hours": {"Monday": "11:0-21:0", "Friday": "11:0-2:30"},
        "review_info": [{"review_stars": 5, "review_text": "Best ever. Not worth my money? No, worth every cent."},
                        {"review_stars": 4, "review_text": "It retains its original \"dock\" charm."},
                        {"review_stars": 1, "review_text": "BEST FISH N CHIPS YET, said nobody."}]}
TRACE = [{"name": "business_data", "args": {}, "result": SHOP}]


def _shop(answer):
    return check_answer(answer, trace=TRACE)


def _high(r):
    return [f for f in r.findings if f.severity == "high"]


# ---- numbers
def test_number_in_a_name_or_address_is_not_a_field_value():
    assert _shop('Here is an overview of the business "7 Seas Grill", at 118 Harbor Rd.').verdict == "ok"


def test_review_and_passage_labels_are_not_checked():
    assert _shop("Review 3: 1 star, the reviewer did not like it.").verdict == "ok"
    assert not _high(check_answer("Passage 12 says the bridge opened in 1932.", {"S1": "The bridge opened in 1932."}))


def test_open_24_7_is_not_a_number():
    assert _shop("It is open 24/7.").verdict == "ok"


def test_own_length_with_a_hyphen():
    assert check_answer("Here is a 98-word summary: the bridge opened in 1932.",
                        {"S1": "The bridge opened in 1932."}).verdict == "ok"


def test_subject_inside_a_prepositional_phrase():
    # "reviews" ends "according to customer reviews"; the subject is the rating, which is the business's
    assert _shop("The overall rating for this business according to customer reviews is 3.5 out of 5 stars.").verdict == "ok"


def test_rounded_temperature_conversion_is_low_and_a_wrong_one_high():
    src = {"S1": "Preheat the oven to 400F."}
    r = check_answer("Preheat the oven to 400°F (200°C).", src)
    assert r.verdict == "ok" and [f.severity for f in r.findings] == ["low"]
    assert [f.text for f in _high(check_answer("Preheat the oven to 400°F (150°C).", src))] == ["150"]


def test_day_of_a_date_with_an_ordinal_is_checked():
    src = {"S1": "She was last seen on April 6. He came 1st in 2019."}
    assert [f.text for f in _high(check_answer("She was found on April 19th.", src))] == ["19"]
    assert check_answer("She was last seen on April 6th.", src).verdict == "ok"
    assert check_answer("She was last seen on the 6th of April.", src).verdict == "ok"
    assert check_answer("He came 1st in the race.", src).verdict == "ok"


def test_24_hour_time_past_midnight_is_not_pm():
    # "11:0-2:30" closes at 2:30 at night, not 2:30 pm
    assert [f.text for f in _high(_shop("On Friday it is open from 11 am to 2:30 pm."))] == ["2:30 pm"]
    assert _shop("On Friday it is open from 11 am to 2:30 am.").verdict == "ok"


# ---- quotes
def test_quote_small_changes_are_low():
    for answer in ['A reviewer said it was "the best ever."',                 # "Best ever" with an extra "the"
                   'One reviewer called it the "best fish and chips yet".',   # n for and
                   'Another found it "not worth the money".']:                # my -> the
        r = _shop(answer)
        assert r.verdict == "ok" and [f.severity for f in r.findings] == ["low"], answer


def test_quote_marks_escaped_in_a_tool_result():
    # the result holds 'its original \\"dock\\" charm' as JSON; the quote without the marks is the same words
    assert _shop('It "retains its original dock charm".').findings == []


def test_quote_with_a_changed_meaning_stays_high():
    src = {"S1": "He said: we cannot win this war."}
    assert _high(check_answer('He said "we can win this war".', src))
    assert check_answer('He said "we cannot win the war".', src).verdict == "ok"


def test_quote_plural_or_spelling_is_low():
    src = {"S1": "These are the best gins I've had, and evrrything was made there."}
    for answer in ['"the best gin I\'ve had"', '"everything was made there"']:
        r = check_answer(answer, src)
        assert r.verdict == "ok" and [f.severity for f in r.findings] == ["low"], answer


def test_example_text_in_quotes_is_not_a_quotation():
    src = {"S1": "Ask for leave in writing, with the dates."}
    assert check_answer('Use a subject line such as "Request for five days of leave".', src).verdict == "ok"
    assert check_answer('So, the answer to the question "How do I ask for leave at work?" is: in writing.',
                        src, question="asking for leave").verdict == "ok"


# ---- self-contradiction
def test_one_passage_saying_nothing_is_not_a_contradiction():
    src = {"S1": "Nausea and vomiting have been reported as side effects of the drug."}
    a = ("Passage 3 does not mention nausea or vomiting as side effects of the drug. "
         "Nausea and vomiting have been reported as side effects of the drug.")
    assert check_answer(a, src).verdict == "ok"


def test_the_sources_saying_nothing_then_giving_it_is_a_contradiction():
    src = {"S1": "Nausea and vomiting have been reported as side effects of the drug."}
    a = ("The passages do not mention nausea or vomiting as side effects of the drug. "
         "Nausea and vomiting have been reported as side effects of the drug.")
    assert [f.check for f in check_answer(a, src).findings] == ["self-contradiction"]
