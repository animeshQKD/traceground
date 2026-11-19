# RAGTruth test split: hand review of the findings on no marked span (2026-11-18, traceground 0.1.0.dev12)

The test split was measured once, with the code frozen after development on the train split
(`ragtruth_test_2026-11-18.md`). traceground made 172 high findings on the 2,675 answers: 123 fall on a span
the RAGTruth annotators marked, 49 on none. All 49 were checked by hand against the source, with
`python ragtruth.py --split test --review 30` (the texts stay in eval/data/, outside git). The reasons below
are in our words; no RAGTruth text is reproduced. The 123 findings on a marked span were not checked one by
one: a person had marked that span as a hallucination.

| Category | QA | Summary | Data2txt | All |
|---|---|---|---|---|
| A. Contradicts the source, or a quote the source does not have | 2 | 1 | 10 | 13 |
| A2. A quote reworded, the meaning kept (not word for word) | 1 | 3 | 2 | 6 |
| B. A number the source does not give at all (outside knowledge, inference or invention) | 4 | 12 | 3 | 19 |
| C. False alarm: traceground is wrong | 1 | 3 | 3 | 7 |
| D. Unclear | 4 | 0 | 0 | 4 |
| Total | 12 | 19 | 18 | 49 |

RAGTruth's guidelines count information the source does not give as a hallucination ("baseless
information"), so B is within what the annotators were asked to mark; many such numbers are true facts the
model knew (a safe cooking temperature, a jury of 12, the year of a well-known event), and a reader cannot
tell them from invented ones without another source. Taken together, 7 of the 172 high findings (4%) are
false alarms and 4 more (2%) unclear.

## Every finding

QA

| Id | Check | Category | Why |
|---|---|---|---|
| 13908 | quote | A2 | one verb changed in form |
| 12704 | number | B | the lower end of a cooking time; the source gives only the upper end |
| 14054 | number | B | a safe meat temperature the passages do not give |
| 11907 | self-contradiction | D | says "the passage" lacks the pay figures, then gives them from passage 2 (two findings) |
| 16154 | quote | A | a phrase in quote marks that no passage has |
| 13163 | number | B | an oven temperature the passages do not give |
| 14397 | self-contradiction | A | says the passages say nothing on the point, then cites passage 3 on it |
| 17056 | quote | D | the answer's own definition put in quote marks, not attributed |
| 13161 | number | B | the upper end of a basting time the passages do not give |
| 17059 | self-contradiction | C | the side effects are not in the passages; the next sentence gives benefits, a different thing |
| 14212 | quote | D | the answer's own sentence put in quote marks, not attributed |

Summary

| Id | Check | Category | Why |
|---|---|---|---|
| 349 | quote | A2 | one word left out of the quotation |
| 436 | number | B | a victim's age the article does not give |
| 2424 | number | B | a release date the article does not give |
| 4226 | number | B | an earlier benefit amount the article does not give |
| 4264 | number | C | the answer's own word count ("within 83 words"), too far from "summary" for the rule |
| 590 | quote | C | a censored word written with other symbols |
| 4067 | number | B | a season year the article does not give |
| 1053 | number | B | a count of survivors the article does not give |
| 615, 614, 617 | number | B | the size of the jury, which the article does not give (three answers) |
| 348 | number | B | the year of a historical event the article does not give |
| 1826 | number | B | "almost 50 years", which the article does not give |
| 4224, 4227 | number | B | a year inferred from "last year" (two answers) |
| 1518, 1566 | quote | A2 | two parts of one statement joined, without the words between them (two answers) |
| 591 | number | A | the wrong year for a campaign the article dates by another election |
| 1236 | number | C | "29,200km" read as 29: a number with a unit glued after a thousands separator |

Data2txt

| Id | Check | Category | Why |
|---|---|---|---|
| 7264 | number | B | an opening year the data does not give |
| 6171 | number | A | an average of the reviews that the review ratings do not give |
| 7025 | quote | A | a quotation no review has |
| 10363, 10364, 7236 | number | A | 10:30 in 24-hour data is the morning; the answers say 10:30 PM (three answers) |
| 6778 | quote | A | a quotation that changes the review's words |
| 8418 | value-to-field | C | "a mixed review of 3.5 stars" is the business rating, which the answer gives correctly |
| 9158 | number | A | a review count that differs from the data |
| 10072 | number | B | menu prices the data does not give |
| 9203 | quote | A | a word added inside the quotation |
| 5686 | quote | A2 | a quotation reworded ("we" to "they", a noun dropped) |
| 9202 | quote | A2 | a word added inside the quotation |
| 7159 | number | C | "11:0 PM" (the data's own minute format) is 23:00, as the data says; the rule did not read it |
| 9158 | number | B | percentages of the reviews that the data does not give |
| 6934 | quote | A | words added inside the quotation |
| 9555 | quote | C | "itself" for the source's "its self" |
| 10738 | quote | A | an adjective added inside the quotation |

This split has now been used once. A fix for these 7 false alarms would be made with them in view, so a
later version's numbers on this split will not be blind; they will be reported as such.
