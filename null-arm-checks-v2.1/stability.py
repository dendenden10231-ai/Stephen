# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""stability.py: the same probe run several times on a non-deterministic judge.

    cells(runs)       per claim x arm, the labels in run order and whether they differ
    pairs(run)        the permuted arm under both definitions used in our exchange, side by side

Input: a list of results objects {claim_id: {arm: label}}, or a CSV "run,claim,A,...".
"""
from __future__ import annotations

import csv
from collections import Counter

from labels import NEI, REF, SUP, determinate, norm

SHORT = {"A": "A_genuine", "B": "B_empty", "C": "C_noise_length", "D": "D_noise_topic",
         "E": "E_contradicting", "F": "F_unrelated", "G": "G_permuted"}


def load_csv(path: str) -> list[dict]:
    runs: dict[str, dict] = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            runs.setdefault(row["run"], {})[row["claim"]] = {SHORT.get(k, k): v for k, v in row.items()
                                                            if k not in ("run", "claim")}
    return [runs[k] for k in sorted(runs, key=lambda x: int(x) if x.isdigit() else x)]


def cells(runs: list[dict]) -> dict:
    """v2.1: a missing answer (no output, N/A, arm not built) is NOT a label change, as FREEZE_v2.txt already ruled.
    It is counted on its own (`missing_answers`); instability is judged over the runs that DID answer, and a cell is
    comparable only if at least two runs answered. v2 counted {SUPPORTED, None} as one flip."""
    seen: dict = {}
    for run in runs:
        for cid, arms in run.items():
            for arm, lab in arms.items():
                n = norm(lab)
                # v2.1: UNTESTED ("answered, then removed by code") is not a verdict, so it counts as no answer.
                seen.setdefault((cid, arm), []).append(None if n == "UNTESTED" else n)
    built = {k: v for k, v in seen.items() if any(x is not None for x in v)}
    comparable = {k: [x for x in v if x is not None] for k, v in built.items()
                  if sum(x is not None for x in v) >= 2}
    unstable = {f"{c}/{a}": built[(c, a)] for (c, a), v in comparable.items() if len(set(v)) > 1}
    missing = sum(x is None for v in built.values() for x in v)
    return {"runs": len(runs), "cells": len(built), "comparable_cells": len(comparable),
            "cells_with_missing": sum(any(x is None for x in v) for v in built.values()),
            "missing_answers": missing, "unstable": len(unstable),
            "unstable_by_arm": dict(Counter(k.split("/")[1] for k in unstable)), "unstable_cells": unstable}


def pairs(run: dict, a="A_genuine", g="G_permuted") -> dict:
    content = [(c, x[a], x[g]) for c, x in run.items() if norm(x.get(a)) in (SUP, REF, NEI) and norm(x.get(g)) in (SUP, REF, NEI)]
    det = [(c, x[a], x.get(g)) for c, x in run.items() if determinate(x.get(a)) and norm(x.get(g)) is not None]
    return {
        "content_pairs": len(content), "content_changed": sum(norm(p) != norm(q) for _, p, q in content),
        "content_unchanged": [c for c, p, q in content if norm(p) == norm(q)],
        "determinate_A": len(det), "determinate_A_changed": sum(norm(p) != norm(q) for _, p, q in det),
        "credulity": [c for c, p, q in det if norm(q) == norm(p)],
        "wrong_direction": [c for c, p, q in det if determinate(q) and norm(q) != norm(p)],
    }
