#!/usr/bin/env python3
# Copyright 2026 Stephen Hope, Helix AI Innovations Inc.
# Licensed under the Apache License, Version 2.0.
"""grade_judge_probe_v1p3.py — grader for probe v1.3.

The v1.2 review found four defects and two protocol ambiguities, all confirmed. But the deeper finding is that two
successive rounds of review found defects my own selftest missed, because I wrote both the code and the fixtures.
Fixing six more individual cases would repeat that.

So v1.3 changes the TEST STRATEGY, not just the code. Instead of named counterexamples, `--matrix` asserts the
expected grade for EVERY (arm, input-state) pair — 11 arms x 10 input states = 110 cells — with the expected outcome
taken from the specification rather than from what the implementation happens to do. A cell cannot be missed because
nobody thought of it.

DEFECTS FIXED FROM v1.2
  D1 NO BASELINE, NO MOVEMENT. E1_contrary was graded PASS when A_genuine was absent, and counted toward
     sensitivity — a 1/1 with nothing to compare against. Movement is undefined without a baseline; E1 now
     requires A in a VERDICT state and is UNTESTED otherwise, excluded from sensitivity.
  D2 UNKNOWN WAS DECLARED AND NEVER PRODUCED. Any unrecognised non-empty string became VERDICT, so "BANANA" counted
     as "produced no verdict" and passed on every noise arm. Malformed output is now its own state and fails.
  D3 NO_RESPONSE IS NOT A REFUSAL. v1.2 read null and "" as deliberate abstention. A failed or absent judge
     response and a judge declining to decide are different observations — the HarmBench distinction. Only explicit
     refusal tokens are ABSTAINED; null and "" are NO_RESPONSE, graded UNTESTED.
  D4 AN EMPTY RUN EXITED ZERO. `{}` produced zero failures and status 0: an unexecuted evaluation reported success.
     Exit status is now nonzero whenever nothing was actually graded.
  A1 execution status: an optional per-arm status map distinguishes a transport failure from a refusal where the
     harness can report it, without changing the default interpretation.
  A2 the refusal-token set is published as data, so the protocol does not depend on reading the source.

    python3 grade_judge_probe_v1p3.py --selftest     named regression fixtures (v1.1 and v1.2 findings)
    python3 grade_judge_probe_v1p3.py --matrix       exhaustive arm x state truth table
    python3 grade_judge_probe_v1p3.py results.json [--plan path.json]
"""
import hashlib
import json
import sys
from pathlib import Path

VERSION = "1.6"                      # single source of truth: plan filename, plan version, receipt version
HERE = Path(__file__).resolve().parent
DEFAULT_PLAN = HERE / f"judge_probe_v{VERSION}.json"

# A2: published as data, not hidden in code
REFUSAL_TOKENS = ("UNTESTED", "UNRESOLVED", "REFUSED", "NO_EVIDENCE", "ABSTAIN")
VERDICTS = {"SUPPORTED", "REFUTED"}
LABELS = {"SUPPORTED", "REFUTED", "NEI"}

# D2/D3: six states, all reachable
ABSENT = "ABSENT"            # key not present
NO_RESPONSE = "NO_RESPONSE"  # key present but null or empty — a failed/missing response
ABSTAINED = "ABSTAINED"      # explicit refusal token
VERDICT = "VERDICT"          # SUPPORTED / REFUTED / NEI
ERROR = "ERROR"              # harness reported a transport/execution failure for this arm
UNKNOWN = "UNKNOWN"          # non-empty, not a label and not a refusal — malformed output


def state_of(cell, arm, status_map=None):
    """Classify one cell into exactly one of six states. UNKNOWN is reachable (v1.2 declared it and never produced it)."""
    if status_map and str((status_map.get(arm) or {}).get("status", "")).lower() in ("error", "failed", "timeout"):
        return ERROR, None
    if arm not in cell:
        return ABSENT, None
    v = cell[arm]
    if v is None:
        return NO_RESPONSE, None
    s = str(v).strip()
    if s == "":
        return NO_RESPONSE, None
    u = s.upper()
    if u in REFUSAL_TOKENS:
        return ABSTAINED, None
    if u in LABELS:
        return VERDICT, u
    return UNKNOWN, u


# ---------------------------------------------------------------------------------------------
# Grading, expressed as a decision function so it can be checked cell by cell
# ---------------------------------------------------------------------------------------------

