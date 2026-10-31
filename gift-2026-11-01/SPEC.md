# Specification

Version 1, 1 November 2026. Denis Vashkevich (helixcom.org). Apache-2.0.
Scope: the gaps S2.10, S2.11 and S2.13 of `BASELINES_AND_SHORTCOMINGS_v1.6.md` (Stephen Hope, null-arm probe v1.6) and the two instrument defects seen in its live run. Everything else in v1.6 is left as it is.

## 1. Labels (`labels.py`)

One vocabulary for both judges, so results can be compared without translation:

```
SUPPORTED        ← SUP, OK, EXACT_MATCH, SUPPORTED
REFUTED          ← CONTRADICTED, REFUTED
NOT_ENOUGH_INFO  ← UNSUPPORTED_NUMBER, NEI, NOT_ENOUGH_INFO
REFUSAL          ← NO_NUMBERS, UNTESTABLE, refusal codes
```

`determinate(label)` is true for SUPPORTED and REFUTED only.

## 2. Number oracle (`number_check.py`)

`reconcile(claim, passage)` returns one finding per quantity or date in the claim:

| Finding | Rule |
|---|---|
| MATCH | same value and unit |
| ROUNDED_MATCH | claim is the passage rounded to the claim's written precision (step of the last written digit) |
| SCALE_MISMATCH | same mantissa, ratio a power of 10 (thousand/million/billion, k/m/b) |
| UNIT_MISMATCH | same value, different unit (barrels/day vs barrels/week, km vs miles, USD vs EUR) |
| VALUE_MISMATCH | same unit, value outside rounding |
| DATE_SHIFT | date differs; detail gives `claim_minus_passage_years` or `_days` |
| NOT_IN_PASSAGE | no comparable quantity in the passage |

`distortion(claim, passage)` returns the most serious finding. Scale suffixes are read only as standalone tokens (`400,000 b/d` is barrels per day, not billions).

## 3. Quotation oracle (`quote_check.py`)

`check(claim, passage)` finds quoted text in the claim and returns EXACT, ALTERED (with the changed words) or NOT_FOUND, by word-level sequence matching (threshold 0.6).

## 4. Arm validity (`arm_check.py`) — defects 1 and 2, S2.10

`check_distorted(variant, source)`: an E2 arm is VALID only if the oracles find a real distortion (SCALE, UNIT, VALUE, DATE_SHIFT or ALTERED quotation) and the variant stays comparable with the source. MATCH or ROUNDED_MATCH (11.7 → 11.70) and NOT_IN_PASSAGE (2022 → 4044, nothing left to compare) are INVALID: the arm tests nothing.

`expected_on_unrelated(claim, passage)`: on F_unrelated, REFUTED is admissible only if the passage itself carries a quantity or date of the same kind that contradicts the claim (REFUTED_ADMISSIBLE). Otherwise the only correct answer is NOT_ENOUGH_INFO (NEI_EXPECTED). This replaces "permissive" with a rule both sides can apply the same way.

## 5. Mutation set (`mutation_set.py`) — S2.11

From genuine passages, sentences carrying a number, date or quotation are rewritten deterministically:

```
identity            as written                                   SUPPORTED
paraphrase_number   400,000 → 400k, 9 → nine                     SUPPORTED
unit_swap           per day → per week, km → miles               REFUTED
scale_shift         ×1000 or ÷1000                               REFUTED
value_shift         ±25 %, measures only (not names, not days)   REFUTED
year_shift          ±1 year                                      REFUTED
quote_alteration    one word inside a quotation changed          REFUTED
```

Each item is checked by the oracles before it is kept; items the oracle cannot confirm are dropped with `dropped_reason`. The correct label is therefore known without human labelling, and the set is independent of which judge is tested.

`score(items, labels)` reports per mutation type: correct, wrong, NEI, refusal; and over-strictness, the share of SUPPORTED items (identity, paraphrase) that the judge refuted.

## 6. Bearing consistency (`bearing_consistency.py`)

For judges that expose per-evidence bearings. `check(output, fields)`:

| Status | Meaning |
|---|---|
| CONSISTENT | verdict follows from the bearings |
| LABEL_WITHOUT_BEARING | determinate verdict, no bearing supports it |
| BEARING_CONTRADICTS_LABEL | the judge's own bearings argue the opposite |
| CONFLICT_NOT_RECORDED | supporting and refuting bearings both present, verdict ignores the conflict |
| REFUSAL_WITH_BEARINGS | refusal although bearings are determinate |
| NO_BEARINGS_EXPOSED | nothing to check |

## 7. Stability (`stability.py`)

`cells(runs)` groups repeated runs per claim × arm. `pairs(run)` reports both definitions of "G changed the label": by content (any change) and determinate-A (only where A was SUPPORTED/REFUTED), plus credulity (G accepted wrong evidence) and wrong direction.

## 8. Signature (`signing.py`) — S2.13

Ed25519 per RFC 8032 over the receipt digest (the hex SHA-256 of the canonical receipt, as v1.6 already computes). Block added to a receipt:

```json
{"alg": "Ed25519", "signed": "receipt digest", "public_key": "<hex>", "value": "<hex>"}
```

`check_block(block, digest_hex)` verifies. Either side signs with its own key; nobody needs the other's code. Reference implementation, not constant-time; for real keys sign with a vetted library, same format.

## 9. What this does not claim

No model was called. Nothing here has been run against either judge. The oracles are lexical. Numbers in README are from `python3 test_gift.py` and the commands shown there, 31 October 2026.
