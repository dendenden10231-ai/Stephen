# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""mutation_set.py: claims whose correct label is known BY CONSTRUCTION, with no human labelling.

The null-arm probe measures dependence on evidence, and its plan says so: "sensitivity and
specificity are about dependence, not truth; they do not test correctness". This module adds the
missing correctness layer without a gold set. From a genuine passage it takes sentences that carry
a quantity, a date or a quotation, and writes deterministic variants:

    identity            the sentence as written                         -> SUPPORTED
    paraphrase_number   400,000 -> 400k, 9 -> nine, 11.7 million -> 11.7M -> SUPPORTED
    unit_swap           barrels per day -> barrels per week, km -> miles  -> REFUTED
    scale_shift         x1000 or /1000 (thousand <-> million <-> billion) -> REFUTED
    value_shift         the number moved by 25% (beyond any rounding)     -> REFUTED
    year_shift          the year moved by one                             -> REFUTED
    quote_alteration    one word inside a quotation replaced              -> REFUTED

Each variant is passed back through the oracles (number_check, quote_check) against the passage;
a variant the oracle cannot tell from the passage is dropped, so no item can be mislabelled by the
generator itself. The judge sees (variant, passage) as claim and evidence; score() reports
accuracy per mutation type and, separately, false refutations on paraphrases (over-strictness).

Limits, stated: only English; only distortions a deterministic oracle can see. It does not test
wrong inferences, missing context or superseded figures. Twelve passages give dozens of items,
not a benchmark; report counts.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

from number_check import distortion
from quote_check import check as quote_check

_SENT = re.compile(r"(?<=[.!?;])\s+|\n+")
_NUMBER = re.compile(r"(?<![\w.,])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![\w,]|\.\d)")
_YEAR = re.compile(r"\b(19\d{2}|20\d{2})\b")
_QUOTED = re.compile(r"([\"“])([^\"“”]{8,}?)([\"”])")
_UNIT_SWAPS = [
    (r"barrels?\s+(?:a|per)\s+day|b/d|bpd", "barrels per week"),
    (r"\bkm\b|kilomet(?:re|er)s", "miles"),
    (r"\btonnes\b", "barrels"),
    (r"\bper cent\b|\bpercent\b", "percentage points"),
]
_SCALE_UP = {"thousand": "million", "million": "billion", "billion": "trillion",
             "k": "M", "mn": "bn", "M": "B", "bn": "tn"}
_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
          9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}
_QUOTE_SWAPS = [("one of the reasons", "the only reason"), ("one of the", "the sole"), ("some", "all"), ("may", "will"), ("could", "will"),
                ("increase", "decrease"), ("rise", "fall"), ("more", "less"), ("not", "")]


def _sentences(passage: str) -> list[str]:
    return [s.strip() for s in _SENT.split(passage) if len(s.strip()) > 20]


def _paraphrase(s: str) -> str | None:
    m = re.search(r"\b(\d{1,3}),000\b(?!,)", s)
    if m:
        return s[:m.start()] + f"{m.group(1)}k" + s[m.end():]
    m = re.search(r"\b(\d+(?:\.\d+)?) million\b", s)
    if m:
        return s[:m.start()] + f"{m.group(1)}M" + s[m.end():]
    for n in range(12, 0, -1):
        m = re.search(rf"(?<![\w.,$]){n}(?=\s+[a-z])", s)
        if m and not _YEAR.match(s[m.start():m.start() + 4]):
            return s[:m.start()] + _WORDS[n] + s[m.end():]
    return None


def _unit_swap(s: str) -> str | None:
    for pat, repl in _UNIT_SWAPS:
        m = re.search(pat, s, re.I)
        if m:
            return s[:m.start()] + repl + s[m.end():]
    return None


def _scale_shift(s: str) -> str | None:
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*(thousand|million|billion|mn|bn|k|M)\b", s)
    if m and m.group(2) in _SCALE_UP:
        return s[:m.start(2)] + _SCALE_UP[m.group(2)] + s[m.end(2):]
    m = re.search(r"\b(\d{1,3}),000\b", s)
    if m:
        return s[:m.start()] + m.group(1) + s[m.end():]
    return None


_MONTH = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"


def _is_day_of_month(s: str, m) -> bool:
    after = s[m.end():m.end() + 12].lower()
    before = s[max(0, m.start() - 12):m.start()].lower()
    return bool(re.match(rf"\s*[-–]?\s*\d{{0,2}}\s*{_MONTH}\b", after) or re.search(rf"\b{_MONTH}\.?\s*$", before))


_MEASURE_AFTER = re.compile(r"\s*(?:%|k\b|M\b|B\b|bn\b|mn\b|million|billion|thousand|barrels?|b/d|bbl|t/d|"
                            r"/gal|/bbl|kg\b|km\b|tonnes?|per\s*cent|"
                            # v2.1: the corpus's own vocabulary that v2 missed (m3 26, tank 126, worker 22, refiner 573
                            # occurrences in arms_v2.json): counted objects and a volume unit.
                            r"m3\b|m³|tanks?\b|workers?\b|refiner(?:y|ies)\b)", re.I)


def _is_measure(s: str, m) -> bool:
    """Only numbers that measure something: a currency before it or a unit/scale after it.
    "Phillips 66" and "PADD 3" are names, not quantities, and must not be shifted."""
    before = s[max(0, m.start() - 2):m.start()]
    return "$" in before or "€" in before or bool(_MEASURE_AFTER.match(s[m.end():m.end() + 12]))


