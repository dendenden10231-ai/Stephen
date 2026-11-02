# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""scoring_v2.py: deterministic scoring for arm set v2. No model anywhere.

    python3 scoring_v2.py --selftest        degenerate judges must all score J_gate = 0
    python3 scoring_v2.py --baselines       five local baselines on arms_v2.json
    python3 scoring_v2.py --runs RUNS       RUNS = {run_name: {claim_id: {arm: label}}} -> stability across runs
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
  6  per_family: every cell belongs to a construction family (NEI-CAP, Findings of EMNLP 2026,
     10.18653/2026.findings-emnlp.796: "report the construction family alongside the score"). An aggregate
     that mixes families is exactly what their Table 3 shows to be misleading, so the family table is printed
     next to J_gate and never instead of it.
  7  necessity: for each claim, does the LEXICAL oracle report something different about this evidence than
     about A's evidence? Where it does not, no code-only reader can tell the arms apart and only a judge with
     knowledge of the subject can; that share is reported per family. Free, deterministic, no model.
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

NEG = ("B_empty", "C_noise_length", "C_num_noise", "D_noise_topic", "F_unrelated", "G_deranged",
       "S_same_document", "H_high_overlap", "R_pair",
       "P_forecast_own", "P_forecast_weaken", "P_forecast_borrowed", "N_no_source", "R_disagree")
NOISE_ARMS = ("C_noise_length", "C_num_noise", "D_noise_topic")
FORECAST = {"own": "P_forecast_own", "weaken": "P_forecast_weaken", "borrowed": "P_forecast_borrowed"}


def forecast_diagnostic(manifest: dict, got: dict) -> dict:
    """S. Hope, 31 Oct: arm G does contamination and credulity at once, and one arm cannot tell them
    apart. Three arms on the SAME forecast claim can: its own driver sentence, a sentence arguing it
    down, and a borrowed neighbour sentence."""
    out = {}
    for cid in sorted({a["claim_id"] for a in manifest["arms"] if a["arm"] == FORECAST["own"]}):
        lab = lambda k: norm(got.get(cid, {}).get(FORECAST[k]))
        own, weak, bor = lab("own"), lab("weaken"), lab("borrowed")
        if own == labels.SUP:
            verdict = "CREDULITY — supports the forecast from its own driver, so the scope limit is not implemented at all"
        elif bor == labels.SUP:
            verdict = "CONTAMINATION — refuses the forecast on its own evidence, accepts the neighbour's as support"
        elif own == labels.REFUSAL:
            verdict = "HOLDS — refused on its own evidence and not carried by the neighbour's"
        else:
            verdict = "SCOPE_NOT_REFUSED — answered with a label instead of a refusal"
        out[cid] = {"own": own, "weaken": weak, "borrowed": bor, "diagnostic": verdict}
    return out


def score_runs(manifest: dict, runs: dict) -> dict:
    """runs = {run_name: {claim_id: {arm: label}}}. A cell whose label changes between runs is not
    evidence of anything except instability; S. Hope caught c06 under A flipping NEI/SUP/NEI and noted
    that is what R2 exists to catch."""
    cells = [a for a in manifest["arms"] if not a["anchor"]]
    unstable = []
    for a in cells:
        seen = {r: lab for r, lab in
                ((r, norm(g.get(a["claim_id"], {}).get(a["arm"]))) for r, g in sorted(runs.items())) if lab}
        if len(set(seen.values())) > 1:
            unstable.append({"claim_id": a["claim_id"], "arm": a["arm"], "labels": seen})
    strict = {}
    for sub in ("A_supported", "A2_distorted_claim"):
        xs = [a for a in cells if a["arm"] == "A_genuine" and a["subclass"] == sub]
        strict[sub] = {"stable_correct": sum(all(
            norm(g.get(a["claim_id"], {}).get(a["arm"])) == a["expected"] for g in runs.values()) for a in xs),
            "n": len(xs), "single_run_correct_would_overstate_by":
                sum(any(norm(g.get(a["claim_id"], {}).get(a["arm"])) == a["expected"] for g in runs.values()) for a in xs)
                - sum(all(norm(g.get(a["claim_id"], {}).get(a["arm"])) == a["expected"] for g in runs.values()) for a in xs)}
    return {"runs": sorted(runs), "unstable_cells": len(unstable),
            "unstable_A_genuine": [u for u in unstable if u["arm"] == "A_genuine"],
            "A_accuracy_requiring_stability": strict, "unstable_detail": unstable}


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
    noise = [a for a in cells if a["arm"] in NOISE_ARMS]
    noise_split = {labels.NEI: sum(lab(a) == labels.NEI for a in noise),
                   labels.REFUSAL: sum(lab(a) == labels.REFUSAL for a in noise),
                   "n": len(noise)}
    per_family = {}
    for fam in sorted({a.get("family", "") for a in cells if a.get("family")}):
        xs = [a for a in cells if a.get("family") == fam]
        ok = sum(lab(a) in [norm(e) for e in a["acceptable"]] for a in xs)
        exact = sum(lab(a) == norm(a["expected"]) for a in xs)
        bad_det = sum(lab(a) in (labels.SUP, labels.REF)
                      and lab(a) not in [norm(e) for e in a["acceptable"]] for a in xs)
        per_family[fam] = {"n": len(xs), "acceptable": ok, "expected_exact": exact,
                           "unacceptable_determinate": bad_det, "wilson95": wilson(ok, len(xs)),
                           "fixed_claim": bool(xs[0].get("fixed_claim")),
                           **({"small_n": True} if len(xs) < 30 else {})}
    return {"A_accuracy": block1, "over_strictness_A_refusals": over,
            "Det_A": round(det_A, 4), "negative_cells": len(neg),
            "noise_answered_NEI_vs_REFUSAL": noise_split,
            "FDR_neg": round(fdr, 4), "FDR_neg_SUP": round(wrong_sup / len(neg), 4) if neg else 0.0,
            "FDR_neg_REF": round(wrong_ref / len(neg), 4) if neg else 0.0,
            "FDR_strict": round(fdr_strict, 4), "Acc_A": round(acc_A, 4),
            "J_gate": round(acc_A - fdr_strict, 4), "per_arm": per_arm, "per_family": per_family}


