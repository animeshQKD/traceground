# Planted errors in real answers, 2026-11-19T09:58:44

Runs: 2026-11-17_groq_openai-gpt-oss-120b.jsonl, 2026-11-17_groq_openai-gpt-oss-20b.jsonl

327 planted errors in 35 real answers that are correct by hand and that traceground passes. The errors are planted, not made by the models.

| Kind | Planted | Caught | Flagged elsewhere | Missed | Caught by |
|---|---|---|---|---|---|
| digits swapped | 76 | 76 (100%) | 0 | 0 | number 36, value-to-field 40 |
| last digit off by one | 79 | 77 (97%) | 0 | 2 | number 37, value-to-field 40 |
| value of another field | 142 | 85 (60%) | 6 | 51 | value-to-field 85 |
| two values swapped | 26 | 20 (77%) | 3 | 3 | value-to-field 20 |
| fraction as percent | 4 | 4 (100%) | 0 | 0 | value-to-field 4 |
| all | 327 | 262 (80%) | 9 | 56 | number 73, value-to-field 189 |

Answers not used: h02 (openai/gpt-oss-120b): wrong by hand; h07 (openai/gpt-oss-120b): wrong by hand; h14 (openai/gpt-oss-120b): traceground says problems; h08 (openai/gpt-oss-20b): wrong by hand; h14 (openai/gpt-oss-20b): traceground says problems

## Missed (56)

* **h01** · openai/gpt-oss-120b · value of another field: 535 (duration_min) -> 6200 (distance_km)
  * Answer: Flight LH‑400 travels about 6,200 km and takes roughly 6200 minutes (about 8 hours 55 minutes).
* **h01** · openai/gpt-oss-120b · value of another field: 535 (duration_min) -> 25 (delay_min)
  * Answer: Flight LH‑400 travels about 6,200 km and takes roughly 25 minutes (about 8 hours 55 minutes).
* **h03** · openai/gpt-oss-120b · value of another field: 689.0 (price_eur) -> 6200 (distance_km)
  * Answer: LH‑400 costs €6200, while BA‑117 costs €812.5, so LH‑400 is the cheaper ticket.
* **h03** · openai/gpt-oss-120b · value of another field: 689.0 (price_eur) -> 535 (duration_min)
  * Answer: LH‑400 costs €535, while BA‑117 costs €812.5, so LH‑400 is the cheaper ticket.
* **h03** · openai/gpt-oss-120b · value of another field: 812.5 (price_eur) -> 5540 (distance_km)
  * Answer: LH‑400 costs €689.0, while BA‑117 costs €5540, so LH‑400 is the cheaper ticket.
* **h03** · openai/gpt-oss-120b · value of another field: 812.5 (price_eur) -> 495 (duration_min)
  * Answer: LH‑400 costs €689.0, while BA‑117 costs €495, so LH‑400 is the cheaper ticket.
* **h04** · openai/gpt-oss-120b · value of another field: 1,343.04 (total) -> 8 (items)
  * Answer: The invoice totals €8, of which €212.04 is tax.
* **h04** · openai/gpt-oss-120b · value of another field: 1,343.04 (total) -> 1,240 (subtotal)
  * Answer: The invoice totals €1,240, of which €212.04 is tax.
* **h04** · openai/gpt-oss-120b · value of another field: 212.04 (tax) -> 8 (items)
  * Answer: The invoice totals €1,343.04, of which €8 is tax.
* **h04** · openai/gpt-oss-120b · value of another field: 212.04 (tax) -> 1240 (subtotal)
  * Answer: The invoice totals €1,343.04, of which €1240 is tax.
* **h04** · openai/gpt-oss-120b · two values swapped: 1,343.04 (total) <-> 212.04 (tax)
  * Answer: The invoice totals €212.04, of which €1,343.04 is tax.
* **h08** · openai/gpt-oss-120b · last digit off by one: 2024 -> 2025
  * Answer: Nordwind’s revenue grew from $1,612.3 million in 2025 to $1,840.5 million in 2025, an increase of about $228.2 million.
* **h08** · openai/gpt-oss-120b · value of another field: 2024 (year) -> 1612.3 (revenue_musd)
  * Answer: Nordwind’s revenue grew from $1,612.3 million in 1612.3 to $1,840.5 million in 2025, an increase of about $228.2 million.
* **h08** · openai/gpt-oss-120b · value of another field: 2024 (year) -> 251.6 (operating_income_musd)
  * Answer: Nordwind’s revenue grew from $1,612.3 million in 251.6 to $1,840.5 million in 2025, an increase of about $228.2 million.
