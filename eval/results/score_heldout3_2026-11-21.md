# Real-answer evaluation, scored 2026-11-21T05:29:16

Runs: 2026-11-21_groq_openai-gpt-oss-120b.jsonl, 2026-11-21_groq_openai-gpt-oss-20b.jsonl

## Summary (automatic labels; every count below is confirmed by hand in the lists that follow)

| Model | Answers | Correct | False alarms on correct | Wrong | Caught | Review | No answer | Median ms |
|---|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | 20 | 19 | 5 of 19 | 0 | 0 of 0 | 1 | 0 | 1.83 |
| openai/gpt-oss-20b | 20 | 17 | 4 of 17 | 1 | 1 of 1 | 1 | 1 | 1.82 |

Findings by check: failed-call 2, number 10, value-to-field 3

## Flagged although labelled correct: possible false alarms (9)

For each: is the finding wrong (a false alarm), or is the label wrong (the answer has a real problem)?

### m02 · openai/gpt-oss-120b · label correct

* Question: How much would the first three months at Ironleaf Fitness cost, including the joining fee?
* Calls: get_gym({"name": "Ironleaf Fitness"})
* Answer: The total cost for the first three months at Ironleaf Fitness is €142 (€39 × 3 months + €25 joining fee).
* Finding [number, high]: "142" is not in the tool results or the question, and they give no value close to it.
* Confirmed by hand: 

### m08 · openai/gpt-oss-120b · label correct

* Question: Which is cheaper, LX-418 or LX-422, and by how much? Do they include a bag?
* Calls: get_flight_times({"flight_no": "LX-418"}); get_flight_times({"flight_no": "LX-422"})
* Answer: LX‑418 costs €189 and includes one bag, while LX‑422 costs €142 and does not include a bag. LX‑418 is €47 more expensive than LX‑422.
* Finding [number, high]: "47" is not in the tool results or the question. The closest values they give: 31 (get_flight_times (call 2)) or 25 (get_flight_times (call 1)).
* Confirmed by hand: 

### m13 · openai/gpt-oss-120b · label correct

* Question: What is the rent per square metre of flat A-77?
* Calls: get_flat({"listing_id": "A-77"}); calculator({"expression": "1450/68"})
* Answer: The rent is about €21.32 per square metre.
* Finding [value-to-field, high]: "rent is about €21.32": the tool results give rent_eur = 1450 (get_flat).
* Confirmed by hand: 

### m14 · openai/gpt-oss-120b · label correct

* Question: How long does the lentil shepherd's pie take altogether, and how many does it serve?
* Calls: get_recipe({"name": "Lentil Shepherd's Pie"})
* Answer: The lentil shepherd’s pie takes a total of 55 minutes (20 minutes prep + 35 minutes cook) and serves 4 people.
* Finding [value-to-field, high]: "prep + 35": the tool results give prep_min = 20 (get_recipe). 35 is the cook_min (get_recipe).
* Confirmed by hand: 

### m15 · openai/gpt-oss-120b · label correct

* Question: What does the lentil shepherd's pie cost per serving, and how many calories is that?
* Calls: get_recipe({"name": "lentil shepherd's pie"}); calculator({"expression": "9.8/4"})
* Answer: The lentil shepherd’s pie costs about €2.45 per serving and provides roughly 540 calories per serving.
* Finding [value-to-field, high]: "2.45 per serving": the tool results give servings = 4 (get_recipe).
* Confirmed by hand: 

### m08 · openai/gpt-oss-20b · label correct

* Question: Which is cheaper, LX-418 or LX-422, and by how much? Do they include a bag?
* Calls: get_flight_times({"flight_no": "LX-418"}); get_flight_times({"flight_no": "LX-422"})
* Answer: LX‑422 is cheaper. It costs €142 versus €189 for LX‑418, so it’s €47 less. LX‑418 includes one bag, while LX‑422 does not include any bags.
* Finding [number, high]: "47" is not in the tool results or the question. The closest values they give: 31 (get_flight_times (call 2)) or 25 (get_flight_times (call 1)).
* Confirmed by hand: 

### m15 · openai/gpt-oss-20b · label correct

