# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""build_arms_v2_1.py (v2.1 copy of build_arms_v2.py reading mutation_items_v2_1.json): a rebuilt arm set for the null-arm probe, with the invariants of the review checked IN CODE.

Input : mutation_items_v2_1.json (from mutation_set.build over passages_reconstructed.json) and
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
  S_same_document  NEI-CAP "same-document": a non-rationale sentence from the SAME passage. v1 hit this by
                   accident in 24 of 45 G arms; here it is a designed family with its own expected label.
  H_high_overlap   NEI-CAP "BM25 near-miss": the highest lexical overlap obtainable outside the passage while
                   still insufficient. Their verifiers fell hardest on this family.
  M_diluted        A's supporting sentence first plus one unrelated sentence: the label must stay what A's is.
  R_pair           two sources pointing opposite ways, second one CONSTRUCTED and tagged as constructed;
                   expects REFUSAL, because the contract says record both and average neither.
Every cell carries `family` (which construction produced its expected label) and `fixed_claim` (the claim is
held while only the evidence changes), so no aggregate can hide which construction a score came from.
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
TYPED_ARMS = ("opinion_or_forecast_as_fact", "plausible_fabricated_citation", "two_genuine_sources_conflict")
NEGATIVE_ARMS = ("B_empty", "C_noise_length", "C_num_noise", "D_noise_topic", "F_unrelated", "G_deranged",
                 "S_same_document", "H_high_overlap", "R_pair",
                 "P_forecast_own", "P_forecast_weaken", "P_forecast_borrowed", "N_no_source", "R_disagree")
# Construction family of every cell, named after NEI-CAP (Findings of EMNLP 2026,
# 10.18653/2026.findings-emnlp.796) where our evidence condition is theirs, and after our own mechanism where
# it is not. The family says WHICH construction produced the expected label, so no aggregate can hide it.
FAMILY = {"A_genuine": "full_support", "B_empty": "placeholder", "C_noise_length": "length_matched_noise",
          "C_num_noise": "length_matched_noise_with_claim_numbers", "D_noise_topic": "same_topic_non_rationale",
          "E_contradicting": "contradicting_distortion", "E_restore": "restored_match",
          "F_unrelated": "random_irrelevant", "G_deranged": "other_document_substitution",
          "S_same_document": "same_document_non_rationale", "H_high_overlap": "high_overlap_insufficient",
          "M_diluted": "diluted_support", "R_pair": "conflicting_sources",
          "P_forecast_own": "forecast_as_fact", "P_forecast_weaken": "forecast_weakened",
          "P_forecast_borrowed": "forecast_borrowed_evidence", "N_no_source": "cited_source_absent",
          "R_disagree": "conflicting_sources"}
