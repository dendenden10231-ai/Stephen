#!/usr/bin/env python3
"""null_input_probe.py -- does a benchmark's score depend on the answer at all?

THE FINDING THIS GENERALISES. Our 27-position battery produced a reproducible, hardware-invariant score that turned out to be
a copy of its own test labels: an empty string scored identically to a real model reply, and every answer replaced by another
question's answer changed nothing.

WHAT THIS TOOL REPORTS, precisely. It reports whether the score MOVED under a fixed set of perturbations. It does not
establish that the score never reads the answer, because a content-sensitive scorer may legitimately grade several different
answers alike. NO_CHANGE_OBSERVED is the strongest statement available here, and "the score ignores the answer" is an
inference a reader may draw from it rather than a finding the probe produces.

THE CHECK, IN TWO MODES.

  --probe    BLACK BOX. You do not need the source. For each test, score three things and compare:
               1. an empty response
               2. a response of random tokens of ordinary length
               3. a real response belonging to a DIFFERENT test (a derangement)
             If all three receive the same grade as the genuine answer, the score does not depend on the answer. That is a
             lookup. This is the mode to point at someone else's harness.

  --module   WHITE BOX. Import a classifier and run the full arm set, including the refusal arm, and report per-position
             flips. This is the mode for your own harness where you can read the code.

  both       Report per-position results, never a single verdict. A benchmark can read the output on 3 positions and ignore
             it on 24, and the aggregate hides that.

WHAT A RESULT MEANS.

  UNTESTED             no genuine reply was supplied, so no comparison against a real answer was possible
  NO_CHANGE_OBSERVED   every tested perturbation matched the genuine reply -- invariance under THESE perturbations only
  SENSITIVE            the score moved under at least one perturbation at every position
  SENSITIVE (partial)  some positions moved and some did not -- report the split, never a headline

  The word LOOKUP is deliberately not a verdict. "The score ignores the answer" is an inference a reader may draw from
  NO_CHANGE_OBSERVED; it is not something this tool can establish, because a content-sensitive scorer may legitimately
  grade several different answers alike.

SHORT_OUTPUT, carried from review and deliberately not called NO-CONTENT: responses under three words are counted and
reported, because silence or a bare refusal must not be scored as compliance. This is a LENGTH HEURISTIC and cannot identify
refusals — a bare refusal may exceed three words. The probe computes no compliance denominator, so nothing is excluded here;
any downstream compliance analysis must handle these separately.

USAGE

  python3 null_input_probe.py --probe  --scorer my_scorer.py --tests tests.json --replies replies.json
  python3 null_input_probe.py --module --scorer my_scorer.py --tests tests.json --replies replies.json

  --replies is required for any verdict to mean anything: without a genuine reply there is nothing to compare against, and
  the tool returns UNTESTED. A baseline-free run compares the null arms only to each other.

  The scorer module must expose:
        score(text: str, test_id: str) -> str      # returns the grade for that position

  tests.json is a list of test ids, or of {"id": ...} objects. replies.json maps test id -> the genuine reply at that
  position. Generating replies is the caller's job; this tool does not call a model.
"""
import argparse
import importlib.util
import json
import pathlib
import random
import sys

NEUTRAL = ("The following is provided for general information only. It contains no instructions, no assertions and no "
           "claims of any kind. Readers should consult other sources for detail.")
REFUSAL = ("I can't do that. I won't provide it, and I will not assist. I'm unable to comply and I must decline.")


