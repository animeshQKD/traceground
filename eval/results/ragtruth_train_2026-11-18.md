# RAGTruth, train split (2026-11-18, traceground 0.1.0.dev12)

Answers rated good by RAGTruth. A finding is high severity unless stated. "Marked" = a span the
RAGTruth annotators marked as a hallucination. Texts are not included: see eval/ragtruth.py.

| Task | Answers | With a marked span | Flagged | Flagged and marked | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| QA | 4892 | 1546 | 228 | 178 | 0.781 | 0.115 | 0.201 |
| Summary | 4755 | 1480 | 278 | 217 | 0.781 | 0.147 | 0.247 |
| Data2txt | 5295 | 3672 | 262 | 255 | 0.973 | 0.069 | 0.130 |

| Task | Marked spans with a digit | of them flagged | High findings | on a marked span |
|---|---|---|---|---|
| QA | 1145 | 191 | 494 | 321 |
| Summary | 403 | 174 | 317 | 201 |
| Data2txt | 1073 | 196 | 287 | 211 |

High findings by check (on a marked span / on none):

* QA: number 287/142, quote 34/22, self-contradiction 0/9
* Summary: number 192/89, quote 9/27
* Data2txt: number 207/25, quote 4/47, value-to-field 0/4

RAGTruth ids of answers flagged with no marked span (for a person to check):

* QA: 11919, 12038, 12122, 12123, 12267, 12268, 12326, 12375, 12467, 12477, 12652, 12658, 12737, 12779, 12857, 13055, 13177, 13526, 13551, 13557, 13571, 13798, 13894, 14157, 14328, 14476, 14619, 14989, 14992, 15190, 15232, 15285, 15435, 16005, 16083, 16200, 16252, 16335, 16406, 16407, 16408, 16425, 16731, 16732, 16845, 17241, 17315, 17422, 17541, 17721
* Summary: 48, 49, 174, 228, 306, 375, 399, 495, 496, 497, 516, 624, 629, 630, 756, 762, 912, 984, 1010, 1165, 1322, 1388, 1497, 1505, 1737, 1804, 2001, 2021, 2029, 2063, 2178, 2491, 2574, 2688, 2701, 2732, 2815, 2844, 2952, 3114, 3142, 3186, 3192, 3216, 3295, 3443, 3465, 3484, 3687, 3729, 4336, 4458, 4516, 4894, 5130, 5131, 5133, 5134, 5135, 5548, 5551
* Data2txt: 7813, 8647, 11247, 11353, 11430, 11431, 11622
