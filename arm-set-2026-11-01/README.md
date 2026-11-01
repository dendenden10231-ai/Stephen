# Arm set for the 45 kept mutation claims — 238 arms

Built 1 November 2026 by Spider-local (Helix node, helixclaw) under the
Custodian's direction, from `null-arm-checks/mutation_items_no_second_refinery.json`
(Denis Vashkevich, Apache-2.0).

This folder adds the **arms** to Denis's **claims**. His set supplies one
evidence item per claim and a label known by construction; this set supplies the
null arms those claims need before the null-arm question can be answered at all.

## What is here

| File | What it is |
|---|---|
| `arms_expanded.json` | 238 arms over the 45 kept claims, ready for either judge |
| `build_arms.py` | the builder; deterministic, stdlib only, no model called |
| `ARM_MANIFEST.json` | expected verdict and scoring class for **every** arm |
| `make_manifest.py` | emits the manifest from the arm set |
| `scoring.py` | the scoring contract, with baselines and a selftest |

Regenerate and verify:

```bash
python3 build_arms.py       # writes arms_expanded.json, prints the build report
python3 make_manifest.py    # writes ARM_MANIFEST.json + its sha256
python3 scoring.py --selftest    # proves the scorer behaves
python3 scoring.py --baselines   # the numbers a real judge has to beat
```

Anyone can run it and confirm nothing was hand-placed. Construction is mechanical
and seeded from each claim id, so both sides get byte-identical noise.

## The scoring contract

No single aggregate over the 238 arms. Five blocks, reported separately:

1. **A accuracy** — positive arms, determinate label expected
2. **negative-arm false-SUPPORTED rate** — credulity across B, C, F, G
3. **over-strictness** — A arms refused or abstained
4. **REFUTED-class accuracy** — A arms whose expected label is REFUTED
5. **SUPPORTED-class over-strictness** — A arms whose expected label is SUPPORTED

`E` is **small-n** (13 arms): reported with a Wilson 95 % interval and labelled
small-n, never as a stable contradiction-accuracy rate.

Every arm's expected verdict is stated in `ARM_MANIFEST.json`, including the
labels that count as acceptable and the ones that are specifically wrong:

| arm | acceptable | specifically wrong |
|---|---|---|
| `A_genuine` | the claim's constructed label | refusal/NEI = over-strictness |
| `B_empty` | NEI, REFUSAL | SUPPORTED = credulity from no evidence |
| `C_noise_length` | NEI, REFUSAL | SUPPORTED = mode 2 (length-sensitive) |
| `E_contradicting` | REFUTED | SUPPORTED = credulity |
| `F_unrelated` | NEI, REFUSAL, REFUTED\* | SUPPORTED = credulity on irrelevant evidence |
| `G_permuted` | NEI, REFUSAL | SUPPORTED = mode 1 (content-blind) |

\* `REFUTED` on `F` is admissible only per the S2.10 rule — that passage carries
a contradicting quantity of the same kind.

`c10.s0.identity` is **prose-only** (no number, no quotation), so the reference
oracles cannot grade it. It is carried as an **anchor** and excluded from accuracy.

## Baselines — the numbers a judge has to beat

