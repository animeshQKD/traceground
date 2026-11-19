"""The number check: what counts as a number, what is left out, and when the evidence supports it.
Every rule has a case it must flag and a case it must pass."""
import pytest

from traceground import check_answer
from traceground.numbers import answer_numbers, find_numbers


def values(text):
    return [(n.text, n.value) for n in find_numbers(text)]


def flagged(answer, sources, question="", **kw):
    """The texts of the high findings."""
    return [f.text.strip() for f in check_answer(answer, sources, question, **kw).findings if f.severity == "high"]


# ---------------------------------------------------------------- reading numbers
@pytest.mark.parametrize("text, value", [
    ("12,250.43", 12250.43), ("1,234,567", 1234567.0), ("1,23,456", 123456.0), ("0.5", 0.5),
    ("3.2e-4", 3.2e-4), ("3.2E-4", 3.2e-4), ("3.2×10⁻⁴", 3.2e-4), ("3.2 x 10^-4", 3.2e-4), ("3.2·10^(-4)", 3.2e-4),
    ("10^-4", 1e-4), ("10⁻⁴", 1e-4), ("−0.5", 0.5), ("-0.5", 0.5), ("+3.5", 3.5), ("42", 42.0),
])
def test_reads_one_number(text, value):
    (got,) = find_numbers(text)
    assert got.value == pytest.approx(value) and got.text == text


@pytest.mark.parametrize("text", ["7%", "7 %", "7 percent", "7 per cent"])
def test_reads_percentages(text):
    (n,) = find_numbers(text)
    assert n.value == 7 and n.percent


@pytest.mark.parametrize("text, scale", [("41.2 million", 1e6), ("12k", 1e3), ("3 lakh", 1e5), ("2 crore", 1e7),
                                         ("5bn", 1e9), ("4.5 billion", 1e9)])
def test_reads_scale_words(text, scale):
    (n,) = find_numbers(text)
    assert n.scale == scale


@pytest.mark.parametrize("text", ["COVID-19", "MX-200", "GPT-4", "Q3", "rho_1", "λ_1", "CO2", "H2O", "1st", "22nd",
                                  "5km", "3D", "v2"])
def test_digits_glued_to_a_word_are_not_numbers(text):
    assert find_numbers(text) == []


def test_range_and_uncertainty_give_two_numbers():
    assert values("5–10") == [("5", 5.0), ("10", 10.0)]
    assert values("0.92 ± 0.01") == [("0.92", 0.92), ("0.01", 0.01)]


def test_a_comma_without_three_digits_separates_numbers():
    assert values("[0.3,0.1]") == [("0.3", 0.3), ("0.1", 0.1)]


@pytest.mark.parametrize("answer", [
    "As shown in Eq. (3) and Fig. 12, see Table 14.", "See Section 4.2 and page 17.", "Step 22 is next.",
    "The result [1] and [S14] and [doc23] and [P1-p4-2] and [12, 13].", "Smith et al. 2020 found it.",
    "Hradil (1997) proposed it.", "This was shown before (Smith, 2020; Jones 2019).",
    "1. First point\n2. Second point\n13. Thirteenth point",
])
def test_labels_citations_list_numbers_and_cited_years_are_not_checked(answer):
    keep, _left = answer_numbers(answer)
    assert keep == []


@pytest.mark.parametrize("answer", [
    "Details at https://example.com/2024/05/report-77.html and www.example.org/v/2023.",
    "Write to team42@example.com.", "Set `retries = 30` in the config.",
    "Use this:\n```python\nx = 4096\ny = 0.75\n```\nThat is all.",
])
def test_urls_emails_and_code_are_not_checked(answer):
    assert answer_numbers(answer)[0] == []


def test_small_integers_are_left_out_unless_asked():
    assert answer_numbers("It has 3 options.")[0] == []
    assert [n.text for n in answer_numbers("It has 3 options.", check_small_integers=True)[0]] == ["3"]
    # a small integer with a percent sign, a decimal or a scale word is checked
    assert [n.text for n in answer_numbers("3% and 3.0 and 3 million")[0]] == ["3%", "3.0", "3 million"]


# ---------------------------------------------------------------- supported or not
def test_real_error_a_number_no_source_contains():
    src = ["Acme's revenue for the third quarter was $41.2 million, up 8% from the second quarter."]
    r = check_answer("Acme's Q3 revenue was $42.1 million, up 8% from Q2.", src)
    (f,) = r.findings
    assert r.verdict == "problems" and f.text == "42.1 million" and f.severity == "high"
    assert "41.2 million (S1)" in f.message
    assert f.evidence[0]["source"] == "S1" and "41.2 million" in f.evidence[0]["context"]


