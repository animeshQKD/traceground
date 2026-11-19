"""check_answer() and check_messages(): the calls most users need."""
from traceground import binding, numbers, quotes, selftalk, textnorm, toolchecks, traces
from traceground.result import Result


def normalize_sources(sources) -> list:
    """Accept the usual shapes and return [(id, text), ...]:
    None; one string; a list of strings (ids S1, S2, ...); a dict {id: text}; a list of
    (id, text) pairs; a list of dicts with "text" (and "id")."""
    if sources is None:
        return []
    if isinstance(sources, str):
        return [("S1", sources)]
    if isinstance(sources, dict):
        return _checked_ids([(str(k), str(v)) for k, v in sources.items()])
    out = []
    for i, s in enumerate(sources, 1):
        if isinstance(s, str):
            out.append((f"S{i}", s))
        elif isinstance(s, dict):
            out.append((str(s.get("id", f"S{i}")), str(s["text"])))
        elif isinstance(s, (tuple, list)) and len(s) == 2:
            out.append((str(s[0]), str(s[1])))
        else:
            raise TypeError(f"source {i}: expected a string, a (id, text) pair or a dict with 'text', got {type(s).__name__}")
    return _checked_ids(out)


def _checked_ids(out: list) -> list:
    ids = [sid for sid, _t in out]
    if len(set(ids)) != len(ids):
        raise ValueError(f"source ids must be unique, got {ids}")
    if "question" in ids:
        raise ValueError('"question" is reserved for the question; give the source another id')
    return out


