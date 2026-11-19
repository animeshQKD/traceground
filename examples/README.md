# Examples

Real error types, in everyday settings, to try on the command line:

* `loan_chat.json`: an OpenAI-style chat. The question asks for 5 years; the tool was called with 3.

      traceground --trace examples/loan_chat.json

* `game_calls.json` with `game_answer.txt`: the answer swaps rebounds and assists.

      traceground --trace examples/game_calls.json --answer examples/game_answer.txt
