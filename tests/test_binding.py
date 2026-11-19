"""Value-to-field and argument binding. Each rule: the real errors it must catch, and correct answers
(written the way models write them) it must pass."""
import pytest

from traceground import check_answer
from traceground.binding import key_words, stem


def findings(answer, trace, question="", check=None, **kw):
    fs = check_answer(answer, question=question, trace=trace, **kw).findings
    return [f for f in fs if check is None or f.check == check]


def call(name, args, result):
    return {"name": name, "args": args, "result": result}


# ---------------------------------------------------------------- field names
@pytest.mark.parametrize("key, words", [
    ("rain_chance_pct", ("rain", "chance")), ("werner_weight", ("werner", "weight")), ("high_c", ("high",)),
    ("monthlyPayment", ("month", "payment")), ("amount_eur", ("amount",)), ("rebounds", ("rebound",)),
    ("value", ()), ("id", ()), ("result_count", ()), ("x2", ()),
])
def test_key_words(key, words):
    assert key_words(key) == words


def test_stem():
    assert [stem(w) for w in ["rebounds", "monthly", "Minutes", "batteries", "loss", "gas"]] == [
        "rebound", "month", "minute", "battery", "loss", "gas"]


# ---------------------------------------------------------------- value-to-field: real errors
PHYSICS = [call("apply_global_noise", {"state": "phi+", "channel": "global_depolarizing", "param": 0.3},
                {"state": "rho_1", "werner_weight": 0.7}),
           call("compute_measures", {"state": "rho_1"}, {"concurrence": 0.55, "negativity": 0.275, "purity": 0.6175})]


def test_real_error_concurrence_given_the_werner_weight():
    (f,) = findings("Global depolarizing noise with p = 0.3 turns phi+ into a Werner state with p_W = 0.7, "
                    "so concurrence = 0.7.", PHYSICS, check="value-to-field")
    assert f.text == "concurrence = 0.7"
    assert f.message == ('"concurrence = 0.7": the tool results give concurrence = 0.55 (compute_measures). '
                         '0.7 is the werner_weight (apply_global_noise).')


def test_swapped_fields_and_one_finding_per_value():
    stats = [call("player_game_stats", {"player": "Jordan Reyes"}, {"points": 27, "rebounds": 11, "assists": 7})]
    fs = findings("Jordan Reyes scored 27 points with 7 rebounds and 11 assists.", stats)
    assert [(f.check, f.text) for f in fs] == [("value-to-field", "7 rebounds"), ("value-to-field", "11 assists")]


def test_field_name_after_the_number_in_any_order():
    fc = [call("get_forecast", {"city": "Oslo"}, {"high_c": 9, "low_c": 4, "rain_chance_pct": 70, "wind_kmh": 18})]
    (f,) = findings("A high of 9 °C, wind of 18 km/h and a 4% chance of rain.", fc)
    assert f.text == "4% chance of rain" and "4% is the low_c (get_forecast)" in f.message


def test_field_synonyms():
    fc = [call("get_forecast", {}, {"precip_pct": 70})]
    assert findings("Precipitation is 40%.", fc, check="value-to-field") == []           # no field named so
    (f,) = findings("Precipitation is 40%.", fc, field_synonyms={"precip_pct": ["precipitation"]},
                    check="value-to-field")
    assert "precip_pct = 70" in f.message


# ---------------------------------------------------------------- value-to-field: correct answers pass
CORRECT = [
    ("Paris is 14 °C with 82% humidity, while Rome is warmer at 21 °C and drier at 55% humidity.",
     [call("get_weather", {"city": "Paris"}, {"temp_c": 14, "humidity": 82}),
      call("get_weather", {"city": "Rome"}, {"temp_c": 21, "humidity": 55})], "Compare Paris and Rome."),
    ("Apple trades at $189.50, down 1.2% on volume of 51.2 million shares; the change is -1.2%.",
     [call("get_quote", {"symbol": "AAPL"}, {"price": 189.5, "change_pct": -1.2, "volume": 51200000})], "How is Apple doing?"),
    ("Over 30 years at 6.5%, the monthly payment is 1,580.17 and total interest comes to 318,861.20.",
     [call("mortgage", {"principal": 250000, "years": 30, "rate": 0.065},
           {"monthly_payment": 1580.17, "total_interest": 318861.2})],
     "What is the monthly payment for a 250,000 mortgage over 30 years at 6.5%?"),
    ("Japan had about 124 million people in 2024.",
     [call("search", {"query": "population of Japan 2024"}, "Japan's population was 123.9 million in 2024.")],
     "What was Japan's population in 2024?"),
    ("5 miles is about 8.05 km.", [call("convert", {"value": 5, "from_unit": "mi", "to_unit": "km"}, {"result": 8.04672})],
     "Convert 5 miles to km."),
    ("15% of 240 is 36.", [call("calculator", {"expression": "0.15*240"}, "36.0")], "What's 15% of 240?"),
    ("At 7%, 3 years cost 12,250.43 in total and 5 years cost 13,500.10 in total.",
     [call("loan_cost", {"rate": 0.07, "years": 3}, {"total": 12250.43}),
      call("loan_cost", {"rate": 0.07, "years": 5}, {"total": 13500.10})], "Compare 3-year and 5-year costs at 7%."),
    ("He shot 48.5% from the field and scored 31 points.",
     [call("player_stats", {"player": "X"}, {"fg_pct": 0.485, "points": 31})], "How did X play?"),
    ("The high and low are 9 and 4 °C respectively.",
     [call("get_forecast", {"city": "Oslo"}, {"high_c": 9, "low_c": 4})], "Oslo tomorrow?"),
    ("Tomorrow: a low of 4 °C and a high of 9 °C, with a 70% chance of rain.",
     [call("get_forecast", {"city": "Oslo"}, {"high_c": 9, "low_c": 4, "rain_chance_pct": 70})], "Oslo tomorrow?"),
    ("Over 3 years at 7% you pay 340.29 a month and 12,250.43 in total.",
     [call("loan_cost", {"rate": 0.07, "years": 3}, {"total": 12250.43, "monthly": 340.29})],
     "What do I pay per month and in total for the 3-year loan at 7%?"),
    ("Global depolarizing noise with p = 0.3 leaves a concurrence of 0.55; local depolarizing noise with p = 0.1 "
     "on both photons leaves 0.715.",
     [call("apply_global_noise", {"state": "phi+", "param": 0.3}, {"state": "rho_1", "werner_weight": 0.7}),
      call("apply_local_noise", {"state": "phi+", "param": 0.1, "qubits": "both"}, {"state": "rho_2", "werner_weight": 0.81}),
      call("compute_measures", {"state": "rho_1"}, {"concurrence": 0.55}),
      call("compute_measures", {"state": "rho_2"}, {"concurrence": 0.715})],
     "Apply global and local depolarizing noise with p = 0.3 and 0.1 respectively to phi+, and compare the concurrences."),
    ("The forecast for the next 3 days in Paris: 12, 14 and 11 °C.",
     [call("forecast", {"city": "Paris", "days": 3}, {"highs_c": [12, 14, 11]})], "Weather for the next 3 days in Paris?"),
    ("Book 2 rooms on 20 June: done, booking AB123.",
     [call("book", {"rooms": 2, "date": "2026-06-20"}, {"booking": "AB123"})], "Book 2 rooms for 20 June."),
]


