# Hand review of the third held-out set, 2026-11-21

Runs: `runs/heldout3/2026-11-21_groq_openai-gpt-oss-120b.jsonl` and
`runs/heldout3/2026-11-21_groq_openai-gpt-oss-20b.jsonl` (Groq, 20 questions each). Questions:
`questions_heldout3.json`, written on 2026-11-21 after the 0.1.2 changes and before any model answered. The
0.1.2 code was frozen before the runs and not changed after.

gpt-oss-20b gave no answer to m13: Groq rejected its tool call (HTTP 400, a tool named
`calculator<|channel|>commentary`). It was not retried, so 39 answers are counted.

Every answer was read in full against its tool results and labelled by hand before traceground was run on
it. traceground 0.1.2 was then run once (`score_heldout3_2026-11-21.md`, `mutations_heldout3_2026-11-21.md`),
and 0.1.1 on the same answers for comparison.

## Result, confirmed by hand

| | gpt-oss-120b | gpt-oss-20b | both | 0.1.1, both |
|---|---|---|---|---|
| Answers | 20 | 19 | 39 | 39 |
| Correct | 18 | 16 | 34 | 34 |
| False alarms on correct answers | 4 (m02, m08, m13, m14) | 3 (m08, m19, m20) | 7 of 34 | 9 of 34 |
| Wrong | 1 (m05) | 2 (m02, m05) | 3 | 3 |
| Wrong and caught | 0 of 1 | 2 of 2 | 2 of 3 | 2 of 3 |
| Ambiguous (the data does not say) | 1 (m15) | 1 (m15) | 2, both flagged | 2, both flagged |

The two false alarms 0.1.2 no longer raises are 20b m01 ("a rating of 4.2 stars") and 20b m16 ("an overall
rating of 4.7 stars"): the fix for a rating said in stars, made on the second held-out set, held here.

## Each answer that is not plainly correct, or was flagged

* **20b m02, wrong, caught.** "€147.00 in total, which includes €39.00 per month for three months (€117.00)
  plus a €25.00 joining fee": 117 + 25 = 142. traceground reports 147.00 as not in the tool results (and also
  117.00, which is right: 39 × 3 worked out without the calculator).
* **20b m05, wrong, caught.** Called `get_event` twice for the class (both failed), then guessed "most spin
  sessions run for about an hour. So it would normally finish around 19:00"; `get_gym` gives 45 minutes, so
  18:45. traceground reports 19:00 as not a time in the tool results, and the two failed calls.
* **120b m05, wrong, not flagged: out of scope.** Calls no tool and says it has no data on class schedules;
  `get_gym` has them. No number or quote to check.
* **m08, both models, correct, false alarm.** "€47 more expensive" (120b) and "it's €47 less" (20b): 189 −
  142, worked out in the answer. Neither "more expensive than" nor "less" is among the words that say a
  number is worked out.
* **20b m19, correct, false alarm.** "a decline of 0.6 percentage points": 7.1 − 6.5; "decline" is not
  among those words either.
* **120b m02, correct, false alarm.** "€142 (€39 × 3 months + €25 joining fee)": the answer shows its
  working, but as a product plus a sum, which the rule for shown products does not cover.
* **20b m20, correct, false alarm.** "operating profit was about €273 000": 6.5% of €4.2 million, worked
  out without the calculator. (120b used the calculator for the same number and is not flagged.)
* **120b m13, correct, false alarm.** "The rent is about €21.32 per square metre": the calculator gave
  21.323529 for 1450/68, but "rent is about €21.32" is compared with rent_eur (1450). The rule that a value
  another call worked out from the field is not the field's does not read the calculator's expression.
* **120b m14, correct, false alarm.** "(20 minutes prep + 35 minutes cook)": 35 is tied to prep_min, the
  word before it, rather than cook_min, the word after it. 0.1.1 reports it too.
* **m15, both models, ambiguous, flagged.** The recipe's `calories` (540) does not say whether it is per
  serving or for the dish. 120b: "€2.45 per serving" (calculator) is compared with `servings` (4), a false
  alarm in itself, and "roughly 540 calories per serving" assumes per serving. 20b: "€9.80 ÷ 4 ≈ €2.45" and
  "540 kcal ÷ 4 ≈ 135 kcal" are reported as not in the tool results (a shown division is not covered).
* **120b m20 and 20b m20.** "profit ... €273,000 (6.5 % of €4.2 million revenue)" is the operating profit,
  said how; labelled correct, with "profit" a loose word for it.

## Planted errors

| Kind | 0.1.2 planted | 0.1.2 caught | 0.1.1 planted | 0.1.1 caught |
|---|---|---|---|---|
| digits swapped | 57 | 55 (96%) | 54 | 52 (96%) |
| last digit off by one | 67 | 65 (97%) | 64 | 62 (97%) |
| value of another field | 56 | 28 (50%) | 50 | 20 (40%) |
| two values swapped | 9 | 4 (44%) | 9 | 4 (44%) |
| fraction as percent | 10 | 10 (100%) | 10 | 10 (100%) |
| all | 199 | 162 (81%) | 187 | 148 (79%) |

The versions plant into different answers (an answer traceground flags is not used), so the counts differ.
Most missed values of another field are in answers about two flats at once ("flat B-12 is roughly 1180 km
from the metro"): with metro_km in two calls, the field named near the number is not one field, so nothing
is compared. All misses are listed in `mutations_heldout3_2026-11-21.md`.

## What this says

On tools it was not developed on, 0.1.2 raised false alarms on 7 of 34 correct answers (21%; 0.1.1: 9), caught
2 of 3 wrong answers (the third had nothing to check), and caught a planted value of another field 50% of the
time (0.1.1: 40%). Most remaining false alarms are arithmetic the answer does itself in words the rules do
not know ("€47 less", "a decline of 0.6 percentage points") or in a shown working the rules do not cover
("€39 × 3 + €25", "€9.80 ÷ 4"). This set has now been read, so changes made for what it shows need another
fresh set.
