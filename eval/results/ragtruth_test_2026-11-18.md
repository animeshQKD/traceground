# RAGTruth, test split (2026-11-18, traceground 0.1.0.dev12)

Answers rated good by RAGTruth. A finding is high severity unless stated. "Marked" = a span the
RAGTruth annotators marked as a hallucination. Texts are not included: see eval/ragtruth.py.

| Task | Answers | With a marked span | Flagged | Flagged and marked | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| QA | 875 | 160 | 34 | 26 | 0.765 | 0.163 | 0.268 |
| Summary | 900 | 204 | 41 | 24 | 0.585 | 0.118 | 0.196 |
| Data2txt | 900 | 579 | 51 | 46 | 0.902 | 0.079 | 0.146 |

| Task | Marked spans with a digit | of them flagged | High findings | on a marked span |
|---|---|---|---|---|
| QA | 104 | 29 | 74 | 62 |
| Summary | 51 | 22 | 44 | 25 |
| Data2txt | 151 | 34 | 54 | 36 |

High findings by check (on a marked span / on none):

* QA: number 57/4, quote 5/4, self-contradiction 0/4
* Summary: number 25/15, quote 0/4
* Data2txt: number 35/9, quote 1/8, value-to-field 0/1

RAGTruth ids of answers flagged with no marked span (for a person to check):

* QA: 11907, 12704, 13908, 14054, 14212, 16154, 17056, 17059
* Summary: 349, 436, 590, 591, 614, 615, 617, 1053, 1236, 1518, 1566, 2424, 4067, 4224, 4226, 4227, 4264
* Data2txt: 8418, 9202, 9203, 10072, 10363
