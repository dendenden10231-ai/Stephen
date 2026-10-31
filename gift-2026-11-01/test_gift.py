# Copyright 2026 Denis Vashkevich
# Licensed under the Apache License, Version 2.0 (see LICENSE).
"""Tests. Run with pytest, or without it: python3 test_gift.py"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import arm_check  # noqa: E402
import bearing_consistency  # noqa: E402
import mutation_set  # noqa: E402
import signing  # noqa: E402
import stability  # noqa: E402
from number_check import distortion  # noqa: E402
from quote_check import check as quote_check  # noqa: E402


# ── oracles ──────────────────────────────────────────────────────────────────────────────
def test_number_oracle():
    assert distortion("capacity of 400,000 barrels per week", "Jazan (400k b/d)") == "UNIT_MISMATCH"
    assert distortion("reached $5.85 on 4 September 2025", "$5.85/gal on 4 September 2026") == "DATE_SHIFT"
    assert distortion("400 barrels per day", "400,000 barrels per day") == "SCALE_MISMATCH"
    assert distortion("12 million barrels a day", "11.7 million barrels a day") == "ROUNDED_MATCH"
    assert distortion("costs $40 billion", "costs $45 billion") == "VALUE_MISMATCH"
    assert distortion("Nine refineries", "9 refineries") == "MATCH"
    assert distortion("400k b/d", "400,000 b/d") == "MATCH"        # "b" of b/d is not "billion"


def test_quote_oracle():
    q = quote_check('diesel is "the main reason why bond yields are so high"',
                    'diesel is "one of the reasons why bond yields are so high"')
    assert q[0]["kind"] == "ALTERED"


# ── arm_check: positive controls; two of the four v1.6 instrument defects ────────────────
def test_v16_defect_identical_number_is_rejected():
    r = arm_check.check_distorted("capacity of 11.70 million barrels a day", "capacity of 11.7 million barrels a day")
    assert r["status"] == "INVALID"


def test_v16_defect_doubled_year_is_rejected_and_realistic_shift_accepted():
    assert arm_check.check_distorted("the record set in 4044", "the record set in 2022")["status"] == "INVALID"
    ok = arm_check.check_distorted("the record set in 2021", "the record set in 2022")
    assert ok["status"] == "VALID" and ok["distortion"] == "DATE_SHIFT"


def test_unrelated_arm_expectation():
    assert arm_check.expected_on_unrelated("Diesel reached $5.85 a gallon",
                                           "Gasoline averaged $3.10 a gallon")["expected"] == "REFUTED_ADMISSIBLE"
    assert arm_check.expected_on_unrelated("Diesel reached $5.85 a gallon",
                                           "Nine refineries were damaged")["expected"] == "NEI_EXPECTED"


# ── mutation_set ─────────────────────────────────────────────────────────────────────────
def test_mutations_known_labels():
    items = mutation_set.build([{"id": "p1", "text": "Jazan (400,000 b/d) was damaged on 27 July 2026. "
                                                     "Diesel reached $5.85 a gallon in 2026."}])
    kept = {i["mutation"]: i for i in items if not i.get("dropped_reason")}
    assert kept["identity"]["expected"] == "SUPPORTED"
    assert kept["unit_swap"]["expected"] == "REFUTED" and "barrels per week" in kept["unit_swap"]["claim"]
    assert kept["year_shift"]["expected"] == "REFUTED"
    assert "400k" in kept["paraphrase_number"]["claim"]


def test_names_and_days_are_not_shifted():
    items = mutation_set.build([{"id": "p", "text": "Phillips 66 said PADD 3 stocks fell on 28 August."}])
    assert not [i for i in items if i["mutation"] == "value_shift" and not i.get("dropped_reason")]


def test_mutation_score():
    items = [{"id": "a", "mutation": "unit_swap", "expected": "REFUTED"},
             {"id": "b", "mutation": "unit_swap", "expected": "REFUTED"},
             {"id": "c", "mutation": "paraphrase_number", "expected": "SUPPORTED"}]
    s = mutation_set.score(items, {"a": "CONTRADICTED", "b": "NOT_ENOUGH_INFO", "c": "REFUTED"})
    assert s["unit_swap"]["accuracy"] == "1/2" and s["unit_swap"]["abstained"] == 1
    assert s["_over_strictness"]["false_refutations_on_paraphrase"] == 1


# ── bearing_consistency ──────────────────────────────────────────────────────────────────
def test_bearing_consistency():
    c = bearing_consistency.check
    assert c({"label": "SUPPORTED", "bearings": [{"bearing": "supports"}]})["finding"] == "CONSISTENT"
    assert c({"label": "SUPPORTED", "bearings": [{"bearing": "refutes"}]})["finding"] == "BEARING_CONTRADICTS_LABEL"
    assert c({"label": "REFUTED", "bearings": [{"bearing": "neutral"}]})["finding"] == "LABEL_WITHOUT_BEARING"
    assert c({"label": "SUPPORTED", "bearings": [{"bearing": "+"}, {"bearing": "-"}]})["finding"] == "CONFLICT_NOT_RECORDED"
    assert c({"label": "UNTESTED", "bearings": [{"bearing": "supports"}]})["finding"] == "REFUSAL_WITH_BEARINGS"
    assert c({"label": "SUPPORTED"})["finding"] == "NO_BEARINGS_EXPOSED"


# ── stability ────────────────────────────────────────────────────────────────────────────
def test_stability_and_both_pair_definitions():
    runs = [{"c1": {"A_genuine": "SUP", "G_permuted": "UNT"}, "c2": {"A_genuine": "NEI", "G_permuted": "NEI"}},
            {"c1": {"A_genuine": "SUP", "G_permuted": "NEI"}, "c2": {"A_genuine": "SUP", "G_permuted": "NEI"}}]
    st = stability.cells(runs)
    assert st["unstable"] == 2 and "c2/A_genuine" in st["unstable_cells"]
    p = stability.pairs(runs[0])
    assert (p["content_pairs"], p["content_changed"]) == (1, 0)
    assert (p["determinate_A"], p["determinate_A_changed"]) == (1, 1) and p["credulity"] == []


# ── signing: RFC 8032 test vector 1 ──────────────────────────────────────────────────────
def test_ed25519_rfc8032_vector_1():
    sk = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
    assert signing.public_key(sk).hex() == "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    sig = signing.sign(sk, b"")
    assert sig.hex() == ("e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555"
                         "fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")
    assert signing.verify(signing.public_key(sk), b"", sig)
    assert not signing.verify(signing.public_key(sk), b"tampered", sig)


def test_signature_block_on_a_receipt_digest():
    sk, _ = signing.keypair(bytes(range(32)))
    block = signing.signature_block(sk, "ab" * 32)
    assert signing.check_block(block, "ab" * 32) and not signing.check_block(block, "cd" * 32)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    bad = 0
    for t in tests:
        try:
            t()
            print(f"  OK    {t.__name__}")
        except Exception as e:  # noqa: BLE001
            bad += 1
            print(f"  FAIL  {t.__name__}: {e!r}")
    print(f"\n  {len(tests) - bad}/{len(tests)} passed")
    sys.exit(1 if bad else 0)
