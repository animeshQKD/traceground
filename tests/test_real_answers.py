"""Answers written by real models (Groq openai/gpt-oss-120b and openai/gpt-oss-20b, 2026-11-17,
eval/run_eval.py) against the deterministic tools in eval/tools.py. Each was checked by hand; the ids
ending in -20b are gpt-oss-20b's. f09, w05, c04 (120b) were false alarms before 0.1.0.dev5; f01-20b,
f07-20b, c02-20b and p05-20b before 0.1.0.dev6. The tests also check that the same answers with a
wrong number are still caught."""
import json
from pathlib import Path

import pytest

from traceground import check_answer, check_messages

DATA = {r["id"]: r for r in json.loads((Path(__file__).parent / "data" / "real_answers_2026-11-17.json")
                                       .read_text(encoding="utf-8"))}


def _with_answer(qid, old, new):
    msgs = json.loads(json.dumps(DATA[qid]["messages"]))
    assert old in msgs[-1]["content"]
    msgs[-1]["content"] = msgs[-1]["content"].replace(old, new)
    return msgs


@pytest.mark.parametrize("qid", ["f09", "w05", "c04", "u02", "s01", "p05",
                                 "f01-20b", "f03-20b", "f07-20b", "c02-20b", "k03-20b"])
def test_correct_real_answers_have_no_findings(qid):
    r = check_messages(DATA[qid]["messages"])
    assert r.verdict == "ok", [f.message for f in r.findings]


# f01-20b, f07-20b: "The monthly payment on a $20,000 loan ... is $469.70": "on" starts a new phrase
def test_f01_20b_wrong_payment_still_caught():
    r = check_messages(_with_answer("f01-20b", "$469.70", "$496.70"))
    assert r.verdict == "problems" and any("496.70" in f.text for f in r.findings)


# c02-20b: "40\u202f983.61": a narrow no-break space as thousands separator
def test_c02_20b_wrong_amount_still_caught():
    r = check_messages(_with_answer("c02-20b", "40\u202f983.61", "40\u202f893.61"))
    assert r.verdict == "problems" and r.findings[0].text.strip() == "40\u202f893.61"


# p05-20b: "$119.70" with no calculator call: 39.9 x 3 is right, but no tool worked it out: a minor finding
def test_p05_20b_arithmetic_in_the_answer_is_minor():
    r = check_messages(DATA["p05-20b"]["messages"])
    assert r.verdict == "ok" and [(f.check, f.severity) for f in r.findings] == [("number", "low")]
    assert "39.9 (get_product) \u00d7 3 (the question)" in r.findings[0].message
    assert r.stats["numbers_computed_in_answer"] == 1
    r = check_messages(_with_answer("p05-20b", "$119.70", "$129.70"))
    assert r.verdict == "problems"


def test_k03_semantic_error_is_out_of_scope():
    # "volume ... so ACME moved more": every number is in the tool results; the reasoning is wrong,
    # which a grounding check does not judge
    assert check_messages(DATA["k03"]["messages"]).verdict == "ok"


# f09: "The monthly payment for a $30,000 loan ... is about $892.41": "for" starts a new phrase,
# so "monthly payment" is not attached to 30,000
def test_f09_wrong_payment_still_caught():
    r = check_messages(_with_answer("f09", "$892.41", "$829.41"))
    assert r.verdict == "problems" and any("829.41" in f.text for f in r.findings)


def test_f09_wrong_principal_still_caught():
    r = check_messages(_with_answer("f09", "$30,000 loan", "$35,000 loan"))
    assert r.verdict == "problems"


# w05: "the high temperature will be about 91.4 °F" is the calculator's result, in another unit than high_c
def test_w05_wrong_conversion_still_caught():
    r = check_messages(_with_answer("w05", "91.4", "93.2"))
    assert r.verdict == "problems"


def test_w05_celsius_value_on_wrong_field_still_caught():
    r = check_messages(_with_answer("w05", "about\u202f91.4\u202f°F", "about 26 °C"))   # 26 is the low
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"