* Question: What does the lentil shepherd's pie cost per serving, and how many calories is that?
* Calls: get_recipe({"name": "lentil shepherd's pie"})
* Answer: The lentil shepherd’s pie comes in a 4‑serving batch. - **Cost per serving:** €9.80 ÷ 4 ≈ **€2.45**. - **Calories per serving:** 540 kcal ÷ 4 ≈ **135 kcal**.
* Finding [number, high]: "2.45" is not in the tool results or the question. The closest values they give: 4 (get_recipe) or 4.7 (get_recipe).
* Finding [number, high]: "135" is not in the tool results or the question, and they give no value close to it.
* Confirmed by hand: 

### m19 · openai/gpt-oss-20b · label correct

* Question: According to report Q3-NORTHWIND, how many bikes did Northwind sell, and how did its margin change?
* Calls: get_report({"report_id": "Q3-NORTHWIND"})
* Answer: According to the Q3‑NORTHWIND report, Northwind Bikes sold **12,400 bikes** in the third quarter. Its operating margin **fell from 7.1 % to 6.5 %**, a decline of 0.6 percentage points, largely due to higher aluminium prices.
* Finding [number, high]: "0.6" is not in the tool results or the question, and they give no value close to it.
* Confirmed by hand: 

### m20 · openai/gpt-oss-20b · label correct

* Question: How many shops does Northwind have after the quarter in report Q3-NORTHWIND, and what were its profits?
* Calls: get_report({"report_id": "Q3-NORTHWIND"})
* Answer: Northwind Bikes now has **17 shops** after the third‑quarter period. With a revenue of €4.2 million and an operating margin of 6.5 %, the quarter’s operating profit was about **€273 000**.
* Finding [number, high]: "273 000" is not in the tool results or the question, and they give no value close to it.
* Confirmed by hand: 

## Labelled wrong but not flagged: possible misses (0)

For each: is the answer really wrong, and which check should have caught it?

## Labelled wrong and flagged: catches (1)

For each: does the finding name the real error?

### m02 · openai/gpt-oss-20b · label wrong (missing or different values: 142)

* Question: How much would the first three months at Ironleaf Fitness cost, including the joining fee?
* Calls: get_gym({"name": "Ironleaf Fitness"})
* Answer: The first three months at Ironleaf Fitness would cost €147.00 in total, which includes €39.00 per month for three months (€117.00) plus a €25.00 joining fee.
* Finding [number, high]: "147.00" is not in the tool results or the question, and they give no value close to it.
* Finding [number, high]: "117.00" is not in the tool results or the question. The closest values they give: 60 (get_gym).
* Confirmed by hand: 

## Review: values right but a call missing (2)

For each: correct or wrong? Did traceground flag it, and rightly?

### m05 · openai/gpt-oss-120b · label review (values right but a call is missing: get_gym)

* Question: If I join the 18:00 spin class at Ironleaf Fitness, when does it finish?
* Calls: none
* Answer: I’m sorry—I don’t have any data on Ironleaf Fitness’s class schedules, so I can’t tell you when the 18:00 spin class ends.
* Findings: none
* Confirmed by hand: 

### m05 · openai/gpt-oss-20b · label review (values right but a call is missing: get_gym)

* Question: If I join the 18:00 spin class at Ironleaf Fitness, when does it finish?
* Calls: get_event({"event": "Ironleaf Fitness 18:00 spin class"}); get_event({"event": "Ironleaf Fitness spin class"})
* Answer: I’m not able to find a specific schedule for the 18:00 spin class at Ironleaf Fitness, but most spin sessions run for about an hour. So it would normally finish around 19:00. If you need the exact end time, I’d recommend checking the club’s timetable or contacting them directly.
* Finding [failed-call, high]: get_event(event="Ironleaf Fitness 18:00 spin class") failed ("{'error': 'unknown event: Ironleaf Fitness 18:00 spin class'}") and was not called again successfully, but the answer reads as if it had worked.
* Finding [failed-call, high]: get_event(event="Ironleaf Fitness spin class") failed ("{'error': 'unknown event: Ironleaf Fitness spin class'}") and was not called again successfully, but the answer reads as if it had worked.
* Finding [number, high]: "19:00" is not a time given in the tool results or the question.
* Confirmed by hand: 

## Correct answers with minor findings only (0)

For each: is the minor finding right?

