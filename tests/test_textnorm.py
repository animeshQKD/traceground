from traceground.textnorm import clean, match_form, sentence_spans, split_sentences


def test_clean_keeps_the_wording():
    assert clean("ﬁnal  e­ﬃcient​ text here") == "final efficient text here"
    assert clean("fu¨r") == "für"


def test_match_form_ignores_case_dashes_quotes_and_spaces():
    assert match_form("“Small but Robust” — 3%") == match_form('"small but robust" 3 %')
    assert match_form("entangle-ment") == match_form("entanglement")
    assert match_form("does not guarantee") != match_form("does not ensure")


def test_sentences_do_not_split_inside_decimals_abbreviations_or_initials():
    text = "The value is 0.92 ± 0.01, see Fig. 2 and Eq. 3. A. Einstein agreed, e.g. in 1935. Next one!"
    assert split_sentences(text) == ["The value is 0.92 ± 0.01, see Fig. 2 and Eq. 3.",
                                     "A. Einstein agreed, e.g. in 1935.", "Next one!"]


def test_sentence_spans_are_offsets_into_the_original_text():
    text = "  First one.   Second one?\n\n- item one\n- item two"
    spans = sentence_spans(text)
    assert [text[a:b] for a, b in spans] == ["First one.", "Second one?", "- item one", "- item two"]


def test_lower_case_after_a_period_does_not_split():
    assert split_sentences("It costs approx. two dollars at 3 a.m. Today it is more.") == [
        "It costs approx. two dollars at 3 a.m. Today it is more."]
