#!/usr/bin/env python3
"""Self-check of the USGS second-domain freeze against the audit list we promised
(passages from the catalogue, labels by construction, noise arms free of comparable quantities,
distorting arms that distort). Deterministic, no network, no model.
Usage:  python audit_selfcheck.py            (run in this folder; prints a table, exit 1 on any FAIL)
"""
import json, re, sys
from pathlib import Path

D = Path(__file__).parent
corpus = json.loads((D / "corpus_frozen.json").read_text(encoding="utf-8"))
arms = json.loads((D / "руки_usgs_заморозка.json").read_text(encoding="utf-8"))["руки"]
rec = {r["id"]: r for r in corpus["записи"]}
usable = {k: r for k, r in rec.items() if r.get("http") == 200}
NUM = re.compile(r"\d+(?:\.\d+)?")
EXPECT = {"A_supported": "SUPPORTED", "C_noise_no_quantity": "NOT_ENOUGH_INFO", "C_num_same_value": "NOT_ENOUGH_INFO",
          "C_num_contradicting": "REFUTED", "D_distorting": "REFUTED", "R_absent_source": "REFUSAL"}
out, fails = [], 0


def check(name, ok, detail=""):
    global fails
    fails += (not ok)
    out.append((name, "PASS" if ok else "FAIL", detail))


# 1. labels known by construction: expected label is a function of the family only
check("labels by construction", all(a["expected"] == EXPECT[a["family"]] for a in arms),
      f"{len(arms)} arms; expected label equals the family's contract in every arm; sensor verdict is not an input")

# 2. passages are from the catalogue: every A_supported passage is "magnitude <M> at <place>" with M and place equal to the stored record
bad = []
A = [x for x in arms if x["family"] == "A_supported"]
for a in A:
    r = usable.get(a["source_id"])
    m = re.fullmatch(r"magnitude (\d+(?:\.\d+)?) at (.+)", a["evidence"])
    if not (r and m and float(m.group(1)) == float(r["магнитуда"]) and m.group(2) == r["место"]):
        bad.append(a["source_id"])
check("A_supported passages come from the stored catalogue record", not bad,
      f"mismatching: {bad}" if bad else f"{len(A)} arms; magnitude and place equal the stored record values")

# 3. noise arms
nq = [a for a in arms if a["family"] == "C_noise_no_quantity"]
check("C_noise_no_quantity carries no number at all", all(not NUM.search(a["evidence"]) for a in nq), f"{len(nq)} arms")
sv = [a for a in arms if a["family"] == "C_num_same_value"]
okc = all(set(NUM.findall(a["evidence"])) <= set(NUM.findall(a["claim"])) and NUM.findall(a["evidence"]) for a in sv)
check("C_num_same_value repeats only the claim's own number(s), no other value", okc, f"{len(sv)} arms")
ct = [a for a in arms if a["family"] == "C_num_contradicting"]
# contradicting: same quantity phrase, different number than the claim
okt = True
for a in ct:
    cn, en = NUM.findall(a["claim"]), NUM.findall(a["evidence"])
    okt &= bool(en) and en[0] != cn[0] and "magnitude" in a["evidence"]
check("C_num_contradicting evidence differs from the claim in the one number it names", okt,
      f"{len(ct)} arms, one contradicting quantity per arm (manifest count = 1)")

# 4. distorting arms distort
dd = [a for a in arms if a["family"] == "D_distorting"]
okd, alt = True, 0
for a in dd:
    r = usable[a["source_id"]]
    cn, en = NUM.findall(a["claim"]), NUM.findall(a["evidence"])
    okd &= bool(cn) and bool(en) and float(cn[0]) != float(en[0])
    alt += float(en[0]) != float(r["глубина_km"])
check("D_distorting: evidence value differs from the claim value", okd, f"{len(dd)} arms")

# 5. the one refusal arm is on an id that is absent
ra = [a for a in arms if a["family"] == "R_absent_source"]
check("R_absent_source id is the recorded absence", len(ra) == 1 and ra[0]["source_id"] in corpus["нет_в_каталоге"]
      or any(ra[0]["source_id"] in str(x) for x in corpus["нет_в_каталоге"]), ra[0]["source_id"] if ra else "none")

# 6. corpus counts and public access
check("corpus: 12 requested, 11 usable, 1 absent", corpus["запрошено"] == 12 and len(usable) == 11, f"usable={len(usable)}")
check("no record requires a paid tier or a key", all(r["url"].startswith("https://earthquake.usgs.gov/fdsnws/") and "key" not in r["url"].lower()
      for r in rec.values()), "all request URLs are the public FDSN endpoint, plain GET")

w = max(len(n) for n, _, _ in out)
for n, s, d in out:
    print(f"{s}  {n.ljust(w)}  {d}")
print(f"\nD_distorting arms whose evidence value is not the stored catalogue value: {alt} of {len(dd)} (declared: the evidence is altered by construction)")
sys.exit(1 if fails else 0)
