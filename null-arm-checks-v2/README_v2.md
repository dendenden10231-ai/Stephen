# Arm set v2 — draft for your review, regenerated 1 November 2026

Prepared 1 November 2026 by Denis Vashkevich (helixcom.org). Apache-2.0. Standard library only.
**No model was called to produce or test anything in this folder, and no judge has been run on it.**

Your frozen v1 (`arm-set-2026-11-01/`) is untouched. This folder is a proposal built on your review of PR #3
and on our audit of PR #4. Nothing here is final until you agree. If you disagree with a point, change the file
and say why; we re-freeze by running `python3 freeze_v2.py`, which rewrites `FREEZE_v2.txt` and
`LABEL_MAP_v2.json` from the files as they actually are — so the freeze cannot drift from the artifacts.

## What changed against v1, point by point (numbers recomputed 1 November 2026)

| # | Finding on v1 | What v2 does | How it is checked (`python3 test_v2.py`) |
|---|---|---|---|
| 1 | G received A's own evidence in 24 of 45 arms, and its own **passage** in 33 of 45 | `G_deranged`: another claim's sentence from another passage, cyclic scan with both guards | 0 collisions of 48; asserted |
| 2 | F had no passage guard | `F_unrelated`: candidate must come from another passage | asserted per arm |
| 3 | Manifest allowed REFUTED on every F arm | REFUTED acceptable only where `arm_check.expected_on_unrelated` returns `REFUTED_ADMISSIBLE`: **36 of 96** F/G arms | asserted against the oracle |
| 4 | C arms carried `"source": ""` in 45 of 45 | `C_noise_length` keeps A's source — **48 of 48 equal**; `C_num_noise` keeps the source and puts the claim's own numbers and units in meaningless surroundings | source equality and length ±5 % asserted |
| 5 | No D arm at all | `D_noise_topic` restored: 33 of 48 claims, oracle-checked to carry no comparable quantity | asserted; the other 15 claims have no usable string |
| 6 | `A_genuine` was two different things inside one number | every A arm carries `subclass`: `A_supported` (20, excluding the prose anchor) or `A2_distorted_claim` (27), scored separately; `E_restore` (27) gives the distorted claim matching evidence and expects SUPPORTED | scorer and tests |
| 7 | Negative block penalised only SUPPORTED | `FDR_neg` counts any determinate label that is not acceptable, SUPPORTED (credulity) and REFUTED (a refutation from nothing), separately | selftest |
| 8 | Our label map lacked `NEEDS_RECOVERY` | pinned in `LABEL_MAP_v2.json`: mapped to NOT_ENOUGH_INFO, with `--needs-recovery refusal` for the sensitivity run. Measured effect: **52 refusal-only cells** move on this set, **0** on your frozen v1 — your acceptable sets already list both labels, so your scorer cannot tell a refusal from a label | `scoring_v2.py`, `r7_mapping.py` |
| 9 | Our date oracle missed four records | it now sees all four ("back to 1989", "(2023)→(2025)", "H1 2025", "4M+ barrels per week → b/d"), plus `m3`, `t/d`, `$/gal`, `$/bbl`, `percentage points`; a price with and without its denominator is one unit | tested |
| 10 | Generation artefacts ("Phillips 82", "12–11 September", "mthree") | E now uses the validated mutation functions of `mutation_set.py`; the paraphrase pattern no longer turns `m3` into `mthree`; the quote swap is grammatical | asserted absent |
| 11 | Our `stability.py` counted a missing answer as a label change | fixed, and now written into the freeze file as a rule | tested |

## What this set contains

51 claims, **511 arms**: A 48, B 48, C 48, C_num 48, D 33, E_contradicting 13, E_restore 27, F 48, G_deranged 48,
`S_same_document` 28, `H_high_overlap` 29, `M_diluted` 48, `R_pair` 40, and the typed arms
`P_forecast_own`, `P_forecast_weaken`, `P_forecast_borrowed`, `N_no_source`, `R_disagree` (one cell each).
The anchor `c10.s0.identity` (prose without a number) is flagged and excluded from accuracy in every arm, so
9 of the 511 cells are anchor cells: 502 scored cells, 368 of them negative. The single `paraphrase_number`
item of v1 turned out to be the `mthree` artefact, so that class is empty and over-strictness on paraphrases
is still not measured by this set — see item 6 of the list below.

