# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""Tests for arm set v2: every invariant from the review, checked on the shipped arms_v2_1.json. Run: python3 test_v2_1.py"""
import json
import re
import sys

import build_arms_v2_1 as b
import labels
import stability
from arm_check import check_distorted, expected_on_unrelated
from number_check import distortion, reconcile
from scoring_v2 import baselines, constant_judge, forecast_diagnostic, necessity, perfect_judge, score, score_runs


def shares(claim, text):
    return any(f.kind in ("MATCH", "ROUNDED_MATCH") for f in reconcile(claim, text))


def overlap(claim, text):
    """Same token definition as the generator: content words of four letters or more, share over the claim."""
    a = set(re.findall(r"[a-z]{4,}", claim.lower()))
    t = set(re.findall(r"[a-z]{4,}", text.lower()))
    return len(a & t) / max(1, len(a))

ARMS = json.load(open("arms_v2_1.json", encoding="utf-8"))["arms"]
MAN = json.load(open("ARM_MANIFEST_v2_1.json", encoding="utf-8"))
ITEMS = {x["id"]: x for x in json.load(open("mutation_items_v2_1.json", encoding="utf-8"))}
OLD = {x["id"]: x for x in json.load(open("../null-arm-checks/mutation_items_no_second_refinery.json", encoding="utf-8"))}
BY = {}
for a in ARMS:
    BY.setdefault(a["claim_id"], {})[a["arm"]] = a
MUT = {c: d for c, d in BY.items() if "A_genuine" in d}   # the 48 mutation claims; typed.* claims have their own arms
ev = lambda a: a["evidence"][0]["text"] if a["evidence"] else ""


def test_G_never_gets_its_own_evidence_or_its_own_passage():
    n = 0
    for cid, d in MUT.items():
        g = d["G_deranged"]
        assert ev(g) != ev(d["A_genuine"]), cid
        assert ITEMS[g["borrowed_from"]]["passage_id"] != ITEMS[cid]["passage_id"], cid
        n += 1
    assert n == 49   # v2.1: 49 kept items (v2: 48)


def test_F_passage_always_differs():
    assert all(ITEMS[d["F_unrelated"]["borrowed_from"]]["passage_id"] != ITEMS[c]["passage_id"] for c, d in MUT.items())


def test_S2_10_is_applied_not_assumed():
    for a in ARMS:
        if a["arm"] in ("F_unrelated", "G_deranged"):
            exp = expected_on_unrelated(a["claim"], ev(a))["expected"]
            assert (labels.REF in a["acceptable"]) == (exp == "REFUTED_ADMISSIBLE"), a["claim_id"]
            assert not any(f.kind in ("MATCH", "ROUNDED_MATCH") for f in reconcile(a["claim"], ev(a)))


def test_known_generation_artefacts_are_gone():
    blob = json.dumps(ARMS, ensure_ascii=False) + json.dumps(list(ITEMS.values()), ensure_ascii=False)
    for bad in ("Phillips 82", "12–11 September", "mthree", "the main reasons"):
        assert bad not in blob, bad


def test_C_keeps_the_source_and_C_num_keeps_the_numbers():
    for cid, d in MUT.items():
        a = d["A_genuine"]
        for arm in ("C_noise_length", "C_num_noise"):
            c = d[arm]
            assert c["evidence"][0]["source"] == a["evidence"][0]["source"] != "", (cid, arm)
            assert 0.95 * len(ev(a)) <= len(ev(c)) <= 1.05 * len(ev(a)), (cid, arm)
        from build_arms_v2_1 import claim_tokens
        assert all(t.lower() in ev(d["C_num_noise"]).lower() for t in claim_tokens(a["claim"])), cid
        assert not any(ch.isdigit() for ch in ev(d["C_noise_length"])), cid


