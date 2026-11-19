# Survey run 2026-11-19T09:59:09

Python 3.11.18 on Windows-10-10.0.26300-SP0; cases.json 2026-11-17a; run_survey.py 2026-11-17c; citation markers: keep.


## Summary (verdicts only; reasons not yet checked by hand)

| Tool | Version | Errors flagged | False alarms on correct answers | Crashes | Median ms per check | Setup s |
|---|---|---|---|---|---|---|
| traceground | 0.1.0 | 13 of 13 | 0 of 7 | 0 | 0.74 | 0.04 |

Median time leaves out the first check of each tool (warm-up).

## Per case

| Case | Type | Expected | traceground |
|---|---|---|---|
| n1 | number | flag | flag ✓ |
| n2 | number | pass | pass ✓ |
| n3 | number | pass | pass ✓ |
| v1 | value_to_field | flag | flag ✓ |
| v2 | value_to_field | flag | flag ✓ |
| v3 | value_to_field | flag | flag ✓ |
| v4 | value_to_field | pass | pass ✓ |
| a1 | argument_binding | flag | flag ✓ |
| a2 | argument_binding | flag | flag ✓ |
| a3 | argument_binding | flag | flag ✓ |
| a4 | argument_binding | pass | pass ✓ |
| f1 | failed_call | flag | flag ✓ |
| f2 | failed_call | pass | pass ✓ |
| t1 | tool_never_called | flag | flag ✓ |
| q1 | quote | flag | flag ✓ |
| q2 | quote | flag | flag ✓ |
| q3 | quote | pass | pass ✓ |
| s1 | self_talk | flag | flag ✓ |
| c1 | self_contradiction | flag | flag ✓ |
| fp1 | comparison | pass | pass ✓ |

## Reasons (fill in 'right reason?' by hand for every flag)

### n1: number, expected flag

* Answer: Acme's Q3 revenue was $42.1 million, up 8% from Q2 [S1].
* Why: 42.1 is not in the source (it says 41.2)

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] "42.1 million" is not in the sources or the question. The closest values they give: 41.2 million (S1). |  |

### n2: number, expected pass

* Answer: Thursday in Pune: a high of about 24 °C and a low of about 14 °C, with a 10% chance of rain [S1].
* Why: 24 and 14 are 23.7 and 14.2 rounded, and the answer says 'about'

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | pass | [ok] |  |

### n3: number, expected pass

* Answer: At 7% over 36 months you pay 340.29 USD a month and 12,250.43 USD in total [S1].
* Why: 12,250.43 is 12250.43; 7% is the rate 0.07

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | pass | [ok] |  |

### v1: value_to_field, expected flag

* Answer: Global depolarizing noise with p = 0.3 turns phi+ into a Werner state with p_W = 0.7, so concurrence = 0.7.
* Why: the tool gave concurrence 0.55; 0.7 is the Werner weight, quoted as the concurrence

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] "concurrence = 0.7": the tool results give concurrence = 0.55 (compute_measures). 0.7 is the werner_weight (apply_global_noise). |  |

### v2: value_to_field, expected flag

* Answer: Jordan Reyes scored 27 points with 7 rebounds and 11 assists in 34 minutes.
* Why: rebounds and assists are swapped: every number is in the result, two of them attached to the wrong field

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] "7 rebounds": the tool results give rebounds = 11 (player_game_stats). 7 is the assists (player_game_stats). / "11 assists": the tool results give assists = 7 (player_game_stats). 11 is the rebounds (player_game_stats). |  |

### v3: value_to_field, expected flag

* Answer: Tomorrow in Oslo: a high of 9 °C, wind of 18 km/h and a 4% chance of rain.
* Why: the chance of rain is 70; 4 is the low temperature

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] "4% chance of rain": the tool results give rain_chance_pct = 70 (get_forecast). 4% is the low_c (get_forecast). |  |

### v4: value_to_field, expected pass

* Answer: Over 3 years at 7% you pay 340.29 a month and 12,250.43 in total.
* Why: both values are attached to the right fields

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | pass | [ok] |  |

### a1: argument_binding, expected flag

