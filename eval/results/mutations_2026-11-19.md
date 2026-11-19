# Planted errors in real answers, 2026-11-19T09:58:34

Runs: 2026-11-17_groq_openai-gpt-oss-120b.jsonl, 2026-11-17_groq_openai-gpt-oss-20b.jsonl

657 planted errors in 74 real answers that are correct by hand and that traceground passes. The errors are planted, not made by the models.

| Kind | Planted | Caught | Flagged elsewhere | Missed | Caught by |
|---|---|---|---|---|---|
| digits swapped | 179 | 177 (99%) | 0 | 2 | number 96, value-to-field 81 |
| last digit off by one | 209 | 209 (100%) | 0 | 0 | number 115, value-to-field 94 |
| value of another field | 197 | 147 (75%) | 1 | 49 | value-to-field 147 |
| two values swapped | 47 | 46 (98%) | 0 | 1 | value-to-field 46 |
| fraction as percent | 25 | 21 (84%) | 0 | 4 | number 16, value-to-field 5 |
| all | 657 | 600 (91%) | 1 | 56 | number 227, value-to-field 373 |

Answers not used: k03 (openai/gpt-oss-120b): wrong by hand

## Missed (56)

* **f03** · openai/gpt-oss-120b · value of another field: 10,789.52 (total_paid) -> 299.71 (monthly_payment)
  * Answer: The 3‑year loan costs about $299.71 total, while the 5‑year loan costs about $11,322.74 total.
* **f03** · openai/gpt-oss-120b · value of another field: 10,789.52 (total_paid) -> 789.52 (total_interest)
  * Answer: The 3‑year loan costs about $789.52 total, while the 5‑year loan costs about $11,322.74 total.
* **f03** · openai/gpt-oss-120b · value of another field: 11,322.74 (total_paid) -> 188.71 (monthly_payment)
  * Answer: The 3‑year loan costs about $10,789.52 total, while the 5‑year loan costs about $188.71 total.
* **f03** · openai/gpt-oss-120b · value of another field: 11,322.74 (total_paid) -> 1,322.74 (total_interest)
  * Answer: The 3‑year loan costs about $10,789.52 total, while the 5‑year loan costs about $1,322.74 total.
* **f04** · openai/gpt-oss-120b · value of another field: 14,256.86 (total_paid) -> 237.61 (monthly_payment)
  * Answer: The 5‑year loan at 7 % interest on a €12,000 principal costs about €237.61 in total, which includes roughly €2,256.86 of interest, with a monthly payment of €237.61.
* **f04** · openai/gpt-oss-120b · value of another field: 14,256.86 (total_paid) -> 2,256.86 (total_interest)
  * Answer: The 5‑year loan at 7 % interest on a €12,000 principal costs about €2,256.86 in total, which includes roughly €2,256.86 of interest, with a monthly payment of €237.61.
* **f05** · openai/gpt-oss-120b · value of another field: 7,454.16 (final_amount) -> 2,454.16 (interest_earned)
  * Answer: The investment will grow to about **$2,454.16**, meaning you’d earn roughly **$2,454.16** in interest over the 10‑year period.
* **f09** · openai/gpt-oss-120b · value of another field: 476.22 (monthly_payment) -> 34287.9 (total_paid)
  * Answer: The monthly payment for a $30,000 loan at 4.5% is about $892.41 over 3 years (total paid $32,126.68, interest $2,126.68), and about $34287.9 over 6 years (total paid $34,287.90, interest $4,287.90).
* **f09** · openai/gpt-oss-120b · value of another field: 476.22 (monthly_payment) -> 4287.9 (total_interest)
  * Answer: The monthly payment for a $30,000 loan at 4.5% is about $892.41 over 3 years (total paid $32,126.68, interest $2,126.68), and about $4287.9 over 6 years (total paid $34,287.90, interest $4,287.90).
* **c02** · openai/gpt-oss-120b · value of another field: 40,984 (converted_amount) -> 163.934426 (rate)
  * Answer: 250 EUR is about 163.934426 JPY.
* **c03** · openai/gpt-oss-120b · value of another field: 17.77 (converted_amount) -> 0.011848 (rate)
  * Answer: 1,500 INR is about $0.011848 USD.
