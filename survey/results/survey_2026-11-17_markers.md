# Survey run 2026-11-17T12:40:08

Python 3.11.18 on Windows-10-10.0.26300-SP0; cases.json 2026-11-17a; run_survey.py 2026-11-17a; citation markers: keep.


## Summary (verdicts only; reasons not yet checked by hand)

| Tool | Version | Errors flagged | False alarms on correct answers | Crashes | Median ms per check | Setup s |
|---|---|---|---|---|---|---|
| groundlens | 6.0.5 | 5 of 13 | 3 of 7 | 0 | 9.95 | 0.04 |
| longtracer | 0.3.1 | 3 of 13 | 0 of 7 | 0 | 101.36 | 12.15 |
| ragground | 0.2.2 | 10 of 13 | 6 of 7 | 0 | 424.31 | 0.85 |
| halluguard | 0.3.1 | 10 of 13 | 4 of 7 | 0 | 195.27 | 3.79 |

Median time leaves out the first check of each tool (warm-up).

## Per case

| Case | Type | Expected | groundlens | longtracer | ragground | halluguard |
|---|---|---|---|---|---|---|
| n1 | number | flag | flag ✓ | pass ✗ | flag ✓ | flag ✓ |
| n2 | number | pass | flag ✗ | pass ✓ | flag ✗ | pass ✓ |
| n3 | number | pass | flag ✗ | pass ✓ | flag ✗ | flag ✗ |
| v1 | value_to_field | flag | pass ✗ | pass ✗ | flag ✓ | flag ✓ |
| v2 | value_to_field | flag | flag ✓ | pass ✗ | pass ✗ | pass ✗ |
| v3 | value_to_field | flag | flag ✓ | pass ✗ | pass ✗ | pass ✗ |
| v4 | value_to_field | pass | pass ✓ | pass ✓ | flag ✗ | pass ✓ |
| a1 | argument_binding | flag | pass ✗ | pass ✗ | flag ✓ | flag ✓ |
| a2 | argument_binding | flag | flag ✓ | pass ✗ | flag ✓ | pass ✗ |
| a3 | argument_binding | flag | pass ✗ | flag ✓ | flag ✓ | flag ✓ |
| a4 | argument_binding | pass | pass ✓ | pass ✓ | flag ✗ | flag ✗ |
| f1 | failed_call | flag | flag ✓ | pass ✗ | flag ✓ | flag ✓ |
| f2 | failed_call | pass | flag ✗ | pass ✓ | pass ✓ | pass ✓ |
| t1 | tool_never_called | flag | pass ✗ | pass ✗ | flag ✓ | flag ✓ |
| q1 | quote | flag | pass ✗ | pass ✗ | flag ✓ | flag ✓ |
| q2 | quote | flag | pass ✗ | pass ✗ | flag ✓ | flag ✓ |
| q3 | quote | pass | pass ✓ | pass ✓ | flag ✗ | flag ✗ |
| s1 | self_talk | flag | pass ✗ | flag ✓ | pass ✗ | flag ✓ |
| c1 | self_contradiction | flag | pass ✗ | flag ✓ | flag ✓ | flag ✓ |
| fp1 | comparison | pass | pass ✓ | pass ✓ | flag ✗ | flag ✗ |

## Reasons (fill in 'right reason?' by hand for every flag)

### n1: number, expected flag

* Answer: Acme's Q3 revenue was $42.1 million, up 8% from Q2 [S1].
* Why: 42.1 is not in the source (it says 41.2)

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | flag | [FAIL] c4: groundlens.numeric contradicted: $42.1 million not in sources; nearest 41200000 USD in ctx-0 (relative distance 0.021) |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: Acme's Q3 revenue was $42.1 million, up 8% from Q2 [S1]. |  |
| halluguard | flag | [1 of 1 claims flagged] Acme's Q3 revenue was $42.1 million, up 8% from Q2 [S1]. (support 0.87) |  |

### n2: number, expected pass

* Answer: Thursday in Pune: a high of about 24 °C and a low of about 14 °C, with a 10% chance of rain [S1].
* Why: 24 and 14 are 23.7 and 14.2 rounded, and the answer says 'about'

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | flag | [FAIL] c4: groundlens.numeric contradicted: 24 °C not in sources; nearest 296.85 K in ctx-0 (relative distance 0.001); c6: groundlens.numeric contradicted: 14 °C not in sources; nearest 287.35 K in ctx-0 (relative distance 0.001) |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: Thursday in Pune: a high of about 24 °C and a low of about 14 °C, with a 10% chance of rain [S1]. |  |
| halluguard | pass | [0 of 1 claims flagged] |  |

### n3: number, expected pass

* Answer: At 7% over 36 months you pay 340.29 USD a month and 12,250.43 USD in total [S1].
* Why: 12,250.43 is 12250.43; 7% is the rate 0.07

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | flag | [FAIL] c1: groundlens.numeric contradicted: 7% is in no source and matches no sum, difference, ratio or change of 340.29 USD, 12,250.43 USD |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: At 7% over 36 months you pay 340.29 USD a month and 12,250.43 USD in total [S1]. |  |
| halluguard | flag | [1 of 1 claims flagged] At 7% over 36 months you pay 340.29 USD a month and 12,250.43 USD in total [S1]. (support 0.55) |  |

