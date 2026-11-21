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
python_version: "3.12"
tags:
  - mcp-server
  - grounding
  - hallucination-detection
  - rag
  - ai-agents
---

# traceground demo

Paste an AI answer with its sources, the tool calls the model made, or both, and see every number, quote,
value or tool argument they do not support. No language model and no API key: the check is
deterministic and takes milliseconds.

The write-up, with real examples and the measurement: [what a model-free check catches in real AI
answers](https://huggingface.co/blog/animesh1986/traceground-what-a-model-free-check-catches-in-rea).

This page runs [traceground](https://github.com/animeshQKD/traceground) 0.1.2, installed from
[PyPI](https://pypi.org/project/traceground/). It shows a verdict, the answer with each finding marked (and
the sentences with nothing to check in grey), each finding with the evidence it was checked against, the
Python code that gives the same report, and the report to download (JSON, Markdown).

Five examples are real: unedited chats of OpenAI's gpt-oss-120b and gpt-oss-20b (served by Groq) from the
evaluation in the repository's `eval/` folder, answering held-out questions with its made-up test tools
(`real_examples.json`). One is correct, three have real errors traceground reports, and one has true numbers
from the model's own knowledge, which it reports because no tool gave them. The others are made up, one per
check.

**What you paste.** On the online page, the text is checked on the Hugging Face server that runs it. No
language model or API sees it, and the report files for the download buttons are deleted after an hour. To
keep everything on your own computer, run the page locally (below).

## As an API and an MCP tool

The same check is one endpoint, `traceground_check`, for programs (Gradio's API, "Use via API or MCP" at the
bottom of the page) and for AI agents as an MCP tool. The tool takes the answer, the sources, the tool calls
or a whole chat, and the question, all as text, and returns the report as JSON. Its address (Streamable
HTTP) is

* on this Space: https://animesh1986-traceground.hf.space/gradio_api/mcp/, where the tool is named
  `traceground_traceground_check` (Gradio puts the Space's name in front of every tool on a Space)
* run locally: http://127.0.0.1:7860/gradio_api/mcp/, where it is named `traceground_check`

`mcp_check.py` in the repository connects to either as an MCP client and checks two answers:
`python space/mcp_check.py https://animesh1986-traceground.hf.space/gradio_api/mcp/`.

## Run it locally

From a copy of the [repository](https://github.com/animeshQKD/traceground):

```
pip install traceground "gradio[mcp]==6.32.0"
python space/app.py
```

then open http://127.0.0.1:7860. `demo_logic.py` holds the logic and the examples; `app.py` the page.