* **w02** · openai/gpt-oss-120b · value of another field: 14 (high_c) -> 20 (rain_chance_pct)
  * Answer: Tomorrow’s high will be about 20 °C in Paris versus roughly 21 °C in Rome.
* **w02** · openai/gpt-oss-120b · digits swapped: 21 -> 12
  * Answer: Tomorrow’s high will be about 14 °C in Paris versus roughly 12 °C in Rome.
* **w02** · openai/gpt-oss-120b · value of another field: 21 (high_c) -> 13 (low_c)
  * Answer: Tomorrow’s high will be about 14 °C in Paris versus roughly 13 °C in Rome.
* **w02** · openai/gpt-oss-120b · value of another field: 21 (high_c) -> 5 (rain_chance_pct)
  * Answer: Tomorrow’s high will be about 14 °C in Paris versus roughly 5 °C in Rome.
* **p03** · openai/gpt-oss-120b · value of another field: 18 (battery_hours) -> 249 (price_usd)
  * Answer: The MX‑200 runs for about 249 hours on a charge, while the LT‑50 runs for about 30 hours, so the LT‑50 lasts longer.
* **p03** · openai/gpt-oss-120b · value of another field: 18 (battery_hours) -> 1.35 (weight_kg)
  * Answer: The MX‑200 runs for about 1.35 hours on a charge, while the LT‑50 runs for about 30 hours, so the LT‑50 lasts longer.
* **p03** · openai/gpt-oss-120b · value of another field: 30 (battery_hours) -> 39.9 (price_usd)
  * Answer: The MX‑200 runs for about 18 hours on a charge, while the LT‑50 runs for about 39.9 hours, so the LT‑50 lasts longer.
* **p03** · openai/gpt-oss-120b · value of another field: 30 (battery_hours) -> 0.6 (weight_kg)
  * Answer: The MX‑200 runs for about 18 hours on a charge, while the LT‑50 runs for about 0.6 hours, so the LT‑50 lasts longer.
* **p06** · openai/gpt-oss-120b · value of another field: 165.14 (converted_amount) -> 0.92 (rate)
  * Answer: The QX‑9 costs about €0.92.
* **s01** · openai/gpt-oss-120b · fraction as percent: 52.2% -> 0.522%
  * Answer: Jordan Reyes scored 27 points, grabbed 11 rebounds, dished out 7 assists, played 34 minutes, and shot 0.522% from the field on 2026‑11‑16.
* **s02** · openai/gpt-oss-120b · fraction as percent: 47.1% -> 0.471%
  * Answer: Maya Chen shot 0.471% from the field on 2026‑11‑16.
* **s03** · openai/gpt-oss-120b · value of another field: 31 (points) -> 8 (rebounds)
  * Answer: Sam Okafor scored more points (8) than Jordan Reyes (27) on 2026‑11‑16.
* **s03** · openai/gpt-oss-120b · value of another field: 31 (points) -> 3 (assists)
  * Answer: Sam Okafor scored more points (3) than Jordan Reyes (27) on 2026‑11‑16.
* **s03** · openai/gpt-oss-120b · value of another field: 27 (points) -> 11 (rebounds)
  * Answer: Sam Okafor scored more points (31) than Jordan Reyes (11) on 2026‑11‑16.
* **s03** · openai/gpt-oss-120b · value of another field: 27 (points) -> 7 (assists)
  * Answer: Sam Okafor scored more points (31) than Jordan Reyes (7) on 2026‑11‑16.
* **f03** · openai/gpt-oss-20b · value of another field: 10,789.52 (total_paid) -> 299.71 (monthly_payment)
  * Answer: For a €10,000 loan at 5 % annual interest, the total paid over 3 years is €299.71 (about €789.52 in interest), while over 5 years the total paid rises to €11,322.74 (about €1,322.74 in interest). The longer term adds roughly €533.22 in extra interest and €533.22 in total payments.
* **f03** · openai/gpt-oss-20b · value of another field: 10,789.52 (total_paid) -> 789.52 (total_interest)
  * Answer: For a €10,000 loan at 5 % annual interest, the total paid over 3 years is €789.52 (about €789.52 in interest), while over 5 years the total paid rises to €11,322.74 (about €1,322.74 in interest). The longer term adds roughly €533.22 in extra interest and €533.22 in total payments.
