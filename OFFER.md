# Further cross-checks we can run together

Everything below is labelled by what you can verify yourself today
(**checkable**), what we can only report (**assertion**), and what does not
exist yet (**not built**). Numbers were measured on 30 October 2026.

## 1. Free and public now — checkable

**`https://helixcom.org/check`** — paste a claim and its source text; HELIX
reconciles numbers and dates with code, in a fraction of a second, no sign-in,
no model call. It shows which number was found where and which was not. It does
not judge opinions or forecasts. Your probe can be pointed at it the same way it
was pointed at our core: one claim per position, a genuine source per position,
the null arms in place of the source.

## 2. Hosted battery endpoint — not built yet

Agreed in your PART 2: an endpoint rather than source, per-position discipline,
`UNTESTED` where no genuine reply is supplied. The AK-MASTER battery has 28
checks, 27 of them model-free; the endpoint will publish its exact check list
under a daily cap. We will send the URL when it is live — not before.

## 3. The paid judge — on request, at our cost

The full HELIX research pipeline goes beyond reconciling numbers. It runs several
live search rounds over the open web and scientific databases, then a judge model
reads and labels the evidence. Every consequence of those labels is computed by
named Python functions, not by the model:
- evidence levels (ECT);
- the Heuer-style ACH hypothesis matrix;
- whether a human is required.

Measured runs (published on our side):

| run | sources / facts | time | cost |
|---|---|---|---|
| Moon landings, run 4 | 110 search facts | 493 s | $1.56 |
| Moon landings, run 7 | 83 search facts | 1 697 s | $1.73 |
| Chernobyl, scientific run 4 | 170 sources | 13 min | — |

Because it is paid, it is not open to the public. We offer to run it on a small
set of claims **you** choose — including claims built to break it — and to
publish the per-claim output, failures included. The judge is exactly the kind of
instrument your probe exists for: a null-arm test of the judge stage is the check
we have **not** done yet and would most like you to design.

## 4. Size and contract audit of the engine — assertion

The code and specifications are private. Reported with the command that
produces each number, so a reviewer given read access can reproduce them in
under an hour:

| what | number | command |
|---|---|---|
| HELIX core modules | 113 (38 577 lines) | module registry |
| written HELIX specification | 51 876 lines in 23 files | `cat helix_pipeline/docs/specs/*.md \| wc -l` |
| states the specs name / unreachable by code | 949 / 0, across 5 specs | `python -m helix_pipeline.engine.helix_contract_audit` |
| Mr. Helix capsules / states / unreachable | 99 / 583 / 0 | `python -m mr_helix.engine.capsule_contract_audit` |

"Unreachable 0" means every state a spec names, the code can return. It is not
load certification and not proof that the state is returned under the right
conditions. That second question is the one your probe asks.

## 5. What we have not done, stated up front

- We have not run `null_model_test.py` against your classifier; we make no claim about your battery.
- The scorer for our newsroom's "strength of analysis" is not probed yet (it aggregates several pipeline stages and needs its own empty-input contract).
- One published figure still carries an older build tag because its sample no longer exists.
