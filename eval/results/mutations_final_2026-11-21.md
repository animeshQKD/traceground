# Planted errors in real answers, 2026-11-21T15:25:27

Runs: 2026-11-21_groq_openai-gpt-oss-120b.jsonl, 2026-11-21_groq_openai-gpt-oss-20b.jsonl

282 planted errors in 42 real answers that are correct by hand and that traceground passes. The errors are planted, not made by the models.

| Kind | Planted | Caught | Flagged elsewhere | Missed | Caught by |
|---|---|---|---|---|---|
| digits swapped | 89 | 89 (100%) | 0 | 0 | number 65, value-to-field 24 |
| last digit off by one | 110 | 102 (93%) | 0 | 8 | number 74, value-to-field 28 |
| value of another field | 70 | 47 (67%) | 7 | 16 | value-to-field 47 |
| two values swapped | 10 | 8 (80%) | 1 | 1 | value-to-field 8 |
| fraction as percent | 3 | 3 (100%) | 0 | 0 | number 3 |
| all | 282 | 249 (88%) | 8 | 25 | number 142, value-to-field 107 |

Answers not used: z03 (openai/gpt-oss-120b): wrong by hand; z04 (openai/gpt-oss-120b): wrong by hand; z05 (openai/gpt-oss-120b): traceground says problems; z08 (openai/gpt-oss-120b): traceground says problems; z09 (openai/gpt-oss-120b): traceground says problems; z12 (openai/gpt-oss-120b): traceground says problems; z18 (openai/gpt-oss-120b): traceground says problems; z19 (openai/gpt-oss-120b): traceground says problems; z29 (openai/gpt-oss-120b): traceground says problems; z32 (openai/gpt-oss-120b): traceground says problems; z33 (openai/gpt-oss-120b): traceground says problems; z34 (openai/gpt-oss-120b): wrong by hand; z35 (openai/gpt-oss-120b): traceground says problems; z39 (openai/gpt-oss-120b): traceground says problems; z03 (openai/gpt-oss-20b): traceground says problems; z04 (openai/gpt-oss-20b): wrong by hand; z05 (openai/gpt-oss-20b): wrong by hand; z09 (openai/gpt-oss-20b): traceground says problems; z14 (openai/gpt-oss-20b): traceground says problems; z18 (openai/gpt-oss-20b): traceground says problems; z19 (openai/gpt-oss-20b): traceground says problems; z21 (openai/gpt-oss-20b): wrong by hand; z25 (openai/gpt-oss-20b): wrong by hand; z28 (openai/gpt-oss-20b): traceground says problems; z29 (openai/gpt-oss-20b): traceground says problems; z32 (openai/gpt-oss-20b): traceground says problems; z33 (openai/gpt-oss-20b): traceground says problems; z35 (openai/gpt-oss-20b): traceground says problems; z37 (openai/gpt-oss-20b): wrong by hand

## Missed (25)

* **z01** · openai/gpt-oss-120b · value of another field: 4.5 (rating) -> 4 (review_count)
  * Answer: Marlow & Finch Books has a rating of 4 stars and 4 reviews.
* **z10** · openai/gpt-oss-120b · value of another field: 23 (min_age) -> 52 (price_per_day_eur)
  * Answer: You must be at least 52 years old to rent offer CR‑71, and its fuel policy is “full to full.”
* **z10** · openai/gpt-oss-120b · value of another field: 23 (min_age) -> 450 (deposit_eur)
  * Answer: You must be at least 450 years old to rent offer CR‑71, and its fuel policy is “full to full.”
* **z11** · openai/gpt-oss-120b · last digit off by one: 18 -> 19
  * Answer: The Harbour Lights Orchestra concert’s doors open at 19:30, and the performance ends at 21:45.
* **z13** · openai/gpt-oss-120b · last digit off by one: 20 -> 21
  * Answer: The Harbour Lights Orchestra concert still has tickets available in the stalls tier (45 € each, 18 left) and the standing tier (21 € each, 140 left); the balcony tier is sold out.
* **z25** · openai/gpt-oss-120b · last digit off by one: 2025 -> 2026
  * Answer: Casa da Luz had 186,400 visitors in 2026.