> **CORRECTION 2026-11-01 (after external audit by Denis Vashkevich).** The
> baseline table below is **superseded**. It was measured on a v1 arm set with
> three structural defects, all confirmed:
>
> 1. **`G` borrowed by claim index, not passage.** The corpus is 12 passages
>    across 45 claims (up to six claims per passage), so **33 of 45 `G` arms fed
>    the claim its own source passage**. They were not permuted-evidence arms.
> 2. **`C` noise arms carried an empty `source`** — 45 of 45 — so a change of
>    source could explain a label change rather than the content.
> 3. **`F` allowed `REFUTED` unconditionally** in the manifest — 45 of 45 —
>    where rule S2.10 permits it only when that passage carries a contradicting
>    quantity.
>
> Consequence for the headline: the `diff-engine` figure of **0.4773 false
> SUPPORTED on `G` was an artefact of defect 1**, not a property of the baseline.
> On a collision-free set the same baseline has `FDR_neg 0.0000`, `Acc_A 0.5319`,
> and its real weakness is 5 of 27 on the already-distorted half. Anywhere this
> number was quoted, it is wrong and should be replaced.
>
> The v2 proposal (`null-arm-checks-v2`, PR #4) enforces all three invariants in
> code with assertions, restores `D`, adds `C_num_noise`, and splits `A` into
> supported and already-distorted halves scored separately.

Measured with `python3 scoring.py --baselines` — **v1, superseded, see correction above**:

| baseline | A accuracy | negative false-SUPPORTED | REFUTED-class | E (small-n) |
|---|---|---|---|---|
| always SUPPORTED (credulous) | 0.4773 | **1.0000** (176/176) | 0.0 | 0.0 |
| always NOT_ENOUGH_INFO | 0.0 | 0.0 | 0.0 | 0.0 |
| always REFUSAL | 0.0 | 0.0 | 0.0 | 0.0 |
| diff-engine (string similarity) | 0.5455 | 0.1193 (G: 0.4773) | **0.1304** | 0.0 |

Corrected figures on the v2 (assertion-enforced) set, for comparison:

| baseline | Acc(A) | FDR_neg | J_gate |
|---|---|---|---|
| always SUPPORTED | 0.4255 | 1.0000 | −0.5745 |
| always REFUTED | 0.5745 | 0.8652 | −0.4255 |
| diff-engine | 0.5319 | **0.0000** | 0.5319 |
| oracle-only | 0.9787 | 0.1199 | **0.7240** |


## The arms

Per claim, where constructible:

| Arm | Evidence supplied | Requirement |
|---|---|---|
| `A_genuine` | the passage the claim was built from | determinate label equal to the expected label |
| `B_empty` | none | `NOT_ENOUGH_INFO` or `REFUSAL` — never determinate |
| `C_noise_length` | random prose, char count within ±5 % of A | must **differ** from this claim's A label; equality is mode 2 |
| `E_contradicting` | the passage with a real distortion injected | must differ from A, opposite direction (`REFUTED`) |
| `F_unrelated` | another passage's genuine evidence | `REFUTED` only if that passage carries a contradicting quantity; else `NOT_ENOUGH_INFO` |
| `G_permuted` | the next claim's genuine evidence (cyclic) | must not reproduce this claim's A label; equality proves mode 1 |

Counts: 45 A · 45 B · 45 C · 45 F · 45 G · 13 E = **238**.
E exists only for claims whose genuine arm expects `SUPPORTED` and whose
contradicting passage passes the validity gate; 32 claims have no E arm.

## Two things the builder found in its own output

Both were fixed before this set was committed, and both are the reason the
builder applies Denis's rule to its own arms rather than assuming they are sound:

1. **Three E arms were invalid.** The first construction produced contradicting
   passages that the number oracle scored `MATCH` — the passage did not actually
   contradict. That is the same defect class as `11.7 → 11.70`, and it is what
   `arm_check.check_distorted` exists to reject. The builder now gates every E arm
   on the oracle and drops any that fail (0 invalid E in the shipped set).
2. **Nine C arms carried number words.** The first noise generator drew from a
   word list containing `one`, `two`, `three`, `quarter`; the number oracle read
   them as comparable quantities (`VALUE_MISMATCH`). Length-matched noise must
   carry **no comparable quantity**, or it stops being a null arm. The word list
   was stripped of numerals and the set rebuilt (0 contaminated C; length match
   mean 2.28 %, max 5.00 %).

## Limits, same as the source set

- The oracles are lexical. They read numbers, units, dates and quotations; they
  do not read meaning. A claim wrong in words but right in numbers passes.
- `C` is trivially satisfied by a judge that refuses everything — and that judge
  then fails `A`. **A and C must be scored as a pair, never separately.**
- 45 claims is 45, not 450. The result is a count and an identity of failures,
  not an interval around a rate.
- Nothing here has been run against either judge.

## Licence

Apache-2.0, matching the source set. Attribution: claims and oracles
Denis Vashkevich (helixcom.org); arms and builder Helix AI Innovations Inc.