@pytest.mark.parametrize("answer, trace, question", CORRECT, ids=[f"correct{i}" for i in range(len(CORRECT))])
def test_correct_trace_answers_raise_nothing(answer, trace, question):
    r = check_answer(answer, question=question, trace=trace)
    assert r.findings == [] and r.verdict == "ok", [f.message for f in r.findings]


# ---------------------------------------------------------------- argument binding: real errors
def test_real_error_kreout_case_asked_0_3_called_with_0_03():
    trace = [call("apply_global_noise", {"state": "phi+", "param": 0.03}, {"state": "rho_1", "werner_weight": 0.97}),
             call("compute_measures", {"state": "rho_1"}, {"concurrence": 0.955})]
    (f,) = findings("With global depolarizing noise of p = 0.3, the concurrence of phi+ falls to 0.955.", trace,
                    "Apply global depolarizing noise with p = 0.3 to phi+. What is its concurrence?")
    assert f.check == "argument" and f.text == "0.3"
    assert f.message == "The question asks for 0.3, but apply_global_noise was called with param=0.03."


def test_asked_5_years_called_with_3():
    (f,) = findings("Over 5 years at 7% you pay 12,250 in total, 340.29 a month.",
                    [call("loan_cost", {"rate": 0.07, "years": 3}, {"total": 12250.43, "monthly": 340.29})],
                    "What is the 5-year cost at 7% interest?")
    assert f.message == "The question asks for 5-year, but loan_cost was called with years=3."


def test_swapped_between_two_calls():
    trace = [call("convert_currency", {"amount": 80, "from": "USD", "to": "EUR"}, {"amount_eur": 73.6}),
             call("convert_currency", {"amount": 120, "from": "GBP", "to": "EUR"}, {"amount_eur": 140.4})]
    (f,) = findings("120 USD is 73.60 EUR and 80 GBP is 140.40 EUR.", trace, "Convert 120 USD and 80 GBP to euros.")
    assert f.check == "argument" and f.text == "120"
    assert f.message.startswith("The question pairs 120 with USD and 80 with GBP, but the calls swap them")


def test_swapped_inside_one_call():
    (f,) = findings("At 3% over 5 years you pay 1,234.",
                    [call("loan_cost", {"rate": 5, "years": 3}, {"total": 1234})], "What is the 5-year cost at 3%?")
    assert f.message == "The question asks for 5-year, but loan_cost was called with years=3."


def test_asked_3_days_called_with_7():
    (f,) = findings("The forecast for the next days in Paris is mild.",
                    [call("forecast", {"city": "Paris", "days": 7}, {"summary": "mild"})],
                    "Weather for the next 3 days in Paris?")
    assert f.message == "The question asks for 3 days, but forecast was called with days=7."


# ---------------------------------------------------------------- argument binding: silent when unsure
@pytest.mark.parametrize("question, trace", [
    ("Show me the top 5 results for quantum.", [call("search", {"query": "quantum", "limit": 10}, "...")]),
    ("Is a 1.5% fee on 2,000 USD more than 25 USD?", [call("calc", {"expression": "2000*0.015"}, "30")]),
    ("Convert 5 years to months.", [call("convert", {"value": 60, "unit": "months"}, {"ok": True})]),
    ("What is the 5-year cost at 7%?", [call("rates", {}, {"rate": 0.07})]),            # no arguments to compare
])
def test_argument_binding_is_silent_when_unsure(question, trace):
    assert findings("Done.", trace, question, check="argument") == []