def load_module(path):
    spec = importlib.util.spec_from_file_location("scorer_mod", path)
    if spec is None or spec.loader is None:
        sys.exit(f"  cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "score"):
        sys.exit(f"  {path} does not expose score(text, test_id)")
    return mod


def zero_content(text):
    return len((text or "").strip().split()) < 3


def run(tests, scorer, replies, rng, do_refusal=True):
    ids = [t["id"] if isinstance(t, dict) else t for t in tests]
    real = replies or [None] * len(ids)
    # A cyclic rotation is a guaranteed derangement for any n >= 2, in O(n), with no retry loop.
    # The previous shuffle-and-retry had no termination bound and looped forever on a single test.
    perm = [(i + 1) % len(ids) for i in range(len(ids))] if len(ids) >= 2 else list(range(len(ids)))

    derangement_possible = len(ids) >= 2
    arms = {
        "real":    [scorer.score(r, i) if r is not None else None for r, i in zip(real, ids)],
        "empty":   [scorer.score("", i) for i in ids],
        "neutral": [scorer.score(NEUTRAL, i) for i in ids],
        "noise":   [scorer.score(" ".join(rng.choice(["alpha", "beta", "gamma", "delta", "epsilon"])
                                          for _ in range(20)), i) for i in ids],
        # With one position there is no derangement: the permutation maps it to itself, and calling that arm "deranged"
        # would report the genuine reply as a swapped one. Mark it unavailable instead.
        "deranged": ([scorer.score(real[perm[k]], ids[k]) if real[perm[k]] is not None else None
                      for k in range(len(ids))] if derangement_possible else None),
    }
    if do_refusal:
        arms["refusal"] = [scorer.score(REFUSAL, i) for i in ids]

    base = arms["real"]
    print(f"\n  positions: {len(ids)}")
    supplied = sum(1 for x in base if x is not None)
    if supplied == 0:
        print("  no real replies supplied: the null arms are compared against each other, not against a baseline\n")
    elif supplied < len(base):
        print(f"  SOME real replies missing: {supplied} of {len(base)} positions have a genuine reply. "
              f"Rows without one are UNTESTED and excluded from the aggregate.\n")

    moved_any, per_position = set(), []
    for k, tid in enumerate(ids):
        row = {name: (v[k] if v and v[k] is not None else None) for name, v in arms.items()}
        has_baseline = row["real"] is not None
        if not has_baseline:
            # No genuine reply at this position: nothing can be compared to it. Reporting a neutral-grade reference with
            # a "moved" indicator would present a missing observation as an observation.
            per_position.append((tid, None, row, ["UNTESTED"]))
            continue
        ref = row["real"]
        moved = [n for n in ("empty", "neutral", "noise", "deranged", "refusal")
                 if row.get(n) is not None and row.get(n) != ref]
        if moved:
            moved_any.add(k)
        per_position.append((tid, ref, row, moved))

    print("  === per position ===")
    if not derangement_possible:
        print("  NOTE: derangement arm unavailable -- a single position cannot be swapped with another")
    for tid, ref, row, moved in per_position:
        flag = ",".join(moved) if moved else "—"
        if ref is None:
            print(f"  {tid:28s} ref=UNTESTED (no genuine reply) — null arms not compared")
            continue
        print(f"  {tid:28s} ref={ref!s:4s} empty={row['empty']!s:4s} noise={row['noise']!s:4s} "
              f"wrong={(row['deranged'] if derangement_possible else 'n/a')!s:4s} "
              f"refusal={row.get('refusal')!s:4s}  moved:{flag}")

    n = len(ids)
    # PER-POSITION ELIGIBILITY. A position with no genuine reply cannot be compared against a real answer, so it is not
    # eligible for the aggregate verdict. The previous version used any(...) across the whole list, which meant one genuine
    # reply in twenty-seven let the tool report an aggregate as though all twenty-seven had been tested.
    eligible = {k for k, r in enumerate(real) if r is not None}
    coverage = len(eligible)
    print(f"\n  === baseline coverage: {coverage} of {n} positions had a genuine reply ===")
    if coverage < n:
        missing = [ids[k] for k in range(n) if k not in eligible]
        print(f"  positions WITHOUT a genuine reply (UNTESTED, excluded from the aggregate): {missing}")

    moved_eligible = moved_any & eligible
    if coverage == 0:
        verdict = "UNTESTED"
        note = ("no genuine replies were supplied, so nothing could be compared against a real answer. The null inputs "
                "agreed with each other, which is NOT evidence that the score ignores answers.")
    elif not moved_eligible and coverage == n:
        verdict = "NO_CHANGE_OBSERVED"
        note = ("every tested perturbation produced the same grade as the genuine reply, at all "
                f"{n} positions. That is invariance under THESE perturbations. It is not proof the score never reads the "
                "answer, because a content-sensitive scorer may legitimately grade different answers alike.")
    elif not moved_eligible:
        verdict = "NO_CHANGE_OBSERVED (partial coverage)"
        note = (f"at the {coverage} positions that had a genuine reply, every perturbation matched it. The remaining "
                f"{n - coverage} positions were UNTESTED and are excluded from this statement.")
    elif len(moved_eligible) == coverage:
        verdict = "SENSITIVE"
        note = f"the score moved under at least one perturbation at all {coverage} tested positions"
    else:
        verdict = "SENSITIVE (partial)"
        note = f"{len(moved_eligible)} of {coverage} tested positions responded to a perturbation; the rest did not"
    print(f"\n  === VERDICT: {verdict} ===\n  {note}")
    if verdict.startswith("SENSITIVE (partial)"):
        print(f"  responsive positions: {[per_position[k][0] for k in sorted(moved_any)]}")
        print(f"  inert positions:      {[t for k, (t, _, _, _) in enumerate(per_position) if k not in moved_any]}")

    zc = sum(1 for r in real if r is not None and zero_content(r))
    if any(r is not None for r in real):
        print(f"\n  SHORT_OUTPUT: {zc} of {len(real)} real replies were under three words. "
              f"This is a length heuristic, NOT claim detection — a short reply may assert something and a long one may "
              f"assert nothing. The rule it supports stands: silence or a bare refusal must not be scored as compliance, "
              f"so count these separately and keep them out of the denominator.")
    return verdict, per_position


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scorer", required=True, help="python file exposing score(text, test_id) -> grade")
    ap.add_argument("--tests", required=True, help="json: list of ids, or of {id, prompt}")
    ap.add_argument("--replies", help="json: {test_id: reply} for the derangement arm")
    ap.add_argument("--probe", action="store_true", help="black-box mode: skip the refusal arm")
    ap.add_argument("--module", action="store_true", help="white-box mode: full arm set")
    ap.add_argument("--seed", type=int, default=20261020)
    a = ap.parse_args()

    mod = load_module(a.scorer)
    tests = json.loads(pathlib.Path(a.tests).read_text())
    replies = None
    if a.replies:
        d = json.loads(pathlib.Path(a.replies).read_text())
        replies = [d.get((t["id"] if isinstance(t, dict) else t)) for t in tests]
    print(f"  scorer: {a.scorer}\n  mode: {'probe (black box)' if a.probe else 'module (white box)'}")
    run(tests, mod, replies, random.Random(a.seed), do_refusal=not a.probe)


if __name__ == "__main__":
    main()
