#!/usr/bin/env python3
"""
scoring.py — the scoring contract for the 238-arm set.

Deterministic. Stdlib only. No model called.

Usage:
    python3 scoring.py results.json          # score one judge's results
    python3 scoring.py --baselines           # score the reference baselines
    python3 scoring.py --selftest            # prove the scorer behaves

Input: a results file, JSON:
    [{"claim_id": "...", "arm": "A_genuine", "label": "SUPPORTED"}, ...]
or {"results": [ ... ]}. Labels: SUPPORTED | REFUTED | NOT_ENOUGH_INFO | REFUSAL,
with the v1.6 synonyms folded (SUP/OK/CONTRADICTED/NEI/UNTESTED/...).

There is NO single aggregate over the 238 arms. The report is five blocks:
  1. A accuracy                    (positive arms, determinate label expected)
  2. negative-arm false-SUPPORTED  (credulity rate across B/C/F/G)
  3. over-strictness               (A arms refused or abstained)
  4. REFUTED-class accuracy        (A arms whose expected label is REFUTED)
  5. SUPPORTED-class over-strictness (A arms whose expected label is SUPPORTED)

E (contradicting) is small-n: 13 arms, reported with a Wilson 95% interval and
labelled small-n, never as a stable rate. Anchors are excluded from accuracy and
reported separately.
"""
import json, sys, math

NEI, REF = "NOT_ENOUGH_INFO", "REFUSAL"
SYNONYMS = {
    "SUPPORTED": {"SUPPORTED", "SUP", "OK", "EXACT_MATCH"},
    "REFUTED": {"REFUTED", "CONTRADICTED"},
    NEI: {NEI, "NEI", "UNSUPPORTED_NUMBER", "NOT_ENOUGH_INFORMATION", "UNRESOLVED"},
    REF: {REF, "UNTESTED", "UNTESTABLE", "NO_NUMBERS", "REFUSED", "ABSTAIN"},
}

def norm(label):
    if label is None:
        return "MISSING"
    u = str(label).strip().upper().replace(" ", "_").replace("-", "_")
    for canon, forms in SYNONYMS.items():
        if u in forms:
            return canon
    return u

def wilson(k, n, z=1.96):
    """Wilson score interval, 95%."""
    if n == 0:
        return (0.0, 0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, max(0.0, (c - m) / d), min(1.0, (c + m) / d))

def load(path):
    d = json.load(open(path))
    if isinstance(d, dict):
        d = d.get("results", [])
    return {(r["claim_id"], r["arm"]): norm(r.get("label")) for r in d}

def score(results, manifest):
    arms = manifest["arms"]
    by = {(a["claim_id"], a["arm"]): a for a in arms}

    # --- block 1/3: the positive A block ---
    a_arms = [a for a in arms if a["arm"] == "A_genuine" and not a["anchor"]]
    a_hit = a_refused = a_abstained = a_wrongdir = a_missing = 0
    refuted_bucket = [0, 0]
    supported_bucket = [0, 0]
    a_misses = []
    for a in a_arms:
        got = results.get((a["claim_id"], "A_genuine"), "MISSING")
        want = a["expected"]
        if got == "MISSING":
            a_missing += 1
            continue
        ok = got in a["acceptable"]
        if ok:
            a_hit += 1
        else:
            if got == REF:
                a_refused += 1
            elif got == NEI:
                a_abstained += 1
            else:
                a_wrongdir += 1
            a_misses.append({"claim_id": a["claim_id"], "expected": want, "got": got})
        if want == "REFUTED":
            refuted_bucket[1] += 1
            refuted_bucket[0] += 1 if ok else 0
        elif want == "SUPPORTED":
            supported_bucket[1] += 1
            supported_bucket[0] += 1 if ok else 0

    n_a = len(a_arms) - a_missing

    # --- block 2: negative arms, credulity ---
    neg_arms = [a for a in arms if a["class"] == "negative" and not a["anchor"]]
    cred = {}
    neg_total = neg_n = 0
    for a in neg_arms:
        got = results.get((a["claim_id"], a["arm"]), "MISSING")
        if got == "MISSING":
            continue
        neg_n += 1
        neg_total += 1
        cred.setdefault(a["arm"], [0, 0])
        cred[a["arm"]][1] += 1
        if got == "SUPPORTED":
            cred[a["arm"]][0] += 1
    cred_total = sum(v[0] for v in cred.values())

    # --- block 4: E small-n ---
    e_arms = [a for a in arms if a["arm"] == "E_contradicting"]
    e_hit = e_n = 0
    for a in e_arms:
        got = results.get((a["claim_id"], "E_contradicting"), "MISSING")
        if got == "MISSING":
            continue
        e_n += 1
        if got in a["acceptable"]:
            e_hit += 1

    p, lo, hi = wilson(e_hit, e_n)

    return {
        "A_block": {
            "n": n_a,
            "accuracy": None if not n_a else round(a_hit / n_a, 4),
            "hits": a_hit,
            "over_strict_refusal": a_refused,
            "over_strict_abstention": a_abstained,
            "wrong_direction": a_wrongdir,
            "missing": a_missing,
            "over_strictness_rate": None if not n_a else round((a_refused + a_abstained) / n_a, 4),
        },
        "negative_block": {
            "n": neg_n,
            "false_SUPPORTED": cred_total,
            "false_SUPPORTED_rate": None if not neg_n else round(cred_total / neg_n, 4),
            "by_arm": {k: {"false_supported": v[0], "n": v[1],
                           "rate": round(v[0] / v[1], 4) if v[1] else None}
                       for k, v in sorted(cred.items())},
        },
        "refuted_class": {
            "n": refuted_bucket[1],
            "accuracy": None if not refuted_bucket[1] else round(refuted_bucket[0] / refuted_bucket[1], 4),
        },
        "supported_class": {
            "n": supported_bucket[1],
            "over_strictness": None if not supported_bucket[1]
                               else round((supported_bucket[1] - supported_bucket[0]) / supported_bucket[1], 4),
        },
        "E_contradicting": {
            "n": e_n,
            "accuracy": None if not e_n else round(p, 4),
            "wilson95": [round(lo, 4), round(hi, 4)],
            "small_n": e_n < 30,
        },
        "anchors_excluded": manifest.get("anchors", []),
        "A_misses": a_misses[:12],
    }

