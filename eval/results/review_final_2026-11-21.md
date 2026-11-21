# Hand review of the final test set, 2026-11-21

Runs: `runs/final/2026-11-21_groq_openai-gpt-oss-120b.jsonl` and
`runs/final/2026-11-21_groq_openai-gpt-oss-20b.jsonl` (Groq, 40 questions each). Questions:
`questions_final.json` (SHA-256 `d826ff32191a7c8f96865fd96def1d5f99ffd3bf108d0745f704085f5bf2abe5`), written on
2026-11-21 after the 0.2.0 code was frozen (SHA-256 of `src/traceground/*.py`, hashed together:
`d590783de06b337b35359d76a11decabd46701b4d04a57fa61050495f0df1452`) and before any model answered.

Fixed before the runs: each command is run once; a question that ends in an error is asked once more, and
what is still an error counts as no answer; and whatever this test shows is published as it is, with no
change to the code after it. gpt-oss-20b's z27 ended in an error both times (Groq rejected its tool call:
`calculator<|channel|>commentary`), so 79 answers are counted.

Every answer was read in full against its tool results and labelled by hand before traceground was run on
it (the labels' SHA-256 was given in the chat before the run). traceground 0.2.0 was then run once
(`score_final_2026-11-21.md`, `mutations_final_2026-11-21.md`), and 0.1.2 on the same answers for comparison.

Labels: **correct**; **wrong** (anything false, including an answer that calls no tool and then says no tool
or data exists); **no answer** (called a tool that failed, and said plainly it has no answer).

## Result, confirmed by hand

| | gpt-oss-120b | gpt-oss-20b | both | 0.1.2, both |
|---|---|---|---|---|
| Answers | 40 | 39 | 79 | 79 |
| Correct | 35 | 27 | 62 | 62 |
| False alarms on correct answers | 11 | 9 | **20 of 62 (32%)** | 20 of 62 |
| Wrong | 3 | 5 | 8 | 8 |
| Wrong and caught | 0 of 3 | 2 of 5 | **2 of 8** | 2 of 8 |
| No answer | 2 | 7 | 9 | 9 |
| No answer, but flagged | 0 | 1 (z03) | 1 of 9 | 1 of 9 |

This is much worse than on the earlier sets (third set: 7 of 34 false alarms with 0.1.2, 1 with 0.2.0 after
development on it). This set asks for more arithmetic (17 of 40 questions need a computed number), and most
of its false alarms are arithmetic the answer does in a form the rules do not read. 0.2.0 and 0.1.2 flag the
same 20 correct answers; 0.2.0's changes, made on the third set, did not carry over to these.

## Why the 20 correct answers were flagged

| Cause | Answers |
|---|---|
| Arithmetic the answer does itself in a form the rules do not read: a product of two stated numbers without "×" ("10 weeks at 3 hours per week, 30 hours"; "€45 each ... €90"), a count written as a word ("twice the €2.40 fare: €4.80"), a percentage off ("€21.60 after the 10% discount"), "50 km more", a sum with no cue word ("140 ... and 60 more, so 200"), a working followed by its unit ("€14 ÷ 25 GB ≈ €0.56", "22 € per month × 24 months = €528") | 15: 120b z05, z08, z09, z18, z29, z32, z35, z39; 20b z09, z14, z18, z28, z29, z32, z35 |
| A clock time plus a duration ("the 8:00 bus ... 41 minutes ... 8:41") | 2: z19, both models |
| A bug in the argument check: the question's "8:00" is read as an argument "00" ("The question asks for 00 bus on route, but get_bus_route was called with route=42") | the same 2 (z19) |
| A price compared with a percentage field ("the early-bird price ... is €408" against early_bird_pct = 15) | 2: z33, both models |
| A duration written "2 hours and 15 minutes" is not read as one, so 15 is checked alone | 1: 120b z12 |

Some answers have more than one: 120b z09 also ties "€0.20 per km" to price_per_day_eur.

## The wrong answers

* **20b z05, caught.** "€21 after the 10 % loyalty discount": 24 × 0.9 = 21.60.
* **20b z21, caught.** After `get_restaurant` failed: "Casa da Luz is a restaurant, not an event venue, so it
  doesn't sell adult or child tickets". It is a museum (€12 and €6). Reported as a failed call the answer
  reads as if it had worked.
* **120b z03, z04; 20b z04, z25, not flagged: out of scope.** Each calls no tool and says no tool or data
  exists (events, reviews, visitor numbers); the tools give them. No number or quote to check.
* **120b z34, 20b z37, not flagged: out of scope.** A misspelt name: "Dr. Inéas Moura" for Inês Moura;
  "Tom Á Reyes" for Tomás Reyes (the quote itself is exact). Names are not checked.

## The no-answer answers

Nine answers called a tool that failed (often the wrong tool: `get_restaurant` or `get_hotel` for the
museum, `get_event` for the bookshop and the concert) and said so; one more (20b z40) said the release does
not give the earlier revenue, which is true as written. One was flagged: 20b z03 ("I don't have a way to
retrieve the current event schedule") is reported as a failed call the answer reads as if it had worked,
which it does not.

## Planted errors

| Kind | 0.2.0 planted | 0.2.0 caught | 0.1.2 caught |
|---|---|---|---|
| digits swapped | 89 | 89 (100%) | 89 |
| last digit off by one | 110 | 102 (93%) | 102 |
| value of another field | 70 | 47 (67%) | 47 |
| two values swapped | 10 | 8 (80%) | 9 |
| fraction as percent | 3 | 3 (100%) | 3 |
| all | 282 | 249 (88%) | 250 (89%) |

Both versions plant into the same answers (those neither flags), so the counts compare directly.

## What this says

On tools and questions it was not developed on, traceground 0.2.0 raised false alarms on 20 of 62 correct
answers (32%), caught 2 of 8 wrong answers (the other 6 had no number or quote to check, or a misspelt
name), and caught 249 of 282 planted errors (88%). Its number check is reliable on numbers copied from the
tool results, and weak on numbers the answer works out itself: it reports them unless the answer shows
the working with ×, ÷, + or − or says it with one of the words it knows, and this set has many of them.
As fixed before the run, the code was not changed after this test.
