#!/usr/bin/env python3
"""
Build the expanded arm set (A/B/C/F/G + E where constructible) from Denis's
45-kept mutation claims, per the v1.6 arm rules.

Deterministic. Stdlib only. No model called. Fixed seeds so both sides
construct byte-identical arms and nobody's discretion is in the loop.

Reads: mutation_items_no_second_refinery.json (Denis, Apache-2.0)
Writes: arms_expanded.json  + a build report on stdout
"""
import json, random, re, hashlib, sys

sys.path.insert(0, "../null-arm-checks")
from number_check import distortion

SRC = "../null-arm-checks/mutation_items_no_second_refinery.json"
OUT = "arms_expanded.json"

raw = json.load(open(SRC))
items = [x for x in raw if "dropped_reason" not in x]
assert len(items) == 45, f"expected 45 kept, got {len(items)}"

# ---- deterministic length-matched noise (arm C) -------------------------
# Random prose from a fixed word list, seeded per claim id, tuned to within
# +/-5% of the genuine evidence character count.
WORDS = (
    "the of and to in for on with as by from that this which at be been were "
    "was is are has have had it its not but or if then than so such may might "
    "could would should can will over under between across "
    "report record volume measure sample period total change noted stated "
    "observed figure value table entry column row document archive register "
    "ledger account filing notice summary detail item list sheet page file "
    "morning evening season annual weekly daily monthly standard "
    "ordinary plain general common regular simple basic formal neutral"
).split()

def noise_for(text, claim_id, tolerance=0.05):
    """Random prose with char length within +/-5% of `text`."""
    target = len(text)
    seed = int(hashlib.sha256(claim_id.encode()).hexdigest()[:12], 16)
    rng = random.Random(seed)
    # build up until within tolerance of target
    for _ in range(200):
        out = []
        n = 0
        while n < target * (1 - tolerance):
            w = rng.choice(WORDS)
            out.append(w)
            n += len(w) + 1
        cand = " ".join(out).rstrip(".,;") + "."
        if abs(len(cand) - target) <= max(2, int(target * tolerance)):
            return cand
    # fallback: trim/extend to nearest
    return cand

# ---- contradicting evidence for SUPPORTED claims (arm E) ----------------
def contradict_passage(passage):
    """Take a passage and shift its first number/year by a factor that the
    oracles will register as a real distortion, so the passage now REFUTES a
    claim that matched the original."""
    # year first
    m = re.search(r"\b(19|20)\d{2}\b", passage)
    if m:
        return passage[:m.start()] + str(int(m.group(0)) - 1) + passage[m.end():]
    # then a scale suffix
    m = re.search(r"(\d[\d,.]*)\s*(M|B|K)\b", passage)
    if m:
        rep = {"M": "B", "B": "K", "K": "M"}[m.group(2)]
        return passage[:m.start(2)] + rep + passage[m.end(2):]
    # then a percentage-free value shift
    m = re.search(r"\b(\d[\d,]{1,})\b", passage)
    if m:
        old = m.group(1).replace(",", "")
        try:
            new = str(int(int(old) * 1.25))
        except ValueError:
            return None
        return passage[:m.start()] + new + passage[m.end():]
    return None

def evidence_item(entry, tag):
    """One evidence entry, copying shape from the source set."""
    return {"text": entry["text"], "source": entry.get("source", ""), "arm_tag": tag}

arms = []
report = {"claims": 0, "arms": 0, "e_built": 0, "e_absent": 0, "e_skipped": [],
          "c_char_deltas": [], "label_conflicts": []}