def report(name, s):
    print(f"\n=== {name} ===")
    a, n, r, sup, e = (s["A_block"], s["negative_block"],
                       s["refuted_class"], s["supported_class"], s["E_contradicting"])
    print(f"  1. A accuracy                 {a['hits']}/{a['n']}  = {a['accuracy']}")
    print(f"  2. negative false-SUPPORTED   {n['false_SUPPORTED']}/{n['n']}  = {n['false_SUPPORTED_rate']}")
    for arm, v in n["by_arm"].items():
        print(f"       {arm:18} {v['false_supported']}/{v['n']}  = {v['rate']}")
    print(f"  3. over-strictness (A)        {a['over_strict_refusal']} refused + "
          f"{a['over_strict_abstention']} abstained  = {a['over_strictness_rate']}")
    print(f"  4. REFUTED-class accuracy     {r['accuracy']}  (n={r['n']})")
    print(f"  5. SUPPORTED-class over-strict {sup['over_strictness']}  (n={sup['n']})")
    print(f"  E small-n                     {e['accuracy']}  95% CI {e['wilson95']}  n={e['n']}")
    if a["missing"]:
        print(f"  MISSING results: {a['missing']} A arms")

# ---------------- baselines ---------------------------------------------
def baselines(manifest):
    """Trivial baselines plus a diff-engine. These are what a real judge has to
    beat; if a baseline scores as well, the set is not measuring judgment."""
    import difflib
    arms = manifest["arms"]
    out = {}

    for const in ("SUPPORTED", NEI, REF):
        out[f"always_{const}"] = {(a["claim_id"], a["arm"]): const for a in arms}

    # diff-engine: SUPPORTED when the claim is near-identical to the evidence,
    # REFUTED when it is close but not equal, NEI otherwise. A pure string
    # matcher, which is what a judge must be shown to beat.
    def diff_label(a):
        ev = next((x for x in [a] if a["n_evidence"]), None)
        if not ev:
            return NEI
        return None  # decided below with the text

    txt = {}
    for a in arms:
        txt[(a["claim_id"], a["arm"])] = a["claim"]
    # rebuild with evidence text from the arm set
    return out, txt

def diff_engine(manifest, arms_src):
    import difflib
    res = {}
    for a in manifest["arms"]:
        key = (a["claim_id"], a["arm"])
        src = next(x for x in arms_src if x["claim_id"] == a["claim_id"] and x["arm"] == a["arm"])
        if not src["evidence"]:
            res[key] = NEI
            continue
        ratio = difflib.SequenceMatcher(None, src["claim"], src["evidence"][0]["text"]).ratio()
        if ratio >= 0.95:
            res[key] = "SUPPORTED"
        elif ratio >= 0.70:
            res[key] = "REFUTED"
        else:
            res[key] = NEI
    return res

def main():
    manifest = json.load(open("ARM_MANIFEST.json"))
    if "--selftest" in sys.argv:
        arms_src = json.load(open("arms_expanded.json"))["arms"]
        # a perfect judge: every arm gets its expected label
        perfect = {(a["claim_id"], a["arm"]): a["expected"] for a in manifest["arms"]}
        # a credulous judge: everything SUPPORTED
        credulous = {(a["claim_id"], a["arm"]): "SUPPORTED" for a in manifest["arms"]}
        # an abstaining judge: everything NEI
        abstain = {(a["claim_id"], a["arm"]): NEI for a in manifest["arms"]}
        d = diff_engine(manifest, arms_src)
        report("SELFTEST perfect", score(perfect, manifest))
        report("SELFTEST credulous (always SUPPORTED)", score(credulous, manifest))
        report("SELFTEST abstaining (always NEI)", score(abstain, manifest))
        report("SELFTEST diff-engine (string similarity)", score(d, manifest))
        s = score(perfect, manifest)
        ok = (s["A_block"]["accuracy"] == 1.0 and s["negative_block"]["false_SUPPORTED"] == 0
              and s["E_contradicting"]["accuracy"] == 1.0)
        print(f"\nSELFTEST {'PASSED' if ok else 'FAILED'}: a perfect judge must score 1.0 / 0 / 1.0")
        return
    if "--baselines" in sys.argv:
        arms_src = json.load(open("arms_expanded.json"))["arms"]
        for const in ("SUPPORTED", NEI, REF):
            r = {(a["claim_id"], a["arm"]): const for a in manifest["arms"]}
            report(f"BASELINE always {const}", score(r, manifest))
        report("BASELINE diff-engine", score(diff_engine(manifest, arms_src), manifest))
        return
    report(sys.argv[1], score(load(sys.argv[1]), manifest))

if __name__ == "__main__":
    main()
