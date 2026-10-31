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
    seen: dict = {}
    for run in runs:
        for cid, arms in run.items():
            for arm, lab in arms.items():
                seen.setdefault((cid, arm), []).append(norm(lab))
    built = {k: v for k, v in seen.items() if any(x is not None for x in v)}
    unstable = {f"{c}/{a}": v for (c, a), v in built.items() if len(set(v)) > 1}
    return {"runs": len(runs), "cells": len(built), "unstable": len(unstable),
            "unstable_by_arm": dict(Counter(k.split("/")[1] for k in unstable)), "unstable_cells": unstable}


def pairs(run: dict, a="A_genuine", g="G_permuted") -> dict:
    content = [(c, x[a], x[g]) for c, x in run.items() if norm(x.get(a)) in (SUP, REF, NEI) and norm(x.get(g)) in (SUP, REF, NEI)]
    det = [(c, x[a], x.get(g)) for c, x in run.items() if determinate(x.get(a))]
    return {
        "content_pairs": len(content), "content_changed": sum(norm(p) != norm(q) for _, p, q in content),
        "content_unchanged": [c for c, p, q in content if norm(p) == norm(q)],
        "determinate_A": len(det), "determinate_A_changed": sum(norm(p) != norm(q) for _, p, q in det),
        "credulity": [c for c, p, q in det if norm(q) == norm(p)],
        "wrong_direction": [c for c, p, q in det if determinate(q) and norm(q) != norm(p)],
    }
