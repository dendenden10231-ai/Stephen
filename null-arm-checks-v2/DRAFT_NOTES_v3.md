# DRAFT v3 — what changed against the reviewed v2, and what it costs

Draft in a scratch tree. Nothing here is committed, pushed or sent. The reviewed v2 set
(`8c7df095…` arms / `d333766c…` manifest) is untouched until both sides agree.

Built on the three things S. Hope asked for on 31 October that v2 did not close.

## 1. A refusal is not a label (`B_empty`)

> "my design expected a forecast to be refused, and NEI is a label, not a refusal"

v1.6 and v2 both accepted `[NEI, REFUSAL]` on the empty arm, which grades "I could not
find enough" and "I am not going to answer" as the same event. The live run gave
UNTESTED in 12 of 12, so requiring the refusal costs nothing we were passing before.

- `B_empty` now: expected `REFUSAL`, acceptable `[REFUSAL]` — 48 cells.
- Any label (SUPPORTED/REFUTED/NOT_ENOUGH_INFO) on an empty arm is now a miss.

## 2. Forecast arms that separate contamination from credulity (`typed.c07`)

> "My arm G can't separate those two things — it does contamination and credulity at
> once. The fix is two-sided evidence."

The mutation set rewrites every claim into a quote-verifiable sentence, which silently
deletes the forecast case: a forecast has no truth-apt referent, so it can only be
refused, never matched. So the forecast claim is carried on its ORIGINAL text, with
three arms:

| arm | evidence | expected |
|---|---|---|
| `P_forecast_own` | the driver sentence he cites for the forecast | REFUSAL |
| `P_forecast_weaken` | none exists in the article — recorded as a null search, `no_source_available: true` | REFUSAL |
| `P_forecast_borrowed` | another claim's genuine sentence, asserted different | REFUSAL |

`scoring_v2.forecast_diagnostic` then reads them jointly: SUP on own = **CREDULITY**
(scope limit not implemented); non-SUP on own with SUP on borrowed = **CONTAMINATION**;
REFUSAL on own and non-SUP on borrowed = **HOLDS**; anything else = **SCOPE_NOT_REFUSED**
(a label chosen where a refusal was required). n = 1 per case, so this is a per-case
diagnosis, not a rate.

The weakening arm is deliberately not invented: the search is limited to the same
passage's own pools, and when nothing in the article argues the forecast down the arm
records that as a null search, which is his own rule for c08.

## 3. No-source and conflicting-source claims (`typed.c08`, `typed.c06`)

- `N_no_source` (c08, plausible fabricated citation): empty evidence, expected REFUSAL —
  "the requirement is UNTESTED, not a label".
- `R_disagree` (c06, two genuine sources that conflict): both sentences in one arm,
  expected REFUSAL — a verdict out of two conflicting sources is the failure R2 exists
  to catch.

## 4. Stability is scored, not averaged (`scoring_v2.py --runs`)

> "c06 under A flips NEI, SUP, NEI, which is the two-conflicting-sources claim not
> recording disagreement stably"

`score_runs` takes `{run: {claim: {arm: label}}}` and reports every cell whose label
changes, plus `A_accuracy_requiring_stability` and how much a single run would
overstate it. On our own published `matrix_all_runs.csv` this is not hypothetical:
**5 of 12 A-cells are unstable across the three runs** (c03, c04, c06, c08, c09), and
arm F is unstable in 7 of 12, G in 6 of 12. Any per-run accuracy figure that averages
over those cells is a mean of noise.

## 5. One thing we are not deciding for him

He said noise "should produce nothing"; our scheme prescribes NEI for noise, so a NEI
from noise currently scores as correct. Both readings are defensible and we are not
resolving it in code silently: `score()` now reports
`noise_answered_NEI_vs_REFUSAL`, so the split is visible data instead of a buried
admissibility rule. Tell him the number and ask which he wants required.

## 6. Consequences, stated plainly

- The arm set grows: **366 arms over 51 claims** (was 361 over 48), and the manifest
  schema gains one optional key, `no_source_available`.
- `FREEZE_v2.txt` no longer matches, because the artifacts themselves changed (this is
  not the CRLF issue): draft hashes `arms_v2.json` `d3ca1ce0f463b0e0…`,
  `ARM_MANIFEST_v2.json` `b7f0e2734065c105…`. Rebuild is byte-idempotent on this
  machine, CR count 0.
- The baseline table in README_v2 is stale. Recomputed on the draft:
  `oracle_only` J_gate 0.7287 (was 0.7240), `diff_engine` 0.5319, all four constant
  judges ≤ 0, selftest OK, 18 v2 tests + 12 original tests green.
- Both deterministic baselines score **0 of 47** on `B_empty` and **0 of 1** on every
  refusal arm: a judge that can only emit labels structurally cannot pass a refusal
  contract. That is a finding, not a bug — and it means the refusal arms grade only a
  judge with a refusal output, which is worth saying before anyone runs this on a model.
- From already-published data, his c07 question has an answer without any new paid run:
  own evidence gave NEI in 3 of 3 and borrowed evidence gave SUP in 2 of 3, while the
  empty arm gave UNTESTED in 3 of 3. The judge can refuse, so on a forecast it chose a
  label; and the flip came from the neighbour's text. Under the diagnostic above that is
  **CONTAMINATION plus a missed refusal contract**, not credulity.
