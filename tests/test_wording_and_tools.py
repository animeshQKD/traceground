"""Failed calls, tools never called, self-talk and self-contradiction: the real errors each check must
catch, and correct answers (written the way models write them) it must pass."""
import pytest

from traceground import check_answer


def checks(answer, sources=None, question="", trace=None):
    return [(f.check, f.text) for f in check_answer(answer, sources, question, trace).findings]


def call(name, args, result, error=None):
    d = {"name": name, "args": args, "result": result}
    if error is not None:
        d["error"] = error
    return d


FAILED_FORECAST = call("get_forecast", {"city": "Oslo", "day": "tomorrow"}, "Error: upstream service timed out")
FORECAST = call("get_forecast", {"city": "Oslo", "day": "tomorrow"}, {"high_c": 9, "rain_chance_pct": 70})


# ---------------------------------------------------------------- failed calls
def test_real_error_a_failed_call_reported_as_a_result():
    r = check_answer("Tomorrow in Oslo: about 9 °C with a 70% chance of rain.", trace=[FAILED_FORECAST],
                     question="What will the weather be like in Oslo tomorrow?")
    f = next(f for f in r.findings if f.check == "failed-call")
    assert f.message == ('get_forecast(city="Oslo", day="tomorrow") failed ("Error: upstream service timed out") and '
                         'was not called again successfully, but the answer reads as if it had worked.')


@pytest.mark.parametrize("answer, trace", [
    ("Tomorrow in Oslo: a high of 9 °C.", [FAILED_FORECAST, FORECAST]),                        # called again, worked
    ("I could not get the forecast for Oslo: the weather service timed out.", [FAILED_FORECAST]),  # says it failed
    ("Sorry, the forecast service is unavailable right now; please try again later.", [FAILED_FORECAST]),
    ("Oslo: 9 °C tomorrow.", [call("search_web", {"query": "Oslo weather tomorrow"}, "Error: 429"),  # a fallback tool
                              call("weather_api", {"city": "Oslo"}, {"temp_c": 9})]),
    ("Hotels in Bengaluru start at 3,200 a night.", [call("search_flights", {"origin": "DEL"}, {"error": "bad date"}),
                                                     call("get_hotels", {"city": "Bengaluru"}, {"min_price": 3200})]),
])
def test_failed_calls_that_are_fine(answer, trace):
    assert [c for c, _t in checks(answer, trace=trace)] == []


# ---------------------------------------------------------------- tools never called
def test_real_error_a_web_search_that_never_happened():
    r = check_answer("I searched the web and found that the MX-200 warranty is 2 years, so after 3 years it has expired.",
                     trace=[call("lookup_product", {"sku": "MX-200"}, {"warranty_years": 2})])
    (f,) = r.findings
    assert f.check == "tool-not-called" and f.text == "I searched the web"
    assert f.message == ('The answer says "I searched the web", but no tool for a web search was called '
                         '(calls: lookup_product).')


@pytest.mark.parametrize("answer, names", [
    ("I googled it: the answer is yes.", ["calculator"]),
    ("According to my web search, it opened in 2019.", []),
    ("I ran the code and it prints 42.", ["search_web"]),
    ("I queried the database: 12 orders are open.", ["web_search"]),
    ("I used the currency_converter tool to get the rate.", ["calculator"]),
])
def test_claims_about_tools_that_were_not_called(answer, names):
    trace = [call(n, {}, {"ok": True}) for n in names]
    assert [c for c, _t in checks(answer, trace=trace) if c == "tool-not-called"] == ["tool-not-called"]


@pytest.mark.parametrize("answer, names", [
    ("I searched the web and found it opened in 2019.", ["web_search"]),
    ("I can search the web for more details if you like.", []),          # an offer, not a claim
    ("You can look it up online.", []),                                  # advice, not a claim
    ("I searched the documents you provided.", []),                      # not the web
    ("I ran the numbers: it is cheaper.", []),                           # not code
    ("I used the loan calculator tool.", ["loan_calculator"]),
    ("I used the search tool to find it.", ["tavily_search"]),
])
def test_claims_that_are_fine(answer, names):
    trace = [call(n, {}, {"ok": True}) for n in names]
    assert [c for c, _t in checks(answer, trace=trace) if c == "tool-not-called"] == []


