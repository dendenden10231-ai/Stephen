# Null-Arm Probe v1.6

A test of whether a judge's verdict depends on the evidence supplied to it, rather than on something that correlates
with evidence.

Built for HELIX's judge stage, run against your live endpoint (`helixcom.org/api/check`). **Result: the judge came out
clean on every case we could construct. Every defect we found was in our own instrument.**

Stephen Hope, Helix AI Innovations Inc. · Apache-2.0

---

## The finding, first

Twelve numeric claims from our own article, six arms, **72 judge calls, 14 seconds, $0**:

```
A_genuine      SUPPORTED  12/12     baseline clean
E2_distorted   REFUTED    11/12     the 12th is entailment, correctly
C_noise        NEI        12/12     specificity perfect
E1_contrary    REFUTED    10/12
```

Probed separately, all correct:

```
inequality   "below 200m" vs source "below 100m"  -> OK                  100m IS below 200m
             "below 50m"  vs source "below 100m"  -> UNSUPPORTED_NUMBER  bound false
date         "since 1982" vs source "since 1983"  -> OK                  weaker claim, entailed
             "since 1990" vs source "since 1983"  -> CONTRADICTED         stronger claim
forecast     forecast, no figure                  -> NO_NUMBERS          refused
             forecast + a neighbour's evidence    -> NO_NUMBERS          no contamination
             factual twin, identical evidence     -> OK                  the control HOLDS
fabrication  figure absent from the cited source  -> CONTRADICTED
misquotation no figures to bind                   -> NO_NUMBERS
superseded   old number against a newer source    -> CONTRADICTED
concurrency  12 parallel calls                    -> 12/12, 0.2 s
transport    dead endpoint                        -> HTTP 404, surfaced as ERROR not a refusal
```

**The forecast scope limit holds.** `NO_NUMBERS` on the forecast's own evidence *and* under a neighbour's, with the
factual twin binding on identical text — so the result is attributable to claim type, not to weak evidence.

**The judge evaluates figures inside forecasts when they are present**, and does it correctly: "stays below 400,000"
against evidence giving exactly 400,000 returns `CONTRADICTED`. It did not affirm a forecast to be agreeable.

## Two corrections we owe you

**1. An empty source never reaches your judge.** It returns `HTTP 422` at the request validator:

```
empty source  -> 422  {"msg": "Value error, empty field", "loc": ["body","source"]}
```

So our earlier "12 of 12, no verdict on an empty source" was measuring your request validation, not the judge's
refusal behaviour. Correctly specified — a source present but carrying nothing to reconcile — the judge refuses
cleanly: `UNSUPPORTED_NUMBER / NEEDS_RECOVERY`, 12 of 12. The behaviour is right; our arm measured the wrong layer.

**2. We retracted our own headline finding.** We first reported that years were not reconciled. That was wrong: we had
distorted years by doubling them (`2022 → 4044`), and a judge returning `NEI` to an absurd figure is being reasonable.
With a realistic one-year shift, 3 of 3 are caught. The finding described our distortion.

## What is not tested

**Live retrieval.** `api/check` takes evidence as input and never searches, so no arm here can test whether your search
finds the right sources. That needs the hosted battery endpoint, which is not deployed. It is the one gap we cannot
close from our side, and we would rather say so than imply coverage we do not have.

Also untested: `NEI` under genuinely ambiguous evidence, which is where a real disagreement would most likely live.

## The instrument's own defects

Four survived every reading of the code and were found only by running it:

| defect | consequence |
|---|---|
| years distorted by doubling | produced the false finding above |
| `11.7 million → 11.70 million` | numerically identical; the arm tested nothing |
| inequality claims tested as equalities | `"below 200m"` correctly matches a 100m source |
| `2e+08 million` — unit double-counted | returned the *expected* verdict for the wrong reason |

**The rule it earns:** an arm that produces the expected verdict for the wrong reason is worse than one that fails,
because it is indistinguishable from success. Every distortion, bound and unit needs a positive control proving it
changed what it claims to change.

Review history: four independent review rounds found 7, 6, 6 and 6 defects in successive versions — each of a class
the previous round's testing could not see. v1.6 is **not validated**, and there is no basis for believing a fifth
round would find none.

## Files

| file | what |
|---|---|
| `judge_probe_v1.6.json` | the plan: arms, claims, grading rules, refusal contract |
| `grade_judge_probe_v1p6.py` | deterministic grader, receipt builder/verifier, selftest, 150-cell truth table |
| `helix_judge_probe.py` | the live harness: claim extraction, arm construction, receipts |
| `final_completeness.py` | closes the untested list: `E3`, fabrication, misquotation, superseded, transport, concurrency |
| `claims.json` | the 12 claims, bundled so the live run reproduces without our article |
| `results/live_run.json` | the 72 calls, with receipts — all 72 hashes verify |
| `RECEIPT.md` | the shared receipt format |
| `BASELINES_AND_SHORTCOMINGS_v1.6.md` | all fourteen known shortcomings, stated plainly |

## Run it

```bash
python3 grade_judge_probe_v1p6.py --selftest     # 8 named regressions, receipt checks, 150 cells
python3 grade_judge_probe_v1p6.py --matrix       # truth table, every cell against the spec
python3 final_completeness.py                    # the untested-list pass, 8 checks
python3 helix_judge_probe.py --claims 12         # re-run the live probe (72 calls, ~15 s)
```

No dependencies beyond the standard library. Everything above was run from an extracted copy in a clean directory
before this was sent.
