# Arm set v2.1 (DRAFT) — fixes after the review of 07 Nov 2026

v2 is **not changed** (`null-arm-checks-v2/`, frozen). v2.1 is a separate folder; `arms_v2.json` and `mutation_items_v2.json` here are
byte-identical reference copies of the v2 files, used only for the comparison tests. Not a joint freeze until the other party agrees.

Review by Stephen Hope (PR #4, comment 6706907873): all four defects we listed reproduced; he grouped them into three root causes. This
folder fixes those three and records the effect, in numbers, on the v2 material.

## What was fixed

| # | Defect (v2) | Root cause | v2.1 | Test |
|---|---|---|---|---|
| 1 | `$5.85/gal` vs `€5.85/gal` read as MATCH | the extractor decides WHAT is compared; behind a measure suffix the currency symbol was dropped from the unit | `number_check.py`: the symbol is part of the unit also with a suffix ("USD per gallon"); £ added; `$5.85` vs `$5.85/gal` still agree, `/gal` vs `/bbl` still do not | `test_v2_1_fixes.py` |
| 4 | `10–11 September` vs `12–13 September` read as VALUE_MISMATCH | same root cause: a day range with a month and no year never became a date | `number_check.py`: `_DATE_DM` / `_DATE_MD`, compared by month and day (capitalised month names only, so "5 may be" is not a date) | `test_v2_1_fixes.py` |
| 2 | `stability.cells`: a missing answer counted as a flip | a reporting defect about absence; FREEZE_v2 already ruled that a missing answer is not a label change, but only `pairs` was fixed | `stability.py`: `missing_answers` apart, instability judged over answered runs, comparable cells need ≥ 2 answers; `UNTESTED` counts as no answer | `test_v2_1_fixes.py`, `test_checks_v2_1.py` |
| 2b | `UNTESTED` rows sat inside the denominators of our own rates | `labels.py` mapped `UNTESTED` to `REFUSAL` | `UNTESTED` is its own label; `scoring_v2.score` reports it apart and gives every rate over judged rows too (`judged_denominators`) | `test_v2_1_fixes.py` |
| 3 | `_MEASURE_AFTER` lacked the corpus's own words, and the loss left no trace | vocabulary gap plus no audit trail | `mutation_set.py`: `m3`, `m³`, tanks, workers, refineries added; every candidate leaves a trace (`status`/`reason` on items, `exclusions_v2_1.json` for candidates with no variant) | `test_v2_1_fixes.py` |

## What the fixes did to the v2 material (measured, not estimated)

- **Mutation items:** all 48 v2 items are still kept under the v2.1 oracles; **1** new item appears (`c06.s0.value_shift`). The loss v2 could not
  count is now counted: of 98 candidates that yielded no variant, 86 are "mutation not applicable", 7 "no number", **3 "number without a recognised
  measure"** (1 of them recovered by the widened vocabulary) and 2 "only years / days of month / unchanged by rounding". `exclusions_v2_1.json` lists them all.
- **Arms:** 511 (v2) → 523 (v2.1). 14 arms are new (12 for the new item, 2 more for `c06.s0.identity`), 2 v2 arms are gone
  (`c09.s1.identity` / `c09.s1.value_shift` in H_high_overlap), 27 common arms changed their evidence (C_num_noise 7, F_unrelated 9, M_diluted 7, H_high_overlap 4).
- **Oracle reading of the 511 frozen v2 arms:** 21 arms change their `distortion()` verdict under v2.1: H_high_overlap 5 (NOT_IN_PASSAGE → DATE_SHIFT),
  S_same_document 4 and G_deranged 3 and M_diluted 1 (VALUE_MISMATCH → DATE_SHIFT: the wrong object compared), F_unrelated 5, and **3 C_num_noise arms
  that v2 read as MATCH become NOT_IN_PASSAGE: those v2 noise arms did not carry the claim's date range as a date**. Unrelated evidence (F, G, H) that
  shares a month and day with the claim now reads as DATE_SHIFT or MATCH, so the generator re-selects it; that is why those arms changed.
- **Currency:** no effect on the frozen set (`€` and `£` occur 0 times, `$` 503 times).

## Not changed on purpose
v2 files; the 511 frozen arms; the scoring definitions other than the added `UNTESTED` block and `judged_denominators`.

## Run
```
python3 build_items_v2_1.py          # items + exclusion log (deterministic)   [--check to verify]
python3 build_arms_v2_1.py           # arms_v2_1.json, ARM_MANIFEST_v2_1.json
python3 freeze_v2_1.py               # LABEL_MAP_v2_1.json, FREEZE_v2_1.txt
python3 verify_all_v2_1.py           # one command, exit code is the verdict
```
Standard library only. Environment line in `FREEZE_v2_1.txt` records the machine the freeze was written on.