### v1: value_to_field, expected flag

* Answer: Global depolarizing noise with p = 0.3 turns phi+ into a Werner state with p_W = 0.7, so concurrence = 0.7.
* Why: the tool gave concurrence 0.55; 0.7 is the Werner weight, quoted as the concurrence

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: Global depolarizing noise with p = 0.3 turns phi+ into a Werner state with p_W = 0.7, so concurrence = 0.7. |  |
| halluguard | flag | [1 of 1 claims flagged] Global depolarizing noise with p = 0.3 turns phi+ into a Werner state with p_W = 0.7, so concurrence = 0.7. (support 0.72) |  |

### v2: value_to_field, expected flag

* Answer: Jordan Reyes scored 27 points with 7 rebounds and 11 assists in 34 minutes.
* Why: rebounds and assists are swapped: every number is in the result, two of them attached to the wrong field

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | flag | [REVIEW] c9: groundlens.numeric unsupported: 34 minutes has no source value of the same dimension |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | pass | [grounded=True, neural=True] |  |
| halluguard | pass | [0 of 1 claims flagged] |  |

### v3: value_to_field, expected flag

* Answer: Tomorrow in Oslo: a high of 9 °C, wind of 18 km/h and a 4% chance of rain.
* Why: the chance of rain is 70; 4 is the low temperature

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | flag | [REVIEW] c4: groundlens.numeric unsupported: 9 °C has no source value of the same dimension; c6: groundlens.numeric unsupported: 18 km has no source value of the same dimension; c8: groundlens.numeric unsupported: 4% has no source value of the same dimension |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | pass | [grounded=True, neural=True] |  |
| halluguard | pass | [0 of 1 claims flagged] |  |

### v4: value_to_field, expected pass

* Answer: Over 3 years at 7% you pay 340.29 a month and 12,250.43 in total.
* Why: both values are attached to the right fields

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: Over 3 years at 7% you pay 340.29 a month and 12,250.43 in total. |  |
| halluguard | pass | [0 of 1 claims flagged] |  |

### a1: argument_binding, expected flag

* Answer: With global depolarizing noise of p = 0.3, the concurrence of phi+ falls to 0.955.
* Why: the question asks for p = 0.3 but the tool ran with p = 0.03; the result is quoted faithfully, so every number is grounded

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: With global depolarizing noise of p = 0.3, the concurrence of phi+ falls to 0.955. |  |
| halluguard | flag | [1 of 1 claims flagged] With global depolarizing noise of p = 0.3, the concurrence of phi+ falls to 0.955. (support 0.86) |  |

### a2: argument_binding, expected flag

* Answer: Over 5 years at 7% you pay 12,250 in total, 340.29 a month.
* Why: the question asks for 5 years but the tool was called with years=3

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | flag | [FAIL] c4: groundlens.numeric contradicted: 12,250 not in sources; nearest 12250.43 in ctx-0 (relative distance 0.000) |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: Over 5 years at 7% you pay 12,250 in total, 340.29 a month. |  |
| halluguard | pass | [0 of 1 claims flagged] |  |

### a3: argument_binding, expected flag

* Answer: 120 USD is 73.60 EUR and 80 GBP is 140.40 EUR.
* Why: the amounts are swapped between the two calls: 73.60 EUR is 80 USD, 140.40 EUR is 120 GBP

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | flag | [FAIL] 0/1 claims supported, 1 hallucination(s) detected. 120 USD is 73.60 EUR and 80 GBP is 140.40 EUR. |  |
| ragground | flag | [grounded=False, neural=True] CONTRADICTED: 120 USD is 73.60 EUR / CONTRADICTED: 80 GBP is 140.40 EUR. |  |
| halluguard | flag | [1 of 1 claims flagged] 120 USD is 73.60 EUR and 80 GBP is 140.40 EUR. (support 0.82) |  |

### a4: argument_binding, expected pass

* Answer: Global depolarizing noise with p = 0.3 leaves a concurrence of 0.55; local depolarizing noise with p = 0.1 on both photons leaves 0.715.
* Why: global ran with 0.3 and local with 0.1, as asked

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] CONTRADICTED: Global depolarizing noise with p = 0.3 leaves a concurrence of 0.55 / CONTRADICTED: local depolarizing noise with p = 0.1 on both photons leaves 0.715. |  |
| halluguard | flag | [1 of 1 claims flagged] Global depolarizing noise with p = 0.3 leaves a concurrence of 0.55; local depolarizing noise with p = 0.1 on both photo (support 0.67) |  |

### f1: failed_call, expected flag

