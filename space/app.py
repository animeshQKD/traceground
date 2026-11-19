"""traceground demo: paste an AI answer with its sources, its tool calls, or both, and see what they do
not support.

    python space/app.py          # then open http://127.0.0.1:7860

Uses no language model and no API key. The logic is in demo_logic.py. On Hugging Face Spaces it runs as
https://huggingface.co/spaces/animesh1986/traceground.
The same check is an API endpoint (traceground_check) and an MCP tool, at http://127.0.0.1:7860/gradio_api/mcp/
(needs gradio[mcp]; see README.md)."""
import gradio as gr

import demo_logic as D

CSS = """
.tg-banner {border-radius: 10px; padding: 14px 18px; border: 1px solid var(--border-color-primary);
  font-size: 0.95rem; line-height: 1.45}
.tg-banner .tg-head {font-size: 1.25rem; font-weight: 700; margin-bottom: 4px}
.tg-ok {background: rgba(34,197,94,.13); border-color: rgba(34,197,94,.55)}
.tg-problems {background: rgba(239,68,68,.13); border-color: rgba(239,68,68,.55)}
.tg-unsure, .tg-idle {background: var(--background-fill-secondary)}
.tg-idle {color: var(--body-text-color-subdued)}
.tg-error {background: rgba(245,158,11,.13); border-color: rgba(245,158,11,.55)}
.tg-box {border: 1px solid var(--border-color-primary); border-radius: 10px; padding: 12px 16px}
.tg-title {font-size: 0.8rem; text-transform: uppercase; letter-spacing: .04em;
  color: var(--body-text-color-subdued); margin: 4px 0 8px}
.tg-answer {font-size: 1rem; line-height: 1.75}
.tg-mark {border-radius: 3px; padding: 1px 2px}
.tg-num {font-weight: 700; font-size: .7rem; margin-left: 1px}
.tg-unchecked {color: var(--body-text-color-subdued); opacity: .75}
.tg-legend {margin-top: 10px; display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: .82rem}
.tg-key {display: inline-flex; align-items: center; gap: 5px}
.tg-swatch {width: 12px; height: 12px; border-radius: 3px; display: inline-block}
.tg-note {margin-top: 8px; font-size: .82rem; color: var(--body-text-color-subdued)}
.tg-card {border: 1px solid var(--border-color-primary); border-radius: 8px; padding: 10px 14px; margin: 8px 0}
.tg-cardhead {display: flex; align-items: center; gap: 8px}
.tg-n {font-weight: 700; font-size: .8rem; border: 1px solid var(--border-color-primary); border-radius: 50%;
  min-width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center}
.tg-sev {font-size: .72rem; padding: 1px 8px; border-radius: 10px; margin-left: auto}
.tg-sev-high {background: rgba(239,68,68,.2)}
.tg-sev-minor {background: var(--background-fill-secondary)}
.tg-text {margin: 6px 0 2px; font-weight: 600}
.tg-why {font-size: .92rem}
.tg-fix {font-size: .9rem; margin-top: 4px}
.tg-details {margin-top: 6px; font-size: .88rem}
.tg-details summary {cursor: pointer; color: var(--link-text-color, #60a5fa)}
.tg-ev {margin-top: 6px; padding: 6px 10px; background: var(--background-fill-secondary); border-radius: 6px;
  white-space: pre-wrap; word-break: break-word}
.tg-evsrc {font-size: .75rem; font-weight: 700; color: var(--body-text-color-subdued)}
.tg-ev mark {background: rgba(250,204,21,.45); color: inherit; border-radius: 2px; padding: 0 1px}
"""
EXAMPLES = (D.REAL_EXAMPLES + [dict(e, trace="") for e in D.SOURCE_EXAMPLES]
            + [dict(e, sources="") for e in D.TRACE_EXAMPLES] + D.BOTH_EXAMPLES)
EXAMPLES_LABEL = ('Examples: click one, then click Check. The five "Real" ones are unedited chats of OpenAI\'s '
                  'gpt-oss-120b and gpt-oss-20b (served by Groq) answering questions with made-up test tools; '
                  'the others are made up, one per check.')