* **h08** · openai/gpt-oss-120b · value of another field: 2025 (year) -> 1840.5 (revenue_musd)
  * Answer: Nordwind’s revenue grew from $1,612.3 million in 2024 to $1,840.5 million in 1840.5, an increase of about $228.2 million.
* **h08** · openai/gpt-oss-120b · value of another field: 2025 (year) -> 312.9 (operating_income_musd)
  * Answer: Nordwind’s revenue grew from $1,612.3 million in 2024 to $1,840.5 million in 312.9, an increase of about $228.2 million.
* **h09** · openai/gpt-oss-120b · value of another field: 4,980 (employees) -> 2,024 (year)
  * Answer: Nordwind’s operating margin in 2024 was 15.6 % and it employed 2,024 people.
* **h09** · openai/gpt-oss-120b · value of another field: 4,980 (employees) -> 1,612.3 (revenue_musd)
  * Answer: Nordwind’s operating margin in 2024 was 15.6 % and it employed 1,612.3 people.
* **h10** · openai/gpt-oss-120b · value of another field: 310 (calories_kcal) -> 14.2 (protein_g)
  * Answer: A serving of dal tadka contains about 14.2 kcal and 14.2 g of protein.
* **h10** · openai/gpt-oss-120b · value of another field: 310 (calories_kcal) -> 9.8 (fat_g)
  * Answer: A serving of dal tadka contains about 9.8 kcal and 14.2 g of protein.
* **h12** · openai/gpt-oss-120b · value of another field: 5.2 (fiber_g) -> 840 (calories_kcal)
  * Answer: Dal tadka provides about 8.1 g of fiber per serving, while margherita pizza has about 840 g. So dal tadka has more fiber.
* **h12** · openai/gpt-oss-120b · value of another field: 5.2 (fiber_g) -> 34 (protein_g)
  * Answer: Dal tadka provides about 8.1 g of fiber per serving, while margherita pizza has about 34 g. So dal tadka has more fiber.
* **h17** · openai/gpt-oss-120b · last digit off by one: 14.5 -> 14.6
  * Answer: Shipping a 2 kg parcel costs €7.3 to Germany and €14.6 to the United States.
  * Finding: "14.6" is not in the tool results or the question; it is 7.3 (get_shipping_quote (call 1)) × 2 (the question), worked out in the answer rather than by a tool.
* **h17** · openai/gpt-oss-120b · value of another field: 14.5 (cost_eur) -> 2 (weight_kg)
  * Answer: Shipping a 2 kg parcel costs €7.3 to Germany and €2 to the United States.
* **h17** · openai/gpt-oss-120b · value of another field: 14.5 (cost_eur) -> 4 (days_min)
  * Answer: Shipping a 2 kg parcel costs €7.3 to Germany and €4 to the United States.
* **h19** · openai/gpt-oss-120b · value of another field: 10,910 (density_per_km2) -> 522,250 (population)
  * Answer: Lyon is more densely populated, with about 522,250 people per km² versus Pune’s roughly 9,432 people per km².
* **h19** · openai/gpt-oss-120b · value of another field: 10,910 (density_per_km2) -> 47.87 (area_km2)
  * Answer: Lyon is more densely populated, with about 47.87 people per km² versus Pune’s roughly 9,432 people per km².
* **h19** · openai/gpt-oss-120b · value of another field: 9,432 (density_per_km2) -> 3,124,458 (population)
  * Answer: Lyon is more densely populated, with about 10,910 people per km² versus Pune’s roughly 3,124,458 people per km².
* **h19** · openai/gpt-oss-120b · value of another field: 9,432 (density_per_km2) -> 331.26 (area_km2)
  * Answer: Lyon is more densely populated, with about 10,910 people per km² versus Pune’s roughly 331.26 people per km².
* **h01** · openai/gpt-oss-20b · value of another field: 535 (duration_min) -> 6200 (distance_km)
  * Answer: Flight LH‑400 runs from Frankfurt (FRA) to New York JFK. It covers roughly 6,200 km and takes about 6200 minutes (≈8 h 55 min) of flight time.
* **h01** · openai/gpt-oss-20b · value of another field: 535 (duration_min) -> 25 (delay_min)
  * Answer: Flight LH‑400 runs from Frankfurt (FRA) to New York JFK. It covers roughly 6,200 km and takes about 25 minutes (≈8 h 55 min) of flight time.
* **h02** · openai/gpt-oss-20b · value of another field: 45 (delay_min) -> 11760 (distance_km)
  * Answer: AI‑101 is scheduled to depart 11760 minutes late, and there are 27 seats still available.
* **h02** · openai/gpt-oss-20b · value of another field: 45 (delay_min) -> 960 (duration_min)
  * Answer: AI‑101 is scheduled to depart 960 minutes late, and there are 27 seats still available.