def check_answer(answer, sources=None, question: str = "", trace=None, *, percent_as_fraction: bool = True,
                 check_small_integers: bool = False, check_quotes: bool = True, min_quote_words: int = 3,
                 check_bindings: bool = True, field_synonyms=None, check_wording: bool = True) -> Result:
    """Check `answer` against its evidence: `sources` (texts), the `question`, and a tool-call `trace`.

    Checks: every number must be supported by the evidence; every quotation of `min_quote_words` words
    or more must occur in the source its sentence cites (or in any source). With a trace, also: a value
    the answer attaches to a field name must be the value the tool gave for it (value-to-field); the
    values in the question must be the ones the tools were called with (argument binding); a failed
    call must not be reported as a result; the answer must not claim tools that were not called.
    The wording (check_wording): no thinking aloud left in, and no "the sources do not say X" followed
    by X from the sources.

    `trace` is a list of {"name", "args", "result"} or OpenAI-style chat messages (see traces.py). When
    the messages hold the question and the final answer, `answer` and `question` may be left empty.

    Returns a Result: verdict "ok", "problems" (at least one finding of severity "high") or "unsure"
    (there are numbers or quotes to check but no evidence at all, and nothing else was found). Nothing
    in the answer is changed.
    """
    calls = []
    if trace is not None:
        t_question, calls, t_answer = traces.load_trace(trace)
        question = question or t_question
        answer = answer if answer else t_answer
        traces.name_calls(calls)
    if trace is not None and not answer:
        raise ValueError("no answer to check: pass the answer, or a chat whose last assistant message is the answer")
    if not isinstance(answer, str):
        raise TypeError(f"answer must be a string, got {type(answer).__name__}")
    srcs = normalize_sources(sources)
    question = question or ""
    ids = {sid for sid, _t in srcs}
    clash = [c.id for c in calls if c.id in ids or c.id == "question"]
    if clash:
        raise ValueError(f"a tool call and a source have the same id: {clash}")
    evidence = srcs + [(c.id, c.render() + _counts_text(c)) for c in calls]
    spans = textnorm.sentence_spans(answer)

    def sentence_of(pos):
        return textnorm.sentence_at(answer, pos, spans)

    has_q = bool(question.strip())
    has_evidence = bool(srcs or calls or has_q)
    kinds = (["the sources"] if srcs else []) + (["the tool results"] if calls else []) + ["the question"]
    name = ", ".join(kinds[:-1]) + " or " + kinds[-1] if len(kinds) > 1 else kinds[0]
    findings, stats = numbers.check_numbers(
        answer, evidence, question, percent_as_fraction=percent_as_fraction,
        check_small_integers=check_small_integers, sentence_of=sentence_of, evidence_name=name)
    if check_quotes:
        q_findings, q_stats = quotes.check_quotes(answer, evidence, question, min_words=min_quote_words,
                                                  sentence_of=sentence_of)
        inside = [(f.start, f.end) for f in q_findings]
        findings = [f for f in findings if not any(a <= f.start < b for a, b in inside)] + q_findings
        stats.update(q_stats)
    else:
        stats.update({"quotes_checked": 0, "quotes_not_found": 0, "quotes_wrong_source": 0,
                      "quotes_changed_slightly": 0})
    if not has_evidence:
        findings = []                 # nothing to check numbers and quotes against: no verdict on them
    stats.update({"bindings_checked": 0, "bindings_wrong": 0, "question_values": 0, "arguments_wrong": 0,
                  "tool_calls_failed_unreported": 0, "tool_claims_unbacked": 0})
    if trace is not None:
        if calls and check_bindings:
            v_findings, v_stats = binding.check_value_to_field(answer, calls, field_synonyms=field_synonyms,
                                                               sentence_of=sentence_of)
            bound = [(f.start, f.end) for f in v_findings]
            findings = [f for f in findings if not any(a < f.end and f.start < b for a, b in bound)] + v_findings
            a_findings, a_stats = binding.check_arguments(answer, question, calls, sentence_spans=spans,
                                                          sentence_of=sentence_of)
            findings += a_findings
            stats.update(v_stats)
            stats.update(a_stats)
        f_findings, f_stats = toolchecks.check_failed_calls(answer, calls, sentence_spans=spans,
                                                            sentence_of=sentence_of)
        n_findings, n_stats = toolchecks.check_tools_not_called(answer, calls, sentence_of=sentence_of)
        findings += f_findings + n_findings
        stats.update(f_stats)
        stats.update(n_stats)
    stats.update({"self_talk": 0, "self_contradictions": 0})
    if check_wording:
        s_findings, s_stats = selftalk.check_self_talk(answer, sentence_of=sentence_of)
        c_findings, c_stats = selftalk.check_self_contradiction(answer, spans, evidence, sentence_of=sentence_of)
        findings += s_findings + c_findings
        stats.update(s_stats)
        stats.update(c_stats)
    findings.sort(key=lambda f: (f.start, f.check))
    # a number finding that a quote or a value-to-field finding replaced is no longer counted as a number
    nums = [f for f in findings if f.check == "number"]
    computed = sum(f.severity == "low" and numbers.COMPUTED_NOTE in f.message for f in nums)
    stats["numbers_unsupported"] = sum(f.severity == "high" for f in nums)
    stats["numbers_computed_in_answer"] = computed
    stats["numbers_cut_short"] = sum(f.severity == "low" for f in nums) - computed
    stats["sources"] = len(srcs)
    stats["tool_calls"] = len(calls)
    stats["tool_calls_failed"] = sum(c.error for c in calls)

    n_num, n_quote, n_bind = stats["numbers_checked"], stats["quotes_checked"], stats["bindings_checked"]
    parts = ([_n(n_num, "number")] if n_num else []) + ([_n(n_quote, "quote")] if n_quote else []) + \
            ([_n(n_bind, "value-to-field binding")] if n_bind else [])
    things = ", ".join(parts[:-1]) + (" and " if len(parts) > 1 else "") + (parts[-1] if parts else "")
    problems = [(stats["numbers_unsupported"], "number", "not supported"),
                (stats["numbers_cut_short"], "number", "cut short"),
                (stats["numbers_computed_in_answer"], "number", "worked out in the answer, not by a tool"),
                (stats["quotes_not_found"], "quote", "not found"),
                (stats["quotes_wrong_source"], "quote", "in another source than the one cited"),
                (stats["quotes_changed_slightly"], "quote", "changed slightly (small words, punctuation or spelling)"),
                (stats["bindings_wrong"], "value", "attached to the wrong field"),
                (stats["arguments_wrong"], "tool argument", "different from the question"),
                (stats["tool_calls_failed_unreported"], "failed tool call", "reported as if it had worked"),
                (stats["tool_claims_unbacked"], "claim", "about a tool that was not called"),
                (stats["self_talk"], "passage", "of the model thinking aloud"),
                (stats["self_contradictions"], "self-contradiction", "about what the sources say")]
    if not has_evidence:
        problems = problems[8:]                  # only the wording can be judged without evidence
    found = [f"{_n(k, word)} {what}" for k, word, what in problems if k]
    high = any(f.severity == "high" for f in findings)
    if not has_evidence:
        if high:
            summary = "; ".join(found) + "." + (f" {things} not checked: no sources or question given." if things else "")
            return Result(verdict="problems", findings=findings, summary=summary[0].upper() + summary[1:], stats=stats)
        if n_num or n_quote:
            return Result(verdict="unsure", findings=findings, stats=stats,
                          summary=f"{things} in the answer, but no sources or question to check against.")
        return Result(verdict="ok", findings=findings, stats=stats, summary="No numbers or quotes to check.")
    if not parts and not found:
        return Result(verdict="ok", findings=findings, stats=stats, summary="No numbers or quotes to check.")
    against = ([_n(len(srcs), "source")] if srcs else []) + ([_n(len(calls), "tool call")] if calls else []) + \
              (["the question"] if has_q else [])
    against_txt = ", ".join(against[:-1]) + (" and " if len(against) > 1 else "") + against[-1]
    summary = (f"{things or 'The answer'} checked against {against_txt}: "
               + ("; ".join(found) if found else "all supported") + ".")
    return Result(verdict="problems" if high else "ok", findings=findings, summary=summary, stats=stats)


def _counts_text(call) -> str:
    """How many items each list in the result has, as text the number check can use ("reviews: 3 items")."""
    counts = binding.list_counts([call])
    return ("\n(counts) " + "; ".join(f"{w}: {n} items" for w, n in counts)) if counts else ""


def check_messages(messages, sources=None, **options) -> Result:
    """Check the final answer of a chat against its tool results, its question and any `sources`. The
    chat can be OpenAI-style messages, Anthropic Messages API messages (tool_use and tool_result blocks)
    or LangChain messages (objects or messages_to_dict dicts). Same options as check_answer()."""
    return check_answer(None, sources, "", trace=messages, **options)


def _n(k: int, word: str) -> str:
    return f"{k} {word}{'' if k == 1 else 's'}"
