# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""scoring_v2.py: deterministic scoring for arm set v2. No model anywhere.

    python3 scoring_v2.py --selftest        degenerate judges must all score J_gate = 0
    python3 scoring_v2.py --baselines       five local baselines on arms_v2.json
    python3 scoring_v2.py results.json      results = {claim_id: {arm: label}}  (labels as the judge wrote them)

Reported blocks (no single aggregate over all arms):
  1  A_supported accuracy and A2_distorted_claim accuracy, SEPARATELY (anchor excluded)
  2  over-strictness: A cells answered with NEI / REFUSAL
  3  FDR_neg: share of negative-arm cells (B, C, C_num, D, F, G) with a DETERMINATE label (SUPPORTED or
     REFUTED) that is not listed as acceptable for that arm. Split into FDR_neg_SUP (credulity) and
     FDR_neg_REF (a refutation from nothing). REFUTED on F/G is acceptable only where S2.10 allows it.
  4  J_gate = Acc(A) - FDR_strict, where Acc(A) is the share of A cells with the EXPECTED label and FDR_strict
     the share of negative cells answered with ANY determinate label (SUPPORTED or REFUTED, even where S2.10
     would allow REFUTED). A judge that always answers one label scores <= 0; the perfect judge scores 1.
     (Det(A) alone cannot be used: it rewards a determinate wrong answer. FDR_neg above stays admissibility-aware.)
  5  E / E_restore accuracy with a Wilson 95 % interval, labelled small-n.