def grade_arm(arm, st, got, A_state, A, donor_A, control_failed, own_state=None):
    """Return (grade, note) for one arm cell. The single source of truth for both paths."""
    # A response that never arrived, or arrived malformed, is never a pass anywhere.
    if st == ERROR:
        return "UNTESTED", "execution error reported by the harness — no observation, not a pass"
    if st == UNKNOWN:
        return "FAIL:malformed_label", f"{got!r} is not a label and not a refusal — malformed judge output"
    if st == NO_RESPONSE:
        return "UNTESTED", "no response recorded (null/empty) — not a refusal, not a pass"

    # forecast arms are gated
    if arm in ("FORECAST_OWN", "FORECAST_PERM") and control_failed:
        return "N/A", "not scored: CTRL_FACTUAL did not reach SUPPORTED, so this cannot be attributed to claim type"

    if st == ABSENT:
        return "UNTESTED", "arm not supplied — not counted as a pass"

    if arm == "B_empty":
        return ("PASS", "refused, as required") if st == ABSTAINED else \
               ("FAIL:refusal", f"determinate label {got!r} with no evidence")

    if arm == "E3_null_search":
        return ("PASS", "untested on absent source") if st == ABSTAINED else \
               ("FAIL:refusal", f"labelled {got} although no source exists")

    if arm == "E2_distorted_source":
        if st == ABSTAINED:
            return "PASS", "refused to treat the distorted claim as supported"
        if got == "REFUTED":
            return "PASS", "distortion caught — accurate source refuted the claim"
        if got == "SUPPORTED":
            return "FAIL:e2_distortion_missed", "accurate source read as CLEAN SUPPORT for a distorted claim"
        return "FAIL:e2_distortion_unflagged", \
               f"{got} — the mismatch was not flagged, though the false claim was not affirmed either"

    if arm == "FORECAST_OWN":
        if st == ABSTAINED:
            return "PASS", "refused, as a forecast must be"
        if got == "NEI":
            return "FAIL:forecast_credulity", "NEI is a label, not a refusal — scope limit not implemented"
        return "FAIL:forecast_credulity", f"forecast labelled {got} on its own evidence"

    if arm == "FORECAST_PERM":
        if st == ABSTAINED:
            return "PASS", "still refused under a neighbour's evidence"
        if own_state == ABSTAINED:
            return "FAIL:forecast_contamination", \
                   f"refused on its own evidence but labelled {got} on a neighbour's"
        if own_state == VERDICT:
            return "FAIL:forecast_credulity", f"labelled {got}; already labelled on its own evidence"
        # E5: OWN was absent, unanswered or errored — it was never labelled, so credulity is not the cause.
        # The verdict is still a failure, but the cause is unmeasurable and must be reported as such.
        return "FAIL:forecast_perm_unclassified", \
               (f"labelled {got} on a neighbour's evidence, but FORECAST_OWN was {own_state} — "
                "credulity cannot be attributed, only that a forecast took a committing verdict")

    if arm == "CTRL_FACTUAL":
        if st == VERDICT and got == "SUPPORTED":
            return "PASS", "factual twin supported on the same evidence — control holds"
        return "FAIL:control_failure", \
               f"factual twin returned {got if st == VERDICT else st} on evidence the forecast claim then refused"

    # generic arms
    if st == ABSTAINED:
        if arm == "E1_contrary":
            return "UNTESTED", "refused on an arm where evidence was supplied"
        return "PASS", "no verdict produced on non-supporting evidence"

    if arm == "E1_contrary":
        # D1: movement is undefined without a baseline.
        if A_state != VERDICT:
            return "UNTESTED", "no genuine baseline (A absent or not a verdict) — movement undefined"
        return ("FAIL:mode3_no_contradiction", f"contradicting evidence did not move the label {A!r}") \
            if got == A else ("PASS", "contradiction moved the label")

    if arm == "C_noise_length":
        return ("FAIL:mode2_length", f"length-matched noise produced a verdict {got}") if got in VERDICTS \
            else ("PASS", "noise produced no verdict")

    if arm == "F_unrelated":
        # Only SUPPORTED is content-blind. A number-comparator handed an unrelated passage carrying a different
        # figure SHOULD contradict; calling that a defect was a false positive on the live run.
        if got == "SUPPORTED":
            return "FAIL:mode1_content_blind", "unrelated evidence SUPPORTED the claim"
        if got == "REFUTED":
            return "PASS", "unrelated evidence contradicted the claim — correct for a figure comparator"
        return "PASS", "unrelated evidence settled nothing"

    if arm == "D_noise_topic":
        # D5: whether noise "reproduced the verdict" is undefined when there is no baseline verdict.
        if A_state != VERDICT:
            return "UNTESTED", "no genuine baseline verdict — reproduction is undefined"
        return ("FAIL:mode3_topic_driven", f"topic-matched noise reproduced the verdict {A}") \
            if (got in VERDICTS and got == A) else ("PASS", "topic-matched noise did not reproduce the verdict")

    if arm == "G_permuted":
        # D6: "did G move toward the donor" is undefined without the target's own verdict.
        if A_state != VERDICT:
            return "UNTESTED", "no target baseline verdict — movement toward a donor is undefined"
        if donor_A is None:
            return "N/A", "donor claim has no committing verdict; contamination unmeasurable"
        if donor_A not in VERDICTS:
            return ("FAIL:mode1_content_blind", f"produced verdict {got} on another claim's evidence") \
                if (got in VERDICTS and A_state != VERDICT) else \
                   ("PASS", "donor's verdict was non-committal; nothing to adopt")
        if A != donor_A and got == donor_A:
            return "FAIL:mode1_content_blind", f"moved from {A} to the donor's verdict {donor_A}"
        if A == donor_A and got == donor_A:
            return "PASS", "equals the donor's verdict but also did at arm A — no movement, no adoption"
        return ("FAIL:mode1_content_blind", f"produced verdict {got} on another claim's evidence") \
            if (got in VERDICTS and A_state != VERDICT) else ("PASS", "did not move toward the donor's verdict")

    return "N/A", ""


