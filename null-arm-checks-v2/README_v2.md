# Arm set v2 — for your review

Prepared 1 November 2026 by Denis Vashkevich (helixcom.org). Apache-2.0. Standard library only. **No model was called to produce or test anything in this folder, and no judge has been run on it.**

Your frozen v1 (`arm-set-2026-11-01/`) is untouched. This folder is a proposal, built in response to the review we posted on PR #3. **Nothing here is final until you agree.** If you disagree with a point, change the file and say why; we will re-freeze together.

## What changed, point by point (numbers recomputed 1 November 2026)

| # | Finding on v1 | What v2 does | How it is checked (`python3 test_v2.py`) |
|---|---|---|---|
| 1 | G got A's own evidence in 24 of 45 arms | `G_deranged`: another claim's sentence, different text AND different passage, cyclic scan | 0 of 48 collisions; test asserts it |
| 2 | F had no passage guard | `F_unrelated`: candidate must come from another passage | 0 same-passage cases; asserted |
| 3 | Manifest allowed REFUTED on all F arms | REFUTED is acceptable only where `expected_on_unrelated` says `REFUTED_ADMISSIBLE` (S2.10): 36 of 96 F/G arms. A candidate that matches a quantity of the claim is rejected | asserted per arm against the oracle |
| 4 | C had `"source": ""` | `C_noise_length` keeps A's source; new `C_num_noise` keeps the source and places the claim's own numbers/dates/units in meaningless surroundings | source equal to A; length within ±5 %; numbers present |
| 5 | No D arm | `D_noise_topic` restored: 33 of 48 claims, from your `topic_noise` strings of the 12-claim run, oracle-checked for no comparable quantity (15 claims have no usable string) | asserted |
| 6 | A_genuine was two things | every A arm carries `subclass`: `A_supported` (21, one is the prose anchor) or `A2_distorted_claim` (27); the scorer reports them separately; new `E_restore` (27) gives the distorted claim matching evidence and expects SUPPORTED | scorer, test_v2 |
| 7 | Negative block penalised only SUPPORTED | `FDR_neg` counts any determinate label that is not acceptable: SUPPORTED (credulity) and REFUTED (a refutation from nothing) separately | selftest |
| 8 | Our label map lacked `NEEDS_RECOVERY` | mapped to NOT_ENOUGH_INFO (switch `--needs-recovery refusal` for the sensitivity run); `SCOPE_EXCLUDED` → REFUSAL | tested |
| 9 | Our oracle missed 4 records | it now sees all four: "back to 1989", "(2023)→(2025)", "H1 2025", and "4M+ barrels per week → b/d" (the scale was followed by "+", which swallowed the unit). Also added: units `m3`, `t/d`, `$/gal`, `$/bbl`, `percentage points`; a price with and without its denominator is treated as the same unit | tested |
| 10 | Generation artefacts | "Phillips 82", "12–11 September", "mthree", "the main reasons" are gone: E now uses the validated mutation functions of `mutation_set.py` (names such as Phillips 66 are never shifted); the paraphrase pattern no longer turns `m3` into `mthree`; the quote swap is grammatical | asserted absent |
| 11 | Our `stability.py` counted a missing G cell as a changed label | fixed | tested |

## What the rebuilt set contains

48 claims from the same 12 passages (v1: 45 kept of 49; the oracle fix keeps all 48 candidates, none dropped; the single `paraphrase_number` item of v1 was the `mthree` artefact, so that class is now empty and over-strictness on paraphrases is not measured by this set). 361 arms: A 48, B 48, C 48, C_num 48, D 33, E_contradicting 13, E_restore 27, F 48, G 48. The anchor `c10.s0.identity` (prose without a number) is flagged and excluded from accuracy.

## Free baselines on v2 (`python3 scoring_v2.py --baselines`)

| baseline | Acc(A) | FDR_neg | J_gate |
|---|---|---|---|
| always SUPPORTED | 0.4255 | 1.0000 | −0.5745 |
| always REFUTED | 0.5745 | 0.8652 | −0.4255 |
| always NOT_ENOUGH_INFO / REFUSAL | 0.0000 | 0.0000 | 0.0000 |
| string similarity (your diff-engine rule) | 0.5319 | 0.0000 | 0.5319 |
| lexical oracle only | 0.9787 | 0.1199 | 0.7240 |

`J_gate = Acc(A) − FDR_strict`. Every constant judge scores ≤ 0; a perfect judge scores 1. On the deranged G the string-similarity baseline has 0 false SUPPORTED, so the earlier 47.7 % was the collision.

## Things we did not fix and want you to look at

1. **Circularity.** The set was built with the same lexical oracles that now score the baseline, so the oracle-only row (0.72) is partly self-agreement. It is a ceiling for what a lexical reader can do here, not a measure of correctness.
2. **E is still 13.** We expected the validated mutation functions to raise it to 21; they do not: eight identity sentences have no number or quotation to distort (7 besides the anchor). The small-n problem for E is therefore mostly the corpus, not the old generator.
3. **One domain, one author, 12 passages.** Unchanged. Claims from one passage are not independent; intervals should be computed by passage, not by claim.
4. **`E_restore` evidence equals the claim text.** It is a control for answering from memory, not a reading test.
5. **The 12 passages were reconstructed** from the evidence sentences of the shipped items (`passages_reconstructed.json`); rebuilding v1 from them with the original v1 code reproduces your 49 items exactly (checked).
6. **Not done:** polarity/negation checks, M_haystack (several evidence items), injected instructions, a second domain, the refusal class. They are in our research plan and need your view on scope first.
7. **The judge changed after your three runs** (forecasts/opinions are now stopped by code before the model). Any run on v2 is a run on the current judge; v1 results describe the earlier one.

## How to review and change it

```
git checkout v2-checks && cd null-arm-checks-v2
python3 test_v2.py            # 12 invariant tests
python3 test_checks.py        # the 12 original tests
python3 scoring_v2.py --selftest
python3 scoring_v2.py --baselines
python3 build_arms_v2.py      # regenerates arms_v2.json and ARM_MANIFEST_v2.json (deterministic)
```
Rules live in `build_arms_v2.py` (construction), `ARM_MANIFEST_v2.json` (expected and acceptable labels) and `scoring_v2.py` (scoring). You can comment on any line of the PR, push a commit to this branch, or tell us what you would do differently. `FREEZE_v2.txt` carries the SHA-256 of every file; it will be rewritten only after we agree.

Nothing has been run on a paid judge. We propose to run nothing until you have looked at this.
