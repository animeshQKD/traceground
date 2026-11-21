# Planted errors in real answers, 2026-11-21T05:29:15

Runs: 2026-11-21_groq_openai-gpt-oss-120b.jsonl, 2026-11-21_groq_openai-gpt-oss-20b.jsonl

199 planted errors in 23 real answers that are correct by hand and that traceground passes. The errors are planted, not made by the models.

| Kind | Planted | Caught | Flagged elsewhere | Missed | Caught by |
|---|---|---|---|---|---|
| digits swapped | 57 | 55 (96%) | 0 | 2 | number 45, value-to-field 10 |
| last digit off by one | 67 | 65 (97%) | 0 | 2 | number 53, value-to-field 12 |
| value of another field | 56 | 28 (50%) | 8 | 20 | value-to-field 28 |
| two values swapped | 9 | 4 (44%) | 0 | 5 | value-to-field 4 |
| fraction as percent | 10 | 10 (100%) | 0 | 0 | number 10 |
| all | 199 | 162 (81%) | 8 | 29 | number 108, value-to-field 54 |

Answers not used: m02 (openai/gpt-oss-120b): traceground says problems; m05 (openai/gpt-oss-120b): wrong by hand; m08 (openai/gpt-oss-120b): traceground says problems; m13 (openai/gpt-oss-120b): traceground says problems; m14 (openai/gpt-oss-120b): traceground says problems; m15 (openai/gpt-oss-120b): traceground says problems; m02 (openai/gpt-oss-20b): wrong by hand; m05 (openai/gpt-oss-20b): wrong by hand; m08 (openai/gpt-oss-20b): traceground says problems; m15 (openai/gpt-oss-20b): traceground says problems; m19 (openai/gpt-oss-20b): traceground says problems; m20 (openai/gpt-oss-20b): traceground says problems

## Missed (29)

* **m10** · openai/gpt-oss-120b · value of another field: 2,900 (deposit_eur) -> 1,450 (rent_eur)
  * Answer: The flat A‑77 costs €1,450 rent per month with a €1,450 deposit, and the listing notes that bills are **not** included.
* **m10** · openai/gpt-oss-120b · value of another field: 2,900 (deposit_eur) -> 68 (size_m2)
  * Answer: The flat A‑77 costs €1,450 rent per month with a €68 deposit, and the listing notes that bills are **not** included.
* **m12** · openai/gpt-oss-120b · digits swapped: 0.4 -> 4.0
  * Answer: Flat A‑77 is about 4.0 km from the metro and 3.1 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 1.9 km from the centre.
* **m12** · openai/gpt-oss-120b · value of another field: 0.4 (metro_km) -> 1450 (rent_eur)
  * Answer: Flat A‑77 is about 1450 km from the metro and 3.1 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 1.9 km from the centre.
* **m12** · openai/gpt-oss-120b · value of another field: 0.4 (metro_km) -> 2900 (deposit_eur)
  * Answer: Flat A‑77 is about 2900 km from the metro and 3.1 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 1.9 km from the centre.
* **m12** · openai/gpt-oss-120b · value of another field: 3.1 (centre_km) -> 1450 (rent_eur)
  * Answer: Flat A‑77 is about 0.4 km from the metro and 1450 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 1.9 km from the centre.
* **m12** · openai/gpt-oss-120b · value of another field: 3.1 (centre_km) -> 2900 (deposit_eur)
  * Answer: Flat A‑77 is about 0.4 km from the metro and 2900 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 1.9 km from the centre.
* **m12** · openai/gpt-oss-120b · value of another field: 1.6 (metro_km) -> 1180 (rent_eur)
  * Answer: Flat A‑77 is about 0.4 km from the metro and 3.1 km from the city centre, while flat B‑12 is roughly 1180 km from the metro and 1.9 km from the centre.
* **m12** · openai/gpt-oss-120b · value of another field: 1.6 (metro_km) -> 1180 (deposit_eur)
  * Answer: Flat A‑77 is about 0.4 km from the metro and 3.1 km from the city centre, while flat B‑12 is roughly 1180 km from the metro and 1.9 km from the centre.
* **m12** · openai/gpt-oss-120b · value of another field: 1.9 (centre_km) -> 1180 (rent_eur)
  * Answer: Flat A‑77 is about 0.4 km from the metro and 3.1 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 1180 km from the centre.
* **m12** · openai/gpt-oss-120b · value of another field: 1.9 (centre_km) -> 1180 (deposit_eur)
  * Answer: Flat A‑77 is about 0.4 km from the metro and 3.1 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 1180 km from the centre.