* **z26** · openai/gpt-oss-120b · value of another field: 25 (data_gb) -> 14 (monthly_eur)
  * Answer: The P‑10 phone plan costs €14 per month and includes 14 GB of data.
* **z26** · openai/gpt-oss-120b · value of another field: 25 (data_gb) -> 12 (contract_months)
  * Answer: The P‑10 phone plan costs €14 per month and includes 12 GB of data.
* **z27** · openai/gpt-oss-120b · value of another field: 12 (contract_months) -> 14 (monthly_eur)
  * Answer: The total cost for plan P‑10 over its 14‑month contract, including the €10 setup fee, is €178.
* **z27** · openai/gpt-oss-120b · two values swapped: 12 (contract_months) <-> 178 (result)
  * Answer: The total cost for plan P‑10 over its 178‑month contract, including the €10 setup fee, is €12.
* **z28** · openai/gpt-oss-120b · value of another field: 24 (contract_months) -> 22 (monthly_eur)
  * Answer: The P‑30 plan costs €22 per month for a 22‑month contract with no setup fee, so the total cost over the whole contract is €22 × 24 = €528.
* **z28** · openai/gpt-oss-120b · value of another field: 24 (contract_months) -> 80 (data_gb)
  * Answer: The P‑30 plan costs €22 per month for a 80‑month contract with no setup fee, so the total cost over the whole contract is €22 × 24 = €528.
* **z30** · openai/gpt-oss-120b · value of another field: 24 (contract_months) -> 22 (monthly_eur)
  * Answer: Plan P‑30 has no setup fee (0 €) and a 22‑month contract.
* **z36** · openai/gpt-oss-120b · last digit off by one: 2027 -> 2028
  * Answer: Helix Robotics announced a €18 million Series B funding round led by Northgate Ventures, bringing its workforce to 140 employees and targeting an additional 60 hires by the end of 2028 while reporting a 72 % revenue increase to €9.4 million last year. CEO Tomás Reyes said the capital will scale its warehouse robots from pilot projects to full‑fleet deployments and that the company aims to achieve profitability in 2028.
* **z01** · openai/gpt-oss-20b · value of another field: 4.5 (rating) -> 4 (review_count)
  * Answer: Marlow & Finch Books has a rating of **4 stars** and has received **4 reviews**.
* **z07** · openai/gpt-oss-20b · value of another field: 38 (price_per_day_eur) -> 300 (deposit_eur)
  * Answer: The CR‑55 car rental costs €38 per day. For a 4‑day stay that stays within the included kilometres, the total would be 4 × €300 = **€152**. (The deposit of €300 is separate and not included in the daily rate.)
* **z07** · openai/gpt-oss-20b · value of another field: 38 (price_per_day_eur) -> 200 (km_included_per_day)
  * Answer: The CR‑55 car rental costs €38 per day. For a 4‑day stay that stays within the included kilometres, the total would be 4 × €200 = **€152**. (The deposit of €300 is separate and not included in the daily rate.)
* **z08** · openai/gpt-oss-20b · value of another field: 200 (km_included_per_day) -> 300 (deposit_eur)
  * Answer: CR‑71 includes more kilometres per day. It offers 250 km/day versus 300 km/day for CR‑55, so it’s 50 km/day higher.
* **z13** · openai/gpt-oss-20b · last digit off by one: 18 -> 19
  * Answer: The Harbour Lights Orchestra concert still has seats available in the **stalls** and **standing** tiers.  
- **Stalls**: €45.00 each, 19 seats left.  
- **Standing**: €20.00 each, 140 tickets left.
* **z24** · openai/gpt-oss-20b · last digit off by one: 2026 -> 2027
  * Answer: At Casa da Luz you can see two current exhibitions:

| Exhibition | Until |
|------------|-------|
| Light and Glass | 31 January 2027 |
| Harbour Photographs 1900‑1950 | 14 December 2027 |

Both are still on display, so you can visit them before the listed dates.
* **z26** · openai/gpt-oss-20b · value of another field: 25 (data_gb) -> 14 (monthly_eur)
  * Answer: The phone plan **P‑10** costs **€14.00 per month** and includes **14 GB of data** (plus unlimited minutes).