for i, it in enumerate(items):
    cid = it["id"]
    genuine = it["evidence"][0]
    gtext = genuine.get("text", "")
    expected_a = it["expected"]

    # ---- A genuine ----
    arms.append({
        "claim_id": cid, "arm": "A_genuine",
        "claim": it["claim"],
        "evidence": [evidence_item(genuine, "A")],
        "requirement": "determinate label equal to expected",
        "expected": expected_a,
    })

    # ---- B empty ----
    arms.append({
        "claim_id": cid, "arm": "B_empty",
        "claim": it["claim"], "evidence": [],
        "requirement": "NOT_ENOUGH_INFO or REFUSAL; never a determinate label",
        "expected": "NOT_ENOUGH_INFO",
    })

    # ---- C noise, length-matched ----
    ctext = noise_for(gtext, cid)
    report["c_char_deltas"].append(abs(len(ctext) - len(gtext)) / max(1, len(gtext)))
    arms.append({
        "claim_id": cid, "arm": "C_noise_length",
        "claim": it["claim"],
        "evidence": [{"text": ctext, "source": "", "arm_tag": "C"}],
        "requirement": "label must DIFFER from this claim's A label; equality = mode 2 (length-sensitive)",
        "expected": "!= label(A)",
    })

    # ---- F unrelated (another passage's genuine evidence) ----
    j = (i + 7) % len(items)
    if j == i:
        j = (i + 1) % len(items)
    arms.append({
        "claim_id": cid, "arm": "F_unrelated",
        "claim": it["claim"],
        "evidence": [evidence_item(items[j]["evidence"][0], "F")],
        "requirement": ("REFUTED admissible only if that passage carries a quantity/date of the "
                        "same kind that contradicts the claim; otherwise NOT_ENOUGH_INFO"),
        "expected": "SEE_RULE",
        "borrowed_from": items[j]["id"],
    })

    # ---- G permuted (cyclic: claim i gets claim i+1's genuine evidence) ----
    k = (i + 1) % len(items)
    arms.append({
        "claim_id": cid, "arm": "G_permuted",
        "claim": it["claim"],
        "evidence": [evidence_item(items[k]["evidence"][0], "G")],
        "requirement": "must not reproduce this claim's A label; equality proves mode 1 (content-blind)",
        "expected": "!= label(A)",
        "borrowed_from": items[k]["id"],
    })

    # ---- E contradicting (only where constructible AND oracle-valid) ----
    if expected_a == "SUPPORTED":
        cpass = contradict_passage(gtext)
        e_ok = False
        if cpass:
            d = distortion(it["claim"], cpass)
            ds = d.get("status") if isinstance(d, dict) else d
            e_ok = ds in ("SCALE_MISMATCH", "UNIT_MISMATCH", "VALUE_MISMATCH", "DATE_SHIFT")
        if e_ok:
            arms.append({
                "claim_id": cid, "arm": "E_contradicting",
                "claim": it["claim"],
                "evidence": [{"text": cpass, "source": genuine.get("source", ""), "arm_tag": "E"}],
                "requirement": "must DIFFER from A, in the opposite direction (REFUTED)",
                "expected": "REFUTED",
            })
            report["e_built"] += 1
        else:
            report["e_absent"] += 1
            report["e_skipped"].append(cid)
    else:
        report["e_absent"] += 1

    report["claims"] += 1

report["arms"] = len(arms)

payload = {
    "version": "1.0",
    "built": "2026-11-01",
    "built_by": "Stephen Hope / Helix AI Innovations (arms only; claims by Denis Vashkevich)",
    "source_set": "mutation_items_no_second_refinery.json — 45 kept of 49, Apache-2.0",
    "note": ("Arms A-F-G-B-C constructed mechanically per null-arm probe v1.6 rules. "
             "C is seeded per claim id (sha256 prefix) so both sides build byte-identical "
             "noise; nobody's discretion is in the construction. E exists only for claims "
             "whose genuine arm expects SUPPORTED."),
    "noise_seed_rule": "int(sha256(claim_id)[:12], 16) -> random.Random; word list in build script",
    "arms": arms,
}
json.dump(payload, open(OUT, "w"), indent=1)

deltas = report["c_char_deltas"]
print(f"claims: {report['claims']}   arms: {report['arms']}")
print(f"E built: {report['e_built']}   E absent: {report['e_absent']}")
print(f"C length match: mean |Δ| {sum(deltas)/len(deltas)*100:.2f}%  max {max(deltas)*100:.2f}%  "
      f"(all within ±5%: {all(d <= 0.05 for d in deltas)})")
print(f"wrote {OUT}")