FAMILIES = tuple(dict.fromkeys(FAMILY.values()))
# Their "fixed-claim" diagnostic: the claim is held, only the evidence changes. In our set that is a property
# of the arm, so it is recorded instead of being inferred from the table layout.
FIXED_CLAIM_ARMS = ("C_noise_length", "C_num_noise", "D_noise_topic", "F_unrelated", "G_deranged",
                    "S_same_document", "H_high_overlap", "M_diluted", "R_pair", "E_contradicting", "E_restore")
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
    return any(f.kind in ("MATCH", "ROUNDED_MATCH", "YEAR_UNSTATED") for f in reconcile(claim, evidence))


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
    rep_lists: dict[str, list] = {"e_absent": [], "d_absent": [], "c_num_absent": [], "g_notes": [],
                                  "s_absent": [], "h_absent": [], "m_absent": [], "r_pair_absent": [],
                                  "t_null_search": []}

    def add(item, arm, evidence, expected, acceptable, **extra):
        arms.append({"claim_id": item["id"], "arm": arm, "claim": item["claim"], "evidence": evidence,
                     "expected": expected, "acceptable": acceptable,
                     "negative": arm in NEGATIVE_ARMS, "anchor": item["id"] in ANCHORS,
                     "family": FAMILY[arm], "fixed_claim": arm in FIXED_CLAIM_ARMS, **extra})
        rep[arm] += 1

    for i, it in enumerate(kept):
        cid, g = it["id"], it["evidence"][0]
        gtext, src, pid = g["text"], g.get("source", ""), it["passage_id"]
        sub = "A_supported" if it["expected"] == SUP else "A2_distorted_claim"
        ev = lambda t, tag: [{"text": t, "source": src, "arm_tag": tag}]
        add(it, "A_genuine", ev(gtext, "A"), it["expected"], [it["expected"]], subclass=sub)
        # S. Hope, 31 Oct: an empty arm must be a refusal. NEI is a label, not a refusal, so it is not acceptable here.
        add(it, "B_empty", [], REFUSAL, [REFUSAL])
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
        ct = None
        if sub == "A_supported":
            ct = contradict(gtext, it["claim"])
            if ct:
                add(it, "E_contradicting", ev(ct[1], "E"), REF, [REF], mutation=ct[0])
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
        f_choice = None
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
            if arm == "F_unrelated":
                f_choice = (o, t)
        # S: NEI-CAP "same-document" — a non-rationale sentence from the SAME passage. v1 produced this by
        # accident (24 of 45 G arms); here it is a designed family, so the accident becomes a measurement.
        sd = next((o["evidence"][0]["text"] for o in kept
                   if o["passage_id"] == pid and o["id"] != cid and o["evidence"][0]["text"] != gtext
                   and not shares_quantity(it["claim"], o["evidence"][0]["text"])), None)
        if sd:
            add(it, "S_same_document", ev(sd, "S"), NEI, [NEI, REFUSAL])
        else:
            rep_lists["s_absent"].append(cid)
        # H: their "BM25 near-miss" — the highest lexical overlap available outside the passage, still
        # insufficient. This is the family their verifiers failed on, so it is built first, not last.
        tok = set(re.findall(r"[a-z]{4,}", it["claim"].lower()))
        best, hit = 0.0, None
        for o in kept:
            if o["passage_id"] == pid:
                continue
            t = o["evidence"][0]["text"]
            if shares_quantity(it["claim"], t) or expected_on_unrelated(it["claim"], t)["expected"] != "NEI_EXPECTED":
                continue
            sc = len(tok & set(re.findall(r"[a-z]{4,}", t.lower()))) / max(1, len(tok))
            if sc > best:
                best, hit = sc, (o, t)
        if hit:
            add(it, "H_high_overlap", [{"text": hit[1], "source": hit[0]["evidence"][0].get("source", ""),
                                       "arm_tag": "H"}], NEI, [NEI, REFUSAL],
                borrowed_from=hit[0]["id"], overlap=round(best, 3))
        else:
            rep_lists["h_absent"].append(cid)
        # M: support present but buried — A's sentence first, an unrelated sentence second. Expects the SAME
        # label as A: a judge that needs the evidence undiluted is not reading it.
        if f_choice:
            add(it, "M_diluted", [{"text": gtext, "source": src, "arm_tag": "A"},
                                  {"text": f_choice[1], "source": f_choice[0]["evidence"][0].get("source", ""),
                                   "arm_tag": "M"}],
                it["expected"], [it["expected"]], borrowed_from=f_choice[0]["id"])
        else:
            rep_lists["m_absent"].append(cid)
        # R_pair: two sources pointing opposite ways. Expected REFUSAL: the contract says record both,
        # average neither. The second source is CONSTRUCTED (we have no second publication), and is tagged
        # as such so nobody reads it as a real citation.
        second = None
        if sub == "A_supported" and ct:
            second = {"text": ct[1], "source": "constructed_variant_of_same_source", "arm_tag": "R2"}
        elif sub == "A2_distorted_claim":
            second = {"text": it["claim"], "source": "constructed_second_hand_restatement", "arm_tag": "R2"}
        if second:
            add(it, "R_pair", [{"text": gtext, "source": src, "arm_tag": "R1"}, second],
                REFUSAL, [REFUSAL], constructed_pair=True)
        else:
            rep_lists["r_pair_absent"].append(cid)
    build_typed(run12, add, rep_lists)
    report = {"claims": n, "arms": len(arms), "by_arm": dict(rep), **rep_lists}
    return arms, report


