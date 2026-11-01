# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""Tests for arm set v2: every invariant from the review, checked on the shipped arms_v2.json. Run: python3 test_v2.py"""
import json
import sys

import labels
import stability
from arm_check import check_distorted, expected_on_unrelated
from number_check import distortion, reconcile
from scoring_v2 import constant_judge, perfect_judge, score, baselines

ARMS = json.load(open("arms_v2.json", encoding="utf-8"))["arms"]
MAN = json.load(open("ARM_MANIFEST_v2.json", encoding="utf-8"))
ITEMS = {x["id"]: x for x in json.load(open("mutation_items_v2.json", encoding="utf-8"))}
OLD = {x["id"]: x for x in json.load(open("../null-arm-checks/mutation_items_no_second_refinery.json", encoding="utf-8"))}
BY = {}
for a in ARMS:
    BY.setdefault(a["claim_id"], {})[a["arm"]] = a
ev = lambda a: a["evidence"][0]["text"] if a["evidence"] else ""


def test_G_never_gets_its_own_evidence_or_its_own_passage():
    n = 0
    for cid, d in BY.items():
        g = d["G_deranged"]
        assert ev(g) != ev(d["A_genuine"]), cid
        assert ITEMS[g["borrowed_from"]]["passage_id"] != ITEMS[cid]["passage_id"], cid
        n += 1
    assert n == 48


def test_F_passage_always_differs():
    assert all(ITEMS[d["F_unrelated"]["borrowed_from"]]["passage_id"] != ITEMS[c]["passage_id"] for c, d in BY.items())


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
    for cid, d in BY.items():
        a = d["A_genuine"]
        for arm in ("C_noise_length", "C_num_noise"):
            c = d[arm]
            assert c["evidence"][0]["source"] == a["evidence"][0]["source"] != "", (cid, arm)
            assert 0.95 * len(ev(a)) <= len(ev(c)) <= 1.05 * len(ev(a)), (cid, arm)
        from build_arms_v2 import claim_tokens
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