* **h02** · openai/gpt-oss-20b · value of another field: 27 (seats_left) -> 11760 (distance_km)
  * Answer: AI‑101 is scheduled to depart 45 minutes late, and there are 11760 seats still available.
* **h02** · openai/gpt-oss-20b · value of another field: 27 (seats_left) -> 960 (duration_min)
  * Answer: AI‑101 is scheduled to depart 45 minutes late, and there are 960 seats still available.
* **h02** · openai/gpt-oss-20b · two values swapped: 45 (delay_min) <-> 27 (seats_left)
  * Answer: AI‑101 is scheduled to depart 27 minutes late, and there are 45 seats still available.
* **h03** · openai/gpt-oss-20b · value of another field: 689.00 (price_eur) -> 6200 (distance_km)
  * Answer: LH‑400 is cheaper. It costs €6200, whereas BA‑117 costs €812.50.
* **h03** · openai/gpt-oss-20b · value of another field: 689.00 (price_eur) -> 535 (duration_min)
  * Answer: LH‑400 is cheaper. It costs €535, whereas BA‑117 costs €812.50.
* **h03** · openai/gpt-oss-20b · value of another field: 812.50 (price_eur) -> 5540 (distance_km)
  * Answer: LH‑400 is cheaper. It costs €689.00, whereas BA‑117 costs €5540.
* **h03** · openai/gpt-oss-20b · value of another field: 812.50 (price_eur) -> 495 (duration_min)
  * Answer: LH‑400 is cheaper. It costs €689.00, whereas BA‑117 costs €495.
* **h04** · openai/gpt-oss-20b · value of another field: 212.04 (tax) -> 8 (items)
  * Answer: The total amount on invoice INV‑1001 is €1,343.04, of which €8 is tax.
* **h04** · openai/gpt-oss-20b · value of another field: 212.04 (tax) -> 1240 (subtotal)
  * Answer: The total amount on invoice INV‑1001 is €1,343.04, of which €1240 is tax.
* **h06** · openai/gpt-oss-20b · value of another field: 468.65 (total) -> 3 (items)
  * Answer: The invoice **INV‑1002** lists a shipping charge of **€9.90**. Including that, the total amount due is **€3**.
* **h06** · openai/gpt-oss-20b · value of another field: 468.65 (total) -> 385.5 (subtotal)
  * Answer: The invoice **INV‑1002** lists a shipping charge of **€9.90**. Including that, the total amount due is **€385.5**.
* **h07** · openai/gpt-oss-20b · value of another field: 2025 (year) -> 1840.5 (revenue_musd)
  * Answer: Nordwind reported a 1840.5 revenue of **$1,840.5 million** and a net income of **$221.4 million**.
* **h07** · openai/gpt-oss-20b · value of another field: 1,840.5 (revenue_musd) -> 2,025 (year)
  * Answer: Nordwind reported a 2025 revenue of **$2,025 million** and a net income of **$221.4 million**.
* **h07** · openai/gpt-oss-20b · value of another field: 1,840.5 (revenue_musd) -> 312.9 (operating_income_musd)
  * Answer: Nordwind reported a 2025 revenue of **$312.9 million** and a net income of **$221.4 million**.
* **h07** · openai/gpt-oss-20b · two values swapped: 2025 (year) <-> 1,840.5 (revenue_musd)
  * Answer: Nordwind reported a 1,840.5 revenue of **$2025 million** and a net income of **$221.4 million**.
* **h09** · openai/gpt-oss-20b · value of another field: 4,980 (employees) -> 2,024 (year)
  * Answer: Nordwind’s operating margin in 2024 was **15.6 %**, and the company employed **2,024** people.
* **h09** · openai/gpt-oss-20b · value of another field: 4,980 (employees) -> 1,612.3 (revenue_musd)
  * Answer: Nordwind’s operating margin in 2024 was **15.6 %**, and the company employed **1,612.3** people.
* **h10** · openai/gpt-oss-20b · value of another field: 310 (calories_kcal) -> 14.2 (protein_g)
  * Answer: A single serving of dal tadka contains roughly **14.2 kcal** and **14.2 g of protein**.
* **h10** · openai/gpt-oss-20b · value of another field: 310 (calories_kcal) -> 9.8 (fat_g)
  * Answer: A single serving of dal tadka contains roughly **9.8 kcal** and **14.2 g of protein**.
* **h11** · openai/gpt-oss-20b · value of another field: 98 (carbs_g) -> 840 (calories_kcal)
  * Answer: A single serving of margherita pizza contains about **32.5 g of fat** and **840 g of carbohydrates**.
* **h11** · openai/gpt-oss-20b · value of another field: 98 (carbs_g) -> 34 (protein_g)
  * Answer: A single serving of margherita pizza contains about **32.5 g of fat** and **34 g of carbohydrates**.
