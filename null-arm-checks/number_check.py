# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""number_check.py: deterministic reconciliation of the quantities in a claim against a passage.

Purpose in the probe: arm E2 gives the judge the genuine passage that a claim distorts
(a unit change, a date shifted by a year, a misquoted figure). This module says, without any
model, WHAT the distortion is, so the grader can tell "the judge caught the distortion" from
"the judge got lucky".

    reconcile(claim, passage) -> list of findings, one per quantity in the claim:
        MATCH            same value, same unit (after normalising scale words and formats)
        ROUNDED_MATCH    the claim is coarser than the passage within its own rounding
        SCALE_MISMATCH   same digits, different scale (x1000, x1e6 ...)
        UNIT_MISMATCH    same value, different unit
        VALUE_MISMATCH   same unit, different value (relative difference given)
        DATE_SHIFT       a date that differs by whole years or days
        NOT_IN_PASSAGE   no quantity of that kind in the passage

English text only. Standard library only.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import date

_MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], 1)}
_MONTHS.update({k[:3]: v for k, v in list(_MONTHS.items())})
_MONTHS["sept"] = 9

_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
          "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
          "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
          "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60,
          "seventy": 70, "eighty": 80, "ninety": 90, "hundred": 100}

_SCALE = {"k": 1e3, "thousand": 1e3, "m": 1e6, "mn": 1e6, "million": 1e6, "millions": 1e6,
          "bn": 1e9, "b": 1e9, "billion": 1e9, "billions": 1e9, "tn": 1e12, "trillion": 1e12}

# Unit families: the canonical name is what is compared.
_UNITS = [
    (r"barrels?\s+(?:a|per)\s+day|b/d|bpd|bbl/d", "barrels/day"),
    (r"barrels?\s+(?:a|per)\s+week|b/w", "barrels/week"),
    (r"barrels?|bbl", "barrels"),
    (r"tonnes?|tons?|metric\s+tons?|\bt\b", "tonnes"),
    (r"kilograms?|kg", "kg"),
    (r"kilomet(?:re|er)s?|km", "km"),
    (r"miles?", "miles"),
    (r"per\s*cent|percent|%", "%"),
    (r"refiner(?:y|ies)", "refineries"),
    (r"(?:us\s*)?dollars?|\$|usd", "USD"),
    (r"euros?|€|eur", "EUR"),
]
_UNIT_RE = "|".join(f"(?:{u})" for u, _ in _UNITS)

_NUM = r"(?P<num>\d{1,3}(?:[ ,  ]\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
_WORDNUM = r"(?P<word>" + "|".join(sorted(_WORDS, key=len, reverse=True)) + r")"
_QTY = re.compile(
    rf"(?P<pre>\$|€)?\s*(?:{_NUM}|\b{_WORDNUM}\b)\s*(?P<scale>thousand|millions?|billions?|trillion|mn|bn|tn|[kmb](?![/\w]))?\b"
    rf"\s*(?P<unit>{_UNIT_RE})?", re.I)
_DATE_DMY = re.compile(r"\b(?P<d1>\d{1,2})(?:\s*[-–]\s*(?P<d2>\d{1,2}))?\s+(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<y>(?:19|20)\d{2})\b")
_DATE_MDY = re.compile(r"\b(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<d1>\d{1,2})(?:\s*[-–]\s*(?P<d2>\d{1,2}))?,?\s+(?P<y>(?:19|20)\d{2})\b")
_DATE_ISO = re.compile(r"\b(?P<y>(?:19|20)\d{2})-(?P<m>\d{2})-(?P<d>\d{2})\b")
_MONTH_YEAR = re.compile(r"\b(?P<mon>[A-Za-z]{3,9})\s+(?P<y>(?:19|20)\d{2})\b")
_YEAR = re.compile(r"\b(?:in|by|since|from|of|during)\s+(?P<y>(?:19|20)\d{2})\b", re.I)


@dataclass
class Quantity:
    value: float
    unit: str            # canonical unit or "" (a bare count)
    text: str
    digits: str = ""     # significant digits without trailing zeros, for SCALE_MISMATCH
    step: float = 1.0    # value of the last digit AS WRITTEN (mantissa x scale), for rounding


@dataclass
class When:
    start: date
    end: date
    precision: str       # "day" | "month" | "year"
    text: str


@dataclass
class Finding:
    kind: str
    claim: str
    passage: str = ""
    detail: dict = field(default_factory=dict)


def _canon_unit(u: str) -> str:
    if not u:
        return ""
    for pattern, name in _UNITS:
        if re.fullmatch(pattern, u.strip(), re.I):
            return name
    return u.strip().lower()


def _dates(text: str) -> tuple[list[When], list[tuple[int, int]]]:
    out: list[When] = []
    spans: list[tuple[int, int]] = []

    def add(m, d1, d2, mon, y, precision):
        try:
            a = date(y, mon, d1)
            b = date(y, mon, d2 or d1)
        except ValueError:
            return
        out.append(When(a, b, precision, m.group(0)))
        spans.append(m.span())

    for rx in (_DATE_DMY, _DATE_MDY):
        for m in rx.finditer(text):
            mon = _MONTHS.get(m.group("mon").lower())
            if mon and not any(s <= m.start() < e for s, e in spans):
                add(m, int(m.group("d1")), int(m.group("d2")) if m.group("d2") else None, mon, int(m.group("y")), "day")
    for m in _DATE_ISO.finditer(text):
        if not any(s <= m.start() < e for s, e in spans):
            add(m, int(m.group("d")), None, int(m.group("m")), int(m.group("y")), "day")
    for m in _MONTH_YEAR.finditer(text):
        mon = _MONTHS.get(m.group("mon").lower())
        if mon and not any(s <= m.start() < e for s, e in spans):
            y = int(m.group("y"))
            last = (date(y + (mon == 12), mon % 12 + 1, 1) - date(y, mon, 1)).days
            out.append(When(date(y, mon, 1), date(y, mon, last), "month", m.group(0)))
            spans.append(m.span())
    for m in _YEAR.finditer(text):
        if not any(s <= m.start("y") < e for s, e in spans):
            y = int(m.group("y"))
            out.append(When(date(y, 1, 1), date(y, 12, 31), "year", m.group("y")))
            spans.append(m.span("y"))
    return out, spans


