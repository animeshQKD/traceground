"""Tests for ragtruth.py on a tiny made-up dataset in RAGTruth's format (no RAGTruth text, no network)."""
import json

import ragtruth

SOURCES = [
    {"source_id": "s1", "task_type": "Summary", "source_info": "The bridge opened in 1932 and cost $4 million.",
     "prompt": "Summarize the following news within 50 words:\nThe bridge opened in 1932 and cost $4 million."},
    {"source_id": "s2", "task_type": "QA", "source_info": {"question": "when did the bridge open",
                                                           "passages": "passage 1: The bridge opened in 1932."},
     "prompt": "Briefly answer the following question:\nwhen did the bridge open\nBear in mind ... "
               "passage 1: The bridge opened in 1932.\noutput:"},
    {"source_id": "s3", "task_type": "Data2txt", "source_info": {"name": "Joe's", "business_stars": 4.0},
     "prompt": "Instruction: Write an objective overview.\nStructured data:\n{...}\nOverview:"},
]


def _resp(rid, sid, text, labels=(), split="test"):
    return {"id": rid, "source_id": sid, "model": "m", "split": split, "quality": "good", "response": text,
            "labels": [{"start": text.index(t), "end": text.index(t) + len(t), "text": t,
                        "label_type": "Evident Conflict"} for t in labels]}


RESPONSES = [
    _resp("1", "s1", "The bridge opened in 1932 and cost $5 million.", labels=["$5 million"]),   # caught
    _resp("2", "s1", "The bridge opened in 1931 and cost $4 million."),          # flagged, not marked
    _resp("3", "s1", "The bridge opened in 1932; it is painted red.", labels=["painted red"]),  # missed
    _resp("4", "s2", "The bridge opened in 1932."),
    _resp("5", "s3", "Joe's has 4 stars."),
    _resp("6", "s3", "Joe's has 2.5 stars.", labels=["2.5"]),
    _resp("7", "s1", "The bridge opened in 1932.", split="train"),               # other split: left out
]


def _write(tmp_path):
    with open(tmp_path / "response.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in RESPONSES)
    with open(tmp_path / "source_info.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(s) + "\n" for s in SOURCES)


def test_instruction_has_no_source_text():
    assert ragtruth.instruction(SOURCES[0]) == "Summarize the following news within 50 words:"
    assert "passage 1" not in ragtruth.instruction(SOURCES[1])
    assert ragtruth.instruction(SOURCES[2]).startswith("Instruction:")


def test_counts(tmp_path):
    _write(tmp_path)
    responses, sources = ragtruth.load(tmp_path)
    report, unmarked = ragtruth.score(responses, sources, "test")
    s = report["Summary"]
    assert (s["answers"], s["answers_marked"], s["flagged"], s["tp"], s["fp"]) == (3, 2, 2, 1, 1)
    assert (s["precision"], s["recall"]) == (0.5, 0.5)
    assert (s["digit_spans"], s["digit_spans_flagged"]) == (1, 1)
    assert s["flagged_unmarked_ids"] == ["2"]
    assert report["QA"]["flagged"] == 0
    d = report["Data2txt"]
    assert (d["answers"], d["flagged"], d["tp"], d["digit_spans_flagged"]) == (2, 1, 1, 1)
    assert [r["id"] for _t, r, _f in unmarked] == ["2"]


def test_main_writes_numbers_only(tmp_path):
    _write(tmp_path)
    out = tmp_path / "results"
    assert ragtruth.main(["--split", "test", "--data", str(tmp_path), "--out", str(out), "--review", "5"]) == 0
    md = next(out.glob("ragtruth_test_*.md")).read_text(encoding="utf-8")
    js = next(out.glob("ragtruth_test_*.json")).read_text(encoding="utf-8")
    for text in ("bridge", "1931", "Joe"):                  # no answer or source text in the results
        assert text not in md and text not in js
    review = (tmp_path / "review_test.txt").read_text(encoding="utf-8")
    assert "1931" in review                                 # the review file, kept next to the data, has it
