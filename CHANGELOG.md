# Changelog

All notable changes to traceground are listed here. Versions follow [Semantic Versioning](https://semver.org/).

## 0.2.0

The last planned release. Developed on the third held-out set (eval/results/review_heldout3_2026-11-21.md),
then measured once on a final test set written after the code was frozen, with the result fixed in
advance to be published as it came out and the code not changed after it.

### Fixed

- Arithmetic the answer does itself is accepted in more forms: a difference said with "less", "more
  expensive", "a decline of", "fell", "rose" (and the like); a difference of two percentages in percentage
  points ("fell from 7.1% to 6.5%, a decline of 0.6 percentage points"); and the result of a working the
  answer writes next to it with ×, ÷, + or − ("€142 (€39 × 3 months + €25 joining fee)", "€9.80 ÷ 4 ≈
  **€2.45**"), when at least one of its numbers is in the evidence and the others are too or are whole
  counts (so "50 x 20 = 1000" of made-up numbers is still reported).
- Value-to-field: a value a calculator worked out from the field is not compared with it, also when the
  calculator's result has no field name ({"result": 21.32} for "1450/68"); a field named right after a time
  unit is the one meant ("35 minutes cook" for cook_min, but not "5 years the total paid"); of the same field
  in two calls, the call whose item (a string argument such as "B-12") the answer names last before the
  number; and the parts of a duration ("2 hours 11 minutes") are not compared with fields.

On the third held-out set, false alarms on correct answers went from 7 of 34 to 1, and the planted errors
caught from 162 of 199 to 232 of 270 (an answer that is flagged is not used for planting). On the dev set and the first two held-out sets, no false alarm was added and the
planted errors caught went up or stayed (dev 600 to 608, first held-out 263 to 272). On RAGTruth, test is
unchanged, and on train one finding on a marked span is no longer raised: "1010 = 8 + 4 + 2 + 1 = 15", right
arithmetic of source numbers behind a wrong claim (binary 1010 is 10).

### Measured

On the final test (79 answers by gpt-oss-120b and gpt-oss-20b to 40 questions on eight new tools, labelled
by hand before traceground was run; eval/results/review_final_2026-11-21.md): false alarms on 20 of 62
correct answers (32%; 0.1.2: the same 20), 2 of 8 wrong answers caught (the other 6 had no number or quote
to check, or a misspelt name), and 249 of 282 planted errors caught (88%; 0.1.2: 250). Fifteen of the false
alarms are arithmetic the answer does itself in a form the rules do not read; 17 of the 40 questions asked
for a computed number.

### Known, not fixed

- A number the answer works out without showing the working and without a word the rules know ("10 weeks
  at 3 hours per week, 30 hours"; "twice the €2.40 fare"; "€21.60 after the 10% discount") is reported.
- A clock time plus a duration ("the 8:00 bus ... 41 minutes ... 8:41") is reported, and a clock time in the
  question can be read as a tool argument ("8:00" as "00").
- A price can be compared with a percentage field ("the early-bird price is €408" against
  early_bird_pct), and "2 hours and 15 minutes" is not read as one duration.

### Added (repository)

- The third and final held-out sets' tools, questions, runs, scores and hand reviews (`--set heldout3`,
  `--set final`).
- The demo on the Space installs traceground 0.2.0. The package is marked beta.

## 0.1.2

Fixes for the false alarms and misses found by hand on the second held-out set
(eval/results/review_heldout2_2026-11-20.md), which was used to develop them and so no longer measures
0.1.2 on unseen answers; a third held-out set, written after these changes and before any model answered
it, does (eval/questions_heldout3.json). On the second set, false alarms on correct answers went from 5 to 1
and a planted value of another field was caught 64% of the time instead of 31%. On the dev set, the first
held-out set and RAGTruth (train and test), no high-severity finding changed; the planted errors caught
stayed at 600 on the dev set and went from 262 to 263 on the first held-out set.

### Fixed

- A field named before the number wins over a list's field named after it: "an overall rating of 4.3
  stars" is the rating, not the reviews' stars; and "an overall rating of 3 stars" is now compared with the
  rating, even though one review gave 3 stars.
- A list's field named for a number that the whole holds, with the list not mentioned near it, is not
  compared: "Harbor Noodle House (3.9 stars)" for the restaurant's rating.
- The difference of two durations the answer states, with a word such as "faster" or "difference", is
  worked out in the answer ("1 hour 52 minutes ... 2 hours 11 minutes ... faster by 19 minutes"); the parts
  of a duration are no longer added or subtracted as numbers of their own.
- The result of a product the answer writes next to it ("€426 for the rooms (3 × €142)", "3 × €142 =
  €426") is worked out in the answer, and neither it nor the multiplier is compared with a field.
- Value-to-field: a number followed by "is higher than ..." is the field's value, not a worked-out
  difference ("a guest rating of 142 is higher than ..." is now compared with the guest rating); of several
  fields in the number's unit, the one whose word is in its clause is meant ("0.8 km from the train
  station": station_km; "a night costs €142": the price field rate_eur, not breakfast_eur); keys such as
  delay_min and duration_min are in minutes ("running 12 minutes late"), while days_min stays a minimum.

### Not fixed

- "Adding breakfast each morning (€16 per day) brings the total to €474": a two-step sum worked out without
  the calculator is still reported as not in the tool results. Accepting it needs a count ("three nights")
  taken from the question's words or from the answer's own products, and both let invented RAGTruth
  numbers through as "worked out", so they were dropped.
- "each costing €14" is still taken as worked out ("each"), so a wrong price there is missed.

### Measured

On the third held-out set (39 answers by gpt-oss-120b and gpt-oss-20b, labelled by hand before traceground
was run; eval/results/review_heldout3_2026-11-21.md): false alarms on 7 of 34 correct answers (0.1.1: 9),
2 of 3 wrong answers caught (0.1.1: the same), and 162 of 199 planted errors caught, a value of another
field 28 of 56 (50%; 0.1.1: 40%). Five of the seven false alarms are arithmetic the answer does itself
("€47 less", "a decline of 0.6 percentage points", "€39 × 3 + €25").

### Added (repository)

- A third held-out set for the evaluation, `--set heldout3`: 20 questions on five new tools (a gym with
  classes and reviews, flight times, flats to rent, a recipe with reviews, a company report), its two runs,
  the scores and the hand review.
- The demo on the Space installs traceground 0.1.2.

## 0.1.1

Fixes for the 7 false alarms found by hand among traceground's high findings on the RAGTruth test split
(eval/results/ragtruth_review_2026-11-18.md), and for 7 more like them on the train split. Since the test
split was used to find them, it no longer measures 0.1.1 on unseen answers; a second held-out set,
written after these changes and before any model answered it, does (eval/questions_heldout2.json). On the
dev and held-out evaluations, the planted errors and the train split, nothing else changed: no finding on
a marked span was lost.

### Fixed

- Times written with one-digit minutes, as Yelp data writes them ("11:0 PM" for 23:0), are read as times.
- A number glued to a unit after a thousands separator or a decimal point is no longer cut short: "29,200km"
  and "$81.6m" are not read as 29 and 81 (they are left unchecked, as "5km" already was), and a source's
  "12.7cm" now supports an answer's "12.7 cm".
- The answer giving its own length is found further from "summary" ("Here is a summary of the news article
  about ... within 83 words").
- Quotes: asterisks are ignored like other punctuation, so a censored word written another way ("s\*\*" for
  "s---") matches; a quote one letter off from the source, in a word of five letters or more and not in a
  digit ("in itself" for "in its self"), is reported as changed slightly (low), as one misspelt word was.
- Self-contradiction: words about the sources ("Based on the given passages") no longer count as shared
  topic words, so "the side effects are not mentioned" is not contradicted by a sentence on the benefits.
- Value-to-field: a number equal to the length of a list named just before it ("Number of reviews: 3") is a
  count; and a number said of one star field that another field holds, where one is a field of a list's
  items and the other is not ("gave the business a 5-star rating" for one review's 5 stars), is not reported,
  since the wording does not tell which is meant.
- "The closest values they give" offers only values of the same kind: a year for a year, a day of a month for
  a day, never a part of a date or time stamp ("03" of "17:03:39"), and not a price for a year.

### Measured

On the second held-out set (40 answers by gpt-oss-120b and gpt-oss-20b, labelled by hand before traceground
was run; eval/results/review_heldout2_2026-11-20.md): false alarms on 5 of 34 correct answers (0.1.0: 6),
1 of 3 wrong answers caught, and 115 of 140 planted errors caught, a value of another field only 10 of 32.
Three of the false alarms have one cause, a rating said in stars ("4.3 stars") tied to the reviews' stars.

### Added (repository)

- A second held-out set for the evaluation, `--set heldout2`: 20 questions on five new tools (restaurants
  with reviews, events, trains, hotels, news articles), its two runs, the scores and the hand review.
- The demo on the Space installs traceground 0.1.1.

### Changed (repository, since 0.1.0)

- The demo is online as a Hugging Face Space, https://huggingface.co/spaces/animesh1986/traceground, which
  installs traceground 0.1.0 from PyPI and is also an MCP server. On the Space, the page says that what is
  pasted is checked on Hugging Face's server (locally it still says nothing leaves the computer), and the
  report files for the download buttons are deleted after an hour.
- The README links to a write-up on the Hugging Face blog, with real examples and the RAGTruth measurement:
  https://huggingface.co/blog/animesh1986/traceground-what-a-model-free-check-catches-in-rea
- `space/mcp_check.py` finds the tool under the name Gradio gives it on a Space
  (`traceground_traceground_check`); it used to look only for `traceground_check` and failed there.

## 0.1.0 (first release)

The first version published on PyPI. Its checks are those of 0.1.0.dev12 below, unchanged; the version
number, the README and the demo's requirements are what changed.

## 0.1.0.dev12 (not published)

Rules found by measuring on the RAGTruth train split (eval/ragtruth.py); each removes a kind of false
alarm or makes a finding more precise. The dev and held-out evaluations and the survey give the same
numbers as with 0.1.0.dev11.

### Added

- Clock times: "2:30 pm" is checked against the times in the evidence, which may be in 24-hour form
  ("14:30", or opening hours such as "11:0-2:30", which close at 2:30 at night, so "2:30 pm" is reported).
- A conversion in brackets, "400°F (200°C)" or "5 km (3.1 miles)", is reported as minor (worked out in
  the answer) when it is right (within 3%, or 6 degrees); a wrong one is reported as unsupported.
- The day of a date written with an ordinal ("April 19th", "the 19th of April") is checked; other
  ordinals ("1st place") are not.
- Quotes: a quote that differs from the source only in small words (a, the, and, of, my, those ...),
  punctuation, the spelling of one word or singular and plural is reported as minor ("The quote differs
  slightly from S1"), with a new count, quotes_changed_slightly. A changed word that changes the meaning
  ("can" for "cannot") is still reported.
- `eval/ragtruth.py` (repository only): measures traceground on RAGTruth. The data is downloaded by
  the user into eval/data/ (gitignored); the results hold numbers and ids only. Test split, measured once
  with this version: 7 of 172 high findings were false alarms by hand review; 85 of the 306 marked spans
  that contain a digit were flagged (eval/README.md).

### Changed (repository only)

- Demo: a verdict banner; the answer with each finding marked and numbered, a legend of only the kinds
  that occur, and the sentences with no number or quote in grey (with how many were checked: claims in
  words are not); each finding as a card with its severity and "Show the evidence", which opens the source
  or tool result with the value marked; "Use this check in your code" (the Python that gives the same
  report); the report as JSON or Markdown to download. The answer box comes first, and the outputs appear
  after the first check. Labels use the words of the summary ("quote not found", "value attached to the
  wrong field").
- Demo: five real examples, unedited chats from the evaluation (gpt-oss-120b and gpt-oss-20b on held-out
  questions): a correct answer with a sentence that is not checked, a departure time no tool gave, US
  dollars reported as euros, a growth rate worked out wrong (14.4% for 14.2%), and true numbers from the
  model's own knowledge. The made-up currency example they replace is gone. Markdown bold marks (**) are
  not shown on the marked answer.
- Demo as an API and an MCP tool: one endpoint, `traceground_check` (answer, sources, tool calls or a
  whole chat, question; returns the report as JSON). `python space/app.py` starts the MCP server too when
  gradio[mcp] is installed (http://127.0.0.1:7860/gradio_api/mcp/); `space/mcp_check.py` connects to it
  as an MCP client and checks two answers. The page's own endpoint is no longer public.

### Fixed

- Not checked any more: the answer counting its own length ("in 150 words", "a 98-word summary"), a
  rating scale ("out of 5", "4/5"), "24/7", labels such as "Passage 2" and "Review 3".
- How many items a list in a tool result has counts as given ("based on 3 reviews" for a list of three
  reviews), and is not read as a field value; years in date strings are not field values either.
- Value-to-field: a number that is part of a name or an address in a result ("4 Eggs & Pizza", "223
  Anacapa St") is not a field value; after "is", a word inside a phrase that starts with a preposition
  ("the rating ... according to customer reviews is 3.5") does not name the field; a more specific
  field named next to the number ("one review gave it 1 star": review_stars) is the one meant.
- Quotes: HTML entities (&amp;) and JSON escapes (\") are ignored; text between two quotations is not a
  quote; example text ('a subject line such as "..."') and the question restated are not quotes.
- Self-contradiction: "Passage 3 does not mention X" followed by X from another passage is not a
  contradiction; a question or a heading ("follow these steps:") does not count as giving the thing.

## 0.1.0.dev11 (not published)

### Added

- `check_messages()` also reads Anthropic Messages API chats (tool_use and tool_result blocks, is_error)
  and LangChain messages (the objects, or the dicts of messages_to_dict; a ToolMessage with status
  "error" is a failed call). No new dependency: the formats are read as they are.

### Fixed

- The summary counted a number twice when a quote or a value-to-field finding replaced the number
  finding ("1 number not supported; 1 value attached to the wrong field" for one finding).
- A changed quote whose nearest wording is far off (similarity 0.4 to 0.6, three words or more in
  common) now shows that wording ("says it differently: ...") instead of "nothing in them is close".

### Changed (repository only)

- Demo: one form with optional sources and optional tool calls (or a chat), so an agent that uses both
  can be checked; one endpoint, check. A "documents and a tool together" example; a how-to section; a
  currency sign or quote marks next to a finding are marked with it; the label "wrong value for its
  field"; a wider Severity column.

## 0.1.0.dev10 (not published)

### Added (repository only)

- `space/`: a Gradio demo (Gradio 6.32), run locally with `python space/app.py`. Two tabs: an answer with
  sources, and an answer with tool calls or a chat. Marks each finding on the answer, lists the findings,
  and shows the full JSON report. Two named endpoints, check_sources and check_trace. Made-up examples,
  one per check. Not published.

### Fixed

- Argument check: when a question's words fit two arguments, the one they name best is reported ("5-year"
  is years=3, not annual_rate, although "annual" means yearly).

## 0.1.0.dev9 (not published)

### Fixed (found on the held-out set; from here on, held-out numbers are no longer blind)

- Numbers: a duration in two units whose total is a source value ("535 minutes, 8 hours 55 minutes").
- Numbers and value-to-field: a scale in a key name (revenue_musd = 1840.5 supports "$1.84 billion").
- Value-to-field: the right value in another currency with no converting call is reported ("€221.4
  million" for net_income_musd), instead of passing as "another unit".
- Value-to-field: unit words inside keys (co2_ppm, pressure_hpa, kcal) no longer name a field on their
  own ("typical levels of 400-600 ppm" is a number from outside the tools, not a wrong co2_ppm).
- Value-to-field: years ("in 2024", or a year the calls give) and numbers followed by a comparative
  ("3.3 hPa higher", "7 °C warmer") are not compared with fields; result fields named year, date or
  timestamp are not compared with numbers ("year-over-year").

## 0.1.0.dev8 (not published)

### Changed: value-to-field finds more wrong fields (developed on the dev set only)

- A lone word that only one multi-word field name has binds the number ("€789.52 in interest" for
  total_interest); measure nouns ("years", "hours") and words several fields share ("total") do not.
- The subject of "... is N" binds N ("The total interest you'll pay on the loan is $3,034.15").
- The two ends of a range bind to a low/high or min/max pair ("between $69.80 and $72.90", "6-10 days").
- Time units name fields too ("249 hours" against battery_hours), like kg and $ in dev7.
- "min" and "max" next to a time noun in a key mean minimum and maximum (days_min), not minutes.
- Words ending in -ed are stemmed ("converted_amount" matches "converts"; "interest_earned", "earn").
- "more points (31)": a bracket that opens on the number no longer hides the field before it.
- Not compared: a value another call worked out from the field (a calculator given price_usd), and a
  number whose clause says it is worked out ("the difference in monthly payment is $166.03").
- Argument check: a percentage is not taken for an argument whose name has no rate word ("4%
  compounded" is not compounds_per_year).

### Added (repository only)

- A held-out set: `eval/questions_heldout.json` (20 questions) and seven new tools in `eval/tools.py`
  (flights, invoices, company figures, nutrition, sensors, shipping, cities). `--set heldout` in
  run_eval.py, score.py and mutate.py; runs go to `eval/runs/heldout/`.
- mutate.py leaves numbers inside dates alone (changing 2026-11-16 is not a wrong field value).

## 0.1.0.dev7 (not published)

### Changed (found with errors planted in the real answers; see eval/results/review_2026-11-17.md)

- Numbers: a value computed from numbers the answer states is accepted only when its sentence says so
  ("total", "together", "extra", "warmer" ... for sums and differences; "each", "per", "times" for a
  count from the question). Products and ratios of two stated numbers are no longer tried. Before,
  chance sums hid errors: a date "2026-11-61" passed as 27 + 34.
- Numbers: a percentage is not supported by a bare fraction below 1 ("0.075%" by annual_rate 0.075),
  unless the evidence writes it as a percentage or under a key such as change_pct. Worked-out
  percentages are compared as fractions ("0.15% of 240 is 36" is reported).
- Value-to-field: a unit names a field when the results have only one field with that unit ("weighs
  249 kg" against weight_kg); it is reported when the value is another field of the same call.

### Added (repository only)

- `eval/mutate.py`: plants five kinds of grounding error in the real answers that are correct by hand
  and counts how many traceground reports; `eval/hand_labels.json` lists the answers found wrong.

## 0.1.0.dev6 (not published)

### Fixed (from the second real-answer run, Groq openai/gpt-oss-20b, 2026-11-17: 4 false alarms on 44 correct answers, now 0)

- Value-to-field: "on" also ends the search for a field name ("the monthly payment on a $20,000 loan").
- Numbers: a thin, narrow no-break or no-break space between groups of three digits is a thousands
  separator ("40 983.61"); a plain space is not.
- Numbers: a source number times or divided by a whole count from the question ("3 lamps" at 39.9 is
  119.70) is a minor finding, "worked out in the answer, not by a tool", instead of an unsupported
  number. New stat `numbers_computed_in_answer`.

### Added (repository only)

- Six gpt-oss-20b answers in `tests/data/real_answers_2026-11-17.json`, with wrong-number versions that
  must still be caught.

## 0.1.0.dev5 (not published)

### Fixed (from the first real-answer run, Groq openai/gpt-oss-120b, 2026-11-17: 3 false alarms on 43 correct answers, now 0)

- Value-to-field: a preposition before the number ("for", "from", "per", ...) ends the search for a
  field name, so "the monthly payment for a $30,000 loan" no longer ties 30,000 to monthly_payment.
- Value-to-field: a number written in another unit of the same kind as the field's unit suffix
  ("91.4 °F" for high_c, "€165" for price_usd) is not compared with that field.
- Numbers: a number the answer computes from numbers it states and the evidence supports is accepted
  (sum, difference, product, ratio, a stated number times a question number, the sum of all), at the
  precision it is written in. Wrong arithmetic is still reported. New stat `numbers_derived`.

### Added (repository only)

- `tests/test_real_answers.py` and `tests/data/real_answers_2026-11-17.json`: seven real answers checked
  by hand, with wrong-number versions that must still be caught.


### Added (repository only, 0.1.0.dev4)

- `eval/`: the real-answer evaluation. Deterministic local tools, 44 questions with the calls and values
  a correct answer needs, a standard-library client for OpenAI-compatible endpoints (Groq, Hugging Face,
  Gemini; OpenAI only with ALLOW_OPENAI=1) with a request cap, an agent loop that records each chat, and
  a scorer that labels answers and lists every disagreement with traceground for review by hand.

### Added

- Failed calls (`toolchecks.py`): a failed call that was not called again successfully, nor replaced by
  another tool called about the same thing, and that the answer reports as if it had worked.
- Tools never called: claims of a web search, of running code, of a database query, or of using a named
  tool, with no such call in the trace.
- Thinking aloud (`selftalk.py`, ported from the Quantum Information Agent): "Wait, let me check:",
  "Let me report the tool's numbers:", retractions, "X? No -"; quoted text and ordinary openers are not
  flagged. Deleting a self-check is offered as a certain fix.
- Self-contradiction (ported from "Ask Your Quantum Physics Research Papers"): "the sources do not say
  X" followed by X from the sources.
- `check_answer(..., check_wording=True)`, `--no-wording`. Thinking aloud is a problem even without
  evidence.

## 0.1.0.dev3

### Added

- Tool traces (`traces.py`): a list of `{name, args, result}` (other common key names too) or
  OpenAI-style chat messages; failed calls recognised; `check_answer(..., trace=...)` and
  `check_messages(messages)`; the command line's `--trace FILE`. Tool results and arguments are
  evidence for the number and quote checks.
- Value-to-field binding (`binding.py`): a number attached to a field name ("concurrence = 0.7",
  "7 rebounds", "4% chance of rain") must be the value a tool result gives for that field;
  `field_synonyms` adds names.
- Argument binding: a question value that no call used while a call used the same digits shifted by a
  power of ten; a question value whose neighbouring word names an argument called with another value;
  two values swapped between two calls.
- The survey gives traceground the trace cases as traces.

## 0.1.0.dev2

### Added

- The quote check: quotations of three words or more must occur in the source their sentence cites, or
  in any source; ellipses and [editorial insertions] allowed; the closest real wording, or the source
  the quote is really in, is reported. Titles, quotes in code and single-quoted text are not checked.
- `citations.py`: which sources a sentence's markers name ([S1], [doc2], [report.txt], [2]). A sentence
  that is only markers ("... night. [S1]") belongs to the sentence before.
- `check_answer(..., check_quotes=True, min_quote_words=3)`; summaries name what was checked and found.

### Fixed

- A percentage read as a fraction (70% as 0.70) is no longer offered "1" as its closest value.
- The source id "question" is refused for every shape of sources, as it names the question.

## 0.1.0.dev1

### Added

- `check_answer(answer, sources, question)` and the `Result` / `Finding` model (verdict, findings with
  span, sentence, plain message, evidence and suggestion; `to_dict`, `to_json`, `to_text`).
- The number check over plain sources: rounding to the precision written, thousands separators
  (Indian grouping too), scientific notation, scale words, percent and fraction, approximate round
  numbers, number words and fractions in the evidence; citation markers, reference labels, list
  numbers, cited years, URLs, e-mail addresses, code, digits glued to words and plain integers 0 to 10
  are not checked. A number cut short (1.97 for
  1.9799) is a minor finding with the certain fix.
- `textnorm`, ported from "Ask Your Quantum Physics Research Papers" and generalized.
- The command line: `traceground --answer FILE --sources FILE ... [--question FILE] [--json]`, with exit
  codes 0 ok, 1 problems, 2 usage error, 3 unsure.
- The survey runs traceground too, and never overwrites an earlier run's files.

## [0.0.1]

### Added

- The package skeleton: `pyproject.toml` (src layout, no dependencies), the `traceground` command with
  `--version`, smoke tests, and CI on Python 3.10 to 3.14 (Linux) and 3.11 and 3.14 (Windows).
- Publishing to TestPyPI and PyPI with Trusted Publishing.
- `survey/` (repository only, not in the package): the Phase-0 survey of existing checkers on 20 cases.