def test_D_exists_and_has_no_comparable_quantity():
    ds = [d["D_noise_topic"] for d in BY.values() if "D_noise_topic" in d]
    assert len(ds) >= 30
    for d in ds:
        assert expected_on_unrelated(d["claim"], ev(d))["expected"] == "NEI_EXPECTED"


def test_E_is_a_validated_distortion_and_E_restore_restores():
    for d in BY.values():
        if "E_contradicting" in d:
            assert check_distorted(d["E_contradicting"]["claim"], ev(d["E_contradicting"]))["status"] == "VALID"
        if "E_restore" in d:
            assert ev(d["E_restore"]) == d["A_genuine"]["claim"] and d["E_restore"]["expected"] == labels.SUP
    assert sum("E_contradicting" in d for d in BY.values()) >= 13


def test_the_four_formerly_dropped_records_are_now_seen():
    for i in ("c01.s0.year_shift", "c12.s0.year_shift", "c12.s1.year_shift", "c12.s1.unit_swap"):
        assert OLD[i].get("dropped_reason") and i in ITEMS
        assert distortion(ITEMS[i]["claim"], ITEMS[i]["evidence"][0]["text"]) in ("DATE_SHIFT", "UNIT_MISMATCH"), i


def test_unit_denominators_and_scale_plus():
    assert distortion("$5.85/gal", "$5.85/bbl") == "UNIT_MISMATCH"
    assert distortion("reached $5.85", "$5.85/gal") == "MATCH"
    assert distortion("80k t/d", "80k t/w") == "UNIT_MISMATCH"
    assert distortion("4M+ barrels per week", "4M+ b/d") == "UNIT_MISMATCH"
    assert distortion("tank of 12,700 m3", "tank of 12,700 m3") == "MATCH"


def test_NEEDS_RECOVERY_is_mapped_and_missing_G_is_not_a_change():
    assert labels.norm("NEEDS_RECOVERY") == labels.NEI
    r = stability.pairs({"c1": {"A_genuine": "SUP", "G_deranged": None}, "c2": {"A_genuine": "SUP", "G_permuted": None}})
    assert r["determinate_A_changed"] == 0


def test_degenerate_judges_cannot_pass_the_gate():
    assert score(MAN, perfect_judge(MAN))["J_gate"] == 1.0
    for l in (labels.SUP, labels.REF, labels.NEI, labels.REFUSAL):
        assert score(MAN, constant_judge(MAN, l))["J_gate"] <= 0.0, l


def test_diff_engine_on_deranged_G_has_no_false_supported():
    b = baselines({"arms": ARMS})["diff_engine"]
    assert b["per_arm"]["G_deranged"]["acceptable"] == b["per_arm"]["G_deranged"]["n"]


def test_empty_arm_requires_a_refusal_not_a_label():
    """S. Hope, 31 Oct: «NEI is a label, not a refusal». An arm with no evidence must be refused. In the
    live run the empty arm gave UNTESTED 12 of 12, so requiring a refusal costs nothing we passed before."""
    bs = [a for a in MAN["arms"] if a["arm"] == "B_empty"]
    assert all(a["expected"] == labels.REFUSAL and a["acceptable"] == [labels.REFUSAL] for a in bs)
    got = {cid: {"B_empty": labels.NEI} for cid in {a["claim_id"] for a in bs}}
    assert score(MAN, got)["per_arm"]["B_empty"]["acceptable"] == 0


def test_forecast_claim_keeps_three_arms_on_its_own_text():
    d = BY["typed.c07"]
    assert {"P_forecast_own", "P_forecast_weaken", "P_forecast_borrowed"} <= set(d)
    assert "will not close" in d["P_forecast_own"]["claim"]
    for arm in d.values():
        assert arm["expected"] == labels.REFUSAL and arm["acceptable"] == [labels.REFUSAL], arm["arm"]
    assert ev(d["P_forecast_borrowed"]) and ev(d["P_forecast_borrowed"]) != ev(d["P_forecast_own"])
    assert d["P_forecast_borrowed"]["borrowed_from"] != "typed.c07"
    m = next(a for a in MAN["arms"] if a["claim_id"] == "typed.c07" and a["arm"] == "P_forecast_weaken")
    assert m["no_source_available"] is True and not d["P_forecast_weaken"]["evidence"]


