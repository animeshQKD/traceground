# Planted errors in real answers, 2026-11-20T10:32:11

Runs: 2026-11-20_groq_openai-gpt-oss-120b.jsonl, 2026-11-20_groq_openai-gpt-oss-20b.jsonl

140 planted errors in 21 real answers that are correct by hand and that traceground passes. The errors are planted, not made by the models.

| Kind | Planted | Caught | Flagged elsewhere | Missed | Caught by |
|---|---|---|---|---|---|
| digits swapped | 46 | 46 (100%) | 0 | 0 | number 40, value-to-field 6 |
| last digit off by one | 56 | 55 (98%) | 0 | 1 | number 49, value-to-field 6 |
| value of another field | 32 | 10 (31%) | 0 | 22 | value-to-field 10 |
| two values swapped | 6 | 4 (67%) | 0 | 2 | value-to-field 4 |
| all | 140 | 115 (82%) | 0 | 25 | number 89, value-to-field 26 |

Answers not used: g01 (openai/gpt-oss-120b): traceground says problems; g02 (openai/gpt-oss-120b): wrong by hand; g11 (openai/gpt-oss-120b): traceground says problems; g01 (openai/gpt-oss-20b): traceground says problems; g04 (openai/gpt-oss-20b): traceground says problems; g11 (openai/gpt-oss-20b): wrong by hand; g17 (openai/gpt-oss-20b): wrong by hand; g19 (openai/gpt-oss-20b): traceground says problems

## Missed (25)

* **g04** · openai/gpt-oss-120b · value of another field: 4.3 (rating) -> 3 (review_count)
  * Answer: Juniper Table is rated higher (3 vs 3.9 for Harbor Noodle House).
* **g04** · openai/gpt-oss-120b · value of another field: 4.3 (rating) -> 2 (price_level)
  * Answer: Juniper Table is rated higher (2 vs 3.9 for Harbor Noodle House).
* **g04** · openai/gpt-oss-120b · value of another field: 3.9 (rating) -> 4 (review_count)
  * Answer: Juniper Table is rated higher (4.3 vs 4 for Harbor Noodle House).
* **g04** · openai/gpt-oss-120b · value of another field: 3.9 (rating) -> 1 (price_level)
  * Answer: Juniper Table is rated higher (4.3 vs 1 for Harbor Noodle House).
* **g07** · openai/gpt-oss-120b · value of another field: 12.5 (price_eur) -> 14 (tickets_left)
  * Answer: The Rooftop Film Club has 14 tickets left, each costing €14.
* **g12** · openai/gpt-oss-120b · last digit off by one: 2025 -> 2026
  * Answer: Riverside Library reopened after a fourteen‑month closure caused by the August 2026 flood, with repairs costing £1.8 million—£1.1 million funded by the council and the remainder by a national fund. Although about 22,000 books were lost, 9,500 have been replaced, and the library will now operate six days a week with extended hours starting in January.
* **g16** · openai/gpt-oss-120b · value of another field: 142 (rate_eur) -> 16 (breakfast_eur)
  * Answer: A night at Hotel Alder costs €16, and breakfast is **not** included (it can be added for an extra €16).
* **g16** · openai/gpt-oss-120b · value of another field: 142 (rate_eur) -> 4.6 (guest_rating)
  * Answer: A night at Hotel Alder costs €4.6, and breakfast is **not** included (it can be added for an extra €16).
* **g16** · openai/gpt-oss-120b · value of another field: 16 (breakfast_eur) -> 142 (rate_eur)
  * Answer: A night at Hotel Alder costs €142, and breakfast is **not** included (it can be added for an extra €142).
* **g16** · openai/gpt-oss-120b · value of another field: 16 (breakfast_eur) -> 4.6 (guest_rating)
  * Answer: A night at Hotel Alder costs €142, and breakfast is **not** included (it can be added for an extra €4.6).
* **g16** · openai/gpt-oss-120b · two values swapped: 142 (rate_eur) <-> 16 (breakfast_eur)
  * Answer: A night at Hotel Alder costs €16, and breakfast is **not** included (it can be added for an extra €142).
* **g17** · openai/gpt-oss-120b · value of another field: 0.8 (station_km) -> 142 (rate_eur)
  * Answer: Hotel Alder is about 142 km from the nearest train station and roughly 13.5 km from the airport.
* **g17** · openai/gpt-oss-120b · value of another field: 0.8 (station_km) -> 16 (breakfast_eur)
  * Answer: Hotel Alder is about 16 km from the nearest train station and roughly 13.5 km from the airport.
* **g17** · openai/gpt-oss-120b · value of another field: 13.5 (airport_km) -> 142 (rate_eur)
  * Answer: Hotel Alder is about 0.8 km from the nearest train station and roughly 142 km from the airport.
* **g17** · openai/gpt-oss-120b · value of another field: 13.5 (airport_km) -> 16 (breakfast_eur)
  * Answer: Hotel Alder is about 0.8 km from the nearest train station and roughly 16 km from the airport.
* **g17** · openai/gpt-oss-120b · two values swapped: 0.8 (station_km) <-> 13.5 (airport_km)
  * Answer: Hotel Alder is about 13.5 km from the nearest train station and roughly 0.8 km from the airport.
* **g07** · openai/gpt-oss-20b · value of another field: 12.50 (price_eur) -> 14 (tickets_left)
  * Answer: There are 14 tickets left for the Rooftop Film Club, and each ticket costs €14.
* **g09** · openai/gpt-oss-20b · value of another field: 12 (delay_min) -> 4 (platform)
  * Answer: Train RX‑12 departs Bristol at 07:00 and arrives in London at 08:52. It is running 4 minutes late.
* **g09** · openai/gpt-oss-20b · value of another field: 12 (delay_min) -> 3 (stops)
  * Answer: Train RX‑12 departs Bristol at 07:00 and arrives in London at 08:52. It is running 3 minutes late.
* **g16** · openai/gpt-oss-20b · value of another field: 142.00 (rate_eur) -> 16 (breakfast_eur)
  * Answer: A night at Hotel Alder in Bristol costs **€16**. Breakfast is **not included**; it can be added for an extra €16.00.
* **g16** · openai/gpt-oss-20b · value of another field: 142.00 (rate_eur) -> 4.6 (guest_rating)
  * Answer: A night at Hotel Alder in Bristol costs **€4.6**. Breakfast is **not included**; it can be added for an extra €16.00.
* **g16** · openai/gpt-oss-20b · value of another field: 16.00 (breakfast_eur) -> 142 (rate_eur)
  * Answer: A night at Hotel Alder in Bristol costs **€142.00**. Breakfast is **not included**; it can be added for an extra €142.
* **g16** · openai/gpt-oss-20b · value of another field: 16.00 (breakfast_eur) -> 4.6 (guest_rating)
  * Answer: A night at Hotel Alder in Bristol costs **€142.00**. Breakfast is **not included**; it can be added for an extra €4.6.
* **g20** · openai/gpt-oss-20b · value of another field: 4.6 (guest_rating) -> 142 (rate_eur)
  * Answer: Hotel Alder’s guest rating of 142 is higher than Juniper Table’s rating of 4.3.
* **g20** · openai/gpt-oss-20b · value of another field: 4.6 (guest_rating) -> 16 (breakfast_eur)
  * Answer: Hotel Alder’s guest rating of 16 is higher than Juniper Table’s rating of 4.3.

## Flagged elsewhere (0)