def check(answer: str, question: str, sources: str, trace: str, small: bool, quotes: bool):
    """Check an answer against its sources ([S1] ... [S2] ...), its tool calls (JSON), or both. The tool
    calls can also be a whole chat (OpenAI, Anthropic or LangChain format)."""
    r = D.run(answer, question, sources, trace, check_small_integers=small, check_quotes=quotes, files=True)
    shown = gr.update(visible=r["ok"])
    js, md = r["files"] or (None, None)
    return (r["banner"], r["answer_html"], r["findings_html"], gr.update(value=r["code"]),
            gr.update(value=js), gr.update(value=md), gr.update(value=r["json"]), shown, shown, shown)


def build() -> gr.Blocks:
    # delete_cache: Gradio's copies of the downloaded reports are removed after an hour
    with gr.Blocks(title="traceground: check an AI answer against its evidence", delete_cache=(1800, 3600)) as demo:
        gr.Markdown("# traceground\nCheck an AI answer against the evidence it was given: documents, tool "
                    "calls, or both. No language model is involved. " + D.WHERE_SHORT)
        with gr.Accordion("What it checks, and how to use this page", open=False):
            gr.Markdown(D.ABOUT + "\n\n" + D.HOW_TO)
        with gr.Row():
            with gr.Column(scale=5):
                answer = gr.Textbox(label="Answer to check (leave empty to check a chat's last answer)", lines=4)
                question = gr.Textbox(label="Question (optional; numbers in it count as evidence)", lines=1)
                sources = gr.Textbox(label="Sources (optional): documents the AI was given. Start each with [S1], "
                                           "[S2], ... or separate them with a line ---", lines=5)
                trace = gr.Code(label="Tool calls (optional): JSON list of {\"name\", \"args\", \"result\"}, or a "
                                      "whole chat in OpenAI, Anthropic or LangChain format", language="json",
                                lines=6, max_lines=18)
                with gr.Row():
                    small = gr.Checkbox(label="Also check small whole numbers (0 to 10)", value=False)
                    quotes = gr.Checkbox(label="Check quotes", value=True)
                button = gr.Button("Check", variant="primary")
            with gr.Column(scale=6):
                verdict = gr.HTML(D.PLACEHOLDER)
                marked = gr.HTML()
                cards = gr.HTML()
                with gr.Accordion("Use this check in your code", open=False, visible=False) as code_box:
                    gr.Markdown("With traceground installed, this code gives the same report.")
                    code = gr.Code(language="python", interactive=False, show_label=False)
                with gr.Row(visible=False) as downloads:
                    get_json = gr.DownloadButton("Download the report (JSON)", size="sm", variant="secondary")
                    get_md = gr.DownloadButton("Download the report (Markdown)", size="sm", variant="secondary")
                with gr.Accordion("Full report (JSON)", open=False, visible=False) as raw_box:
                    raw = gr.JSON(show_label=False)
        gr.Examples(examples=[[e["answer"], e["question"], e["sources"], e["trace"]] for e in EXAMPLES],
                    inputs=[answer, question, sources, trace], example_labels=[e["title"] for e in EXAMPLES],
                    label=EXAMPLES_LABEL, examples_per_page=len(EXAMPLES))
        button.click(check, [answer, question, sources, trace, small, quotes],
                     [verdict, marked, cards, code, get_json, get_md, raw, code_box, downloads, raw_box],
                     api_name="check_page", api_visibility="private")
        # the endpoint for programs and agents (and the MCP tool, when launched with mcp_server=True)
        gr.api(D.traceground_check, api_name="traceground_check")
    return demo


def has_mcp() -> bool:
    """gradio[mcp] is installed (the mcp package); without it the page runs without the MCP server."""
    import importlib.util
    return importlib.util.find_spec("mcp") is not None


if __name__ == "__main__":
    if not has_mcp():
        print('MCP server off: install it with  pip install "gradio[mcp]==6.32.0"')
    build().launch(css=CSS, mcp_server=has_mcp())
