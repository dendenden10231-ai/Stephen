# Your null-arm probe design, run on our judge: results

**File 2 of 2, now with results.** All labels of all three runs: [`matrix_all_runs.csv`](matrix_all_runs.csv). Topic: your article "No second refinery". Design: your issue #1, "Null-Arm Probe Design — HELIX Judge Stage".
Setup: your 12 claim types, seven arms (A genuine, B empty, C length-matched noise, D same-subject noise, E contradicting, F unrelated, G permuted),
the judge called with supplied evidence and live search disabled (the harness raises if search is ever called; 0 search calls in every run).
Judge: Gemini on the server key. Three full runs of 63 judge calls each, about $1.9 per run by the product's spend counter (an estimate from tokens at list price, not a bill).

Labels: SUP supported · REF refuted · NEI not enough information · UNT untested (refusal) · n/a no arm built.
Arm E exists for c02, c05, c06 only: for the other claims we could not find a genuine refuting passage and did not invent one (see README).

## Final run

| | A | B | C | D | E | F | G |
|---|---|---|---|---|---|---|---|
| c01 | SUP | UNT | UNT | NEI | n/a | NEI | UNT |
| c02 | SUP | UNT | UNT | NEI | REF | UNT | NEI |
| c03 | REF | UNT | UNT | NEI | n/a | UNT | NEI |
| c04 | REF | UNT | UNT | NEI | n/a | UNT | NEI |
| c05 | SUP | UNT | UNT | NEI | REF | NEI | UNT |
| c06 | NEI | UNT | UNT | NEI | REF | NEI | NEI |
| c07 | NEI | UNT | UNT | NEI | n/a | NEI | **SUP** |
| c08 | NEI | UNT | UNT | NEI | n/a | NEI | NEI |
| c09 | NEI | UNT | UNT | NEI | n/a | UNT | NEI |
| c10 | SUP | UNT | UNT | NEI | n/a | UNT | NEI |
| c11 | REF | UNT | UNT | NEI | n/a | UNT | NEI |
| c12 | REF | UNT | UNT | NEI | n/a | NEI | NEI |

## What we found

1. **Mode 1, content-blind.** Not observed. Where A carries a determinate label (c01, c02, c03, c04, c05, c10, c11, c12), swapping in a neighbour's evidence (G) changed the label in 8 of 8.
2. **Mode 2, length-sensitive.** Not observed. Length-matched noise (C) returned a refusal in 12 of 12, never the genuine label.
3. **Mode 3, no contradiction.** Not observed. Where E exists (3 claims), the label moved to REF in 3 of 3.
4. **Refusal contract.** The empty arm gave UNTESTED in 12 of 12; R1 to R5 hold in 12 of 12. Cells that errored: 0 of 75.
5. **Sensitivity and specificity, reported together.** Sensitivity (E differs from A, where E exists): 3/3. Specificity (C does not equal A): 12/12. These are about dependence on the evidence, not about truth.

On the claim types (arm A): the true and trivial claims came back SUP; the wrong unit (c03), the year shifted by one (c04), the misquote (c11) and the right quote with a wrong inference (c12) came back REF;
two genuine sources in conflict (c06) were recorded as NEI, not averaged; the forecast (c07), the fabricated citation (c08) and the superseded figure (c09) were not silently labelled.

## The one place we would like your view

**c07, arm G.** The forecast claim ("the global refined-product deficit will not close when the Gulf war ends") received **SUPPORTED** on the evidence of the neighbouring claim (nine damaged Gulf refineries).
The topic is the same, the forecast does not follow from those facts. Your design expects c07 to be refused, not labelled. This is the only case of 12 where a permuted arm produced a determinate label different from A, and it recurred in two of the three runs (the first run gave NEI). Is our reading right that this is a real weakness of the judge on forecasts, and not an artefact of how the neighbour's evidence was chosen?

## What the probe found in our own code

Three defects, all fixed and deployed, each with a test:
- Supplied facts lacked the field the number check reads, so the first paid run crashed on the first conclusion that quoted a number.
- The number check looked for dates literally, so a conclusion written in Russian ("4 сентября 2026") was dropped against English evidence ("4 September 2026"): a false refusal on c04 and c09.
- The month table lacked "March", and number formats such as "400 000" against "400k", or "9" against "nine", were not matched: false refusals on c03 and c08.

Run to run the labels are not identical (the model is not deterministic): across three runs, c03, c04, c06, c08 and c09 changed in arm A. Twelve claims are twelve, and one run per configuration is one run.

Thank you for the design. It found things in our judge that our own tests had missed.