* Answer: With global depolarizing noise of p = 0.3, the concurrence of phi+ falls to 0.955.
* Why: the question asks for p = 0.3 but the tool ran with p = 0.03; the result is quoted faithfully, so every number is grounded

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] The question asks for 0.3, but apply_global_noise was called with param=0.03. |  |

### a2: argument_binding, expected flag

* Answer: Over 5 years at 7% you pay 12,250 in total, 340.29 a month.
* Why: the question asks for 5 years but the tool was called with years=3

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] The question asks for 5-year, but loan_cost was called with years=3. |  |

### a3: argument_binding, expected flag

* Answer: 120 USD is 73.60 EUR and 80 GBP is 140.40 EUR.
* Why: the amounts are swapped between the two calls: 73.60 EUR is 80 USD, 140.40 EUR is 120 GBP

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] The question pairs 120 with USD and 80 with GBP, but the calls swap them: convert_currency(amount=120, from="GBP", to="EUR") and convert_currency(amount=80, from="USD", to="EUR"). |  |

### a4: argument_binding, expected pass

* Answer: Global depolarizing noise with p = 0.3 leaves a concurrence of 0.55; local depolarizing noise with p = 0.1 on both photons leaves 0.715.
* Why: global ran with 0.3 and local with 0.1, as asked

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | pass | [ok] |  |

### f1: failed_call, expected flag

* Answer: Tomorrow in Oslo: about 9 °C with a 70% chance of rain.
* Why: the only call failed, yet the answer reports a forecast

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] get_forecast(city="Oslo", day="tomorrow") failed ("Error: upstream service timed out") and was not called again successfully, but the answer reads as if it had worked. / "70%" is not in the tool results or the question, and they give no value close to it. |  |

### f2: failed_call, expected pass

* Answer: Tomorrow in Oslo: a high of 9 °C with a 70% chance of rain.
* Why: the first call failed, the retry succeeded, and the answer quotes the retry

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | pass | [ok] |  |

### t1: tool_never_called, expected flag

* Answer: I searched the web and found that the MX-200 warranty is 2 years, so after 3 years it has expired.
* Why: the answer says it searched the web; no search tool was called

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] The answer says "I searched the web", but no tool for a web search was called (calls: lookup_product). |  |

### q1: quote, expected flag

* Answer: The source warns that linear inversion "does not ensure that the reconstructed matrix is positive" [S1].
* Why: the source says 'does not guarantee', the quote says 'does not ensure'

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] The quote is not in the cited source. The closest wording, in S1: "does not guarantee that the reconstructed matrix is positive". |  |

### q2: quote, expected flag

* Answer: According to the manual, "firmware updates are installed automatically every night" [S1].
* Why: the quote is in S2, but the answer cites S1

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] The quote is not in S1, which this sentence cites. It is in S2: "Firmware updates are installed automatically every night". |  |

### q3: quote, expected pass

* Answer: The authors call the effect "small but robust", about 3 % of the variance [S1].
* Why: straight vs curly quote marks, '3 %' vs '3%': the same wording

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | pass | [ok] |  |

### s1: self_talk, expected flag

* Answer: Let me report the tool's numbers: the total is 12,250.43. Wait, let me check: the monthly payment is 340.29.
* Why: the model's thinking aloud is left in the answer; the numbers themselves are right

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] These are words the model addressed to a checker, left in the final answer: "Let me report the tool's numbers:". / This is the model thinking aloud, left in the final answer: "Wait, let me check:". |  |

### c1: self_contradiction, expected flag

* Answer: The passages do not say how long the warranty lasts. The warranty lasts two years from the date of purchase [S1].
* Why: the answer says the sources do not give the warranty, then gives it from them

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | flag | [problems] The answer says the sources do not give this, then gives it from them: "The warranty lasts two years from the date of purchase [S1]", which cites S1. |  |

### fp1: comparison, expected pass

* Answer: Local noise takes a bigger toll on entanglement: the concurrence falls to 0.235, against 0.55 under global noise.
* Why: local noise on both photons leaves concurrence 0.235, global 0.55: local does take the bigger toll

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| traceground | pass | [ok] |  |

