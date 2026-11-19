"""The quote check: every rule has a case it must flag and a case it must pass."""
import pytest

from traceground import check_answer
from traceground.citations import cited, marker_spans
from traceground.quotes import closest_wording, find_quotes

SRC = {
    "S1": "Linear inversion does not guarantee that the reconstructed matrix is positive.",
    "S2": "Firmware updates are installed automatically every night at 3 a.m.",
}


def quote_findings(answer, sources=SRC, **kw):
    return [f for f in check_answer(answer, sources, **kw).findings if f.check == "quote"]


# ---------------------------------------------------------------- finding quotes
def test_finds_quotes_of_three_words_or_more_with_any_double_quote_marks():
    answer = 'A "two words" B "three short words" C “curly quoted text here” D «guillemet quoted text».'
    assert [q for _a, _b, q in find_quotes(answer)] == ["three short words", "curly quoted text here",
                                                       "guillemet quoted text"]


def test_quotes_in_code_and_single_quotes_are_not_checked():
    assert find_quotes('Run `print("not a real quote here")` now.') == []
    assert find_quotes("He said 'this is not checked at all' today.") == []


def test_span_is_the_text_inside_the_marks():
    answer = 'It says "does not guarantee that" here.'
    ((a, b, q),) = find_quotes(answer)
    assert answer[a:b] == q == "does not guarantee that"


# ---------------------------------------------------------------- citations
def test_markers_name_sources():
    ids = ["S1", "S2", "doc3", "report.txt"]
    assert cited("as shown [S2] and [doc3, report.txt].", ids) == ["S2", "doc3", "report.txt"]
    assert cited("bare numbers [1] and [2; 9]", ids) == ["S1", "S2"]
    assert cited("not markers [sic] [1999] [x]", ids) == []
    assert marker_spans("a [sic] b [S1]", ids) == [(10, 14)]


# ---------------------------------------------------------------- supported or not
@pytest.mark.parametrize("answer", [
    'It "does not guarantee that the reconstructed matrix is positive" [S1].',
    'It “Does NOT guarantee that the reconstructed‐matrix is positive” [S1].',   # case, curly marks, hyphen
    'It "does not guarantee that the reconstructed matrix is positive." [S1]',               # punctuation inside
    'Updates are "installed automatically every night" [S2].',
    'Updates are "installed automatically every night".',                                     # no citation: any source
    'It "does not guarantee ... is positive" [S1].',                                          # ellipsis
    'It "does not guarantee that the reconstructed matrix is positive". [S1]',                # marker after the period
    'Updates are "installed automatically every night" [2].',                                 # bare number for S2
])
def test_supported_quotes(answer):
    assert quote_findings(answer) == []


def test_real_error_a_quote_with_changed_words():
    (f,) = quote_findings('The source warns that linear inversion "does not ensure that the reconstructed '
                          'matrix is positive" [S1].')
    assert f.severity == "high" and f.text == "does not ensure that the reconstructed matrix is positive"
    assert f.message == ('The quote is not in the cited source. The closest wording, in S1: '
                         '"does not guarantee that the reconstructed matrix is positive".')
    assert f.evidence == [{"source": "S1", "value": "does not guarantee that the reconstructed matrix is positive",
                           "context": ""}]
    assert f.suggestion is None                            # a closest wording is not a certain fix


def test_real_error_a_quote_from_another_source_than_the_one_cited():
    (f,) = quote_findings('According to the manual, "firmware updates are installed automatically every night" [S1].')
    assert f.message == ('The quote is not in S1, which this sentence cites. It is in S2: '
                         '"Firmware updates are installed automatically every night".')
    assert f.evidence[0]["source"] == "S2"


def test_a_quote_nothing_resembles():
    (f,) = quote_findings('They call it "a revolution in quantum cooking".')
    assert f.message == "The quote is not in the sources, and nothing there is close to it."


def test_ellipsis_parts_must_all_be_there():
    assert quote_findings('It "does not guarantee ... is always positive" [S1].')


def test_a_quote_of_the_question_is_supported():
    r = check_answer('You asked "what is the warranty period".', ["The warranty is 2 years."],
                     "What is the warranty period?")
    assert r.findings == []


def test_no_sources_is_unsure():
    assert check_answer('They say "this is a quote".').verdict == "unsure"


def test_min_quote_words():
    assert quote_findings('It is "fast and cheap" [S1].') != []
    assert quote_findings('It is "fast and cheap" [S1].', min_quote_words=4) == []


def test_a_number_in_a_flagged_quote_is_reported_once():
    r = check_answer('It says "updates run every night at 4 a.m. sharp" [S2].', SRC)
    assert [f.check for f in r.findings] == ["quote"]


def test_closest_wording_returns_the_source_wording():
    sid, wording, ratio = closest_wording("installed automatically every evening", list(SRC.items()))
    assert sid == "S2" and wording == "installed automatically every night" and 0.6 <= ratio < 1


def test_editorial_insertions_in_brackets_are_skipped():
    assert quote_findings('It "does not guarantee that [the] reconstructed matrix is positive" [S1].') == []
    assert quote_findings('It "does not guarantee [that] the matrix is negative" [S1].')      # still wrong words


@pytest.mark.parametrize("title", ["Attention Is All You Need", "The Theory of Quantum Information",
                                   "A Mathematical Theory of Communication"])
def test_titles_are_not_checked(title):
    assert quote_findings(f'The paper "{title}" says so [S1].') == []


def test_a_sentence_case_quote_is_still_checked():
    assert quote_findings('The paper says "Attention is all you need" [S1].')


@pytest.mark.parametrize("quote, source, wording", [
    ("updates are installed every week", "Updates are installed automatically every night.",
     "Updates are installed automatically every night"),                 # extra word in the source
    ("the cat sat quietly", "yesterday the dog sat quietly on the mat", "the dog sat quietly"),   # first word changed
])
def test_closest_wording_covers_the_changed_words_at_both_ends(quote, source, wording):
    assert closest_wording(quote, [("S", source)])[1] == wording
