# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""arm_check.py: a positive control for an arm BEFORE the judge sees it.

"An arm that produces the expected verdict for the wrong reason is worse than one that fails."
The cheapest way to rule that out is to check, without the judge, that the arm really contains
what it claims to contain. Two checks, both deterministic:

    check_distorted(claim_variant, source)   E2: is the variant really distorted against the source?
        VALID   with the distortion named (UNIT_MISMATCH, SCALE_MISMATCH, DATE_SHIFT, VALUE_MISMATCH,
                QUOTE_ALTERED)
        INVALID "11.7 million -> 11.70 million" (numerically identical), a rounding, or nothing changed
    expected_on_unrelated(claim, passage)    F: what should a comparator say on an unrelated passage?
        REFUTED_ADMISSIBLE  the passage carries a comparable quantity (same unit) with another value:
                            a contradiction here is a real reading, not luck
        NEI_EXPECTED        no comparable quantity: REFUTED here is contradiction by accident
"""
from __future__ import annotations

from number_check import distortion, reconcile
from quote_check import check as quote_check

_DISTORTED = ("UNIT_MISMATCH", "SCALE_MISMATCH", "DATE_SHIFT", "VALUE_MISMATCH")


def check_distorted(claim_variant: str, source: str) -> dict:
    quotes = [q for q in quote_check(claim_variant, source) if q["kind"] != "EXACT"]
    if quotes:
        return {"status": "VALID", "distortion": "QUOTE_" + quotes[0]["kind"], "detail": quotes[0]}
    kind = distortion(claim_variant, source)
    if kind in _DISTORTED:
        f = next(x for x in reconcile(claim_variant, source) if x.kind == kind)
        return {"status": "VALID", "distortion": kind, "detail": {"claim": f.claim, "source": f.passage, **f.detail}}
    return {"status": "INVALID", "distortion": kind,
            "why": {"MATCH": "the variant states the same quantity as the source",
                    "ROUNDED_MATCH": "the variant is a rounding of the source",
                    "YEAR_UNSTATED": "month and day agree; the year is stated on one side only",
                    "NOT_IN_PASSAGE": "the source has no comparable quantity",
                    "NONE": "nothing to compare"}.get(kind, kind)}


def expected_on_unrelated(claim: str, passage: str) -> dict:
    found = reconcile(claim, passage)
    comparable = [f for f in found if f.kind in ("VALUE_MISMATCH", "SCALE_MISMATCH", "DATE_SHIFT")]
    if comparable:
        f = comparable[0]
        return {"expected": "REFUTED_ADMISSIBLE", "because": f"{f.claim!r} vs {f.passage!r} ({f.kind})"}
    return {"expected": "NEI_EXPECTED", "because": "no quantity of the same kind in the passage"}