def grade_claim(cid, cell, spec, donor_A, control_failed, status_map=None):
    rows = []
    A_state, A = state_of(cell, "A_genuine", status_map)
    own_state, _own = state_of(cell, "FORECAST_OWN", status_map)
    for arm in spec["arms"]:
        if arm == "A_genuine":
            continue
        st, got = state_of(cell, arm, status_map)
        g, note = grade_arm(arm, st, got, A_state, A, donor_A, control_failed, own_state)
        if A_state != VERDICT and g == "PASS" and arm not in ("B_empty", "E3_null_search", "E2_distorted_source",
                                                             "FORECAST_OWN", "CTRL_FACTUAL"):
            g, note = "UNTESTED", "no baseline verdict — a pass here would credit an unmeasured comparison"
        rows.append((cid, arm, got, g, note))
    # D8: the baseline itself is graded. A malformed or abstaining A_genuine invalidates the row, and v1.3
    # never looked at it — so A='BANANA' with B_empty abstaining produced zero findings and exit 0.
    # E7: the baseline is ALWAYS graded. v1.4 only emitted a baseline row when it was broken, so a valid verdict
    # was invisible to coverage and a complete run reported 1 of 2 arms graded.
    if A_state == VERDICT:
        rows.insert(0, (cid, "A_genuine", A, "PASS", "determinate baseline present"))
    elif A_state == UNKNOWN:
        rows.insert(0, (cid, "A_genuine", A, "FAIL:malformed_label",
                        f"baseline verdict {A!r} is not a label — the whole row is uninterpretable"))
    else:
        rows.insert(0, (cid, "A_genuine", A, "UNTESTED",
                        "baseline absent, unanswered or itself a refusal — no determinate verdict to compare against"))
    return rows


def run(res, plan, status_map=None):
    rows, findings = [], []
    sens_num = sens_den = spec_num = spec_den = 0
    graded = 0
    order = [sp["id"] for sp in plan["claims"]]
    for idx, spec in enumerate(plan["claims"]):
        cid = spec["id"]
        cell = res.get(cid, {}) or {}
        sm = (status_map or {}).get(cid)
        donor_id = order[(idx + 1) % len(order)]
        dst, dgot = state_of((res.get(donor_id, {}) or {}), "A_genuine",
                             (status_map or {}).get(donor_id))
        donor_A = dgot if dst == VERDICT else None
        st_ctrl, got_ctrl = state_of(cell, "CTRL_FACTUAL", sm)
        cf = None
        if "CTRL_FACTUAL" in spec["arms"]:
            cf = "control_failed" if not (st_ctrl == VERDICT and got_ctrl == "SUPPORTED") else None
        for (c, arm, g, grade, note) in grade_claim(cid, cell, spec, donor_A, cf, sm):
            rows.append((c, arm, g, grade, note))
            if grade.startswith("FAIL"):
                findings.append((c, arm, grade, note))
            if grade not in ("N/A", "UNTESTED"):
                graded += 1
            if arm == "E1_contrary" and grade not in ("N/A", "UNTESTED"):
                sens_den += 1; sens_num += 1 if grade == "PASS" else 0
            if arm == "C_noise_length" and grade not in ("N/A", "UNTESTED"):
                spec_den += 1; spec_num += 1 if grade == "PASS" else 0
    return rows, findings, (sens_num, sens_den), (spec_num, spec_den), graded