def _quantities(text: str, skip: list[tuple[int, int]]) -> list[Quantity]:
    out = []
    for m in _QTY.finditer(text):
        if not (m.group("num") or m.group("word")):
            continue
        if any(s <= m.start("num" if m.group("num") else "word") < e for s, e in skip):
            continue
        if m.group("num"):
            raw = re.sub(r"[ ,  ]", "", m.group("num"))
            if not m.group("unit") and not m.group("scale") and not m.group("pre") and re.fullmatch(r"(19|20)\d{2}", raw):
                continue   # a bare year is a date, not a quantity
            value = float(raw)
            digits = raw.replace(".", "").lstrip("0") or "0"
            decimals = len(raw.split(".")[1]) if "." in raw else 0
        else:
            value = float(_WORDS[m.group("word").lower()])
            digits, decimals = str(int(value)), 0
        scale = (m.group("scale") or "").lower()
        factor = _SCALE.get(scale, 1.0) if scale else 1.0
        value *= factor
        step = (10 ** (-decimals)) * factor
        unit = _canon_unit(m.group("unit") or "")
        if not unit and m.group("pre"):
            unit = "USD" if m.group("pre") == "$" else "EUR"
        out.append(Quantity(value, unit, m.group(0).strip(), digits.rstrip("0") or "0", step))
    return out


def _rel(a: float, b: float) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-12)


def _rounded(claim: Quantity, passage: Quantity) -> bool:
    """The claim is a coarser rounding of the passage (382 kg vs 381.7 kg; 12 million vs 11.7 million)."""
    if claim.value == 0 or passage.step >= claim.step:
        return False
    return abs(claim.value - passage.value) <= claim.step / 2 * (1 + 1e-9)


def reconcile(claim: str, passage: str) -> list[Finding]:
    c_dates, c_spans = _dates(claim)
    p_dates, p_spans = _dates(passage)
    findings: list[Finding] = []

    for w in c_dates:
        if not p_dates:
            findings.append(Finding("NOT_IN_PASSAGE", w.text, detail={"type": "date"}))
            continue
        hit = next((p for p in p_dates if p.start <= w.start and w.end <= p.end or w.start <= p.start and p.end <= w.end), None)
        if hit:
            findings.append(Finding("MATCH", w.text, hit.text, {"type": "date"}))
            continue
        best = min(p_dates, key=lambda p: abs((p.start - w.start).days))
        years = best.start.year - w.start.year
        if years and (best.start.month, best.start.day) == (w.start.month, w.start.day) or (years and w.precision != "day"):
            findings.append(Finding("DATE_SHIFT", w.text, best.text, {"claim_minus_passage_years": -years}))
        else:
            findings.append(Finding("DATE_SHIFT", w.text, best.text, {"claim_minus_passage_days": (w.start - best.start).days}))

    p_qty = _quantities(passage, p_spans)
    for q in _quantities(claim, c_spans):
        if not p_qty:
            findings.append(Finding("NOT_IN_PASSAGE", q.text, detail={"type": "quantity"}))
            continue
        same_unit = [p for p in p_qty if p.unit == q.unit]
        exact = [p for p in same_unit if _rel(p.value, q.value) < 1e-9]
        if exact:
            findings.append(Finding("MATCH", q.text, exact[0].text))
            continue
        rounded = [p for p in same_unit if _rounded(q, p)]
        if rounded:
            findings.append(Finding("ROUNDED_MATCH", q.text, rounded[0].text))
            continue
        scaled = [p for p in same_unit if p.digits == q.digits and p.value
                  and abs(math.log10(q.value / p.value)) >= 1
                  and float(math.log10(q.value / p.value)).is_integer()]
        if scaled:
            findings.append(Finding("SCALE_MISMATCH", q.text, scaled[0].text, {"factor": q.value / scaled[0].value}))
            continue
        other_unit = [p for p in p_qty if p.unit != q.unit and _rel(p.value, q.value) < 1e-9]
        if other_unit:
            findings.append(Finding("UNIT_MISMATCH", q.text, other_unit[0].text,
                                    {"claim_unit": q.unit or "(none)", "passage_unit": other_unit[0].unit or "(none)"}))
            continue
        if same_unit:
            best = min(same_unit, key=lambda p: _rel(p.value, q.value))
            findings.append(Finding("VALUE_MISMATCH", q.text, best.text, {"relative_difference": round(_rel(best.value, q.value), 4)}))
            continue
        findings.append(Finding("NOT_IN_PASSAGE", q.text, detail={"type": "quantity", "unit": q.unit}))
    return findings


def distortion(claim: str, passage: str) -> str:
    """One word for the grader: the strongest distortion found, or MATCH / NONE."""
    order = ["UNIT_MISMATCH", "SCALE_MISMATCH", "DATE_SHIFT", "VALUE_MISMATCH", "NOT_IN_PASSAGE", "ROUNDED_MATCH", "MATCH"]
    kinds = {f.kind for f in reconcile(claim, passage)}
    return next((k for k in order if k in kinds), "NONE")
