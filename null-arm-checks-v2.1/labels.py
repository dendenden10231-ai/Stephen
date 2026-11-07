# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""labels.py: one normalisation of judge labels for every module here."""
from __future__ import annotations

SUP, REF, NEI, REFUSAL = "SUPPORTED", "REFUTED", "NOT_ENOUGH_INFO", "REFUSAL"
# v2.1: UNTESTED is "the judge answered and code threw the answer away" (a state set by code, not a label the model emits).
# It is neither a refusal nor a verdict, so it is counted apart and kept out of the judged denominators.
UNTESTED = "UNTESTED"
_ALIASES = {"SUP": SUP, "SUPPORTED": SUP, "OK": SUP, "EXACT_MATCH": SUP, "TRUE": SUP,
            "REF": REF, "REFUTED": REF, "CONTRADICTED": REF, "FALSE": REF,
            "NEI": NEI, "NOT_ENOUGH_INFO": NEI, "UNSUPPORTED_NUMBER": NEI,
            "UNT": UNTESTED, "UNTESTED": UNTESTED, "UNRESOLVED": REFUSAL, "REFUSED": REFUSAL,
            "NO_NUMBERS": REFUSAL, "NO_EVIDENCE": REFUSAL, "ABSTAIN": REFUSAL,
            # v2: number binding found no matching number in the supplied source ("needs recovery")
            "NEEDS_RECOVERY": NEI, "SCOPE_EXCLUDED": REFUSAL}


def norm(label):
    """SUPPORTED | REFUTED | NOT_ENOUGH_INFO | REFUSAL | None (no output / arm not built).
    The HELIX /api/check statuses (OK, CONTRADICTED, UNSUPPORTED_NUMBER, NO_NUMBERS) map here."""
    if label is None:
        return None
    s = str(label).strip().upper()
    if s in ("", "N/A", "NA", "NONE", "-"):
        return None
    return _ALIASES.get(s, s)


def determinate(label) -> bool:
    return norm(label) in (SUP, REF)
