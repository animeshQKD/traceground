# Real-answer evaluation, scored 2026-11-19T09:58:25

Runs: 2026-11-17_groq_openai-gpt-oss-120b.jsonl, 2026-11-17_groq_openai-gpt-oss-20b.jsonl

## Summary (automatic labels; every count below is confirmed by hand in the lists that follow)

| Model | Answers | Correct | False alarms on correct | Wrong | Caught | Review | No answer | Median ms |
|---|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | 20 | 18 | 1 of 18 | 2 | 2 of 2 | 0 | 0 | 0.94 |
| openai/gpt-oss-20b | 20 | 20 | 2 of 20 | 0 | 0 of 0 | 0 | 0 | 0.89 |

Findings by check: number 5, value-to-field 2

## Flagged although labelled correct: possible false alarms (3)

For each: is the finding wrong (a false alarm), or is the label wrong (the answer has a real problem)?

### h14 · openai/gpt-oss-120b · label correct

* Question: Is the CO2 level at LAB-2 high, and how charged is its battery?
* Calls: get_sensor({"sensor_id": "LAB-2"})
* Answer: The LAB‑2 sensor reports a CO₂ concentration of 1,240 ppm, which is above typical indoor background levels (≈400‑600 ppm) and can be considered high. Its battery is low, at only 12 % charge.
* Finding [number, high]: "400" is not in the tool results or the question, and they give no value close to it.
* Finding [number, high]: "600" is not in the tool results or the question. The closest values they give: 1009.3 (get_sensor).
* Confirmed by hand: 

### h08 · openai/gpt-oss-20b · label correct

* Question: How much did Nordwind's revenue grow from 2024 to 2025?
* Calls: get_company_financials({"company": "Nordwind", "year": 2024}); get_company_financials({"company": "Nordwind", "year": 2025})
* Answer: Nordwind’s revenue rose from $1,612.3 million in 2024 to $1,840.5 million in 2025, an increase of about $228.2 million, which is roughly a **14.4 %** year‑over‑year growth.
* Finding [number, high]: "14.4 %" is not in the tool results or the question. The closest values they give: 15.6 (get_company_financials (call 1)) or 17.0 (get_company_financials (call 2)).
* Confirmed by hand: 

### h14 · openai/gpt-oss-20b · label correct

* Question: Is the CO2 level at LAB-2 high, and how charged is its battery?
* Calls: get_sensor({"sensor_id": "LAB-2"})
* Answer: The CO₂ concentration at LAB‑2 is 1,240 ppm, which is above typical indoor comfort levels (usually < 800 ppm). The sensor’s battery is only at 12 % charge.
* Finding [number, high]: "800" is not in the tool results or the question. The closest values they give: 1009.3 (get_sensor) or 1240 (get_sensor).
* Confirmed by hand: 

## Labelled wrong but not flagged: possible misses (0)

For each: is the answer really wrong, and which check should have caught it?

## Labelled wrong and flagged: catches (2)

For each: does the finding name the real error?

### h02 · openai/gpt-oss-120b · label wrong (missing or different values: 45)

* Question: How late is AI-101 and how many seats are still free?
* Calls: get_flight({"flight_no": "AI-101"})
* Answer: AI‑101 departs at 16:00 (4 PM) and currently has 27 seats still free.
* Finding [number, high]: "16" is not in the tool results or the question. The closest values they give: 27 (get_flight).
* Confirmed by hand: 

### h07 · openai/gpt-oss-120b · label wrong (missing or different values: 1840.5)

* Question: What were Nordwind's revenue and net income in 2025?
* Calls: get_company_financials({"company": "Nordwind", "year": 2025})
* Answer: Nordwind earned about €1.84 billion in revenue and €221.4 million in net income in 2025.
* Finding [value-to-field, high]: "1.84 billion in revenue": the tool results give revenue_musd = 1840.5 (get_company_financials) in USD; the answer writes EUR, and no call converted it.
* Finding [value-to-field, high]: "221.4 million in net income": the tool results give net_income_musd = 221.4 (get_company_financials) in USD; the answer writes EUR, and no call converted it.
* Confirmed by hand: 

## Review: values right but a call missing (0)

For each: correct or wrong? Did traceground flag it, and rightly?

## Correct answers with minor findings only (0)

For each: is the minor finding right?