def typed_claims(run12: list[dict]) -> list[dict]:
    return [c for c in run12 if c["type"] in TYPED_ARMS]


def weakening_candidate(c: dict) -> dict | None:
    """A sentence from THIS claim's own pools that argues the forecast down. Cross-passage reuse is
    excluded by construction, so the honest answer is usually 'none' and the arm becomes a null search."""
    cues = ("restart", "restor", "reopen", "resum", "returns", "come back", "close", "surplus", "no longer")
    own = {e["text"] for e in c["evidence"]}
    for pool in ("topic_noise", "unrelated"):
        for e in c.get(pool, []):
            low = e["text"].lower()
            if e["text"] not in own and any(k in low for k in cues) and not shares_quantity(c["claim"], e["text"]):
                return e
    return None


def build_typed(run12, add, rep_lists) -> None:
    """Arms for the three claim types S. Hope named, on their ORIGINAL claim text. The mutation set
    rewrites every claim into a quote-verifiable sentence, which is exactly what deletes the forecast
    case: a forecast has no truth-apt referent, so it can only be refused, never matched."""
    tc = typed_claims(run12)
    for c in sorted(tc, key=lambda x: x["id"]):
        item = {"id": "typed." + c["id"], "claim": c["claim"], "passage_id": c["id"], "evidence": c["evidence"]}
        src = c["evidence"][0].get("source", "")
        if c["type"] == "opinion_or_forecast_as_fact":
            add(item, "P_forecast_own", [{"text": c["evidence"][0]["text"], "source": src, "arm_tag": "P"}],
                REFUSAL, [REFUSAL], subclass="T_forecast_own")
            w = weakening_candidate(c)
            if w:
                add(item, "P_forecast_weaken", [{"text": w["text"], "source": w.get("source", ""), "arm_tag": "Pw"}],
                    REFUSAL, [REFUSAL], subclass="T_forecast_weaken")
            else:
                rep_lists["t_null_search"].append({"claim_id": item["id"], "pools_searched": ["topic_noise", "unrelated"]})
                add(item, "P_forecast_weaken", [], REFUSAL, [REFUSAL], subclass="T_forecast_weaken",
                    no_source_available=True)
            b = next((x for x in tc if x["id"] != c["id"] and x["evidence"][0]["text"] != c["evidence"][0]["text"]
                      and not shares_quantity(c["claim"], x["evidence"][0]["text"])), None)
            if b:
                add(item, "P_forecast_borrowed", [{"text": b["evidence"][0]["text"],
                                                   "source": b["evidence"][0].get("source", ""), "arm_tag": "Pb"}],
                    REFUSAL, [REFUSAL], borrowed_from="typed." + b["id"], subclass="T_forecast_borrowed")
        elif c["type"] == "plausible_fabricated_citation":
            rep_lists["t_null_search"].append({"claim_id": item["id"], "pools_searched": ["named source, no list"]})
            add(item, "N_no_source", [], REFUSAL, [REFUSAL], subclass="T_no_source", no_source_available=True)
        elif c["type"] == "two_genuine_sources_conflict" and len(c["evidence"]) > 1:
            add(item, "R_disagree", [{"text": e["text"], "source": e.get("source", ""), "arm_tag": "R"}
                                     for e in c["evidence"]], REFUSAL, [REFUSAL], subclass="T_disagree")


def main() -> int:
    items = json.load(open("mutation_items_v2_1.json", encoding="utf-8"))
    run12 = json.load(open("claims_run12.json", encoding="utf-8"))
    arms, report = build(items, run12)
    json.dump({"version": "v2.1", "arms": arms}, open("arms_v2_1.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    json.dump({"version": "v2.1", "arms": [{k: a[k] for k in ("claim_id", "arm", "expected", "acceptable", "negative",
                                                            "anchor", "family", "fixed_claim")}
                                         | {"subclass": a.get("subclass", "")}
                                         | ({"overlap": a["overlap"]} if "overlap" in a else {})
                                         | ({"constructed_pair": True} if a.get("constructed_pair") else {})
                                         | ({"no_source_available": True} if a.get("no_source_available") else {})
                                         for a in arms]},
              open("ARM_MANIFEST_v2_1.json", "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
