# v1.6 final — baselines run, and known shortcomings

**Date:** 2026-10-30 · **Artefact under test:** `JUDGE_PROBE_v1.6_final.md` (as shipped, 78,975 bytes)
**Method:** code extracted from the document's fenced blocks into an empty directory and run there. Nothing from the
working tree was used.

---

## 1. Baselines, as shipped

| # | baseline | result |
|---|---|---|
| 1 | `--selftest` | **PASSED** — 8 named regressions, 4 receipt checks, 5 parts, 150 matrix cells |
| 2 | `--matrix` | **PASSED** — 150 cells, every one matching the specification |
| 3 | grade the live run | **graded** — 2 failures (c10 E1, c11 E2), sensitivity 11/12, specificity 12/12, coverage 71% |
| 3b | `--require-complete` on the live run | **exit 1** — nonzero, as it should be with failures present |
| 4 | empty input `{}` | **exit 3** — nothing graded, not reported as success |
| 5 | garbage label `"BANANA"` | **FAIL:malformed_label** on every arm it touches |

The document runs from a clean directory with only what it carries. That is the first time that has been true.

---

## 2. Known shortcomings

### Serious — the package cannot reproduce its own live run

**S2.1 The live harness is not in the bundle.** `action/helix_judge_probe.py` — the script that built the claims,
constructed the six arms, called the endpoint 72 times and wrote the receipts — is absent. The document carries the
*results* and the *grader* but not the means to produce them. A reader can re-grade the 72 calls; they cannot re-run
them, and cannot check how the arms were constructed. Given that four of the four real defects found in this project
were in arm construction, that is the most important missing file.

**S2.2 The bundle has two JSON blocks and nothing distinguishing them.** Plan and live run are both fenced `json`.
My own extraction script grabbed the wrong one on the first attempt, because last-block-wins. Filename markers above
each fence would fix it; there are none.

**S2.3 The shipped plan does not match the live run.** The plan carries 12 claims × up to 8 arms. The live run used a
derived plan of 6 arms because `E3_null_search`, `FORECAST_*` and `CTRL_FACTUAL` were never exercised. Grading the
live run against the shipped plan therefore reports **71% coverage**, and that number reflects a design/run mismatch
rather than missing data. A reader could reasonably conclude 29% of the plan failed to execute.

### Untested — never run against a real judge

**S2.4 `E3_null_search`** — never exercised, live or otherwise.

**S2.5 The entire forecast apparatus** — `FORECAST_OWN`, `FORECAST_PERM`, `CTRL_FACTUAL`, the decision table and the
control gate. These carry the largest part of the v1.1–v1.6 work and have only ever run against synthetic fixtures.
The instrument is not validated for the claim type it spent longest designing for.

**S2.6 `_status` ERROR path** — the transport-failure branch is simulated in fixtures only. No real timeout, 5xx or
connection reset has ever flowed through it.

**S2.7 Live retrieval** — every arm injects evidence, so nothing here tests whether HELIX's search finds sources.
That is a different instrument and it does not exist.

**S2.8 Concurrency and load** — 72 sequential calls, 0.3 s each. No parallel run, no rate-limit behaviour, no
partial-failure run.

### Semantic — unsettled, not broken

**S2.9 `NEI` versus `CONTRADICTED` on a distorted claim.** One live case (c11) returned `NEI` where the arm expected
`REFUTED`. It is graded `e2_distortion_unflagged` — a failure, but a lesser one. Whether `NEI` is acceptable there is
a policy question for HELIX, not something the grader should decide alone.

**S2.10 `F_unrelated` scoring for inequality/comparator judges.** A comparator handed an unrelated passage carrying a
different figure *should* contradict, so `REFUTED` passes. But there is no test distinguishing "correctly contradicted
unrelated material" from "happened to contradict it". The arm is permissive by construction.

**S2.11 Claim source bias.** All 12 live claims came from one article of ours about refining capacity — heavy on
quantities and years. The deliberately-spoiled claim set (unit swaps, misquotes, fabricated citations) was never used
live. The equality/inequality/date paths are covered; fabrication, misquotation and superseded figures are not.

### Structural — stated, not hidden

**S2.12 The matrix is not exhaustive over joint states.** 150 cells across marginal states plus the named
dependencies. This was claimed exhaustive in v1.3 and was not; the claim is withdrawn and the limitation stated in
the docstring.

**S2.13 Receipts are tamper-evident, not authenticating.** The digest proves a receipt was not edited after
publication. It does not prove the call happened. The format has a `signature` block for the stronger claim; nothing
implements it yet, and `model.version_or_hash` is `null` for the live run because HELIX publishes no endpoint version.

**S2.14 Six versions, and it is still not validated.** Four review rounds found defects in each round that the
previous round's testing could not see. There is no basis for believing a fifth round would find none.

---

## 3. What the baselines do establish

The grader is deterministic, self-testing, portable, and refuses to report success when it has observed nothing. It
grades malformed output as failure rather than restraint, distinguishes a missing observation from a refusal, and
carries its own named regressions for every defect found across four review rounds and two live runs.

The **judge under test came out clean** on everything constructible: 12 baselines, 11 of 12 distortions, 12 noise
arms, 12 empty sources, and direct probes of the equality, inequality and date paths.

The four defects that mattered were all in the instrument, and all were found by running it — which is the argument
for the next round being a live run rather than another read.