NEEDS_RECOVERY is mapped by labels.py (NEI by default); --needs-recovery refusal switches it for the
sensitivity analysis.
"""
from __future__ import annotations

import difflib
import json
import math
import sys

import labels
from labels import norm

NEG = ("B_empty", "C_noise_length", "C_num_noise", "D_noise_topic", "F_unrelated", "G_deranged")


def wilson(k: int, n: int, z: float = 1.96) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 4), round((c + h) / d, 4)]


def score(manifest: dict, got: dict) -> dict:
    cells = [a for a in manifest["arms"] if not a["anchor"]]

    def lab(a):
        return norm(got.get(a["claim_id"], {}).get(a["arm"]))

    A = [a for a in cells if a["arm"] == "A_genuine"]
    block1, over = {}, {}
    for sub in ("A_supported", "A2_distorted_claim"):
        xs = [a for a in A if a["subclass"] == sub]
        k = sum(lab(a) == a["expected"] for a in xs)
        block1[sub] = {"correct": k, "n": len(xs), "wilson95": wilson(k, len(xs))}
        over[sub] = sum(lab(a) in (labels.NEI, labels.REFUSAL) for a in xs)
    det_A = sum(lab(a) in (labels.SUP, labels.REF) for a in A) / len(A) if A else 0.0
    neg = [a for a in cells if a["negative"]]
    wrong_sup = sum(lab(a) == labels.SUP and labels.SUP not in a["acceptable"] for a in neg)
    wrong_ref = sum(lab(a) == labels.REF and labels.REF not in a["acceptable"] for a in neg)
    fdr = (wrong_sup + wrong_ref) / len(neg) if neg else 0.0
    fdr_strict = sum(lab(a) in (labels.SUP, labels.REF) for a in neg) / len(neg) if neg else 0.0
    acc_A = sum(lab(a) == a["expected"] for a in A) / len(A) if A else 0.0
    per_arm = {}
    for arm in sorted({a["arm"] for a in cells}):
        xs = [a for a in cells if a["arm"] == arm]
        ok = sum(lab(a) in [norm(e) for e in a["acceptable"]] for a in xs)
        per_arm[arm] = {"acceptable": ok, "n": len(xs), "wilson95": wilson(ok, len(xs)),
                        **({"small_n": True} if len(xs) < 30 else {})}
    return {"A_accuracy": block1, "over_strictness_A_refusals": over,
            "Det_A": round(det_A, 4), "negative_cells": len(neg),
            "FDR_neg": round(fdr, 4), "FDR_neg_SUP": round(wrong_sup / len(neg), 4) if neg else 0.0,
            "FDR_neg_REF": round(wrong_ref / len(neg), 4) if neg else 0.0,
            "FDR_strict": round(fdr_strict, 4), "Acc_A": round(acc_A, 4),
            "J_gate": round(acc_A - fdr_strict, 4), "per_arm": per_arm}


def constant_judge(manifest: dict, label: str) -> dict:
    out: dict = {}
    for a in manifest["arms"]:
        out.setdefault(a["claim_id"], {})[a["arm"]] = label
    return out


def perfect_judge(manifest: dict) -> dict:
    out: dict = {}
    for a in manifest["arms"]:
        out.setdefault(a["claim_id"], {})[a["arm"]] = a["expected"] if a["expected"] else a["acceptable"][0]
    return out


def diff_engine(arms: list[dict]) -> dict:
    """String-similarity baseline: ratio >= .95 SUPPORTED, >= .70 REFUTED, else NEI. Empty evidence -> NEI."""
    out: dict = {}
    for a in arms:
        t = a["evidence"][0]["text"] if a["evidence"] else ""
        r = difflib.SequenceMatcher(None, a["claim"], t).ratio() if t else 0.0
        out.setdefault(a["claim_id"], {})[a["arm"]] = labels.SUP if r >= .95 else labels.REF if r >= .70 else labels.NEI
    return out


def oracle_only(arms: list[dict]) -> dict:
    """Deterministic oracle baseline: any distortion found -> REFUTED; all matched -> SUPPORTED; else NEI."""
    from number_check import distortion
    bad = ("UNIT_MISMATCH", "SCALE_MISMATCH", "DATE_SHIFT", "VALUE_MISMATCH")
    out: dict = {}
    for a in arms:
        t = a["evidence"][0]["text"] if a["evidence"] else ""
        k = distortion(a["claim"], t) if t else "NONE"
        out.setdefault(a["claim_id"], {})[a["arm"]] = labels.REF if k in bad else labels.SUP if k in ("MATCH", "ROUNDED_MATCH") else labels.NEI
    return out


def baselines(arms_doc: dict) -> dict:
    manifest = {"arms": [{k: v for k, v in a.items() if k not in ("claim", "evidence")} | {"subclass": a.get("subclass", "")}
                         for a in arms_doc["arms"]]}
    res = {f"always_{l}": score(manifest, constant_judge(manifest, l))
           for l in (labels.SUP, labels.REF, labels.NEI, labels.REFUSAL)}
    res["diff_engine"] = score(manifest, diff_engine(arms_doc["arms"]))
    res["oracle_only"] = score(manifest, oracle_only(arms_doc["arms"]))
    return res


def selftest() -> int:
    arms = json.load(open("arms_v2.json", encoding="utf-8"))
    manifest = json.load(open("ARM_MANIFEST_v2.json", encoding="utf-8"))
    bad = []
    p = score(manifest, perfect_judge(manifest))
    if not (p["Acc_A"] == 1.0 and p["FDR_neg"] == 0.0 and p["J_gate"] == 1.0):
        bad.append(("perfect judge", p["Det_A"], p["FDR_neg"], p["J_gate"]))
    for l in (labels.SUP, labels.REF, labels.NEI, labels.REFUSAL):
        s = score(manifest, constant_judge(manifest, l))
        if s["J_gate"] > 0.0:
            bad.append((f"always {l}", s["J_gate"]))
    print("selftest:", "OK (perfect judge J=1; every constant judge J<=0)" if not bad else f"FAILED {bad}")
    return 0 if not bad else 1


def main() -> int:
    if "--needs-recovery" in sys.argv:
        labels._ALIASES["NEEDS_RECOVERY"] = labels.REFUSAL if sys.argv[sys.argv.index("--needs-recovery") + 1] == "refusal" else labels.NEI
    if "--selftest" in sys.argv:
        return selftest()
    if "--baselines" in sys.argv:
        b = baselines(json.load(open("arms_v2.json", encoding="utf-8")))
        for name, s in b.items():
            print(f"{name:22s} Acc_A={s['Acc_A']:.4f}  FDR_neg={s['FDR_neg']:.4f} (SUP {s['FDR_neg_SUP']:.4f}, REF {s['FDR_neg_REF']:.4f}) strict={s['FDR_strict']:.4f}  J_gate={s['J_gate']:.4f}  "
                  f"A_supported {s['A_accuracy']['A_supported']['correct']}/{s['A_accuracy']['A_supported']['n']}  "
                  f"A2 {s['A_accuracy']['A2_distorted_claim']['correct']}/{s['A_accuracy']['A2_distorted_claim']['n']}")
        return 0
    path = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    if not path:
        print(__doc__)
        return 2
    manifest = json.load(open("ARM_MANIFEST_v2.json", encoding="utf-8"))
    print(json.dumps(score(manifest, json.load(open(path, encoding="utf-8"))), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