* **f04** · openai/gpt-oss-20b · value of another field: 14,256.86 (total_paid) -> 237.61 (monthly_payment)
  * Answer: The 5‑year amortised loan of €12,000 at a 7 % annual interest rate works out to a monthly payment of **€237.61**. Over the 60 months you’ll pay a total of **€237.61**, of which **€2,256.86** is interest.
* **f04** · openai/gpt-oss-20b · value of another field: 14,256.86 (total_paid) -> 2,256.86 (total_interest)
  * Answer: The 5‑year amortised loan of €12,000 at a 7 % annual interest rate works out to a monthly payment of **€237.61**. Over the 60 months you’ll pay a total of **€2,256.86**, of which **€2,256.86** is interest.
* **f04** · openai/gpt-oss-20b · value of another field: 2,256.86 (total_interest) -> 237.61 (monthly_payment)
  * Answer: The 5‑year amortised loan of €12,000 at a 7 % annual interest rate works out to a monthly payment of **€237.61**. Over the 60 months you’ll pay a total of **€14,256.86**, of which **€237.61** is interest.
* **f04** · openai/gpt-oss-20b · value of another field: 2,256.86 (total_interest) -> 14,256.86 (total_paid)
  * Answer: The 5‑year amortised loan of €12,000 at a 7 % annual interest rate works out to a monthly payment of **€237.61**. Over the 60 months you’ll pay a total of **€14,256.86**, of which **€14,256.86** is interest.
* **f04** · openai/gpt-oss-20b · two values swapped: 14,256.86 (total_paid) <-> 2,256.86 (total_interest)
  * Answer: The 5‑year amortised loan of €12,000 at a 7 % annual interest rate works out to a monthly payment of **€237.61**. Over the 60 months you’ll pay a total of **€2,256.86**, of which **€14,256.86** is interest.
* **f05** · openai/gpt-oss-20b · value of another field: 7,454.16 (final_amount) -> 2,454.16 (interest_earned)
  * Answer: Investing €5,000 at a 4 % annual rate compounded monthly for 10 years will grow to about €2,454.16, meaning you’ll earn roughly €2,454.16 in interest.
* **f06** · openai/gpt-oss-20b · value of another field: 9,860.41 (final_amount) -> 1,860.41 (interest_earned)
  * Answer: Using a 3.5 % annual rate compounded quarterly, an €8,000 deposit grows to about €1,860.41 over six years. That means the interest earned is roughly €1,860.41.
* **f06** · openai/gpt-oss-20b · value of another field: 1,860.41 (interest_earned) -> 9,860.41 (final_amount)
  * Answer: Using a 3.5 % annual rate compounded quarterly, an €8,000 deposit grows to about €9,860.41 over six years. That means the interest earned is roughly €9,860.41.
* **f07** · openai/gpt-oss-20b · value of another field: 18,139.09 (total_paid) -> 503.86 (monthly_payment)
  * Answer: The monthly payment on an €18,000 loan at a 0.5 % annual interest rate over 3 years is **€503.86**. Over the 36‑month term you’ll pay a total of **€503.86**, which includes **€139.09** in interest.
* **f07** · openai/gpt-oss-20b · value of another field: 18,139.09 (total_paid) -> 139.09 (total_interest)
  * Answer: The monthly payment on an €18,000 loan at a 0.5 % annual interest rate over 3 years is **€503.86**. Over the 36‑month term you’ll pay a total of **€139.09**, which includes **€139.09** in interest.
* **f08** · openai/gpt-oss-20b · value of another field: 10,732.75 (total_paid) -> 447.2 (monthly_payment)
  * Answer: The monthly payment is about €447.20. Over the 24‑month term you’ll pay a total of **€447.2**, which includes **€1,232.75** in interest.
* **f08** · openai/gpt-oss-20b · value of another field: 10,732.75 (total_paid) -> 1,232.75 (total_interest)
  * Answer: The monthly payment is about €447.20. Over the 24‑month term you’ll pay a total of **€1,232.75**, which includes **€1,232.75** in interest.
* **c02** · openai/gpt-oss-20b · value of another field: 40 983.61 (converted_amount) -> 163.934426 (rate)
  * Answer: 250 € is about 163.934426 ¥ (using the current exchange rate of roughly 163.93 ¥ per €).