def test_forecast_diagnostic_separates_contamination_from_credulity():
    def diag(own, bor):
        return forecast_diagnostic(MAN, {"typed.c07": {"P_forecast_own": own,
                                                       "P_forecast_weaken": labels.REFUSAL,
                                                       "P_forecast_borrowed": bor}})["typed.c07"]["diagnostic"]
    assert diag(labels.SUP, labels.SUP).startswith("CREDULITY")
    assert diag(labels.NEI, labels.SUP).startswith("CONTAMINATION")
    assert diag(labels.REFUSAL, labels.REFUSAL).startswith("HOLDS")
    assert diag(labels.NEI, labels.NEI).startswith("SCOPE_NOT_REFUSED")


def test_no_source_claim_requires_untested_not_a_label():
    m = next(a for a in MAN["arms"] if a["arm"] == "N_no_source")
    assert m["claim_id"] == "typed.c08" and m["expected"] == labels.REFUSAL and m["no_source_available"] is True
    assert not BY["typed.c08"]["N_no_source"]["evidence"]


def test_two_conflicting_sources_are_recorded_as_disagreement():
    a = BY["typed.c06"]["R_disagree"]
    assert len(a["evidence"]) == 2 and a["evidence"][0]["text"] != a["evidence"][1]["text"]
    assert a["expected"] == labels.REFUSAL


def test_unstable_across_runs_is_reported_not_averaged():
    """Synthetic triple on purpose: the real pattern he caught was c06 under A = NEI, SUP, NEI
    (judge-probe-on-this-topic/matrix_all_runs.csv). A flip is one unstable cell, not two passes and a miss."""
    sup = [a for a in MAN["arms"] if a["arm"] == "A_genuine" and a["subclass"] == "A_supported" and not a["anchor"]]
    (cid, exp), (cid2, exp2) = (sup[0]["claim_id"], sup[0]["expected"]), (sup[1]["claim_id"], sup[1]["expected"])
    other = labels.NEI if exp == labels.SUP else labels.SUP
    runs = {r: {cid: {"A_genuine": lab}, cid2: {"A_genuine": exp2}} for r, lab in (("r1", exp), ("r2", other), ("r3", exp))}
    r = score_runs(MAN, runs)
    assert [u["claim_id"] for u in r["unstable_A_genuine"]] == [cid], r["unstable_A_genuine"]
    s = r["A_accuracy_requiring_stability"]["A_supported"]
    assert s["n"] == len(sup) and s["stable_correct"] == 1 and s["single_run_correct_would_overstate_by"] == 1


def test_every_cell_carries_a_construction_family():
    """NEI-CAP (Findings of EMNLP 2026): report the construction family alongside the score. Here it is not
    a reporting habit but a field of the artifact, so a score cannot be printed without it."""
    for a in ARMS:
        assert a["family"] == b.FAMILY[a["arm"]], (a["claim_id"], a["arm"], a["family"])
        assert a["family"] in b.FAMILIES, a["family"]
        assert a["fixed_claim"] == (a["arm"] in b.FIXED_CLAIM_ARMS), a["arm"]
    for m in MAN["arms"]:
        assert m.get("family") in b.FAMILIES and "fixed_claim" in m, m["arm"]


def test_S_same_document_is_the_designed_version_of_the_v1_accident():
    """v1 produced same-document evidence by accident in 24 of 45 G arms. S does it on purpose: same passage,
    different sentence, and the claim's own quantities absent, so NEI is the label by construction."""
    n = 0
    for cid, d in MUT.items():
        s = d.get("S_same_document")
        if not s:
            continue
        assert s["claim_id"] == cid and ev(s) != ev(d["A_genuine"])
        assert any(o["passage_id"] == ITEMS[cid]["passage_id"]
                   for o in ITEMS.values() if o["evidence"][0]["text"] == ev(s)), cid
        assert not shares(s["claim"], ev(s)), cid
        assert s["expected"] == labels.NEI and labels.REF not in s["acceptable"], cid
        n += 1
    assert n == 29, n   # v2: 28


