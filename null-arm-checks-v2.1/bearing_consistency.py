# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""bearing_consistency.py: does the judge's verdict agree with its own per-evidence bearings?

The plan's prerequisite is that "the judge must expose per-item bearings, not only the
aggregate". Once it does, a known defect becomes checkable without reading prose: a PASS whose
own reasoning argues for FAIL. Here the reasoning is the list of bearings, so the check is exact.

    check(output, fields=None) -> {"consistent": bool, "finding": str, "detail": {...}}

Findings:
    CONSISTENT                 the label follows from the bearings
    LABEL_WITHOUT_BEARING      a determinate label with no bearing in its direction
    BEARING_CONTRADICTS_LABEL  the label points one way, the bearings only the other way
    CONFLICT_NOT_RECORDED      bearings both ways, label determinate, no conflict flag
    REFUSAL_WITH_BEARINGS      the label is a refusal although bearings decide the claim
    NO_BEARINGS_EXPOSED        the output has no per-item bearings (the prerequisite is not met)

Bearings are normalised: supports/support/for/+ ; refutes/refute/against/- ; anything else neutral.
Field names are configurable so the check fits any judge's output object.
"""
from __future__ import annotations

DEFAULT = {"label": "label", "bearings": "bearings", "bearing": "bearing", "conflict": "conflict_recorded"}
_POS = {"supports", "support", "supported", "for", "+", "pro", "h1"}
_NEG = {"refutes", "refute", "refuted", "against", "-", "contra", "h2"}


def _b(x) -> str:
    s = str(x or "").strip().lower()
    return "+" if s in _POS else "-" if s in _NEG else "0"


def check(output: dict, fields: dict | None = None) -> dict:
    from labels import norm
    f = {**DEFAULT, **(fields or {})}
    label = norm(output.get(f["label"]))
    raw = output.get(f["bearings"])
    if not isinstance(raw, list) or not raw:
        return {"consistent": False, "finding": "NO_BEARINGS_EXPOSED", "detail": {"label": label}}
    bearings = [_b(item.get(f["bearing"]) if isinstance(item, dict) else item) for item in raw]
    pos, neg = bearings.count("+"), bearings.count("-")
    d = {"label": label, "supports": pos, "refutes": neg, "neutral": bearings.count("0")}
    conflict = bool(output.get(f["conflict"]))
    if label == "SUPPORTED":
        if pos == 0 and neg > 0:
            return {"consistent": False, "finding": "BEARING_CONTRADICTS_LABEL", "detail": d}
        if pos == 0:
            return {"consistent": False, "finding": "LABEL_WITHOUT_BEARING", "detail": d}
        if neg and not conflict:
            return {"consistent": False, "finding": "CONFLICT_NOT_RECORDED", "detail": d}
    elif label == "REFUTED":
        if neg == 0 and pos > 0:
            return {"consistent": False, "finding": "BEARING_CONTRADICTS_LABEL", "detail": d}
        if neg == 0:
            return {"consistent": False, "finding": "LABEL_WITHOUT_BEARING", "detail": d}
        if pos and not conflict:
            return {"consistent": False, "finding": "CONFLICT_NOT_RECORDED", "detail": d}
    elif label in ("REFUSAL", "UNTESTED") and (pos or neg) and not (pos and neg):   # v2.1: UNTESTED is its own label
        return {"consistent": False, "finding": "REFUSAL_WITH_BEARINGS", "detail": d}
    return {"consistent": True, "finding": "CONSISTENT", "detail": d}