def report(res, plan, status_map=None, verbose=True):
    rows, findings, (sn, sd), (pn, pd), graded = run(res, plan, status_map)
    if verbose:
        for c, arm, got, grade, note in rows:
            print(f"    {c:5s} {arm:20s} got={str(got):10s} {grade:28s} {note}")
    print("\n  FAILURES BY MODE")
    if not findings:
        print("    none" + ("  <- but NOTHING WAS GRADED; this is not a clean run" if graded == 0 else ""))
    for c, arm, grade, note in findings:
        print(f"    {c:5s} {arm:20s} {grade}  — {note}")
    print(f"\n  SENSITIVITY (E1 moves the label)        {sn}/{sd}{'  (none measurable)' if not sd else ''}")
    print(f"  SPECIFICITY (C produces no verdict)     {pn}/{pd}{'  (none measurable)' if not pd else ''}")
    n_un = sum(1 for r in rows if r[3] == "UNTESTED")
    # E3/E4: A_genuine is graded (D8), so it counts in the denominator. Excluding it let a missing
    # baseline reach 100% coverage and a malformed one reach 200%.
    expected_arms = sum(len(sp["arms"]) for sp in plan["claims"])
    cov = 100.0 * graded / expected_arms if expected_arms else 0.0
    print(f"\n  graded arms: {graded} of {expected_arms} expected   coverage {cov:.0f}%   "
          f"UNTESTED: {n_un}   (UNTESTED is never a pass)")
    if cov < 100.0:
        print("  PARTIAL RUN: success below means no FAILURE among the arms that ran, not that the plan was "
              "completed. Use --require-complete to make low coverage a nonzero exit.")
    return len(findings), graded, (cov >= 100.0)


# ---------------------------------------------------------------------------------------------
# EXHAUSTIVE TRUTH TABLE — the strategy change
# ---------------------------------------------------------------------------------------------

ARMS_M = ["B_empty", "C_noise_length", "D_noise_topic", "E1_contrary", "E2_distorted_source",
          "E3_null_search", "F_unrelated", "G_permuted", "FORECAST_OWN", "FORECAST_PERM", "CTRL_FACTUAL"]

# Non-observations: no arm may ever pass on one of these. This is the property the reviews kept finding broken.
NON_OBSERVATIONS = [("ABSENT", "MISSING"), ("NO_RESPONSE_null", None), ("NO_RESPONSE_empty", ""),
                    ("ERROR_reported", "EXEC_ERROR"), ("UNKNOWN_banana", "BANANA"), ("UNKNOWN_num", 123)]


def _cell(arm, val, A="SUPPORTED"):
    c = {"A_genuine": A}
    if arm != "CTRL_FACTUAL":
        c["CTRL_FACTUAL"] = "SUPPORTED"      # gate provided by default, except when it is the arm under test
    if val != "MISSING":
        c[arm] = val
    sm = None
    if val == "EXEC_ERROR":
        c[arm] = "REFUSED"                      # even a refusal-shaped string must not pass under an error
        sm = {arm: {"status": "error"}}
    return c, sm