# c04: "a total of roughly 549 EUR" = 315 + 234
def test_c04_wrong_total_still_caught():
    r = check_messages(_with_answer("c04", "roughly\u202f549", "roughly\u202f559"))
    assert r.verdict == "problems" and "559" in r.findings[0].text


# ------------------------------------------------------------ the three rules on their own
def test_preposition_ends_the_field_search():
    trace = [{"name": "loan_cost", "args": {"principal": 30000},
              "result": {"monthly_payment": 892.41, "total_paid": 32126.68}}]
    assert check_answer("The monthly payment for a $30,000 loan is $892.41.", trace=trace).verdict == "ok"
    assert check_answer("The monthly payment on a $30,000 loan is $892.41.", trace=trace).verdict == "ok"
    r = check_answer("The monthly payment is $30,000.", trace=trace)
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"


def test_unit_of_the_same_kind_keeps_the_binding():
    trace = [{"name": "get_weather", "args": {"city": "Paris"}, "result": {"high_c": 14, "low_c": 8}}]
    assert check_answer("In Paris the high is 14 °C.", trace=trace).verdict == "ok"
    r = check_answer("In Paris the high is 8 °C.", trace=trace)
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"
    # "the high in Paris is 8": the subject of "is" names the field (since 0.1.0.dev8)
    r = check_answer("The high in Paris is 8 °C.", trace=trace)
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"


def test_unit_conflict_skips_the_binding():
    trace = [{"name": "get_weather", "args": {"city": "Mumbai"}, "result": {"high_c": 33, "low_c": 26}},
             {"name": "calculator", "args": {"expression": "33*9/5+32"}, "result": {"result": 91.4}}]
    assert check_answer("The high will be 91.4 °F.", trace=trace).verdict == "ok"
    assert check_answer("The high will be 91.4 F.", trace=trace).verdict == "ok"
    r = check_answer("The high will be 26 °C.", trace=trace)
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"


def test_derived_numbers():
    src = {"S1": "300 CHF is 315 EUR. 200 GBP is 234 EUR."}
    r = check_answer("That is 315 EUR and 234 EUR, 549 EUR in total.", src)
    assert r.verdict == "ok" and r.stats["numbers_derived"] == 1
    assert check_answer("That is 315 EUR and 234 EUR, 81 EUR apart.", src).verdict == "ok"       # difference
    assert check_answer("That is 315 EUR and 234 EUR, 550 EUR in total.", src).verdict == "problems"
    # an unsupported number in the answer cannot support another one
    assert check_answer("That is 315 EUR and 244 EUR, 559 EUR in total.", src).verdict == "problems"
    # a stated number times a question number: "3 lamps" x 39.9
    r = check_answer("Three lamps at $39.90 each cost $119.70.", {"S1": "LT-50 price_usd: 39.9"},
                     question="How much would 3 LT-50 lamps cost?")
    assert r.verdict == "ok"


def test_si_thousands_separators():
    src = {"S1": "The total is 40983.61 yen."}
    for sep in ("\u202f", "\u2009", "\u00a0"):
        assert check_answer(f"It is 40{sep}983.61 yen.", src).verdict == "ok"
    assert check_answer("It is 40,983.61 yen.", src).verdict == "ok"
    # a plain space still separates two numbers
    assert check_answer("It is 40 983.61 yen.", src).verdict == "problems"


# ------------------------------------------------------------ found with planted errors (eval/mutate.py)
def test_arithmetic_needs_a_word_that_says_so():
    trace = [{"name": "get_player_stats", "args": {"date": "2026-11-16"},
              "result": {"points": 27, "rebounds": 11, "minutes": 34}}]
    # 61 = 27 + 34 by chance: no "total", so it is not taken as a sum
    r = check_answer("He scored 27 points in 34 minutes on 2026-11-61.", trace=trace)
    assert r.verdict == "problems" and r.findings[0].text == "61"
    src = {"S1": "300 CHF is 315 EUR. 200 GBP is 234 EUR."}
    assert check_answer("That is 315 EUR and 234 EUR, so together 549 EUR.", src).verdict == "ok"
    assert check_answer("That is 315 EUR and 234 EUR, which makes 549 EUR.", src).verdict == "ok"
    assert check_answer("That is 315 EUR and 234 EUR; 549 EUR.", src).verdict == "problems"
    # products and ratios of two stated numbers are not tried: 9,860.41 / 1,860.41 is 5.3 by chance
    src = {"S1": "final_amount 9860.41, interest_earned 1860.41, annual_rate 0.035"}
    r = check_answer("At 5.3 % in total, 8,000 grows to 9,860.41, of which 1,860.41 is interest.", src,
                     question="How much interest does 8,000 earn at 3.5%?")
    assert r.verdict == "problems" and r.findings[0].text.startswith("5.3")


