# Your null-arm probe design, applied to your own topic

**File 2 of 2.** Topic: "No second refinery" (12 September 2026), the sourcing section at the end of the article.
Design followed: your issue #1, "Null-Arm Probe Design — HELIX Judge Stage".

## Status: built, **not yet run**

Nothing in this folder is a result. We say so plainly so that nobody reads the claim set as one.

| Item | State |
|---|---|
| 12 claims, one per type c01–c12, texts taken from your sourcing section | done, [`claims.json`](claims.json) |
| Arm A (genuine evidence) | 12 of 12, your own sourcing lines |
| Arm B (empty) | 12 of 12, mechanical |
| Arm C (length-matched noise, ±5%, same source, no digits) | 12 of 12, mechanical |
| Arm D (same subject, no bearing on the claim) | 12 of 12, other sentences of your article |
| Arm F (genuine passage about another claim) | 12 of 12, other lines of your sourcing |
| Arm G (claim *i* gets the evidence of claim *i+1*, cyclic) | 12 of 12, mechanical |
| Arm E (a genuine passage that refutes the claim) | **3 of 12**: c02, c05, c06 |
| Judge harness: fixed-evidence mode, search disabled, refusal contract R1–R5 | done; 16 tests with stub judges, no network |
| Export in the input format of your `grade_judge_probe.py` | done |
| **Paid run of the judge** | **not run** |

Estimated size of the full run: about 64 judge calls, about 99k input tokens. At list price that is on the order of **$7**, and up to about $11 if the model's replies are long or need retries. If only your first-choice arm is run (G, plus A as the reference), it is 24 calls, on the order of **$3**.

## Why arm E is only 3 of 12

Your design asks for "a genuine passage that refutes the claim". We did not invent any. For the others we could not find a real one, for different reasons:

- **c01** (East Coast stocks 19.3 mb), **c10** (diesel is made from crude): the claim is true. EIA confirms c01. There is nothing genuine to refute it with.
- **c03, c04, c08, c11, c12** are the deliberately spoiled claims (wrong unit, year, citation, quote, inference). Arm A already contains the passage that refutes the spoiled claim, so A is expected to be REFUTED and an "opposite direction" for E would need a passage that *supports* the spoiled claim. None exists.
- **c07** (forecast presented as fact): the one candidate we found was a fleet-software vendor's marketing blog dated three months before the events. We rejected it as evidence.
- **c09** (superseded figure): the superseding figure is already in A.

We would be grateful for your advice here. For the spoiled-claim types, how would you build E so that it stays genuine and still moves the label in the opposite direction? You know this design far better than we do, and we would rather follow your answer than guess.

## Permutation direction

Your text and your JSON plan differ on which neighbour's evidence a claim receives. We followed the JSON: claim *i* gets the arm-A evidence of claim *i+1*, cyclic.

## What will be reported when it runs

Per your grading section: PASS / FAIL by mode for each claim and arm, sensitivity (E differs from A) and specificity (C does not equal A) **together**, the count and identity of failures (not an interval, twelve is twelve), and the R1–R5 diff for the four refusal-expected claims c02, c07, c08, c11.

Limits you already state apply: this tests dependence on evidence, not truth, and it bypasses retrieval, so it says nothing about whether live search finds the right sources. File 1 is where that is visible.
