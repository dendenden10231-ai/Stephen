# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""quote_check.py: does a quotation in the claim appear in the passage as written?

For arm E2 on misquote claims (c11 type). For each quoted span in the claim ("..." or “...”):
    EXACT        the words appear in the passage in the same order (case and punctuation ignored)
    ALTERED      the closest span in the passage differs; the changed words are listed
    NOT_FOUND    nothing in the passage is close (similarity below the threshold)
Standard library only (difflib).
"""
from __future__ import annotations

import difflib
import re

_QUOTE = re.compile(r"[\"“”«»„]([^\"“”«»„]{8,}?)[\"“”«»„]")
_WORD = re.compile(r"[\w'’-]+", re.U)


def _words(text: str) -> list[str]:
    return [w.lower().replace("’", "'") for w in _WORD.findall(text)]


def check(claim: str, passage: str, threshold: float = 0.6) -> list[dict]:
    pw = _words(passage)
    out = []
    for q in _QUOTE.findall(claim):
        qw = _words(q)
        if not qw:
            continue
        n = len(qw)
        best, best_i = 0.0, 0
        for i in range(0, max(1, len(pw) - n + 1)):
            r = difflib.SequenceMatcher(None, qw, pw[i:i + n + 2]).ratio()
            if r > best:
                best, best_i = r, i
        window = pw[best_i:best_i + n + 2]
        if best < threshold:
            out.append({"kind": "NOT_FOUND", "quote": q, "similarity": round(best, 3)})
            continue
        sm = difflib.SequenceMatcher(None, qw, window)
        blocks = [b for b in sm.get_matching_blocks() if b.size]
        start = blocks[0].b if blocks else 0
        end = (blocks[-1].b + blocks[-1].size) if blocks else n
        window = window[start:end]
        if window == qw:
            out.append({"kind": "EXACT", "quote": q})
            continue
        changes = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, qw, window).get_opcodes():
            if tag != "equal":
                changes.append({"claim": " ".join(qw[i1:i2]), "passage": " ".join(window[j1:j2])})
        out.append({"kind": "ALTERED", "quote": q, "passage_span": " ".join(window), "changes": changes})
    return out