@pytest.mark.parametrize("answer, source", [
    ("about 24 °C", "high 23.7 °C"),                     # rounding to the precision written
    ("1.98", "1.9799"), ("2.0", "1.9799"), ("0.26", "0.255"),
    ("12,250", "12250.43"), ("12,250.43", "12250.43"),   # thousands separators
    ("12250.43", "12,250.43"), ("1,23,456", "123456"),
    ("7%", "rate 0.07"), ("0.07", "rate 7%"), ("61.12%", "0.61122"),   # percent and fraction
    ("41,200,000", "41.2 million"), ("41.2 million", "41200000"), ("12k", "12,000"),
    ("3.2×10⁻⁴", "3.2e-4"), ("0.00032", "3.2 x 10^-4"),
    ("about 12,000", "12,250"), ("roughly 1,200", "1,234"), ("~300", "296"),
    ("20 years", "twenty years"), ("21 apples", "twenty-one apples"), ("50%", "half of them"),
    ("200 units", "model MX-200"),                        # loose digits in the evidence count
    ("0.5", "1/2 of them"), ("75%", "3/4 of the runs"), ("0.333", "1/3"),
])
def test_supported(answer, source):
    assert flagged(answer, [source]) == []


@pytest.mark.parametrize("answer, source", [
    ("25 °C", "high 23.7 °C"),                           # 23.7 rounds to 24
    ("1.99", "1.9799"), ("12,251", "12250.43"), ("41.3 million", "41.2 million"),
    ("12,000", "12,250"),                                 # a round number without "about" is not rounding
    ("7%", "rate 0.7"), ("4.2e-4", "3.2e-4"), ("1,234.5", "1234.4"),
])
def test_not_supported(answer, source):
    assert flagged(answer, [source])


def test_percent_as_fraction_can_be_turned_off():
    assert flagged("7%", ["rate 0.07"], percent_as_fraction=False) == ["7%"]


def test_numbers_in_the_question_count_as_evidence():
    assert flagged("Over 36 months you pay 340.29.", ["monthly 340.29"]) == ["36"]
    assert flagged("Over 36 months you pay 340.29.", ["monthly 340.29"], "What is the 36-month cost?") == []


def test_a_number_cut_short_is_a_minor_finding_with_a_certain_fix():
    r = check_answer("The value is 1.97.", ["The value is 1.9799."])
    (f,) = r.findings
    assert f.severity == "low" and f.suggestion == "1.98" and r.verdict == "ok"
    assert "1.9799 (S1) cut short" in f.message


def test_cut_short_keeps_the_sign_and_the_separators():
    (f,) = check_answer("It fell by −1,234.5.", ["a change of -1234.56"]).findings
    assert f.suggestion == "−1,234.6"


def test_no_close_value_says_so():
    (f,) = check_answer("It is 950.", ["It is 3.2 and 7."]).findings
    assert "give no value close to it" in f.message and f.evidence == []


def test_spans_point_into_the_answer():
    answer = "First 1.5. Then, as shown, 42.1 million and 77.7."
    r = check_answer(answer, ["1.5 only"])
    assert [answer[f.start:f.end] for f in r.findings] == [f.text for f in r.findings]
    assert [f.sentence for f in r.findings] == ["Then, as shown, 42.1 million and 77.7."] * 2


def test_a_realistic_correct_answer_raises_nothing():
    sources = {
        "trial.txt": "The trial enrolled 1,204 patients aged 18-65 between March 2023 and June 2024. "
                     "The response rate was 61.2% in the treatment arm and 48.7% with placebo (p = 0.003). "
                     "Median follow-up was 14.5 months; two thirds of patients completed the study.",
    }
    answer = ("The trial [trial.txt] enrolled about 1,200 patients aged 18–65 (2023–2024). Response was 61% "
              "with treatment against 48.7% with placebo, p = 0.003, over a median of 14.5 months; see "
              "Table 2 and https://example.org/trial/2024. Step 3 of the protocol is unchanged.")
    r = check_answer(answer, sources)
    assert r.findings == [] and r.verdict == "ok"
    assert [n.text for n in answer_numbers(answer)[0]] == [
        "1,200", "18", "65", "2023", "2024", "61%", "48.7%", "0.003", "14.5"]      # Table 2, the URL, Step 3: left out
    assert r.stats["numbers_checked"] == 9
