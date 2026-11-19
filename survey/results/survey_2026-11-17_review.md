# Survey 2026-11-17: hand review of every flag

Run: `results/survey_2026-11-17.json` (citation markers taken out), Windows, Python 3.11.18, GroundLens 6.0.5,
LongTracer 0.3.1, RAGGround 0.2.2, halluguard 0.3.1. Reviewed 2026-11-17.

## How a flag is judged

* **right**: the reason names the wrong value or span (GroundLens n1), or the tool flags the one false
  sentence and passes the matching correct answer (its "twin"), so the flag tells the two apart.
* **unclear**: a sentence-level flag with no reason, from a tool that also flags the correct twin. Such a
  flag cannot tell the error from the correct answer.
* **wrong**: the reason is not the error (GroundLens v2: "34 minutes"), or the flagged content is in
  fact supported (q2 with markers taken out: the quote is in S2, so only the citation was wrong, and
  that citation was removed).

Twins used: n1 ↔ n3 (finance numbers); v1, a1 ↔ a4, fp1 (physics); a2 ↔ v4 (the same loan trace);
f1 ↔ f2 (weather); q1, q2 ↔ q3 (quotes). a3, t1 and c1 have no twin, so a sentence-level flag counts as
right if the flagged sentence is the false one.

## Errors (13): flags by verdict

| Case | GroundLens | LongTracer | RAGGround | halluguard |
|---|---|---|---|---|
| n1 number | **right** (42.1, nearest 41.2) | missed | unclear (also flags n3) | unclear (also flags n3) |
| v1 value-to-field | missed | missed | unclear (also flags a4, fp1) | unclear (also flags a4, fp1) |
| v2 value-to-field | wrong ("34 minutes has no source value of the same dimension") | missed | missed | missed |
| v3 value-to-field | wrong (every number lacks a unit in the JSON; the same reason flags the correct f2) | missed | missed | missed |
| a1 argument binding | missed | missed | unclear (also flags a4) | unclear (also flags a4) |
| a2 argument binding | wrong (12,250 vs 12250.43: a rounding complaint) | missed | unclear (also flags v4, its twin) | missed |
| a3 swapped arguments | missed | **right** (the sentence) | **right** (each half CONTRADICTED) | **right** (the sentence) |
| f1 failed call | **right** ("no numeral in any source") | missed | **right** (passes f2) | **right** (passes f2) |
| t1 tool never called | missed | missed | unclear (no twin; the content is supported, the fault is "I searched the web") | unclear (as RAGGround) |
| q1 quote changed | missed | missed | **right** (passes q3) | missed |
| q2 quote, wrong passage | missed | missed | wrong (quote is in S2; marker removed) | wrong (as RAGGround) |
| s1 self-talk | missed | wrong (calls correct numbers unsupported) | missed | wrong (as LongTracer) |
| c1 self-contradiction | missed | **right** (flags "do not say") | **right** (CONTRADICTED) | **right** |
| **right / unclear / wrong / missed** | **2 / 0 / 3 / 8** | **2 / 0 / 1 / 10** | **4 / 5 / 1 / 3** | **3 / 4 / 2 / 4** |

## Correct answers (7): false alarms

| Case | GroundLens | LongTracer | RAGGround | halluguard |
|---|---|---|---|---|
| n2 rounding (23.7 → "about 24 °C") | false alarm ("contradicted", compared in kelvin) | ok | ok | ok |
| n3 7% ↔ 0.07, 12,250.43 ↔ 12250.43 | false alarm (7%) | ok | false alarm | false alarm |
| v4 loan, right fields | ok | ok | false alarm | ok |
| a4 "0.3 and 0.1 respectively" | ok | ok | false alarm | false alarm |
| f2 failed call redone | false alarm (no units in the JSON) | ok | ok | ok |
| q3 typographic quote marks | ok | ok | ok | ok |
| fp1 "takes a bigger toll" (true) | ok | ok | false alarm | false alarm |
| **false alarms** | **3 of 7** | **0 of 7** | **4 of 7** | **3 of 7** |

## What it shows (20 cases we wrote ourselves: direction, not a claim for the README)

* **No tool caught a value-to-field error for the right reason (v1–v3), nor an argument-binding error
  found only by comparing the question with the arguments (a1, a2).** a3 is caught because its swap is
  visible inside one passage (amount and result together). The trace checks are the gap.
* No tool checks that a quote is in the passage it cites (q2), recognises self-talk (s1), or a claim
  about a tool that was never called (t1, unclear at best).
* GroundLens is the only one that names the wrong value (n1, with the nearest source value), in about
  10 ms. On tool traces it reads JSON values as unitless (`"high_c": 9`), so every value with a unit in
  the answer is "unsupported" (v3, f2), and it flagged the rounding in n2 and a2.
* The NLI tools flag sentences without saying why, and flag the true physics and finance twins as
  often as the false ones (v1/a1 vs a4/fp1, a2 vs v4).
* LongTracer raised no false alarm but passed 42.1 for 41.2 (n1); its optional number model (`[slm]`)
  was not installed.

## Before anything here is stated in public

* Rerun GroundLens with a rounding policy (`rounding: within_last_digit`) and LongTracer with `[slm]`,
  so neither is judged on a setting it offers.
* Every error case gets a correct twin (t1, a3 and c1 have none), so a flag can always be told apart
  from a reflex.
* Our own checker must be run through the same harness on the same cases, and on cases we did not
  write (Phase 5).

## Timing (median per check, first check left out)

| Tool | Run 1 | Run 2 (models cached) | Load time, run 2 |
|---|---|---|---|
| GroundLens | 12.84 ms | 9.95 ms | 0.04 s |
| LongTracer | 135.61 ms | 101.36 ms | 12.15 s |
| RAGGround | 609.64 ms | 424.31 ms | 0.85 s |
| halluguard | 365.23 ms | 195.27 ms | 3.79 s |

Run 1's load times (60.76 s, 65.3 s) include the model downloads. The medians change by up to 47%
between runs (halluguard), so only the order of magnitude is meaningful. halluguard's time includes
building its index for each case, which the harness does per case.
