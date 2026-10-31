#!/usr/bin/env python3
"""helix_judge_probe.py — the null-arm probe run against the LIVE HELIX judge.

First real data run. Everything before this was synthetic fixtures; here the judge is helixcom.org/api/check,
which reconciles numbers and dates deterministically with no model call, and returns a structured verdict.

WHAT IT DOES. Pulls numeric claims from our own article, builds the arms mechanically, calls the judge once per
arm, writes v1.5-format receipts, and emits a results file the grader can read. Nothing is hand-labelled: the arm
construction is fixed and the labels come from the judge's own response.

LABEL MAPPING, taken from the judge's documented vocabulary:
    verdict OK / status BOUND            -> SUPPORTED
    verdict CONTRADICTED                 -> REFUTED
    anything else, or no number bound    -> NEI
    HTTP failure / empty response        -> NO_RESPONSE (the grader records it as UNTESTED, not a refusal)

ARMS, per the v1.5 plan:
    A_genuine      claim + the sentence it came from            expect SUPPORTED
    E2_distorted   claim with ONE figure altered + same source  expect REFUTED  (the accurate source, distorted claim)
    C_noise_length claim + random prose, similar length         expect no verdict
    B_empty        claim + empty source                         expect refusal
    F_unrelated    claim + a different claim's source           expect no verdict
    G_permuted     same as F but scored against the donor        expect not the donor's verdict

Usage:  python3 helix_judge_probe.py [--claims N] [--out results.json]
"""
import argparse, hashlib, json, random, re, sys, time, urllib.error, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAIMS = HERE / "claims.json"          # bundled, so the run reproduces anywhere
ARTICLE = None                          # optional: --article to re-extract from source text
API = "https://helixcom.org/api/check"
OUT = HERE / "results" / "live_run.json"
TIMEOUT = 45


