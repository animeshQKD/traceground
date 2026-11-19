# Phase 0 survey: what existing checkers already catch

Runs our checker and four existing ones on 20 cases and records, for each case, whether the tool flagged
the answer and the reason it gave:

| Tool | What it uses | Version |
|---|---|---|
| traceground (ours) | exact checks, no model; reads the tool-call traces itself | the version installed from this folder |
| GroundLens | exact checks of figures (Rust engine), no model | 6.0.5 |
| LongTracer | sentence similarity + NLI (DeBERTa) | 0.3.1 |
| RAGGround | fuzzy overlap, then an NLI cross-encoder (ONNX) | 0.2.2 |
| halluguard | MiniLM similarity + NLI (DeBERTa-v3-base), as its README sets it up | 0.3.1 |

The cases (`cases.json`): 13 answers with one error each (the real errors of handoff section 5, some
rewritten in everyday domains) and 7 correct answers that a checker must let through.
`test_survey.py` checks that the cases are well-formed and that every number in them is consistent
(the Werner-state measures, the loan, the currency rates).

How the cases are given to the four other tools, which all take an answer and a list of passages
(traceground gets the same, except that it reads a trace case's tool calls directly): each source,
or each tool call with its result, is one passage; the question is one more passage; citation markers
such as `[S1]` are taken out of the answer (`--markers keep` leaves them in). The details are at the
top of `run_survey.py`.

A flag only counts as a catch if its reason points at the real error. The script cannot decide that:
the report lists every reason, and the "right reason?" column is filled in by hand.

Output: `results/survey_<date>.md` (tables) and `results/survey_<date>.json` (everything). A run of only
some tools adds their names to the file name (`survey_<date>_traceground.md`), and an existing file is
never overwritten (`_2`, `_3`, ... are added).