* **m12** · openai/gpt-oss-120b · two values swapped: 0.4 (metro_km) <-> 3.1 (centre_km)
  * Answer: Flat A‑77 is about 3.1 km from the metro and 0.4 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 1.9 km from the centre.
* **m12** · openai/gpt-oss-120b · two values swapped: 0.4 (metro_km) <-> 1.9 (centre_km)
  * Answer: Flat A‑77 is about 1.9 km from the metro and 3.1 km from the city centre, while flat B‑12 is roughly 1.6 km from the metro and 0.4 km from the centre.
* **m12** · openai/gpt-oss-120b · two values swapped: 3.1 (centre_km) <-> 1.6 (metro_km)
  * Answer: Flat A‑77 is about 0.4 km from the metro and 1.6 km from the city centre, while flat B‑12 is roughly 3.1 km from the metro and 1.9 km from the centre.
* **m17** · openai/gpt-oss-120b · last digit off by one: 3 -> 4
  * Answer: Northwind Bikes sold 12,400 bikes in Q3 2026, generating €4.2 million in revenue but seeing its operating margin dip to 6.5% from 7.1% due to higher aluminium costs, while opening new stores in Bergen and Ghent to bring its total to 17 locations. CEO Mara Lindqvist described the quarter as “steady rather than spectacular” and announced a planned price increase of about 4% starting in January.
* **m10** · openai/gpt-oss-20b · value of another field: 2,900 (deposit_eur) -> 1,450 (rent_eur)
  * Answer: Flat A‑77 rents €1,450 per month and requires a €1,450 deposit. Bills are **not** included in the rent.
* **m10** · openai/gpt-oss-20b · value of another field: 2,900 (deposit_eur) -> 68 (size_m2)
  * Answer: Flat A‑77 rents €1,450 per month and requires a €68 deposit. Bills are **not** included in the rent.
* **m12** · openai/gpt-oss-20b · digits swapped: 0.4 -> 4.0
  * Answer: Flat A‑77 is about 4.0 km from the nearest metro stop and roughly 3.1 km from the city centre.  
Flat B‑12 is about 1.6 km from the metro and roughly 1.9 km from the centre.
* **m12** · openai/gpt-oss-20b · value of another field: 0.4 (metro_km) -> 1450 (rent_eur)
  * Answer: Flat A‑77 is about 1450 km from the nearest metro stop and roughly 3.1 km from the city centre.  
Flat B‑12 is about 1.6 km from the metro and roughly 1.9 km from the centre.
* **m12** · openai/gpt-oss-20b · value of another field: 0.4 (metro_km) -> 2900 (deposit_eur)
  * Answer: Flat A‑77 is about 2900 km from the nearest metro stop and roughly 3.1 km from the city centre.  
Flat B‑12 is about 1.6 km from the metro and roughly 1.9 km from the centre.
* **m12** · openai/gpt-oss-20b · value of another field: 3.1 (centre_km) -> 1450 (rent_eur)
  * Answer: Flat A‑77 is about 0.4 km from the nearest metro stop and roughly 1450 km from the city centre.  
Flat B‑12 is about 1.6 km from the metro and roughly 1.9 km from the centre.
* **m12** · openai/gpt-oss-20b · value of another field: 3.1 (centre_km) -> 2900 (deposit_eur)
  * Answer: Flat A‑77 is about 0.4 km from the nearest metro stop and roughly 2900 km from the city centre.  
Flat B‑12 is about 1.6 km from the metro and roughly 1.9 km from the centre.
* **m12** · openai/gpt-oss-20b · value of another field: 1.6 (metro_km) -> 1180 (rent_eur)
  * Answer: Flat A‑77 is about 0.4 km from the nearest metro stop and roughly 3.1 km from the city centre.  
Flat B‑12 is about 1180 km from the metro and roughly 1.9 km from the centre.
* **m12** · openai/gpt-oss-20b · value of another field: 1.6 (metro_km) -> 1180 (deposit_eur)
  * Answer: Flat A‑77 is about 0.4 km from the nearest metro stop and roughly 3.1 km from the city centre.  
Flat B‑12 is about 1180 km from the metro and roughly 1.9 km from the centre.
* **m12** · openai/gpt-oss-20b · value of another field: 1.9 (centre_km) -> 1180 (rent_eur)
  * Answer: Flat A‑77 is about 0.4 km from the nearest metro stop and roughly 3.1 km from the city centre.  
Flat B‑12 is about 1.6 km from the metro and roughly 1180 km from the centre.
* **m12** · openai/gpt-oss-20b · value of another field: 1.9 (centre_km) -> 1180 (deposit_eur)
  * Answer: Flat A‑77 is about 0.4 km from the nearest metro stop and roughly 3.1 km from the city centre.  
