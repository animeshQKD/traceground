# traceground

[![tests](https://github.com/animeshQKD/traceground/actions/workflows/tests.yml/badge.svg)](https://github.com/animeshQKD/traceground/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/traceground)](https://pypi.org/project/traceground/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/animeshQKD/traceground/blob/main/LICENSE)

**Status: alpha (0.1.1).** It has the number and quote checks over sources; the tool-trace checks
(value-to-field and argument binding, failed calls, tools never called); the wording checks (thinking
aloud, self-contradiction); `check_answer()`, `check_messages()`, the command line, and a Gradio demo
that is also an MCP tool (`space/`). Rules and messages may still change between 0.x versions.

**Read the write-up** on Hugging Face: [what a model-free check catches in real AI answers](https://huggingface.co/blog/animesh1986/traceground-what-a-model-free-check-catches-in-rea),
with real errors from gpt-oss-120b and gpt-oss-20b, and the RAGTruth measurement.

## What it is for

traceground takes an AI answer together with its sources or its tool-call trace, and lists every
number, quote, value or argument that the evidence doesn't support. Each finding names the exact span,
the reason, and what the evidence actually says. No language model is involved, so the same input
always gives the same verdict.

An example of the error it is built for:

* **Question:** "What is the 5-year cost at 7% interest?"
* **Tool call:** `loan_cost(rate=0.07, years=3)` returned `{"total": 12250.43, "monthly": 340.29}`
* **Answer:** "Over 5 years at 7% you pay 12,250 in total, 340.29 a month."

Every number in the answer matches the tool result or the question (12,250 is 12,250.43 rounded), so
a check of numbers alone passes it. The error is that the tool was called with `years=3` when the question asks for 5 years.

## Use

```python
from traceground import check_answer

result = check_answer(
    "Acme's Q3 revenue was $42.1 million, up 8% from Q2.",
    sources=["Acme's revenue for the third quarter was $41.2 million, up 8% from the second quarter."],
)
print(result.to_text())
```

```
PROBLEMS: 2 numbers checked against 1 source: 1 number not supported.
1. [number] "42.1 million" in: Acme's Q3 revenue was $42.1 million, up 8% from Q2.
   "42.1 million" is not in the sources or the question. The closest values they give: 41.2 million (S1).
```

From the command line (exit code 0 ok, 1 problems, 2 usage error, 3 unsure, for use in CI):

```
traceground --answer answer.txt --sources report.txt --question question.txt
```

## The number check (implemented)

A number in the answer is supported when the sources or the question contain it at the precision the
answer wrote it with: "1.98" is supported by 1.9799 and "about 24" by 23.7. Thousands separators,
scientific notation, scale words ("41.2 million"), 7% for 0.07, "about 12,000" for 12,250, and number
words and fractions in the sources ("twenty", "1/2") are understood. Citation markers, labels such as
"Eq. (3)" or "Passage 2", list numbers, cited years, URLs, code, digits glued to words (Q3, CO2, MX-200,
1st), the answer counting its own length ("in 150 words", "a 98-word summary"), a rating scale ("out of
5"), "24/7" and plain integers from 0 to 10 are not checked: when unsure, it says nothing. A number cut
short (1.97 for 1.9799) is reported as minor.

A scale in a key name is understood (revenue_musd = 1840.5 supports "$1.84 billion"), and so is a duration
written in two units ("535 minutes, about 8 hours 55 minutes"). Clock times are compared as times ("2:30
pm" against "14:30"), and the day of a date is checked even with an ordinal ("April 19th"). A conversion
in brackets, "400°F (200°C)", is reported as minor when it is right (within 3%, or 6 degrees) and as
unsupported when it is wrong. A tool result's list counts as giving its length ("based on 3 reviews").

A percentage is not supported by a bare fraction below 1: "0.075%" is not 0.075 (that is 7.5%),
unless the source writes it as a percentage or under a key such as change_pct.

A number the answer computes from numbers it states, which the sources support, is accepted when its
sentence says it is computed: "315 EUR and 234 EUR, a total of 549 EUR" (a sum or difference of two
of them, with a word such as "total", "together", "extra", "warmer"), or "3 lamps at 39.90 each cost
119.70" (a stated number times a count from the question, with "each", "per", "times"). It must round
to the written number at the precision it is written in: "a total of 550 EUR" is reported. A source number times a count from the question
("3 lamps" at 39.90 each is 119.70) is reported as minor: right, but worked out in the answer rather
than by a tool. Thin and narrow no-break spaces work as thousands separators ("40 983.61").

Not yet: signs are not compared, units are converted only in a pair written together ("5 km (3.1
miles)"), and a value computed from numbers the answer does not state (a sum of two source values that
the answer leaves out) is reported as unsupported.

## The quote check (implemented)

Every quotation of three words or more must occur in the source its sentence cites ([S1], [doc2],
[report.txt], or [2] for the second source), or in any source if the sentence cites none. Case,
accents, dashes, quote marks, spacing and punctuation do not matter; the words do. Ellipses and
editorial insertions in square brackets are allowed. A quote that differs only in small words (a, the,
of, my ...), punctuation, the spelling of one word, or singular and plural is reported as minor. A quote
that is not found is reported with the closest wording the sources contain; a quote found in another
source than the one cited is reported with the source it is really in.

```
The quote is not in the cited source. The closest wording, in S1: "does not guarantee that the
reconstructed matrix is positive".
```

Not checked: quotes of one or two words, titles (every main word capitalized), quotes in code, quotes in
single quote marks, example text ('a subject line such as "..."') and the question restated.

## Tool traces (implemented)

Give the tool calls as a list of `{"name", "args", "result"}`, or as a chat (then the question and the
final answer are taken from it: `check_messages(messages)`). A chat can be OpenAI-style messages,
Anthropic Messages API messages (`tool_use` and `tool_result` blocks), or LangChain messages (the
objects, or the dicts of `messages_to_dict`). Sources can be given at the same time, for an agent that
reads documents and calls tools. The tool results and arguments become evidence for the number and quote
checks, and two more checks run.

**Argument binding**: the values in the question must be the ones the tools were called with. Every
number below is in the tool result or the question, so a number check passes this answer; the error is
that the tool computed 3 years, not 5.

```python
result = check_answer(
    "Over 5 years at 7% you pay 12,250 in total, 340.29 a month.",
    question="What is the 5-year cost at 7% interest?",
    trace=[{"name": "loan_cost", "args": {"rate": 0.07, "years": 3},
            "result": {"total": 12250.43, "monthly": 340.29}}],
)
```

```
PROBLEMS: 3 numbers and 2 value-to-field bindings checked against 1 tool call and the question: 1 tool argument different from the question.
1. [argument] "5" in: Over 5 years at 7% you pay 12,250 in total, 340.29 a month.
   The question asks for 5-year, but loan_cost was called with years=3.
```

It also reports a question value whose digits the call shifted by a power of ten (asked p = 0.3,
called with 0.03) and two values swapped between two calls (asked 120 USD and 80 GBP, called with
amount=80 for USD and amount=120 for GBP).

**Value-to-field binding**: a number the answer attaches to a field name must be the value the tool
gave for that field. Field names come from the JSON keys (`rain_chance_pct` is "rain chance";
`field_synonyms` adds names).

```python
result = check_answer(
    "Jordan Reyes scored 27 points with 7 rebounds and 11 assists.",
    trace=[{"name": "player_game_stats", "args": {"player": "Jordan Reyes"},
            "result": {"points": 27, "rebounds": 11, "assists": 7}}],
)
```

```
PROBLEMS: 2 numbers and 3 value-to-field bindings checked against 1 tool call: 2 values attached to the wrong field.
1. [value-to-field] "7 rebounds" in: Jordan Reyes scored 27 points with 7 rebounds and 11 assists.
   "7 rebounds": the tool results give rebounds = 11 (player_game_stats). 7 is the assists (player_game_stats).
2. [value-to-field] "11 assists" in: Jordan Reyes scored 27 points with 7 rebounds and 11 assists.
   "11 assists": the tool results give assists = 7 (player_game_stats). 11 is the rebounds (player_game_stats).
```

A field can also be named in other ways: by a unit (in "weighs 249 kg" the 249 is compared with the
results' only kg field, and reported when it is the value of another field of the same call), by a
word only one multi-word field name has ("€789.52 in interest" for total_interest), by the subject of
"... is N" ("The total interest you'll pay on the loan is $3,034.15"), and by a range ("between $69.80
and $72.90" for day_low and day_high). The right value in another currency is reported when no call
converted it ("€221.4 million" when the tool gives net_income_musd = 221.4).

Both checks stay silent when a binding is unsure: no field word right next to the number (a
preposition such as "for" or "on" starts a new phrase: "the monthly payment for a $30,000 loan"), a number in
another unit than the field ("91.4 °F" for high_c), a clause that says the number is worked out ("the
difference in monthly payment is $166") or a comparative follows it ("3.3 hPa higher"), a year ("in
2024"), a sentence with "respectively", a question number
with no argument that names it or resembles it, a number that is part of a name or an address in the
results ("4 Eggs & Pizza", "223 Anacapa St").

From the command line: `traceground --trace chat.json`, or `traceground --trace calls.json --answer
answer.txt --question question.txt`.

## What the answer says about its tools, and its own wording (implemented)

* **Failed calls**: a call failed, was not called again successfully (nor replaced by another tool
  called about the same thing), and the answer reads as if it had worked.
* **Tools never called**: "I searched the web" with no search tool, "I ran the code", "I queried the
  database", "I used the X tool". Offers ("I can search the web") and advice are not claims.
* **Thinking aloud** left in the final answer: "Wait, let me check:", "Let me report the tool's
  numbers:", a paragraph that takes back what came before. Ordinary openers ("Let me explain") are fine.
* **Self-contradiction**: "The passages do not say how long the warranty lasts." followed by a sentence
  that gives it from the sources. A statement about one passage ("Passage 3 does not mention it") is not
  a contradiction when another passage gives it.

```python
result = check_answer(
    "I searched the web and found that the MX-200 warranty is 2 years. Wait, let me check: yes, 2 years.",
    trace=[{"name": "lookup_product", "args": {"sku": "MX-200"}, "result": {"warranty_years": 2}}],
)
```

```
PROBLEMS: 2 value-to-field bindings checked against 1 tool call: 1 claim about a tool that was not called; 1 passage of the model thinking aloud.
1. [tool-not-called] "I searched the web" in: I searched the web and found that the MX-200 warranty is 2 years.
   The answer says "I searched the web", but no tool for a web search was called (calls: lookup_product).
2. [self-talk] "Wait, let me check:" in: Wait, let me check: yes, 2 years.
   This is the model thinking aloud, left in the final answer: "Wait, let me check:".
```

## Measured

**On RAGTruth.** On the test split of [RAGTruth](https://github.com/ParticleMedia/RAGTruth), 2,675 real
answers by six models with hallucinations marked by people, measured once with 0.1.0.dev12 (whose checks
0.1.0 keeps unchanged) after development on the train split: 7 of traceground's 172 high-severity findings
(4%) were false alarms, by hand review. It flagged 85 of the 306 marked spans that contain a digit, and 8%
to 16% of the answers with any marked span: most marked hallucinations are claims in words, which it does
not check. 0.1.1 fixes those 7 false alarms, so for 0.1.1 the test split is no longer unseen.

**On fresh tool-calling chats (0.1.1).** 40 answers by gpt-oss-120b and gpt-oss-20b to 20 questions on five
tools made for this test (restaurants with reviews, events, trains, hotels, news articles), written after
the 0.1.1 changes and labelled by hand before traceground was run on them:

* False alarms on 5 of the 34 correct answers (15%); three come from one cause, a rating said in stars
  ("an overall rating of 4.3 stars") tied to the reviews' stars instead of the rating. 0.1.0 had 6.
* Of the 3 wrong answers, it caught 1 (a speed comparison by arrival times, "faster by 2 hours 49
  minutes"); the other 2 called no tool and said no tool existed, with no number or quote to check.
* Planted errors: 115 of 140 caught (82%), but a value of another field only 10 of 32 (31%), against 60%
  to 75% on the earlier sets.

Details, and how to rerun both, in
[eval/README.md](https://github.com/animeshQKD/traceground/blob/main/eval/README.md) and
[eval/results/review_heldout2_2026-11-20.md](https://github.com/animeshQKD/traceground/blob/main/eval/results/review_heldout2_2026-11-20.md).

## Demo

Try it online: **[huggingface.co/spaces/animesh1986/traceground](https://huggingface.co/spaces/animesh1986/traceground)**.
Paste an answer with its sources, its tool calls (or a whole chat), or both, and the page marks every finding
on the answer, shows the evidence for each, and greys out the sentences it has nothing to check in. The same
check is an MCP tool at https://animesh1986-traceground.hf.space/gradio_api/mcp/ (on the Space it is named
`traceground_traceground_check`: Gradio puts the Space's name in front).

The page is `space/app.py`, and it runs on your own computer too, with no API key. From a copy of this
repository:

```
pip install traceground "gradio[mcp]==6.32.0"
python space/app.py
```

then open http://127.0.0.1:7860. The same check is an MCP tool, `traceground_check`, at
http://127.0.0.1:7860/gradio_api/mcp/ while the page runs ([space/README.md](https://github.com/animeshQKD/traceground/blob/main/space/README.md)).

## Planned next

* 0.1.2: the false alarms and misses the fresh chats showed (a rating said in stars; a value of
  another field given with a verb or unit, such as "costs €16"), measured on another fresh set.
* Citations mode: marker styles, every marker checked, every factual sentence cited (optional).
* An opt-in automatic fix where a fix is certain (a number cut short, thinking aloud removed).
* LangGraph / LangChain helpers.
* Report-only stays the default; when a check is unsure, it says nothing.

## Install

```
pip install traceground
```

Python 3.10 to 3.14. The package depends on the standard library only. To work on it, from a copy of this
repository: `pip install -e ".[test]"`, then `python -m pytest`.

## License

MIT
