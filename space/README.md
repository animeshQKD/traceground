---
title: traceground
emoji: 🔎
colorFrom: blue
colorTo: gray
sdk: gradio
sdk_version: 6.32.0
app_file: app.py
pinned: false
license: mit
short_description: Check an AI answer against its sources and tool calls
---

# traceground demo

Paste an AI answer with its sources, the tool calls the model made, or both, and see every number, quote,
value or tool argument they do not support. No language model and no API key: the check is
deterministic, and nothing pasted leaves the machine the demo runs on.

Run it on your own computer, from the project folder:

```
pip install "gradio[mcp]==6.32.0"
python space/app.py
```

then open http://127.0.0.1:7860. The page shows a verdict, the answer with each finding marked (and the
sentences with nothing to check in grey), each finding with the evidence it was checked against, the Python
code that gives the same report, and the report to download (JSON, Markdown). `demo_logic.py` holds the
logic and the examples; `app.py` the page. Five examples are real: unedited chats of OpenAI's gpt-oss-120b
and gpt-oss-20b (served by Groq) from the evaluation in `eval/`, answering held-out questions with its
made-up test tools (`real_examples.json`); one is correct, three have real errors traceground reports, and
one has true numbers from the model's own knowledge, which it reports because no tool gave them. The others
are made up, one per check.

## As an API and an MCP tool

The same check is one endpoint, `traceground_check`, for programs (Gradio's API, "Use via API or MCP" at the
bottom of the page) and for AI agents as an MCP tool. With `gradio[mcp]` installed, `python space/app.py`
prints the MCP server's address, http://127.0.0.1:7860/gradio_api/mcp/ (Streamable HTTP). The tool takes
the answer, the sources, the tool calls or a whole chat, and the question, all as text, and returns the
report as JSON. To check that it works, run `python space/mcp_check.py` while the page is running.

(The block at the top of this file is the configuration a Hugging Face Space reads; the demo is not
published yet.)