def test_percent_is_not_supported_by_a_bare_fraction():
    trace = [{"name": "loan_cost", "args": {"annual_rate": 0.075, "principal": 15000},
              "result": {"total_interest": 3034.15}}]
    q = "How much interest on 15,000 at 7.5%?"
    assert check_answer("At 7.5% the interest is 3,034.15.", trace=trace, question=q).verdict == "ok"
    r = check_answer("At 0.075% the interest is 3,034.15.", trace=trace, question=q)
    assert r.verdict == "problems" and r.findings[0].text.startswith("0.075")
    # a percentage of 1 or more, or under a key that says pct / percent, is matched as written
    quote = [{"name": "q", "args": {}, "result": {"change_pct": -1.2, "yield_percent": 0.4, "change": 0.3}}]
    assert check_answer("It fell 1.2% and yields 0.4%.", trace=quote).verdict == "ok"
    assert check_answer("It rose 0.3%.", trace=quote).verdict == "problems"     # "change" may be in dollars
    # a percentage worked out in the answer is its fraction: 36 / 240 is 15%, not 0.15%
    calc = [{"name": "calculator", "args": {"expression": "0.15*240"}, "result": {"result": 36.0}}]
    q = "What is 15% of 240?"
    assert check_answer("15% of 240 is 36.", trace=calc, question=q).verdict == "ok"
    assert check_answer("0.15% of 240 is 36.", trace=calc, question=q).verdict == "problems"


def test_a_unit_names_the_field():
    trace = [{"name": "get_product", "args": {"sku": "MX-200"},
              "result": {"price_usd": 249.0, "weight_kg": 1.35, "battery_hours": 18}}]
    assert check_answer("It costs $249 and weighs 1.35 kg.", trace=trace).verdict == "ok"
    r = check_answer("It costs $1.35 and weighs 249 kg.", trace=trace)
    assert r.verdict == "problems" and {f.check for f in r.findings} == {"value-to-field"} and len(r.findings) == 2
    # a value from another call (a calculator) in the same unit is left to the number check
    calc = trace + [{"name": "calculator", "args": {"expression": "249*3"}, "result": {"result": 747.0}}]
    assert check_answer("Three cost $747.", trace=calc).verdict == "ok"
    # two fields with the unit (two products): nothing is bound by the unit alone
    two = trace + [{"name": "get_product", "args": {"sku": "LT-50"}, "result": {"price_usd": 39.9, "weight_kg": 0.6}}]
    r = check_answer("They cost $0.6 and $1.35.", trace=two)
    assert all(f.check != "value-to-field" for f in r.findings)


# ------------------------------------------------------------ 0.1.0.dev8: more ways to name a field
LOAN = [{"name": "loan_cost", "args": {"principal": 15000, "annual_rate": 0.075, "years": 5},
         "result": {"monthly_payment": 300.57, "total_paid": 18034.15, "total_interest": 3034.15, "months": 60}}]


def test_a_word_only_one_field_has():
    assert check_answer("You pay €3,034.15 in interest.", trace=LOAN).verdict == "ok"
    r = check_answer("You pay €300.57 in interest.", trace=LOAN)
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"
    # "total" fits total_paid and total_interest: nothing is bound by it alone
    assert check_answer("It costs €3,034.15 in total.", trace=LOAN).findings == []
    # measure nouns name what is counted, not the field: "after 3 years" is not warranty_years
    prod = [{"name": "p", "args": {"sku": "A"}, "result": {"warranty_years": 2}}]
    assert check_answer("After 3 years it is out of warranty.", trace=prod).findings == []
    # a question value said again is not a field ("a $15,000 loan" next to "interest")
    assert check_answer("On $15,000 of interest-bearing debt you pay €3,034.15.", trace=LOAN).verdict == "ok"


