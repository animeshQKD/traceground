# Hand review of the second held-out set, 2026-11-20

Runs: `runs/heldout2/2026-11-20_groq_openai-gpt-oss-120b.jsonl` and
`runs/heldout2/2026-11-20_groq_openai-gpt-oss-20b.jsonl` (Groq, 20 questions each, all answered).
Questions: `questions_heldout2.json`, written on 2026-11-20 after the 0.1.1 changes and before any model
answered. The 0.1.1 code was frozen before the runs and not changed after.

Every answer was read in full against its tool results and labelled by hand before traceground was run on
it. traceground 0.1.1 was then run once (`score_heldout2_2026-11-20.md`, `mutations_heldout2_2026-11-20.md`).

## Result, confirmed by hand

| | gpt-oss-120b | gpt-oss-20b | both |
|---|---|---|---|
| Answers | 20 | 20 | 40 |
| Correct | 18 | 16 | 34 |
| False alarms on correct answers | 2 (g01, g11) | 3 (g01, g04, g19) | 5 of 34 |
| Wrong | 1 (g02) | 2 (g11, g17) | 3 |
| Wrong and caught | 0 of 1 | 1 of 2 (g11) | 1 of 3 |
| Incomplete (nothing false) | 1 (g10) | 1 (g10) | 2, not flagged |
| No answer, said plainly | 0 | 1 (g02) | 1, not flagged |

traceground 0.1.0 on the same answers: the same, plus one more false alarm (20b g03, a quote with
`**bold**` inside it), so 6 of 34. Planted errors: 115 of 140 caught with either version.

## Each answer that is not plainly correct, or was flagged

* **g01, both models, correct, false alarm.** "an overall rating of 4.3 stars". 4.3 is `rating`; the word
  "stars" tied the number to the reviews' `stars` field (5, 4, 3). A limit of the field matching: the field
  named by "rating" before the number should win.
* **20b g04, correct, false alarm.** "Harbor Noodle House (3.9 stars)": the same cause.
* **120b g11, correct, false alarm.** "RX-12 takes about 1 hour 52 minutes (7:00 → 8:52) while RX-30 takes
  about 2 hours 11 minutes ... faster by roughly 19 minutes". 19 is 2:11 − 1:52; a difference of two times
  stated in the answer is not recognised as computed.
* **20b g19, correct, false alarm.** "€426 for the rooms (3 × €142) ... brings the total to €474". The model
  did the arithmetic without the calculator: 426 and 474 are reported as not in the tool results, and
  "rooms" tied 426 and 3 to `rooms_free` (5).
* **20b g11, wrong, caught.** "RX-12 is faster ... The difference is 2 hours 49 minutes": it compares the
  arrival times (11:41 − 8:52); by journey time RX-12 is faster by 19 minutes. traceground reports 49 as
  not in the tool results.
* **120b g02, wrong, not flagged: out of scope.** Calls no tool and says it has no tool for opening hours;
  `get_restaurant` gives them. There is no number or quote to check.
* **20b g17, wrong, not flagged: out of scope.** Calls no tool and says it has no tool for the distances;
  `get_hotel` gives 0.8 km and 13.5 km. The same: nothing to check.
* **g10, both models, incomplete.** Gives the 6 stops but not the platform (11). Nothing false; an omission
  is not something traceground checks.
* **20b g02, no answer.** Called `get_event` for the restaurant, which failed, and said plainly that it has
  no opening times. Correctly not flagged.
* **20b g12, correct.** One loose phrase in words: "after fourteen months of flood repairs" (the source says
  it reopened fourteen months after the flood closed it). Not a number or a quote.

## Planted errors

| Kind | Planted | Caught |
|---|---|---|
| digits swapped | 46 | 46 (100%) |
| last digit off by one | 56 | 55 (98%) |
| value of another field | 32 | 10 (31%) |
| two values swapped | 6 | 4 (67%) |
| all | 140 | 115 (82%) |

A value of another field is caught far less often here than on the dev set (75%) and the first held-out
set (60%). About half the misses use a verb or a unit rather than the field's name: "A night ... costs
€16" for the breakfast price (`rate_eur` 142, `breakfast_eur` 16), "running 4 minutes late" for the
platform number, "rated higher (3 vs 3.9)" for the review count. The others name the field and are still
missed: "guest rating of 142", "about 142 km from the nearest train station", "an extra €142" for
breakfast. All 25 misses are listed in `mutations_heldout2_2026-11-20.md`.

## What this says

0.1.1 is not worse than 0.1.0 anywhere this was measured, and fixes one false alarm here. But on tools it
was not developed on, it raised false alarms on 5 of 34 correct answers (15%), three of them from one
cause (a rating said in stars), and it caught a planted value of another field only 31% of the time.
These are the known limits for 0.1.2; since this set has now been read, 0.1.2 needs another fresh set.