* Answer: Tomorrow in Oslo: about 9 °C with a 70% chance of rain.
* Why: the only call failed, yet the answer reports a forecast

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | flag | [REVIEW] c3: groundlens.numeric unsupported: 9 °C : no numeral in any source; c4: groundlens.numeric unsupported: 70% : no numeral in any source |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: Tomorrow in Oslo: about 9 °C with a 70% chance of rain. |  |
| halluguard | flag | [1 of 1 claims flagged] Tomorrow in Oslo: about 9 °C with a 70% chance of rain. (support 0.82) |  |

### f2: failed_call, expected pass

* Answer: Tomorrow in Oslo: a high of 9 °C with a 70% chance of rain.
* Why: the first call failed, the retry succeeded, and the answer quotes the retry

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | flag | [REVIEW] c4: groundlens.numeric unsupported: 9 °C has no source value of the same dimension; c5: groundlens.numeric unsupported: 70% has no source value of the same dimension |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | pass | [grounded=True, neural=True] |  |
| halluguard | pass | [0 of 1 claims flagged] |  |

### t1: tool_never_called, expected flag

* Answer: I searched the web and found that the MX-200 warranty is 2 years, so after 3 years it has expired.
* Why: the answer says it searched the web; no search tool was called

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: I searched the web and found that the MX-200 warranty is 2 years, so after 3 years it has expired. |  |
| halluguard | flag | [1 of 1 claims flagged] I searched the web and found that the MX-200 warranty is 2 years, so after 3 years it has expired. (support 0.76) |  |

### q1: quote, expected flag

* Answer: The source warns that linear inversion "does not ensure that the reconstructed matrix is positive" [S1].
* Why: the source says 'does not guarantee', the quote says 'does not ensure'

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: The source warns that linear inversion "does not ensure that the reconstructed matrix is positive" [S1]. |  |
| halluguard | flag | [1 of 1 claims flagged] The source warns that linear inversion "does not ensure that the reconstructed matrix is positive" [S1]. (support 0.89) |  |

### q2: quote, expected flag

* Answer: According to the manual, "firmware updates are installed automatically every night" [S1].
* Why: the quote is in S2, but the answer cites S1

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: According to the manual, "firmware updates are installed automatically every night" [S1]. |  |
| halluguard | flag | [1 of 1 claims flagged] According to the manual, "firmware updates are installed automatically every night" [S1]. (support 0.89) |  |

### q3: quote, expected pass

* Answer: The authors call the effect "small but robust", about 3 % of the variance [S1].
* Why: straight vs curly quote marks, '3 %' vs '3%': the same wording

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: The authors call the effect "small but robust", about 3 % of the variance [S1]. |  |
| halluguard | flag | [1 of 1 claims flagged] The authors call the effect "small but robust", about 3 % of the variance [S1]. (support 0.93) |  |

### s1: self_talk, expected flag

* Answer: Let me report the tool's numbers: the total is 12,250.43. Wait, let me check: the monthly payment is 340.29.
* Why: the model's thinking aloud is left in the answer; the numbers themselves are right

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | flag | [FAIL] 0/2 claims supported, 1 hallucination(s) detected. Let me report the tool's numbers: the total is 12,250.43. / Wait, let me check: the monthly payment is 340.29. |  |
| ragground | pass | [grounded=True, neural=True] |  |
| halluguard | flag | [2 of 2 claims flagged] Let me report the tool's numbers: the total is 12,250.43. (support 0.31) / Wait, let me check: the monthly payment is 340.29. (support 0.44) |  |

### c1: self_contradiction, expected flag

* Answer: The passages do not say how long the warranty lasts. The warranty lasts two years from the date of purchase [S1].
* Why: the answer says the sources do not give the warranty, then gives it from them

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | flag | [FAIL] 1/2 claims supported, 1 hallucination(s) detected. The passages do not say how long the warranty lasts. |  |
| ragground | flag | [grounded=False, neural=True] CONTRADICTED: The passages do not say how long the warranty lasts. / UNSUPPORTED: The warranty lasts two years from the date of purchase [S1]. |  |
| halluguard | flag | [2 of 2 claims flagged] The passages do not say how long the warranty lasts. (support 0.62) / The warranty lasts two years from the date of purchase [S1]. (support 0.79) |  |

### fp1: comparison, expected pass

* Answer: Local noise takes a bigger toll on entanglement: the concurrence falls to 0.235, against 0.55 under global noise.
* Why: local noise on both photons leaves concurrence 0.235, global 0.55: local does take the bigger toll

| Tool | Verdict | Reason given | Right reason? |
|---|---|---|---|
| groundlens | pass | [PASS] |  |
| longtracer | pass | [PASS] All 1 claim(s) supported. |  |
| ragground | flag | [grounded=False, neural=True] UNSUPPORTED: Local noise takes a bigger toll on entanglement: the concurrence falls to 0.235, against 0.55 under global noise. |  |
| halluguard | flag | [1 of 1 claims flagged] Local noise takes a bigger toll on entanglement: the concurrence falls to 0.235, against 0.55 under global noise. (support 0.65) |  |