def test_the_subject_of_is():
    assert check_answer("The total interest you'll pay on this loan over 5 years is $3,034.15.",
                        trace=LOAN).verdict == "ok"
    r = check_answer("The total interest you'll pay on this loan over 5 years is $300.57.", trace=LOAN)
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"
    # a subject that names a quantity worked out from the field is left alone
    two = LOAN + [{"name": "loan_cost", "args": {"principal": 15000, "annual_rate": 0.075, "years": 3},
                   "result": {"monthly_payment": 466.6, "total_paid": 16797.6, "total_interest": 1797.6, "months": 36}}]
    r = check_answer("The difference in monthly payment is $166.03.", trace=two)
    assert all(f.check != "value-to-field" for f in r.findings)


def test_ranges():
    quote = [{"name": "q", "args": {"symbol": "X"}, "result": {"price": 72.15, "day_low": 69.8, "day_high": 72.9}}]
    assert check_answer("It traded between $69.80 and $72.90.", trace=quote).verdict == "ok"
    r = check_answer("It traded between $72.90 and $69.80.", trace=quote)
    assert r.verdict == "problems" and {f.check for f in r.findings} == {"value-to-field"}
    ship = [{"name": "s", "args": {"country": "IN"}, "result": {"cost_eur": 24.5, "days_min": 6, "days_max": 10}}]
    assert check_answer("It costs €24.50 and arrives in 6-10 days.", trace=ship).verdict == "ok"
    assert check_answer("Delivery takes from 6 to 10 days.", trace=ship).verdict == "ok"
    r = check_answer("Delivery takes from 6 to 12 days.", trace=ship)
    assert r.verdict == "problems"


def test_min_next_to_a_time_noun_is_minimum():
    from traceground.binding import key_words
    assert key_words("days_min") == ("day", "minimum") and key_words("delay_min") == ("delay",)


def test_a_measure_unit_names_the_field():
    prod = [{"name": "get_product", "args": {"sku": "MX-200"},
             "result": {"price_usd": 249.0, "battery_hours": 18, "weight_kg": 1.35}}]
    assert check_answer("It runs for 18 hours on a charge.", trace=prod).verdict == "ok"
    r = check_answer("It runs for 249 hours on a charge.", trace=prod)
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"
    # a number in hours that is no field of the call is left to the number check
    assert all(f.check != "value-to-field" for f in check_answer("Charge it for 3 hours.", trace=prod).findings)


def test_verb_forms_name_fields():
    fx = [{"name": "convert_currency", "args": {"amount": 120, "from_currency": "USD", "to_currency": "EUR"},
           "result": {"converted_amount": 110.4, "rate": 0.92}}]
    assert check_answer("120 USD converts to about 110.4 EUR.", trace=fx).verdict == "ok"
    r = check_answer("120 USD converts to about 0.92 EUR.", trace=fx)
    assert r.verdict == "problems" and r.findings[0].check == "value-to-field"
    # "4% compounded" is the rate, not compounds_per_year
    dep = [{"name": "compound_interest", "args": {"principal": 5000, "annual_rate": 0.04, "years": 10,
                                                   "compounds_per_year": 12},
            "result": {"final_amount": 7454.16}}]
    assert check_answer("At 4% compounded monthly it grows to $7,454.16.", trace=dep,
                        question="5,000 at 4% compounded monthly for 10 years?").verdict == "ok"


# ------------------------------------------------------------ 0.1.0.dev9: found on the held-out set
@pytest.mark.parametrize("qid", ["h01-120b", "h01-20b", "h09-120b", "h09-20b", "h15-20b", "h02-20b", "h07-20b"])
def test_heldout_correct_answers_have_no_findings(qid):
    r = check_messages(DATA[qid]["messages"])
    assert r.findings == [], [f.message for f in r.findings]