* **h12** · openai/gpt-oss-20b · value of another field: 5.2 (fiber_g) -> 840 (calories_kcal)
  * Answer: Dal tadka contains about 8.1 g of fiber per serving, whereas a margherita pizza has roughly 840 g. So dal tadka has more fiber per serving.
* **h12** · openai/gpt-oss-20b · value of another field: 5.2 (fiber_g) -> 34 (protein_g)
  * Answer: Dal tadka contains about 8.1 g of fiber per serving, whereas a margherita pizza has roughly 34 g. So dal tadka has more fiber per serving.

## Flagged elsewhere (9)

* **h08** · openai/gpt-oss-120b · value of another field: 1,612.3 (revenue_musd) -> 2,024 (year)
  * Answer: Nordwind’s revenue grew from $2,024 million in 2024 to $1,840.5 million in 2025, an increase of about $228.2 million.
  * Finding: "228.2 million" is not in the tool results or the question. The closest values they give: 221.4 (get_company_financials (call 2)) or 251.6 (get_company_financials (call 1)).
* **h08** · openai/gpt-oss-120b · value of another field: 1,612.3 (revenue_musd) -> 251.6 (operating_income_musd)
  * Answer: Nordwind’s revenue grew from $251.6 million in 2024 to $1,840.5 million in 2025, an increase of about $228.2 million.
  * Finding: "228.2 million" is not in the tool results or the question. The closest values they give: 221.4 (get_company_financials (call 2)) or 251.6 (get_company_financials (call 1)).
* **h08** · openai/gpt-oss-120b · value of another field: 1,840.5 (revenue_musd) -> 2,025 (year)
  * Answer: Nordwind’s revenue grew from $1,612.3 million in 2024 to $2,025 million in 2025, an increase of about $228.2 million.
  * Finding: "228.2 million" is not in the tool results or the question. The closest values they give: 221.4 (get_company_financials (call 2)) or 251.6 (get_company_financials (call 1)).
* **h08** · openai/gpt-oss-120b · value of another field: 1,840.5 (revenue_musd) -> 312.9 (operating_income_musd)
  * Answer: Nordwind’s revenue grew from $1,612.3 million in 2024 to $312.9 million in 2025, an increase of about $228.2 million.
  * Finding: "228.2 million" is not in the tool results or the question. The closest values they give: 221.4 (get_company_financials (call 2)) or 251.6 (get_company_financials (call 1)).
* **h08** · openai/gpt-oss-120b · two values swapped: 1,612.3 (revenue_musd) <-> 2024 (year)
  * Answer: Nordwind’s revenue grew from $2024 million in 1,612.3 to $1,840.5 million in 2025, an increase of about $228.2 million.
  * Finding: "228.2 million" is not in the tool results or the question. The closest values they give: 221.4 (get_company_financials (call 2)) or 251.6 (get_company_financials (call 1)).
* **h08** · openai/gpt-oss-120b · two values swapped: 1,612.3 (revenue_musd) <-> 2025 (year)
  * Answer: Nordwind’s revenue grew from $2025 million in 2024 to $1,840.5 million in 1,612.3, an increase of about $228.2 million.
  * Finding: "228.2 million" is not in the tool results or the question. The closest values they give: 221.4 (get_company_financials (call 2)) or 251.6 (get_company_financials (call 1)).
* **h08** · openai/gpt-oss-120b · two values swapped: 2024 (year) <-> 1,840.5 (revenue_musd)
  * Answer: Nordwind’s revenue grew from $1,612.3 million in 1,840.5 to $2024 million in 2025, an increase of about $228.2 million.
  * Finding: "228.2 million" is not in the tool results or the question. The closest values they give: 221.4 (get_company_financials (call 2)) or 251.6 (get_company_financials (call 1)).
* **h15** · openai/gpt-oss-20b · value of another field: 1009.3 (pressure_hpa) -> 19.8 (temperature_c)
  * Answer: LAB‑1 reports a pressure of **1012.6 hPa**, while LAB‑2 reports **19.8 hPa**. Thus LAB‑1’s air pressure is about **3.3 hPa higher** than LAB‑2’s.
  * Finding: "3.3" is not in the tool results or the question, and they give no value close to it.
* **h15** · openai/gpt-oss-20b · value of another field: 1009.3 (pressure_hpa) -> 55 (humidity_pct)
  * Answer: LAB‑1 reports a pressure of **1012.6 hPa**, while LAB‑2 reports **55 hPa**. Thus LAB‑1’s air pressure is about **3.3 hPa higher** than LAB‑2’s.
  * Finding: "3.3" is not in the tool results or the question, and they give no value close to it.