**Construction family, as a field, not as a habit.** Every cell carries `family` (17 of them) and
`fixed_claim`. We took that from NEI-CAP (Findings of EMNLP 2026, `10.18653/2026.findings-emnlp.796`), whose
conclusion is exactly the failure we had found in ourselves: an aggregate over mixed constructions hides which
problem a score solved. Three of the families are new on our side and were built after reading their taxonomy:
`same_document_non_rationale` (their family, which v1 produced by accident in 24 of 45 G arms — here it is
designed, 28 cells), `high_overlap_insufficient` (their "BM25 near-miss", the family their verifiers failed on,
29 cells), and `diluted_support` / `conflicting_sources` (48 and 40 cells, support present but buried, and two
sources that must be recorded rather than averaged). `R_pair`'s second source is **constructed** — one article
cannot give us two publications — and is labelled `constructed_second_*` so nobody mistakes it for a citation.

**What the refusal arms do and do not show.** The manifest demands REFUSAL on **93** cells whose only acceptable
label is REFUSAL (48 empty arm, 40 conflicting pairs, 5 typed), and both deterministic baselines score
**0 of 93** on them: a judge that only labels cannot pass the refusal contract. The conflicting-pair and
forecast arms are now numerous enough to report per family, but they are still one corpus and one article, so
the interval is about these sentences, not about refusal in general.

## Free baselines on this state (`python3 scoring_v2.py --baselines`)

| baseline | Acc(A) | FDR_neg | J_gate | A_supported | A2_distorted |
|---|---|---|---|---|---|
| always SUPPORTED | 0.4255 | 1.0000 | **−0.5745** | 20/20 | 0/27 |
| always REFUTED | 0.5745 | 0.9022 | **−0.4255** | 0/20 | 27/27 |
| always NOT_ENOUGH_INFO | 0.0000 | 0.0000 | 0.0000 | 0/20 | 0/27 |
| always REFUSAL | 0.0000 | 0.0000 | 0.0000 | 0/20 | 0/27 |
| string similarity (your diff-engine rule) | 0.5319 | 0.1087 | 0.4232 | 20/20 | 5/27 |
| lexical oracle only | 0.9787 | 0.2364 | **0.6445** | 20/20 | 26/27 |

The oracle floor moved from **0.7240** (the 361-arm state you ran) to **0.6445**, and the string matcher from
0.5319 to 0.4232. That is the point of the new families: they are hard for a lexical reader in a way the old
set was not — the oracle now produces REFUTED where the contract wants REFUSAL (FDR_neg_REF 0.1223 on
`conflicting_sources` and `same_document` cells). Your "usable range starts at 0.72" holds for the old set; for
this one it starts at 0.6445, and any judge we run has to be read against the family table, not the aggregate.

## Necessity of evidence, computed free (`python3 scoring_v2.py --families`)

EGR-FV (EMNLP 2026 main, `10.18653/2026.emnlp-main.813`) scores each sample by how much the verifier's answer
*needs* the evidence, which takes a trained model. We have a code-only version of the same question: does the
lexical oracle report something different about this arm's evidence than about A's? Where it does not, no
rule-based reader can separate the arms and only a judge that knows the subject can. On this set **71 of 502**
scored cells are like that, and they concentrate exactly where we expected:
`same_document_non_rationale` 39 % of its cells, `length_matched_noise_with_claim_numbers` 34 %,
`random_irrelevant` / `other_document_substitution` / `diluted_support` 28 % each, while `placeholder` gives
the oracle 0 % to bite on. Those numbers come from `verdict over ALL submitted evidence items`, not the first
one — reading only the first item is a bug we shipped for an hour and now have a test against.