def necessity(arms_doc: dict) -> dict:
    """Where the lexical oracle reports the SAME thing about this arm's evidence as about A's, no code-only
    reader can separate the arms: only a judge with knowledge of the subject can. Reported per family,
    deterministic, free. This is our code-only analogue of the per-sample evidence-necessity score of
    EGR-FV (EMNLP 2026 main, 10.18653/2026.emnlp-main.813), which needs a trained verifier to compute."""
    from number_check import distortion
    bad = ("UNIT_MISMATCH", "SCALE_MISMATCH", "DATE_SHIFT", "VALUE_MISMATCH")

    def verdict(claim: str, evidence: list) -> tuple:
        """What the lexical oracle sees in ALL the evidence put together, not just the first item:
        an arm that carries the supporting sentence plus a contradicting one is not the same as A."""
        if not evidence:
            return ("NO_EVIDENCE",)
        kinds = set()
        for e in evidence:
            k = distortion(claim, e["text"])
            kinds.add("CONTRADICTS" if k in bad else "MATCHES" if k in ("MATCH", "ROUNDED_MATCH") else k)
        return tuple(sorted(kinds))

    by: dict = {}
    for a in arms_doc["arms"]:
        by.setdefault(a["claim_id"], {})[a["arm"]] = a
    per_fam, hard = {}, []
    for cid, arms in sorted(by.items()):
        a = arms.get("A_genuine")
        if not a:
            continue
        base = verdict(a["claim"], a["evidence"])
        for arm, x in arms.items():
            if arm == "A_genuine" or x.get("anchor"):
                continue
            seen = verdict(x["claim"], x["evidence"])
            st = per_fam.setdefault(x.get("family", ""), {"n": 0, "oracle_can_tell": 0})
            st["n"] += 1
            st["oracle_can_tell"] += seen != base
            if seen == base:
                hard.append(f"{cid}:{arm}")
    for st in per_fam.values():
        st["share_oracle_cannot_tell"] = round(1 - st["oracle_can_tell"] / st["n"], 4) if st["n"] else None
    return {"by_family": dict(sorted(per_fam.items())), "cells_count": len(hard),
            "cells_where_oracle_cannot_tell": hard[:24]}


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
    if "--families" in sys.argv:
        arms_doc = json.load(open("arms_v2.json", encoding="utf-8"))
        manifest = json.load(open("ARM_MANIFEST_v2.json", encoding="utf-8"))
        for name, judge in (("perfect judge", perfect_judge(manifest)),
                            ("oracle_only", oracle_only(arms_doc["arms"])),
                            ("diff_engine", diff_engine(arms_doc["arms"]))):
            s = score(manifest, judge)
            print(f"\n=== {name}: J_gate={s['J_gate']:.4f}, Acc_A={s['Acc_A']:.4f} — by construction family ===")
            for fam, v in s["per_family"].items():
                print(f"  {fam:36s} cells={v['n']:>3} expected_exact={v['expected_exact']:>3} "
                      f"acceptable={v['acceptable']:>3} unacceptable_determinate={v['unacceptable_determinate']:>3}"
                      f"{' [small n]' if v.get('small_n') else ''}"
                      f"{' [fixed-claim]' if v['fixed_claim'] else ''}")
        nec = necessity(arms_doc)
        print("\n=== evidence necessity: arms whose oracle verdict equals A's (a lexical reader cannot tell them apart) ===")
        for fam, v in nec["by_family"].items():
            print(f"  {fam:36s} cells={v['n']:>3} oracle_can_tell={v['oracle_can_tell']:>3} "
                  f"share_indistinguishable={v['share_oracle_cannot_tell']}")
        print("cells where the oracle says the same as on A:", nec["cells_count"])
        calls = sum(1 for a in arms_doc["arms"] if a["evidence"])
        print(f"judge calls in one full run: {calls} (arms {len(arms_doc['arms'])}, "
              f"empty-evidence arms are cut by code before the model)")
        return 0
    if "--runs" in sys.argv:
        manifest = json.load(open("ARM_MANIFEST_v2.json", encoding="utf-8"))
        runs = json.load(open(sys.argv[sys.argv.index("--runs") + 1], encoding="utf-8"))
        print(json.dumps(score_runs(manifest, runs), ensure_ascii=False, indent=1))
        return 0
    path = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
    if not path:
        print(__doc__)
        return 2
    manifest = json.load(open("ARM_MANIFEST_v2.json", encoding="utf-8"))
    got = json.load(open(path, encoding="utf-8"))
    out = score(manifest, got)
    out["forecast_diagnostic"] = forecast_diagnostic(manifest, got)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
