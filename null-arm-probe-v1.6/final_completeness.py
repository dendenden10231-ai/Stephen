#!/usr/bin/env python3
"""final_completeness.py — close the untested list before the package goes out.

Everything still open after the two live runs, except live retrieval (structurally impossible — their search is not
exposed; every arm injects evidence by design).

  1. E3_null_search      claim against an explicit "no source found" result
  2. fabrication         claim citing a source that does not exist
  3. misquotation        claim quoting something the source does not say, with no figures to bind
  4. superseded figure   claim using an old figure against a source carrying the new one
  5. transport error     the harness pointed at a dead endpoint — does the ERROR path fire
  6. concurrency         N parallel calls — rate limiting, partial failure, ordering

Each reports its own expectation. A case whose expectation is not met is a finding, not a failure of the run.
"""
import json, sys, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

API = "https://helixcom.org/api/check"
DEAD = "https://helixcom.org/api/contract-that-does-not-exist"


def call(claim, source, url=API, timeout=45):
    body = json.dumps({"claim": claim, "source": source}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json",
                                                          "User-Agent": "probe/1.6"})
    t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            code = r.status
    except urllib.error.HTTPError as e:
        return {"state": "ERROR", "http": e.code, "detail": str(e)[:80], "s": round(time.time() - t, 2)}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"state": "ERROR", "http": None, "detail": f"{type(e).__name__}: {str(e)[:80]}",
                "s": round(time.time() - t, 2)}
    if not raw.strip():
        return {"state": "ERROR", "http": code, "detail": "empty body", "s": round(time.time() - t, 2)}
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return {"state": "ERROR", "http": code, "detail": "non-JSON", "s": round(time.time() - t, 2)}
    return {"state": "OK", "verdict": d.get("verdict"), "status": d.get("status"),
            "bindings": len(d.get("bindings") or []), "s": round(time.time() - t, 2)}


def show(name, r, expect):
    got = r.get("verdict") or r.get("detail")
    met = expect in str(got).upper()
    print(f"  {'PASS' if met else 'NOTE'}  {name:46s} -> {str(got):26s}  {r['s']}s"
          + ("" if met else f"   (expected ~{expect})"))
    return met


def main():
    ok = 0
    total = 0
    SRC = "Aramco's Jazan refinery has 400,000 barrels a day of diesel capacity."

    print("  1. E3_null_search — claim against an explicit no-source result")
    for name, src in (("empty string (expect HTTP 422, not a verdict)", ""),
                      ("explicit 'no source found'", "No source found for this claim."),
                      ("explicit 'source unavailable'", "The source could not be retrieved.")):
        total += 1
        # An empty source is rejected by the request validator and never reaches the judge, so the expectation
        # there is HTTP_422 (surfaced as ERROR), not a judge verdict. UNSUPPORTED_NUMBER is the abstention.
        want = "ERROR" if src == "" else "UNSUPPORTED_NUMBER"
        ok += show(name, call("Aramco's Jazan refinery has 400,000 barrels a day.", src), want)

    print("\n  2. fabricated citation — the source does not exist")
    total += 1
    ok += show("claim citing a nonexistent report",
               call("According to the 2019 IEA Refining Outlook, Jazan has 400,000 barrels a day.",
                    "IEA World Energy Outlook 2023, chapter 4."), "CONTRADICTED")

    print("\n  3. misquotation — no figures to bind")
    total += 1
    ok += show("claim attributes words the source lacks",
               call("Vitol called the refined-product deficit permanent and irreversible.",
                    "Vitol executives called the refined-product deficit structural, more pronounced than crude."),
               "NO_NUMBERS")

    print("\n  4. superseded figure — old number against a newer source")
    total += 1
    ok += show("claim uses the superseded figure",
               call("Kuwait's refining capacity is 800,000 barrels a day.",
                    "Kuwait's refining capacity is now 1,200,000 barrels a day."), "CONTRADICTED")

    print("\n  5. transport error — the ERROR path must fire, not be read as a refusal")
    total += 1
    r = call("Aramco's Jazan refinery has 400,000 barrels a day.", SRC, url=DEAD)
    good = r["state"] == "ERROR"
    print(f"  {'PASS' if good else 'FAIL'}  {'dead endpoint raises':46s} -> {r['state']:26s}  {r['s']}s  "
          f"{r.get('http') or ''} {r.get('detail','')[:40]}")
    ok += good

    print("\n  6. concurrency — 12 parallel calls")
    claims = [(f"Aramco's Jazan refinery has {n},000 barrels a day of diesel capacity.",
               f"Aramco's Jazan refinery has {n},000 barrels a day of diesel capacity.") for n in range(410, 422)]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=12) as ex:
        rs = list(ex.map(lambda c: call(*c), claims))
    wall = time.time() - t0
    errs = [r for r in rs if r["state"] != "OK"]
    verdicts = sorted({r.get("verdict") for r in rs if r["state"] == "OK"})
    total += 1
    good = (len(errs) == 0 and verdicts == ["OK"])
    ok += good
    print(f"  {'PASS' if good else 'FAIL'}  {'12 parallel, all matching':46s} -> "
          f"{len(rs)-len(errs)}/{len(rs)} ok, verdicts {verdicts}, wall {wall:.1f}s")
    if errs:
        for e in errs[:3]:
            print(f"        {e}")

    print(f"\n  {ok}/{total} cases met their expectation")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
