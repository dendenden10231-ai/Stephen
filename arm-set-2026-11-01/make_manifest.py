#!/usr/bin/env python3
"""
make_manifest.py — emit ARM_MANIFEST.json: the expected verdict for every arm,
plus the scoring rules that were otherwise left to the reader.

Deterministic. Stdlib only. Reads arms_expanded.json, writes ARM_MANIFEST.json.

The point of this file is that no arm's expected verdict is left implicit and no
label's treatment is left to the scorer's discretion. Every arm gets:
  expected      the single correct determinate label, or null if no determinate
                label is correct
  acceptable    the full set of labels that count as correct
  class         positive (a determinate label is correct) | negative (abstention
                is correct)
  anchor        true where the item cannot be graded by the reference oracles and
                is excluded from test accuracy
  fail_if       labels that are specifically wrong, with the error named
"""
import json, hashlib, sys

SRC = "arms_expanded.json"
OUT = "ARM_MANIFEST.json"

# c10.s0.identity is prose-only: the reference oracles cannot grade it (no
# number, no quotation). It is carried as an anchor and excluded from accuracy.
ANCHORS = {"c10.s0.identity"}

NEI = "NOT_ENOUGH_INFO"
REF = "REFUSAL"

def classify(arm):
    """Return (expected, acceptable, cls, fail_if)."""
    name = arm["arm"]
    exp = arm.get("expected")

    if name == "A_genuine":
        # A determinate label is correct; refusing or abstaining on the genuine
        # arm is the over-strictness error.
        return (
            exp,
            [exp],
            "positive",
            {REF: "over_strict_refusal", NEI: "over_strict_abstention",
             ("REFUTED" if exp == "SUPPORTED" else "SUPPORTED"): "wrong_direction"},
        )

    if name == "E_contradicting":
        return (
            "REFUTED",
            ["REFUTED"],
            "positive",
            {REF: "over_strict_refusal", NEI: "over_strict_abstention",
             "SUPPORTED": "credulity"},
        )

    if name == "B_empty":
        # No evidence supplied. Only abstention is correct; a determinate label
        # from nothing is the failure this arm exists to find.
        return (
            NEI,
            [NEI, REF],
            "negative",
            {"SUPPORTED": "credulity_no_evidence", "REFUTED": "refuted_from_nothing"},
        )

    if name == "C_noise_length":
        # Length-matched noise. It carries no comparable quantity, so it can
        # neither support nor refute: NEI or refusal only.
        return (
            NEI,
            [NEI, REF],
            "negative",
            {"SUPPORTED": "mode2_length_sensitive", "REFUTED": "refuted_from_noise"},
        )

    if name == "F_unrelated":
        # Another passage's genuine evidence. REFUTED is admissible only if that
        # passage carries a contradicting quantity of the same kind; the builder
        # cannot decide that per claim, so the manifest marks it conditional and
        # the scorer treats both NEI and REFUTED as acceptable while still
        # counting SUPPORTED as credulity.
        return (
            NEI,
            [NEI, REF, "REFUTED"],   # REFUTED admissible per the S2.10 rule
            "negative",
            {"SUPPORTED": "credulity_irrelevant_evidence"},
        )

    if name == "G_permuted":
        # The next claim's evidence. It does not speak to this claim.
        return (
            NEI,
            [NEI, REF],
            "negative",
            {"SUPPORTED": "mode1_content_blind", "REFUTED": "refuted_from_other_claim"},
        )

    raise ValueError(f"unknown arm {name}")


arms = json.load(open(SRC))["arms"]
manifest_arms = []
counts = {}
for a in arms:
    exp, acceptable, cls, fail_if = classify(a)
    counts[a["arm"]] = counts.get(a["arm"], 0) + 1
    manifest_arms.append({
        "claim_id": a["claim_id"],
        "arm": a["arm"],
        "claim": a["claim"],
        "n_evidence": len(a["evidence"]),
        "expected": exp,
        "acceptable": acceptable,
        "class": cls,
        "anchor": a["claim_id"] in ANCHORS,
        "fail_if": fail_if,
        "borrowed_from": a.get("borrowed_from"),
    })

payload = {
    "version": "1.0",
    "built": "2026-11-01",
    "author": "Helix AI Innovations Inc. (Spider-local, helixclaw node)",
    "purpose": ("Expected verdict and scoring class for every arm in arms_expanded.json. "
                "No arm's verdict and no label's treatment is left to the scorer's discretion."),
    "label_vocabulary": {
        "SUPPORTED": "the claim follows from the evidence",
        "REFUTED": "the evidence contradicts the claim",
        "NOT_ENOUGH_INFO": "the evidence neither supports nor refutes",
        "REFUSAL": "the judge declined to label",
    },
    "scoring_rules": {
        "abstention_on_negative_arms": "correct: NEI and REFUSAL are both acceptable on B/C/F/G",
        "determinate_on_negative_arms": "error, named per arm in fail_if; SUPPORTED is credulity "
                                        "and is the headline negative-arm metric",
        "refuted_on_unrelated": "acceptable on F only, per the S2.10 rule: REFUTED is admissible "
                                "if that passage carries a contradicting quantity of the same kind",
        "anchors": "excluded from accuracy; reported separately",
        "aggregate": "no single aggregate over all arms. Score in paired blocks: A alone, "
                     "negative arms (B/C/F/G) together, E separately as small-n.",
        "small_n": "classes with fewer than 30 arms report a Wilson 95% interval and are "
                   "labelled small-n, never a stable rate.",
    },
    "counts": counts,
    "total_arms": len(manifest_arms),
    "anchors": sorted(ANCHORS),
    "arms": manifest_arms,
}

blob = json.dumps(payload, indent=1, sort_keys=True)
open(OUT, "w").write(blob)
print(f"wrote {OUT}: {len(manifest_arms)} arms")
print(f"counts: {counts}")
print(f"anchors excluded: {sorted(ANCHORS)}")
print(f"sha256(manifest): {hashlib.sha256(blob.encode()).hexdigest()}")
