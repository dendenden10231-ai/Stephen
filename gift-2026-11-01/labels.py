# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""labels.py: one normalisation of judge labels for every module here."""
from __future__ import annotations

SUP, REF, NEI, REFUSAL = "SUPPORTED", "REFUTED", "NOT_ENOUGH_INFO", "REFUSAL"
_ALIASES = {"SUP": SUP, "SUPPORTED": SUP, "OK": SUP, "EXACT_MATCH": SUP, "TRUE": SUP,
            "REF": REF, "REFUTED": REF, "CONTRADICTED": REF, "FALSE": REF,
            "NEI": NEI, "NOT_ENOUGH_INFO": NEI, "UNSUPPORTED_NUMBER": NEI,
            "UNT": REFUSAL, "UNTESTED": REFUSAL, "UNRESOLVED": REFUSAL, "REFUSED": REFUSAL,
            "NO_NUMBERS": REFUSAL, "NO_EVIDENCE": REFUSAL, "ABSTAIN": REFUSAL}


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