def test_H_high_overlap_is_other_passage_and_still_insufficient():
    n = 0
    for cid, d in MUT.items():
        h = d.get("H_high_overlap")
        if not h:
            continue
        assert ITEMS[h["borrowed_from"]]["passage_id"] != ITEMS[cid]["passage_id"], cid
        assert 0 < h["overlap"] <= 1, cid
        assert not shares(h["claim"], ev(h)), cid
        assert h["expected"] == labels.NEI, cid
        n += 1
    assert n == 28, n   # v2: 29


def test_H_beats_the_random_arm_on_overlap():
    """The family exists only if it is harder than random_irrelevant: same claim, more shared words."""
    better = same = 0
    for cid, d in MUT.items():
        h, f = d.get("H_high_overlap"), d.get("F_unrelated")
        if not h or not f:
            continue
        if h["overlap"] > overlap(f["claim"], ev(f)):
            better += 1
        else:
            same += 1
    assert better >= 20, (better, same)


def test_M_diluted_keeps_the_support_and_asks_the_same_label_as_A():
    n = 0
    for cid, d in MUT.items():
        m = d.get("M_diluted")
        if not m:
            continue
        assert len(m["evidence"]) == 2 and m["evidence"][0]["text"] == ev(d["A_genuine"]), cid
        # the corpus is ONE article, so both items carry the same source string: what is diluted here is
        # the evidence set, not the provenance. Provenance contrast is the job of R_pair.
        assert m["evidence"][1]["text"] != m["evidence"][0]["text"], cid
        assert m["expected"] == d["A_genuine"]["expected"] and m["acceptable"] == [m["expected"]], cid
        assert m["negative"] is False, "dilution is a positive control, not a negative arm"
        n += 1
    assert n == 49, n   # v2: 48


def test_R_pair_presents_two_opposite_sources_and_demands_a_refusal():
    n = 0
    for cid, d in BY.items():
        r = d.get("R_pair")
        if not r:
            continue
        assert len(r["evidence"]) == 2 and r["evidence"][0]["text"] != r["evidence"][1]["text"], cid
        assert r["evidence"][0]["source"] != r["evidence"][1]["source"], cid
        assert r["expected"] == labels.REFUSAL and r["acceptable"] == [labels.REFUSAL], cid
        assert r.get("constructed_pair") and "constructed" in r["evidence"][1]["source"], cid
        n += 1
    assert n == 42, n   # v2: 40


def test_necessity_reads_every_evidence_item_not_only_the_first():
    """Regression: reading only evidence[0] made diluted and conflicting arms look identical to A, which
    would have reported 100 % of them as 'the oracle cannot tell'."""
    nec = necessity({"arms": ARMS})
    conf = nec["by_family"]["conflicting_sources"]
    dil = nec["by_family"]["diluted_support"]
    assert conf["share_oracle_cannot_tell"] < 0.1, conf
    assert dil["oracle_can_tell"] > 0, dil


def test_family_table_is_printed_next_to_the_gate_not_instead_of_it():
    s = score(MAN, perfect_judge(MAN))
    assert s["J_gate"] == 1.0 and s["per_family"], s["J_gate"]
    assert sum(v["n"] for v in s["per_family"].values()) == len([a for a in MAN["arms"] if not a["anchor"]])


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            try:
                fn(); print("  OK   ", name)
            except Exception as e:  # noqa: BLE001
                fails += 1; print("  FAIL ", name, repr(e)[:200])
    print(f"\n  {'all passed' if not fails else str(fails) + ' failed'}")
    sys.exit(1 if fails else 0)