`J_gate = Acc(A) − FDR_strict`. Every constant judge scores ≤ 0; a perfect judge scores 1. Accepted from your
review and now written into the freeze file: **J_gate is a gate, not a metric** — never reported without Acc(A)
per subclass and both FDR_neg components beside it, because a judge at −0.5745 and a judge at 0.0000 fail
differently. On the collision-free G the string-similarity baseline has 0 false SUPPORTED, which is why the
withdrawn 47.7 % was an artefact of defect 1 rather than a property of the baseline.

## Freeze and identity

`python3 freeze_v2.py` rewrites two files: `LABEL_MAP_v2.json` (the four-label scale, every alias, the
NEEDS_RECOVERY decision and its measured sensitivity) and `FREEZE_v2.txt` (SHA-256, bytes, lines and CR count of
all 25 artifacts — every code file, every data file, both notes files and the license texts — plus the
environment: OS, build, Python version, LF-only, standard library only, and the seven scoring rules a number
depends on). `FREEZE_v2.txt` does not hash itself. Anything that changes an artifact
invalidates it, including a line-ending change: that is defect 3 we logged against ourselves, now closed by
`newline="\n"` at every write, with CR measured at zero in each artifact.

## Things we did not fix and want you to look at

1. **Circularity.** The set was built with the same lexical oracles that now score the baseline, so the
   oracle-only row (0.7287 here, 0.7240 on the state you ran) is partly self-agreement. It is a ceiling for what
   a lexical reader can do here, not a measure of correctness.
2. **E is still 13.** We expected the validated mutation functions to raise it to 21; they do not — eight
   identity sentences have no number or quotation to distort (7 besides the anchor). Your proposal to generate E
   for the 27 already-distorted items instead is the way out, and we have not implemented it yet.
3. **One domain, one author, 12 passages.** Claims from one passage are not independent; intervals should be
   computed by passage, not by claim. Our design effect is 2.8 at ρ = 0.3 and 4.6 at ρ = 0.6.
4. **`E_restore` evidence equals the claim text.** It is a control for answering from memory, not a reading test.
5. **The 12 passages were reconstructed** from the evidence sentences of the shipped items
   (`passages_reconstructed.json`); rebuilding v1 from them with your original code reproduces your 49 items
   exactly (checked).
6. **Not done or only half done:** polarity and negation checks; order permutations inside a multi-evidence arm
   (we now have such arms — `M_diluted`, `R_pair` — but in one order only); injected instructions inside
   evidence; the second domain (USGS first pass — ours to build, so please don't start it); mechanical paraphrase
   arms (400,000 → 400k → four hundred thousand, units held) for over-strictness; and the pre-model forecast
   filter's false positives, which need control claims where "will" sits inside a quotation.
7. **The judge changed after your three runs:** forecasts and opinions are now stopped by code before the model.
   Any run on this set is a run on the current judge; your v1 results describe the earlier one.

## How to review and change it

```
git checkout v2-checks && cd null-arm-checks-v2
python3 test_checks.py                 # the 12 original tests
python3 test_v2.py                      # 26 tests: every invariant above, including the family fields
python3 test_freeze.py                  # freeze file vs files on disk, label map completeness
python3 verify_all.py                   # everything above plus idempotency, CR and text hygiene; exit code
python3 scoring_v2.py --selftest        # degenerate judges must not pass the gate
python3 scoring_v2.py --baselines       # the table above
python3 scoring_v2.py --families        # per construction family, plus the necessity table
python3 build_arms_v2.py                # regenerate arms and manifest (idempotent, verified byte-exact)
python3 freeze_v2.py                    # rewrite LABEL_MAP_v2.json and FREEZE_v2.txt
```

Rules live in `build_arms_v2.py` (construction), `ARM_MANIFEST_v2.json` (expected and acceptable labels),
`LABEL_MAP_v2.json` (label scale) and `scoring_v2.py` (scoring). Comment on any line of the PR, push a commit to
this branch, or tell us what you would do differently.

Nothing has been run on a paid judge, and per your message neither side runs until the freeze is joint.
