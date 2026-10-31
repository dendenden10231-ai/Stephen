# Your null-arm probe design, applied to your own topic

**File 2 of 2.** Topic: "No second refinery" (12 September 2026), the sourcing section at the end of the article.
Design followed: your issue #1, "Null-Arm Probe Design — HELIX Judge Stage".

## Status: **run.** Results are in [`RESULTS_en.md`](RESULTS_en.md)

Three full runs of 63 judge calls each, live search disabled (0 search calls), about $1.9 per run by the product's spend counter (an estimate from tokens at list price, not a bill). Labels per claim and arm for all three runs: [`matrix_all_runs.csv`](matrix_all_runs.csv).

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
| Judge: fixed-evidence mode, search disabled, refusal contract R1–R5 | run on the product's server; the harness is in our private repository |
| Paid run of the judge | **done, three runs** |

## Why arm E is only 3 of 12

Your design asks for "a genuine passage that refutes the claim". We did not invent any. For the others we could not find a real one, for different reasons:

- **c01** (East Coast stocks 19.3 mb), **c10** (diesel is made from crude): the claim is true. EIA confirms c01. There is nothing genuine to refute it with.
- **c03, c04, c08, c11, c12** are the deliberately spoiled claims (wrong unit, year, citation, quote, inference). Arm A already contains the passage that refutes the spoiled claim, so A is expected to be REFUTED and an "opposite direction" for E would need a passage that *supports* the spoiled claim. None exists.
- **c07** (forecast presented as fact): the one candidate we found was a fleet-software vendor's marketing blog dated three months before the events. We rejected it as evidence.
- **c09** (superseded figure): the superseding figure is already in A.

Our finding: for the spoiled-claim types a genuine E that points the opposite way does not seem to exist. Is that true? If not, how would you build E for them so that it stays genuine and still moves the label in the opposite direction?

## Permutation direction

Your text and your JSON plan differ on which neighbour's evidence a claim receives. We followed the JSON: claim *i* gets the arm-A evidence of claim *i+1*, cyclic.

## How to read the results

Per your grading section the results report sensitivity (E differs from A) and specificity (C does not equal A) **together**, the count and identity of failures (not an interval, twelve is twelve), and the R1–R5 diff for the four refusal-expected claims c02, c07, c08, c11. Limits you already state apply: this tests dependence on evidence, not truth, and it bypasses retrieval, so it says nothing about whether live search finds the right sources. File 1 is where that is visible.
