# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""Tests for the four v2.1 fixes (review by S. Hope, 07 Nov 2026) and the frozen-v2 invariants they must not break.
Run: python3 test_v2_1_fixes.py   (or pytest)"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import labels  # noqa: E402
import mutation_set as ms  # noqa: E402
import scoring_v2  # noqa: E402
import stability  # noqa: E402
from number_check import _dates, distortion  # noqa: E402

HERE = Path(__file__).resolve().parent


# 1. currency is part of the unit, also behind a measure suffix --------------------------------------------------
def test_currency_behind_a_measure_suffix_is_not_dropped():
    assert distortion("Prices rose to $5.85/gal.", "Prices rose to €5.85/gal.") == "UNIT_MISMATCH"
    assert distortion("Prices rose to $5.85/gal.", "Prices rose to £5.85/gal.") == "UNIT_MISMATCH"
    assert distortion("Costs fell to $5.85.", "Costs fell to €5.85.") == "UNIT_MISMATCH"


def test_same_currency_and_price_with_or_without_denominator_still_agree():
    assert distortion("Prices rose to $5.85/gal.", "Prices rose to $5.85/gal.") == "MATCH"
    assert distortion("Costs fell to $5.85.", "Costs fell to $5.85 per gallon.") == "MATCH"
    assert distortion("Costs fell to $5.85 per gallon.", "Costs fell to $5.85.") == "MATCH"


def test_gallon_against_barrel_is_still_a_unit_mismatch():
    assert distortion("Costs $5.85/gal.", "Costs $5.85/bbl.") == "UNIT_MISMATCH"


# 2. a day range with a month and no year is a date --------------------------------------------------------------
def test_day_range_without_year_is_a_date():
    whens, spans = _dates("10–11 September")
    assert len(whens) == 1 and whens[0].yearless and spans
    assert distortion("10–11 September", "12–13 September") == "DATE_SHIFT"
    assert distortion("September 10–11", "September 12–13") == "DATE_SHIFT"
    assert distortion("10–11 September", "10–11 September") == "MATCH"
    # r2 (Stephen, 08 Nov): a claim without a year is not the same assertion as one dated 2026
    assert distortion("10–11 September", "10–11 September 2026") == "YEAR_UNSTATED"
    assert distortion("10–11 September", "10-11 September 2026") == "YEAR_UNSTATED"
    assert distortion("10–11 September", "2026-09-10") == "YEAR_UNSTATED"
    assert distortion("10–11 September 2026", "10–11 September") == "YEAR_UNSTATED"
    assert distortion("10 September", "10 September 2026") == "YEAR_UNSTATED"
    assert distortion("10–11 September 2026", "10–11 September 2025") == "DATE_SHIFT"


def test_day_range_without_year_is_not_compared_with_a_bare_year():
    # r2: this is what removed two H arms in the first v2.1 draft ("first since 2003")
    assert distortion("10–11 September", "stocks below 100M bbl, first since 2003") == "NOT_IN_PASSAGE"
    assert distortion("10–11 September", "in 2003 the price rose") == "NOT_IN_PASSAGE"
    assert distortion("1 January 2003", "first since 2003") != "DATE_SHIFT"


def test_the_two_h_arms_lost_in_the_first_draft_are_back():
    import json
    arms = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "arms_v2_1.json"), encoding="utf-8"))["arms"]
    have = {(a["claim_id"], a["arm"]) for a in arms}
    assert ("c09.s1.identity", "H_high_overlap") in have and ("c09.s1.value_shift", "H_high_overlap") in have


def test_a_modal_verb_is_not_a_month():
    assert _dates("there are 5 may be more")[0] == []


def test_dated_form_still_works_as_before():
    assert distortion("2026-09-10", "2026-09-12") == "DATE_SHIFT"
    assert distortion("10 September 2026", "10 September 2025") == "DATE_SHIFT"