@pytest.mark.parametrize("qid, text, check", [
    ("h02-120b", "16", "number"),                  # a departure time no tool gave; the delay left out
    ("h08-20b", "14.4 %", "number"),               # 228.2 / 1612.3 is 14.2%, not 14.4%
    ("h07-120b", "1.84 billion in revenue", "value-to-field"),     # euros; the tool gives US dollars
])
def test_heldout_wrong_answers_are_reported_for_the_right_reason(qid, text, check):
    r = check_messages(DATA[qid]["messages"])
    found = (" ".join(r.findings[0].text.split()), r.findings[0].check)       # models write narrow spaces
    assert r.verdict == "problems" and found == (text, check)
    if qid == "h07-120b":
        assert "in USD; the answer writes EUR, and no call converted it" in r.findings[0].message


@pytest.mark.parametrize("qid, numbers", [("h14-120b", ["400", "600"]), ("h14-20b", ["800"])])
def test_numbers_from_outside_the_tools_are_reported_as_numbers(qid, numbers):
    # "typical indoor levels (400-600 ppm)": right, but no tool gave it; not a wrong co2_ppm
    r = check_messages(DATA[qid]["messages"])
    assert [(f.check, f.text) for f in r.findings] == [("number", x) for x in numbers]


def test_durations_in_two_units():
    t = [{"name": "f", "args": {"flight_no": "X"}, "result": {"duration_min": 535}}]
    assert check_answer("It takes 535 minutes (8 hours 55 minutes).", trace=t).verdict == "ok"
    assert check_answer("It takes about 8 h 55 min.", trace=t).verdict == "ok"
    assert check_answer("It takes 535 minutes (8 hours 45 minutes).", trace=t).verdict == "problems"


def test_scale_in_the_key_name():
    from traceground.numbers import key_scale
    assert (key_scale("revenue_musd"), key_scale("sales_eur_mn"), key_scale("distance_m")) == (1e6, 1e6, 1.0)
    t = [{"name": "g", "args": {"year": 2025}, "result": {"revenue_musd": 1840.5}}]
    assert check_answer("Revenue was $1.84 billion in 2025.", trace=t).verdict == "ok"
    assert check_answer("Revenue was $1.94 billion in 2025.", trace=t).verdict == "problems"


def test_currency_without_a_conversion():
    t = [{"name": "g", "args": {"year": 2025}, "result": {"net_income_musd": 221.4}}]
    r = check_answer("Net income was €221.4 million.", trace=t)
    assert r.verdict == "problems" and "no call converted it" in r.findings[0].message
    conv = t + [{"name": "convert_currency", "args": {"amount": 221.4, "from_currency": "USD", "to_currency": "EUR"},
                 "result": {"converted_amount": 203.69}}]
    assert check_answer("Net income was $221.4 million, about €203.69 million.", trace=conv).verdict == "ok"


def test_years_and_comparatives_are_not_field_values():
    t = [{"name": "g", "args": {"company": "N", "year": 2024}, "result": {"operating_margin_pct": 15.6, "year": 2024}}]
    assert check_answer("The operating margin in 2024 was 15.6%.", trace=t).verdict == "ok"
    s = [{"name": "s", "args": {"id": "A"}, "result": {"pressure_hpa": 1012.6}},
         {"name": "s", "args": {"id": "B"}, "result": {"pressure_hpa": 1009.3}}]
    assert check_answer("A is at 1012.6 hPa and B at 1009.3 hPa, so A's pressure is 3.3 hPa higher.",
                        trace=s).verdict == "ok"


def test_the_argument_the_words_name_best():
    # "5-year" names years (one word, all of it) before annual_rate ("annual" is yearly too)
    trace = [{"name": "loan_cost", "args": {"principal": 12000, "annual_rate": 0.07, "years": 3},
              "result": {"total_paid": 13338.72}}]
    r = check_answer("Over 5 years you pay 13,338.72.", trace=trace,
                     question="What is the 5-year cost at 7% interest on a 12,000 loan?")
    assert [f.check for f in r.findings] == ["argument"] and r.findings[0].message.endswith("years=3.")
