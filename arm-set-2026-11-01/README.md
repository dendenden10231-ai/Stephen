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

Regenerate and verify:

```bash
python3 build_arms.py     # writes arms_expanded.json, prints the build report
```

Anyone can run it and confirm nothing was hand-placed. Construction is mechanical
and seeded from each claim id, so both sides get byte-identical noise.

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