Flat B‑12 is about 1.6 km from the metro and roughly 1180 km from the centre.
* **m12** · openai/gpt-oss-20b · two values swapped: 0.4 (metro_km) <-> 3.1 (centre_km)
  * Answer: Flat A‑77 is about 3.1 km from the nearest metro stop and roughly 0.4 km from the city centre.  
Flat B‑12 is about 1.6 km from the metro and roughly 1.9 km from the centre.
* **m12** · openai/gpt-oss-20b · two values swapped: 1.6 (metro_km) <-> 1.9 (centre_km)
  * Answer: Flat A‑77 is about 0.4 km from the nearest metro stop and roughly 3.1 km from the city centre.  
Flat B‑12 is about 1.9 km from the metro and roughly 1.6 km from the centre.
* **m17** · openai/gpt-oss-20b · last digit off by one: 3  -> 4 
  * Answer: Northwind Bikes sold 12,400 bikes in Q3 2026, an 8 % year‑over‑year increase, generating €4.2 million in revenue but seeing its operating margin drop to 6.5 % from 7.1 % due to higher aluminium costs. The company opened two new shops, now operating 17 stores, and CEO Mara Lindqvist noted the quarter was “steady rather than spectacular” while anticipating a 4 % price rise in January.

## Flagged elsewhere (8)

* **m09** · openai/gpt-oss-120b · value of another field: 135 (duration_min) -> 25 (delay_min)
  * Answer: LX‑418 lasts 25 minutes, while LX‑422 lasts 150 minutes, so LX‑418 is the shorter flight by 15 minutes.
  * Finding: "15" is not in the tool results or the question. The closest values they give: 25 (get_flight_times (call 1)) or 9 (get_flight_times (call 1)).
* **m09** · openai/gpt-oss-120b · value of another field: 135 (duration_min) -> 189 (price_eur)
  * Answer: LX‑418 lasts 189 minutes, while LX‑422 lasts 150 minutes, so LX‑418 is the shorter flight by 15 minutes.
  * Finding: "15" is not in the tool results or the question. The closest values they give: 25 (get_flight_times (call 1)) or 9 (get_flight_times (call 1)).
* **m09** · openai/gpt-oss-120b · value of another field: 150 (duration_min) -> 0 (delay_min)
  * Answer: LX‑418 lasts 135 minutes, while LX‑422 lasts 0 minutes, so LX‑418 is the shorter flight by 15 minutes.
  * Finding: "15" is not in the tool results or the question. The closest values they give: 25 (get_flight_times (call 1)) or 9 (get_flight_times (call 1)).
* **m09** · openai/gpt-oss-120b · value of another field: 150 (duration_min) -> 142 (price_eur)
  * Answer: LX‑418 lasts 135 minutes, while LX‑422 lasts 142 minutes, so LX‑418 is the shorter flight by 15 minutes.
  * Finding: "15" is not in the tool results or the question. The closest values they give: 25 (get_flight_times (call 1)) or 9 (get_flight_times (call 1)).
* **m09** · openai/gpt-oss-20b · value of another field: 135 (duration_min) -> 25 (delay_min)
  * Answer: LX‑418 is the shorter flight. It flies for 25 minutes, whereas LX‑422 flies for 150 minutes – a difference of 15 minutes.
  * Finding: "15" is not in the tool results or the question. The closest values they give: 25 (get_flight_times (call 1)) or 9 (get_flight_times (call 1)).
* **m09** · openai/gpt-oss-20b · value of another field: 135 (duration_min) -> 189 (price_eur)
  * Answer: LX‑418 is the shorter flight. It flies for 189 minutes, whereas LX‑422 flies for 150 minutes – a difference of 15 minutes.
  * Finding: "15" is not in the tool results or the question. The closest values they give: 25 (get_flight_times (call 1)) or 9 (get_flight_times (call 1)).
* **m09** · openai/gpt-oss-20b · value of another field: 150 (duration_min) -> 0 (delay_min)
  * Answer: LX‑418 is the shorter flight. It flies for 135 minutes, whereas LX‑422 flies for 0 minutes – a difference of 15 minutes.
  * Finding: "15" is not in the tool results or the question. The closest values they give: 25 (get_flight_times (call 1)) or 9 (get_flight_times (call 1)).
* **m09** · openai/gpt-oss-20b · value of another field: 150 (duration_min) -> 142 (price_eur)
  * Answer: LX‑418 is the shorter flight. It flies for 135 minutes, whereas LX‑422 flies for 142 minutes – a difference of 15 minutes.
  * Finding: "15" is not in the tool results or the question. The closest values they give: 25 (get_flight_times (call 1)) or 9 (get_flight_times (call 1)).