* **z26** · openai/gpt-oss-20b · value of another field: 25 (data_gb) -> 12 (contract_months)
  * Answer: The phone plan **P‑10** costs **€14.00 per month** and includes **12 GB of data** (plus unlimited minutes).
* **z30** · openai/gpt-oss-20b · value of another field: 24 (contract_months) -> 22 (monthly_eur)
  * Answer: Plan P‑30 has no setup fee (0 €) and comes with a 22‑month contract.
* **z36** · openai/gpt-oss-20b · last digit off by one: 2027 -> 2028
  * Answer: Helix Robotics announced a €18 million Series B funding round led by Northgate Ventures, boosting its workforce to 140 and targeting an additional 60 hires by the end of 2028. The company, which saw revenue jump 72 % to €9.4 million last year, plans to scale its warehouse‑robot fleet from pilot projects to full deployments and expects profitability by 2028.
* **z39** · openai/gpt-oss-20b · last digit off by one: 2027 -> 2028
  * Answer: According to the press release (PR‑HELIX), Helix Robotics currently employs 140 people and plans to hire 60 more by the end of 2028, bringing the total to 200 employees.

## Flagged elsewhere (8)

* **z28** · openai/gpt-oss-120b · value of another field: 22 (monthly_eur) -> 80 (data_gb)
  * Answer: The P‑30 plan costs €22 per month for a 24‑month contract with no setup fee, so the total cost over the whole contract is €80 × 24 = €528.
  * Finding: "528" is not in the tool results or the question, and they give no value close to it.
* **z28** · openai/gpt-oss-120b · value of another field: 22 (monthly_eur) -> 24 (contract_months)
  * Answer: The P‑30 plan costs €22 per month for a 24‑month contract with no setup fee, so the total cost over the whole contract is €24 × 24 = €528.
  * Finding: "528" is not in the tool results or the question, and they give no value close to it.
* **z28** · openai/gpt-oss-120b · value of another field: 24 (contract_months) -> 22 (monthly_eur)
  * Answer: The P‑30 plan costs €22 per month for a 24‑month contract with no setup fee, so the total cost over the whole contract is €22 × 22 = €528.
  * Finding: "528" is not in the tool results or the question, and they give no value close to it.
* **z28** · openai/gpt-oss-120b · value of another field: 24 (contract_months) -> 80 (data_gb)
  * Answer: The P‑30 plan costs €22 per month for a 24‑month contract with no setup fee, so the total cost over the whole contract is €22 × 80 = €528.
  * Finding: "528" is not in the tool results or the question, and they give no value close to it.
* **z28** · openai/gpt-oss-120b · two values swapped: 24 (contract_months) <-> 22 (monthly_eur)
  * Answer: The P‑30 plan costs €22 per month for a 22‑month contract with no setup fee, so the total cost over the whole contract is €24 × 24 = €528.
  * Finding: "528" is not in the tool results or the question, and they give no value close to it.
* **z08** · openai/gpt-oss-20b · value of another field: 250 (km_included_per_day) -> 52 (price_per_day_eur)
  * Answer: CR‑71 includes more kilometres per day. It offers 52 km/day versus 200 km/day for CR‑55, so it’s 50 km/day higher.
  * Finding: "50" is not in the tool results or the question. The closest values they give: 52.0 (get_car_rental (call 2)) or 38.0 (get_car_rental (call 1)).
* **z08** · openai/gpt-oss-20b · value of another field: 250 (km_included_per_day) -> 450 (deposit_eur)
  * Answer: CR‑71 includes more kilometres per day. It offers 450 km/day versus 200 km/day for CR‑55, so it’s 50 km/day higher.
  * Finding: "50" is not in the tool results or the question. The closest values they give: 52.0 (get_car_rental (call 2)) or 38.0 (get_car_rental (call 1)).
* **z08** · openai/gpt-oss-20b · value of another field: 200 (km_included_per_day) -> 38 (price_per_day_eur)
  * Answer: CR‑71 includes more kilometres per day. It offers 250 km/day versus 38 km/day for CR‑55, so it’s 50 km/day higher.
  * Finding: "50" is not in the tool results or the question. The closest values they give: 52.0 (get_car_rental (call 2)) or 38.0 (get_car_rental (call 1)).