# 3. stability: a missing answer is not a flip ---------------------------------------------------------------------
def test_missing_answer_is_counted_apart_and_is_not_instability():
    st = stability.cells([{"c1": {"A": "SUP"}}, {"c1": {"A": None}}])
    assert st["unstable"] == 0 and st["missing_answers"] == 1 and st["comparable_cells"] == 0
    st = stability.cells([{"c1": {"A": "SUP"}}, {"c1": {"A": "SUP"}}, {"c1": {"A": None}}])
    assert st["unstable"] == 0 and st["comparable_cells"] == 1 and st["cells_with_missing"] == 1


def test_a_real_flip_among_answers_is_still_instability():
    st = stability.cells([{"c1": {"A": "SUP"}}, {"c1": {"A": "REF"}}, {"c1": {"A": None}}])
    assert st["unstable"] == 1 and st["missing_answers"] == 1


def test_untested_is_no_answer_for_stability_and_its_own_label():
    assert labels.norm("UNTESTED") == labels.UNTESTED != labels.REFUSAL
    st = stability.cells([{"c1": {"G": "UNT"}}, {"c1": {"G": "NEI"}}])
    assert st["unstable"] == 0 and st["missing_answers"] == 1


# 4. vocabulary and an audit trail ------------------------------------------------------------------------------------
def test_widened_measure_vocabulary():
    for s in ("a capacity of 3 tanks", "25 m3 of water", "400 workers were laid off", "12 refineries shut"):
        m = ms._NUMBER.search(s)
        assert ms._is_measure(s, m), s
    m = ms._NUMBER.search("Phillips 66 reported")
    assert not ms._is_measure("Phillips 66 reported", m)


def test_every_candidate_leaves_a_trace():
    passages = json.load(open(HERE / "passages_reconstructed.json", encoding="utf-8"))
    exclusions: list = []
    items = ms.build(passages, exclusions)
    assert items and all(i["status"] in ("kept", "dropped") and "reason" in i for i in items)
    assert exclusions and all({"id", "mutation", "reason"} <= set(e) for e in exclusions)
    assert any(e["reason"].startswith("number_without_recognised_measure") for e in exclusions)


def test_no_frozen_v2_item_is_lost_and_the_new_one_is_named():
    v2 = {x["id"] for x in json.load(open(HERE / "mutation_items_v2.json", encoding="utf-8"))}
    v21 = {x["id"] for x in json.load(open(HERE / "mutation_items_v2_1.json", encoding="utf-8")) if x["status"] == "kept"}
    assert v2 <= v21 and v21 - v2 == {"c06.s0.value_shift"}


# denominators: UNTESTED apart, both denominators reported -----------------------------------------------------------
def test_untested_rows_are_kept_out_of_the_judged_denominators():
    manifest = json.load(open(HERE / "arms_v2_1.json", encoding="utf-8"))
    arms = [a for a in manifest["arms"] if not a["anchor"]]
    got: dict = {}
    for k, a in enumerate(arms):
        lab = "UNTESTED" if k % 10 == 0 else labels.NEI
        if a["negative"] and k % 7 == 0 and lab != "UNTESTED":
            lab = labels.SUP
        got.setdefault(a["claim_id"], {})[a["arm"]] = lab
    r = scoring_v2.score(manifest, got)
    assert r["UNTESTED"]["all"] > 0 and r["UNTESTED"]["negative"] > 0
    j = r["judged_denominators"]
    assert j["negative_judged"] == r["negative_cells"] - r["UNTESTED"]["negative"]
    assert j["FDR_strict_judged"] >= r["FDR_strict"]   # a smaller denominator can only raise the rate


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  OK    {name}")
            except AssertionError as e:
                fails += 1
                print(f"  FAIL  {name}: {e!r}")
    print(f"  {'all passed' if not fails else str(fails) + ' failed'}")
    sys.exit(1 if fails else 0)
