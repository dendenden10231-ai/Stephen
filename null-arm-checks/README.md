# Checks for the gaps listed in v1.6

Prepared 1 November 2026 by Denis Vashkevich (helixcom.org) for Stephen Hope, Helix AI Innovations Inc.
Apache-2.0. Python standard library only. No model is called anywhere. Nothing here edits or copies your code.

## Why this exists

Your null-arm probe v1.6 (PR #2, branch `null-arm-probe-v1.6`) already does what an earlier draft of ours tried to add: D/G grading, the E1/E2/E3 split, FORECAST_OWN/PERM, CTRL_FACTUAL, canonical receipts, the 150-cell matrix. We dropped that draft rather than send you a copy of your own work.

What is left is the list you wrote yourself in `BASELINES_AND_SHORTCOMINGS_v1.6.md`, plus two instrument defects visible in the run. This folder addresses only those, one module per gap:

| Gap (your numbering) | What goes wrong today | Module here |
|---|---|---|
| S2.13 receipts do not authenticate; signature unimplemented | anyone can recompute a receipt, nobody can tell who issued it | `signing.py`: Ed25519 (RFC 8032), pure stdlib, signs the receipt digest |
| S2.10 F_unrelated scored permissively | REFUTED on an unrelated passage is counted as fine or as wrong without a rule | `arm_check.expected_on_unrelated`: says when REFUTED is admissible and when only NEI is |
| S2.11 claim-source bias; spoiled set never run live | every claim comes from the same passages that grade it; no claim with a known wrong answer | `mutation_set.py`: claims whose correct label is known by construction, each confirmed by an oracle before use |
| defect: "11.7 → 11.70 tested nothing" | the distorted arm was the same number written differently | `arm_check.check_distorted` → INVALID, MATCH |
| defect: years doubled (2022 → 4044) | the distorted arm left the plausible range, so it tests nothing either | `arm_check.check_distorted` → INVALID |
| (not in your list) verdict vs. the judge's own bearings | a SUPPORTED whose per-evidence reasoning argues REFUTED is invisible to arm-level grading | `bearing_consistency.py` |

Supporting pieces: `number_check.py` (deterministic number/unit/scale/date comparison), `quote_check.py` (exact vs altered quotation), `labels.py` (one label vocabulary for both judges), `stability.py` (repeated runs, both definitions of "the permuted arm changed the label").

## Run

```
python3 test_checks.py            # 12 tests, also under pytest
python3 -c "import arm_check as a; print(a.check_distorted('11.70 million','11.7 million'))"
```

Measured on 31 October 2026:

```
check_distorted('11.70 million', '11.7 million')  INVALID  MATCH           (your defect 1)
check_distorted('in 4044', 'in 2022')             INVALID  NOT_IN_PASSAGE  (your defect 2)
check_distorted('in 2021', 'in 2022')             VALID    DATE_SHIFT -1
mutation set from your passages (no second refinery): 49 built, 45 kept, 4 dropped by the oracle
```

`mutation_items_no_second_refinery.json` is that set. It is ready to send to any judge; we have not run it against yours or ours. That run costs money on our side and is the owner's decision each time.

## Limits, stated plainly

- The oracles read English numbers, units and dates with regular expressions. They do not read meaning. A claim that is wrong in words but right in numbers passes them.
- `mutation_set` makes REFUTED items by changing one number, year, unit or quotation. It measures whether a judge notices a precise change, not whether it reasons well.
- `signing.py` is a reference implementation: correct against RFC 8032 test vector 1, not constant-time. Use a vetted library (PyNaCl, cryptography) for keys that matter; the signature format is the same.
- HELIX still publishes no endpoint version, so `model.version_or_hash` stays null on our side. A signature proves who issued a receipt, not which model produced it.

Details and the exact rules: `SPEC.md`.

## Update, 1 November 2026

The folder was renamed from `gift-2026-11-01/` to `null-arm-checks/` (and `test_gift.py` to `test_checks.py`). Content is unchanged.

Everything above was re-run on 1 November 2026 before this note, with the same commands:

```
python3 test_checks.py                                  12/12 passed
check_distorted('11.70 million', '11.7 million')        INVALID  MATCH
check_distorted('in 4044', 'in 2022')                   INVALID  NOT_IN_PASSAGE
check_distorted('in 2021', 'in 2022')                   VALID    DATE_SHIFT -1
mutation_items_no_second_refinery.json                  49 records: 45 kept, 4 carry a dropped_reason
```

One clarification about the set: the file holds all 49 records. Four of them have a `dropped_reason` (the oracle could not see the mutation against the passage) and are not part of the 45 to send to a judge; filter on the absence of that field.

Still not done: the 45 claims have not been run against either judge.
