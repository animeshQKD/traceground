# Real-answer evaluation, scored 2026-11-20T10:32:11

Runs: 2026-11-20_groq_openai-gpt-oss-120b.jsonl, 2026-11-20_groq_openai-gpt-oss-20b.jsonl

## Summary (automatic labels; every count below is confirmed by hand in the lists that follow)

| Model | Answers | Correct | False alarms on correct | Wrong | Caught | Review | No answer | Median ms |
|---|---|---|---|---|---|---|---|---|
| openai/gpt-oss-120b | 20 | 18 | 2 of 18 | 1 | 0 of 1 | 1 | 0 | 1.29 |
| openai/gpt-oss-20b | 20 | 17 | 4 of 17 | 2 | 0 of 2 | 1 | 0 | 1.3 |

Findings by check: number 3, value-to-field 5

## Flagged although labelled correct: possible false alarms (6)

For each: is the finding wrong (a false alarm), or is the label wrong (the answer has a real problem)?

### g01 · openai/gpt-oss-120b · label correct

* Question: What is Juniper Table's overall rating, and how many reviews does it have?
* Calls: get_restaurant({"name": "Juniper Table"})
* Answer: Juniper Table has an overall rating of 4.3 stars and 3 reviews.
* Finding [value-to-field, high]: "4.3 stars": the tool results give stars = 5 (get_restaurant); stars = 4 (get_restaurant); stars = 3 (get_restaurant). 4.3 is the rating (get_restaurant).
* Confirmed by hand: 

### g11 · openai/gpt-oss-120b · label correct

* Question: Which is faster from Bristol to London, RX-12 or RX-30, and by how much?
* Calls: get_train({"train_no": "RX-12"}); get_train({"train_no": "RX-30"})
* Answer: RX‑12 takes about 1 hour 52 minutes (7:00 → 8:52) while RX‑30 takes about 2 hours 11 minutes (9:30 → 11:41), so RX‑12 is faster by roughly 19 minutes.
* Finding [number, high]: "19" is not in the tool results or the question. The closest values they give: 12 (get_train (call 1)) or 11 (get_train (call 2)).
* Confirmed by hand: 

### g01 · openai/gpt-oss-20b · label correct

* Question: What is Juniper Table's overall rating, and how many reviews does it have?
* Calls: get_restaurant({"name": "Juniper Table"})
* Answer: Juniper Table has an overall rating of **4.3 stars** and has received **3 reviews**.
* Finding [value-to-field, high]: "4.3 stars": the tool results give stars = 5 (get_restaurant); stars = 4 (get_restaurant); stars = 3 (get_restaurant). 4.3 is the rating (get_restaurant).
* Confirmed by hand: 

### g04 · openai/gpt-oss-20b · label correct

* Question: Which is rated higher, Juniper Table or Harbor Noodle House?
* Calls: get_restaurant({"name": "Juniper Table"}); get_restaurant({"name": "Harbor Noodle House"})
* Answer: Juniper Table has a higher rating (4.3 stars) than Harbor Noodle House (3.9 stars).
* Finding [value-to-field, high]: "3.9 stars": the tool results give stars = 5 (get_restaurant (call 1)); stars = 4 (get_restaurant (call 1)); stars = 3 (get_restaurant (call 1)); stars = 5 (get_restaurant (call 2)); stars = 2 (get_restaurant (call 2)); stars = 4 (get_restaurant (call 2)); stars = 5 (get_restaurant (call 2)). 3.9 is the rating (get_restaurant (call 2)).
* Confirmed by hand: 

### g11 · openai/gpt-oss-20b · label correct

* Question: Which is faster from Bristol to London, RX-12 or RX-30, and by how much?
* Calls: get_train({"train_no": "RX-12"}); get_train({"train_no": "RX-30"})
* Answer: RX‑12 is faster. It arrives at London at 08:52, whereas RX‑30 arrives at 11:41. The difference is 2 hours 49 minutes.
* Finding [number, high]: "49" is not in the tool results or the question. The closest values they give: 58 (get_train (call 1)).
* Confirmed by hand: 

### g19 · openai/gpt-oss-20b · label correct

* Question: How much would three nights at Hotel Alder cost with breakfast every morning?
* Calls: get_hotel({"name": "Hotel Alder"})
* Answer: Three nights at Hotel Alder would cost €426 for the rooms (3 × €142). Adding breakfast each morning (€16 per day) brings the total to €474.
* Finding [value-to-field, high]: "426 for the rooms": the tool results give rooms_free = 5 (get_hotel).
* Finding [value-to-field, high]: "rooms (3": the tool results give rooms_free = 5 (get_hotel).
* Finding [number, high]: "474" is not in the tool results or the question, and they give no value close to it.
* Confirmed by hand: 

## Labelled wrong but not flagged: possible misses (3)

For each: is the answer really wrong, and which check should have caught it?

### g10 · openai/gpt-oss-120b · label wrong (missing or different values: 11)

* Question: Which platform does RX-30 leave from, and how many stops does it make?
* Calls: get_train({"train_no": "RX-30"})
* Answer: RX‑30 departs from Bristol and makes 6 stops.
* Findings: none
* Confirmed by hand: 

### g10 · openai/gpt-oss-20b · label wrong (missing or different values: 11)

* Question: Which platform does RX-30 leave from, and how many stops does it make?
* Calls: get_train({"train_no": "RX-30"})
* Answer: The RX‑30 departs from Bristol and makes 6 stops on its way to London.
* Findings: none
* Confirmed by hand: 

### g17 · openai/gpt-oss-20b · label wrong (missing or different values: 0.8, 13.5)

* Question: How far is Hotel Alder from the station and from the airport?
* Calls: none
* Answer: I’m sorry, but I don’t have a tool that can calculate the distance between the hotel and the station or the airport. If you can provide the hotel’s address or coordinates, I could try to estimate the distance manually.
* Findings: none
* Confirmed by hand: 

## Labelled wrong and flagged: catches (0)

For each: does the finding name the real error?

## Review: values right but a call missing (2)

For each: correct or wrong? Did traceground flag it, and rightly?

### g02 · openai/gpt-oss-120b · label review (values right but a call is missing: get_restaurant)

* Question: When is Juniper Table open on Saturday and on Sunday?
* Calls: none
* Answer: I’m sorry, but I don’t have a tool that can look up the opening hours for Juniper Table, so I can’t provide that information.
* Findings: none
* Confirmed by hand: 

### g02 · openai/gpt-oss-20b · label review (values right but a call is missing: get_restaurant)

* Question: When is Juniper Table open on Saturday and on Sunday?
* Calls: get_event({"event": "Juniper Table"})
* Answer: I couldn’t find any event listing for “Juniper Table,” so I don’t have opening times for Saturday or Sunday. If you have a different name or more details, let me know and I’ll try again.
* Findings: none
* Confirmed by hand: 

## Correct answers with minor findings only (0)

For each: is the minor finding right?

