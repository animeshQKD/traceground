"""Citation markers: which sources does a sentence cite?

A marker is a bracket group whose items name source ids: [S1], [doc2], [report.txt], [P1-p4-2],
[S1, S2]. A bare number [2] also names source "S2" when the sources were given without ids. A bracket
group whose items name no source ([sic], [1999]) is not a citation and is ignored.
(The full citations mode, with marker styles and a check of every marker, comes later.)
"""
import re

_GROUP = re.compile(r"\[([^\[\]\n]{1,80})\]")
_SPLIT = re.compile(r"\s*[,;]\s*")


def _resolve_item(item: str, ids: dict):
    item = item.strip()
    if item.casefold() in ids:
        return ids[item.casefold()]
    if item.isdigit() and f"s{int(item)}" in ids:
        return ids[f"s{int(item)}"]
    return None


def cited(text: str, source_ids) -> list:
    """The source ids that the markers in `text` name, in order, without repeats."""
    ids = {sid.casefold(): sid for sid in source_ids}
    out = []
    for m in _GROUP.finditer(text):
        for item in _SPLIT.split(m.group(1)):
            sid = _resolve_item(item, ids)
            if sid and sid not in out:
                out.append(sid)
    return out


def marker_spans(text: str, source_ids) -> list:
    """Spans of the bracket groups in `text` that name at least one source."""
    ids = {sid.casefold(): sid for sid in source_ids}
    return [(m.start(), m.end()) for m in _GROUP.finditer(text)
            if any(_resolve_item(i, ids) for i in _SPLIT.split(m.group(1)))]
