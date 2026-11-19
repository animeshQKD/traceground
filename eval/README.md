# Real-answer evaluation

How often does traceground raise a false alarm on a real model's correct answer, and how many of a
real model's errors does it catch? The 20 survey cases cannot say: we wrote them around the checks.
Here real models answer 44 everyday questions with local tools, and every answer is scored.

* `tools.py`: 9 deterministic tools (loans, compound interest, currency, units, weather, products, player
  statistics, stock quotes, a calculator). No network. Reykjavik's weather always fails; unknown
  products, cities and currencies return an error.
* `questions.json`: 44 questions, each with the calls a correct answer needs and the values it must
  state. Some are traps for known errors (0.5% passed as 0.05, values to swap, a failing tool, a request
  for a web search with no web tool).
* `run_eval.py`: a model answers the questions through the tools; each chat is saved to `runs/`.
* `score.py`: labels each answer from the known tool results, runs traceground on each chat, and writes
  `results/score_<date>.md` with the counts and, for a person to confirm, every disagreement.
* `mutate.py`: plants one grounding error at a time in the real answers that are correct by hand
  (`hand_labels.json` lists the wrong ones) and counts how many traceground reports. Writes
  `results/mutations_<date>.md`.

## Running it

Keys go in `.env` in the project folder (never in git; `.gitignore` keeps it out). The same keys as
the Quantum Information Agent work: `GROQ_API_KEY`, `GOOGLE_API_KEY`, `HF_TOKEN`; `OPENAI_API_KEY` only
with `ALLOW_OPENAI=1`.

```
cd eval
python run_eval.py --provider groq                  # free tier; openai/gpt-oss-120b
python run_eval.py --provider gemini                # free tier; gemini-3.8-flash
python run_eval.py --provider hf --max-calls 150    # your HF credits; DeepSeek V4 Flash
python score.py
python mutate.py                                    # planted errors; no network
```

Each run stops at `--max-calls` requests (default 120; a question takes about 2 to 4). Run the same
command again to continue: questions already answered that day are skipped.

## What the automatic label can and cannot see

It checks that the required values are stated and the required calls were made with the right
arguments. It does not check which name a value is attached to: an answer that swaps two values is
labelled correct, and appears in the list "flagged although labelled correct", where a person decides.
Every count in the report is confirmed by hand before it is quoted anywhere.

## Planted errors

The models may make no grounding error at all (gpt-oss-120b and gpt-oss-20b made none on these 44
questions), so a run alone cannot say how many errors traceground catches. `mutate.py` changes each
correct answer in one place, keeping the model's own wording, and checks the changed chat:

| Kind | Example |
|---|---|
| digits swapped | 892.41 -> 892.14 |
| last digit off by one | 469.70 -> 469.71 |
| value of another field | the monthly payment written as the total interest |
| two values swapped | 27 points, 11 rebounds -> 11 points, 27 rebounds |
| fraction as percent | 52.2% -> 0.522% |

A planted error is caught when a high-severity finding covers the changed text. These are errors we
planted, not errors models made, so the rates say how well each kind is detected in real wording, not
how often models make it. Every miss is listed in the report.

## The held-out set

Changes made after reading the planted-error misses look better on those same errors than they are.
`questions_heldout.json` holds 20 questions on seven other tools (flights, invoices, company figures,
nutrition, sensors, shipping, cities), written before the 0.1.0.dev8 wrong-field changes and not used
to tune them. They are the ones to quote:

```
python run_eval.py --provider groq --set heldout
python run_eval.py --provider groq --model openai/gpt-oss-20b --set heldout --max-calls 200
python score.py --set heldout
python mutate.py --set heldout
```

The same person wrote the questions and the checker, so the set is not blind to the field names; it is
blind to how the models word their answers and to which planted errors get through.

## RAGTruth: real answers marked by people

`ragtruth.py` runs traceground on [RAGTruth](https://github.com/ParticleMedia/RAGTruth) (Niu et al., ACL
2024; MIT license): answers by six models (GPT-3.5, GPT-4, Llama-2 7B/13B/70B, Mistral 7B) to three tasks,
where annotators marked every span that conflicts with the source or adds what the source does not give.
Most marked spans are claims in words, which traceground does not check; it checks numbers, quotes and
values. The data is not in this repository (the sources are news articles, web pages and Yelp data):
download it as the top of `ragtruth.py` shows, into `eval/data/ragtruth/`, which git ignores. The results
files hold numbers and RAGTruth ids only.

The rules were developed on the train split; the test split was measured once, with the code frozen
(0.1.0.dev12, 2026-11-18). Answers RAGTruth rates good; the task's instruction is passed as the question.

| Test split | QA | Summary | Data2txt |
|---|---|---|---|
| Answers | 875 | 900 | 900 |
| with a marked span | 160 | 204 | 579 |
| flagged (a high finding) | 34 | 41 | 51 |
| flagged and marked | 26 | 24 | 46 |
| marked spans with a digit, flagged | 29 of 104 | 22 of 51 | 34 of 151 |
| high findings, on a marked span | 62 of 74 | 25 of 44 | 36 of 54 |

All 49 high findings on no marked span were checked by hand (`results/ragtruth_review_2026-11-18.md`):
13 contradict the source or quote what it does not have, 6 reword a quote, 19 give a number the source does
not give at all, 7 are false alarms and 4 are unclear. So 7 of the 172 high findings (4%) were false alarms.

What this says, and what it does not:

* Most hallucinations RAGTruth marks are not numbers or quotes. traceground flags 8% to 16% of the answers
  with a marked span (by task), and 85 of the 306 marked spans that contain a digit (28%). On the train
  split, many of the missed digit spans were claims around a number ("open Monday to Sunday", "with varying
  hours") rather than the number itself.
* Of the 172 high findings, 7 were false alarms and 4 unclear; the other 161 point at a number or quote the
  source does not support (the 123 on a marked span were marked by a person and not checked again). The
  annotators did not mark all of these: counted against the marks alone, the precision would look like 59%
  to 90%.
* The first measurement of the test split, with 0.1.0.dev11 and without the instruction as the question, had
  more noise: 379 answers flagged, 230 of them with no marked span (now 126 and 30), for about the same number
  of marked digit spans flagged (83 then, 85 now). Same answers, same counts (`ragtruth.py` run with the old
  code), but that measurement was blind and this one comes after work on the train split.