def test_no_trace_means_no_claim_check():
    assert checks("I searched the web and it is fine.") == []


# ---------------------------------------------------------------- self-talk
def test_real_error_thinking_aloud_left_in():
    r = check_answer("Let me report the tool's numbers: the total is 12,250.43. Wait, let me check: the monthly "
                     "payment is 340.29.", trace=[call("loan_cost", {"rate": 0.07, "years": 3},
                                                      {"total": 12250.43, "monthly": 340.29})])
    assert [(f.check, f.text) for f in r.findings] == [("self-talk", "Let me report the tool's numbers:"),
                                                        ("self-talk", "Wait, let me check:")]
    assert r.findings[1].suggestion == ""                # deleting "Wait, let me check:" is a certain fix
    assert r.findings[1].message == 'This is the model thinking aloud, left in the final answer: "Wait, let me check:".'


@pytest.mark.parametrize("answer, text", [
    ("Wait — that's not right, the concurrence is 0.55.", "Wait —"),
    ("Hmm... actually it is 0.55.", "Hmm..."),
    ("These are the actual computed values.", "These are the actual computed values."),
    ("CHSH max = 2.263 > 2√2? No — it is below the bound.", "CHSH max = 2.263 > 2√2? No —"),
    ("The total is 12,000.\n\nLet me reconsider. The total is 12,250.43.", "Let me reconsider. The total is 12,250.43."),
])
def test_more_self_talk(answer, text):
    assert ("self-talk", text) in checks(answer)


@pytest.mark.parametrize("answer", [
    "Let me explain how the loan works: you pay 340.29 a month.",
    "Let me summarize: the total is 12,250.43.",
    "Let me know if you need anything else!",
    "Wait times at the counter are about 5 minutes.",
    "Hmm, interesting question! The short answer is yes.",
    'The manual says "wait, let me check: the light must be green" before you start.',
    "You can verify this by checking the manual.",
])
def test_ordinary_wording_is_not_self_talk(answer):
    assert [c for c, _t in checks(answer)] == []


def test_self_talk_is_a_problem_even_without_evidence():
    r = check_answer("Wait, let me check: it is 42.6.")
    assert r.verdict == "problems"
    assert r.summary == "1 passage of the model thinking aloud. 1 number not checked: no sources or question given."


# ---------------------------------------------------------------- self-contradiction
WARRANTY = ["The warranty period is two years from the date of purchase."]


@pytest.mark.parametrize("answer", [
    "The passages do not say how long the warranty lasts. The warranty lasts two years from the date of purchase [S1].",
    "The passages do not say how long the warranty lasts. The warranty lasts two years from the date of purchase.",
    "The sources don't mention how long the warranty lasts. The warranty lasts two years from the date of purchase.",
])
def test_real_error_says_the_sources_do_not_say_then_says_it(answer):
    r = check_answer(answer, WARRANTY)
    (f,) = r.findings
    assert f.check == "self-contradiction" and f.text.endswith("how long the warranty lasts.")
    assert f.message.startswith("The answer says the sources do not give this, then gives it from them:")


@pytest.mark.parametrize("answer", [
    "The documents do not say when the warranty starts. They say it lasts two years from the date of purchase.",
    "The sources don't mention the price. The warranty lasts two years from the date of purchase [S1].",
    "The passages do not give the warranty for refurbished units. The warranty is two years from the date of purchase.",
    "The passages do not say how long the warranty lasts.",
])
def test_partial_or_different_topics_are_fine(answer):
    assert [c for c, _t in checks(answer, WARRANTY) if c == "self-contradiction"] == []
