# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""build_arms_v2.py: a rebuilt arm set for the null-arm probe, with the invariants of the review checked IN CODE.

Input : mutation_items_v2.json (from mutation_set.build over passages_reconstructed.json) and
        claims_run12.json (the 12 claims of the first live run: topic_noise per passage, S. Hope).
Output: arms_v2.json and ARM_MANIFEST_v2.json (expected / acceptable labels of every arm).
No model is called. Deterministic: noise is seeded from the claim id.

Arms per claim (where constructible):
  A_genuine        the passage sentence the claim was built from. Sub-class A_supported (expects
                   SUPPORTED) or A2_distorted_claim (the claim already carries a distortion: expects REFUTED).
  B_empty          no evidence.
  C_noise_length   length-matched noise (+-5 %), NO numbers, the SAME source as A (v1 had source "").
  C_num_noise      length-matched noise that contains the claim's own numbers/dates/units in meaningless
                   surroundings, same source as A. Separates "noise" from "no numbers / no source".
  D_noise_topic    same-subject text with no comparable quantity (claims_run12.json), oracle-checked.
  E_contradicting  only for A_supported: the passage with ONE validated distortion (functions of
                   mutation_set, so names such as "Phillips 66" are never shifted), oracle-checked.
  E_restore        only for A2_distorted_claim: the evidence is brought into line with the (distorted) claim,
                   expects SUPPORTED. Catches a judge that answers from memory of the genuine passage.
  F_unrelated      another passage's genuine sentence; passage_id MUST differ (asserted).
  G_deranged       the genuine sentence of another claim; text AND passage_id MUST differ (asserted).
F and G: REFUTED is acceptable only where arm_check.expected_on_unrelated says REFUTED_ADMISSIBLE (S2.10);
a candidate that matches a quantity of the claim is rejected (the label would no longer be "by accident").
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import sys
from collections import Counter

import mutation_set as ms
from arm_check import check_distorted, expected_on_unrelated
from number_check import _dates, _quantities, reconcile

NEI, REFUSAL, SUP, REF = "NOT_ENOUGH_INFO", "REFUSAL", "SUPPORTED", "REFUTED"
WORDS = ("the of and to in for on with as by from that this which at be been were was is are has have had it "
         "its not but or if then than so such over under between across report record volume measure sample "
         "period total change noted stated observed figure value table entry column row document archive "
         "register ledger account filing notice summary detail item list sheet page file morning evening "
         "season annual weekly daily monthly standard ordinary plain general common regular simple basic "
         "formal neutral").split()
ANCHORS = {"c10.s0.identity"}   # prose without a number or a quotation: the oracles cannot grade it


def rng_for(cid: str, salt: str = "") -> random.Random:
    return random.Random(int(hashlib.sha256((cid + salt).encode()).hexdigest()[:12], 16))


def noise_words(target: int, rng: random.Random) -> str:
    out, n = [], 0
    while n < target:
        w = rng.choice(WORDS)
        if n + len(w) + (1 if out else 0) > target * 1.05:
            # try a word that lands inside the window; otherwise stop at the closest
            fit = [x for x in WORDS if target * 0.95 <= n + len(x) + (1 if out else 0) <= target * 1.05]
            if not fit:
                break
            w = rng.choice(fit)
        out.append(w)
        n += len(w) + (1 if len(out) > 1 else 0)
        if n >= target * 0.95:
            break
    return " ".join(out)


def claim_tokens(claim: str) -> list[str]:
    dts, spans = _dates(claim)
    toks = [d.text for d in dts] + [q.text for q in _quantities(claim, spans)]
    seen, out = set(), []
    for t in toks:
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


def num_noise(claim: str, text: str, cid: str) -> str | None:
    toks = claim_tokens(claim)
    target = len(text)
    rng = rng_for(cid, "num")
    for _ in range(40):
        budget = target - sum(len(t) + 1 for t in toks)
        if budget < 8:
            return None
        base = noise_words(budget, rng).split()
        words = base[:]
        for t in toks:
            words.insert(rng.randint(0, len(words)), t)
        s = " ".join(words)
        if 0.95 * target <= len(s) <= 1.05 * target:
            return s
    return None


def shares_quantity(claim: str, evidence: str) -> bool:
    return any(f.kind in ("MATCH", "ROUNDED_MATCH") for f in reconcile(claim, evidence))


def contradict(sent: str, claim: str) -> tuple[str, str] | None:
    """One validated distortion of the PASSAGE so that it refutes the claim (which states the original)."""
    for name in ("unit_swap", "scale_shift", "value_shift", "year_shift", "quote_alteration"):
        fn = ms.MUTATIONS[name][0]
        cand = fn(sent)
        if cand and cand != sent and check_distorted(claim, cand)["status"] == "VALID":
            return name, cand
    return None


