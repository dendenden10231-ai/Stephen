# Re-scoring of your run `helix-nullarm-run-2026-11-02` (commit `e368e3f`) — where we reproduce it and where we do not

We promised on 03.11 a review that names, per family, where we reproduce your numbers. This is it.
Method: your `results_gptoss120b.jsonl` and `got_helix_gptoss120b.json` from your branch, our
`scoring_v2.py` (branch `v2-checks`, 511-arm `arms_v2.json`), nothing edited, no model, no network.

| claim in your comment | our re-score | verdict |
|---|---|---|
| `scoring_v2_output.json` as published | `python3 scoring_v2.py got_helix_gptoss120b.json` output is **identical to yours on every key** (deep comparison) | reproduced |
| Acc_A 0.9149, Det_A 0.9362 | 0.9149, 0.9362 (A_supported 19/20, A2_distorted 24/27) | reproduced |
| FDR_neg 0.0951 (SUP 0.0543, REF 0.0408), J_gate 0.8198 | same | reproduced |
| 126 noise cells: 117 NEI vs 1 REFUSAL | 117 / 1 | reproduced |
| class SUPPORTED 64/67, REFUTED 59/67, REFUSAL 62/92 | 64/67, 59/67, 62/92 (label equals expected) | reproduced |
| class NOT_ENOUGH_INFO 265/276 | **264/276** when the label must equal the expected one; **265/276** when any acceptable label counts | reproduced under the acceptable-label reading; one cell is the difference |
| conflicting sources "13 of 40, 24 unacceptable determinate" | per-family table: **13 acceptable of 41 cells, 24 unacceptable determinate**; the two unparsable labels are both in this family (`c03.s0.year_shift/R_pair`, `c12.s0.scale_shift/R_pair`) | 13 and 24 reproduced; the denominator is 41 in our scorer, not 40 — we have not found which cell your 40 leaves out |
| `C_num_noise` "39 of 47, 8 unacceptable determinate" | `length_matched_noise_with_claim_numbers`: 39 acceptable of 47, 8 unacceptable determinate | reproduced |
| `c07` forecast diagnostic `SCOPE_NOT_REFUSED` | own NEI, borrowed NEI, weakened REFUSAL → `SCOPE_NOT_REFUSED` | reproduced |
| 502 cells scored, 9 anchors excluded, 0 transport errors, 2 unparsable | 511 rows, 9 anchors, 2 empty labels | reproduced |

Definitions: "acceptable" is the arm's `acceptable` list in `ARM_MANIFEST_v2.json`; "determinate" is SUPPORTED or
REFUTED; "unacceptable determinate" is a determinate label not on that list.

Other families in the same re-score, for completeness: `placeholder`, `random_irrelevant`, `other_document_substitution`,
`same_topic_non_rationale`, `high_overlap_insufficient`: no unacceptable determinate answer; `same_document_non_rationale`
3 of 28; `diluted_support` 2 of 47; `contradicting_distortion` 1 of 13; `full_support` 1 of 47.

Where we do not reproduce: only the two denominators above (265 vs 264, 40 vs 41), both one cell. We list them rather than round them away.