def why_no_value_shift(s: str) -> str:
    """v2.1: the reason a sentence yields no value_shift variant, so a lost candidate is countable."""
    seen_number = False
    skipped = []
    for m in _NUMBER.finditer(s):
        raw = m.group(1)
        seen_number = True
        if _YEAR.fullmatch(raw):
            continue
        if _is_day_of_month(s, m):
            continue
        if not _is_measure(s, m):
            skipped.append(s[m.start():m.end() + 14].strip())
    if not seen_number:
        return "no_number"
    if skipped:
        return "number_without_recognised_measure: " + " | ".join(skipped[:4])
    return "only_years_or_days_of_month_or_rounding_unchanged"


def _value_shift(s: str) -> str | None:
    for m in _NUMBER.finditer(s):
        raw = m.group(1)
        if _YEAR.fullmatch(raw) or _is_day_of_month(s, m) or not _is_measure(s, m):
            continue
        v = float(raw.replace(",", ""))
        if v == 0:
            continue
        new = v * 1.25
        txt = f"{new:,.0f}" if "," in raw or "." not in raw else f"{new:.{len(raw.split('.')[1])}f}"
        if txt == raw:
            continue
        return s[:m.start()] + txt + s[m.end():]
    return None


def _year_shift(s: str) -> str | None:
    m = _YEAR.search(s)
    if not m:
        return None
    return s[:m.start()] + str(int(m.group(1)) - 1) + s[m.end():]


def _quote_alteration(s: str) -> str | None:
    m = _QUOTED.search(s)
    if not m:
        return None
    inner = m.group(2)
    for a, b in _QUOTE_SWAPS:
        hit = re.search(rf"\b{re.escape(a)}\b", inner, re.I)
        if hit:
            changed = (inner[:hit.start()] + b + inner[hit.end():]).replace("  ", " ").strip()
            return s[:m.start(2)] + changed + s[m.end(2):]
    return None   # no meaning-changing swap available: better no item than a garbled one


MUTATIONS = {
    "identity": (lambda s: s, "SUPPORTED"),
    "paraphrase_number": (_paraphrase, "SUPPORTED"),
    "unit_swap": (_unit_swap, "REFUTED"),
    "scale_shift": (_scale_shift, "REFUTED"),
    "value_shift": (_value_shift, "REFUTED"),
    "year_shift": (_year_shift, "REFUTED"),
    "quote_alteration": (_quote_alteration, "REFUTED"),
}


def _oracle_agrees(variant: str, passage: str, expected: str) -> bool:
    kind = distortion(variant, passage)
    quotes = quote_check(variant, passage)
    altered = any(q["kind"] != "EXACT" for q in quotes)
    if expected == "SUPPORTED":
        return kind in ("MATCH", "ROUNDED_MATCH", "NONE") and not altered
    return altered or kind in ("UNIT_MISMATCH", "SCALE_MISMATCH", "VALUE_MISMATCH", "DATE_SHIFT")


def build(passages: list[dict], exclusions: list | None = None) -> list[dict]:
    """passages: [{"id": "...", "text": "..."}]. Returns items:
    {id, passage_id, mutation, claim, evidence, expected, status, reason, dropped_reason?}.
    v2.1: every candidate leaves a trace. A candidate that produced a variant carries `status` kept|dropped and a `reason`;
    a candidate for which no variant could be built is appended to `exclusions` (if given) as
    {id, mutation, reason}, so the number of lost candidates can be stated."""
    items = []
    for p in passages:
        for k, sent in enumerate(_sentences(p["text"])):
            for name, (fn, expected) in MUTATIONS.items():
                variant = fn(sent)
                cid = f"{p['id']}.s{k}.{name}"
                if not variant or (name != "identity" and variant == sent):
                    if exclusions is not None:
                        why = why_no_value_shift(sent) if name == "value_shift" else "mutation_not_applicable"
                        exclusions.append({"id": cid, "mutation": name, "reason": why})
                    continue
                item = {"id": cid, "passage_id": p["id"], "mutation": name,
                        "claim": variant, "evidence": [{"text": sent, "source": p.get("source", p["id"])}],
                        "expected": expected}
                if not _oracle_agrees(variant, sent, expected):
                    item["dropped_reason"] = "the oracle cannot see this mutation against the passage"
                item["status"] = "dropped" if item.get("dropped_reason") else "kept"
                item["reason"] = item.get("dropped_reason", "")
                items.append(item)
    return items


def score(items: list[dict], labels: dict) -> dict:
    """labels: {item_id: judge label}. Accuracy per mutation type over kept items; refusals and
    NOT_ENOUGH_INFO are counted apart, never as correct."""
    from labels import norm
    per = defaultdict(Counter)
    for it in items:
        if it.get("dropped_reason"):
            continue
        got = norm(labels.get(it["id"]))
        key = ("correct" if got == it["expected"] else
               "missing" if got is None else
               "abstained" if got in ("NOT_ENOUGH_INFO", "REFUSAL") else "wrong")
        per[it["mutation"]][key] += 1
    out = {}
    for m, c in sorted(per.items()):
        n = sum(c.values())
        out[m] = {"items": n, **dict(c), "accuracy": f"{c['correct']}/{n}"}
    para = per.get("paraphrase_number", Counter())
    out["_over_strictness"] = {
        "false_refutations_on_paraphrase": para["wrong"],
        "paraphrase_items": sum(para.values()),
        "note": "a judge that refutes 400,000 against 400k is strict, not careful",
    }
    return out