def build(items: list[dict], run12: list[dict]) -> tuple[list[dict], dict]:
    kept = [x for x in items if not x.get("dropped_reason")]
    topic = {c["id"]: c.get("topic_noise", []) for c in run12}
    n = len(kept)
    arms, rep = [], Counter()
    rep_lists: dict[str, list] = {"e_absent": [], "d_absent": [], "c_num_absent": [], "g_notes": []}

    def add(item, arm, evidence, expected, acceptable, **extra):
        arms.append({"claim_id": item["id"], "arm": arm, "claim": item["claim"], "evidence": evidence,
                     "expected": expected, "acceptable": acceptable,
                     "negative": arm in ("B_empty", "C_noise_length", "C_num_noise", "D_noise_topic", "F_unrelated", "G_deranged"),
                     "anchor": item["id"] in ANCHORS, **extra})
        rep[arm] += 1

    for i, it in enumerate(kept):
        cid, g = it["id"], it["evidence"][0]
        gtext, src, pid = g["text"], g.get("source", ""), it["passage_id"]
        sub = "A_supported" if it["expected"] == SUP else "A2_distorted_claim"
        ev = lambda t, tag: [{"text": t, "source": src, "arm_tag": tag}]
        add(it, "A_genuine", ev(gtext, "A"), it["expected"], [it["expected"]], subclass=sub)
        add(it, "B_empty", [], NEI, [NEI, REFUSAL])
        add(it, "C_noise_length", ev(noise_words(len(gtext), rng_for(cid)), "C"), NEI, [NEI, REFUSAL])
        cn = num_noise(it["claim"], gtext, cid)
        if cn:
            add(it, "C_num_noise", ev(cn, "Cn"), NEI, [NEI, REFUSAL])
        else:
            rep_lists["c_num_absent"].append(cid)
        # D: same-subject text, no comparable quantity
        dtxt = next((t["text"] for t in topic.get(pid, [])
                     if expected_on_unrelated(it["claim"], t["text"])["expected"] == "NEI_EXPECTED"
                     and not shares_quantity(it["claim"], t["text"])), None)
        if dtxt:
            add(it, "D_noise_topic", ev(dtxt, "D"), NEI, [NEI, REFUSAL])
        else:
            rep_lists["d_absent"].append(cid)
        # E / E_restore
        if sub == "A_supported":
            c = contradict(gtext, it["claim"])
            if c:
                add(it, "E_contradicting", ev(c[1], "E"), REF, [REF], mutation=c[0])
            else:
                rep_lists["e_absent"].append(cid)
        else:
            add(it, "E_restore", ev(it["claim"], "Er"), SUP, [SUP])
        # F and G: candidates scanned cyclically, hard invariants
        def pick(start, need_other_passage):
            for off in range(n):
                j = (i + start + off) % n
                o = kept[j]
                t = o["evidence"][0]["text"]
                if j == i or t == gtext or (need_other_passage and o["passage_id"] == pid):
                    continue
                if shares_quantity(it["claim"], t):
                    continue
                return o, t
            return None, None
        for arm, start in (("F_unrelated", 7), ("G_deranged", 1)):
            o, t = pick(start, True)
            if o is None:
                o, t = pick(start, False)
                rep_lists["g_notes"].append(f"{cid}:{arm}: no other-passage candidate, same passage used")
            if o is None:
                rep_lists["g_notes"].append(f"{cid}:{arm}: no candidate")
                continue
            exp = expected_on_unrelated(it["claim"], t)
            acc = [NEI, REFUSAL] + ([REF] if exp["expected"] == "REFUTED_ADMISSIBLE" else [])
            add(it, arm, [{"text": t, "source": o["evidence"][0].get("source", ""), "arm_tag": arm[0]}],
                NEI, acc, borrowed_from=o["id"], rule_S2_10=exp["expected"])
    report = {"claims": n, "arms": len(arms), "by_arm": dict(rep), **rep_lists}
    return arms, report


def main() -> int:
    items = json.load(open("mutation_items_v2.json", encoding="utf-8"))
    run12 = json.load(open("claims_run12.json", encoding="utf-8"))
    arms, report = build(items, run12)
    json.dump({"version": "v2", "arms": arms}, open("arms_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"version": "v2", "arms": [{k: a[k] for k in ("claim_id", "arm", "expected", "acceptable", "negative", "anchor")}
                                         | {"subclass": a.get("subclass", "")} for a in arms]},
              open("ARM_MANIFEST_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