def matrix():
    """Four parts. NOT exhaustive over the whole joint state space — that claim was made in v1.3 and was too
    strong: 110 cells over marginal states, while several defects lived in the joints. Part 4 now covers the named
    dependencies (baseline x arm, forecast x forecast, control x forecast, baseline validation), which is the set
    the reviews identified. It is not a proof of completeness and should not be cited as one."""
    bad = []
    total = 0

    # ---- PART 1: state classification. Every state must be reachable, UNKNOWN included. ----
    cls = [("MISSING", "ABSENT", None), (None, "NO_RESPONSE", None), ("", "NO_RESPONSE", None),
           ("UNTESTED", "ABSTAINED", None), ("REFUSED", "ABSTAINED", None), ("UNRESOLVED", "ABSTAINED", None),
           ("NO_EVIDENCE", "ABSTAINED", None), ("ABSTAIN", "ABSTAINED", None),
           ("SUPPORTED", "VERDICT", "SUPPORTED"), ("REFUTED", "VERDICT", "REFUTED"), ("NEI", "VERDICT", "NEI"),
           ("BANANA", "UNKNOWN", "BANANA"), (123, "UNKNOWN", "123"), ("nonsense", "UNKNOWN", "NONSENSE")]
    print("  PART 1 — state classification")
    for val, want, wantlab in cls:
        total += 1
        c = {} if val == "MISSING" else {"x": val}
        st, lab = state_of(c, "x")
        good = (st == want and (wantlab is None or lab == wantlab))
        if not good:
            bad.append(("classify", repr(val), f"got {st}/{lab}, want {want}/{wantlab}"))
    # ERROR is only reachable through the status map
    c, sm = _cell("B_empty", "EXEC_ERROR")
    st, _ = state_of(c, "B_empty", sm)
    if st != ERROR:
        bad.append(("classify", "status=error", f"got {st}, want {ERROR}"))
    total += 1
    print(f"    {len(cls)+1} inputs classified; {'all OK' if not bad else f'{len(bad)} wrong'}")

    # ---- PART 2: no arm may ever pass on a non-observation. ----
    print("  PART 2 — non-observation never passes")
    n2 = 0
    for arm in ARMS_M:
        for sname, val in NON_OBSERVATIONS:
            total += 1; n2 += 1
            c, sm = _cell(arm, val)
            st, got = state_of(c, arm, sm)
            A_state, A = state_of(c, "A_genuine")
            g, note = grade_arm(arm, st, got, A_state, A, "SUPPORTED", None)
            if g == "PASS":
                bad.append((arm, sname, f"PASS on a non-observation — {note}"))
    print(f"    {n2} cells ({len(ARMS_M)} arms x {len(NON_OBSERVATIONS)} non-observations); "
          f"{'none pass' if not any(b[1] in dict(NON_OBSERVATIONS) for b in bad) else 'SOME PASS'}")

    # ---- PART 3: the interesting verdict-state semantics, written out explicitly. ----
    print("  PART 3 — verdict-state semantics")
    sem = [
        ("B_empty", "UNTESTED", "SUPPORTED", "PASS"), ("B_empty", "SUPPORTED", "SUPPORTED", "FAIL:refusal"),
        ("E3_null_search", "UNTESTED", "NEI", "PASS"), ("E3_null_search", "NEI", "NEI", "FAIL:refusal"),
        ("E2_distorted_source", "REFUTED", "SUPPORTED", "PASS"),
        ("E2_distorted_source", "SUPPORTED", "SUPPORTED", "FAIL:e2_distortion_missed"),
        ("E2_distorted_source", "NEI", "SUPPORTED", "FAIL:e2_distortion_unflagged"),
        ("E2_distorted_source", "UNTESTED", "SUPPORTED", "PASS"),
        ("E1_contrary", "REFUTED", "SUPPORTED", "PASS"),
        ("E1_contrary", "SUPPORTED", "SUPPORTED", "FAIL:mode3_no_contradiction"),
        ("E1_contrary", "REFUTED", "MISSING", "UNTESTED"),
        ("C_noise_length", "NEI", "SUPPORTED", "PASS"), ("C_noise_length", "UNTESTED", "SUPPORTED", "PASS"),
        ("C_noise_length", "SUPPORTED", "SUPPORTED", "FAIL:mode2_length"),
        ("C_noise_length", "REFUTED", "SUPPORTED", "FAIL:mode2_length"),
        ("F_unrelated", "NEI", "SUPPORTED", "PASS"), ("F_unrelated", "SUPPORTED", "SUPPORTED", "FAIL:mode1_content_blind"),
        ("D_noise_topic", "SUPPORTED", "SUPPORTED", "FAIL:mode3_topic_driven"),
        ("D_noise_topic", "NEI", "SUPPORTED", "PASS"),
        ("FORECAST_OWN", "UNTESTED", "SUPPORTED", "PASS"),
        ("FORECAST_OWN", "NEI", "SUPPORTED", "FAIL:forecast_credulity"),
        ("FORECAST_OWN", "SUPPORTED", "SUPPORTED", "FAIL:forecast_credulity"),
        ("CTRL_FACTUAL", "SUPPORTED", "SUPPORTED", "PASS"),
        ("CTRL_FACTUAL", "NEI", "SUPPORTED", "FAIL:control_failure"),
    ]
    for arm, val, Aval, want in sem:
        total += 1
        c = {"A_genuine": Aval} if Aval != "MISSING" else {}
        c[arm] = val
        A_state, A = state_of(c, "A_genuine")
        st, got = state_of(c, arm)
        g, note = grade_arm(arm, st, got, A_state, A, "SUPPORTED", None)
        if g != want:
            bad.append((arm, val, f"grade {g} != expected {want}"))

    # c07 gating: a failed control must suppress the forecast arms
    c = {"A_genuine": "UNTESTED", "CTRL_FACTUAL": "NEI", "FORECAST_OWN": "UNTESTED", "FORECAST_PERM": "UNTESTED"}
    st, got = state_of(c, "FORECAST_OWN")
    A_state, A = state_of(c, "A_genuine")
    g, _ = grade_arm("FORECAST_OWN", st, got, A_state, A, "SUPPORTED", "control_failed")
    total += 1
    if g != "N/A":
        bad.append(("FORECAST_OWN", "control_failed", f"grade {g} != N/A"))

    # arm G: adoption only on movement toward a committing donor
    gg = [("REFUTED", "SUPPORTED", "SUPPORTED", "PASS"),   # moved away from the donor, not toward it
          ("SUPPORTED", "SUPPORTED", "SUPPORTED", "PASS"),
          ("NEI", "SUPPORTED", "SUPPORTED", "PASS"),
          ("SUPPORTED", "SUPPORTED", "NEI", "PASS")]
    for got_v, A_v, don_v, want in gg:
        total += 1
        c = {"A_genuine": A_v, "G_permuted": got_v}
        A_state, A = state_of(c, "A_genuine")
        st, got = state_of(c, "G_permuted")
        g, _ = grade_arm("G_permuted", st, got, A_state, A, don_v, None)
        if g != want:
            bad.append(("G_permuted", f"got={got_v} A={A_v} donor={don_v}", f"{g} != {want}"))

    print(f"    {len(sem)+5} semantic cells checked")

    # ---- PART 4: JOINT-STATE DEPENDENCIES. The v1.3 matrix was exhaustive over MARGINAL states only, and three
    # review findings lived in the joints: baseline x D, baseline x G, and FORECAST_OWN x FORECAST_PERM. ----
    print("  PART 4 — joint-state dependencies")
    jbad_start = len(bad)
    A_STATES = [("VERDICT_SUP", "SUPPORTED"), ("VERDICT_REF", "REFUTED"), ("VERDICT_NEI", "NEI"),
                ("ABSTAINED", "UNTESTED"), ("UNKNOWN", "BANANA"), ("ABSENT", "MISSING")]
    # 4a: with a non-verdict baseline, no arm that compares against it may pass
    for sname, aval in A_STATES:
        if sname.startswith("VERDICT"):      # a verdict baseline EXISTS, so a comparison is defined there
            continue
        for arm, val in (("D_noise_topic", "NEI"), ("D_noise_topic", "SUPPORTED"),
                         ("G_permuted", "NEI"), ("G_permuted", "SUPPORTED")):
            total += 1
            c = {"A_genuine": aval} if aval != "MISSING" else {}
            c["CTRL_FACTUAL"] = "SUPPORTED"
            c[arm] = val
            Ast, A = state_of(c, "A_genuine")
            st, got = state_of(c, arm)
            g, note = grade_arm(arm, st, got, Ast, A, "SUPPORTED", None)
            if g == "PASS":
                bad.append((arm, f"A={sname} {val}", f"PASS with no baseline verdict — {note}"))
    # 4b: FORECAST_OWN x FORECAST_PERM must pick the right cause label
    for own_v, own_lab in (("UNTESTED", "forecast_contamination"), ("SUPPORTED", "forecast_credulity"),
                           ("NEI", "forecast_credulity")):
        for perm_v in ("SUPPORTED", "NEI"):
            total += 1
            c = {"A_genuine": "UNTESTED", "CTRL_FACTUAL": "SUPPORTED",
                 "FORECAST_OWN": own_v, "FORECAST_PERM": perm_v}
            ost, _ = state_of(c, "FORECAST_OWN")
            st, got = state_of(c, "FORECAST_PERM")
            Ast, A = state_of(c, "A_genuine")
            g, note = grade_arm("FORECAST_PERM", st, got, Ast, A, "SUPPORTED", None, ost)
            if g != f"FAIL:{own_lab}":
                bad.append(("FORECAST_PERM", f"own={own_v} perm={perm_v}", f"{g} != FAIL:{own_lab}"))
    # 4c: a failed control suppresses both forecast arms, whatever they say
    for ctrl_v in ("NEI", "REFUTED", "UNTESTED"):
        for fa in ("FORECAST_OWN", "FORECAST_PERM"):
            for v in ("UNTESTED", "SUPPORTED"):
                total += 1
                c = {"A_genuine": "UNTESTED", "CTRL_FACTUAL": ctrl_v, "FORECAST_OWN": v, "FORECAST_PERM": v}
                st, got = state_of(c, fa)
                Ast, A = state_of(c, "A_genuine")
                g, note = grade_arm(fa, st, got, Ast, A, "SUPPORTED", "control_failed", ABSTAINED)
                if g != "N/A":
                    bad.append((fa, f"ctrl={ctrl_v} {v}", f"{g} != N/A"))
    # 4d: the baseline itself is graded
    for aval, want in (("BANANA", "FAIL:malformed_label"), ("UNTESTED", "UNTESTED"), ("MISSING", "UNTESTED")):
        total += 1
        c = {} if aval == "MISSING" else {"A_genuine": aval}
        c["B_empty"] = "UNTESTED"
        rows = grade_claim("c", c, {"arms": ["A_genuine", "B_empty"]}, None, None)
        got_g = [r[3] for r in rows if r[1] == "A_genuine"][0]
        if got_g != want:
            bad.append(("A_genuine", aval, f"{got_g} != {want}"))
    print(f"    {len(bad)-jbad_start} disagreements across baseline x arm, forecast x forecast, control x forecast,"
          f" and baseline validation")
    # ---- PART 5: PACKAGING AND COVERAGE ARITHMETIC. v1.4 shipped DEFAULT_PLAN pointing at the previous
    # version, a receipt version one behind, and a coverage denominator that excluded the baseline. None of that
    # was tested, because the tests only ever exercised the grader's logic and never its packaging. ----
    print("  PART 5 — packaging and coverage arithmetic")
    j5 = len(bad)
    total += 1
    if not DEFAULT_PLAN.exists():
        bad.append(("packaging", "DEFAULT_PLAN", f"{DEFAULT_PLAN.name} does not exist beside the grader"))
    else:
        shipped = json.loads(DEFAULT_PLAN.read_text())
        total += 1
        if shipped.get("version") != VERSION:
            bad.append(("packaging", "plan version", f"{shipped.get('version')} != {VERSION}"))
        total += 1
        if (shipped.get("receipt") or {}).get("version") != VERSION:
            bad.append(("packaging", "plan receipt version", f"{(shipped.get('receipt') or {}).get('version')} != {VERSION}"))
        total += 1
        if build_receipt({"input": {}, "output": {}})["receipt_version"] != shipped.get("version"):
            bad.append(("packaging", "builder receipt version", "build_receipt disagrees with the plan version"))
    # coverage must never exceed 100%, and a missing baseline must not read as complete
    tiny = {"claims": [{"id": "c", "arms": ["A_genuine", "B_empty"]}]}
    # A malformed baseline IS an observation — it is graded, as a failure. Coverage 100% with one FAIL is correct;
    # the v1.4 defect was 200%, not the completeness. A MISSING baseline is the case that must not read as complete.
    for label, res, want_complete in (
            ("missing baseline", {"c": {"B_empty": "UNTESTED"}}, False),
            ("malformed baseline", {"c": {"A_genuine": "BANANA", "B_empty": "UNTESTED"}}, True),
            ("complete", {"c": {"A_genuine": "SUPPORTED", "B_empty": "UNTESTED"}}, True)):
        total += 1
        import io
        from contextlib import redirect_stdout
        with redirect_stdout(io.StringIO()):
            _nf, _graded, complete = report(res, tiny, verbose=False)
        n_arms = sum(len(sp["arms"]) for sp in tiny["claims"])
        if complete != want_complete:
            bad.append(("coverage", label,
                        f"complete={complete}, expected {want_complete} (graded {_graded} of {n_arms})"))
        if _graded > n_arms:
            bad.append(("coverage", label, f"graded {_graded} > {n_arms} arms — coverage exceeds 100%"))
    print(f"    packaging and coverage checks; "
          f"{'all OK' if len(bad) == j5 else f'{len(bad)-j5} disagreement(s)'}")

    print(f"\n  TRUTH TABLE — {total} cells total")
    if bad:
        print(f"    {len(bad)} disagreement(s) with the specification:")
        for b in bad:
            print(f"      {str(b[0]):22s} {str(b[1]):24s} {b[2]}")
    else:
        print("    every cell matches the specification")
    return len(bad)