def canonical(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def load_claims(n, article=None):
    """Bundled claims first, so the run is reproducible without the source article."""
    if article is None:
        d = json.loads(CLAIMS.read_text())
        return [{"source": c["text"], "figure": c["figure"]} for c in d["claims"]][:n]
    return extract_claims(n, article)


def extract_claims(n, article=None):
    """Numeric sentences from the article, sentence-level, with one usable figure each."""
    text = Path(article).read_text() if article else Path(ARTICLE).read_text()
    body = re.sub(r"^#.*$", "", text, flags=re.M)
    sents = re.split(r"(?<=[.;])\s+", body.strip())
    out, seen = [], set()
    for s in sents:
        s = " ".join(s.split())
        if len(s) < 60 or len(s) > 400:
            continue
        nums = re.findall(r"\b\d[\d,]*(?:\.\d+)?\s*(?:million|billion|per cent|%)?", s)
        nums = [x for x in nums if re.search(r"\d{3,}|\d+\.\d+|million|billion", x)]
        if not nums:
            continue
        key = nums[0]
        if key in seen:
            continue
        seen.add(key)
        out.append({"source": s, "figure": nums[0].strip()})
        if len(out) >= n:
            break
    return out


def _numeric(figure):
    """The numeric value of a figure string, so a distortion can be PROVEN to differ numerically."""
    f = figure.lower().replace(",", "").strip()
    mult = 1.0
    for word, m in (("billion", 1e9), ("million", 1e6), ("thousand", 1e3)):
        if word in f:
            mult = m
            f = f.split(word)[0]
            break
    m = re.search(r"\d+(?:\.\d+)?", f)
    return (float(m.group()) * mult) if m else None


def is_year(figure):
    """A four-digit year, as opposed to a quantity. The two behave differently in reconciliation."""
    f = (figure or "").replace(",", "").strip()
    return f.isdigit() and len(f) == 4 and 1900 <= int(f) <= 2100


INEQUALITY_WORDS = ("below", "under", "less than", "fewer than", "above", "over", "more than",
                    "exceeds", "exceeding", "at least", "at most", "up to", "no more than")


def is_inequality(sentence):
    """A bound claim is TRUE or FALSE against a source, not equal or unequal. Testing it as an equality
    ('below 200 million' vs source 'below 100 million') returns a correct COMPARISON_MATCH that looks like a
    miss. Three of my own arms got this wrong before the live run exposed it."""
    low = (sentence or "").lower()
    return any(w in low for w in INEQUALITY_WORDS)


def _with_unit(figure, factor):
    """Scale a figure and re-attach its unit WITHOUT double-counting it.

    _numeric() already multiplies by 1e3/1e6/1e9, so the scaled value must be divided back by the same multiplier
    before the unit word is appended. Getting this wrong produced '2e+08 million' — a value a million times too
    large — which then scored as a correct REFUTED for entirely the wrong reason.
    """
    f = figure.strip().lower()
    for word, mult in (("billion", 1e9), ("million", 1e6), ("thousand", 1e3)):
        if word in f:
            lead = _numeric(f)
            if lead is None:
                return figure
            scaled = (lead * factor) / mult
            return f"{scaled:g} {word}"
    base = _numeric(f)
    if base is None:
        return figure
    return f"{base * factor:g}"


def false_bound(figure, factor=0.5):
    """E2 for an inequality: tighten the bound past the source so the claim becomes FALSE."""
    return _with_unit(figure, factor)


def loosen_bound(figure, factor=2.0):
    """E1 for an inequality: the source must FAIL to establish the claim. Tightening the source ENTIALS the claim
    (the judge correctly answered OK when I did that), so E1 must loosen it."""
    return _with_unit(figure, factor)


def shift_year(figure, delta=1):
    """HELIX's own c04 case: the date wrong by one year. Realistic, and the one that occurs in real copy."""
    return str(int((figure or "0").replace(",", "").strip()) + delta)


def distort(figure):
    """Alter a figure so the result is PROVABLY a different number. Validated by the caller."""
    f = figure.strip()
    base = _numeric(f)
    unit = ""
    for word in ("billion", "million", "thousand"):
        if word in f.lower():
            unit = f" {word}"
            break
    if base is None:
        return f
    # a doubled value is unambiguously different and stays in the same magnitude class
    new = base * 2
    if unit:
        lead = new / {" billion": 1e9, " million": 1e6, " thousand": 1e3}[unit]
        txt = f"{lead:g}{unit}"
    else:
        txt = f"{new:g}" if new < 1e6 else f"{new:,.0f}"
    return txt


def noise_like(s, seed):
    """Random words, length-matched to within a few characters — the C arm."""
    rng = random.Random(seed)
    vocab = ("the of and to in that for on with as by at from is was were has have been which its their "
             "would could should may might reported earlier this week according figures market supply demand "
             "quarter annual period region facility output capacity").split()
    target, words = len(s), []
    while sum(len(w) + 1 for w in words) < target:
        words.append(rng.choice(vocab))
    return " ".join(words)[:target]


def call(claim, source):
    """One judge call. Returns (state, label, raw) where state is OK or NO_RESPONSE."""
    body = json.dumps({"claim": claim, "source": source}).encode()
    req = urllib.request.Request(API, data=body, headers={"Content-Type": "application/json",
                                                          "User-Agent": "helix-null-arm-probe/1.5"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            raw = r.read().decode("utf-8", "replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        return "NO_RESPONSE", None, {"error": f"{type(e).__name__}: {str(e)[:120]}"}
    if not raw.strip():
        return "NO_RESPONSE", None, {"error": "empty body"}
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return "NO_RESPONSE", None, {"error": "non-JSON", "body": raw[:200]}
    v = str(d.get("verdict", "")).upper()
    st = str(d.get("status", "")).upper()
    if v == "OK" or st == "BOUND":
        return "OK", "SUPPORTED", d
    if v == "CONTRADICTED" or st == "CONTRADICTED":
        return "OK", "REFUTED", d
    return "OK", "NEI", d


def receipt(claim, source, arm, label, raw):
    payload = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "party": "helix-ai-innovations",
        "instrument": "null-arm-probe-v1.5 / helix judge /check",
        "claim_id": arm["claim_id"], "arm": arm["arm"],
        "input": {"claim": claim, "evidence": [{"text": source}],
                  "prompt_template": "helixcom.org/api/check (deterministic, no model)", "search_enabled": False},
        "model": {"name": "helix-check", "version_or_hash": None, "temperature": 0.0,
                  "other_params": {"api": API}},
        "output": {"raw": raw, "label": label, "per_evidence": raw.get("bindings") if isinstance(raw, dict) else []},
        "notes": "model hash unavailable: endpoint version not published",
    }
    # v1.6 contract: the full digest covers the object with the ENTIRE `hashes` block removed. The earlier
    # version included the component digests in the hashed body, which is defect F4 and made every receipt fail
    # its own verifier -- caught by the positive control below, not by reading.
    h = {"input_sha256": hashlib.sha256(canonical(payload["input"]).encode()).hexdigest(),
         "output_sha256": hashlib.sha256(canonical(payload["output"]).encode()).hexdigest()}
    body = {k: v for k, v in payload.items() if k != "hashes"}
    h["full_receipt_sha256"] = hashlib.sha256(canonical(body).encode()).hexdigest()
    payload["hashes"] = h
    return payload


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claims", type=int, default=10)
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--article", default=None, help="re-extract claims from a source file instead of claims.json")
    args = ap.parse_args()

    claims = load_claims(args.claims, args.article)
    src = args.article or CLAIMS.name
    print(f"  {len(claims)} claims from {Path(src).name}", flush=True)
    for c in claims:
        print(f"    figure {c['figure']:>12s}  {c['source'][:80]}...", flush=True)

    results, receipts, status = {}, [], {}
    t0 = time.time()
    for i, c in enumerate(claims):
        cid = f"c{i+1:02d}"
        genuine_src = c["source"]
        # a claim stated affirmatively; the source is the sentence it came from
        claim_ok = genuinify(c)
        dg = distort(c["figure"])
        claim_bad = claim_ok.replace(c["figure"], dg)
        # POSITIVE CONTROL: if the figure was not replaced, or the new value equals the old one, the E2 arm
        # has no distortion to detect and must not be scored. This is what the first run got wrong.
        if claim_bad == claim_ok or _numeric(dg) == _numeric(c["figure"]):
            print(f"    {cid} E2 SKIPPED: distortion {c['figure']!r} -> {dg!r} unchanged or numerically equal",
                  flush=True)
            e2_ok = False
        else:
            e2_ok = True
        donor = claims[(i + 1) % len(claims)]
        # the realistic distortion: a one-year shift for years, a doubled quantity otherwise
        fig = c["figure"]
        ineq = is_inequality(claim_ok)
        if ineq:
            dg_realistic = false_bound(fig)          # tighten the bound so the claim becomes false
        elif is_year(fig):
            dg_realistic = shift_year(fig)           # the c04 case: one year out
        else:
            dg_realistic = distort(fig)              # equality: change the value
        claim_realistic = claim_ok.replace(fig, dg_realistic)
        realistic_ok = (claim_realistic != claim_ok and _numeric(dg_realistic) != _numeric(fig))

        # E1: keep the CLAIM accurate and corrupt the SOURCE. For a comparator this should also contradict,
        # which is the point — it tests sensitivity rather than distortion detection.
        # E1 needs the source to NO LONGER SUPPORT the claim. For an inequality that means loosening the bound;
        # tightening it makes the source entail the claim and a correct judge answers OK — which is not a failure.
        dg_source = loosen_bound(fig) if ineq else dg_realistic
        source_altered = genuine_src.replace(fig, dg_source) if realistic_ok else genuine_src

        arms = {
            "A_genuine": (claim_ok, genuine_src),
            "E1_contrary": (claim_ok, source_altered),
            "C_noise_length": (claim_ok, noise_like(genuine_src, i)),
            "B_empty": (claim_ok, ""),
            "F_unrelated": (claim_ok, donor["source"]),
        }
        if realistic_ok:
            arms["E2_distorted_source"] = (claim_realistic, genuine_src)
        else:
            print(f"    {cid} E2 SKIPPED: {fig!r} -> {dg_realistic!r} unchanged", flush=True)
        cell, st_cell = {}, {}
        for arm, (cl, sr) in arms.items():
            st, label, raw = call(cl, sr)
            cell[arm] = label
            if st == "NO_RESPONSE":
                st_cell[arm] = {"status": "error"}
            receipts.append(receipt(cl, sr, {"claim_id": cid, "arm": arm}, label, raw))
            print(f"    {cid} {arm:20s} -> {label}", flush=True)
        results[cid] = cell
        if st_cell:
            status[cid] = st_cell

    kinds = {f"c{i+1:02d}": ("inequality" if is_inequality(genuinify(c))
                              else "year" if is_year(c["figure"]) else "equality") for i, c in enumerate(claims)}
    # the receipts ARE the collaboration artefact -- storing only a count while claiming "with receipts"
    # would be the exact overclaim this whole exercise exists to catch
    out = {"results": results, "status": status, "receipts": receipts, "receipt_count": len(receipts), "kinds": kinds,
           "elapsed_s": round(time.time() - t0, 1), "claims": len(claims)}
    Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    from importlib import import_module
    _g = import_module("grade_judge_probe_v1p6") if (Path(__file__).parent / "grade_judge_probe_v1p6.py").exists() else None
    if _g:
        valid = sum(1 for r in receipts if _g.verify_receipt(r))
        print(f"  receipts verifying: {valid}/{len(receipts)}", flush=True)
    print(f"\n  {len(receipts)} judge calls in {time.time()-t0:.0f}s -> {args.out}")
    print("DONE")


def genuinify(c):
    """Turn the source sentence into a declarative claim about its figure."""
    s = c["source"].rstrip(".")
    return s


if __name__ == "__main__":
    main()