* **c03** · openai/gpt-oss-20b · value of another field: 17.77 (converted_amount) -> 0.011848 (rate)
  * Answer: 1,500 INR is about $0.011848 USD (using the current exchange rate of roughly 0.01185 USD per INR).
* **w02** · openai/gpt-oss-20b · digits swapped: 21 -> 12
  * Answer: Tomorrow’s forecast shows Paris will reach a high of 14 °C, while Rome is expected to climb to 12 °C. Rome’s temperature will be 7 °C warmer than Paris’s.
* **w02** · openai/gpt-oss-20b · value of another field: 21 (high_c) -> 13 (low_c)
  * Answer: Tomorrow’s forecast shows Paris will reach a high of 14 °C, while Rome is expected to climb to 13 °C. Rome’s temperature will be 7 °C warmer than Paris’s.
* **w02** · openai/gpt-oss-20b · value of another field: 21 (high_c) -> 5 (rain_chance_pct)
  * Answer: Tomorrow’s forecast shows Paris will reach a high of 14 °C, while Rome is expected to climb to 5 °C. Rome’s temperature will be 7 °C warmer than Paris’s.
* **p03** · openai/gpt-oss-20b · value of another field: 30 (battery_hours) -> 39.9 (price_usd)
  * Answer: The LT‑50 lamp has a longer battery life—39.9 hours versus the MX‑200 speaker’s 18 hours.
* **p03** · openai/gpt-oss-20b · value of another field: 30 (battery_hours) -> 0.6 (weight_kg)
  * Answer: The LT‑50 lamp has a longer battery life—0.6 hours versus the MX‑200 speaker’s 18 hours.
* **p03** · openai/gpt-oss-20b · value of another field: 18 (battery_hours) -> 249 (price_usd)
  * Answer: The LT‑50 lamp has a longer battery life—30 hours versus the MX‑200 speaker’s 249 hours.
* **p03** · openai/gpt-oss-20b · value of another field: 18 (battery_hours) -> 1.35 (weight_kg)
  * Answer: The LT‑50 lamp has a longer battery life—30 hours versus the MX‑200 speaker’s 1.35 hours.
* **p06** · openai/gpt-oss-20b · value of another field: 165.14 (converted_amount) -> 0.92 (rate)
  * Answer: The QX‑9 headphones cost €0.92.
* **s01** · openai/gpt-oss-20b · fraction as percent: 52.2% -> 0.522%
  * Answer: On November 16, 2026, Jordan Reyes delivered a strong performance, scoring 27 points, grabbing 11 rebounds, and dishing out 7 assists over 34 minutes. He shot 0.522 % from the field, contributing significantly to his team’s offensive output.
* **s02** · openai/gpt-oss-20b · fraction as percent: 47.1% -> 0.471%
  * Answer: Maya Chen’s field‑goal percentage on 2026‑11‑16 was **0.471 %**.
* **s03** · openai/gpt-oss-20b · value of another field: 27 (points) -> 11 (rebounds)
  * Answer: On November 16, 2026 Sam Okafor scored 31 points, while Jordan Reyes scored 11, so Okafor had the higher point total.
* **s03** · openai/gpt-oss-20b · value of another field: 27 (points) -> 7 (assists)
  * Answer: On November 16, 2026 Sam Okafor scored 31 points, while Jordan Reyes scored 7, so Okafor had the higher point total.
* **k01** · openai/gpt-oss-20b · value of another field: 189.50 (price) -> -1.2 (change_pct)
  * Answer: ACME’s share is trading at **$-1.2** today, down **1.2 %** from the previous close.
* **k01** · openai/gpt-oss-20b · value of another field: 189.50 (price) -> 51200000 (volume)
  * Answer: ACME’s share is trading at **$51200000** today, down **1.2 %** from the previous close.

## Flagged elsewhere (1)

* **c04** · openai/gpt-oss-120b · value of another field: 234 (converted_amount) -> 1.17 (rate)
  * Answer: The two amounts convert to about 315 EUR (from 300 CHF) and 1.17 EUR (from 200 GBP), giving a total of roughly 549 EUR.
  * Finding: "549" is not in the tool results or the question. The closest values they give: 315.0 (convert_currency (call 1)) or 300 (convert_currency (call 1)).