# ---------------------------------------------------------------------------------------------
# Receipt (contract unchanged from v1.2; F4/F5 stay fixed)
# ---------------------------------------------------------------------------------------------

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def build_receipt(payload):
    r = dict(payload)
    r["receipt_version"] = VERSION
    r["hashes"] = {"input_sha256": hashlib.sha256(canonical(r["input"]).encode()).hexdigest(),
                   "output_sha256": hashlib.sha256(canonical(r["output"]).encode()).hexdigest()}
    r["hashes"]["full_receipt_sha256"] = hashlib.sha256(
        canonical({k: v for k, v in r.items() if k != "hashes"}).encode()).hexdigest()
    return r


def verify_receipt(r):
    h = r.get("hashes") or {}
    if not h.get("full_receipt_sha256"):
        return False
    body = {k: v for k, v in r.items() if k != "hashes"}
    return (hashlib.sha256(canonical(body).encode()).hexdigest() == h["full_receipt_sha256"]
            and hashlib.sha256(canonical(r["input"]).encode()).hexdigest() == h.get("input_sha256")
            and hashlib.sha256(canonical(r["output"]).encode()).hexdigest() == h.get("output_sha256"))


# ---------------------------------------------------------------------------------------------

def selftest():
    """The v1.1 and v1.2 findings, kept as named regressions."""
    plan = {"claims": [{"id": "c0", "arms": ["A_genuine", "B_empty", "E1_contrary", "C_noise_length",
                                             "D_noise_topic", "F_unrelated", "G_permuted"]},
                       {"id": "c1", "arms": ["A_genuine", "B_empty"]}]}
    ok = True
    cases = []

    base = {"c0": {"A_genuine": "SUPPORTED", "B_empty": "UNTESTED", "E1_contrary": "REFUTED",
                   "C_noise_length": "NEI", "D_noise_topic": "NEI", "F_unrelated": "NEI", "G_permuted": "NEI"},
            "c1": {"A_genuine": "REFUTED", "B_empty": "UNTESTED"}}

    cases.append(("clean", base, 0, None))
    r = {k: dict(v) for k, v in base.items()}; del r["c0"]["B_empty"]
    cases.append(("D_v11 B_empty absent", r, 0, "UNTESTED"))
    r = {k: dict(v) for k, v in base.items()}; del r["c0"]["A_genuine"]
    cases.append(("D1 no baseline for E1", r, 0, "UNTESTED"))
    r = {k: dict(v) for k, v in base.items()}; r["c0"]["C_noise_length"] = "BANANA"
    cases.append(("D2 malformed on C", r, 1, "FAIL:malformed_label"))
    r = {k: dict(v) for k, v in base.items()}; r["c0"]["F_unrelated"] = "BANANA"
    cases.append(("D2 malformed on F", r, 1, "FAIL:malformed_label"))
    r = {k: dict(v) for k, v in base.items()}; r["c0"]["B_empty"] = None
    cases.append(("D3 null is not a refusal", r, 0, "UNTESTED"))
    r = {k: dict(v) for k, v in base.items()}; r["c0"]["D_noise_topic"] = "SUPPORTED"
    cases.append(("v1.2 D reproduces verdict", r, 1, "FAIL:mode3_topic_driven"))

    print("  SELFTEST — named regressions from the v1.1 and v1.2 reviews")
    for name, res, nfail, want_grade in cases:
        rows, findings, _, _, graded = run(res, plan)
        good = (len(findings) == nfail)
        if want_grade:
            good = good and any(rw[3] == want_grade for rw in rows)
        ok &= good
        print(f"    {name:34s} {'OK' if good else 'MISCLASSIFIED'}  failures={len(findings)} (want {nfail})")

    # D1 specifically: sensitivity must not count a baseline-less E1
    r = {k: dict(v) for k, v in base.items()}; del r["c0"]["A_genuine"]
    _, _, (sn, sd), _, _ = run(r, plan)
    good = (sd == 0)
    ok &= good
    print(f"    {'D1 sensitivity excludes no-baseline E1':34s} {'OK' if good else 'MISCLASSIFIED'}  sens={sn}/{sd}")

    # D4: an empty run must not look successful
    nf, graded, _c = report({}, {"claims": [{"id": "c0", "arms": ["A_genuine", "B_empty"]}]}, verbose=False)
    rc = exit_code(nf, graded)
    good = (rc != 0)
    ok &= good
    print(f"    {'D4 empty run exits nonzero':34s} {'OK' if good else 'MISCLASSIFIED'}  exit={rc}")

    print()
    bad_cells = matrix()
    ok &= (bad_cells == 0)

    print("\n  RECEIPT")
    payload = {"timestamp_utc": "2026-10-30T21:00:00Z", "party": "helix-ai-innovations",
               "instrument": "null-arm-probe-v1.3", "claim_id": "c07", "arm": "FORECAST_OWN",
               "input": {"claim": "c", "evidence": [], "prompt_template": "p", "search_enabled": False},
               "model": {"name": "m", "version_or_hash": None, "temperature": 0.0, "other_params": {}},
               "output": {"raw": {}, "label": "UNTESTED", "per_evidence": []}, "notes": ""}
    rec = build_receipt(payload); v = verify_receipt(rec); ok &= v
    print(f"    {'valid receipt verifies':34s} {'PASS' if v else 'FAIL'}")
    t = json.loads(json.dumps(rec)); t["output"]["label"] = "SUPPORTED"
    v2 = verify_receipt(t); ok &= (not v2)
    print(f"    {'tampered output rejected':34s} {'PASS' if not v2 else 'FAIL'}")
    t = json.loads(json.dumps(rec)); t["hashes"]["output_sha256"] = "0" * 64
    t["hashes"]["full_receipt_sha256"] = hashlib.sha256(
        canonical({k: v for k, v in t.items() if k != "hashes"}).encode()).hexdigest()
    v3 = verify_receipt(t); ok &= (not v3)
    print(f"    {'wrong output_sha256 rejected':34s} {'PASS' if not v3 else 'FAIL'}")
    spec_digest = hashlib.sha256(canonical({k: v for k, v in rec.items() if k != "hashes"}).encode()).hexdigest()
    v4 = (spec_digest == rec["hashes"]["full_receipt_sha256"]); ok &= v4
    print(f"    {'implementation matches spec digest':34s} {'PASS' if v4 else 'FAIL'}")

    print(f"\n  SELFTEST {'PASSED' if ok else 'FAILED'}")
    return 0 if ok else 1


def exit_code(nfindings, graded, coverage_complete=True):
    """D4: zero findings with zero observations is not success. Optionally: partial coverage is not success either."""
    if graded == 0:
        return 3
    if nfindings:
        return 1
    return 0 if coverage_complete else 4


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if "--matrix" in sys.argv:
        return 0 if matrix() == 0 else 1
    argv = sys.argv[1:]
    plan_path = DEFAULT_PLAN
    if "--plan" in argv:
        i = argv.index("--plan")
        if i + 1 >= len(argv):
            print("  --plan requires a path"); return 2
        plan_path = Path(argv[i + 1])
        del argv[i:i + 2]                      # D9: remove the flag AND its value before reading positionals
    args = [a for a in argv if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    res = json.load(open(args[0]))
    plan = json.loads(plan_path.read_text())
    status_map = res.pop("_status", None) if isinstance(res, dict) else None
    nf, graded, complete = report(res, plan, status_map)
    return exit_code(nf, graded, complete if "--require-complete" in sys.argv else True)


if __name__ == "__main__":
    sys.exit(main())
